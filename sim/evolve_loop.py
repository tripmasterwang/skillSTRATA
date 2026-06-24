"""Self-evolution loop experiment (multi-round curate; no RL).

Each round runs the *current* Skill Strata over the whole task stream, then at round-end distills
and consolidates new skills from accumulated trace evidence (``skillos.evolve``). The two
consolidation points of the loop:
  * test-time (per task): LEGO assembly synthesizes missing skills ephemerally (``tta``), and the
    trace evidence it uses accumulates;
  * round-end: ``distill_and_consolidate`` fixes the repeatedly-useful ones into deployed skills.

Expected curves (the "self-evolution is happening" evidence — run separately, not here):
  * success ↑ over rounds (system gets stronger),
  * synth_per_task ↓ (what had to be assembled is now in the library),
  * deployed grows then plateaus (assembled skills sediment).

    python -m sim.evolve_loop --seeds 0 1 2 --rounds 5 --hold-out 3
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics

from skillos import Status
from skillos.evolve import distill_and_consolidate
from .tasks import build_world
from .simulator import execute
from . import builders


def run_evolution_loop(world, graph, router, lifecycle, rounds: int = 5, seed: int = 0):
    rng = random.Random(seed + 12345)
    record_trace = getattr(router, "tta", False)
    n = len(world.tasks)
    per_round = []
    for r in range(rounds):
        succ = synth = cov = 0.0
        for task in world.tasks:
            graph.tick()
            tt = world.task_types[task.task_type]
            route = router.route(task.text, task.task_type)
            out = execute(world, tt, route.nodes, route.loaded_tokens, rng)
            succ += out.success
            synth += len(route.synthesized)
            cov += out.covered
            if record_trace:
                needed = world.closure(tt.required)
                bodies = {a: world.atomics[a].body for a in needed if a in world.atomics}
                graph.record_trace(list(needed), out.success, bodies)
            for nid in route.nodes:
                if nid in graph.nodes:
                    node = graph.nodes[nid]
                    node.heat.n_visit += 1
                    node.heat.last_used_step = graph.step
                    if out.success:
                        node.heat.success_count += 1
                    else:
                        node.heat.failure_count += 1
        # round-end curate: distill + consolidate from accumulated trace evidence, then maintain
        consolidated = distill_and_consolidate(graph) if record_trace else []
        if lifecycle is not None:
            lifecycle.step()
        per_round.append({
            "round": r,
            "success": round(succ / n, 4),
            "synth_per_task": round(synth / n, 3),
            "covered": round(cov / n, 4),
            "deployed": len([x for x in graph.nodes.values() if x.status == Status.DEPLOYED]),
            "consolidated": len(consolidated),
        })
    return per_round


def run(seeds: list[int], rounds: int, hold_out: int) -> dict:
    all_runs = []
    for seed in seeds:
        world = build_world(seed=seed)
        g, r, lc = builders.build_skillos(world, hold_out=hold_out, tta=True)
        all_runs.append(run_evolution_loop(world, g, r, lc, rounds=rounds, seed=seed))
    keys = ["success", "synth_per_task", "covered", "deployed", "consolidated"]
    summary = [
        {"round": ri, **{k: round(statistics.mean(run[ri][k] for run in all_runs), 4) for k in keys}}
        for ri in range(rounds)
    ]
    return {"per_seed": all_runs, "summary": summary, "seeds": seeds, "rounds": rounds, "hold_out": hold_out}


def _fmt(summary) -> str:
    cols = ["round", "success", "synth_per_task", "covered", "deployed", "consolidated"]
    head = " ".join(f"{c:>14}" for c in cols)
    lines = [head, "-" * len(head)]
    for s in summary:
        lines.append(" ".join(f"{s[c]:>14}" for c in cols))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--hold-out", type=int, default=3)
    ap.add_argument("--out", default="results/evolve.json")
    args = ap.parse_args()
    res = run(args.seeds, args.rounds, args.hold_out)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    print(_fmt(res["summary"]))
    print(f"\n[saved] {args.out}  (seeds={args.seeds}, rounds={args.rounds}, hold_out={args.hold_out})")


if __name__ == "__main__":
    main()
