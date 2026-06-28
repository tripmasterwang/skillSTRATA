"""Unit tests for the SkillOS engine. Run: python -m pytest tests/ -q"""

from __future__ import annotations

import pytest

from skillos import (
    SkillGraph, SkillNode, Granularity, Status, EdgeType,
    insert, update, link, split, merge, retire, should_split,
    GraphRouter, FlatRouter, LifecycleManager, GraphGovernedEvolver,
    Patch, PatchEdit, compute_skill_heat, HeatConfig,
)


def _atom(name, body="x", tts=None, deps=None):
    return SkillNode.make(name=name, body=body, granularity=Granularity.ATOMIC,
                          task_types=tts or [], dependencies=deps or [])


def test_insert_and_stable_id():
    g = SkillGraph()
    r = insert(g, _atom("Load CSV"))
    assert r.ok and "load_csv" in g.nodes
    # duplicate id rejected
    assert not insert(g, SkillNode.make(name="Load CSV")).ok


def test_link_and_dependency_closure():
    g = SkillGraph()
    insert(g, _atom("a")); insert(g, _atom("b")); insert(g, _atom("c"))
    link(g, "a", "b", EdgeType.DEPENDS_ON)
    link(g, "b", "c", EdgeType.DEPENDS_ON)
    # closure of a must pull transitive prerequisites b, c
    assert g.dependency_closure(["a"]) == {"a", "b", "c"}


def test_split_refactors_monolith():
    g = SkillGraph()
    insert(g, SkillNode.make(name="big", body="P1\n\nP2", task_types=["t1", "t2"],
                             granularity=Granularity.PLAN))
    children = [_atom("c1", tts=["t1"]), _atom("c2", tts=["t2"])]
    res = split(g, "big", children)
    assert res.ok and len(res.affected) == 3
    # parent now PLAN router with PARENT_CHILD + DEPENDS_ON edges to children
    for c in res.affected[1:]:
        assert g.capability.has_edge("big", c)
        assert g.nodes[c].parents == ["big"]
    # a split_decision governance node was recorded
    assert any(r.kind == "split_decision" for r in g.rules.values())


def test_merge_unions_and_retires():
    g = SkillGraph()
    a = _atom("a", tts=["t1"]); b = _atom("b", tts=["t2"])
    a.heat.success_count = 5; b.heat.success_count = 2
    insert(g, a); insert(g, b)
    res = merge(g, ["a", "b"])
    assert res.ok
    assert g.nodes["a"].status == Status.DEPLOYED or g.nodes["a"].status == Status.CANDIDATE
    # survivor is higher-success 'a'; 'b' retired
    assert g.nodes["b"].status == Status.RETIRED
    assert set(g.nodes["a"].task_types) == {"t1", "t2"}


def test_should_split_heuristic():
    big = SkillNode.make(name="big", body="word " * 3000, task_types=["t1", "t2", "t3"])
    small = SkillNode.make(name="small", body="short", task_types=["t1"])
    assert should_split(big)
    assert not should_split(small)


def test_retire_only_low_value():
    g = SkillGraph()
    good = _atom("good"); good.status = Status.DEPLOYED
    good.heat.success_count = 9; good.heat.failure_count = 1
    bad = _atom("bad"); bad.status = Status.DEPLOYED
    bad.heat.success_count = 1; bad.heat.failure_count = 9
    insert(g, good); insert(g, bad)
    g.step = 5
    res = retire(g, floor=999.0)   # high floor -> retire the worst eligible
    assert res.ok and res.affected == ["bad"]   # never the high-success skill


def test_graph_router_minimal_subgraph():
    g = SkillGraph()
    # entry skill 'parse' depends on unhinted prerequisite 'tokenize'
    insert(g, _atom("parse", body="parse handle text", deps=["tokenize"]))
    insert(g, _atom("tokenize", body="tokenize split words"))
    insert(g, _atom("unrelated", body="plot chart axis"))
    for n in g.nodes.values():
        n.status = Status.DEPLOYED
    link(g, "parse", "tokenize", EdgeType.DEPENDS_ON)
    route = GraphRouter(g, top_seeds=1).route("parse handle text")
    # router recovers the unhinted dependency, excludes the unrelated skill
    assert "parse" in route.nodes and "tokenize" in route.nodes
    assert "unrelated" not in route.nodes


