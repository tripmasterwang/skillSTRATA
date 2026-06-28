# Context Bundle — Conclusion (paper-conclusion skill)

> Generated 2026-06-27. Source of truth: PAPER_BRIEF_FILLED.md Part 8 / 2 / 3, _global_facts.md,
> and prior drafts {01_method, 02_experiment, 03_preliminary, 04_related-work}.md.
> FINAL_PLAYBOOK §8 = single-paragraph, 4–6 sentences, 100–150 words, prose-only (no \Cref/\includegraphics).

## Two decisions (locked)
- **Flourish 句 (句5)**: ON (ORAL招式) — MemGen/Snell-style broader implication: governance-from-trace as an OS-style discipline for self-evolving libraries; "load less, compose better, transfer more safely".
- **Future work 句 (句6)**: ON (ORAL 100%) — (1) finish the real-benchmark head-to-head (SpreadsheetBench 280-test, currently in progress), (2) scale to larger skill libraries, (3) integrate node-local verify-loop into broader agent stacks.

## 8 facts
1. **Method name + type**: **SkillStrata** — a [system] (NOT "framework"; type word = *system*, per "curate a system, not a skill"). NOT SkillLEGO.
2. **Method type word**: system.
3. **Components (2–4, must echo abstract句4/method §M2.x)**:
   - **Skill Strata** = stratified three-layer skill graph (trace / capability / governance)
   - **Curate** (offline, no-grad/no-RL): SPLIT/ROUTE + **propose-then-verify gate**
   - **LEGO assembly** (test-time): in-domain ROUTE + out-of-domain synthesis
   - governance sub-mechanism: **node-local verify-loop**
4. **Paradigm I / II** (echo abstract句2 / intro段2 / preliminary):
   - Paradigm I = **monolithic skill** (Trace2Skill / SkillBrew / SkillOpt) — skill bloat / full-load / negative transfer
   - Paradigm II = **flat skill bank** (top-k retrieval) — no dependency closure / no governance / mis-routing
   - → conclusion 句2 末 "transcends the limitations of monolithic and flat-bank paradigms"
5. **3–4 empirical findings for 句3 \ding{} list — MIXED PROVENANCE, mark honestly**:
   - \ding{182} [SIM] highest success at lowest loaded-token cost (0.704 @ 365 tok vs Trace2Skill 0.574 @ 780; ≈2.1× fewer)
   - \ding{183} [SIM] SPLIT and ROUTE are the dominant contributors (ablation), not stacking more skills
   - \ding{184} [REAL] the propose-then-verify gate rejects a harmful distilled batch (−10pp) and accepts a beneficial one (+5pp) — autonomous negative-transfer screening
   - \ding{185} [SIM] test-time assembly recovers out-of-domain coverage from trace sub-parts (~54% of the gap)
   - **Honesty rule**: the [REAL] 280-test head-to-head is **in progress / PENDING** — do NOT state a fabricated number; acknowledge it as the in-progress real validation.
6. **大终点词 / aspiration (echo abstract句1 / intro段1.1)**: **self-evolving agents** (MUST be the exact phrase; 句4).
7. **Flourish (句5)**: shifting from accumulating ever-larger skill documents to *governing a stratified skill system* — governance-from-trace gives self-evolving libraries an OS-style lifecycle discipline (gate at train time, verify-loop at inference time = same principle in two tenses).
8. **Future work (句6)**: complete the real-benchmark head-to-head (in progress), scale to larger libraries, integrate verify-loop into broader agent stacks.

## Echo targets (≥5 must reappear in conclusion)
- method name **SkillStrata** ✓ 句1
- 大终点词 **self-evolving agents** ✓ 句4
- components **Skill Strata / curate / LEGO assembly / SPLIT / ROUTE / verify-loop** ✓ 句2-3
- paradigm names **monolithic / flat-bank** ✓ 句2
- emergent/mechanism finding **propose-then-verify gate (REAL)** ✓ 句3 \ding{184}

## Hard provenance constraints (brief Part 13 + global_facts)
- Every empirical claim must respect [SIM]/[REAL]/[PENDING] provenance.
- 280-test = [PENDING], the in-progress real head-to-head — name it as such, no number.
- Conclusion is qualitative: NO specific numbers in the \ding{} list (numbers live in abstract句6 + experiments). The provenance words ([REAL]/in-progress) are conceptual, not numeric.

## Forbidden words: novel / impressive / remarkable / SOTA / promising (except "promising path/direction")
