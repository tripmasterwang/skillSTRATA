# 06_intro — Justification (paper-intro skill, FINAL_PLAYBOOK §3)

6-paragraph Introduction. 段1 style = **A trend-dump**; 段3 RQ = **A obsbox**; reframe 招式 = **AgentFlow**
(verb-role component naming: organize → govern → route → assemble). Source of truth: PAPER_BRIEF_FILLED.md
Part 3 / 0.2 / 0.3 / 2, `_global_facts.md`, prior drafts 01–05. Provenance ([REAL]/[SIM]/[PENDING]) tagged inline
in 段5; the 280-test head-to-head is [PENDING] and never given a number.

**Length** (detex): 812 alnum tokens / ~770 pure-prose words (excludes the ~40 bare-number + roman-marker tokens
that live in 段5/段2). This sits at the top of the soft band (HARD ceiling ≈770; see G1 note below — flagged honest,
not gold-plated away by deleting a hard-required element). Per-paragraph (detex prose+numeric): 段1 130 / 段2 154 /
段3 142 / 段4 ~150 / 段5 154 / 段6 115.

---

## Sentence-by-sentence (28 local checklists)

### 段 1 — Big environment + subdomain (trend-dump) + external-discipline anchor

**句 1.1** "The ascent of LLM agents that self-evolve by distilling reusable skills…" | R8 trend-dump (style A) | 7-ref dump
- [x] 27 words (band 25–35) · [x] 7 refs (trace2skill, skillopt, skillbrew, evoskill, gmemory, memoryos, skillos_ouyang) ≥5
- [x] strong verb "ascent … marks a paradigm shift" · [x] not "Recent advances in X" · [x] style A locked for whole 段

**句 1.2** "Pivotal to this self-evolution is the agent's **skill library**…" | R8 核心概念点名 | 18-25 词
- [x] 22 words · [x] "Pivotal to" strong phrase · [x] exactly ONE core concept `\textbf{skill library}` bolded first mention
- [x] "conditions future behavior with a frozen backbone" = capability, not a Preliminary-style definition

**句 1.1b (★ external-discipline anchor, HARD)** "Research on **complex networks** offers a familiar template…" | 段1 canonical anchor
- [x] 35 words · [x] (★) discipline named explicitly = **complex networks** (not "akin to humans")
- [x] `\citep{boccaletti2014multilayer}` — SAME cite-key §M0 (01_method.md line 12) recalls · [x] italic thought-core *hierarchical multilayer network* / *operate on top* reused in §M0/§M1/conclusion
- [x] bridge clause "so that structure, not bulk, governs what is used" hooks to the LLM-skill-library problem
- [x] (★) discipline is first-named HERE, not in §Method — §M0 only recalls it ("Just as a hierarchical multilayer network…")

**句 1.4-transition** "The open question is thus no longer *whether* an agent should accumulate skills, but *how*…"
- [x] 24 words · closes 段1 with the structuring question that 段2 answers (two paradigms) and 段3's RQ sharpens
- Note: 句1.3 (adjacent-topic exclusion) + a separate 句1.4 scope-lock are OMITTED (scope clear from title+1.1; per skill §A they are weak-by-default). 句1.5 hot-model dump folded lightly into 段5 backbone mention rather than a standalone sentence (kept Intro tight).

### 段 2 — Two-paradigm conflict

**句 2.0 (★ route-shift lead-in; brief Part 3.2 NON-`[无]` → REQUIRED)** "Trace-to-skill methods implicitly equate a more heavily merged skill with a stronger one…"
- [x] barrier Z named explicitly = **bloated documents polluted by conflicting rules** (skill bloat) — not vague "has limitations"
- [x] "the focus must therefore shift from making a bigger document to governing modular skills" = consequently-connective to route Y, then "two dominant paradigms" hands off to 句2.1
- [x] negates route X (making bigger documents), NOT a single method · merged with 句2.1 (the "two dominant paradigms" clause)

**句 2.2** "The first is **(I) monolithic skill**, which merges distilled patches into one ever-growing document…" | 范式 I
- [x] (I) bold roman (matches §Prelim/§Related/§Method) · [x] 3 refs trace2skill/skillbrew/skillopt · [x] action verb "merges … loaded in full" · [x] 0 method names in main text · [x] 0 praise

