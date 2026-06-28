"""Skill routing — the test-time ROUTE operation and its baselines.

Two strategies share one interface so the ablation "w/o Graph Routing" is a one-line swap:

  * ``GraphRouter``  — SkillOS: seed by similarity, expand 1-hop (G-Memory traversal),
    take the **dependency closure**, drop governance-blocked & conflicting skills.
    Activates a *minimal executable subgraph* (proposal §Routing Output).
  * ``FlatRouter``   — baseline: flat BM25 / embedding top-k over skill bodies, no edges.
    This is what Trace2Skill full-load or a flat skill bank does
    (``cli_skill_preloaded_agent.py:get_system_template`` injects everything / top-k).

Both return a ``Route`` describing the activated subgraph + excluded skills, mirroring the
proposal's "Routing Output" JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rank_bm25 import BM25Okapi

from .embedding import cosine
from .graph import SkillGraph
from .schema import EdgeType, SkillNode, Status


@dataclass
class Route:
    nodes: list[str]
    edges: list[tuple[str, str, str]] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    loaded_tokens: int = 0
    synthesized: list[str] = field(default_factory=list)  # ids composed at test time (TTA)
    # node_id -> the checkpoint guarding it; the executor runs skillos.verify.node_verifier_loop
    # at these (error-prone) nodes instead of executing them once and hoping.
    checkpoints: dict = field(default_factory=dict)

    def render(self) -> str:
        """What gets injected into the executor system prompt (Trace2Skill seam)."""
        return "\n\n".join(self._bodies)

    _bodies: list[str] = field(default_factory=list)


def _candidate_pool(graph: SkillGraph) -> list[SkillNode]:
    """Routable skills = deployed (fall back to validated if nothing deployed yet)."""
    pool = [n for n in graph.nodes.values() if n.status == Status.DEPLOYED]
    if not pool:
        pool = [n for n in graph.nodes.values() if n.status in (Status.DEPLOYED, Status.VALIDATED)]
    return pool


class GraphRouter:
    """Dependency-aware subgraph routing (SkillOS ROUTE).

    Uses the *same* base retriever as the flat baseline (BM25 over skill bodies) to pick seeds,
    then adds the SkillOS-specific step: 1-hop composition expansion + dependency closure, minus
    governance-blocked / conflicting skills. So any success/precision gap vs ``FlatRouter`` is
    attributable to the graph, not to a better retriever.
    """

    def __init__(self, graph: SkillGraph, top_seeds: int = 3, hop: int = 1, retriever: str = "bm25",
                 tta: bool = False, tta_max: int = 3, tta_min_weight: float = 3.0,
                 type_boost: float = 0.0, seed_fn=None):
        self.graph = graph
        self.top_seeds = top_seeds
        self.hop = hop
        self.retriever = retriever
        self.tta = tta                 # enable test-time skill synthesis (skillos.tta)
        self.tta_max = tta_max
        self.tta_min_weight = tta_min_weight
        # retriever="agent": replace ONLY the seed step with an injected agentic selector
        # ``seed_fn(task, task_type, pool, top_seeds) -> list[id]`` (e.g. a ReAct/LLM call). The
        # dependency closure + governance run unchanged on top, so the graph's contribution stays
        # isolable; BM25 stays the default and the fallback when the agent returns nothing usable.
        self.seed_fn = seed_fn
        # type_boost > 0 makes seeding task-type-aware: nodes whose declared task_types appear in
        # the (provided, non-oracle) task_type string get their retriever score boosted, so the
        # right *scope* (e.g. cell- vs sheet-level) is seeded even when surface keywords are sparse.
        # Default 0.0 keeps the pure-retriever behaviour the sim ablations rely on.
        self.type_boost = type_boost

    def route(self, task: str, task_type: str = "") -> Route:
        g = self.graph
        pool = _candidate_pool(g)
        if not pool:
            return Route(nodes=[], excluded=[])

        # 1) seed: pick the most relevant skills. retriever="agent" delegates this one step to an
        #    injected selector (falling back to BM25 if it returns nothing usable); otherwise use
        #    the shared BM25/embed retriever — no ground-truth task-type labels, so OOD task-types
        #    get no oracle advantage.
        seeds = self._retrieve_seeds(task, task_type, pool)

        # 2) close over DEPENDS_ON to assemble the *minimal executable subgraph*: the seeds plus
        #    every prerequisite they transitively need (proposal §Routing Output). Optionally
        #    expand 1 composition hop first (hop>1) for plan-level skills.
        if self.hop > 1:
            seeds = list(g.k_hop(seeds, hop=self.hop - 1))
        activated = g.dependency_closure(seeds)

        # 4) governance: drop blocked skills and conflict-losers
        blocked = g.blocked_skills()
        activated -= blocked
        activated = self._resolve_conflicts(activated, seeds)

        # keep only routable-status skills
        activated = {nid for nid in activated if g.nodes[nid].status in (Status.DEPLOYED, Status.VALIDATED)}

        nodes = sorted(activated)
        edges = [
            (u, v, d["type"])
            for u, v, d in g.capability.edges(data=True)
            if u in activated and v in activated
            and d["type"] in (EdgeType.DEPENDS_ON.value, EdgeType.COMPOSES_WITH.value,
                              EdgeType.PARENT_CHILD.value)
        ]
        excluded = sorted({n.id for n in pool} - activated)
        route = Route(nodes=nodes, edges=edges, excluded=excluded)
        # surface the verify-loop checkpoints guarding any activated (error-prone) node, so the
        # executor can run a node-local verify-or-rollback loop there. First checkpoint wins.
        route.checkpoints = {nid: cps[0] for nid in nodes
                             for cps in (g.guarding_checkpoints(nid),) if cps}
        route._bodies = [g.nodes[nid].body for nid in nodes]
        route.loaded_tokens = sum(g.nodes[nid].heat.token_cost or _est_tokens(g.nodes[nid]) for nid in nodes)

        # 5) test-time adaptation: reassemble missing sub-capabilities from trace evidence
        #    (skillos.tta). Composed skills are ephemeral — injected for this task only.
        if self.tta:
            from .tta import synthesize_gapfill
            pool_ids = {n.id for n in pool}
            for s in synthesize_gapfill(g, route.nodes, pool_ids,
                                        max_synth=self.tta_max, min_weight=self.tta_min_weight):
                if s.atom_id not in route.nodes:
                    route.nodes.append(s.atom_id)
                    route._bodies.append(s.body)
                    route.loaded_tokens += max(1, len(s.body) // 4)
                    route.synthesized.append(s.atom_id)
        return route

    def _retrieve_seeds(self, task: str, task_type: str, pool: list[SkillNode]) -> list[str]:
        """Pick seed skills. retriever="llm" (alias "agent") uses the injected ``seed_fn`` — a single
        LLM call that ranks the pool, NOT a ReAct loop — with a BM25 fallback so a flaky/empty call
        never tanks a task. The graph value (dependency closure + governance) runs on top regardless,
        so the seed step is intentionally a plain LLM retriever, not an agent."""
        if self.retriever in ("llm", "agent") and self.seed_fn is not None:
            try:
                ids = self.seed_fn(task, task_type, pool, self.top_seeds) or []
            except Exception:
                ids = []
            valid = [i for i in ids if i in self.graph.nodes]
            if valid:
                return valid[: self.top_seeds]
            # fall through to BM25/embed seeds when the agent returns nothing usable
        return self._scored_seeds(task, task_type, pool)

    def _scored_seeds(self, task: str, task_type: str, pool: list[SkillNode]) -> list[str]:
        g = self.graph
        if self.retriever == "embed":
            q = g.embedder.embed(task)
            scored = [(n.id, cosine(q, n.embedding) if n.embedding else 0.0) for n in pool]
        else:
            corpus = [(n.name + " " + n.description + " " + n.body).lower().split() for n in pool]
            bm = BM25Okapi(corpus)
            s = bm.get_scores(task.lower().split())
            scored = [(pool[i].id, s[i]) for i in range(len(pool))]

        # task-type-aware boost: lift nodes whose declared scope matches the provided task_type.
        if self.type_boost and task_type:
            tt = task_type.lower()
            ref = max((sc for _, sc in scored), default=0.0) or 1.0
            scored = [
                (nid, sc + (self.type_boost * ref
                            if any(t and t != "all" and t in tt for t in g.nodes[nid].task_types)
                            else 0.0))
                for nid, sc in scored
            ]
        return [nid for nid, _ in sorted(scored, key=lambda x: -x[1])[: self.top_seeds]]

    def _resolve_conflicts(self, activated: set[str], seeds: list[str]) -> set[str]:
        """If two conflicting skills are both active, drop the non-seed / lower-success one."""
        g = self.graph
        out = set(activated)
        for nid in list(activated):
            for _, other, d in g.capability.out_edges(nid, data=True):
                if d.get("type") == EdgeType.CONFLICTS_WITH.value and other in out and nid in out:
                    # keep the one that is a seed, else higher success rate
                    keep, drop = nid, other
                    if other in seeds and nid not in seeds:
                        keep, drop = other, nid
                    elif g.nodes[other].heat.success_rate > g.nodes[nid].heat.success_rate:
                        keep, drop = other, nid
                    out.discard(drop)
        return out


class FlatRouter:
    """Flat top-k retrieval baseline (no graph edges). mode = 'bm25' | 'embed' | 'full'."""

    def __init__(self, graph: SkillGraph, k: int = 5, mode: str = "bm25"):
        self.graph = graph
        self.k = k
        self.mode = mode

    def route(self, task: str, task_type: str = "") -> Route:
        g = self.graph
        pool = _candidate_pool(g)
        if not pool:
            return Route(nodes=[], excluded=[])
        if self.mode == "full":
            chosen = pool                                   # Trace2Skill full-load
        elif self.mode == "embed":
            q = g.embedder.embed(task + " " + task_type)
            ranked = sorted(pool, key=lambda n: -cosine(q, n.embedding or []))
            chosen = ranked[: self.k]
        else:  # bm25
            corpus = [(n.name + " " + n.description + " " + n.body).lower().split() for n in pool]
            bm = BM25Okapi(corpus)
            scores = bm.get_scores((task + " " + task_type).lower().split())
            order = sorted(range(len(pool)), key=lambda i: -scores[i])
            chosen = [pool[i] for i in order[: self.k]]
        nodes = sorted(n.id for n in chosen)
        route = Route(nodes=nodes, excluded=sorted({n.id for n in pool} - set(nodes)))
        route._bodies = [n.body for n in chosen]
        route.loaded_tokens = sum(n.heat.token_cost or _est_tokens(n) for n in chosen)
        return route


def _est_tokens(node: SkillNode) -> int:
    """Rough token estimate from body length (≈4 chars/token) when no measured cost yet."""
    return max(1, len(node.body) // 4)
