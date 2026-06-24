"""CLISkillStrataAgent — per-task SkillStrata routing over a capability graph.

Trace2Skill's ``cli_skill_preloaded`` injects ONE monolithic SKILL.md into every task's
system prompt (its REDUCE output). SkillStrata replaces that seam: it keeps the same skill
knowledge decomposed into a capability graph (``skillos.spreadsheet_capability``) and, per
task, lets a ``GraphRouter`` activate only the *minimal executable subgraph* — the seed
skills plus their dependency closure — so each task sees scope-appropriate guidance instead
of everything. This is the real-benchmark instantiation of the routing the sim exercises.

Three router modes (env ``SKILLSTRATA_ROUTER``) share ONE capability graph so any accuracy
gap is attributable to routing, not to different skill content:
  * ``graph``  (default) — GraphRouter: type-aware seeds + DEPENDS_ON closure + governance.
  * ``full``             — FlatRouter(full): inject ALL fragments = monolithic-122B baseline.
  * ``bm25``             — FlatRouter(bm25): flat top-k retrieval, no graph edges.

Routing happens at the top of ``run()`` (before ``_ensure_agent`` bakes the system prompt),
and the cached ReActAgent is invalidated so the per-task prompt takes effect. Each parallel
worker owns its own agent instance and processes tasks sequentially, so the per-task state
stored on ``self`` is thread-safe.
"""

from __future__ import annotations

import os
import sys

from ..system_prompts import render_full_system_prompt
from .cli_skill_preloaded_agent import CLISkillPreloadedAgent, SKILLS_DIR


def _ensure_skillos_importable() -> None:
    try:
        import skillos  # noqa: F401
        return
    except ImportError:
        pass
    here = os.path.abspath(os.path.dirname(__file__))
    cur = here
    for _ in range(8):
        cur = os.path.dirname(cur)
        if os.path.isfile(os.path.join(cur, "skillos", "router.py")):
            sys.path.insert(0, cur)
            return
    raise ImportError("Could not locate the SkillOS package root (skillos/router.py) above "
                      f"{here}; set PYTHONPATH to the SkillOS project root.")


_ensure_skillos_importable()

from skillos.router import FlatRouter, GraphRouter  # noqa: E402
from skillos.spreadsheet_capability import build_spreadsheet_capability_graph  # noqa: E402


class CLISkillStrataAgent(CLISkillPreloadedAgent):
    """CLI agent that injects a per-task routed subgraph instead of a monolithic skill."""

    def __init__(self, client, skills_dir: str | None = None, **kwargs):
        # The parent discovers a SKILL.md just to satisfy init; we ignore self._skills and
        # build our own capability graph from the xlsx-122B reference fragments.
        super().__init__(client, skills_dir=skills_dir, **kwargs)

        skills_root = os.path.abspath(self.skills_dir)
        self._capability_skill_dir = os.path.join(skills_root, "xlsx-122B")

        self.graph = build_spreadsheet_capability_graph(self._capability_skill_dir)
        self.router_mode = os.environ.get("SKILLSTRATA_ROUTER", "graph").strip().lower()
        seeds = int(os.environ.get("SKILLSTRATA_SEEDS", "3"))
        type_boost = float(os.environ.get("SKILLSTRATA_TYPE_BOOST", "1.0"))

        if self.router_mode == "full":
            self.router = FlatRouter(self.graph, mode="full")
        elif self.router_mode == "bm25":
            k = int(os.environ.get("SKILLSTRATA_K", "5"))
            self.router = FlatRouter(self.graph, k=k, mode="bm25")
        else:
            self.router_mode = "graph"
            self.router = GraphRouter(self.graph, top_seeds=seeds, type_boost=type_boost)

        self._routed_content: str | None = None
        self._last_route = None

    @property
    def name(self) -> str:
        return f"cli_skillstrata_{self.router_mode}"

    # -- routing ------------------------------------------------------------------------
    def _render_route(self, route) -> str:
        """Render the activated subgraph into the skill_content slot of the v1 template."""
        if not route.nodes:
            return "(No capability module selected for this task.)"
        parts = [
            "The following capability modules were selected for THIS task by SkillStrata "
            "routing. They are the modules relevant to the task's scope; follow their guidance "
            "where it applies.",
            "",
        ]
        for nid in route.nodes:
            node = self.graph.nodes[nid]
            parts.append(node.body.strip())
            parts.append("")
        return "\n".join(parts).strip()

    def get_system_template(self) -> str:
        skill_content = self._routed_content
        if skill_content is None:
            # Pre-task (agent-setup) call: fall back to the core module so the prompt is valid.
            core = self.graph.nodes.get("core-solve")
            skill_content = core.body.strip() if core else "(No skill loaded)"
        return render_full_system_prompt(
            "cli_skill_preloaded_full_system_v1.txt",
            skill_content=skill_content,
            skill_dir=self._capability_skill_dir,
        )

    def run(self, context):
        # Route BEFORE the parent builds/caches the ReActAgent (which bakes the system prompt).
        route = self.router.route(getattr(context, "instruction", "") or "",
                                  getattr(context, "instruction_type", "") or "")
        self._last_route = route
        self._routed_content = self._render_route(route)
        # Invalidate the cached agent so the per-task system prompt is used.
        self._agent = None
        return super().run(context)
