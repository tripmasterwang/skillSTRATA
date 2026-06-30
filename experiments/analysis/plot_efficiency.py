#!/usr/bin/env python3
"""Context efficiency: per-task skill-context tokens injected. SkillStrata routes ~3 skills/task;
baselines (full-dump) and SkillOpt (monolithic doc) inject everything every task. Output:
figs/fig_efficiency_context.png"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
HERE = os.path.dirname(__file__)
# (label, tokens/task, is_ours)
rows = [
    ("no-skill (SkillOpt base)", 152, False),
    ("SkillStrata (ours)\nselective routing ~3 skills", 239, True),
    ("human (SkillOpt)", 537, False),
    ("skill-creator (SkillOpt)", 699, False),
    ("SkillOpt self-train\n(claude; q36 same-bb=1615)", 1753, False),
    ("full-dump (ours ablation)\nall 34 skills", 2658, False),
    ("SkillOpt ckpt", 3471, False),
]
rows.sort(key=lambda r: r[1])
labels = [r[0] for r in rows]; vals = [r[1] for r in rows]
cols = ["#27ae60" if r[2] else "#9fb3d0" for r in rows]
fig, ax = plt.subplots(figsize=(9.5, 4.6))
y = range(len(rows))
ax.barh(list(y), vals, color=cols, edgecolor="#555", zorder=2)
base = 239
for i, v in enumerate(vals):
    note = f"{v} tok/task" + ("" if v == base else f"   ({v/base:.1f}× ours)")
    ax.text(v + 40, i, note, va="center", fontsize=9, fontweight=("bold" if v == base else "normal"))
ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=8.5)
ax.set_xlabel("skill-context tokens injected per task (lower = cheaper)", fontsize=9)
ax.set_xlim(0, max(vals) * 1.28)
ax.set_title("Context efficiency: per-task skill-context injected\n"
             "SkillStrata routes a 3-skill subgraph; full-dump & SkillOpt inject the whole library every task",
             fontsize=10.5, loc="left")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
plt.tight_layout()
f = os.path.join(HERE, "figs", "fig_efficiency_context.png")
plt.savefig(f, dpi=150, bbox_inches="tight"); print("wrote", f)