def test_flat_router_topk():
    g = SkillGraph()
    insert(g, _atom("aaa", body="alpha alpha")); insert(g, _atom("bbb", body="beta beta"))
    for n in g.nodes.values():
        n.status = Status.DEPLOYED
    route = FlatRouter(g, k=1, mode="bm25").route("alpha")
    assert route.nodes == ["aaa"]


def test_lifecycle_promote_and_block():
    g = SkillGraph()
    n = _atom("s"); n.status = Status.VALIDATED
    insert(g, n)
    lc = LifecycleManager(g, govern=True, block_min_trials=2, block_success_rate=0.5)
    lc.promote_deployable()
    assert g.nodes["s"].status == Status.DEPLOYED
    # make it a chronic failer -> governance blocks it from routing
    n.heat.success_count = 0; n.heat.failure_count = 5
    lc.govern_sweep()
    assert "s" in g.blocked_skills()


def test_heat_recency_decay():
    n = _atom("s"); n.heat.n_visit = 3; n.heat.coverage = 2; n.heat.last_used_step = 0
    hot = compute_skill_heat(n, now_step=0, cfg=HeatConfig())
    cold = compute_skill_heat(n, now_step=1000, cfg=HeatConfig())
    assert hot > cold   # recency term decays over logical steps


def test_evolver_replaces_reduce():
    """GraphGovernedEvolver.absorb consumes Trace2Skill-style patches into a graph."""
    ev = GraphGovernedEvolver()
    patches = [
        Patch(reasoning="r", edits=[PatchEdit(file="SKILL.md", op="add_section",
              target_section="Date Normalization", content="normalize dates")],
              task_id="t1", task_type="table_qa"),
        Patch(reasoning="r", edits=[PatchEdit(file="SKILL.md", op="add_section",
              target_section="Date Normalization", content="more date rules")],
              task_id="t2", task_type="table_qa"),
    ]
    ev.absorb({"SKILL.md": ""}, patches)
    # the two edits to the same section collapse into one node (not a growing monolith)
    assert "date_normalization" in ev.graph.nodes
    node = ev.graph.nodes["date_normalization"]
    assert "t1" in node.evidence_traces and "t2" in node.evidence_traces


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))


# --------------------------------------------------------------------- verify-loop (node-local)
def test_mint_checkpoint_on_error_prone_node_only():
    from skillos.verify import mint_checkpoints_from_traces
    g = SkillGraph()
    good = SkillNode.make(name="good", body="g", status=Status.DEPLOYED)
    bad = SkillNode.make(name="bad", body="b", status=Status.DEPLOYED)
    g.add_skill(good); g.add_skill(bad)
    good.heat.success_count, good.heat.failure_count = 5, 0      # reliable -> no guard
    bad.heat.success_count, bad.heat.failure_count = 1, 4        # error-prone -> guard
    minted = mint_checkpoints_from_traces(g)
    assert g.guarded_skills() == {bad.id}
    assert len(minted) == 1 and g.guarding_checkpoints(bad.id)[0].postcondition
    # idempotent: a second pass adds nothing
    assert mint_checkpoints_from_traces(g) == []


def test_node_verifier_loop_rolls_back_and_repairs():
    from skillos.verify import node_verifier_loop, record_attempts
    from skillos.schema import GovernanceNode
    g = SkillGraph()
    bad = SkillNode.make(name="bad", body="b", status=Status.DEPLOYED)
    g.add_skill(bad)
    cp = GovernanceNode(id="cp", kind="checkpoint", statement="", targets=[bad.id],
                        postcondition="ok", max_retries=2)
    state = {"v": "dirty"}; restored = []
    out = node_verifier_loop(
        cp,
        execute_fn=lambda i, hint: i,                       # result = attempt index
        verify_fn=lambda res: (res >= 2, "not yet"),        # passes on 3rd attempt
        snapshot_fn=lambda: dict(state),
        restore_fn=lambda tok: restored.append(tok))
    assert out.ok and out.n_attempts == 3
    assert len(restored) == 2                               # rolled back before each of 2 retries
    record_attempts(g, out)
    assert bad.heat.success_count == 1 and bad.heat.failure_count == 2
    assert any(d.get("type") == EdgeType.FIXED_BY.value for _, _, d in g.trace.edges(data=True))


