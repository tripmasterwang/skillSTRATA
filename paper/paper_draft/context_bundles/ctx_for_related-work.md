# Context Bundle for paper-related-work — SkillStrata

> Assembled for the Related Work drafting pass (cumulative-context: Method + Experiment drafts already exist).
> Invent NO papers/numbers/refs beyond the source-of-truth pointers below.

## Pointers (source of truth)
- BRIEF: `/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/projects/skillSTRATA/paper/paper_draft/PAPER_BRIEF_FILLED.md`
  - Part 0.2/0.3 = paradigm framing (subsume single-layer skill graphs as a special case)
  - Part 4 = related work with real refs + cite-keys (4.1 directions, 4.2 per-subsection classes, 4.3 diff-table axes, 4.5 ref list)
- GLOBAL FACTS (LOCKED): `/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/projects/skillSTRATA/paper/paper_draft/_global_facts.md`
- PRIOR DRAFTS (cumulative context — keep refs/claims consistent):
  - `.../drafts/01_method.md` (Eq.~route/split/gate/tta/verify; §M3 already says single-layer methods "approximate" in-domain routing and SkillStrata "subsumes" them)
  - `.../drafts/02_experiment.md` (SkillOpt [REAL] target; [SIM] main/ablation/TTA)

## Locked decisions for this pass
- Method name = **SkillStrata** (NOT SkillLEGO). Method type word = **system**.
- TARGET_SUBSECTIONS = 3. TARGET_LENGTH band ~300–450 words (soft, HARD fail > ~495).
- Differentiation visual = **B. Differentiation Table** (`\Cref{tab:differentiation}`), brief Part 4.3 — 5 boolean axes prior methods do not jointly satisfy. (Asset gate WAIVED, consistent with method/experiment drafts: no `_asset_inventory.json` on disk; emit `\Cref{}` wrapped in a TODO, do not halt.)
- R32 "We are not aware of..." hook = **ONE subsection only** → place in **§C** (closest to the TTA / out-of-domain assembly novelty, which §A/§B do not cover). Task explicitly offers the R32 hook for the test-time out-of-domain assembly novelty.
- §Background "Skill Bloat vs. Skill Governance" already NAMES the common flaw separately (brief 0.6 background_subsection_for_common_flaw=yes) → Related Work must NOT re-name it; only classify competitors.

## Three subsections (task-authoritative; overrides brief 4.1's §C)
- **(A) Trace-to-skill / self-evolving skill libraries** — Trace2Skill, SkillBrew, SkillOpt, EvoSkill, SkillOS-Ouyang.
  - cite-keys: `trace2skill`, `skillbrew`, `skillopt`, `evoskill`, `skillos_ouyang`
  - Classes: (I) monolithic merge (Trace2Skill, SkillBrew); (II) optimization/curation gate (SkillOpt, SkillOS-Ouyang); (III) self-evolving update loops (EvoSkill).
  - Ours falls within yet differs by: **graph governance + routing** (not monolithic merge); refactor-style SPLIT + dependency-aware ROUTE.
  - REAL fact usable: SkillOpt (arXiv 2605.23904) = Microsoft; monolithic SKILL.md + bounded add/delete/replace edits + held-out validation gate; SpreadsheetBench Qwen3.6-35B-A3B (direct-chat, hard) no-skill 38.2 → 47.5 (+9.3); Trace2Skill 33.2 (−5.0 negative transfer).
- **(B) Graph memory & OS lifecycle** — G-Memory, MemoryOS (+ MemOS).
  - cite-keys: `gmemory`, `memoryos`, `memos`
  - Classes: (I) hierarchical graph memory (G-Memory); (II) OS-style lifecycle memory (MemoryOS, MemOS).
  - Ours falls within yet differs by: adapts hierarchical graph memory + OS lifecycle to a *skill* library with **stable IDs + skill lifecycle** (they govern memory, we govern skills; we add SPLIT + dependency routing; stable slug IDs fix G-Memory raw-task-string nodes).
- **(C) Skill graphs / dependency-aware routing** — SkillGraph-RL (2605.12039), Graph-of-Skills/GoS (2604.05333), SkillGraph-ToolSeq (2604.19793).
  - cite-keys: `skillgraph_rl`, `gos`, `skillgraph_toolseq`
  - These = single-layer skill graphs that only ROUTE existing skills. **We subsume them as a special case** (in-domain routing) and add three-layer governance + out-of-domain test-time assembly (TTA) they lack.
  - R32 hook here: not aware of prior work that, beyond routing fixed skills, assembles a missing skill at test time from trace sub-parts.

## Differentiation table axes (brief 4.3) — Ours must be all-cmark
`modular skills?` / `dependency edges?` / `refactor SPLIT?` / `dependency-aware routing?` / `lifecycle governance?`
Rows (1 representative per family): Trace2Skill (monolithic) / Flat skill bank / SkillOpt (prune+gate) / G-Memory (graph, but memory) / SkillGraph-RL or GoS (single-layer skill graph) / **SkillStrata (Ours)**.

## Consistency hooks to Intro (段2 / 段4.4 callback) — Intro not yet written, but global facts lock:
- Paradigm I = monolithic skill (Trace2Skill/SkillBrew/SkillOpt); Paradigm II = flat skill bank (top-k). §A classes must align with these names.
- 句5 diff dimensions = "refactor-style SPLIT" + "dependency-aware ROUTE / minimal executable subgraph" (matches §M2/§M3 and global facts core variable = skill granularity).

## Honesty flags (carry from brief)
- Only Trace2Skill / G-Memory / MemoryOS / SkillOpt are [已精读]; other cite-keys + one-line summaries are provisional → citation-audit needed before submission. Do NOT invent new papers; use only the cite-keys listed above.
- skillos_ouyang (same name "SkillOS", 2605.06614) still needs full-text head-to-head before final.