**句 2.3** "…its reliance on full-load injection inevitably entails **skill bloat** and **negative transfer**." | 范式 I 缺陷
- [x] "its reliance on Y inevitably entails Z" fixed pattern · [x] flaws bolded · [x] "inevitably" root-cause emphasis · [x] negates the paradigm class

**句 2.4** "Conversely, the second is **(II) flat skill bank**, which stores skills as independent entries and retrieves a top-k slice…" | 范式 II
- [x] "Conversely" (not "On the other hand") · [x] (II) bold roman · [x] parallel verb form to 句2.2 · [x] 2 refs skillgraph_rl/gos · [x] 0 method names

**句 2.5** "…with no dependency closure and no governance, its similarity-based routing silently **mis-routes**…" | 范式 II 缺陷
- [x] flaw "tethered to surface similarity" → "**mis-routes**" bolded · [x] uses "tethered to" family (not "entails" — that was 句2.3) · [x] complementary to (I)'s bloat (mis-routing ≠ bloat)

**句 2.6 (★ ORAL common flaw)** "Both reduce skill evolution to mere *accumulation*, leaving the library **ungoverned**… a tension we name **Skill Bloat versus Skill Governance**." | 共同缺陷命名
- [x] SHARED flaw (ungoverned accumulation), not two separate lists · [x] (★ ORAL) named concept **Skill Bloat versus Skill Governance** bolded (matches §Background subsection, brief 0.6) · [x] *accumulation* italic thought-core · [x] no "motivates our approach" (saved for 段4)

### 段 3 — Emerging direction + RQ

**句 3.1** "Given these deficiencies, organizing accumulated experience as a **structured, governed store**… offers a compelling alternative." | 转向第三方向
- [x] "Given these deficiencies" start · [x] third direction `\textbf{structured, governed store}` bolded · [x] "compelling alternative" · [x] no "we propose"

**句 3.2** "Existing efforts either build **(i) hierarchical graph memory**… or maintain **(ii) OS-style lifecycle memory**…" | 再细分两小类
- [x] **lowercase (i)(ii)** (visual layering vs 段2 uppercase (I)(II)) · [x] each sub-class + limitation (raw-task-string nodes / memory-not-skills) · [x] "either … or …" · [x] refs gmemory / memoryos+memos · [x] exactly 2 sub-classes

**句 3.3 + 3.5 (anchor recall)** "Nevertheless, both diverge from a usable skill store in **two critical dimensions**: no *refactoring*… and no *dependency-aware routing*… --- the algorithmic analogue of *stratifying* the library so higher layers *operate on top* of raw trace evidence~\citep{boccaletti2014multilayer}…"
- [x] 句3.3: 2 concrete dims (*refactoring* / *dependency-aware routing*) → map to 段4 govern/route design choices · not "flexibility" vagueness
- [x] 句3.5 (★ ORAL analogy): RECALLS the 段1 complex-networks anchor with shorthand "algorithmic analogue of … operate on top" + re-cites boccaletti2014multilayer; introduces NO new discipline (G6b safe) · italic thought-cores *stratifying* / *operate on top*
- [x] ends naming *minimal executable skill subgraph* (concept word reused in §Prelim/§Method/段4)

**句 3.6 (★ ORAL RQ, obsbox)** "*Should skill evolution end in ever-larger documents, or in a governable, composable, and routable skill graph?*"
- [x] single RQ ≤30 words (16 words) · [x] obsbox (style A) · [x] no method name (uses generic "skill graph") · [x] binary framing echoes 段2 (document vs governed graph) · verbatim from brief 3.3

### 段 4 — Method + callback (AgentFlow verb-role)

**句 4.1** "To address this challenge, we introduce **SkillStrata**, a stratified skill **system**…" | 提方法
- [x] "To address this challenge, we introduce" fixed start · [x] `\textbf{SkillStrata}` first bold (NOT SkillLEGO) · [x] type word = **system** (per "curate a system, not a skill", _global_facts) · [x] 0 architecture detail · [x] 0 forbidden words · [x] forward-teaser `\Cref{fig:framework}` (asset gate WAIVED, ref_home=§M0 owns the float; intro teases it)

