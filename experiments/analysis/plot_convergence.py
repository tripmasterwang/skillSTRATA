#!/usr/bin/env python3
"""Convergence: held-out score over evolution steps, ours vs SkillOpt self-train (both q36 backbone,
SpreadsheetBench). Ours climbs monotonically; SkillOpt self-train's selection score is flat.
Output: figs/fig_convergence.png"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
HERE = os.path.dirname(__file__)

rounds = [0, 1, 2, 3]
ours_val = [0.425, 0.475, 0.55, 0.60]          # our held-out val (n=40), curate_history
sk_sel = [0.273, 0.273]                          # SkillOpt selection/val (n=11): baseline -> final (flat)

fig, ax = plt.subplots(figsize=(8.6, 5.2))
ax.plot(rounds, ours_val, "-o", color="#27ae60", lw=2.4, ms=9,
        label="SkillStrata (ours) — held-out val (n=40)")
for x, y in zip(rounds, ours_val):
    ax.annotate(f"{y:.3f}", (x, y), textcoords="offset points", xytext=(0, 9), ha="center",
                fontsize=8.5, color="#1e7e44", fontweight="bold")
# SkillOpt: only baseline (step0) and final (step4) selection scores -> flat
ax.plot([0, 3], sk_sel, "--s", color="#c0392b", lw=2.0, ms=8,
        label="SkillOpt self-train — selection (n=11)")
ax.annotate("0.273 (baseline)", (0, 0.273), textcoords="offset points", xytext=(4, -16), fontsize=8, color="#c0392b")
ax.annotate("0.273 (after 4 steps — flat)", (3, 0.273), textcoords="offset points", xytext=(-30, -16), fontsize=8, color="#c0392b")

ax.set_xlabel("evolution step / curate round", fontsize=10)
ax.set_ylabel("held-out score", fontsize=10)
ax.set_xticks(rounds); ax.set_ylim(0.20, 0.66)
ax.set_title("Convergence: SkillStrata climbs, SkillOpt self-train is flat (both q36, SpreadsheetBench)\n"
             "ours val +17.5pp over 4 rounds  ·  SkillOpt selection +0.0pp; "
             "build cost: ours ~2.49M tok (est) vs SkillOpt 6.84M tok (logged, 4 steps)",
             fontsize=9.5, loc="left")
ax.legend(loc="center right", fontsize=9)
ax.grid(axis="y", alpha=0.25)
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
# end-to-end test deltas as a side note
ax.text(0.02, 0.04, "held-out TEST Δ (same backbone):  ours 30.7→56.1 (+25.4pp)   |   "
        "SkillOpt 46.0→55.2 (+9.2pp)", transform=ax.transAxes, fontsize=8.2,
        bbox=dict(boxstyle="round", fc="#eef6ef", ec="#27ae60"))
plt.tight_layout()
f = os.path.join(HERE, "figs", "fig_convergence.png")
plt.savefig(f, dpi=150, bbox_inches="tight"); print("wrote", f)
