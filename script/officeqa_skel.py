#!/usr/bin/env python3
"""SkillStrata x OfficeQA — SKELETON smoke (stages B+C).

Validates the SkillStrata pipeline on SkillOpt's officeqa env WITHOUT rebuilding
the agent loop: SkillOpt's eval_only.py is the rollout/eval engine (stage A, run
separately); here we add the SkillStrata-specific graph layer:

  Stage B  distill train traces -> Fragments -> integrate into a SkillGraph
  Stage C  route a test item over the graph -> render skill .md -> eval_only(1 item)

Splits are SkillOpt's own data/officeqa_split (train=50/val=24/test=172). Target +
distill LLM = qwen3.6-35b (xopqwen36v35b) via Xunfei MaaS with the *wys* key.
"""
from __future__ import annotations
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path("/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research")
SKILLSTRATA = ROOT / "projects/skillSTRATA"
SKILLOPT = ROOT / "projects/nonergodic-self-evolution/external/SkillOpt"
SKEL = SKILLSTRATA / "runs/officeqa_skel"
WKEY = (ROOT / "_shared/LLM_apis/.xunfei_api_key_wys").read_text().strip()
QWEN_BASE = "https://maas-api.cn-huabei-1.xf-yun.com/v2"
QWEN_MODEL = "xopqwen36v35b"

sys.path.insert(0, str(SKILLSTRATA))
from skillos.curate import Fragment, integrate_fragments  # noqa: E402
from skillos.graph import SkillGraph  # noqa: E402
from skillos.router import GraphRouter  # noqa: E402
from skillos.persist import save_graph  # noqa: E402

_DISTILL_SYS = (
    "You distill REUSABLE OfficeQA research skills from an agent's execution trace. OfficeQA asks "
    "fact questions answerable from office documents / the web. Extract transferable lessons that "
    "would help on FUTURE similar questions — search/lookup tactics, how to read a doc, how to "
    "format the final <answer>, common failure guards — NOT facts about this one question."
)


def _qwen_client():
    from openai import OpenAI
    return OpenAI(base_url=QWEN_BASE, api_key=WKEY)


def _flatten(conv_path: Path) -> str:
    msgs = json.loads(conv_path.read_text())
    out = []
    for m in msgs:
        c = m.get("content")
        if isinstance(c, list):
            c = " ".join(str(p.get("text", p) if isinstance(p, dict) else p) for p in c)
        out.append(f"[{m.get('role')}] {c}")
    return "\n".join(out)


def distill_trace(client, log_text: str) -> list[Fragment]:
    user = (
        "Execution trace (truncated):\n---\n" + log_text[:12000] + "\n---\n\n"
        "Return ONLY a JSON array (possibly empty) of lesson objects, each:\n"
        '{"name": "...", "description": "...", "body": "<concrete guidance>", '
        '"task_types": ["lookup"|"reasoning"|"extraction"|"format"|"all"], "kind": "skill"|"fix"}'
    )
    r = client.chat.completions.create(
        model=QWEN_MODEL,
        messages=[{"role": "system", "content": _DISTILL_SYS}, {"role": "user", "content": user}],
        extra_body={"enable_thinking": False}, max_tokens=2048, temperature=0.0)
    txt = r.choices[0].message.content or ""
    out: list[Fragment] = []
    for frag in re.findall(r"\[[\s\S]*\]", txt):
        try:
            arr = json.loads(frag)
        except Exception:
            continue
        for o in arr:
            if isinstance(o, dict) and o.get("body"):
                out.append(Fragment(
                    name=str(o.get("name", "lesson"))[:80], description=str(o.get("description", "")),
                    body=str(o["body"]), task_types=list(o.get("task_types", []) or []),
                    kind=str(o.get("kind", "skill"))))
        if out:
            break
    return out