**句 4.2** "At its core, SkillStrata coordinates three verb-roles: it **organizes**… it **governs**… and it **routes**…" | 核心机制 + 列组件 (merged)
- [x] "At its core" strong phrase · [x] AgentFlow verb-role naming **organizes / governs / routes** (concrete verbs, not "improves") · [x] N=3 roles · [x] propose-then-verify gate + "no gradients and no reinforcement learning" · [x] concept words echo 段3 (minimal executable skill subgraph) · [x] 0 hyperparam

**句 4.4 (★ STRICT callback)** "Unlike **(I) monolithic merge**, which invites **skill bloat**, and **(II) flat top-k retrieval**, which leaves the library **ungoverned**, SkillStrata **splits the monolith into a governed graph and routes only a dependency-complete subgraph**."
- [x] (★) explicit callback to 段2 (I) flaw **skill bloat** + (II) flaw **ungoverned** (both bolded, reused from 段2) · [x] "Unlike (I)… and (II)…, ours splits monoliths into a governed graph and routes a minimal executable subgraph" = brief 3.4 verbatim direction · [x] desired property bolded

**句 4.5 (assembly + verify-loop)** "At test time it **assembles** skills like LEGO bricks --- routing existing skills in-domain and casting a missing one from trace sub-parts out-of-domain --- guarded by a node-local verify-loop…"
- [x] 4th verb-role **assemble** (LEGO metaphor preserved) · [x] in-domain ROUTE / out-of-domain synthesis (component 3) + node-local verify-loop (component 4) · [x] "rubber-stamp its own error" foreshadows the §E6 [REAL] 416-15 false-confidence case · concept words echo 段3/method

### 段 5 — Empirical Highlights (★ PROVENANCE-respecting)

**句 5.1** "We evaluate SkillStrata on **[REAL]** SpreadsheetBench (qwen3.6-35b-a3b, the SkillOpt split) and a **[SIM]** deterministic simulator…" | 实验规模
- [x] explicit benchmarks + backbone · [x] [REAL]/[SIM] tags surfaced inline (provenance honesty) · [x] not vague "extensive evaluation"

**句 5.2 (★ ORAL hot baseline)** "Against the published **[REAL]** **SkillOpt** target, a No-Skill floor of 38.2 rises to 47.5 (+9.3) while a naively distilled **Trace2Skill** library *regresses* to 33.2 (−5.0, real negative transfer)…"
- [x] (★) hot baseline **SkillOpt** named (2026-current curation SOTA) · [x] real numbers bolded baselines · [x] ≥2 highlights (SkillOpt +9.3 / Trace2Skill −5.0) · [x] 0 dead baselines · [REAL] provenance · numbers verbatim from `_global_facts` REAL block

**句 5.4 (★ REAL gate — task-critical)** "Crucially, a **[REAL]** from-zero curate run shows the **propose-then-verify gate working**: …42.5%→32.5%, the gate **rejects** it (retiring 12 skills), then **accepts** the next, lifting accuracy to 47.5%…"
- [x] (★) the [REAL] validation-gate result, verbatim provenance: 42.5 → reject 32.5 (−10pp, 12 retired) → accept 47.5 (+5pp) · [x] "Crucially" emphasis · [x] "negative transfer screened out with no gradient signal" mechanism · this is the headline [REAL] evidence the task mandates

**句 5.3 (sim win + [PENDING] honesty)** "On the simulator, **[SIM]** SkillStrata attains the highest success (0.704 vs Trace2Skill's 0.574) at the lowest token cost (365 vs 780), while the full **[REAL]** 280-test head-to-head is **[PENDING]**."
- [x] [SIM] success+token double-win (the [SIM] wins the task lists) · [x] (★ honesty) 280-test = **[PENDING]**, NO fabricated number, named as not-yet-available · respects global_facts provenance lock

**句 5.6 (★★★ ORAL surprise hook)** "**More importantly**, our ablation shows these gains come from **splitting and routing, not amassing more skills** --- removing Split or Route inflates tokens up to 6.6× --- evidence that for **self-evolving agents**, structure beats bulk."
- [x] (★★★) bonus surprise hook present · [x] "More importantly" bolded lead · [x] content = counter-intuitive (gains from split/route, not more skills) = brief 2.5 reframe, [SIM] · [x] (★) echoes 大终点词 **self-evolving agents** (升华回环 to 段1.1/abstract/conclusion) · [x] not a repeat of 句5.2 main result

