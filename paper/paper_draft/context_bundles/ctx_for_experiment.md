# Context Bundle for paper-experiment — SkillStrata

> Assembled for the Experiments section drafting pass (cumulative context: Method already exists).
> Source-of-truth pointers below. Invent NO numbers/refs/claims beyond them.
> ★ NUMBER PROVENANCE IS NON-NEGOTIABLE: every number is tagged [SIM] / [REAL] / [PENDING-280TEST]; tags MUST surface in prose, not be laundered into clean claims.

## Pointers (source of truth)
- BRIEF: `.../projects/skillSTRATA/paper/paper_draft/PAPER_BRIEF_FILLED.md`
  - Part 7 = experiment plan (7.0 subsection list, 7.1 RQ↔evidence map, 7.2 setup, 7.3 main table [SIM], 7.4 cross-domain, 7.5 governance mechanism, 7.5.bis TTA, 7.6 ablation table, 7.9 efficiency, 7.10 stats)
  - Part 2.4/2.5 = experiment-data highlights [SIM] + sentence-7 surprise hook
  - Part 2.6 = REAL from-zero curate evidence (2026-06-27)
  - Part 0.6 = `subsection_title_style = claim-title` (default)
  - Part 12 = table/figure index (ALL [待生成]/PENDING)
- GLOBAL FACTS (LOCKED): `.../_global_facts.md`
- PRIOR DRAFT (cumulative): `.../drafts/01_method.md` (component/symbol names: SkillStrata, Skill Strata, $\mathcal{G}=(\mathcal{G}_{\text{trace}},\mathcal{G}_{\text{cap}},\mathcal{G}_{\text{gov}})$, $\mathcal{S}^\star$, SPLIT/MERGE/LINK/RETIRE, propose-then-verify gate Eq:gate, ROUTE Eq:route, TTA Eq:tta, node-local verify-loop Eq:verify)

## Locked decisions for this pass
- Method name = **SkillStrata**; three-layer system = **Skill Strata** (trace/capability/governance).
- subsection_title_style = **claim-title** (Part 0.6) → result/analysis titles are RQ conclusion sentences.
- Part 7.0 author-declared subsections (USE; do not default to 7) — but ONE-RQ-per-subsection HARD rule splits any multi-RQ row.
- RQ list (global facts §RQ list): RQ1 success@lower-token / RQ2 which operators / RQ3 governance stability / RQ4 routing precision & negative-transfer / RQ5 TTA OOD.
  - Task lumps RQ2+RQ4 into "ablation". ONE-RQ HARD rule forbids `[RQ2,RQ4]` → SPLIT into separate tagged subsections.
- Mode: **Mode C (R55 paragraph-title-as-claim)** for ablation findings; Register-A main table; Register-B mechanism/case.
- Tier: T0-ish on SIM (single synthetic world, no per-env, no SIM case studies) BUT one REAL case study (416-15) → handle as a §E5 case study. Subsection count driven by RQ map (5 RQ → 5 result/analysis subsections + E0 + E1 setup).
- Asset gate WAIVED: may \Cref{tab:main}, tab:ablation, tab:setup, tab:tta, fig:stability though files absent. No `_asset_inventory.json` on disk → wrap refs with TODO comment per skill rule, but DO NOT halt.

## NUMBER PROVENANCE LEDGER (surface tags in prose)
### [SIM] — deterministic simulator harness; pending real-benchmark replacement
- main (tab:main): SkillStrata success **0.704** vs Trace2Skill 0.574 / Flat 0.555 / Pruning 0.557 / NoSkill 0.428; tokens **365** vs 780/431/432/0; NegTransfer **0.105** vs 0.219/0.175; OOD gain **+0.256** vs 0.163/0.119; RoutePrec **0.391** vs 0.234/0.317.
- ablation (tab:ablation): w/o Routing −0.18 (0.643→0.462); w/o Split −0.15 (0.643→0.489) + tokens 360→2345 (~6.6×); w/o Valid+Govern → LateSucc 0.601→0.562 + Stability lowest; Full Loading 0.481 @ 3932 tok.
- TTA (tab:tta): covered 0.296→0.473 (~54% gap recovered), success +0.056 (0.501→0.557), OOD +0.044 (0.408→0.452), tokens +88% (325→611), 2.6 synth/task; upper bound 0.711/0.677/0.621.
- 8 seeds (main + ablation); ±std + paired test PENDING.
### [REAL] — SpreadsheetBench verified-400, qwen3.6-35b-a3b, official per-instance hard
- SkillOpt paper (arXiv 2605.23904 Table 1, direct-chat harness): no-skill **38.2** → SkillOpt **47.5 (+9.3)**; Trace2Skill **33.2 (−5.0, negative transfer)**; GEPA 45.4 / Human 44.3 / LLM-skill 42.9 / TextGrad 22.9. CAVEAT: harness differs from ours (direct-chat vs Trace2Skill agentic ReAct) → compare gain-over-no-skill.
- our from-zero curate validation gate: S0 blank **42.5%** → round0 distilled **32.5% (−10pp) → gate REJECTS, 12 skills retired** → round1 **47.5% (+5pp) → gate ACCEPTS, 12 deployed**.
- negative-transfer case 416-15: no-skill solves; round0 skills break it (datetime→string via strftime; self-verification skill verifies a tautology → false confidence "All checks passed!"). 6/40 val regressions: 3 "Output file not found" (over-engineering), 3 wrong value/format.
### [PENDING-280TEST] — NOT YET AVAILABLE
- 280-test head-to-head no-skill vs with-skill (SkillStrata) on SkillOpt 280 split (split_seed=42). THE main result. → explicit `[PENDING-280TEST]` placeholder in §E2; DO NOT fabricate, DO NOT substitute a [SIM] number.

## §E subsection plan (claim-title, one [RQ_N] per subsection)
- §E0 RQ list opener (RQ1–RQ5; italic central hypothesis) — untagged.
- §E1 Setup — untagged: Models (qwen3.6-35b-a3b) + Datasets (SpreadsheetBench verified-400 official per-instance hard; SkillOpt 80/40/280 split_seed=42; + [SIM] simulator world) + Baselines (No-Skill/Trace2Skill/Flat bank/Pruning/SkillOpt-target) + Metrics + Protocol. tab:setup.
- §E2 [RQ1] main results — [REAL] SkillOpt target table + [PENDING-280TEST] placeholder for our 280-test + [SIM] main table simulator evidence. tab:main. 5 必含要素.
- §E3 [RQ2] ablation — SPLIT/ROUTE largest contributors [SIM] (Mode C finding paragraphs). tab:ablation. ANALYSIS → shallow→deep + S9.
- §E4 [RQ4] routing precision & negative-transfer reduction — [SIM] RoutePrec 0.391 + NegTransfer 0.105 + the REAL gate evidence 42.5→32.5(reject)→47.5(accept). ANALYSIS.
- §E5 [RQ3] governance/validation stability safety net — [SIM] remove-both → late-success/stability lowest. fig:stability. ANALYSIS.
- §E6 [RQ5] test-time assembly OOD — [SIM] TTA ~54% + REAL negative-transfer case study 416-15 (datetime→string false-confidence). tab:tta. ANALYSIS + case study.
- §E7 Efficiency — untagged: tokens [SIM] 365 vs 780 vs 3932.
