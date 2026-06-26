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


def _loop_enabled() -> bool:
    """Node-local verify-loop runs only when SKILLSTRATA_VERIFY_LOOP is truthy. The driver sets it
    per phase: test/val = 1 (deployed mechanism + faithful gate), train rollout = 0 (so checkpoints
    are minted from honest, un-repaired failure rates)."""
    return os.environ.get("SKILLSTRATA_VERIFY_LOOP", "0").strip().lower() in ("1", "true", "yes", "on")


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
                    _json.dump({"id": iid, "router": self.router_mode,
                                "nodes": route.nodes,
                                "guarded": list(getattr(route, "checkpoints", {}).keys())}, fh)
            except Exception:
                pass
        # Invalidate the cached agent so the per-task system prompt is used.
        self._agent = None

        # Node-local verify-loop: if the route activated a LEARNED error-prone (guarded) skill and
        # the loop is enabled (SKILLSTRATA_VERIFY_LOOP=1 — test/val on, train off so the failure
        # signal that mints checkpoints stays honest), guard THIS task with that skill's
        # postcondition, rolling back the output workbook between attempts. Otherwise: one plain pass.
        cps = list(getattr(route, "checkpoints", {}).values())
        if not cps or not _loop_enabled():
            return super().run(context)
        return self._run_with_verify_loop(context, cps)

    # -- node-local verify-or-rollback loop --------------------------------------------
    def _run_with_verify_loop(self, context, cps):
        from skillos.verify import node_verifier_loop
        cp = self._merge_checkpoints(cps)
        base_content = self._routed_content
        out_path = os.path.abspath(context.output_file)

        def execute_fn(i, hint):
            self._routed_content = base_content + (
                f"\n\n## REPAIR (attempt {i + 1})\n{hint}" if i > 0 and hint else "")
            self._agent = None                       # re-bake prompt with repair guidance
            return super(CLISkillStrataAgent, self).run(context)

        def verify_fn(result):
            return self._verify_postcondition(context, cp.postcondition, result)

        def snapshot_fn():
            return open(out_path, "rb").read() if os.path.exists(out_path) else None

        def restore_fn(tok):                          # roll the workbook back to node entry
            if tok is None:
                if os.path.exists(out_path):
                    os.remove(out_path)
            else:
                with open(out_path, "wb") as fh:
                    fh.write(tok)

        outcome = node_verifier_loop(cp, execute_fn, verify_fn,
                                     snapshot_fn=snapshot_fn, restore_fn=restore_fn)
        return outcome.result if outcome.result is not None else {
            "success": False, "answer": "", "turns": 0, "error": "verify-loop produced no result"}

    @staticmethod
    def _merge_checkpoints(cps):
        """Fold all guards on a route into one spec (numbered postconditions, max budget)."""
        from skillos.schema import GovernanceNode
        cps = [c for c in cps if c is not None]
        if len(cps) == 1:
            return cps[0]
        post = "; ".join(f"({i + 1}) {c.postcondition}" for i, c in enumerate(cps) if c.postcondition)
        return GovernanceNode(
            id="merged_checkpoint", kind="checkpoint", statement="merged route guards",
            targets=[c.targets[0] for c in cps if c.targets],
            postcondition=post, max_retries=max((c.max_retries for c in cps), default=2),
            repair_hint=" ".join(c.repair_hint for c in cps if c.repair_hint))

    def _verify_postcondition(self, context, postcondition, result):
        """LLM judge: does the saved output satisfy the guarded skill's sub-goal? Fail-open on a
        flaky verifier (don't tank a completed task). Returns (ok, feedback)."""
        if not result or not result.get("success"):
            return (False, (result or {}).get("error") or "agent did not produce a valid output")
        if self.client is None or not postcondition:
            return (True, "")
        view = self._dump_output(context)
        user = (f"Task: {getattr(context, 'instruction', '')}\n"
                f"Answer position: {getattr(context, 'answer_position', '')}\n"
                f"Resulting output (answer region):\n{view}\n\n"
                f"Required postcondition: {postcondition}\n\n"
                'Does the output satisfy the postcondition? Reply ONLY JSON '
                '{"ok": true|false, "feedback": "<if false: what is wrong and how to fix it>"}.')
        msgs = [Message(role="system",
                        content="You strictly verify whether a spreadsheet task output meets a "
                                "stated postcondition. Be conservative: if it clearly does not, say so."),
                Message(role="user", content=user)]
        settings = ModelSettings(temperature=0.0, max_tokens=400,
                                 extra_body={"enable_thinking": False})
        try:
            reply = self.client.chat(msgs, settings) or ""
            m = _re.search(r"\{[\s\S]*\}", reply)
            o = _json.loads(m.group(0)) if m else {}
            return (bool(o.get("ok", True)), str(o.get("feedback", "")))
        except Exception:
            return (True, "")

    @staticmethod
    def _dump_output(context, max_rows: int = 40, max_cols: int = 20):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(os.path.abspath(context.output_file), data_only=True)
            lines = []
            for ws in wb.worksheets[:3]:
                lines.append(f"# sheet: {ws.title}")
                for r, row in enumerate(ws.iter_rows(values_only=True)):
                    if r >= max_rows:
                        lines.append("...")
                        break
                    lines.append("\t".join("" if c is None else str(c) for c in row[:max_cols]))
            return "\n".join(lines)[:4000]
        except Exception as e:
            return f"(could not read output workbook: {e})"
