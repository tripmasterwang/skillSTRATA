#!/usr/bin/env python3
"""Per-round improvement curve on the 280 held-out test, split by category (Cell/Sheet) and by
difficulty (noskill-behavioral: easy=noskill solved, hard=noskill failed). Rounds:
  r0 = noskill (empty graph), r1/r2 = reconstructed intermediate graphs, r3 = final trained graph.
Handles missing rounds (skips points whose eval json is absent) so it can be run as soon as r1 is in
and re-run when r2 lands. Outputs figs/fig_perround_category.png + fig_perround_difficulty.png.
Also prints the numbers for CONVERGENCE.md §E (test convergence)."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = os.path.join(os.path.dirname(__file__), "..", "..", "external/repos/Trace2Skill/runs/curate_fromzero")
TESTIDS = [x.strip() for x in open(os.path.join(os.path.dirname(__file__), "..", "..", "script/data/skillopt_test_ids.txt"))]
ROUNDS = [
    ("r0\n(noskill)", "test_280_noskill"),
    ("r1\n(13 sk)", "evo_r1_test"),
    ("r2\n(23 sk)", "evo_r2_test"),
    ("r3\n(final 34)", "test_280"),
]

def load(sub):
    p = os.path.join(R, sub, "eval_official_results.json")
    if not os.path.exists(p): return None
    d = json.load(open(p))
    return {str(x["id"]): x for x in d["results"]}

evals = {lab: load(sub) for lab, sub in ROUNDS}
# category (fixed per task) + difficulty group (from noskill behavior)
ref = evals["r3\n(final 34)"] or next(v for v in evals.values() if v)
itype = {i: ref[i].get("instruction_type") for i in ref}
nos = evals["r0\n(noskill)"]
easy = {i for i in TESTIDS if nos and i in nos and nos[i]["success"]}
hard = {i for i in TESTIDS if nos and i in nos and not nos[i]["success"]}

def acc(ev, ids):
    ids = [i for i in ids if ev and i in ev]
    return (sum(ev[i]["success"] for i in ids) / len(ids) * 100) if ids else None

labels = [lab for lab, _ in ROUNDS]
xs = list(range(len(ROUNDS)))
cats = {"Cell-Level": [i for i in TESTIDS if itype.get(i) == "Cell-Level Manipulation"],
        "Sheet-Level": [i for i in TESTIDS if itype.get(i) == "Sheet-Level Manipulation"],
        "Overall": TESTIDS}
diffs = {"easy (noskill solved)": easy, "hard (noskill failed)": hard}

def plot(groups, title, fname, colors):
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    for (name, ids), col in zip(groups.items(), colors):
        ys = [acc(evals[lab], ids) for lab in labels]
        xx = [x for x, y in zip(xs, ys) if y is not None]
        yy = [y for y in ys if y is not None]
        ax.plot(xx, yy, "-o", color=col, lw=2.2, ms=8, label=f"{name} (n={len(ids)})")
        for x, y in zip(xx, yy):
            ax.annotate(f"{y:.0f}", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8, color=col)
    ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("accuracy on 280 held-out (%)"); ax.set_ylim(-3, 103)
    ax.set_title(title, fontsize=11, loc="left"); ax.grid(axis="y", alpha=0.25)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.legend(fontsize=9)
    missing = [lab.split(chr(10))[0] for lab in labels if evals[lab] is None]
    if missing: ax.text(0.02, 0.02, f"pending rounds: {', '.join(missing)}", transform=ax.transAxes, fontsize=8, color="#c0392b")
    plt.tight_layout(); p = os.path.join(os.path.dirname(__file__), "figs", fname)
    plt.savefig(p, dpi=150, bbox_inches="tight"); print("wrote", p)

plot(cats, "Per-round test accuracy by category (SkillStrata evolution)", "fig_perround_category.png",
     ["#2e86de", "#27ae60", "#888"])
plot(diffs, "Per-round test accuracy by difficulty (noskill-behavioral)", "fig_perround_difficulty.png",
     ["#27ae60", "#c0392b"])

print("\n=== per-round numbers (for CONVERGENCE.md §E / DIFFICULTY_BREAKDOWN.md §B) ===")
for lab in labels:
    if evals[lab] is None: print(f"  {lab.replace(chr(10),' ')}: PENDING"); continue
    print(f"  {lab.replace(chr(10),' ')}: overall={acc(evals[lab],TESTIDS):.1f}  "
          f"Cell={acc(evals[lab],cats['Cell-Level']):.1f}  Sheet={acc(evals[lab],cats['Sheet-Level']):.1f}  "
          f"easy={acc(evals[lab],easy):.1f}  hard={acc(evals[lab],hard):.1f}")
