# Look-Back Consistency Audit — SkillStrata paper

## ⚠️ WAIVERS (logged per paper-from-brief blocking rules — user-authorized 2026-06-27)

### W1. Asset-inventory gate (Phase 0.5 / 2.5) — WAIVED by user
- **What**: brief Part 12 lists 3 figures (`fig:framework`, `fig:routing`, `fig:stability`) + 4 tables
  (`tab:main`, `tab:ablation`, `tab:setup`, `tab:tta`). **None exist on disk** (`figures/` and `tables/` empty);
  brief Part 12 itself marks them all `[待生成]`.
- **Decision**: user chose "豁免资产门,现在全量草拟" (waive the asset gate, draft all sections now).
- **Consequence**: sections will `\Cref{}` these labels but the float environments are NOT emitted; the draft
  **WILL NOT COMPILE** until `paper-figure` / `sim/report.py` generates the assets and they are filled in.
  Every such ref is a known dangling ref, intentionally deferred — NOT a G_INV.5 violation to fix now.

### W2. Results provenance — MIXED ([SIM] + partial real + PENDING)
- §Experiments numbers are drawn from: (a) the deterministic simulator `[SIM]` (main table, ablations, TTA);
  (b) real partial data (SkillOpt comparison target, from-zero curate val trajectory, negative-transfer case);
  (c) **the core 280-test head-to-head (no-skill vs with-skill) is NOT YET AVAILABLE** (run still on round 2/4).
- **Consequence**: §Experiments main result is written against `[SIM]` / `[PENDING-280TEST]` placeholders.
  `paper-claim-audit` (Phase 10b) WILL flag every `[SIM]` number — that is expected. These must be replaced with
  real benchmark numbers before submission. Do NOT treat any `[SIM]` number as a verified fact.

### W3. Method name corrected vs stale brief
- Brief Part 1 originally said `SkillLEGO` (2026-06-21). Per memory (2026-06-24 author rename) + project dir
  `skillSTRATA`, the current name is **SkillStrata**. Brief bulk-renamed 2026-06-27; locked in `_global_facts.md`.

---

## Status: foundation built (Phase 0–1 done). Section drafting in progress.
(Full C1–C10 cross-section audit to be populated after all section drafts exist.)

---

# Phase 9 — Cross-Section Look-Back Consistency Audit (C1–C10) — 2026-06-27

Scope: all 9 reading-order sections — `07_abstract`, `06_intro`, `00_background`,
`04_related-work`, `03_preliminary`, `01_method`, `02_experiment`, `05_conclusion`, `08_title`.
Legend: ✅ pass · ⚠️ soft (acceptable, logged) · ❌ hard-fail (fixed in-place; see §"Hard-fails fixed").

**Tally: 18 ✅ · 5 ⚠️ · 1 ❌ (fixed).** No remaining hard-fails.

## C1 — Method naming consistency ✅
- "SkillStrata" appears identically across all sections (79× in drafts); three-layer graph "Skill Strata"
  (12×) used only for the graph object, never the method — distinction is intentional and consistent.
- **"SkillLEGO" leaks: NONE in any draft body.** The only "SkillLEGO" strings are inside `*.justification.md`
  notes that say *"NOT SkillLEGO"* (deliberate reminders) — not paper content. "LEGO" survives only as the
  test-time-assembly metaphor ("assemble … like LEGO"), per the naming lock. ✅
- "SkillOS" appears only as the cite-key/short-name `skillos_ouyang` (same-name competitor) — not as our method.

## C2 — Number consistency across sections ✅
- 0.704 / 0.574 (sim success): identical in abstract, intro §5.3, experiment §E2. ✅
- 365 / 780 tokens, 2.1× (intro says "≈2×", abstract "roughly 2×", experiment "2.1×"): consistent rounding. ✅
- REAL gate 42.5 → 32.5 (−10pp, 12 retired) → 47.5 (+5pp): identical in method §M2, experiment §E4, intro §5.4,
  abstract (qualitative "10 points"). ✅
- SkillOpt target 38.2 → 47.5 (+9.3); Trace2Skill 33.2 (−5.0): identical in intro §5.2 and experiment §E2. ✅
- TTA ~54% (0.296→0.473): identical in method §M3 and experiment §E6. ✅
- 6.6× token inflation on w/o-Split: intro §5.5 and experiment §E3 agree. ✅

