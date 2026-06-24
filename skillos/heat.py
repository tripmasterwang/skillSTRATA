"""Heat scoring for skill lifecycle — adapted from MemoryOS.

Source: ``MemoryOS/memoryos-pypi/mid_term.py:26 compute_segment_heat`` and
``utils.py:228 compute_time_decay``.

MemoryOS heat:   H = alpha*N_visit + beta*L_interaction + gamma*R_recency
                 R_recency = exp(-delta_hours / tau)

SkillOS reinterprets the three factors for *skills* instead of conversation segments:
  * N_visit        -> number of times the skill was activated (invocations)
  * L_interaction  -> coverage = number of distinct task-types the skill has served
  * R_recency      -> decay since last activation, measured in *logical steps*
                      (the simulator has no wall-clock; a step is one task) so the harness
                      stays deterministic and reproducible.

The heat drives two lifecycle decisions (see ``skillos.lifecycle``):
  * promotion  (validated -> deployed): hottest skills earn deployment
  * RETIRE     (any -> retired): coldest, low-success skills are evicted
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .schema import SkillNode


@dataclass
class HeatConfig:
    alpha: float = 1.0          # weight on invocation count   (MemoryOS HEAT_ALPHA)
    beta: float = 1.0           # weight on coverage           (MemoryOS HEAT_BETA)
    gamma: float = 1.0          # weight on recency            (MemoryOS HEAT_GAMMA)
    tau_steps: float = 50.0     # recency decay constant in logical steps (MemoryOS tau_hours)


def time_decay(last_used_step: int, now_step: int, tau_steps: float) -> float:
    """exp(-delta/tau); mirrors MemoryOS compute_time_decay but over logical steps."""
    if last_used_step < 0:
        return 0.0
    delta = max(0, now_step - last_used_step)
    return math.exp(-delta / tau_steps)


def compute_skill_heat(node: SkillNode, now_step: int, cfg: HeatConfig | None = None) -> float:
    """H = alpha*N_visit + beta*coverage + gamma*recency (MemoryOS compute_segment_heat)."""
    cfg = cfg or HeatConfig()
    h = node.heat
    recency = time_decay(h.last_used_step, now_step, cfg.tau_steps)
    return cfg.alpha * h.n_visit + cfg.beta * h.coverage + cfg.gamma * recency


def utility(node: SkillNode, now_step: int, cfg: HeatConfig | None = None) -> float:
    """Retirement utility = heat * success_rate, penalised for unproven skills.

    A skill that is hot but usually *fails* is a negative-transfer hazard; combining heat with
    success rate gives RETIRE a single comparable score (cf. MemoryOS LFU access count, which
    ignored success). Skills with no trials get a small prior so brand-new candidates are not
    instantly retired.
    """
    heat = compute_skill_heat(node, now_step, cfg)
    sr = node.heat.success_rate if node.heat.trials else 0.5
    return heat * sr
