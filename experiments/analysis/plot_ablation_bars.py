#!/usr/bin/env python3
"""Two core component-contribution bar charts that were missing:
  fig_inference_ablation.png — inference ablation (graph/agent/noverify/full/bm25 vs noskill)
  fig_evo_ablation.png       — evolution ablation (5 cells + r2 all-on baseline vs noskill)
Reads live scores where available. English labels (matplotlib has no CJK font); captions are in the HTML.
"""
import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(HERE, "figs")
R = os.path.join(HERE, "..", "..", "external/repos/Trace2Skill/runs")
NOSKILL = 30.7

def score(path):
    ids = set(open(os.path.join(HERE, "..", "..", "script/data/skillopt_test_ids.txt")).read().split())
    if not os.path.exists(path): return None
    d = json.load(open(path)); rs = {str(x["id"]): x["success"] for x in d["results"]}
    sel = [i for i in ids if i in rs]
    return sum(rs[i] for i in sel) / len(sel) * 100 if sel else None

# ---------- 1) inference ablation ----------
inf = [  # (label, val, kind)  kind: ours / drop / base
    ("graph routing (ours)", 58.6, "ours"),
    ("agent routing (ours)", 57.1, "ours"),
    ("complete (orig run)", 56.1, "ours"),
    ("no verify-loop", 44.3, "drop"),
    ("full-dump (all 34)", 43.6, "drop"),
    ("bm25 flat retrieval", 41.8, "drop"),
]
inf.sort(key=lambda x: x[1])
fig, ax = plt.subplots(figsize=(9.5, 4.8))
cmap = {"ours": "#27ae60", "drop": "#9fb3d0"}
y = range(len(inf))
ax.barh(list(y), [v for _, v, _ in inf], color=[cmap[k] for _, _, k in inf], edgecolor="#555", zorder=3)
for i, (_, v, _) in enumerate(inf):
    ax.text(v + 0.4, i, f"{v:.1f}", va="center", fontsize=10, fontweight="bold")
ax.axvline(NOSKILL, color="#c0392b", ls="--", lw=1.5, zorder=2)
ax.text(NOSKILL, len(inf) - 0.3, f" no-skill {NOSKILL}", color="#c0392b", fontsize=9, va="top")
ax.set_yticks(list(y)); ax.set_yticklabels([l for l, _, _ in inf], fontsize=10)
ax.set_xlabel("accuracy on 280 held-out (%)", fontsize=10); ax.set_xlim(0, 66)
ax.set_title("Inference ablation: which test-time component carries the gain\n"
             "graph≈agent (routing needn't be an LLM) · vs full/bm25 = +15pp (graph beats stacking) · "
             "verify-loop = -12.8pp", fontsize=10.5, loc="left")
ax.legend(handles=[Patch(fc="#27ae60", label="SkillStrata routing (with graph)"),
                   Patch(fc="#9fb3d0", label="baselines (no graph / no verify)")], fontsize=9, loc="lower right")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
plt.tight_layout(); p1 = os.path.join(FIGS, "fig_inference_ablation.png")
plt.savefig(p1, dpi=150, bbox_inches="tight"); print("wrote", p1)

# ---------- 2) evolution ablation ----------
r2 = score(os.path.join(R, "curate_fromzero", "evo_r2_test", "eval_official_results.json"))
evo = [
    ("no-split", 45.4), ("no-gate", 44.6), ("no-merge", 40.0),
    ("no-checkpoint", 33.2), ("only-insert (all off)", 32.1),
]
rows = list(evo)
if r2: rows.append(("r2 all-on (baseline)", r2))
rows.sort(key=lambda x: x[1])
fig, ax = plt.subplots(figsize=(9.5, 4.6))
def col(label, v):
    if "baseline" in label: return "#1f6f9f"
    return "#e0a36b"
y = range(len(rows))
ax.barh(list(y), [v for _, v in rows], color=[col(l, v) for l, v in rows], edgecolor="#555", zorder=3)
for i, (_, v) in enumerate(rows):
    tag = f"{v:.1f}" + (f"  (Δ{v-r2:+.1f})" if (r2 and 'baseline' not in rows[i][0]) else "")
    ax.text(v + 0.4, i, tag, va="center", fontsize=9.5, fontweight="bold")
ax.axvline(NOSKILL, color="#c0392b", ls="--", lw=1.5, zorder=2)
ax.text(NOSKILL, len(rows) - 0.3, f" no-skill {NOSKILL}", color="#c0392b", fontsize=9, va="top")
ax.set_yticks(list(y)); ax.set_yticklabels([l for l, _ in rows], fontsize=10)
ax.set_xlabel("accuracy on 280 held-out (%, round-2 early-stop)", fontsize=10); ax.set_xlim(0, 56)
sub = "vs r2 all-on baseline" if r2 else "(r2 all-on baseline pending)"
ax.set_title("Evolution ablation: which evolution component matters\n"
             f"disable one component, round-2 curate from scratch. {sub}. "
             "only-insert ≈ no-skill (organizing matters, not just inserting)", fontsize=10.5, loc="left")
ax.legend(handles=[Patch(fc="#e0a36b", label="one component disabled"),
                   Patch(fc="#1f6f9f", label="all-on baseline (r2)")], fontsize=9, loc="lower right")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
plt.tight_layout(); p2 = os.path.join(FIGS, "fig_evo_ablation.png")
plt.savefig(p2, dpi=150, bbox_inches="tight"); print("wrote", p2, "| r2 baseline =", r2)
