# Related Work — Sentence-by-Sentence Justification (SkillStrata)

Source of truth: `PAPER_BRIEF_FILLED.md` Part 0.2/0.3 + Part 4; `_global_facts.md` (LOCKED); prior drafts `01_method.md`, `02_experiment.md`; task instructions (task §C overrides brief 4.1 §C). Playbook: `FINAL_PLAYBOOK.md §4`.

## Structure decisions (locked before drafting)
- **Subsection count = 3** (default).
- **Differentiation visual = B. Differentiation Table** (`tab:differentiation`), per brief Part 4.3 — 5 boolean axes; chosen over comparison figure because the differentiation is attribute/boolean (≥4 axes), not a single mechanism diagram. Asset gate WAIVED (no `_asset_inventory.json`; consistent with method/experiment drafts) → `\Cref` kept, TODO comment attached.
- **R32 "We are not aware of..." hook = §C only** (one subsection, per rule). Placed at §C because the test-time out-of-domain assembly novelty (TTA) is the thing single-layer skill graphs lack; §A/§B do not own it.
- **PARAGRAPH_CAP = 0 honored**: subsections use `\subsection{}`; the only `\paragraph{}` is the empty-titled R32 hook at the end of §C (the explicit exception).
- **§Background "Skill Bloat vs. Skill Governance" already names the common flaw** → Related Work does NOT re-name it; it only classifies competitors.

## Per-sentence map

| Sub | 句 | 内容 (前 ~8 词) | 模板规则 | 维度/类选择 |
|---|---|---|---|---|
| A | 1 | "Methods that distill reusable skills from execution traces..." | 句1 分类总句 + explicit "three classes" | 3 classes, self-evolving skill libraries |
| A | 2 | "(I) monolithic merge, which hierarchically reduces..." | (I) 罗马数字加粗 + refs | `trace2skill`, `skillbrew` (= Paradigm I, aligns Intro 段2) |
| A | 3 | "(II) optimization-gated curation, which edits..." | (II) 平行 + refs + 埋缺陷(non-decreasing edits) | `skillopt`, `skillos_ouyang` (held-out validation gate, REAL fact) |
| A | 4 | "(III) self-evolving update loops, which iteratively grow..." | (III) 平行 + ref | `evoskill` |
| A | 5 | "Our SkillStrata falls within this self-evolving line, yet distinguishes itself..." | ★ 句5 归属: falls within X yet distinguishes through Y, 2 维度, "rather than" | dims = **refactor-style SPLIT** + **dependency-aware routing of minimal executable subgraph** (matches §M2/§M3 + global-facts core variable = skill granularity) |
| A | R32 | (省略) | hook reserved for §C | — |
| B | 1 | "A parallel line organizes an agent's accumulated experience..." | 句1 + "two classes" | 2 classes, graph memory + OS lifecycle |
| B | 2 | "(I) hierarchical graph memory, which arranges..." | (I) + ref | `gmemory` (k-hop traversal) |
| B | 3 | "(II) OS-style lifecycle memory, which schedules by a heat signal..." | (II) 平行 + refs | `memoryos`, `memos` (heat / promotion / eviction) |
| B | 5 | "Our SkillStrata falls within this graph-and-lifecycle paradigm, yet distinguishes itself..." | ★ 句5 归属, 2 维度, "rather than" | dims = **skill library (not memory store) w/ stable slug IDs** + **dependency-aware SPLIT/ROUTE operators**; rather than promotion/eviction over opaque memory |
| C | 1 | "Closest to our routing mechanism, a recent line represents skills as a graph..." | 句1 + "two classes" + 点明 closest | 2 classes, single-layer skill graphs |
| C | 2 | "(I) reinforcement-trained skill graphs, which learn to traverse..." | (I) + ref | `skillgraph_rl` (2605.12039) |
| C | 3 | "(II) retrieval-and-composition over a fixed skill graph..." | (II) 平行 + refs | `gos` (2604.05333), `skillgraph_toolseq` (2604.19793) |
| C | 5 | "Our SkillStrata falls within this skill-graph paradigm, yet distinguishes itself... which SkillStrata subsumes as the in-domain special case." | ★ 句5 归属 + **SUBSUME** framing | dims = **three-layer stratification (trace/capability/governance)** + **test-time assembly of a missing skill from trace sub-parts**; rather than single-layer routing of fixed skills |
| C | R32 | "While all these graph methods aim to reuse skills... We are not aware of previous attempts to... synthesize a fit skill out-of-domain at test time..." | ★ R32 hook (CRV-style "We are not aware of" softener), 1× only, at the most-novel subsection | TTA novelty |

## The 3 总句 + 归属句 (deliverable summary)

- **§A 总句**: "Methods that distill reusable skills from execution traces and continually update them can be broadly categorized into three classes."
  **§A 归属**: "Our SkillStrata falls within this self-evolving line, yet distinguishes itself … through its dedicated refactor-style Split operator … as well as its dependency-aware routing of a minimal executable subgraph, rather than the monolithic full-load or non-decreasing document edits these methods apply."
