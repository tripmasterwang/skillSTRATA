"""The seven SkillOS governance operations (proposal §Core Operations).

    INSERT  add a new skill node
    UPDATE  update an existing skill node
    SPLIT   refactor an oversized skill into smaller sub-skills   <- novel; no ref implements it
    MERGE   merge redundant skills                                 (cf. G-Memory _merge_rules)
    LINK    add dependency / composition / conflict edges
    RETIRE  retire low-utility / high-risk skills                  (cf. MemoryOS evict_lfu)
    ROUTE   select a minimal skill subgraph                        (see skillos.router)

SPLIT and ROUTE are what distinguish SkillOS from prior insert/update/merge/prune systems
(proposal §Core Operations: "The most important operations are SPLIT and ROUTE").

Each op returns an ``OpResult`` so the lifecycle gate can replay/accept/reject it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .embedding import cosine
from .graph import SkillGraph
from .heat import HeatConfig, utility
from .schema import (
    EdgeType,
    Granularity,
    GovernanceNode,
    SkillNode,
    Status,
    slugify,
)


@dataclass
class OpResult:
    op: str
    ok: bool
    affected: list[str] = field(default_factory=list)
    note: str = ""


# --------------------------------------------------------------------- INSERT
def insert(graph: SkillGraph, node: SkillNode) -> OpResult:
    if node.id in graph.nodes:
        return OpResult("INSERT", False, [node.id], "id already exists")
    graph.add_skill(node)
    return OpResult("INSERT", True, [node.id])


# --------------------------------------------------------------------- UPDATE
def update(graph: SkillGraph, skill_id: str, **fields) -> OpResult:
    if skill_id not in graph.nodes:
        return OpResult("UPDATE", False, [skill_id], "missing")
    node = graph.nodes[skill_id]
    for k, v in fields.items():
        setattr(node, k, v)
    if "body" in fields or "description" in fields:
        node.embedding = graph.embedder.embed(f"{node.name}. {node.description} {node.body}")
    return OpResult("UPDATE", True, [skill_id])


# ---------------------------------------------------------------------- LINK
def link(graph: SkillGraph, src: str, dst: str, etype: EdgeType, weight: float = 1.0) -> OpResult:
    if src not in graph.nodes or dst not in graph.nodes:
        return OpResult("LINK", False, [src, dst], "endpoint missing")
    graph.link(src, dst, etype, weight)
    if etype == EdgeType.DEPENDS_ON and dst not in graph.nodes[src].dependencies:
        graph.nodes[src].dependencies.append(dst)
    if etype == EdgeType.CONFLICTS_WITH and dst not in graph.nodes[src].conflicts:
        graph.nodes[src].conflicts.append(dst)
    return OpResult("LINK", True, [src, dst], etype.value)


# --------------------------------------------------------------------- SPLIT
def split(graph: SkillGraph, skill_id: str, children: list[SkillNode]) -> OpResult:
    """Refactor an oversized plan/functional skill into atomic children.

    The parent is demoted to a thin *router* node that ``PARENT_CHILD``-links its children and
    ``DEPENDS_ON`` them; each child inherits the parent's evidence and serves the task-types
    that actually exercised it. This is the operation prior systems lack — they only ever grow
    or prune a monolith, never refactor it.
    """
    if skill_id not in graph.nodes:
        return OpResult("SPLIT", False, [skill_id], "missing")
    parent = graph.nodes[skill_id]
    affected = [skill_id]
    for child in children:
        if child.id in graph.nodes:
            child.id = slugify(child.name + "_" + skill_id)
        child.parents = [skill_id]
        child.status = Status.CANDIDATE
        # children inherit the slice of evidence/task-types they cover
        child.evidence_traces = list(parent.evidence_traces)
        graph.add_skill(child)
        graph.link(skill_id, child.id, EdgeType.PARENT_CHILD)
        graph.link(skill_id, child.id, EdgeType.DEPENDS_ON)
        affected.append(child.id)
    # parent becomes a lightweight composition node
    parent.granularity = Granularity.PLAN
    parent.body = _router_stub(parent, children)
    parent.embedding = graph.embedder.embed(f"{parent.name}. {parent.description}")
    graph.add_rule(
        GovernanceNode(
            id=slugify(f"split_{skill_id}_{graph.step}"),
            kind="split_decision",
            statement=f"SPLIT {skill_id} into {[c.id for c in children]}",
            targets=affected,
        )
    )
    return OpResult("SPLIT", True, affected, f"split into {len(children)} children")


def _router_stub(parent: SkillNode, children: list[SkillNode]) -> str:
    lines = [f"# {parent.name}", parent.description, "", "## Sub-skills"]
    for c in children:
        lines.append(f"- **{c.name}**: {c.description}")
    return "\n".join(lines)


# --------------------------------------------------------------------- MERGE
def merge(graph: SkillGraph, ids: list[str], into_name: str | None = None) -> OpResult:
    """Merge redundant skills into one (cf. G-Memory _merge_rules / MemoryOS dedup).

    Union of dependencies/conflicts/task-types/evidence; heat counters summed; merged-away
    nodes are RETIRED (kept for provenance) and ALTERNATIVE_TO-redirected to the survivor.
    """
    present = [i for i in ids if i in graph.nodes]
    if len(present) < 2:
        return OpResult("MERGE", False, present, "need >=2 existing skills")
    survivor = graph.nodes[max(present, key=lambda i: graph.nodes[i].heat.success_count)]
    survivor.name = into_name or survivor.name
    for i in present:
        if i == survivor.id:
            continue
        n = graph.nodes[i]
        survivor.dependencies = sorted(set(survivor.dependencies) | set(n.dependencies))
        survivor.conflicts = sorted(set(survivor.conflicts) | set(n.conflicts))
        survivor.task_types = sorted(set(survivor.task_types) | set(n.task_types))
        survivor.evidence_traces = sorted(set(survivor.evidence_traces) | set(n.evidence_traces))
        survivor.heat.success_count += n.heat.success_count
        survivor.heat.failure_count += n.heat.failure_count
        survivor.heat.n_visit += n.heat.n_visit
        n.status = Status.RETIRED
        graph.link(i, survivor.id, EdgeType.ALTERNATIVE_TO)
    survivor.coverage = len(survivor.task_types) if hasattr(survivor, "coverage") else survivor.heat.coverage
    survivor.heat.coverage = len(survivor.task_types)
    survivor.embedding = graph.embedder.embed(f"{survivor.name}. {survivor.description} {survivor.body}")
    return OpResult("MERGE", True, present, f"merged into {survivor.id}")


# --------------------------------------------------------------------- RETIRE
def retire(
    graph: SkillGraph,
    skill_id: str | None = None,
    *,
    floor: float | None = None,
    cfg: HeatConfig | None = None,
) -> OpResult:
    """Retire a specific skill, or the lowest-utility skill below ``floor``.

    Utility = heat * success_rate (``skillos.heat.utility``) — the symmetric "read the bottom
    of the heap" extension of MemoryOS's promotion gate (MemoryOS only ever evicted by LFU).
    """
    if skill_id is not None:
        if skill_id not in graph.nodes:
            return OpResult("RETIRE", False, [skill_id], "missing")
        graph.nodes[skill_id].status = Status.RETIRED
        return OpResult("RETIRE", True, [skill_id])
    # floor-sweep: only retire skills that have been *tried enough* and proven low-value
    # (low success rate). Cold-but-reliable skills are kept — retiring them would just drop
    # coverage. This matches RETIRE's intent: evict low-utility / high-risk skills, not rare ones.
    cands = [
        n for n in graph.active()
        if n.status != Status.CANDIDATE and n.heat.trials >= 6 and n.heat.success_rate < 0.5
    ]
    if not cands:
        return OpResult("RETIRE", False, [], "no low-value skill")
    worst = min(cands, key=lambda n: utility(n, graph.step, cfg))
    if floor is not None and utility(worst, graph.step, cfg) >= floor:
        return OpResult("RETIRE", False, [worst.id], "above floor")
    worst.status = Status.RETIRED
    graph.add_rule(
        GovernanceNode(
            id=slugify(f"retire_{worst.id}_{graph.step}"),
            kind="retirement_signal",
            statement=f"RETIRE {worst.id} (utility below floor)",
            targets=[worst.id],
        )
    )
    return OpResult("RETIRE", True, [worst.id], "floor-swept")


# ------------------------------------------------------- SPLIT trigger heuristic
def should_split(node: SkillNode, max_body_tokens: int = 600, min_task_types: int = 3) -> bool:
    """A skill is a SPLIT candidate when it is large AND serves heterogeneous task-types.

    Large + single-purpose -> leave alone; large + many task-types -> it is a monolith mixing
    local rules across settings, the exact negative-transfer hazard the proposal targets.
    """
    body_tokens = len(node.body) // 4
    return body_tokens >= max_body_tokens and len(node.task_types) >= min_task_types
