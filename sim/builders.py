"""Build each method's skill store from the same world, then hand back a router.

All methods see the *same* trace-derived material (the world's atomics). They differ only in
how that material is organized and routed — which is exactly the variable the proposal isolates.

Methods (proposal §Baselines):
  * no_skill      — empty store.
  * trace2skill   — one monolith per domain (concat of every atomic), full-load.
  * flat_bank     — one node per atomic, no edges, BM25 top-k.
  * pruning       — flat bank + heat-based RETIRE (no split, no graph routing).
  * skillos       — monoliths SPLIT into atomics + dependency edges + dependency-aware routing.
  * skillos_nosplit / skillos_noroute / ... — ablation variants (see run_ablations).
"""

from __future__ import annotations

from skillos import (
    SkillGraph, SkillNode, Granularity, Status, EdgeType,
    GraphRouter, FlatRouter, LifecycleManager, split,
)
from .tasks import World, DOMAINS


def _deploy(node: SkillNode, tokens: int, task_types: list[str]) -> SkillNode:
    node.status = Status.DEPLOYED
    node.heat.token_cost = tokens
    node.task_types = task_types
    node.heat.coverage = len(task_types)
    return node


def _domain_task_types(world: World, domain: str) -> list[str]:
    return [k for k, tt in world.task_types.items() if tt.domain == domain]


def _atomic_task_types(world: World, atomic_id: str) -> list[str]:
    return [k for k, tt in world.task_types.items() if atomic_id in tt.required]


# --------------------------------------------------------------------- builders
def build_no_skill(world: World) -> tuple[SkillGraph, object]:
    g = SkillGraph()
    return g, _NullRouter()


def build_monoliths(world: World) -> SkillGraph:
    """One fat skill per domain = what Trace2Skill's hierarchical merge produces."""
    g = SkillGraph()
    for d in DOMAINS:
        atoms = world.atomics_in(d)
        body = "\n\n".join(a.body for a in atoms)
        tokens = sum(a.tokens for a in atoms)
        node = SkillNode.make(
            id=f"monolith_{d}", name=f"{d} general skill",
            description=f"All {d} capabilities in one document",
            body=body, granularity=Granularity.PLAN,
        )
        g.add_skill(node)
        _deploy(node, tokens, _domain_task_types(world, d))
    return g


def build_trace2skill(world: World) -> tuple[SkillGraph, object]:
    g = build_monoliths(world)
    # Trace2Skill loads the single most-relevant monolith document (one skill family per run,
    # cf. ALLOWED_SKILL_DIR_NAMES) — its whole domain doc, dependencies and local rules included.
    return g, FlatRouter(g, k=1, mode="bm25")


def build_flat_bank(world: World, k: int = 6) -> tuple[SkillGraph, object]:
    g = SkillGraph()
    for a in world.atomics.values():
        node = SkillNode.make(id=a.id, name=a.id, description=a.id, body=a.body,
                              granularity=Granularity.ATOMIC)
        g.add_skill(node)
        _deploy(node, a.tokens, _atomic_task_types(world, a.id))
    return g, FlatRouter(g, k=k, mode="bm25")


def build_pruning(world: World, k: int = 6) -> tuple[SkillGraph, object, LifecycleManager]:
    g, _ = build_flat_bank(world, k=k)
    # pruning-only: shrink the bank by dropping cold/low-utility skills, but no split/graph/route
    lc = LifecycleManager(g, retire_floor=0.2, prune_cold=True)
    return g, FlatRouter(g, k=k, mode="bm25"), lc


def build_skillos(
    world: World, *, do_split: bool = True, do_route: bool = True,
    do_governance: bool = True, hop: int = 1, top_seeds: int = 3,
    hold_out: int = 0, tta: bool = False,
) -> tuple[SkillGraph, object, LifecycleManager]:
    """Monoliths -> SPLIT into atomics -> dependency edges -> dependency-aware routing.

    ``hold_out`` removes, per domain, the K most-needed atomics from the deployed pool — they
    are needed by tasks but were never consolidated into a routable skill (a capability gap).
    ``tta`` enables test-time synthesis to reassemble them on the fly from trace evidence.
    """
    g = build_monoliths(world)

    if do_split:
        for d in DOMAINS:
            mono_id = f"monolith_{d}"
            children = []
            for a in world.atomics_in(d):
                children.append(SkillNode.make(
                    id=a.id, name=a.id, description=a.id, body=a.body,
                    granularity=Granularity.ATOMIC,
                ))
            split(g, mono_id, children)            # exercises the real SPLIT op
            g.nodes[mono_id].status = Status.RETIRED   # monolith no longer routed
            for a, child in zip(world.atomics_in(d), children):
                _deploy(g.nodes[child.id], a.tokens, _atomic_task_types(world, a.id))

        # capability edges: the true atomic dependency DAG (skill -> its prerequisites).
        # This is what lets ROUTE recover unhinted prerequisites a flat retriever misses.
        for aid, prereqs in world.deps.items():
            if aid not in g.nodes:
                continue
            for p in prereqs:
                if p in g.nodes:
                    g.link(aid, p, EdgeType.DEPENDS_ON)
                    g.nodes[aid].dependencies.append(p)
        # composition edges among atomics co-required by a task-type (graph richness; not
        # traversed by the dependency-closure router, used by w/o-split plan routing)
        for tt in world.task_types.values():
            req = [r for r in tt.required if r in g.nodes]
            for i in range(len(req)):
                for j in range(i + 1, len(req)):
                    g.link(req[i], req[j], EdgeType.COMPOSES_WITH)
    else:
        # w/o Split: keep monoliths but still route over the graph
        pass

    # governance is a RUNTIME mechanism (no oracle): the lifecycle observes which skills are
    # repeatedly loaded on tasks that then fail, and BLOCKS_ROUTING the chronic offenders.
    # hold out the most-needed atomics per domain (capability gap: needed but not deployed)
    if hold_out > 0:
        for d in DOMAINS:
            atoms = sorted(world.atomics_in(d), key=lambda a: -len(_atomic_task_types(world, a.id)))
            for a in atoms[:hold_out]:
                if a.id in g.nodes:
                    g.nodes[a.id].status = Status.RETIRED   # not routable -> a gap to fill

    lc = LifecycleManager(
        g, retire_floor=0.15, govern=do_governance,
        block_min_trials=8, block_success_rate=0.30,   # conservative: only egregious offenders
    )
    if do_route:
        router = GraphRouter(g, top_seeds=top_seeds, hop=hop, tta=tta)
    else:
        router = FlatRouter(g, k=6, mode="bm25")   # ablation: graph store but flat retrieval
    return g, router, lc


class _NullRouter:
    def route(self, task: str, task_type: str = ""):
        from skillos import Route
        return Route(nodes=[], excluded=[])
