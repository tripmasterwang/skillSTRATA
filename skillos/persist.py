"""Persist / restore a Skill Strata graph to JSON.

Used to (a) carry the evolving graph across curate rounds and (b) hand the frozen, trained graph
from the train phase to the test phase (the agent loads it via ``SKILLSTRATA_GRAPH_PATH``).
Saves the capability nodes + capability edges + governance decisions; embeddings are recomputed on
load (cheap, deterministic with the hash embedder).
"""

from __future__ import annotations

import json

from .embedding import Embedder
from .graph import SkillGraph
from .schema import EdgeType, Granularity, GovernanceNode, SkillNode, Status


def save_graph(graph: SkillGraph, path: str) -> None:
    data = {
        "skills": [n.to_dict() for n in graph.nodes.values()],
        "capability_edges": [
            {"src": u, "dst": v, "type": d.get("type"), "weight": d.get("weight", 1.0)}
            for u, v, d in graph.capability.edges(data=True)
        ],
        "governance": [
            {"id": r.id, "kind": r.kind, "statement": r.statement, "targets": list(r.targets),
             # checkpoint verify-loop spec (kept so the frozen graph carries its guards to test)
             "postcondition": r.postcondition, "max_retries": r.max_retries,
             "repair_hint": r.repair_hint}
            for r in graph.rules.values()
        ],
        "stats": graph.stats(),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def load_graph(path: str, embedder: Embedder | None = None) -> SkillGraph:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    g = SkillGraph(embedder=embedder or Embedder())

    # pass 1: materialize all nodes (no edges yet, so dependency targets always exist in pass 2)
    for sd in data.get("skills", []):
        node = SkillNode.make(
            sd["name"], id=sd["id"], description=sd.get("description", ""), body=sd.get("body", ""),
            task_types=list(sd.get("task_types", [])), dependencies=list(sd.get("dependencies", [])),
            parents=list(sd.get("parents", [])), conflicts=list(sd.get("conflicts", [])),
            granularity=Granularity(sd.get("granularity", "atomic")),
            status=Status(sd.get("status", "candidate")),
        )
        node.embedding = g.embedder.embed(f"{node.name}. {node.description} {node.body}")
        g.nodes[node.id] = node
        g.capability.add_node(node.id, kind="skill")

    # pass 2: restore capability edges exactly as saved (DEPENDS_ON etc.)
    for e in data.get("capability_edges", []):
        if e["src"] in g.nodes and e["dst"] in g.nodes:
            g.capability.add_edge(e["src"], e["dst"], type=e["type"], weight=e.get("weight", 1.0))

    for r in data.get("governance", []):
        rule = GovernanceNode(id=r["id"], kind=r["kind"], statement=r["statement"],
                              targets=list(r.get("targets", [])),
                              postcondition=r.get("postcondition", ""),
                              max_retries=r.get("max_retries", 2),
                              repair_hint=r.get("repair_hint", ""))
        if rule.kind == "checkpoint":
            # restore as a GUARDS_SKILL guard (not the default APPLIES_TO_SKILL) so the router's
            # guarding_checkpoints() lookup finds it and the test phase runs the verify-loop.
            g.rules[rule.id] = rule
            g.governance.add_node(rule.id, kind="rule")
            for sid in rule.targets:
                g.link(rule.id, sid, EdgeType.GUARDS_SKILL)
        else:
            g.add_rule(rule)
    return g
