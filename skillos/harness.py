"""Harness-agnostic SkillStrata block + the HarnessAdapter interface (plug-and-play).

The point of this module is that SkillStrata is NOT "a ReAct agent with an injected prompt"
(that is what SkillGraph-style baselines do). Instead it is a *system* that adapts to whatever
harness executes the task — single-agent CLI coding agents (Claude Code, Codex, mini-swe-agent)
AND multi-agent teams (LangGraph supervisor/blackboard) — by:

  1. routing a *minimal executable subgraph* PER ROLE (a multi-agent editor gets edit-skills, the
     tester gets test-skills — something a single ReAct agent cannot express), and
  2. placing the routed skills through each harness's NATIVE skill / instruction channel
     (Claude Code ``--append-system-prompt`` or a SKILL.md set, Codex ``AGENTS.md``, a node's
     system prompt for LangGraph), not a one-size task-string prefix, and
  3. wrapping the harness run in a node/session-boundary verify-or-rollback loop and observing the
     trajectory for the offline curate loop.

The GCD every harness exposes (see swepro_eval ``_swe_common.py``): a problem string in, a working
copy (git repo) to snapshot, a patch + pass/fail out. Everything harness-specific (WHERE to inject,
HOW to read the transcript) lives behind ``HarnessAdapter`` — those adapters are the pipeline's
non-GCD part; this block is the GCD part and is written once.

The seed *retriever* here is **LLM-only** (a single ranking call, injected as ``llm_call``), not a
ReAct loop; the graph's dependency closure + governance run on top, which is where the system value
is — so routing stays a plain LLM retriever by design.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .graph import SkillGraph
from .router import GraphRouter, Route


# --------------------------------------------------------------------------- LLM-only retriever
_SEED_SYS = (
    "You select which skill modules to preload for a coding/agent task. Pick ONLY the modules "
    "directly relevant to THIS task (and, if given, to the specified ROLE). Prerequisite modules "
    "are added automatically, so prefer a few precise choices over many. Reply with a JSON array "
    "of module ids, e.g. [\"edit-refactor\",\"run-tests\"]. No prose."
)


def make_llm_seed_fn(llm_call, *, role: str | None = None):
    """Build a router seed_fn that is a SINGLE LLM ranking call (LLM-only retriever, no ReAct).

    ``llm_call(system: str, user: str) -> str`` is injected (wrap your provider). Returns a function
    with the router's seed_fn signature ``(task, task_type, pool, top_seeds) -> list[id]``; an empty
    / unparsable reply makes the router fall back to BM25 so a flaky call never tanks a task.
    """
    def seed_fn(task, task_type, pool, top_seeds):
        if llm_call is None:
            return []
        catalog = "\n".join(f"- {n.id}: {n.name} — {n.description}" for n in pool)
        role_line = f"ROLE: {role}\n" if role else ""
        type_line = f"Task type: {task_type}\n" if task_type else ""
        user = (f"{role_line}{type_line}Task: {task}\n\nAvailable modules (id: name — description):\n"
                f"{catalog}\n\nReturn ONLY a JSON array of the {top_seeds} most relevant module ids.")
        try:
            reply = llm_call(_SEED_SYS, user) or ""
        except Exception:
            return []
        pool_ids = {n.id for n in pool}
        for frag in reversed(re.findall(r"\[[^\[\]]*\]", reply)):
            try:
                arr = json.loads(frag)
            except Exception:
                continue
            ids = [str(x).strip() for x in arr if str(x).strip() in pool_ids]
            if ids:
                return ids
        return []
    return seed_fn


def route_skills(graph: SkillGraph, problem: str, *, role: str | None = None, task_type: str = "",
                 llm_call=None, top_seeds: int = 3, hop: int = 1, type_boost: float = 1.0) -> Route:
    """Route a minimal executable subgraph for ``problem`` (optionally for a specific ROLE).

    LLM-only seeds + dependency closure + governance (the graph value). With no ``llm_call`` the
    router falls back to BM25 seeds. Pass a distinct ``role`` per multi-agent node to get per-role
    routing (the editor's subgraph ≠ the tester's)."""
    seed_fn = make_llm_seed_fn(llm_call, role=role) if llm_call is not None else None
    router = GraphRouter(graph, top_seeds=top_seeds, hop=hop, retriever="llm" if seed_fn else "bm25",
                         type_boost=type_boost, seed_fn=seed_fn)
    return router.route(problem, task_type)


# --------------------------------------------------------------------------- render formats
def render_skill_text(route: Route, *, header: str = "RELEVANT SKILL MODULES (routed for this task)") -> str:
    """Plain skill block — for --append-system-prompt / a node system prompt / a task prefix."""
    if not route.nodes:
        return ""
    parts = [f"## {header}", ""]
    for body in route._bodies:
        parts += [body.strip(), ""]
    return "\n".join(parts).strip()


def render_agents_md(route: Route) -> str:
    """Codex-native AGENTS.md content."""
    body = render_skill_text(route, header="Skills routed for this task")
    return f"# AGENTS.md (SkillStrata-routed)\n\n{body}\n" if body else ""


def render_skill_md_files(route: Route, graph: SkillGraph) -> list[tuple[str, str]]:
    """Claude-Code-native Skills: a list of (filename, SKILL.md-with-frontmatter) for the routed set."""
    out = []
    for nid in route.nodes:
        n = graph.nodes.get(nid)
        if n is None:
            continue
        fm = f"---\nname: {n.id}\ndescription: {n.description}\n---\n\n{n.body.strip()}\n"
        out.append((f"{n.id}/SKILL.md", fm))
    return out


# --------------------------------------------------------------------------- adapter interface
@dataclass
class RunResult:
    patch: str = ""
    success: bool | None = None
    trajectory: str = ""
    attempts: int = 1
    routed: dict = field(default_factory=dict)   # role -> [node ids]


class HarnessAdapter(ABC):
    """Bind the harness-agnostic block to ONE harness. Single-agent harnesses use roles()==['agent'];
    a multi-agent harness returns its node roles so SkillStrata routes per role."""

    name: str = "harness"

    def roles(self) -> list[str]:
        """Roles to route skills for. Override in multi-agent adapters (e.g. explorer/editor/tester)."""
        return ["agent"]

    @abstractmethod
    def inject(self, rendered: dict[str, Route], graph: SkillGraph) -> None:
        """Place the routed skills via the harness's NATIVE channel. ``rendered`` maps role -> Route;
        render it (render_skill_text / render_agents_md / render_skill_md_files) and put it where the
        harness reads instructions (append-system-prompt str, AGENTS.md file, per-node prompt, …)."""

    @abstractmethod
    def run(self, problem: str) -> str:
        """Execute the harness on the (already skill-injected) task; return the git-diff patch."""

    # verify-loop hooks (git-level rollback in the working copy). Optional — default = no rollback.
    def snapshot(self):
        return None

    def restore(self, token) -> None:
        return None

    def read_trajectory(self) -> str:
        """Best-effort transcript for the offline curate/distill loop (empty if unavailable)."""
        return ""


# --------------------------------------------------------------------------- driver
def run_with_skillstrata(adapter: HarnessAdapter, graph: SkillGraph, problem: str, *,
                         llm_call=None, task_type: str = "", top_seeds: int = 3,
                         verify_fn=None, max_retries: int = 0) -> RunResult:
    """The plug-and-play driver: per-role route → native inject → (verify-loop) run → observe.

    ``verify_fn(patch, adapter) -> (ok, feedback)`` enables the node/session-boundary verify-loop:
    on failure, ``adapter.restore`` rolls the working copy back and the harness re-runs up to
    ``max_retries`` times. ``llm_call(system, user) -> str`` drives the LLM-only seed retriever.
    """
    rendered = {role: route_skills(graph, problem, role=None if role == "agent" else role,
                                   task_type=task_type, llm_call=llm_call, top_seeds=top_seeds)
                for role in adapter.roles()}
    adapter.inject(rendered, graph)

    token = adapter.snapshot() if (verify_fn and max_retries) else None
    patch, attempts = "", 0
    for i in range(1 + max(0, max_retries)):
        attempts = i + 1
        patch = adapter.run(problem)
        if verify_fn is None:
            break
        ok, _ = verify_fn(patch, adapter)
        if ok:
            break
        if i < max_retries and token is not None:
            adapter.restore(token)
    return RunResult(patch=patch, trajectory=adapter.read_trajectory(), attempts=attempts,
                     routed={r: rt.nodes for r, rt in rendered.items()})
