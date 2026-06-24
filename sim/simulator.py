"""Executor model: (activated skills, task) -> success / token-cost / negative-transfer.

This is the deterministic stand-in for Trace2Skill's real agent rollout + official verifier.
The success model encodes the proposal's three mechanisms:

  * **coverage** — you can only solve a task if its required atomic skills are loaded
    (or available transitively). Missing requirements lower success.
  * **distraction / negative transfer** — loading *anti-skills* (atomics whose local rules
    clash with this task-type) lowers success; this is proposal §Problem 2.
  * **token cost** — proportional to the total body tokens of loaded skills (proposal §Problem 1
    skill bloat). A monolith loads everything; a routed subgraph loads little.

Swap-in seam for a real-LLM run
-------------------------------
Replace ``execute()`` with:
    ctx = AgentContext(instruction=task.text, system_skill=route.render())   # Trace2Skill
    result = base_spreadsheet_agent.run(ctx)
    success = evaluate_with_official(result)                                  # Trace2Skill
    tokens  = result.usage.total_tokens
Everything upstream (graph, router, lifecycle) is unchanged.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .tasks import TaskType, World


@dataclass
class ExecOutcome:
    success: bool
    tokens: int
    loaded: int
    negative_transfer: float   # fraction of loaded skills that are anti/irrelevant for this task
    covered: float             # fraction of required atomics available in the activated set


# success-model coefficients (fixed; documented so results are auditable)
BASE = 0.97              # ceiling success when fully covered & no distractors
COVER_W = 0.55           # penalty weight for missing required skills
ANTI_W = 0.45            # penalty weight per anti-skill loaded (negative transfer)
IRREL_W = 0.05           # mild penalty for loading merely-irrelevant skills


def _atomics_of(world: World, activated: list[str]) -> set[str]:
    """Expand activated skill nodes to the set of underlying atomics they carry.

    A SkillOS atomic node maps to one atomic id; a monolith node (id prefixed 'monolith_')
    carries many. ``node.task_types`` / id conventions are set by the builders in run_main.
    """
    out: set[str] = set()
    for nid in activated:
        if nid in world.atomics:
            out.add(nid)
        elif nid.startswith("monolith_"):
            # monolith_<domain> carries every atomic of that domain
            domain = nid[len("monolith_"):]
            out.update(a.id for a in world.atomics_in(domain))
        elif "::" in nid:
            # composite "child::atomic" naming from SPLIT
            out.add(nid.split("::", 1)[1])
    return out


POISON_MULT = 0.4        # each loaded harmful/over-generalized skill multiplies success prob


def execute(
    world: World,
    task_type: TaskType,
    activated_ids: list[str],
    loaded_tokens: int,
    rng: random.Random,
) -> ExecOutcome:
    loaded_atomics = _atomics_of(world, activated_ids)
    # success needs the FULL dependency closure of the entry skills, not just the entries
    required = world.closure(task_type.required)
    anti = set(task_type.anti) - required

    covered = len(required & loaded_atomics) / len(required) if required else 1.0
    n_anti = len(anti & loaded_atomics)
    irrelevant = loaded_atomics - required - anti
    irrel_rate = len(irrelevant) / max(1, len(loaded_atomics))
    n_poison = sum(1 for nid in activated_ids if nid in world.poison)

    p = BASE
    p -= COVER_W * (1 - covered)
    p -= ANTI_W * min(1.0, n_anti / 2.0)
    p -= IRREL_W * irrel_rate
    p *= POISON_MULT ** n_poison              # over-generalized skills sharply hurt
    p = max(0.02, min(0.99, p))
    success = rng.random() < p

    # negative transfer is measured per loaded *atomic* (a monolith node carries many atomics)
    n_loaded = max(1, len(loaded_atomics) + n_poison)
    neg_transfer = (n_anti + n_poison + 0.2 * len(irrelevant)) / n_loaded
    return ExecOutcome(
        success=success,
        tokens=loaded_tokens,
        loaded=len(activated_ids),
        negative_transfer=round(min(1.0, neg_transfer), 4),
        covered=round(covered, 4),
    )
