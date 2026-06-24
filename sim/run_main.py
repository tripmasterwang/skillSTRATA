"""Main results table (proposal §"Expected Main Result").

    python -m sim.run_main --seeds 0 1 2 --out results/main.json

Reproduces the comparison: No Skill / Trace2Skill / Flat Bank / Pruning-only / SkillOS.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics

from .tasks import build_world
from .harness import run_method
from . import builders


METHODS = ["No Skill", "Trace2Skill", "Flat Skill Bank", "Pruning-only", "SkillOS"]


def _build(name: str, world):
    """Return (graph, router, lifecycle, validate). Only SkillOS has the validation gate."""
    if name == "No Skill":
        g, r = builders.build_no_skill(world); return g, r, None, False
    if name == "Trace2Skill":
        g, r = builders.build_trace2skill(world); return g, r, None, False
    if name == "Flat Skill Bank":
        g, r = builders.build_flat_bank(world); return g, r, None, False
    if name == "Pruning-only":
        g, r, lc = builders.build_pruning(world); return g, r, lc, False
    if name == "SkillOS":
        g, r, lc = builders.build_skillos(world); return g, r, lc, True
    raise ValueError(name)


def run(seeds: list[int]) -> dict:
    rows: dict[str, list] = {m: [] for m in METHODS}
    for seed in seeds:
        world = build_world(seed=seed)
        for m in METHODS:
            g, r, lc, validate = _build(m, world)
            # main table isolates skill organization + routing (no harmful-skill stressor;
            # that robustness study lives in run_ablations).
            metrics = run_method(world, g, r, lc, seed=seed, validate=validate, inject=False)
            rows[m].append(metrics.as_row())
    # average across seeds
    summary = {}
    for m, rs in rows.items():
        keys = rs[0].keys()
        summary[m] = {k: round(statistics.mean(r[k] for r in rs), 4) for k in keys}
    # OOD Transfer Gain = OOD success improvement over the No-Skill baseline (proposal §Metrics)
    base = summary["No Skill"]["ood_success"]
    for m in summary:
        summary[m]["ood_gain"] = round(summary[m]["ood_success"] - base, 4)
    return {"per_seed": rows, "summary": summary, "seeds": seeds}


def _fmt_table(summary: dict) -> str:
    cols = ["success", "tokens", "loaded", "neg_transfer", "ood_gain", "route_precision", "bank_size"]
    head = f"{'Method':<16} " + " ".join(f"{c:>14}" for c in cols)
    lines = [head, "-" * len(head)]
    for m in METHODS:
        s = summary[m]
        lines.append(f"{m:<16} " + " ".join(f"{s[c]:>14}" for c in cols))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--out", default="results/main.json")
    args = ap.parse_args()

    res = run(args.seeds)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    print(_fmt_table(res["summary"]))
    print(f"\n[saved] {args.out}  (seeds={args.seeds})")


if __name__ == "__main__":
    main()
