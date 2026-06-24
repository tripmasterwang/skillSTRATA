"""Build the SkillStrata **capability layer** (Skill Strata middle layer) for the
SpreadsheetBench domain from Trace2Skill's released skill material.

Trace2Skill's REDUCE step merges all evolved patches into one *monolithic* SKILL.md
(``spreadsheet_agent/skills/xlsx-35B`` / ``xlsx-122B``). SkillStrata replaces that seam:
it keeps the same knowledge **decomposed** into task-type capability nodes connected by
``DEPENDS_ON`` edges, so a ``GraphRouter`` can activate the *minimal executable subgraph*
per task (proposal §Routing) instead of dumping everything. This is the real-benchmark
instantiation of the capability graph that ``sim/`` exercises synthetically.

Design choice for a fair test: fragment bodies are sourced from the GPT-authored
``xlsx-122B`` reference files (already topic-decomposed) plus distilled ``xlsx-35B``
sections. So content quality matches a strong monolithic skill — the only variable under
test is *routing* (which subset is injected), not the underlying skill text.

The dependency topology is the mechanism behind the negative-transfer fix we measured
(Cell-Level 8% vs Sheet-Level 27% under full injection): a cell-level task seeds
``cell-handling`` and its closure is lean (no formula stack), while a formula task seeds
``formula-construction`` and pulls the whole formula bundle. ``core-solve`` is the shared
anchor every node transitively depends on, so workbook-inspection + answer_position
discipline + execution hygiene are always present regardless of route.
"""

from __future__ import annotations

import os

from .embedding import Embedder
from .graph import SkillGraph
from .schema import Granularity, SkillNode, Status

# --- inline bodies distilled from xlsx-35B SKILL.md (the 89-line monolithic skill) ----

_CORE = """\
# Core Task Solving & Answer-Position Discipline
1. Read the task carefully; identify the target workbook, sheet, cells, or columns.
2. Use Python (openpyxl) to INSPECT the workbook structure BEFORE editing — map the exact
   locations of source data and verify your assumptions match the real layout.
3. Decide whether the task needs live formulas or pre-computed values based on how it is graded.
4. Make the SMALLEST change that satisfies the task; preserve untouched sheets/formulas/formatting.
5. Save to the EXACT output path the task gives you, then re-open the saved file and verify the
   expected cells changed correctly. State clearly what changed and where.

## Interpreting answer_position (STRICT)
- When `answer_position` is given (e.g. `'Sheet1'!A1:F14`), ALL modifications MUST occur within
  that exact sheet/range. Do NOT write to a different sheet or duplicate elsewhere.
- An `answer_position` range includes EVERY cell from start to end; headers and data must align
  within it even if some cells stay empty. Verify the final workbook matches the full range spec,
  not just the populated cells.
"""

_CELL = """\
# Cell Object Handling (cell-level edits)
- NEVER compare Cell objects directly to strings — extract `.value` first.
  Example: `if row[0].value == "TOTAL":` not `if row[0] == "TOTAL":`.
- Use `iter_rows(values_only=True)` for raw Python values, or read `.value` on each Cell.
- When assigning, use `cell.value = new_value`, not `cell = new_value`.
"""

_LOOKUP = """\
# Lookup & Cross-Reference Patterns
- Same-row lookups: search parameters and target data live in the same row.
- Cross-row lookups: search parameters are OUTSIDE the target row — you must scan ALL rows to
  find matches. Do NOT assume `row[i]` holds both the search params and the target value.
- When parameters include None but expected results exist elsewhere, suspect a cross-row pattern
  that needs full iteration. For searches across rows, prefer a SUMPRODUCT/explicit-scan approach.
"""

_DATAVAL = """\
# Data Structure Validation
- For structured text (dates, IDs, codes), ALWAYS inspect sample values first via pandas head()
  or openpyxl cell access before parsing.
- Verify your parsing assumptions match the ACTUAL data format before applying formulas/transforms.
- Test your parsing logic on 2-3 known values before processing the full dataset.
"""

_STRUCT = """\
# Structural Modifications (sheet-level restructuring)
- Inserting/deleting rows or columns SHIFTS references and can break existing formulas — re-check
  every formula that points into the modified region after the change.
- Transposition: when moving data between row- and column-orientation, map each source coordinate
  to its target explicitly; do not assume openpyxl preserves orientation.
- Data-range handling: operate only on the specified range; do not let a transform spill into
  header rows or cells outside the task's scope.
"""

_JSONDEBUG = """\
# JSON Action Formatting & Debugging Protocol
- Use SINGLE braces `{}` in JSON actions: `{"name": "bash", "arguments": {"command": "..."}}`.
- For multi-line code, escape properly: `"`→`\\"`, newline→`\\n`, tab→`\\t`. Validate locally with
  `python -c "import json; json.loads(your_json)"` before submitting. Invalid JSON = no execution.
- Debugging: after "Failed to parse your action" twice, STOP repeating the identical command.
  Inspect the error pattern, fix the JSON structure, try a minimal diagnostic, and adapt early —
  monitor the turn count so you do not exhaust your limit.
"""