## C3 — RQ ↔ contribution ↔ §E mapping ⚠️ (soft, documented)
- RQ1–RQ5 each map to EXACTLY ONE §E subsection: E2=RQ1, E3=RQ2, E4=RQ4, E5=RQ3, E6=RQ5
  (one `[RQ_n]` label per subsection — ONE-RQ-HARD rule). ✅ on the one-to-one property.
- ⚠️ **Numbering drift vs `_global_facts.md` RQ list**: global-facts numbers RQ3=governance/stability and
  RQ4=routing/neg-transfer; the experiment draft SWAPS the *display positions* (E4 carries RQ4=routing,
  E5 carries RQ3=stability) so the section order flows outcome→mechanism→safety-net. The brief's own Part 7.1
  table already maps RQ3→§E4 and RQ4→§E2, i.e. the brief is internally inconsistent on RQ3/RQ4 ordering.
  The draft's mapping is self-consistent and each RQ still appears exactly once. Logged as soft, NOT fixed
  (renumbering would touch 5 subsection titles for zero semantic gain). Contributions C1/C2/C3 (intro 段6)
  map cleanly: C1↔Method+Preliminary, C2↔curate loop+TTA+verify-loop (§M2/§M3, §E2/E3), C3↔gate [REAL]+sim [SIM]+[PENDING]. ✅

## C4 — References / cite-keys ✅ (with provenance caveat)
- 13 distinct cite-keys grep'd: trace2skill, skillopt, skillbrew, evoskill, skillos_ouyang, gmemory,
  memoryos, memos, skillgraph_rl, gos, skillgraph_toolseq, boccaletti2014multilayer, qwen36.