- **§B 总句**: "A parallel line organizes an agent's accumulated experience as a structured, governed store, falling into two classes."
  **§B 归属**: "Our SkillStrata falls within this graph-and-lifecycle paradigm, yet distinguishes itself … through its target object being a governed skill library rather than a memory store, organized by stable slug identifiers …, as well as its dependency-aware Split/Route operators, rather than the promotion-and-eviction lifecycle these methods apply to opaque memory items."
- **§C 总句**: "Closest to our routing mechanism, a recent line represents skills as a graph and selects among them at inference, falling into two classes."
  **§C 归属**: "Our SkillStrata falls within this skill-graph paradigm, yet distinguishes itself … through its three-layer stratification of trace, capability, and governance, as well as its test-time assembly of a missing skill from trace sub-parts, rather than the single-layer routing of already-fixed skills these methods perform — which SkillStrata subsumes as the in-domain special case of assembly."

## Cite-keys used per subsection
- **§A**: `trace2skill`, `skillbrew`, `skillopt`, `skillos_ouyang`, `evoskill` (5 refs — within 3–5 band).
- **§B**: `gmemory`, `memoryos`, `memos` (3 refs).
- **§C**: `skillgraph_rl`, `gos`, `skillgraph_toolseq` (3 refs).
- **Table rows** reuse: `trace2skill`, `skillopt`, `gmemory`, `skillgraph_rl` (+ two un-cited family-label rows: "Flat skill bank / Top-$k$ retrieval", which is a baseline category not a single paper).
- All cite-keys are from brief Part 4.5 + Part 0.2 competitor caveats. NO papers invented.

## Global checklist (Phase 3)
| # | Check | Status |
|---|---|---|
| G1 | Word count [300, 450] (prose, excl. table) | ✓ 316 |
| G2 | Subsection count 2–3 | ✓ 3 |
| G3 | Every 句1 explicit "N classes" | ✓ (three / two / two) |
| G4 | Every class 罗马数字 (I)(II)(III) 加粗 | ✓ |
| G5 | Every 句5 "falls within X yet distinguishes itself through Y" 双维度 | ✓ 3/3 |
| G6 | §A classes align with Intro 段2 paradigm names | ✓ (monolithic merge = Paradigm I; flat bank appears in table) — Intro not yet written; global facts lock the names, §A matches them |
| G7 | 句5 diff dims match Intro 段4.4 callback property | ✓ (SPLIT + dependency-aware ROUTE; Intro pending but global-facts-locked) |
| G8 | R32 hook only in 1 subsection (§C) | ✓ |
| G9 | One visual only (table, no figure) | ✓ |
| G10 | 0 forbidden words (impressive/remarkable/promising/strong/novel/first-to/better/improved) | ✓ ("first-class" reworded → "dedicated") |
| G11 | Every ref via `\citep{}` | ✓ |
| G13 | Each subsection ≤ 12 lines double-column | ✓ (compile-time check pending; each ~5–6 sentences) |
| G14 | No prior work expanded to ≥2 sentences | ✓ |
| Ours-row all-cmark | Table Ours row all `\cmark` | ✓ |

**Hard-fail count = 0.**

## Honest notes / per-sentence steps not skipped
- All 句1/句2/句3/(句4)/句5 written per template for every subsection; R32 hook written once. No per-sentence step skipped.
- §A uses 3 classes (句4 present); §B and §C use 2 classes each (句4 absent by design — N=2 is allowed; both are short building-block / closest-competitor subsections).
- §6 (closest call-out) intentionally omitted — §C's 句1 already names the closest line ("Closest to our routing mechanism") and the R32 hook does the call-out work; a separate 句6 would be redundant.

## Asset / dependency caveats (carry forward)
- `\Cref{tab:differentiation}`: table body is inline here; needs a Part 12 inventory row + `\usepackage{pifont}` with `\cmark`/`\xmark`/`\makecell` (requires `makecell` package) at compile time. TODO comment in draft.
- Cite-keys `skillbrew`, `evoskill`, `skillos_ouyang`, `memos`, `skillgraph_rl`, `gos`, `skillgraph_toolseq` are NOT yet [已精读] (brief flags them provisional) → run `citation-audit` / read PDFs before building `references.bib`. `skillos_ouyang` (same-name "SkillOS", 2605.06614) needs full-text head-to-head before final submission.
- The REAL SkillOpt fact (held-out validation gate; 38.2→47.5) is reflected in §A class (II) description; numbers themselves are not dumped into Related Work (they live in §Experiments).

## Suggested second-pass refinements (offered, not auto-applied)
1. If Intro 段2 ends up listing exactly (I) monolithic + (II) flat bank, consider adding "flat skill bank (top-$k$ retrieval)~\citep{}" as an explicit clause in §A 句2 so §A's class list and Intro's paradigm list are verbatim-aligned (currently flat bank lives only in the table).
2. Once `skillos_ouyang` is read full-text, confirm it belongs in class (II) "optimization-gated curation" vs. a curation class of its own; if it differs materially, split it out or move to §A 句4.
3. After `citation-audit`, if SkillGraph-ToolSeq turns out to be tool-sequencing rather than skill-graph routing, demote it from §C 句3 to a single `\citep` inside class (II) or drop it (keep `gos` as the (II) anchor).
