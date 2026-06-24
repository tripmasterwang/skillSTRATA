"""SkillOS — a hierarchical graph-governed skill system for LLM agents.

Public API mirrors the proposal's operations. See ``CODE_DESIGN.md`` for provenance against
the three reference codebases (Trace2Skill / G-Memory / MemoryOS).
"""

from .schema import (
    SkillNode,
    TraceNode,
    GovernanceNode,
    Edge,
    EdgeType,
    Granularity,
    Status,
    HeatStats,
    Patch,
    PatchEdit,
    slugify,
)
from .graph import SkillGraph
from .embedding import Embedder, cosine
from .heat import HeatConfig, compute_skill_heat, utility
from .operations import insert, update, link, split, merge, retire, should_split, OpResult
from .router import GraphRouter, FlatRouter, Route
from .lifecycle import LifecycleManager, GateMetrics, GateDecision, verify_gate
from .evolver import GraphGovernedEvolver
from .tta import synthesize_gapfill, Synthesized
from .evolve import distill_and_consolidate

__all__ = [
    "SkillNode", "TraceNode", "GovernanceNode", "Edge", "EdgeType", "Granularity",
    "Status", "HeatStats", "Patch", "PatchEdit", "slugify",
    "SkillGraph", "Embedder", "cosine",
    "HeatConfig", "compute_skill_heat", "utility",
    "insert", "update", "link", "split", "merge", "retire", "should_split", "OpResult",
    "GraphRouter", "FlatRouter", "Route",
    "LifecycleManager", "GateMetrics", "GateDecision", "verify_gate",
    "GraphGovernedEvolver",
    "synthesize_gapfill", "Synthesized",
    "distill_and_consolidate",
]

__version__ = "0.1.0"
