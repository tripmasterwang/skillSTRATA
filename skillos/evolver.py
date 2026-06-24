"""GraphGovernedEvolver — the drop-in replacement for Trace2Skill's monolithic merge.

Trace2Skill consolidates MAP-phase patches with an LLM *tree-merge* into one giant SKILL.md:

    # Trace2Skill/skill_evolver/parallel_evolving_agent.py
    def run_reduce_phase(self, skill_state: dict[str, str],
                         patches: list[Patch]) -> Patch | None:   # line ~2319
        ... LLM merges 5 patches at a time, level by level, into ONE patch ...

SkillOS keeps MAP unchanged but replaces REDUCE: instead of collapsing every patch into one
document, we **route each ``PatchEdit`` to a graph node** keyed by its ``target_section`` /
``file`` (the closest thing Trace2Skill has to a node identity), creating/splitting/merging
skill nodes under governance. The monolith never forms.

Real-LLM integration (documented, not run by default)
-----------------------------------------------------
    from skill_evolver.parallel_evolving_agent import ParallelSkillEvolver
    from skillos.evolver import GraphGovernedEvolver

    class GraphTrace2Skill(ParallelSkillEvolver):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.gov = GraphGovernedEvolver()
        def run_reduce_phase(self, skill_state, patches):
            # patches are Trace2Skill Patch objects; field-compatible with skillos.schema.Patch
            self.gov.absorb(skill_state, patches)
            return None  # APPLY/VERIFY now operate per-node via self.gov.graph

Then swap ``cli_skill_preloaded_agent.get_system_template`` to inject
``GraphRouter(self.gov.graph).route(task).render()`` instead of the full SKILL.md.
"""

from __future__ import annotations

from .graph import SkillGraph
from .operations import insert, merge, should_split, split, link
from .schema import (
    EdgeType,
    Granularity,
    Patch,
    SkillNode,
    Status,
    slugify,
)
from .embedding import cosine


class GraphGovernedEvolver:
    """Absorb MAP-phase patches into the skill graph instead of merging into a monolith."""

    def __init__(self, graph: SkillGraph | None = None, dedup_threshold: float = 0.82):
        self.graph = graph or SkillGraph()
        self.dedup_threshold = dedup_threshold

    # ------------------------------------------------------------------ absorb
    def absorb(self, skill_state: dict[str, str], patches: list[Patch]) -> None:
        """Route every PatchEdit to a graph node. Same inputs as run_reduce_phase."""
        for patch in patches:
            for edit in patch.edits:
                self._route_edit(patch, edit)
        self._maybe_split_all()

    def _route_edit(self, patch: Patch, edit) -> None:
        # the section a Trace2Skill edit targets becomes the skill node identity
        section = edit.target_section or edit.after_section or edit.file or "general"
        name = section.strip().lstrip("#").strip() or "general"
        nid = slugify(name)
        body = (edit.content or "").strip()
        ttype = patch.task_type or ""

        existing = self.graph.nodes.get(nid)
        if existing is None:
            # dedup against near-duplicate nodes before creating (MemoryOS merge-or-create)
            dup = self._find_duplicate(name + " " + body)
            if dup is not None:
                existing = dup
                nid = dup.id

        if existing is None:
            node = SkillNode.make(
                name=name,
                description=name,
                body=body,
                granularity=Granularity.FUNCTIONAL,
                status=Status.CANDIDATE,
                task_types=[ttype] if ttype else [],
            )
            insert(self.graph, node)
            if patch.task_id:
                node.evidence_traces.append(patch.task_id)
        else:
            if body and body not in existing.body:
                existing.body = (existing.body + "\n\n" + body).strip()
            if ttype and ttype not in existing.task_types:
                existing.task_types.append(ttype)
            existing.heat.coverage = len(existing.task_types)
            if patch.task_id and patch.task_id not in existing.evidence_traces:
                existing.evidence_traces.append(patch.task_id)
            existing.embedding = self.graph.embedder.embed(
                f"{existing.name}. {existing.description} {existing.body}"
            )

    def _find_duplicate(self, text: str) -> SkillNode | None:
        q = self.graph.embedder.embed(text)
        best, best_s = None, 0.0
        for n in self.graph.nodes.values():
            if n.status == Status.RETIRED or n.embedding is None:
                continue
            s = cosine(q, n.embedding)
            if s > best_s:
                best, best_s = n, s
        return best if best_s >= self.dedup_threshold else None

    def _maybe_split_all(self) -> None:
        """Refactor any node that has grown into a heterogeneous monolith (SPLIT)."""
        for nid in list(self.graph.nodes):
            node = self.graph.nodes[nid]
            if node.status == Status.RETIRED:
                continue
            if should_split(node):
                children = self._propose_children(node)
                if len(children) >= 2:
                    split(self.graph, nid, children)

    def _propose_children(self, node: SkillNode) -> list[SkillNode]:
        """Heuristic split: one atomic child per task-type the monolith mixes.

        In a real-LLM run this is where Trace2Skill's MAP/TRANSLATE prompt would propose the
        decomposition; offline we split by the task-types recorded on the node so the
        simulator can measure the negative-transfer reduction the proposal predicts.
        """
        from .schema import Granularity as G

        paras = [p.strip() for p in node.body.split("\n\n") if p.strip()]
        children = []
        for i, tt in enumerate(node.task_types):
            chunk = paras[i] if i < len(paras) else (paras[0] if paras else node.description)
            children.append(
                SkillNode.make(
                    name=f"{node.name} for {tt}",
                    description=f"{node.name} specialised for {tt} tasks",
                    body=chunk,
                    granularity=G.ATOMIC,
                    task_types=[tt],
                )
            )
        return children