### 段 6 — Contributions (3 core, task → method → effect)

**Contrib ① 任务/系统级** "We **introduce** the problem of curating a *stratified skill system* rather than a single skill, instantiated as **SkillStrata**… subsumes single-layer skill-graph methods as its in-domain special case."
- [x] verb "introduce" · [x] task-level (the stratified-skill-system problem) + system named · [x] subsume framing (collapses competitors)

**Contrib ② 方法级** "We **propose** a gradient-free **curate** loop --- refactor-style Split and dependency-aware Route under a propose-then-verify gate --- with test-time **LEGO assembly** and a node-local verify-loop…"
- [x] verb "propose" · [x] method-level: curate (SPLIT/ROUTE + propose-then-verify gate) + test-time LEGO assembly + node-local verify-loop, no RL — exactly the task's ② spec

**Contrib ③ 效果** "We **show** that the gate autonomously rejects a harmful batch yet accepts a beneficial one on a real benchmark **[REAL]**, and that SkillStrata attains the highest success at the lowest token cost **[SIM]**, with the real-benchmark head-to-head **[PENDING]**."
- [x] verb "show" · [x] effect-level, MIXED provenance: [REAL] gate + [SIM] wins + [PENDING] 280-test in progress · [x] ③ ↔ §E2 main results
- [x] itemize (not inline 1)2)3)) · [x] 3 items (no release 4th — brief lists release as optional; kept core 3) · [x] semantic order task→method→effect · [x] 0 forbidden words

---

## Inter-paragraph consistency map (G4)
- 段2 (I) skill bloat / (II) ungoverned → 段4 句4.4 explicit callback "Unlike (I) … invites **skill bloat**, and (II) … leaves the library **ungoverned**" ✓
- 段2 named flaw "Skill Bloat versus Skill Governance" → §Background subsection (brief 0.6) ✓
- 段3 (i)(ii) lowercase vs 段2 (I)(II) uppercase (visual layering) ✓
- 段3 concept words (skill graph / minimal executable skill subgraph / lifecycle) → 段4 verb-roles organize/govern/route + "minimal executable skill subgraph" ✓
- 段1.1b complex-networks anchor (boccaletti2014multilayer) → 段3.5 recall → §M0 line 12 only recalls (no new discipline) ✓ (G6a/G6b)
- 段5.2 hot baseline SkillOpt → §E2 [REAL] target in 02_experiment.md (38.2→47.5, Trace2Skill 33.2) ✓
- 段5.4 [REAL] gate 42.5→32.5→47.5 → §E4 / §M2 same numbers ✓
- 段6 ③ effect ↔ §E2 main results; 大终点词 self-evolving agents = abstract句1 / conclusion句4 ✓

## Global pre-delivery checklist (Phase 3)
| # | Check | Result |
|---|---|---|
| G1 | Word count [500–700] | **⚠ ~770 prose / 812 detex-token — at/just over HARD ceiling ~770. Flagged honestly (see note).** |
| G2 | Paragraph count 6 | PASS (6) |
| G3 | All per-sentence local checklists pass | PASS (28/28; 句1.3/1.4/1.5 deliberately omitted per §A weak-by-default) |
| G4 | Inter-paragraph consistency map intact | PASS |
| G5 | 段2 two paradigms (I)(II) bold roman | PASS |
| G5a | 句2.0 route-shift present (brief 3.2 NON-`[无]`) + barrier Z named | PASS (skill-bloat barrier explicit) |
| G6 | 段3 external analogy + ≥1 authoritative cite | PASS (complex networks, boccaletti2014multilayer, recalled) |
| G6a | (★) 段1 句1.1b names discipline + cites same key §M0 uses | PASS |
| G6b | (★) §M0/§E5/conclusion introduce NO new discipline | PASS (§M0 line 12 recalls complex networks; conclusion uses OS-style, already seeded via memoryos/§M2 heat) |
| G7 | 段3 explicit RQ (obsbox) | PASS |
| G8 | 段4 explicit callback 段2+3 flaws | PASS (句4.4) |
| G9 | 段5.2 hot baseline named | PASS (SkillOpt) |
| G10 | 段5 efficiency double-win (perf↑+cost↓ same sentence) | PASS (句5.3: highest success AT lowest token cost, one sentence) |
| G11 | 段5.6 surprise hook present | PASS |
| G12 | 段6 numbered contributions verb-first | PASS (3 items) |
| G13 | No forbidden words (novel/impressive/remarkable/SOTA/promising) | PASS (grep clean) |
| G14 | ≥1 italic thought-core word | PASS (*operate on top*, *stratifying*, *accumulation*, etc.) |

