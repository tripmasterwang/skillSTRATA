"""From-zero curate — evolve the 3-layer Skill Strata from execution trajectories.

This is the real "learn from scratch" pipeline (no gradients, no RL). Starting from an EMPTY
graph (S0), one round is:

    rollout(agent on train)  -> trajectories
        -> distill(LLM)      -> candidate Fragments   (our MAP: knowledge is written here)
        -> integrate         -> capability graph: INSERT new / MERGE near-duplicates / SPLIT
                                divergent, + trace evidence + governance provenance
        -> validation gate    -> accept the round's INSERTs only if val score strictly improves,
                                else revert them (rejected-edit buffer in governance).

Repeat for E rounds. This replaces Trace2Skill's monolithic REDUCE seam with graph construction,
and is the mechanism that makes "from a blank seed" real and SkillOpt-comparable.

The LLM ``distill_fn`` and the agent ``rollout_fn`` / ``val_score_fn`` are INJECTED callables, so
the graph logic in this module is deterministic and unit-testable offline; the server driver
(``script/run_curate.sh`` + ``skillos/curate_driver``) supplies the API-backed implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import operations as ops
from .embedding import Embedder, cosine
from .graph import SkillGraph
from .schema import GovernanceNode, Granularity, SkillNode, Status, slugify


@dataclass
class Fragment:
    """A candidate capability distilled from trajectories (the output of our MAP step)."""
    name: str
    description: str
    body: str
    task_types: list[str] = field(default_factory=list)
    evidence_traces: list[str] = field(default_factory=list)
    kind: str = "skill"            # "skill" (success pattern) | "fix" (failure-derived guard)


# --------------------------------------------------------------------------- integrate
def integrate_fragments(graph: SkillGraph, fragments: list[Fragment], *,
                        sim_threshold: float = 0.80, embedder: Embedder | None = None) -> dict:
    """Fold distilled fragments into the capability graph.

    * near-duplicate of an existing node (cosine >= sim_threshold) -> MERGE/consolidate into it
      (append evidence, union task_types, bump heat) — keeps the library from ballooning.
    * otherwise -> INSERT as a CANDIDATE node (the validation gate decides if it survives).

    Returns {"inserted": [...], "merged": [...]}.
    """
    emb = embedder or graph.embedder
    inserted: list[str] = []
    merged: list[str] = []
    for fr in fragments:
        vec = emb.embed(f"{fr.name}. {fr.description} {fr.body}")
        best_id, best_s = None, 0.0
        for nid, node in graph.nodes.items():
            if node.status == Status.RETIRED or not node.embedding:
                continue
            s = cosine(vec, node.embedding)
            if s > best_s:
                best_id, best_s = nid, s

        if best_id is not None and best_s >= sim_threshold:
            node = graph.nodes[best_id]
            node.evidence_traces += [t for t in fr.evidence_traces if t not in node.evidence_traces]
            for tt in fr.task_types:
                if tt not in node.task_types:
                    node.task_types.append(tt)
            node.heat.n_visit += 1
            merged.append(best_id)
            graph.add_rule(GovernanceNode(
                id=slugify(f"merge_{best_id}_{graph.step}_{len(merged)}"), kind="merge_decision",
                statement=f"fragment '{fr.name}' folded into {best_id} (sim {best_s:.2f})",
                targets=[best_id]))
        else:
            nid, base, k = slugify(fr.name), slugify(fr.name), 1
            while nid in graph.nodes:
                k += 1
                nid = f"{base}-{k}"
            node = SkillNode.make(fr.name, id=nid, description=fr.description, body=fr.body,
                                  task_types=list(fr.task_types), granularity=Granularity.ATOMIC,
                                  status=Status.CANDIDATE)
            node.evidence_traces = list(fr.evidence_traces)
            node.embedding = vec
            ops.insert(graph, node)
            inserted.append(nid)
            graph.add_rule(GovernanceNode(
                id=slugify(f"insert_{nid}_{graph.step}"), kind="insert_decision",
                statement=f"insert '{fr.name}' from {len(fr.evidence_traces)} trajectory evidence(s)",
                targets=[nid]))
    return {"inserted": inserted, "merged": merged}


# --------------------------------------------------------------------------- split
def split_divergent(graph: SkillGraph, *, min_task_types: int = 3, min_body: int = 600) -> list[str]:
    """SPLIT a node that has grown to cover too many distinct task-types (a sign it conflates
    several capabilities) into per-task-type children. Returns ids that were split."""
    split_ids: list[str] = []
    for nid in list(graph.nodes):
        node = graph.nodes.get(nid)
        if node is None or node.status == Status.RETIRED:
            continue
        if len(node.task_types) >= min_task_types and len(node.body) >= min_body:
            children = [
                SkillNode.make(f"{node.name} ({tt})", id=f"{nid}--{slugify(tt)}",
                               description=f"{node.description} [{tt}]", body=node.body,
                               task_types=[tt], granularity=Granularity.ATOMIC,
                               status=node.status)
                for tt in node.task_types
            ]
            if ops.split(graph, nid, children).ok:
                split_ids.append(nid)
                graph.add_rule(GovernanceNode(
                    id=slugify(f"split_{nid}_{graph.step}"), kind="split_decision",
                    statement=f"split {nid} across {len(children)} task-types", targets=[nid]))
    return split_ids


# --------------------------------------------------------------------------- validation gate
def validation_gate(graph: SkillGraph, round_inserts: list[str], val_score_fn, *,
                    baseline_score: float) -> tuple[bool, float]:
    """SkillOpt-style gate: keep this round's INSERTs only if they strictly improve the val score.

    The round's inserts are CANDIDATE; the router only routes DEPLOYED/VALIDATED skills, so we
    tentatively DEPLOY them first — otherwise the val rollout could never see the new skills and
    the gate could never accept. Accept -> keep them DEPLOYED. Reject -> RETIRE them and log a
    rejected-edit record in governance. Returns (accepted, score_to_carry_forward).
    """
    for nid in round_inserts:                       # tentatively deploy so val can route them
        if nid in graph.nodes and graph.nodes[nid].status == Status.CANDIDATE:
            graph.nodes[nid].status = Status.DEPLOYED
    score = val_score_fn(graph)
    if score > baseline_score:
        graph.add_rule(GovernanceNode(
            id=slugify(f"accept_round_{graph.step}"), kind="accept",
            statement=f"round accepted: val {score:.3f} > baseline {baseline_score:.3f}",
            targets=list(round_inserts)))
        return True, score
    for nid in round_inserts:
        if nid in graph.nodes:
            graph.nodes[nid].status = Status.RETIRED
    graph.add_rule(GovernanceNode(
        id=slugify(f"reject_round_{graph.step}"), kind="rejected_edit",
        statement=f"round rejected: val {score:.3f} !> baseline {baseline_score:.3f}",
        targets=list(round_inserts)))
    return False, baseline_score


# --------------------------------------------------------------------------- driver
def curate(graph: SkillGraph, rounds: int, train_tasks, distill_fn, rollout_fn, val_score_fn, *,
           embedder: Embedder | None = None, do_split: bool = True) -> list[dict]:
    """Full from-zero curate loop over E rounds, starting from whatever ``graph`` is (use an empty
    SkillGraph for true from-scratch). Injected callables:

      rollout_fn(graph, train_tasks) -> trajectories   (run the agent on train with the current graph)
      distill_fn(trajectories)       -> list[Fragment] (LLM authors candidate capabilities)
      val_score_fn(graph)            -> float          (route the graph on val, return a scalar score)

    Returns a per-round history (the "success ↑ / library grows / synth ↓" evidence).
    """
    history: list[dict] = []
    baseline = val_score_fn(graph)                       # S0 (blank seed) validation score
    for r in range(rounds):
        graph.tick()
        trajectories = rollout_fn(graph, train_tasks)
        fragments = distill_fn(trajectories)
        res = integrate_fragments(graph, fragments, embedder=embedder)
        if do_split:
            split_divergent(graph)
        accepted, score = validation_gate(graph, res["inserted"], val_score_fn,
                                           baseline_score=baseline)
        if accepted:
            baseline = score
        history.append({
            "round": r,
            "inserted": len(res["inserted"]),
            "merged": len(res["merged"]),
            "accepted": accepted,
            "val": round(score, 4),
            "deployed": len([n for n in graph.nodes.values() if n.status == Status.DEPLOYED]),
        })
    return history