def stage_b() -> SkillGraph:
    print("=== STAGE B: distill train traces -> graph ===")
    client = _qwen_client()
    graph = SkillGraph()
    pred = SKEL / "train_rollout/predictions"
    all_frags: list[Fragment] = []
    for uid_dir in sorted(pred.iterdir()):
        conv = uid_dir / "conversation.json"
        if not conv.is_file():
            continue
        frags = distill_trace(client, _flatten(conv))
        all_frags += frags
        print(f"  [{uid_dir.name}] distilled {len(frags)} fragment(s): {[f.name for f in frags]}")
    res = integrate_fragments(graph, all_frags)
    print(f"  integrate -> inserted={len(res['inserted'])} merged={len(res['merged'])} "
          f"| graph nodes={len(graph.nodes)}")
    # NOTE: integrate inserts nodes as CANDIDATE; the router only pools DEPLOYED/VALIDATED nodes.
    # In the full curate loop, skillos.curate.validation_gate promotes nodes that beat the empty
    # graph on the VAL split (needs val rollouts). For this skeleton smoke we promote directly so
    # routing is exercised; the full run MUST replace this with validation_gate(+val_score_fn).
    from skillos.schema import Status
    for n in graph.nodes.values():
        n.status = Status.DEPLOYED
    print(f"  [skeleton] promoted {len(graph.nodes)} nodes CANDIDATE->DEPLOYED "
          f"(full run uses validation_gate instead)")
    save_graph(graph, str(SKEL / "graph.json"))
    print(f"  saved graph -> {SKEL/'graph.json'}")
    return graph


def stage_c(graph: SkillGraph):
    print("=== STAGE C: route a test item -> skill.md -> eval_only(1 test item) ===")
    test_items = json.loads((SKILLOPT / "data/officeqa_split/test/items.json").read_text())
    q = test_items[0].get("question", "")
    print(f"  test[0] uid={test_items[0].get('uid')} q={q[:90]!r}")
    route = GraphRouter(graph).route(q)
    skill_md = route.render()
    skill_path = SKEL / "routed_skill.md"
    skill_path.write_text(skill_md or "# (empty route)\n")
    print(f"  routed nodes={getattr(route,'nodes',None) or getattr(route,'node_ids',None)} "
          f"| skill.md {len(skill_md)} chars -> {skill_path}")

    env = dict(os.environ)
    env.update(
        TARGET_QWEN_CHAT_BASE_URL=QWEN_BASE, TARGET_QWEN_CHAT_API_KEY=WKEY,
        TARGET_QWEN_CHAT_MODEL=QWEN_MODEL, TARGET_QWEN_CHAT_TEMPERATURE="0",
        TARGET_QWEN_CHAT_ENABLE_THINKING="false",
        OPTIMIZER_QWEN_CHAT_BASE_URL=QWEN_BASE, OPTIMIZER_QWEN_CHAT_API_KEY=WKEY,
        OPTIMIZER_QWEN_CHAT_MODEL=QWEN_MODEL)
    out = SKEL / "test_routed_1"
    cmd = [sys.executable, "scripts/eval_only.py", "--config", "configs/officeqa/default.yaml",
           "--skill", str(skill_path), "--split", "test",
           "--cfg-options", "env.data_dirs=data/officeqa_hf", "env.max_tool_turns=10",
           "env.exec_timeout=300",
           "--target_backend", "qwen_chat", "--target_model", QWEN_MODEL,
           "--optimizer_backend", "qwen_chat", "--optimizer_model", QWEN_MODEL,
           "--test_env_num", "1", "--workers", "1", "--seed", "1", "--out_root", str(out)]
    print(f"  running eval_only on 1 test item ...")
    subprocess.run(cmd, cwd=str(SKILLOPT), env=env, check=False)
    summ = out / "eval_summary.json"
    if summ.is_file():
        print(f"  STAGE C eval_summary: {summ.read_text().strip()}")
    else:
        print("  STAGE C: no eval_summary produced")


if __name__ == "__main__":
    g = stage_b()
    stage_c(g)
    print("=== SKELETON SMOKE COMPLETE ===")
