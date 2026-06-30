#!/usr/bin/env python3
"""What did evolution actually evolve? Group the 34 deployed skills by the CONTENT of their bodies
(manual categorization, anchored to real skill text) and show how much each theme is actually used
(total routing trials). Answers RQ1: the library is a small set of robust-openpyxl coding habits,
dominated by "compute in Python, write static values (not fragile Excel formulas)".

Output: figs/fig_evo_content_themes.png
"""
import json, os, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
L = json.load(open(os.path.join(HERE, "evolution_ledger.json")))
dep = {s["name"]: s for s in L["skills"] if s["status"] == "deployed"}

# theme -> exact skill names (manual, grounded in body text). English labels to match figs 1-2.
THEMES = [
 ("Compute in Python, write static values\n(not fragile Excel formulas)",
  ["precompute_and_write_static_values", "Python Computation Over Live Formulas", "In-Memory Lookup Mapping"]),
 ("Dynamic ranges via max_row\n(never hardcode limits)",
  ["targeted_column_population", "Dynamic Range Detection", "openpyxl_max_column_attribute",
   "Dynamic Range Determination", "dynamic_range_detection", "DynamicRangeDetection"]),
 ("Text parsing & robust matching",
  ["parse_text_range_for_inclusive_count", "Safe String Matching in Cells", "partial_case_insensitive_matching"]),
 ("Safe row delete/insert\n(iterate backwards)",
  ["Safe Backward Row Deletion", "SafeRowModificationIteration", "Backward Row Deletion"]),
 ("openpyxl value/type/error/date handling",
  ["Detecting Excel Error Values in OpenPyXL", "handle_openpyxl_datetimes",
   "date_serialization_in_spreadsheet", "openpyxl_cell_value_comparison"]),
 ("Dynamic formula references",
  ["Dynamic Formula Reference Adjustment"]),
 ("Aggregation / grouping",
  ["Dictionary-Based Category Aggregation", "cross_sheet_lookup_replacement"]),
 ("Tool-call / exec-env pitfalls\n(JSON, heredoc, lib names)  [all n=0]",
  ["Verify Library Names Before Execution", "Use Heredocs for Multi-line Python", "Robust Script Execution",
   "Safe_Embedded_Code_Execution", "JSON Command Formatting for Bash Tool", "JSON Escaping for Embedded Scripts",
   "Action Schema Strictness", "avoid_literal_newlines_in_tool_json", "Verify Library Names Before Importing",
   "transition_from_exploration_to_execution", "guarantee_output_file_generation"]),
]

rows = []
seen = set()
for label, names in THEMES:
    tot = 0; cnt = 0
    for nm in names:
        # there can be two deployed nodes sharing a name (e.g. "Dynamic Range Detection")
        matches = [s for s in L["skills"] if s["status"] == "deployed" and s["name"] == nm]
        for s in matches:
            tot += (s["trials"] or 0); cnt += 1; seen.add(id(s))
    rows.append((label, tot, cnt))
rows.sort(key=lambda r: r[1])   # ascending so largest on top in barh

labels = [r[0] for r in rows]
trials = [r[1] for r in rows]
counts = [r[2] for r in rows]
y = range(len(rows))
cols = ["#c0392b" if t == 0 else plt.cm.Blues(0.35 + 0.6 * t / max(trials)) for t in trials]

fig, ax = plt.subplots(figsize=(11, 6.5))
ax.barh(list(y), trials, color=cols, edgecolor="#555", linewidth=0.6, zorder=2,
        hatch=["////" if t == 0 else "" for t in trials])
for i, (t, c) in enumerate(zip(trials, counts)):
    note = f"{t} routings · {c} skills" + ("  (zombies/unmeasured)" if t == 0 else "")
    ax.text(t + 3, i, note, va="center", fontsize=8, color=("#c0392b" if t == 0 else "#222"))
ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=8.5)
ax.set_xlabel("total routing trials across the 34 deployed skills (= how much that content is actually used)", fontsize=9)
ax.set_xlim(0, max(trials) * 1.32)
ax.set_title("What did from-zero evolution actually evolve?\n"
             "34 deployed skills grouped by body CONTENT — robust-openpyxl coding habits, "
             "dominated by 'compute static values, not Excel formulas'", fontsize=11, loc="left")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
plt.tight_layout()
f = os.path.join(HERE, "figs", "fig_evo_content_themes.png")
plt.savefig(f, dpi=150, bbox_inches="tight"); print("wrote", f)

print("\n=== content-theme summary (trials desc) ===")
for label, t, c in sorted(rows, key=lambda r: -r[1]):
    print(f"  {t:>3} trials | {c:>2} skills | {label.splitlines()[0]}")
