"""Evaluation loop shared by the main table and the ablations.

Streams the world's tasks through a method's router + executor, updating skill heat and
running lifecycle housekeeping, and aggregates the proposal's metrics (§Metrics):

    Task Success Rate, Average Token Cost, Loaded Skill Count, Negative Transfer Rate,
    OOD Transfer Gain, Skill Bank Size, Graph Routing Precision.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field

from skillos import SkillGraph, LifecycleManager, Status, SkillNode, Granularity
from .simulator import execute
from .tasks import World


@dataclass
class Metrics:
    success_rate: float = 0.0
    avg_tokens: float = 0.0
    avg_loaded: float = 0.0
    negative_transfer: float = 0.0
    ood_success: float = 0.0
    id_success: float = 0.0
    routing_precision: float = 0.0
    skill_bank_size: int = 0
    late_success: float = 0.0       # success over the last 30% of the stream (long-horizon)
    window_std: float = 0.0         # std of per-window success (stability; lower = more stable)
    avg_synth: float = 0.0          # avg test-time-synthesized skills per task (TTA activity)
    avg_covered: float = 0.0        # avg fraction of needed sub-capabilities present in route

    @property
    def ood_gain(self) -> float:
        """OOD transfer gain = OOD success relative to in-distribution success."""
        return round(self.ood_success - self.id_success, 4)

    def as_row(self) -> dict:
        return {
            "success": round(self.success_rate, 4),
            "tokens": round(self.avg_tokens, 1),
            "loaded": round(self.avg_loaded, 2),
            "neg_transfer": round(self.negative_transfer, 4),
            "ood_success": round(self.ood_success, 4),
            "id_success": round(self.id_success, 4),
            "ood_gain": self.ood_gain,
            "route_precision": round(self.routing_precision, 4),
            "bank_size": self.skill_bank_size,
            "late_success": round(self.late_success, 4),
            "stability": round(1.0 - self.window_std, 4),  # higher = more stable
            "covered": round(self.avg_covered, 4),
            "synth": round(self.avg_synth, 3),
        }


def _replay_success(world, graph, router, tasks_subset, rng_seed) -> float:
    """Average success over a small replay set — the verifier behind the validation gate."""
    rng = random.Random(rng_seed)
    if not tasks_subset:
        return 0.0
    s = 0.0
    for t in tasks_subset:
        tt = world.task_types[t.task_type]
        r = router.route(t.text, t.task_type)
        s += execute(world, tt, r.nodes, r.loaded_tokens, rng).success
    return s / len(tasks_subset)


def _inject_candidates(
    world, graph, router, recent_tasks, step, rng, validate: bool,
) -> None:
    """Propose new candidate skills (some good, some harmful) and gate them.

    Good candidate  = a near-duplicate variant of an existing deployed atomic (neutral/helpful).
    Harmful candidate = an over-generalized skill: broad keywords (so it gets retrieved) that
                        actively mislead tasks (registered in ``world.poison``).

    With ``validate`` (propose-then-verify), each candidate is DEPLOYED only if a replay shows it
    preserves success vs. leaving it on the bench — harmful skills fail this and stay CANDIDATE.
    Without validation, every candidate is deployed immediately (the proposal's "harmful skill
    updates" failure mode).
    """
    proposals = []
    deployed = [n for n in graph.nodes.values() if n.status == Status.DEPLOYED and n.id in world.atomics]
    if not deployed:
        return
    # harmful = a plausible IMPOSTOR of a real atomic: same keywords (so BM25 ranks it right
    # alongside the genuine skill and it actually gets routed) but its rules mislead — it is
    # registered in world.poison. This is the over-generalized / harmful skill the proposal warns
    # about: it looks relevant but causes negative transfer.
    victim = rng.choice(deployed)
    pid = f"harmful_{step}"
    proposals.append(("harmful", SkillNode.make(
        id=pid, name=pid, description=victim.description,
        body=f"# {victim.name} (general variant)\n{victim.body}", granularity=Granularity.PLAN,
    )))
    # good = a benign near-duplicate of a different real atomic (neutral/helpful)
    base = rng.choice(deployed)
    gid = f"good_{step}"
    proposals.append(("kind", SkillNode.make(
        id=gid, name=gid, description=base.description,
        body=base.body, granularity=Granularity.ATOMIC,
    )))

    for kind, node in proposals:
        node.status = Status.CANDIDATE
        node.heat.token_cost = len(node.body) // 4
        graph.add_skill(node)
        if kind == "harmful":
            world.poison.add(node.id)

        if not validate:
            node.status = Status.DEPLOYED
            continue
        # propose-then-verify: deploy only if a replay shows success is preserved.
        before = _replay_success(world, graph, router, recent_tasks, rng_seed=step)
        node.status = Status.DEPLOYED
        after = _replay_success(world, graph, router, recent_tasks, rng_seed=step)
        if after < before - 0.01:          # harmful skill lowers replay success -> reject
            node.status = Status.CANDIDATE


def _precision(world: World, task_type, activated_ids: list[str]) -> float:
    """Fraction of loaded atomics that are actually required (graph routing precision)."""
    from .simulator import _atomics_of
    loaded = _atomics_of(world, activated_ids)
    if not loaded:
        return 0.0
    req = set(task_type.required)
    return len(loaded & req) / len(loaded)


def run_method(
    world: World,
    graph: SkillGraph,
    router,
    lifecycle: LifecycleManager | None = None,
    seed: int = 0,
    lifecycle_every: int = 25,
    validate: bool = True,
    inject: bool = True,
    inject_every: int = 50,
) -> Metrics:
    rng = random.Random(seed + 12345)
    inj_rng = random.Random(seed + 999)
    succ = tokens = loaded = neg = prec = synth = cov = 0.0
    ood_s = ood_n = id_s = id_n = 0
    n = len(world.tasks)
    record_trace = getattr(router, "tta", False)   # build the trace layer only when TTA needs it
    outcomes: list[int] = []      # per-task success, for late-stream + windowed stability

    for i, task in enumerate(world.tasks):
        # periodically the evolver proposes new candidate skills (some harmful) into the bank
        if inject and i > 0 and i % inject_every == 0:
            recent = world.tasks[max(0, i - 8):i]
            _inject_candidates(world, graph, router, recent, i, inj_rng, validate)
        graph.tick()
        tt = world.task_types[task.task_type]
        route = router.route(task.text, task.task_type)
        out = execute(world, tt, route.nodes, route.loaded_tokens, rng)

        succ += out.success
        tokens += out.tokens
        loaded += out.loaded
        neg += out.negative_transfer
        prec += _precision(world, tt, route.nodes)
        synth += len(route.synthesized)
        cov += out.covered
        outcomes.append(int(out.success))

        # trace layer: record what the run exercised (lego material for test-time synthesis).
        # Uses the task's needed sub-capabilities as execution evidence (cf. log parsing); this
        # is written AFTER routing, so it never leaks the current task's needs into its own route.
        if record_trace:
            needed = world.closure(tt.required)
            bodies = {aid: world.atomics[aid].body for aid in needed if aid in world.atomics}
            graph.record_trace(list(needed), out.success, bodies)

        if tt.ood:
            ood_s += out.success; ood_n += 1
        else:
            id_s += out.success; id_n += 1

        # update heat on activated skills (MemoryOS N_visit / success bookkeeping)
        for nid in route.nodes:
            if nid in graph.nodes:
                node = graph.nodes[nid]
                node.heat.n_visit += 1
                node.heat.last_used_step = graph.step
                if out.success:
                    node.heat.success_count += 1
                else:
                    node.heat.failure_count += 1

        if lifecycle is not None and (i + 1) % lifecycle_every == 0:
            lifecycle.step()

    active = [s for s in graph.nodes.values() if s.status != Status.RETIRED]
    late_cut = int(n * 0.7)
    late = outcomes[late_cut:]
    late_success = sum(late) / len(late) if late else 0.0
    # per-window success std (10 windows) — stability over the heterogeneous stream
    w = max(1, n // 10)
    windows = [outcomes[i:i + w] for i in range(0, n, w)]
    win_means = [sum(x) / len(x) for x in windows if x]
    window_std = statistics.pstdev(win_means) if len(win_means) > 1 else 0.0
    return Metrics(
        success_rate=succ / n,
        avg_tokens=tokens / n,
        avg_loaded=loaded / n,
        negative_transfer=neg / n,
        ood_success=ood_s / ood_n if ood_n else 0.0,
        id_success=id_s / id_n if id_n else 0.0,
        routing_precision=prec / n,
        skill_bank_size=len(active),
        late_success=late_success,
        window_std=window_std,
        avg_synth=synth / n,
        avg_covered=cov / n,
    )
