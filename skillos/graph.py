"""The three-layer SkillOS graph.

Grounded in G-Memory's hierarchical memory (``GMemory/mas/memory/mas_memory/GMemory.py``):
  * G-Memory TaskLayer (``:352``)  -> our **capability graph** (networkx, k-hop traversal)
  * G-Memory StateChain (``common.py:53``) -> our **trace graph**
  * G-Memory InsightsManager (``:467``, correlation back-refs) -> our **governance graph**

Two improvements over the reference:
  1. **Stable node IDs** (slugs) instead of raw task strings, so edits address nodes reliably.
  2. All three layers are first-class ``networkx`` graphs with explicit cross-layer edges,
     rather than G-Memory's mix of networkx + JSON list-of-dicts.

The k-hop retrieval primitive is taken straight from
``TaskLayer.retrieve_related_task`` (``GMemory.py:404``):
``nx.single_source_shortest_path_length(graph, node, cutoff=hop)``.
"""

from __future__ import annotations

import itertools
import json
import networkx as nx

from .embedding import Embedder, cosine
from .schema import (
    Edge,
    EdgeType,
    GovernanceNode,
    SkillNode,
    Status,
    TraceNode,
)


class SkillGraph:
    """Holds the trace / capability / governance layers and their cross-layer edges."""

    def __init__(self, embedder: Embedder | None = None, sim_threshold: float = 0.5):
        self.embedder = embedder or Embedder()
        self.sim_threshold = sim_threshold      # G-Memory TaskLayer.similarity_threshold (0.7)
        # capability graph: directed (dependency edges are directional)
        self.capability = nx.DiGraph()
        # trace graph: directed (temporal_order / caused_failure / fixed_by)
        self.trace = nx.DiGraph()
        # governance graph: directed (rule -> skill)
        self.governance = nx.DiGraph()
        self.nodes: dict[str, SkillNode] = {}
        self.traces: dict[str, TraceNode] = {}
        self.rules: dict[str, GovernanceNode] = {}
        self.step = 0                            # logical clock for heat recency
        # trace-layer statistics used by test-time adaptation (see record_trace):
        #   cooc[(a,b)] = how often sub-capabilities a,b co-occurred in (mostly successful) runs
        #   atom_evidence[a] = a trace fragment that demonstrates sub-capability a
        self.cooc: dict[tuple[str, str], float] = {}
        self.atom_evidence: dict[str, str] = {}

    # ------------------------------------------------------------------ tick
    def tick(self) -> int:
        self.step += 1
        return self.step

    # ------------------------------------------------------- capability layer
    def add_skill(self, node: SkillNode) -> SkillNode:
        if node.embedding is None:
            node.embedding = self.embedder.embed(f"{node.name}. {node.description} {node.body}")
        self.nodes[node.id] = node
        self.capability.add_node(node.id, kind="skill")
        # materialise declared structural edges
        for dep in node.dependencies:
            self.link(node.id, dep, EdgeType.DEPENDS_ON)
        for parent in node.parents:
            self.link(parent, node.id, EdgeType.PARENT_CHILD)
        for c in node.conflicts:
            self.link(node.id, c, EdgeType.CONFLICTS_WITH)
        # similarity edges (G-Memory TaskLayer.add_task_node vector-seeded edges)
        self._add_similarity_edges(node)
        return node

    def _add_similarity_edges(self, node: SkillNode, k: int = 8) -> None:
        sims = []
        for other_id, other in self.nodes.items():
            if other_id == node.id or other.embedding is None:
                continue
            s = cosine(node.embedding, other.embedding)
            if s >= self.sim_threshold:
                sims.append((other_id, s))
        for other_id, s in sorted(sims, key=lambda x: -x[1])[:k]:
            # alternative_to is symmetric "similar capability" — only if not already structural
            if not self.capability.has_edge(node.id, other_id):
                self.link(node.id, other_id, EdgeType.ALTERNATIVE_TO, weight=s)

    def link(self, src: str, dst: str, etype: EdgeType, weight: float = 1.0) -> None:
        layer = self._layer_for(etype)
        layer.add_edge(src, dst, type=etype.value, weight=weight)

    def unlink(self, src: str, dst: str, etype: EdgeType) -> None:
        layer = self._layer_for(etype)
        if layer.has_edge(src, dst):
            layer.remove_edge(src, dst)

    def _layer_for(self, etype: EdgeType) -> nx.DiGraph:
        trace_edges = {
            EdgeType.TEMPORAL_ORDER, EdgeType.CO_OCCURRENCE,
            EdgeType.CAUSED_FAILURE, EdgeType.FIXED_BY,
        }
        gov_edges = {
            EdgeType.SUPPORTED_BY_TRACE, EdgeType.APPLIES_TO_SKILL,
            EdgeType.BLOCKS_ROUTING, EdgeType.PROMOTES_SKILL,
        }
        if etype in trace_edges:
            return self.trace
        if etype in gov_edges:
            return self.governance
        return self.capability

    # ------------------------------------------------------------ trace layer
    def add_trace(self, trace: TraceNode) -> TraceNode:
        self.traces[trace.id] = trace
        self.trace.add_node(trace.id, kind="trace")
        for sid in trace.used_skills:
            # cross-layer evidence edge trace -> capability
            self.governance.add_edge(trace.id, sid, type=EdgeType.EVIDENCE_FOR.value)
            if sid in self.nodes:
                self.nodes[sid].evidence_traces.append(trace.id)
        return trace

    # ------------------------------------------------------- governance layer
    def add_rule(self, rule: GovernanceNode) -> GovernanceNode:
        self.rules[rule.id] = rule
        self.governance.add_node(rule.id, kind="rule")
        for sid in rule.targets:
            self.governance.add_edge(rule.id, sid, type=EdgeType.APPLIES_TO_SKILL.value)
        return rule

    # ----------------------------------------------- trace layer (test-time adaptation)
    def record_trace(
        self,
        atom_ids: list[str],
        success: bool,
        bodies: dict[str, str] | None = None,
        w_success: float = 2.0,
        w_fail: float = 0.5,
    ) -> TraceNode:
        """Write one execution trace into the trace graph and update co-occurrence stats.

        ``atom_ids`` = the sub-capabilities the run actually exercised (parsed from the
        execution log; in the simulator = the task's needed atomics). This is the *evidence*
        layer: it records what happened, including sub-steps that have **no deployed skill yet**.
        Those become the raw material the test-time synthesizer reassembles into a skill when a
        new-but-overlapping task arrives (lego-style). Successful runs weigh more (``w_success``).
        """
        bodies = bodies or {}
        tid = f"trace_{len(self.traces)}"
        tr = TraceNode(id=tid, task_id="", task_type="", success=success, used_skills=list(atom_ids))
        self.traces[tid] = tr
        self.trace.add_node(tid, kind="trace", success=success)
        w = w_success if success else w_fail
        for a in atom_ids:
            self.trace.add_node(a, kind="atom_evidence")
            self.trace.add_edge(tid, a, type="contains")           # trace -> sub-capability
            if a in bodies:
                self.atom_evidence.setdefault(a, bodies[a])
        # co-occurrence edges between sub-capabilities that succeeded together
        for a, b in itertools.combinations(sorted(set(atom_ids)), 2):
            key = (a, b)
            self.cooc[key] = self.cooc.get(key, 0.0) + w
            if self.trace.has_edge(a, b):
                self.trace[a][b]["weight"] = self.trace[a][b].get("weight", 0.0) + w
            else:
                self.trace.add_edge(a, b, type=EdgeType.CO_OCCURRENCE.value, weight=w)
        return tr

    def trace_cooccurring(
        self, seed_ids: list[str], exclude: set[str], top_m: int = 3, min_weight: float = 2.0,
    ) -> list[tuple[str, float]]:
        """Sub-capabilities that frequently co-occurred with the seeds (descending weight).

        This is the capability->trace down-drill: given the routed skills, walk the trace
        co-occurrence statistics to find what *usually accompanies them in successful runs* but
        is not already in the activated set — the gap the synthesizer should fill.
        """
        seeds = set(seed_ids)
        score: dict[str, float] = {}
        for (a, b), w in self.cooc.items():
            if a in seeds and b not in seeds and b not in exclude:
                score[b] = score.get(b, 0.0) + w
            if b in seeds and a not in seeds and a not in exclude:
                score[a] = score.get(a, 0.0) + w
        ranked = [(k, v) for k, v in score.items() if v >= min_weight]
        return sorted(ranked, key=lambda x: -x[1])[:top_m]

    def blocked_skills(self) -> set[str]:
        """Skills a governance rule marks BLOCKS_ROUTING (conflict / quarantine)."""
        out = set()
        for u, v, d in self.governance.edges(data=True):
            if d.get("type") == EdgeType.BLOCKS_ROUTING.value:
                out.add(v)
        return out

    # --------------------------------------------------------------- queries
    #: edges the router may walk to assemble an *executable* neighborhood
    _EXEC_EDGES = {
        EdgeType.DEPENDS_ON.value,
        EdgeType.COMPOSES_WITH.value,
        EdgeType.PARENT_CHILD.value,
    }

    def k_hop(self, seeds: list[str], hop: int = 1) -> set[str]:
        """G-Memory retrieve_related_task k-hop expansion (GMemory.py:404).

        Walk only dependency/composition/parent-child edges (undirected) up to ``hop`` from
        each seed. ALTERNATIVE_TO (similarity) and CONFLICTS_WITH edges are intentionally
        excluded — expanding over them would pull in distractors / conflict hazards.
        """
        exec_view = nx.restricted_view(
            self.capability,
            nodes=[],
            edges=[
                (u, v)
                for u, v, d in self.capability.edges(data=True)
                if d.get("type") not in self._EXEC_EDGES
            ],
        ).to_undirected(as_view=True)
        related: set[str] = set(seeds)
        for s in seeds:
            if s in exec_view:
                related.update(
                    nx.single_source_shortest_path_length(exec_view, s, cutoff=hop).keys()
                )
        return related

    def dependency_closure(self, seeds: list[str]) -> set[str]:
        """All transitive DEPENDS_ON of the seeds — the minimal *executable* set.

        A skill cannot run without its dependencies, so ROUTE must close over them.
        """
        closure: set[str] = set()
        stack = list(seeds)
        while stack:
            sid = stack.pop()
            if sid in closure or sid not in self.capability:
                continue
            closure.add(sid)
            for _, dst, d in self.capability.out_edges(sid, data=True):
                if d.get("type") == EdgeType.DEPENDS_ON.value and dst not in closure:
                    stack.append(dst)
        return closure

    def deployed(self) -> list[SkillNode]:
        return [n for n in self.nodes.values() if n.status == Status.DEPLOYED]

    def active(self) -> list[SkillNode]:
        return [n for n in self.nodes.values() if n.status != Status.RETIRED]

    # ----------------------------------------------------------------- stats
    def stats(self) -> dict:
        by_status: dict[str, int] = {}
        for n in self.nodes.values():
            by_status[n.status.value] = by_status.get(n.status.value, 0) + 1
        return {
            "skills_total": len(self.nodes),
            "by_status": by_status,
            "capability_edges": self.capability.number_of_edges(),
            "trace_nodes": len(self.traces),
            "governance_nodes": len(self.rules),
            "governance_edges": self.governance.number_of_edges(),
        }

    def to_json(self) -> str:
        return json.dumps(
            {
                "skills": [n.to_dict() for n in self.nodes.values()],
                "capability_edges": [
                    {"src": u, "dst": v, **d} for u, v, d in self.capability.edges(data=True)
                ],
                "stats": self.stats(),
            },
            indent=2,
        )
