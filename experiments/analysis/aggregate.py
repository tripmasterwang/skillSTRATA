#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only aggregation + plotting for SkillStrata analysis."""
import json, os, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/projects/skillSTRATA"
RUNS = os.path.join(ROOT, "external/repos/Trace2Skill/runs")
SKILLOPT = "/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/projects/nonergodic-self-evolution/external/SkillOpt/outputs/harness_ms"
OUT = os.path.join(ROOT, "experiments/analysis")
FIGS = os.path.join(OUT, "figs")
os.makedirs(FIGS, exist_ok=True)

def jload(p):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception as e:
        return {"_error": str(e)}

def eval_summary(test_dir):
    """Return dict from eval_official_results.json summary."""
    p = os.path.join(test_dir, "eval_official_results.json")
    if not os.path.exists(p):
        return None
    d = jload(p)
    s = d.get("summary", {})
    res = d.get("results", [])
    return {
        "path": p,
        "N": s.get("total_instances"),
        "passed": s.get("fully_correct_instances"),
        "instance_acc": s.get("instance_accuracy"),
        "hard": s.get("avg_hard_score"),
        "soft": s.get("avg_soft_score"),
        "n_results": len(res),
    }

agg = {"ours_evolution": {}, "ours_curate_test": {}, "ours_fromzero_3tier": {},
       "ours_strongbase_comparison": {}, "skillopt_matrix": {}, "_meta": {}}

# ---------- 1. ours evolution trajectories ----------
for h in ["fromzero", "codex", "claude", "minisweagent"]:
    hp = os.path.join(RUNS, f"curate_{h}/curate_history.json")
    hist = jload(hp)
    graph = jload(os.path.join(RUNS, f"curate_{h}/trained_graph.json"))
    gov = graph.get("governance", [])
    kinds = collections.Counter(x.get("kind") for x in gov)
    agg["ours_evolution"][h] = {
        "history_path": hp,
        "rounds": [{"round": x.get("round"), "val": x.get("val"),
                    "accepted": x.get("accepted"), "inserted": x.get("inserted"),
                    "merged": x.get("merged"), "deployed": x.get("deployed")} for x in hist],
        "graph_path": os.path.join(RUNS, f"curate_{h}/trained_graph.json"),
        "skills": len(graph.get("skills", [])),
        "capability_edges": len(graph.get("capability_edges", [])),
        "governance_total": len(gov),
        "governance_kinds": dict(kinds),
        "real_checkpoints": kinds.get("checkpoint", 0),
    }
    # curate test_280 (graph routing)
    es = eval_summary(os.path.join(RUNS, f"curate_{h}/test_280"))
    if es:
        agg["ours_curate_test"][h] = es

# ---------- 2. fromzero 3-tier cross-harness ----------
tiers = {
    "codex":        ["test_280_codex_bare", "test_280_codex_skill", "test_280_codex"],
    "claude":       ["test_280_claude_bare", "test_280_claude_skill", "test_280_claude"],
    "minisweagent": ["test_280_minisweagent_bare", "test_280_minisweagent_skill", "test_280_minisweagent"],
}
labels = ["bare", "skill", "skillstrata"]
for harness, dirs in tiers.items():
    agg["ours_fromzero_3tier"][harness] = {}
    for lab, dn in zip(labels, dirs):
        es = eval_summary(os.path.join(RUNS, "curate_fromzero", dn))
        agg["ours_fromzero_3tier"][harness][lab] = es
# also noskill + main skillstrata graph (fromzero/test_280)
agg["ours_fromzero_3tier"]["_noskill"] = eval_summary(os.path.join(RUNS, "curate_fromzero/test_280_noskill"))
agg["ours_fromzero_3tier"]["_skillstrata_graph"] = eval_summary(os.path.join(RUNS, "curate_fromzero/test_280"))

# ---------- 3. strong-base COMPARISON.md (parse the markdown table) ----------
comp = {}
cmp_path = os.path.join(RUNS, "COMPARISON.md")
with open(cmp_path) as f:
    for line in f:
        if line.startswith("|") and "%" in line and "Instance Acc" not in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            run = cells[0]
            acc = cells[1].split("%")[0].strip()
            try:
                comp[run] = {"instance_acc_hard_pct": float(acc), "raw": cells[1]}
            except Exception:
                pass
agg["ours_strongbase_comparison"] = {"source": cmp_path, "N": 400, "rows": comp}

# ---------- 4. SkillOpt competitor matrix ----------
benches = ["officeqa", "spreadsheetbench", "searchqa", "alfworld"]
harnesses = ["codex", "claude"]
tiers_so = ["noskill", "human", "skillcreator", "skillopt_ckpt", "skillopt_self"]
mat = {}
for b in benches:
    mat[b] = {}
    for hn in harnesses:
        mat[b][hn] = {}
        for t in tiers_so:
            vals = {}
            for seed in range(1, 6):
                # handle both underscore and hyphen variants
                cands = [f"{b}_{hn}_{t}_s{seed}", f"{b}_{hn}-{t}_s{seed}"]
                found = None
                for c in cands:
                    p = os.path.join(SKILLOPT, c, "eval_summary.json")
                    if os.path.exists(p):
                        found = p; break
                if found:
                    d = jload(found)
                    vals[seed] = {"hard": d.get("hard"), "soft": d.get("soft"),
                                  "n": d.get("n_items"), "path": found}
            if vals:
                hard_vals = [v["hard"] for v in vals.values() if v["hard"] is not None]
                mat[b][hn][t] = {
                    "seeds": vals,
                    "n_seeds": len(vals),
                    "mean_hard": sum(hard_vals)/len(hard_vals) if hard_vals else None,
                    "n_items": next(iter(vals.values()))["n"],
                }
            else:
                mat[b][hn][t] = None