- Every key has a stub in `references.bib`. ✅
- ⚠️ 9 keys are PROVISIONAL (`% TODO citation-audit`: skillbrew, evoskill, skillos_ouyang, memos,
  skillgraph_rl, gos, skillgraph_toolseq, boccaletti2014multilayer, qwen36 — `qwen36` added beyond the
  brief's list because §E1 cites it). `memos` arXiv id is a hard placeholder. Must run citation-audit
  before submission. Logged (already covered by submission-TODO #3).

## C5 — Equation labels ✅
- Defined: eq:node, eq:route, eq:split, eq:gate, eq:tta, eq:verify (method); eq:objective, eq:route-prelim
  (preliminary). Every `\Cref{eq:*}` in-text resolves to a defined label. No duplicate labels across
  the two files (eq:route vs eq:route-prelim are distinct, intentionally). alg:ops defined + referenced. ✅

## C6 — Figure / table labels ⚠️ (W1-deferred, expected)
- Defined floats: fig:framework (method, currently commented-out block), tab:differentiation (related-work, LIVE).
- ⚠️ Dangling refs (label NOT emitted, by W1 waiver): fig:routing, fig:stability, tab:main, tab:ablation,
  tab:setup, tab:tta. All six are catalogued in main.tex `% ===== ASSET TODO =====`. Each in-text `\Cref`
  is wrapped with a `% TODO` comment. NOT a fix-now item (gate waived); will be a real undefined-ref at
  compile until assets exist. Logged.

## C7 — Inter-section bridges ✅
- Intro 段4 callback "splits the monolith into a governed graph and routes only a dependency-complete
  subgraph" echoes Method §M1 closer and the framework caption verbatim-ish. ✅
- Preliminary `eq:route-prelim` reuses Method `eq:route` symbols verbatim (seed_k, closure, blocked). ✅
- Experiment §E0 hypothesis ("split, routed, assembled on demand") echoes Method narrative. ✅
- Conclusion 句2 recalls curate / Skill Strata / SPLIT / ROUTE / propose-then-verify / LEGO assembly. ✅

## C7a — §M0 ↔ Intro duplication (external analogy) ⚠️ (soft)
- The complex-networks / hierarchical-multilayer-network analogy is INTRODUCED in Intro 段1
  ("Research on complex networks offers a familiar template …", `\citep{boccaletti2014multilayer}`).
- §M0 RECALLS it ("Just as a hierarchical multilayer network …") — a callback, not a fresh concept. ✅ on role.
- ⚠️ §M0 re-`\citep{boccaletti2014multilayer}` and re-states the "operate on top" gloss, which reads close to
  re-introduction. Acceptable as a method-opening callback (FINAL_PLAYBOOK allows §M0 to restate the analogy
  ONCE) but flagged: if a reviewer dings duplication, trim §M0 to "Recalling the multilayer-network view of
  §Intro, …" without the full gloss. Not fixed (within tolerance). Abstract 句1/句2.5 also use the analogy —
  that is the intended echo map, not duplication.

## C8 — ORAL signals ✅
- Abstract: 8-sentence structure with 句2.5 bridge ("This tension is not fundamental: a hierarchical
  multilayer network already resolves it…") + 句7 "Most strikingly" false-confidence hook. ✅
- Intro: 6-paragraph, obsbox RQ, "More importantly" highlight hook, threefold contributions. ✅
- Experiment subsections use claim-titles + "More generally, this suggests a transferable principle" S9 hooks. ✅
- Conclusion: \ding{182–185} numbered highlights + aspiration ("self-evolving agents") + ORAL flourish. ✅

## C9 — Length / anti-compression ✅
- Abstract 8 sentences (~215 words, within 180–255 band). Conclusion single paragraph 6 sentences (~150 words).
- Background subsection ~80 words (target met). Method 5 subsections + algorithm box. Experiment 6 RQ
  subsections + setup + efficiency — no per-benchmark or per-ablation compression beyond what the [SIM]
  single-world setup forces (documented in brief 7.3.bis). ✅

## C10 — Appendix ✅ N/A
- No appendix assembled this phase (brief Part 9 appendix is deferred with the asset/real-benchmark work).
  No `\appendix` / `\input{appendix}` in main.tex; no in-text `\Cref{app:*}` in any draft. Consistent. ✅

## Provenance integrity (cross-cut, part of W2) ✅
- [SIM] / [REAL] / [PENDING] / [PENDING-280TEST] tags are consistent across abstract / intro / experiment /
  conclusion. No section launders a [SIM] number into a clean claim: the abstract carries the 0.704/0.574
  sim figure but frames it as "in controlled simulation" (acceptable — abstracts omit bracket tags by
  convention, the qualifier carries provenance). The 280-test head-to-head is [PENDING] everywhere it
  appears and is NEVER given a fabricated number (abstract deliberately omits it; intro 段5.3/段6③ and
  experiment §E2 mark it [PENDING]/[PENDING-280TEST] explicitly). ✅

---

## Hard-fails found AND fixed (in-place)

### F1 ❌→✅ — Orphan `\caption{}` outside its float (compile-breaker) — FIXED
- **Where**: `sections/01_method.tex` (copied from draft) lines ~142–147: the framework figure's
  `figure*` block is commented out (asset PENDING / W1) but the `\caption{...}` beneath it was LEFT LIVE,
  i.e. a `\caption` with no enclosing float → hard LaTeX error the moment anything else compiles.
- **Fix**: commented out the orphan `\caption{...}` block in `sections/01_method.tex` and added
  "% ASSET TODO: uncomment … once figures/framework.pdf exists". The figure caption now travels as one
  commented unit with its `figure*` and uncomments cleanly when the asset lands.
- Note: the original draft `paper_draft/drafts/01_method.md` was left as-is (it is the source draft);
  the fix is applied to the assembled `sections/01_method.tex` which is what main.tex `\input`s.

## "SkillLEGO" leak scan result
- **0 leaks in paper content.** Confirmed via `grep -rni "skilllego|skill lego"` over all 8 section drafts —
  every hit is inside `*.justification.md` audit notes phrased as "NOT SkillLEGO". The metaphor "LEGO"
  (test-time assembly) is intentionally retained. ✅

## Could NOT verify / assemble (honest notes)
- **Compile**: NOT attempted (per instruction). main.tex will NOT compile until (a) cleveref-without-hyperref
  or \Cref→literal replacement is done, (b) the 6 deferred floats + tables are generated, (c) the 9 provisional
  bib entries are verified. All catalogued in main.tex ASSET TODO.
- **Bib correctness**: 9/13 cite-keys are unverified placeholders (titles/authors/ids inferred from brief);
  `memos` arXiv id is fabricated-placeholder. citation-audit still required.
- **[SIM]/[PENDING] numbers**: not independently re-derived from `results/*.json` this phase (that is
  paper-claim-audit's job); only cross-section *consistency* was checked, which passed.
- **RQ3/RQ4 numbering**: left as the draft's self-consistent ordering despite mismatch with `_global_facts`
  RQ list ordering (soft C3) — flagged for author decision, not auto-renumbered.
