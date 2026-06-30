#!/usr/bin/env python3
"""Test-time component usage frequency (main test_280, agent router, the 56.1 run).
Reads test_280/routes/*.json (per-task: nodes routed, guarded=gated-and-routed) + evolution_ledger
(which skills carry a verify-gate). Answers: at test time, which skills are actually used, how often,
which carry a gate, and how many skills are dead weight.

Output: figs/fig_test_usage.png
"""
import json, glob, os, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

HERE = os.path.dirname(__file__)
R = os.path.join(HERE, "..", "..", "external/repos/Trace2Skill/runs/curate_fromzero")
g = json.load(open(os.path.join(R, "trained_graph.json")))
skills = g["skills"]; skills = list(skills.values()) if isinstance(skills, dict) else skills
id2name = {s["id"]: s["name"] for s in skills}
dep_ids = {s["id"] for s in skills if s["status"] == "deployed"}
L = json.load(open(os.path.join(HERE, "evolution_ledger.json")))
gated_names = {s["name"] for s in L["skills"] if s["checkpoint_round"] is not None}
TOOL = {"Verify Library Names Before Execution", "Use Heredocs for Multi-line Python", "Robust Script Execution",
        "Safe_Embedded_Code_Execution", "JSON Command Formatting for Bash Tool", "JSON Escaping for Embedded Scripts",
        "Action Schema Strictness", "avoid_literal_newlines_in_tool_json", "Verify Library Names Before Importing",
        "transition_from_exploration_to_execution", "guarantee_output_file_generation"}

files = glob.glob(os.path.join(R, "test_280", "routes", "*.json"))
freq = collections.Counter(); ntask = len(files); sizes = []
guarded_tasks = 0
for f in files:
    rj = json.load(open(f)); nodes = rj.get("nodes", []); sizes.append(len(nodes))
    if rj.get("guarded"): guarded_tasks += 1
    for nid in nodes: freq[nid] += 1

used = [(id2name[i], freq[i]) for i in dep_ids if freq[i] > 0]
used.sort(key=lambda x: x[1])
never = [id2name[i] for i in dep_ids if freq[i] == 0]
n_tool_never = sum(1 for n in never if n in TOOL)

fig, ax = plt.subplots(figsize=(10.5, 8))
y = list(range(len(used)))
bars = ax.barh(y, [c for _, c in used], color="#2e86de", edgecolor="#1b4f72", zorder=2)
for i, (nm, c) in enumerate(used):
    # gate marker
    if nm in gated_names:
        ax.scatter(c + 2, i, marker="D", s=40, color="black", zorder=4)
    ax.text(c + (6 if nm in gated_names else 3), i, str(c), va="center", fontsize=7.5)
ax.set_yticks(y); ax.set_yticklabels([nm[:44] for nm, _ in used], fontsize=7.5)
ax.set_xlabel("times routed across the 280 test tasks", fontsize=9)
ax.set_xlim(0, max(c for _, c in used) * 1.16)

# dead-weight summary box at the bottom
ax.text(max(c for _, c in used) * 0.40, 0.4,
        f"+ {len(never)} deployed skills NEVER routed at test\n"
        f"   (incl. {n_tool_never} tool-class skills, all 0 use)",
        fontsize=9, color="#c0392b", va="bottom",
        bbox=dict(boxstyle="round", fc="#fdecea", ec="#c0392b"))

ax.set_title("Test-time component usage frequency  (main test_280, agent router, 56.1%)\n"
             f"only {len(used)}/{len(dep_ids)} deployed skills are ever routed · mean "
             f"{sum(sizes)/len(sizes):.2f} skills/task · verify-gates cover {guarded_tasks}/{ntask} "
             f"({guarded_tasks/ntask*100:.0f}%) tasks", fontsize=10.5, loc="left")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.legend(handles=[Patch(fc="#2e86de", label="routed at test (count on bar)"),
                   Line2D([0],[0], marker="D", color="w", markerfacecolor="black", markersize=7,
                          label="carries a verify-gate")],
          loc="lower right", fontsize=8)
plt.tight_layout()
f = os.path.join(HERE, "figs", "fig_test_usage.png")
plt.savefig(f, dpi=150, bbox_inches="tight"); print("wrote", f)
print(f"used={len(used)} never={len(never)} tool_never={n_tool_never} mean_size={sum(sizes)/len(sizes):.2f} gate_cover={guarded_tasks}/{ntask}")
