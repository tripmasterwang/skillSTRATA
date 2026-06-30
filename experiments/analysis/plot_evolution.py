#!/usr/bin/env python3
"""Visualize the from-zero curate evolution (fromzero, 4 rounds). Reads evolution_ledger.json.
Outputs:
  figs/fig_evo_lifecycle.png   per-skill lifecycle gantt (minted -> deployed/retired, gates)
  figs/fig_evo_val_growth.png  val curve + library growth, per-round events
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

HERE = os.path.dirname(__file__)
L = json.load(open(os.path.join(HERE, "evolution_ledger.json")))
hist = L["history"]; skills = L["skills"]
FINAL = 3.6   # x where "survives into final graph" ends

# round -> color
RC = {0: "#c0392b", 1: "#2e86de", 2: "#27ae60", 3: "#8e44ad"}

# ---------------- Figure 1: lifecycle gantt ----------------
dep = [s for s in skills if s["status"] == "deployed"]
ret = [s for s in skills if s["status"] == "retired"]
# order: deployed by mint round then trials desc (busy first); retired (all r0) at bottom
dep.sort(key=lambda s: (s["mint_round"], -(s["trials"] or 0)))
ret.sort(key=lambda s: s["name"])
ordered = dep + ret                       # top = deployed r1.., bottom = retired r0
n = len(ordered)
LAST = max(s["mint_round"] for s in skills if s["mint_round"] is not None)  # last curate round
fig, ax = plt.subplots(figsize=(11, 11))
for i, s in enumerate(ordered):
    y = n - 1 - i                         # top-down
    r = s["mint_round"]; col = RC[r]
    used = (s["trials"] or 0) > 0
    if s["status"] == "deployed":
        # trials==0 means two different things: minted in the LAST round (never had a later train
        # rollout to earn trials -> UNMEASURED) vs minted earlier but still never routed -> ZOMBIE.
        if used:
            hatch, alpha, tagcol = "", 0.95, "black"
        elif r == LAST:
            hatch, alpha, tagcol = "....", 0.45, "#9a6fb0"          # unmeasured (last round)
        else:
            hatch, alpha, tagcol = "////", 0.30, "#888"            # real zombie
        ax.barh(y, FINAL - r, left=r, height=0.62, color=col, alpha=alpha,
                hatch=hatch, edgecolor=col, linewidth=0.8, zorder=2)
        # checkpoint marker
        if s["checkpoint_round"] is not None:
            ax.scatter(s["checkpoint_round"] + 0.5, y, marker="D", s=42, color="black", zorder=4)
        # right-side succ / unused tag
        if used:
            tag = f"succ {s['succ']:.2f} (n={s['trials']})"
        elif r == LAST:
            tag = "unmeasured (minted last round, no later rollout)"
        else:
            tag = "zombie: never routed (n=0)"
        ax.text(FINAL + 0.05, y, tag, va="center", ha="left", fontsize=6.5, color=tagcol)
    else:   # retired (r0, gate-rejected)
        ax.barh(y, 0.7, left=0, height=0.62, color=RC[0], alpha=0.85,
                edgecolor=RC[0], hatch="xx", zorder=2)
        ax.text(0.75, y, "rejected by gate", va="center", ha="left", fontsize=6.5, color=RC[0])
    ax.text(-0.08, y, s["name"][:44], va="center", ha="right", fontsize=6.3)

ax.set_xlim(-0.05, FINAL + 1.7)
ax.set_ylim(-1, n)
ax.set_xticks([0, 1, 2, 3, FINAL])
ax.set_xticklabels(["R0", "R1", "R2", "R3", "final\ngraph"], fontsize=9)
ax.set_yticks([])
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
ax.axvline(0.85, color="#ddd", lw=0.8, zorder=0)
ax.set_title("SkillStrata from-zero evolution: per-skill lifecycle\n"
             "46 minted -> 34 deployed / 12 rejected (R0 whole round gate-rejected); 11 verify-gates",
             fontsize=11, loc="left")
leg = [Patch(fc=RC[1], label="minted R1"), Patch(fc=RC[2], label="minted R2"),
       Patch(fc=RC[3], label="minted R3"), Patch(fc=RC[0], hatch="xx", label="R0 rejected (retired)"),
       Patch(fc="#bbb", hatch="////", label="zombie: never routed despite 1-2 rollout chances (n=0)"),
       Patch(fc="#bbb", hatch="....", label="unmeasured: minted last round, no later rollout (n=0)"),
       Line2D([0],[0], marker="D", color="w", markerfacecolor="black", markersize=7,
              label="verify-gate (checkpoint)")]
ax.legend(handles=leg, loc="lower right", fontsize=7.5, framealpha=0.95)
plt.tight_layout()
f1 = os.path.join(HERE, "figs", "fig_evo_lifecycle.png")
plt.savefig(f1, dpi=150, bbox_inches="tight"); print("wrote", f1)

# ---------------- Figure 2: val curve + library growth ----------------
rounds = [h["round"] for h in hist]
val = [h["val"] for h in hist]
deployed_cum = [h["deployed"] for h in hist]
inserted = [h["inserted"] for h in hist]
merged = [h["merged"] for h in hist]
ckpt = [h["checkpoints"] for h in hist]
accepted = [h["accepted"] for h in hist]

fig, ax1 = plt.subplots(figsize=(9, 5.2))
ax2 = ax1.twinx()
# library growth (bars, right axis)
ax2.bar(rounds, deployed_cum, width=0.5, color="#dfe6f0", edgecolor="#9fb3d0", zorder=1,
        label="deployed skills (cumulative)")
for r, d in zip(rounds, deployed_cum):
    ax2.text(r, d + 0.6, str(d), ha="center", fontsize=8, color="#4a6fa5")
# val line (left axis)
ax1.plot(rounds, val, "-o", color="#c0392b", lw=2.2, ms=8, zorder=3, label="val accuracy")
for r, v, acc in zip(rounds, val, accepted):
    ax1.annotate(f"{v:.3f}", (r, v), textcoords="offset points", xytext=(0, 10),
                 ha="center", fontsize=8.5, color="#c0392b", fontweight="bold")
    mark = "ACCEPT" if acc else "REJECT (all minted retired)"
    ax1.annotate(mark, (r, v), textcoords="offset points", xytext=(0, -16), ha="center",
                 fontsize=7, color=("#27ae60" if acc else "#c0392b"))
# per-round event annotations along the top
for r in rounds:
    h = hist[r]
    ev = f"+{h['inserted']} mint"
    if h["merged"]: ev += f"\n{h['merged']} merged"
    if h["checkpoints"]: ev += f"\n+{h['checkpoints']} gates"
    ax1.text(r, 0.71, ev, ha="center", va="top", fontsize=6.8, color="#555")

ax1.set_xlabel("curate round", fontsize=10)
ax1.set_ylabel("val accuracy", color="#c0392b", fontsize=10)
ax2.set_ylabel("deployed skills (library size)", color="#4a6fa5", fontsize=10)
ax1.set_ylim(0.40, 0.73); ax2.set_ylim(0, 40)
ax1.set_xticks(rounds)
ax1.set_title("From-zero curate: val accuracy climbs as the library grows under the gate\n"
              "0.425 -> 0.475 -> 0.55 -> 0.60   |   0 -> 12 -> 22 -> 34 deployed", fontsize=11, loc="left")
ax1.tick_params(axis="y", labelcolor="#c0392b")
ax2.tick_params(axis="y", labelcolor="#4a6fa5")
ax1.set_zorder(ax2.get_zorder() + 1); ax1.patch.set_visible(False)
h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc="lower right", fontsize=8, framealpha=0.95)
plt.tight_layout()
f2 = os.path.join(HERE, "figs", "fig_evo_val_growth.png")
plt.savefig(f2, dpi=150, bbox_inches="tight"); print("wrote", f2)