agg["skillopt_matrix"] = {"source_root": SKILLOPT, "data": mat}

# ---------- write agg json ----------
with open(os.path.join(OUT, "agg_results.json"), "w") as f:
    json.dump(agg, f, indent=2, ensure_ascii=False)
print("wrote agg_results.json")

# ================= FIGURES =================
# fig1 evolution curves
fig, ax = plt.subplots(figsize=(8, 5))
colors = {"fromzero": "tab:blue", "codex": "tab:orange", "claude": "tab:green", "minisweagent": "tab:red"}
for h, info in agg["ours_evolution"].items():
    rs = info["rounds"]
    x = [r["round"] for r in rs]
    y = [r["val"] for r in rs]
    ax.plot(x, y, marker="o", label=h, color=colors.get(h))
    for r in rs:
        if r["accepted"] is False:
            ax.annotate("X", (r["round"], r["val"]), color="red", fontsize=11,
                        fontweight="bold", ha="center", va="bottom")
ax.set_xlabel("curate round")
ax.set_ylabel("validation accuracy")
ax.set_title("Fig1: Self-evolution val acc per round (X = rejected by validation gate)")
ax.set_xticks([0,1,2,3])
ax.legend(title="seed harness")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIGS, "fig1_evolution_curves.png"), dpi=130)
plt.close(fig)
print("fig1 done")

# fig2 cross-harness 3tier
fig, ax = plt.subplots(figsize=(9, 5.5))
harnesses3 = ["codex", "claude", "minisweagent"]
import numpy as np
x = np.arange(len(harnesses3))
w = 0.25
tier_colors = {"bare": "#bbbbbb", "skill": "#7fb3d5", "skillstrata": "#1f77b4"}
for i, lab in enumerate(labels):
    ys = []
    for hn in harnesses3:
        es = agg["ours_fromzero_3tier"][hn][lab]
        ys.append((es["instance_acc"]*100) if es and es.get("instance_acc") is not None else 0)
    bars = ax.bar(x + (i-1)*w, ys, w, label=lab, color=tier_colors[lab])
    for b_, yv in zip(bars, ys):
        ax.annotate(f"{yv:.1f}", (b_.get_x()+b_.get_width()/2, yv), ha="center", va="bottom", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(harnesses3)
ax.set_ylabel("instance accuracy (%) on official-400")
ax.set_title("Fig2: Cross-harness 3-tier (bare / skill / skillstrata) — fromzero test_280")
ax.legend()
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIGS, "fig2_cross_harness_3tier.png"), dpi=130)
plt.close(fig)
print("fig2 done")

# fig3 skillopt matrix
fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharey=True)
tier_color = {"noskill":"#999999","human":"#f0ad4e","skillcreator":"#5bc0de",
              "skillopt_ckpt":"#5cb85c","skillopt_self":"#1f77b4"}
for ax, hn in zip(axes, harnesses):
    x = np.arange(len(benches))
    nt = len(tiers_so); w = 0.16
    for i, t in enumerate(tiers_so):
        ys = []
        for b in benches:
            cell = agg["skillopt_matrix"]["data"][b][hn][t]
            ys.append((cell["mean_hard"]*100) if cell and cell.get("mean_hard") is not None else 0)
        ax.bar(x + (i-(nt-1)/2)*w, ys, w, label=t, color=tier_color[t])
    ax.set_xticks(x); ax.set_xticklabels(benches, rotation=20)
    ax.set_title(f"harness={hn}")
    ax.set_ylabel("mean hard acc (%) over seeds")
    ax.grid(axis="y", alpha=0.3)
axes[0].legend(fontsize=8, ncol=2)
fig.suptitle("Fig3: SkillOpt competitor matrix (5 tiers x 4 benches), mean over available seeds")
fig.tight_layout()
fig.savefig(os.path.join(FIGS, "fig3_skillopt_matrix.png"), dpi=130)
plt.close(fig)
print("fig3 done")

# fig4 graph composition fromzero governance
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
fz = agg["ours_evolution"]["fromzero"]
kinds = fz["governance_kinds"]
ax1.bar(list(kinds.keys()), list(kinds.values()), color="tab:purple")
for i,(k,v) in enumerate(kinds.items()):
    ax1.annotate(str(v),(i,v),ha="center",va="bottom")
ax1.set_title(f"Fig4a: fromzero governance kinds (total={fz['governance_total']}, real checkpoints={fz['real_checkpoints']})")
ax1.tick_params(axis="x", rotation=25)
ax1.set_ylabel("count")
# pie of skills/edges/gov composition
comp_vals = [fz["skills"], fz["capability_edges"], fz["governance_total"]]
ax2.pie(comp_vals, labels=[f"skills={fz['skills']}", f"cap_edges={fz['capability_edges']}", f"gov={fz['governance_total']}"],
        autopct="%1.0f%%", colors=["#7fb3d5","#5cb85c","#c39bd3"])
ax2.set_title("Fig4b: fromzero trained_graph 3-layer composition")
fig.tight_layout()
fig.savefig(os.path.join(FIGS, "fig4_graph_composition.png"), dpi=130)
plt.close(fig)
print("fig4 done")
print("ALL DONE")
