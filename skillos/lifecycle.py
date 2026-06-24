"""Skill lifecycle management — promotion, validation gate, and retirement sweep.

Grounded in MemoryOS's tier-transition template
(``MemoryOS/memoryos-pypi/memoryos.py:126 _trigger_profile_and_knowledge_update_if_needed``):
peek the heat heap, compare to a tier threshold, transform, then reset heat + set a cooldown
flag. We instantiate that template for the skill lifecycle:

    CANDIDATE --(propose-then-verify gate)--> VALIDATED --(heat gate)--> DEPLOYED
                                                                   \--(utility floor)--> RETIRED

The validation gate is the proposal's "propose-then-verify" training strategy: a candidate
operation is accepted iff it **preserves/improves success while reducing token cost or
negative transfer** (proposal §Training Strategy, §Validation-Time Output).
"""

from __future__ import annotations

from dataclasses import dataclass

from .graph import SkillGraph
from .heat import HeatConfig, compute_skill_heat, utility
from .operations import retire
from .schema import Status


@dataclass
class GateMetrics:
    success_rate: float
    avg_tokens: float
    negative_transfer: float

    def as_dict(self) -> dict:
        return {
            "success_rate": round(self.success_rate, 4),
            "avg_tokens": round(self.avg_tokens, 1),
            "negative_transfer": round(self.negative_transfer, 4),
        }


@dataclass
class GateDecision:
    accept: bool
    before: GateMetrics
    after: GateMetrics
    reason: str


def verify_gate(
    before: GateMetrics,
    after: GateMetrics,
    *,
    success_tol: float = 0.01,
) -> GateDecision:
    """Accept iff success is preserved (within tol) AND (tokens drop OR neg-transfer drops).

    Mirrors the Validation-Time Output example in the proposal.
    """
    success_ok = after.success_rate >= before.success_rate - success_tol
    cost_better = after.avg_tokens < before.avg_tokens
    transfer_better = after.negative_transfer < before.negative_transfer
    accept = success_ok and (cost_better or transfer_better)
    if not success_ok:
        reason = "reject: success regressed"
    elif accept:
        gains = []
        if cost_better:
            gains.append("tokens↓")
        if transfer_better:
            gains.append("neg-transfer↓")
        reason = "accept: " + "+".join(gains)
    else:
        reason = "reject: no cost/transfer gain"
    return GateDecision(accept, before, after, reason)


class LifecycleManager:
    """Drives status transitions using heat thresholds (MemoryOS promotion-gate pattern)."""

    def __init__(
        self,
        graph: SkillGraph,
        cfg: HeatConfig | None = None,
        deploy_heat: float = 2.0,        # MemoryOS H_PROFILE_UPDATE_THRESHOLD analogue
        retire_floor: float = 0.15,
        max_deployed: int | None = None,
        govern: bool = False,
        block_min_trials: int = 10,
        block_success_rate: float = 0.30,
        prune_cold: bool = False,
        cold_after_step: int = 60,
    ):
        self.graph = graph
        self.cfg = cfg or HeatConfig()
        self.deploy_heat = deploy_heat
        self.retire_floor = retire_floor
        self.max_deployed = max_deployed
        self.govern = govern
        self.block_min_trials = block_min_trials
        self.block_success_rate = block_success_rate
        self.prune_cold = prune_cold
        self.cold_after_step = cold_after_step

    def validate(self, skill_id: str, decision: GateDecision) -> bool:
        """CANDIDATE -> VALIDATED iff the verify gate accepted the introducing op."""
        node = self.graph.nodes.get(skill_id)
        if node is None or not decision.accept:
            return False
        if node.status == Status.CANDIDATE:
            node.status = Status.VALIDATED
        return True

    def promote_deployable(self) -> list[str]:
        """VALIDATED -> DEPLOYED when heat crosses the deploy threshold.

        MemoryOS peeks the hottest segment; we promote every validated skill above threshold
        (and seed-deploy validated skills early so routing has a pool to draw from).
        """
        promoted = []
        for n in self.graph.nodes.values():
            if n.status != Status.VALIDATED:
                continue
            heat = compute_skill_heat(n, self.graph.step, self.cfg)
            if heat >= self.deploy_heat or n.heat.trials == 0:
                n.status = Status.DEPLOYED
                promoted.append(n.id)
        if self.max_deployed is not None:
            self._enforce_deploy_cap()
        return promoted

    def _enforce_deploy_cap(self) -> None:
        deployed = self.graph.deployed()
        if len(deployed) <= self.max_deployed:
            return
        ranked = sorted(deployed, key=lambda n: utility(n, self.graph.step, self.cfg))
        for n in ranked[: len(deployed) - self.max_deployed]:
            n.status = Status.VALIDATED  # demote coldest back to bench

    def retire_sweep(self) -> list[str]:
        """RETIRE skills whose utility fell below the floor (symmetric to promotion)."""
        retired = []
        # repeatedly remove the worst while below floor
        for _ in range(len(self.graph.active())):
            res = retire(self.graph, floor=self.retire_floor, cfg=self.cfg)
            if not res.ok:
                break
            retired.extend(res.affected)
        return retired

    def govern_sweep(self) -> list[str]:
        """BLOCKS_ROUTING the chronic offenders: skills tried often that mostly fail.

        Governance graph records a ``retirement_signal``-style rule that ``blocks_routing`` such
        a skill so the router stops loading it (the proposal's governance->routing constraint).
        Conservative thresholds keep it from quarantining merely-rare skills.
        """
        from .schema import EdgeType, GovernanceNode, slugify

        blocked = []
        already = self.graph.blocked_skills()
        for n in self.graph.nodes.values():
            if n.status == Status.RETIRED or n.id in already:
                continue
            if n.heat.trials >= self.block_min_trials and n.heat.success_rate < self.block_success_rate:
                rid = slugify(f"block_{n.id}_{self.graph.step}")
                self.graph.add_rule(GovernanceNode(
                    id=rid, kind="block_signal",
                    statement=f"BLOCKS_ROUTING {n.id} (success_rate<{self.block_success_rate})",
                    targets=[n.id],
                ))
                self.graph.governance.add_edge(rid, n.id, type=EdgeType.BLOCKS_ROUTING.value)
                blocked.append(n.id)
        return blocked

    def cold_prune(self) -> list[str]:
        """Retire skills never used since deployment (pruning-style bank shrinking).

        Unlike heat-aware RETIRE this ignores future need — pruning a skill before the OOD task
        that needs it arrives is the characteristic failure mode of usage-only pruning.
        """
        pruned = []
        if self.graph.step < self.cold_after_step:
            return pruned
        for n in self.graph.active():
            if n.status == Status.CANDIDATE:
                continue
            if n.heat.n_visit == 0:
                n.status = Status.RETIRED
                pruned.append(n.id)
        return pruned

    def step(self) -> dict:
        """One lifecycle housekeeping tick: promote, govern (optional), then retire/prune."""
        promoted = self.promote_deployable()
        blocked = self.govern_sweep() if self.govern else []
        retired = self.retire_sweep()
        pruned = self.cold_prune() if self.prune_cold else []
        return {"promoted": promoted, "blocked": blocked, "retired": retired, "pruned": pruned}