# --- fragment manifest: id, name, description, task_types, deps, and body source -------
# `src` = path (relative to the xlsx-122B skill dir) of a GPT-authored reference file whose
# content becomes the node body; otherwise `body` is the inline distillation above.
_R = "references"
_FRAGMENTS = [
    dict(id="command-patterns", name="Valid JSON Command Patterns",
         description="Working bash/python command patterns for JSON actions; write-script-to-file "
                     "for complex logic; broken patterns (heredoc, unescaped quotes) to avoid.",
         task_types=["all"], deps=[], src=f"{_R}/command-patterns.md"),
    dict(id="json-debug", name="JSON Action Formatting & Debugging Protocol",
         description="Single-brace JSON actions, escaping multi-line code, validating JSON before "
                     "submit, breaking repetition cycles on parse failures.",
         task_types=["all"], deps=["command-patterns"], body=_JSONDEBUG),
    dict(id="core-solve", name="Core Task Solving & Answer-Position Discipline",
         description="Inspect the workbook first, honor the answer_position range exactly, make the "
                     "smallest change, save to the exact output path, then re-open and verify.",
         task_types=["all"], deps=["command-patterns", "json-debug"], body=_CORE),
    dict(id="openpyxl-patterns", name="OpenPyXL Safe Patterns",
         description="Safe cell access, sheet-name existence checks, comment detection, optional "
                     "output files, correct row iteration.",
         task_types=["cell", "sheet", "data"], deps=["core-solve"], src=f"{_R}/openpyxl-patterns.md"),
    dict(id="cell-handling", name="Cell Object Handling",
         description="Extract .value before comparing, iter_rows(values_only), correct cell "
                     "assignment — for cell-level edits and value reads.",
         task_types=["cell"], deps=["core-solve"], body=_CELL),
    dict(id="data-validation", name="Data Structure Validation",
         description="Inspect sample values first, verify parsing assumptions for dates/IDs/codes, "
                     "test on 2-3 values before the full dataset.",
         task_types=["data", "cell"], deps=["core-solve"], body=_DATAVAL),
    dict(id="lookup-patterns", name="Lookup & Cross-Reference Patterns",
         description="Same-row vs cross-row lookups, scanning all rows to find matches, "
                     "VLOOKUP/SUMPRODUCT search across a range.",
         task_types=["lookup", "formula"], deps=["core-solve", "openpyxl-patterns"], body=_LOOKUP),
    dict(id="formula-best-practices", name="Formula Writing & Verification",
         description="Verify computed results not just syntax, Excel version compatibility, "
                     "range validation checklist.",
         task_types=["formula"], deps=["core-solve"], src=f"{_R}/formula-best-practices.md"),
    dict(id="formulas", name="Formula Handling in openpyxl",
         description="Array formulas across cells, openpyxl cell formula assignment vs raw XML, "
                     "post-modification verification of computed values.",
         task_types=["formula"], deps=["openpyxl-patterns"], src=f"{_R}/formulas.md"),
    dict(id="formula-construction", name="Formula Construction Guide",
         description="Match formula scope to the analysis, avoid volatile functions, validate "
                     "column references, multi-row SUMPRODUCT search patterns.",
         task_types=["formula"], deps=["formula-best-practices", "formulas"],
         src=f"{_R}/formula-construction.md"),
    dict(id="structural-mods", name="Structural Modifications",
         description="Insert/delete rows or columns safely (breaks formulas), transposition rules, "
                     "data-range handling — for sheet-level restructuring.",
         task_types=["sheet"], deps=["core-solve", "formulas"], body=_STRUCT),
    dict(id="common-pitfalls", name="Common Editing Pitfalls",
         description="String escaping in generated code, ARGB vs RGBA color format, formula "
                     "preservation after modification.",
         task_types=["all", "formatting"], deps=["core-solve"], src=f"{_R}/common-pitfalls.md"),
]


def _read_src(skill_dir: str, rel: str) -> str:
    path = os.path.join(skill_dir, rel)
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read().strip()


def build_spreadsheet_capability_graph(skill_dir: str, embedder: Embedder | None = None) -> SkillGraph:
    """Construct the SpreadsheetBench capability graph.

    ``skill_dir`` is the path to the ``xlsx-122B`` skill directory (it must contain a
    ``references/`` folder with the topic files). All nodes are added DEPLOYED so they are
    immediately routable by ``GraphRouter`` / ``FlatRouter``.
    """
    g = SkillGraph(embedder=embedder or Embedder())
    for frag in _FRAGMENTS:
        body = frag.get("body") or _read_src(skill_dir, frag["src"])
        node = SkillNode.make(
            frag["name"],
            id=frag["id"],
            granularity=Granularity.ATOMIC,
            description=frag["description"],
            body=body,
            status=Status.DEPLOYED,
            dependencies=list(frag.get("deps", [])),
            task_types=list(frag.get("task_types", [])),
        )
        g.add_skill(node)
    return g