→ **Hard-fail count: 0 on G2–G14. G1 is at the ceiling (~770) — see honest note.**
→ **ORAL-soft: 6/7 (G6 anchor, G6a, G7 RQ, G9 hot-baseline, G10 double-win, G11 surprise hook). G14 italic ✓.**

## G hard-fails encountered + fixes
- **G1 length (initial 1125 → 770 prose).** First draft ran ~1125 prose words (every paragraph over budget). Trimmed across 6 passes: 段2 dropped "as unrelated behaviors are dragged into every task" + redundant clauses; 段4 merged the strata-definition sentence into 句4.1 and cut "equipping the agent with structure rather than bulk"; 段5 dropped "(8 seeds, four domains)" / "($2.1\times$ fewer)" / "and reported as in progress" filler and tightened the SkillOpt sentence; 段3 句3.4 (separate "raises whether…") folded into 句3.3 so the obsbox carries the RQ; 段6 ③ dropped "recovering out-of-domain coverage". Landed at ~770 prose / 812 detex tokens.
- **Honest residual:** even after trimming, the Intro sits at the HARD ceiling (~770). The remaining length is load-bearing: the 7-ref dump (1.1), the mandatory external-discipline anchor (1.1b), the full 段4 callback, and — critically — the **mandated [REAL]/[SIM]/[PENDING] provenance disclosure in 段5** (3 separate real/sim/pending claims that cannot be collapsed without hiding provenance). I did not delete any hard-required element to gold-plate the word count under the band; if a further ~40-word cut is required, the only safe target is 段5 句5.3 (drop the parenthetical sim numbers, keeping the qualitative claim) — left to the author since it would weaken the only [SIM] quantitative hook.

## Honest notes
- **No per-sentence step skipped.** All 28 checklists run; 句1.3 (adjacent-topic exclusion), 句1.4 (scope-lock), 句1.5 (hot-model standalone dump) deliberately OMITTED per skill §A (weak-by-default; scope clear from title + 句1.1; models mentioned lightly in 段5 backbone instead) — this is a documented omission, not a skipped check.
- **Asset gate WAIVED** for `\Cref{fig:framework}` (no `_asset_inventory.json` on disk; `figures/framework.pdf` is [ASSET PENDING] per _global_facts line 63). Consistent with how 01_method.md / 02_experiment.md / 04_related-work.md wrap their `\Cref{}`/`\includegraphics` with TODO and proceed. ref_home of fig:framework = §M0 (it owns the float); 段4 句4.1 teases it forward, which is allowed.
- **Provenance integrity:** the 280-test head-to-head is [PENDING] everywhere it appears (段5 句5.3, 段6 ③) — NO fabricated number. The [REAL] gate (42.5/32.5/47.5) and SkillOpt target (38.2/47.5; Trace2Skill 33.2/−5.0) are verbatim from `_global_facts` REAL block. [SIM] numbers (0.704/0.574, 365/780, 6.6×) verbatim from the [SIM] block.
- **Naming:** SkillStrata throughout (NOT SkillLEGO); LEGO kept only as the test-time-assembly *metaphor* (段4 句4.5, 段6 ②), consistent with brief naming lock and prior drafts.
- **Forbidden-word grep:** clean (no novel/impressive/remarkable/SOTA; "promising" absent — not even the allowed "promising path" needed here).

## Suggested second-pass refinements
1. If the author confirms the brief Part 13.1.bis Introduction band override (none set today), the ~770 length is fine as-is; otherwise apply the single safe ~40-word cut noted under G1 (段5 句5.3 parenthetical sim numbers).
2. Once `figures/framework.pdf` exists and an `_asset_inventory.json` is generated, replace the `\Cref{fig:framework}` TODO waiver and confirm ref_home=§M0 (intro teaser allowed).
3. When the [PENDING] 280-test result lands, 段5 句5.3 + 段6 ③ can be upgraded from "[PENDING]" to a real headline number — at which point the [SIM] sim hook in 句5.3 may be demoted to the appendix.
