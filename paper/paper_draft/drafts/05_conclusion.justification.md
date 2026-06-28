# 05_conclusion — Justification (paper-conclusion skill, FINAL_PLAYBOOK §8)

Single-paragraph Conclusion, **6 sentences (full ORAL), 165 words** (band 100–150 + ±10% tol → ceiling ~165; landed at the boundary). Prose-only: 0 `\Cref`, 0 `\includegraphics`, 0 specific numbers (G11). Source of truth: PAPER_BRIEF_FILLED.md Part 8/2/3, `_global_facts.md`, prior drafts 01–04.

## Sentence-by-sentence

| 句 | 内容 (前 8 词) | 模板规则 | 风格 |
|---|---|---|---|
| 1 | "In this work, we introduced \textbf{SkillStrata}, a stratified skill \textbf{system}..." | Method recall + 加粗 method; type word = **system** (NOT framework, per "curate a system, not a skill") | MemGen "In this work, we introduced" |
| 2 | "By curating a Skill Strata graph through refactor-style Split..." | Mechanism (curate + SPLIT/ROUTE + propose-then-verify gate + LEGO assembly) + paradigm callback "transcends the monolithic and flat-bank paradigms" | MemGen "By [verb] X through A and B, … transcends" |
| 3 | "Our experiments showcase \ding{182}...\ding{185}..." | \ding 4-finding list, all bold, MIXED provenance, NO numbers | MemGen \ding 招式 |
| 4 | "These results suggest a promising path toward self-evolving agents..." | 大终点 aspiration; echoes abstract句1/intro段1.1 | MemGen "promising path toward [大终点]" |
| 5 (★) | "More broadly, shifting from ever-larger skill documents to..." | ORAL flourish: "shifting from X to Y" → OS-style governance discipline | CRV/Snell flourish |
| 6 (★) | "Future directions include completing the in-progress real-benchmark head-to-head..." | 3 directions, last = integrate into broader agent stacks | playbook future-work template |

## 句3 \ding{} highlights — provenance honored (task-critical)
- **\ding{182}** [SIM] highest task success at lowest loaded-token cost (qualitative; numbers in §E2/abstract).
- **\ding{183}** [SIM] splitting and routing, not amassing skills, drive the gains (ablation, §E3).
- **\ding{184}** [REAL] real-benchmark validation gate autonomously rejects a harmful batch yet accepts a beneficial one — this is the verified propose-then-verify gate behavior (SpreadsheetBench from-zero curate, −10pp rejected / +5pp accepted). The phrase "real-benchmark" surfaces its [REAL] status without stating a fabricated number.
- **\ding{185}** [SIM] test-time assembly recovers out-of-domain coverage from trace sub-parts (~54% of gap; §E5).
- **280-test head-to-head = [PENDING]**: encoded in 句6 future work as "completing the in-progress real-benchmark head-to-head." NO number stated. This is the honest acknowledgment the brief/global_facts mandate.

## Aspiration sentence (句4)
> "These results suggest a **promising path toward self-evolving agents** that govern their own skills rather than merely amass them."
大终点词 = **self-evolving agents** — exact phrase from `_global_facts.md` (abstract句1 ↔ intro段1.1 ↔ conclusion句4). Not swapped.

## Echo check vs abstract/intro key concepts (≥5 target)
| Key concept | Echoed? |
|---|---|
| Method name **SkillStrata** | ✓ 句1 |
| 大终点词 **self-evolving agents** | ✓ 句4 (+ reinforced 句5) |
| Components **Skill Strata / curate / SPLIT / ROUTE / LEGO assembly / propose-then-verify / verify-loop** | ✓ 句2-3, 6 |
| Paradigm names **monolithic / flat-bank** | ✓ 句2 |
| Emergent/mechanism finding **propose-then-verify gate (REAL)** | ✓ 句3 \ding{184} |
→ 5/5 echoes. PASS.

## Global pre-delivery checklist (Phase 3)
- G1 word count 165 (band 100–150 + ±10% → ≤165): **PASS at boundary**
- G2 sentence count 6 (4–6, = full ORAL): PASS
- G3 per-sentence local checklists: PASS
- G4 echoes abstract (大终点 + paradigm + method + components + 1 emergent): PASS (5/5)
- G5 句3 uses `\ding{182}\ding{183}\ding{184}\ding{185}` (not 1)2)3)): PASS
- G6 句3 highlight block bolded as one `\textbf{...}`: PASS
- G7 句4 大终点词 = abstract句1 ("self-evolving agents", unchanged): PASS
- G8 (★ORAL) 句5 flourish present: PASS
- G9 (★ORAL) 句6 future work present: PASS
- G10 no forbidden words (novel/impressive/remarkable/SOTA/promising-except-"promising path"): PASS ("promising path" is the allowed exception)
- G11 zero specific numbers (numbers live in abstract句6 + experiments): PASS
- G12 single paragraph, not split: PASS (no blank lines in body)
→ **Hard-fail count: 0. ORAL-soft: 3/3 (flourish + future work + \ding).**

## G hard-fails + fixes during drafting
- Initial draft = 220 words (HARD fail >165). Cause: 句3 \ding list + 句2 + 句5 over-long. Fixed across 4 trim passes: removed redundant "at test time" duplication between 句1/句2, compressed flourish ("two tenses of one principle" → "gates curation and execution alike"), trimmed 句3 ("harmful skill batch" → "harmful batch"), and 句6 ("far larger" → "larger"). Landed at 165 (boundary), 0 hard-fails.

## Honest notes
- **No abstract/intro drafts exist yet** (drafts dir has only 01–04). Echo targets for abstract句1/句2/句4/句7 and intro段1.1/段6 were sourced from PAPER_BRIEF_FILLED.md Part 2/3 and `_global_facts.md` (the locked facts), not from a written abstract. When paper-abstract/paper-intro are drafted later, re-verify the 大终点词 ("self-evolving agents"), paradigm names ("monolithic"/"flat-bank"), and the 句7 emergent hook actually match this conclusion; adjust if the abstract picks a different emergent finding for its 句7.
- Conclusion is qualitative per G11; provenance ([REAL]/[SIM]/[PENDING]) is encoded via wording ("real-benchmark", "in-progress real-benchmark head-to-head") rather than `[TAG]` markers, since those inline tags belong in §Experiments, not the prose Conclusion. No fabricated 280-test number anywhere.
