"""Test-time adaptation experiment (proposal: trace-graph lego-style synthesis).

    python -m sim.run_tta --seeds 0 1 2 3 4 --hold-out 3

Setup: per domain, the K most-needed atomic sub-capabilities are *held out* of the deployed
skill pool — tasks still need them, but no routable skill covers them (a capability gap that a
purely route-over-deployed-skills system cannot close). We compare:

  * SkillOS (full skills, ref) — no gap; upper reference.
  * SkillOS (-held, no TTA)    — gap present, route only over deployed skills.
  * SkillOS (-held, +TTA)      — gap present, but reassemble the missing capability at test time
                                 from the trace layer's co-occurrence evidence.

If TTA works, the +TTA row recovers coverage / OOD success toward the no-gap reference, while
keeping token cost modest — demonstrating trace-graph test-time adaptation, not just routing.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics

from .tasks import build_world
from .harness import run_method
from . import builders

ORDER = ["SkillOS (full skills, ref)", "SkillOS (-held, no TTA)", "SkillOS (-held, +TTA)"]


def _variants(world, hold_out: int):
    g0, r0, lc0 = builders.build_skillos(world, hold_out=0, tta=False)
    g1, r1, lc1 = builders.build_skillos(world, hold_out=hold_out, tta=False)
    g2, r2, lc2 = builders.build_skillos(world, hold_out=hold_out, tta=True)
    return {
        ORDER[0]: (g0, r0, lc0),
        ORDER[1]: (g1, r1, lc1),
        ORDER[2]: (g2, r2, lc2),
    }


def run(seeds: list[int], hold_out: int) -> dict:
    rows: dict[str, list] = {k: [] for k in ORDER}
    for seed in seeds:
        world = build_world(seed=seed)
        for name, (g, r, lc) in _variants(world, hold_out).items():
            m = run_method(world, g, r, lc, seed=seed, validate=True, inject=False)
            rows[name].append(m.as_row())
    summary = {}
    for name, rs in rows.items():
        keys = rs[0].keys()
        summary[name] = {k: round(statistics.mean(r[k] for r in rs), 4) for k in keys}
    return {"per_seed": rows, "summary": summary, "seeds": seeds, "hold_out": hold_out}


def _fmt(summary: dict) -> str:
    cols = ["success", "id_success", "ood_success", "covered", "tokens", "synth"]
    head = f"{'Variant':<28} " + " ".join(f"{c:>12}" for c in cols)
    lines = [head, "-" * len(head)]
    for name in ORDER:
        s = summary[name]
        lines.append(f"{name:<28} " + " ".join(f"{s[c]:>12}" for c in cols))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--hold-out", type=int, default=3)
    ap.add_argument("--out", default="results/tta.json")
    args = ap.parse_args()
    res = run(args.seeds, args.hold_out)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    print(_fmt(res["summary"]))
    print(f"\n[saved] {args.out}  (seeds={args.seeds}, hold_out={args.hold_out})")


if __name__ == "__main__":
    main()