def test_verify_loop_gives_up_within_budget():
    from skillos.verify import node_verifier_loop
    from skillos.schema import GovernanceNode
    cp = GovernanceNode(id="cp", kind="checkpoint", targets=["x"], statement="",
                        postcondition="ok", max_retries=2)
    out = node_verifier_loop(cp, execute_fn=lambda i, h: i,
                             verify_fn=lambda res: (False, "always fails"))
    assert not out.ok and out.n_attempts == 3              # 1 + max_retries, then escalate


# --------------------------------------------------------------------- harness block (plug-and-play)
def test_route_skills_is_per_role():
    from skillos.harness import route_skills
    g = SkillGraph()
    for nm in ["edit refactor", "run tests", "locate code"]:
        g.add_skill(SkillNode.make(name=nm, body="b:" + nm, status=Status.DEPLOYED))
    def fake_llm(system, user):
        if "editor" in user: return '["edit_refactor"]'
        if "explorer" in user: return '["locate_code"]'
        return '["run_tests"]'
    ed = route_skills(g, "fix bug", role="editor", llm_call=fake_llm)
    ex = route_skills(g, "fix bug", role="explorer", llm_call=fake_llm)
    assert ed.nodes == ["edit_refactor"] and ex.nodes == ["locate_code"]   # per-role routing differs


def test_render_listing_hides_body():
    from skillos.harness import route_skills, render_skill_text, render_skill_md_files
    g = SkillGraph()
    g.add_skill(SkillNode.make(name="edit", description="edit desc", body="SECRET-BODY", status=Status.DEPLOYED))
    r = route_skills(g, "edit something")
    assert "SECRET-BODY" in render_skill_text(r)                # full inject has body
    assert render_skill_md_files(r, g)[0][0] == "edit/SKILL.md"


# --------------------------------------------------------------------- navtrace (node-level curate)
def test_nav_attribution_is_per_visited_node(tmp_path):
    import json
    from skillos.navtrace import parse_nav_log, attribute_nav_heat
    g = SkillGraph()
    for nm in ["a", "b", "c"]:
        g.add_skill(SkillNode.make(name=nm, body="x", status=Status.DEPLOYED))
    log = tmp_path / "nav.jsonl"
    log.write_text("\n".join(json.dumps(r) for r in [
        {"action": "locate", "cursor": "a", "task": "t"},
        {"action": "step_to", "cursor": "b"},
        {"action": "go_off_graph", "cursor": None, "note": "no skill"}]))
    nav = parse_nav_log(str(log), "i1")
    attribute_nav_heat(g, nav, success=False)
    assert g.nodes["a"].heat.failure_count == 1 and g.nodes["b"].heat.failure_count == 1
    assert g.nodes["c"].heat.trials == 0          # unvisited node is NOT blamed (precision over route-set)


def test_offgraph_distills_into_new_node(tmp_path):
    import json
    from skillos.navtrace import curate_from_navlogs
    from skillos.curate import Fragment
    g = SkillGraph()
    g.add_skill(SkillNode.make(name="a", body="x", status=Status.DEPLOYED))
    log = tmp_path / "nav.jsonl"
    log.write_text("\n".join(json.dumps(r) for r in [
        {"action": "locate", "cursor": "a", "task": "t"},
        {"action": "go_off_graph", "cursor": None, "note": "regen proto"}]))
    summ = curate_from_navlogs(g, [(str(log), "i1", False)],
                               distill_fn=lambda note, task: Fragment(name="regen proto", description="d", body="HOWTO"))
    assert summ["inserted"] == 1 and "regen_proto" in g.nodes   # graph learned a skill from off-graph
