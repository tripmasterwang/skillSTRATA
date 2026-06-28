"""SkillStrata under THREE external coding-agent harnesses (Codex CLI / Claude Code CLI /
mini-swe-agent), evaluated on SpreadsheetBench.

DESIGN — the harness is a *replaceable GCD block*, the SkillStrata pipeline is preserved.
The greatest-common-denominator across ReAct / Codex / Claude / mini-swe is exactly one thing:
"given a task prompt + a working dir (input.xlsx), run an agentic loop and produce output.xlsx
(+ an observable trajectory)". THAT is the only part we swap per harness (``_execute``).

Everything else that ``cli_skillstrata`` (the ReAct executor) does is SkillStrata pipeline and is
KEPT, wrapped around whatever harness runs:
  1. graph routing (the minimal executable subgraph)          -> inherited from CLISkillStrataAgent
  2. domain task prompt w/ official fields + MANDATORY self-verification block  -> _task_prompt
  3. node-local verify-or-rollback loop at LEARNED checkpoints  -> reuses skillos.verify +
     CLISkillStrataAgent._verify_postcondition / _merge_checkpoints (postcondition LLM judge,
     snapshot/restore the output workbook, REPAIR-hint retry)
So introducing Codex/Claude/mini-swe does NOT drop the verify-loop, the self-check prompt, or the
routing — only the inner agent loop changes. Routed skills are injected through each harness's
native channel (Codex=AGENTS.md, Claude=.claude/skills/<id>/SKILL.md, mini-swe=system prompt).

Env knobs (set by script/run_harness*.sh):
    XFYUN_BASE_URL/API_KEY/MODEL/EFFORT  CODEX_HOME  ANTHROPIC_BASE_URL/AUTH_TOKEN
    SKILLSTRATA_VERIFY_LOOP (1=on; on at test/val, off at train)
    HARNESS_STEP_LIMIT (default 30)  HARNESS_TIMEOUT (default 420)
"""
from __future__ import annotations

import os
import subprocess
import time

from .cli_skillstrata_agent import CLISkillStrataAgent


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


def _loop_enabled() -> bool:
    return os.environ.get("SKILLSTRATA_VERIFY_LOOP", "").strip().lower() in ("1", "true", "yes", "on")


