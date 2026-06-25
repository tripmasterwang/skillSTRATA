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

import json as _json  # noqa: E402
import re as _re  # noqa: E402
from react_agent.models import Message, ModelSettings  # noqa: E402


class CLISkillStrataAgent(CLISkillPreloadedAgent):
    """CLI agent that injects a per-task routed subgraph instead of a monolithic skill."""

    def __init__(self, client, skills_dir: str | None = None, **kwargs):
        # The parent discovers a SKILL.md just to satisfy init; we ignore self._skills and
        # build our own capability graph from the xlsx-122B reference fragments.
        super().__init__(client, skills_dir=skills_dir, **kwargs)

        skills_root = os.path.abspath(self.skills_dir)
        self._capability_skill_dir = os.path.join(skills_root, "xlsx-122B")

        # Graph source (priority):
        #   SKILLSTRATA_GRAPH_PATH set + file exists -> load the TRAINED/evolving graph (from-0 curate)
        #   SKILLSTRATA_GRAPH_PATH set + missing/empty -> start from an EMPTY graph (blank seed, round 0)
        #   unset -> legacy hand-built capability graph from xlsx-122B fragments (deprecated)
        graph_path = os.environ.get("SKILLSTRATA_GRAPH_PATH", "").strip()
        if graph_path:
            from skillos.persist import load_graph  # noqa: E402
            if os.path.isfile(graph_path):
                self.graph = load_graph(graph_path)
            else:
                from skillos.graph import SkillGraph  # noqa: E402
                self.graph = SkillGraph()  # blank seed (S0): nothing to route yet
        else:
            self.graph = build_spreadsheet_capability_graph(self._capability_skill_dir)
        self.router_mode = os.environ.get("SKILLSTRATA_ROUTER", "graph").strip().lower()
        seeds = int(os.environ.get("SKILLSTRATA_SEEDS", "3"))
        type_boost = float(os.environ.get("SKILLSTRATA_TYPE_BOOST", "1.0"))

        if self.router_mode == "full":
            self.router = FlatRouter(self.graph, mode="full")
        elif self.router_mode == "bm25":
            k = int(os.environ.get("SKILLSTRATA_K", "5"))
            self.router = FlatRouter(self.graph, k=k, mode="bm25")
        elif self.router_mode == "agent":
            # GraphRouter, but the SEED step is an LLM (qwen3.6 via self.client) instead of BM25;
            # dependency closure + governance run on top unchanged. BM25 (with type_boost) is the
            # fallback if the LLM returns nothing usable.
            self._agent_think_budget = int(os.environ.get("SKILLSTRATA_AGENT_THINK_BUDGET", "1024"))
            self.router = GraphRouter(self.graph, top_seeds=seeds, retriever="agent",
                                      type_boost=type_boost, seed_fn=self._llm_seed_fn)
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

    # -- agentic (LLM) seed retriever --------------------------------------------------
    _SEED_SYS = ("You select which skill modules to preload for an Excel/spreadsheet task. "
                 "Pick only the modules directly relevant to THIS task; prerequisite modules are "
                 "added automatically, so prefer a few precise choices over many.")

    def _llm_seed_fn(self, task, task_type, pool, top_seeds):
        """LLM-as-retriever: ask qwen3.6 which modules to seed. Returns a list of node ids
        (validated by the router; empty -> router falls back to BM25)."""
        if self.client is None:
            return []
        catalog = "\n".join(f"- {n.id}: {n.name} — {n.description}" for n in pool)
        pool_ids = {n.id for n in pool}
        user = (f"Task type: {task_type}\nTask: {task}\n\n"
                f"Available modules (id: name — description):\n{catalog}\n\n"
                f"Return ONLY a JSON array of the {top_seeds} most relevant module ids "
                f'(fewer is fine), e.g. ["formula-construction","lookup-patterns"]. No prose.')
        msgs = [Message(role="system", content=self._SEED_SYS), Message(role="user", content=user)]
        settings = ModelSettings(
            temperature=0.0, max_tokens=max(512, self._agent_think_budget + 512),
            extra_body={"enable_thinking": True, "thinking_budget": self._agent_think_budget},
        )
        try:
            reply = self.client.chat(msgs, settings) or ""
        except Exception:
            return []
        return self._parse_seed_ids(reply, pool_ids)

    @staticmethod
    def _parse_seed_ids(reply, pool_ids):
        # prefer a JSON array; fall back to exact id mentions in order of appearance.
        for frag in reversed(_re.findall(r"\[[^\[\]]*\]", reply)):
            try:
                arr = _json.loads(frag)
            except Exception:
                continue
            ids = [str(x).strip() for x in arr if str(x).strip() in pool_ids]
            if ids:
                return ids
        found = []
        for pid in pool_ids:
            m = _re.search(r"(?<![\w-])" + _re.escape(pid) + r"(?![\w-])", reply)
            if m:
                found.append((m.start(), pid))
        return [pid for _, pid in sorted(found)]

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
        # Per-task route log (so RESULTS.md can show which skills were routed for each instance).
        rd = os.environ.get("SKILLSTRATA_ROUTE_DIR", "").strip()
        if rd:
            try:
                os.makedirs(rd, exist_ok=True)
                iid = str(getattr(context, "instance_id", "") or "unknown")
                with open(os.path.join(rd, f"{iid}.json"), "w", encoding="utf-8") as fh:
                    _json.dump({"id": iid, "router": self.router_mode, "nodes": route.nodes}, fh)
            except Exception:
                pass
        # Invalidate the cached agent so the per-task system prompt is used.
        self._agent = None
        return super().run(context)
