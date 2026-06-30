#!/usr/bin/env python3
"""Capability radar: SkillStrata vs no-skill across 6 axes (same backbone, same 280 held-out).
5 accuracy axes + 1 token-efficiency axis (normalized vs full-dump 2658 tok). Output: figs/fig_radar.png
"""
import os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
dims = ["Overall\nacc", "Cell-Level", "Sheet-Level", "Hard task\n(noskill failed)",
        "Easy task\n(noskill solved)", "Token eff.\n(less injected)"]
# token efficiency normalized: (1 - inject/full_dump_2658)*100  -> higher = leaner
def teff(tok): return (1 - tok / 2658.0) * 100
ss = [56.1, 52.3, 64.4, 43.8, 83.7, teff(239)]    # SkillStrata
ns = [30.7, 22.3, 49.4, 0.0, 100.0, teff(152)]    # no-skill

N = len(dims)
ang = [n / N * 2 * math.pi for n in range(N)] + [0]
def closed(v): return v + v[:1]

fig = plt.figure(figsize=(7.6, 7.0))
ax = plt.subplot(111, polar=True)
ax.set_theta_offset(math.pi / 2); ax.set_theta_direction(-1)
ax.set_xticks(ang[:-1]); ax.set_xticklabels(dims, fontsize=10)
ax.set_ylim(0, 100); ax.set_yticks([20, 40, 60, 80, 100])
ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=8, color="#888")
for series, name, col in [(ns, "no-skill", "#9aa7b4"), (ss, "SkillStrata (ours)", "#1f8f5f")]:
    ax.plot(ang, closed(series), color=col, lw=2.4, label=name)
    ax.fill(ang, closed(series), color=col, alpha=0.22)
# annotate SkillStrata values
for a, v in zip(ang[:-1], ss):
    ax.text(a, v + 5, f"{v:.0f}", color="#1f6f54", fontsize=9, ha="center", fontweight="bold")
ax.set_title("Capability radar — SkillStrata vs no-skill\n(same backbone q36 · same 280 held-out · 5 accuracy axes + 1 token-efficiency axis)",
             fontsize=11.5, pad=24)
ax.legend(loc="upper right", bbox_to_anchor=(1.18, 1.12), fontsize=10)
plt.tight_layout()
p = os.path.join(HERE, "figs", "fig_radar.png")
plt.savefig(p, dpi=150, bbox_inches="tight"); print("wrote", p)
print("note: Token eff. = (1 - inject_tokens/2658)*100; SS=239->%.0f, NS=152->%.0f" % (teff(239), teff(152)))