class _HarnessSkillStrataBase(CLISkillStrataAgent):
    """Shared pipeline (route + self-check prompt + verify-loop); subclasses implement ``_execute``."""

    harness_name = "harness"

    def __init__(self, client, skills_dir=None, **kwargs):
        self._log_dir = kwargs.get("log_dir")
        super().__init__(client, skills_dir=skills_dir, **kwargs)
        self.step_limit = _env_int("HARNESS_STEP_LIMIT", 30)
        self.task_timeout = _env_int("HARNESS_TIMEOUT", 420)

    @property
    def name(self) -> str:
        return f"cli_skillstrata_{self.harness_name}_{self.router_mode}"

    # ---- routing (same as cli_skillstrata) ----------------------------------
    def _route_blocks(self, context):
        route = self.router.route(context.instruction or "", context.instruction_type or "")
        self._last_route = route
        blocks = []
        for nid in route.nodes:
            n = self.graph.nodes.get(nid)
            if n is not None:
                blocks.append((n.id, getattr(n, "name", n.id),
                               getattr(n, "description", ""), (n.body or "").strip()))
        route_dir = os.environ.get("SKILLSTRATA_ROUTE_DIR")
        if route_dir:
            import json
            os.makedirs(route_dir, exist_ok=True)
            guarded = sorted(getattr(route, "checkpoints", {}).keys())
            with open(os.path.join(route_dir, f"{context.instance_id}.json"), "w",
                      encoding="utf-8") as f:
                json.dump({"id": context.instance_id, "harness": self.harness_name,
                           "router": self.router_mode, "nodes": route.nodes,
                           "guarded": guarded}, f, ensure_ascii=False, indent=2)
        return route, blocks

    @staticmethod
    def _skill_text(blocks) -> str:
        if not blocks:
            return ""
        parts = ["## RELEVANT SKILL MODULES (routed for this task)", ""]
        for _id, name, desc, body in blocks:
            parts.append(f"### {name} ({_id})")
            if desc:
                parts.append(desc)
            if body:
                parts.append("")
                parts.append(body)
            parts.append("")
        return "\n".join(parts).strip()

    # ---- task prompt: official fields + MANDATORY self-verification (kept from cli_only) -----
    def _task_prompt(self, context, repair: str | None = None) -> str:
        wd = os.path.abspath(context.working_dir)
        inp = os.path.abspath(context.input_file)
        out = os.path.abspath(context.output_file)
        p = f"""Below is the spreadsheet manipulation question you need to solve:

### working_directory
{wd}

### instruction
{context.instruction}

### spreadsheet_path (INPUT)
{inp}

### spreadsheet_content (preview)
{context.spreadsheet_content}

### instruction_type
{context.instruction_type}

### answer_position
{context.answer_position}

### output_path (SAVE HERE)
{out}

---
**REMINDER**: Work only within `{wd}`. Use Python in the shell (openpyxl / pandas are available) to
read the INPUT workbook, apply the instruction, and SAVE the modified workbook to the exact
output_path above. Preserve all other cells/sheets; only change what the instruction asks.

**CRITICAL — write VALUES, not formulas.** The evaluator reads only the STORED CELL VALUES with
openpyxl and does NOT calculate formulas. So you MUST compute every result in Python and write the
resulting STATIC VALUE into each answer cell. Do NOT leave a live `=FORMULA` in the output — even if
the instruction's wording mentions a "formula", write the computed values (a stored `=FORMULA` reads
back as None and will be scored WRONG).
---

**MANDATORY SELF-VERIFICATION (do not finish without it).** After saving the output file, you MUST:
1. Re-open the saved output and PRINT the contents of the answer_position range.
2. Check EACH requirement against what you printed: all required cells filled (no unintended blanks);
   ordering/sorting exactly as asked; aggregations (sum/count/dedup) correct -- recompute them
   independently in Python and compare; value types correct (numbers as numbers, dates as Excel
   dates not strings); ONLY the answer range modified, other cells intact.
3. If ANY check fails, fix the script, re-save, and verify again.
Common pitfalls: do not compare openpyxl Cell objects (use .value); datetime must be written as an
Excel serial; ALWAYS write Python-computed static values and NEVER leave a live =FORMULA in the
output (the evaluator does not calculate formulas), even if the instruction says "formula"."""
        if repair:
            p += f"\n\n## REPAIR (a previous attempt failed verification)\n{repair}\n" \
                 "Re-open the output, fix exactly this, re-save to the output_path, and re-verify."
        return p

    # ---- logging ------------------------------------------------------------
    def _write_log(self, context, text):
        if not self._log_dir:
            return
        os.makedirs(self._log_dir, exist_ok=True)
        path = os.path.join(self._log_dir, f"{self.name}_{context.instance_id}.md")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError:
            pass

    # ---- one harness attempt (GCD call) -> result dict ----------------------
    def _attempt(self, context, blocks, repair=None):
        prompt = self._task_prompt(context, repair)
        t0 = time.time()
        try:
            log = self._execute(context, blocks, prompt)
            err = None
        except subprocess.TimeoutExpired:
            log, err = "TIMEOUT", "timeout"
        except Exception as e:  # noqa: BLE001 - never let one task kill the worker
            log, err = f"EXCEPTION: {type(e).__name__}: {e}", str(e)
        elapsed = time.time() - t0
        success = os.path.exists(context.output_file)
        self._write_log(context,
                        f"# {self.name} / {context.instance_id}\n\n"
                        f"- success(output exists): {success}\n- elapsed: {elapsed:.1f}s\n"
                        f"- repair: {bool(repair)}\n- routed nodes: {[b[0] for b in blocks]}\n"
                        f"- error: {err}\n\n## harness output\n\n```\n{log}\n```\n")
        return {"success": success, "answer": "", "turns": 0, "error": err}

    # ---- contract: route -> (verify-loop) -> harness ------------------------
    def run(self, context):
        os.environ["INPUT_FILE"] = context.input_file
        os.environ["OUTPUT_FILE"] = context.output_file
        route, blocks = self._route_blocks(context)

        cps = list(getattr(route, "checkpoints", {}).values())
        if not cps or not _loop_enabled():
            return self._attempt(context, blocks, repair=None)

        # node-local verify-or-rollback loop, identical to cli_skillstrata but the executor is the harness
        from skillos.verify import node_verifier_loop
        cp = self._merge_checkpoints(cps)
        out_path = os.path.abspath(context.output_file)

        def execute_fn(i, hint):
            return self._attempt(context, blocks, repair=(hint if i > 0 and hint else None))

        def verify_fn(result):
            return self._verify_postcondition(context, cp.postcondition, result)

        def snapshot_fn():
            return open(out_path, "rb").read() if os.path.exists(out_path) else None

        def restore_fn(tok):
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

    def _execute(self, context, blocks, prompt) -> str:  # pragma: no cover - abstract
        raise NotImplementedError


