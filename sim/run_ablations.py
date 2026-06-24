"""Ablation study (proposal §"Ablation Study").

    python -m sim.run_ablations --seeds 0 1 2 --out results/ablations.json

Variants:
  1. w/o Graph Routing       -> SkillOS graph but flat BM25 retrieval
  2. w/o Split               -> keep monoliths, route over graph
  3. w/o Lifecycle Validation-> no lifecycle housekeeping (no promote/retire)
  4. w/o Governance Graph    -> drop conflict/block edges
  5. Full Skill Loading      -> load all deployed skills
  6. Flat Skill Bank         -> atomics, no edges
  + SkillOS (full) reference row.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics

from skillos import GraphRouter, FlatRouter
from .tasks import build_world
from .harness import run_method
from . import builders


def _variants(world):
    """Return {name: (graph, router, lifecycle, validate)}."""
    out = {}

    g, r, lc = builders.build_skillos(world)
    out["SkillOS (full)"] = (g, r, lc, True)

    g, r, lc = builders.build_skillos(world, do_route=False)
    out["w/o Graph Routing"] = (g, r, lc, True)

    g, r, lc = builders.build_skillos(world, do_split=False)
    out["w/o Split"] = (g, r, lc, True)

    # isolate the validation gate: lifecycle (govern + retire) stays on, only validate=False
    g, r, lc = builders.build_skillos(world)
    out["w/o Lifecycle Validation"] = (g, r, lc, False)

    g, r, lc = builders.build_skillos(world, do_governance=False)
    out["w/o Governance Graph"] = (g, r, lc, True)

    # remove BOTH safety nets — validation gate and governance blocking
    g, r, lc = builders.build_skillos(world, do_governance=False)
    out["w/o Valid.+Govern."] = (g, r, lc, False)

    g, r, lc = builders.build_skillos(world)
    out["Full Skill Loading"] = (g, FlatRouter(g, mode="full"), lc, True)

    g, r = builders.build_flat_bank(world)
    out["Flat Skill Bank"] = (g, r, None, False)
    return out


ORDER = [
    "SkillOS (full)", "w/o Graph Routing", "w/o Split", "w/o Lifecycle Validation",
    "w/o Governance Graph", "w/o Valid.+Govern.", "Full Skill Loading", "Flat Skill Bank",
]


def run(seeds: list[int]) -> dict:
    rows: dict[str, list] = {k: [] for k in ORDER}
    for seed in seeds:
        world = build_world(seed=seed)
        for name, (g, r, lc, validate) in _variants(world).items():
            # frequent harmful-skill injection stresses the safety mechanisms
            rows[name].append(
                run_method(world, g, r, lc, seed=seed, validate=validate,
                           inject=True, inject_every=25, lifecycle_every=25).as_row()
            )
    summary = {}
    for name, rs in rows.items():
        keys = rs[0].keys()
        summary[name] = {k: round(statistics.mean(r[k] for r in rs), 4) for k in keys}
    return {"per_seed": rows, "summary": summary, "seeds": seeds}


def _fmt(summary: dict) -> str:
    cols = ["success", "tokens", "neg_transfer", "route_precision", "late_success", "stability"]
    head = f"{'Variant':<26} " + " ".join(f"{c:>14}" for c in cols)
    lines = [head, "-" * len(head)]
    for name in ORDER:
        s = summary[name]
        lines.append(f"{name:<26} " + " ".join(f"{s[c]:>14}" for c in cols))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--out", default="results/ablations.json")
    args = ap.parse_args()
    res = run(args.seeds)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    print(_fmt(res["summary"]))
    print(f"\n[saved] {args.out}  (seeds={args.seeds})")


if __name__ == "__main__":
    main()
