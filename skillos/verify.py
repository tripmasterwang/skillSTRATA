"""Node-local verify-or-rollback loops for critical / error-prone skills.

Standard "loop engineering" wraps the WHOLE task in one planner -> executor -> verifier loop: the
verifier only sees the final task goal, and any failure forces re-running everything. This module
pushes the verifier DOWN to individual capability nodes. A *checkpoint* (a governance node, kind
``checkpoint``, linked to a skill by a ``GUARDS_SKILL`` edge) carries a sub-goal (postcondition) and
a small retry budget. When the executor routes through a guarded node it runs:

    execute -> verify(sub-goal) -> on fail: rollback to the node's entry state, retry with feedback
            -> loop until the postcondition holds or the budget is spent.

Two halves, matching the codebase's "deterministic graph logic + injected API callables" split:

  * ``mint_checkpoints_from_traces`` — LEARNED governance: the trace layer already records which
    skills sit in failing runs (``heat`` success/failure counts). Skills that fail often enough get
    a checkpoint auto-attached. So "which steps are error-prone" is discovered, not hand-labelled —
    the same train-time-governance idea as ``validation_gate`` / ``blocks_routing``.
  * ``node_verifier_loop`` — the RUNTIME loop. ``execute_fn`` / ``verify_fn`` / ``snapshot_fn`` /
    ``restore_fn`` are injected (the server driver wires them to the agent + the xlsx file state),
    so the control flow here is deterministic and unit-testable offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .graph import SkillGraph
from .schema import EdgeType, GovernanceNode, Status, TraceNode, slugify


# --------------------------------------------------------------------------- learn checkpoints
def mint_checkpoints_from_traces(graph: SkillGraph, *, min_trials: int = 3,
                                 max_success_rate: float = 0.6,
                                 postcondition_fn=None, default_max_retries: int = 2) -> list[str]:
    """Attach a checkpoint to every error-prone skill the trace layer has flagged.

    A skill is "error-prone" if it has been tried ``>= min_trials`` times and its success rate is
    ``<= max_success_rate`` (low-success deployed nodes are exactly where a local verify-loop pays
    off). ``postcondition_fn(node) -> str`` (injected; e.g. an LLM that reads the node body +
    failing traces) authors the sub-goal text; a generic fallback is used if it is None or returns
    empty. Idempotent: a node that is already guarded is skipped. Returns the new checkpoint ids.
    """
    minted: list[str] = []
    already = graph.guarded_skills()
    for nid, node in list(graph.nodes.items()):
        if node.status != Status.DEPLOYED or nid in already:
            continue
        if node.heat.trials < min_trials or node.heat.success_rate > max_success_rate:
            continue
        post = ""
        if postcondition_fn is not None:
            try:
                post = (postcondition_fn(node) or "").strip()
            except Exception:
                post = ""
        if not post:
            post = (f"The result of '{node.name}' is correct and complete: it did the task's "
                    f"intended edit, ran without error, and left the spreadsheet consistent.")
        cid = slugify(f"checkpoint_{nid}_{graph.step}")
        rule = GovernanceNode(id=cid, kind="checkpoint",
                              statement=f"verify-loop guards '{nid}' (succ {node.heat.success_rate:.2f}"
                                        f" over {node.heat.trials} trials)",
                              targets=[nid], postcondition=post,
                              max_retries=default_max_retries,
                              repair_hint=f"Previous attempt at '{node.name}' failed its check. "
                                          f"Re-read the requirement and fix the specific failure.")
        graph.rules[rule.id] = rule
        graph.governance.add_node(rule.id, kind="rule")
        graph.link(rule.id, nid, EdgeType.GUARDS_SKILL)
        minted.append(cid)
    return minted


# --------------------------------------------------------------------------- runtime loop
@dataclass
class Attempt:
    n: int
    ok: bool
    feedback: str = ""


@dataclass
class VerifyOutcome:
    skill_id: str
    ok: bool
    result: object = None
    attempts: list[Attempt] = field(default_factory=list)

    @property
    def n_attempts(self) -> int:
        return len(self.attempts)


def node_verifier_loop(checkpoint: GovernanceNode, execute_fn, verify_fn, *,
                       snapshot_fn=None, restore_fn=None) -> VerifyOutcome:
    """Run one guarded node under a local verify-or-rollback loop.

      execute_fn(attempt_idx, repair_hint) -> result   run the node's skill (e.g. an agent sub-call)
      verify_fn(result)                    -> (ok, feedback)   check ``checkpoint.postcondition``
      snapshot_fn()  -> token             capture pre-attempt side-effect state (e.g. copy the xlsx)
      restore_fn(token)                    roll the side-effect state back before a retry

    Loops up to ``1 + checkpoint.max_retries`` times. On a failed attempt it restores the snapshot
    (so retries don't compound corruption) and re-executes with the verifier's feedback prepended to
    ``checkpoint.repair_hint``. Stops at the first pass. The returned outcome (incl. ``ok`` and the
    per-attempt history) is what the caller feeds back into the trace layer via ``record_attempts``.
    """
    attempts: list[Attempt] = []
    base_hint = checkpoint.repair_hint
    token = snapshot_fn() if snapshot_fn else None
    last_result = None
    for i in range(1 + max(0, checkpoint.max_retries)):
        hint = base_hint if i == 0 else f"{attempts[-1].feedback}\n{base_hint}".strip()
        last_result = execute_fn(i, hint)
        ok, feedback = verify_fn(last_result)
        attempts.append(Attempt(n=i, ok=ok, feedback="" if ok else (feedback or "check failed")))
        if ok:
            return VerifyOutcome(checkpoint.targets[0] if checkpoint.targets else "", True,
                                 last_result, attempts)
        if restore_fn and token is not None and i < checkpoint.max_retries:
            restore_fn(token)          # rollback before the next retry
    return VerifyOutcome(checkpoint.targets[0] if checkpoint.targets else "", False,
                         last_result, attempts)


def record_attempts(graph: SkillGraph, outcome: VerifyOutcome, task_type: str = "") -> None:
    """Fold a verify-loop's attempts back into the trace + heat layers so the mechanism is
    self-reinforcing: failed attempts become CAUSED_FAILURE evidence and bump the node's failure
    count (which is what minted the checkpoint in the first place); a final pass after retries
    becomes a FIXED_BY edge — raw material distill turns into a ``kind='fix'`` repair skill."""
    sid = outcome.skill_id
    if sid not in graph.nodes:
        return
    node = graph.nodes[sid]
    for att in outcome.attempts:
        tid = f"trace_{len(graph.traces)}"
        graph.traces[tid] = TraceNode(id=tid, task_id="", task_type=task_type, success=att.ok,
                                      used_skills=[sid], fail_reason="" if att.ok else att.feedback)
        graph.trace.add_node(tid, kind="trace", success=att.ok)
        if att.ok:
            node.heat.success_count += 1
            if att.n > 0:                              # passed only after a repair -> FIXED_BY
                graph.link(sid, tid, EdgeType.FIXED_BY)
        else:
            node.heat.failure_count += 1
            graph.link(sid, tid, EdgeType.CAUSED_FAILURE)
    node.heat.last_used_step = graph.step