class CodexSkillStrataAgent(_HarnessSkillStrataBase):
    """SkillStrata executed by the Codex CLI; skills injected via AGENTS.md."""

    harness_name = "codex"

    def _execute(self, context, blocks, prompt) -> str:
        skill_text = self._skill_text(blocks)
        with open(os.path.join(context.working_dir, "AGENTS.md"), "w", encoding="utf-8") as f:
            f.write("# Repository guidelines (SkillStrata-routed skills)\n\n")
            f.write(skill_text or "(no routed skills)\n")
        model = os.environ.get("XFYUN_MODEL", "xopqwen36v35b")
        cmd = ["codex", "exec", "--skip-git-repo-check", "--ephemeral",
               "--dangerously-bypass-approvals-and-sandbox",
               "-C", context.working_dir, "-m", model, prompt]
        p = subprocess.run(cmd, env=os.environ.copy(), cwd=context.working_dir,
                           stdin=subprocess.DEVNULL,  # else codex reads stdin when run head-less
                           capture_output=True, text=True, timeout=self.task_timeout)
        return (p.stdout or "") + "\n--- STDERR ---\n" + (p.stderr or "")


class ClaudeCodeSkillStrataAgent(_HarnessSkillStrataBase):
    """SkillStrata executed by the Claude Code CLI; skills injected as native SKILL.md files."""

    harness_name = "claude"

    def _execute(self, context, blocks, prompt) -> str:
        skills_root = os.path.join(context.working_dir, ".claude", "skills")
        for _id, name, desc, body in blocks:
            d = os.path.join(skills_root, _id)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(f"---\nname: {_id}\ndescription: {desc or name}\n---\n\n{body}\n")
        if blocks:  # ensure native skills are DISCOVERED (progressive disclosure may not auto-fire in -p)
            ids = ", ".join(b[0] for b in blocks)
            prompt = prompt + ("\n\n## ROUTED SKILLS (consult before solving)\nTask-specific skills are "
                               f"installed at .claude/skills/<name>/SKILL.md: {ids}. Read the relevant "
                               "ones first and follow their guidance.")
        env = os.environ.copy()
        model = os.environ.get("XFYUN_MODEL", "xopqwen36v35b")
        env.setdefault("ANTHROPIC_AUTH_TOKEN", "dummy")
        env["ANTHROPIC_MODEL"] = model
        env["ANTHROPIC_SMALL_FAST_MODEL"] = model
        env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
        cmd = ["claude", "-p", prompt, "--permission-mode", "bypassPermissions",
               "--add-dir", context.working_dir, "--model", model,
               "--max-turns", str(self.step_limit), "--output-format", "text"]
        p = subprocess.run(cmd, env=env, cwd=context.working_dir,
                           stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=self.task_timeout)
        return (p.stdout or "") + "\n--- STDERR ---\n" + (p.stderr or "")


class MiniSweSkillStrataAgent(_HarnessSkillStrataBase):
    """SkillStrata executed by mini-swe-agent (in-process); skills in the system prompt."""

    harness_name = "minisweagent"

    _SYS = (
        "You are a careful spreadsheet-editing assistant operating in a shell.\n\n"
        "Your response must contain exactly ONE bash code block with ONE command, in a\n"
        "```mswea_bash_command``` block, preceded by a short THOUGHT. Directory/env changes are\n"
        "NOT persistent across actions, so prefix with `cd <dir> && ...` when needed.\n"
        "When the OUTPUT workbook has been saved AND self-verified, finish by issuing exactly:\n"
        "`echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` on its own."
    )

    def _execute(self, context, blocks, prompt) -> str:
        from minisweagent.agents.default import DefaultAgent
        from minisweagent.environments.local import LocalEnvironment
        from minisweagent.models.litellm_model import LitellmModel

        base = os.environ.get("XFYUN_BASE_URL", "https://maas-api.cn-huabei-1.xf-yun.com/v2")
        key = os.environ.get("XFYUN_API_KEY", "")
        model = os.environ.get("XFYUN_MODEL", "xopqwen36v35b")
        effort = os.environ.get("XFYUN_EFFORT", "medium")

        skill_text = self._skill_text(blocks)
        system = self._SYS + ("\n\n" + skill_text if skill_text else "")
        system_tmpl = "{% raw %}" + system + "{% endraw %}"
        instance_tmpl = "{% raw %}" + prompt + "{% endraw %}"

        mdl = LitellmModel(
            model_name="openai/" + model, cost_tracking="ignore_errors",
            model_kwargs={"api_base": base, "api_key": key, "temperature": 0.0,
                          "max_tokens": 8192, "drop_params": True,
                          "extra_body": {"enable_thinking": True, "reasoning_effort": effort}})
        env = LocalEnvironment(cwd=context.working_dir, timeout=120,
                               env={"PAGER": "cat", "MANPAGER": "cat",
                                    "PIP_PROGRESS_BAR": "off", "TQDM_DISABLE": "1"})
        agent = DefaultAgent(mdl, env, system_template=system_tmpl, instance_template=instance_tmpl,
                             step_limit=self.step_limit, cost_limit=0.0)
        result = agent.run(task="")
        tail = "\n".join(f"[{m.get('role')}] " + (m.get('content') or '')[:2000]
                         for m in agent.messages[-6:])
        return f"exit={result}\n\n--- last messages ---\n{tail}"
