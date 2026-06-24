"""SkillOS core data schema.

Two families of types live here:

1. The **SkillOS node/edge model** (`SkillNode`, `Edge`, enums) — the unit the graph store
   governs. `SkillNode` mirrors the YAML in ``skillos_proposal.md`` ("Skill Node Example")
   and adds *stable IDs* plus lifecycle/heat counters.

2. The **Trace2Skill interchange** (`PatchEdit`, `Patch`) — mirrored verbatim from
   ``Trace2Skill/skill_evolver/parallel_evolving_agent.py:64`` so SkillOS can ingest the
   output of the unchanged Trace2Skill MAP phase and route each edit into the graph instead
   of feeding it to the monolithic LLM merge.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class Granularity(str, Enum):
    """Skill granularity in the capability graph (proposal §Capability Graph)."""

    ATOMIC = "atomic"          # smallest reusable unit (e.g. date_normalization)
    FUNCTIONAL = "functional"  # a coherent sub-capability (e.g. data_cleaning)
    PLAN = "plan"              # plan-level / task-type skill (e.g. table_qa)


class Status(str, Enum):
    """Lifecycle status (proposal §Skill Lifecycle; MemoryOS tier analogy).

    raw trace -> patch -> CANDIDATE -> VALIDATED -> DEPLOYED -> (SPLIT/MERGED/RETIRED)
    """

    CANDIDATE = "candidate"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    RETIRED = "retired"


class EdgeType(str, Enum):
    """Edge types across the three layers (proposal §Hierarchical Graph Structure)."""

    # capability graph
    DEPENDS_ON = "depends_on"
    COMPOSES_WITH = "composes_with"
    ALTERNATIVE_TO = "alternative_to"
    CONFLICTS_WITH = "conflicts_with"
    PARENT_CHILD = "parent_child"
    # trace graph
    TEMPORAL_ORDER = "temporal_order"
    CO_OCCURRENCE = "co_occurrence"
    CAUSED_FAILURE = "caused_failure"
    FIXED_BY = "fixed_by"
    # governance graph + cross-layer
    SUPPORTED_BY_TRACE = "supported_by_trace"  # governance/skill -> trace
    APPLIES_TO_SKILL = "applies_to_skill"      # governance rule -> skill
    BLOCKS_ROUTING = "blocks_routing"          # governance rule -> skill
    PROMOTES_SKILL = "promotes_skill"          # governance rule -> skill
    EVIDENCE_FOR = "evidence_for"              # trace -> capability (cross-layer)


def slugify(text: str) -> str:
    """Deterministic stable-ID generator (fixes G-Memory's raw-task-string node IDs)."""
    s = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    return s[:64] or "node"


# ---------------------------------------------------------------------------
# SkillOS node / edge model
# ---------------------------------------------------------------------------
@dataclass
class HeatStats:
    """Per-skill usage counters consumed by ``skillos.heat`` (MemoryOS-derived)."""

    success_count: int = 0
    failure_count: int = 0
    n_visit: int = 0                 # invocations (MemoryOS N_visit)
    coverage: int = 0               # distinct task-types touched (MemoryOS L_interaction)
    token_cost: int = 0             # mean loaded tokens when active
    last_used_step: int = -1        # logical clock of last activation (for recency decay)

    @property
    def trials(self) -> int:
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        return self.success_count / self.trials if self.trials else 0.0


@dataclass
class SkillNode:
    """A modular skill in the capability graph.

    Field names follow ``skillos_proposal.md`` "Skill Node Example"; ``id`` is a stable slug
    (not the raw description, unlike G-Memory) so MAP/TRANSLATE can address it reliably.
    """

    id: str
    name: str
    granularity: Granularity = Granularity.ATOMIC
    description: str = ""
    body: str = ""                                  # the skill text (Trace2Skill SKILL.md body)
    status: Status = Status.CANDIDATE
    parents: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    task_types: list[str] = field(default_factory=list)  # which task-types it serves
    heat: HeatStats = field(default_factory=HeatStats)
    evidence_traces: list[str] = field(default_factory=list)
    embedding: list[float] | None = None

    @classmethod
    def make(cls, name: str, **kw: Any) -> "SkillNode":
        nid = kw.pop("id", None) or slugify(name)
        return cls(id=nid, name=name, **kw)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["granularity"] = self.granularity.value
        d["status"] = self.status.value
        d.pop("embedding", None)
        return d


@dataclass
class Edge:
    src: str
    dst: str
    type: EdgeType
    weight: float = 1.0

    def key(self) -> tuple[str, str, str]:
        return (self.src, self.dst, self.type.value)


@dataclass
class TraceNode:
    """Execution-level evidence in the trace graph (proposal §Trace Graph)."""

    id: str
    task_id: str
    task_type: str
    success: bool
    steps: list[str] = field(default_factory=list)
    fail_reason: str = ""
    used_skills: list[str] = field(default_factory=list)


@dataclass
class GovernanceNode:
    """A higher-level rule/decision in the governance graph (proposal §Governance Graph)."""

    id: str
    kind: str          # rule | split_decision | merge_decision | retirement_signal
    statement: str
    targets: list[str] = field(default_factory=list)  # skill ids it applies to


# ---------------------------------------------------------------------------
# Trace2Skill interchange (mirrored from parallel_evolving_agent.py:64)
# ---------------------------------------------------------------------------
@dataclass
class PatchEdit:
    """A single edit op within a patch — identical fields to Trace2Skill's PatchEdit."""

    file: str
    op: str  # insert_after, insert_before, append_to_section, replace_in_section,
    #          add_section, delete_section, create, delete_file
    target_section: str = ""
    target_text: str = ""
    content: str = ""
    old_text: str = ""
    after_section: str = ""


@dataclass
class Patch:
    """A patch proposed by Trace2Skill's MAP phase (mirrored)."""

    reasoning: str
    edits: list[PatchEdit]
    changelog_entries: list[str] = field(default_factory=list)
    batch_index: int = -1
    raw_json: dict = field(default_factory=dict)
    # SkillOS extension: carry provenance so edits can be routed to graph nodes.
    task_id: str = ""
    task_type: str = ""
