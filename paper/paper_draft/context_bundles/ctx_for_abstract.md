# Context Bundle — SkillStrata Abstract (paper-abstract skill)

> Assembled 2026-06-27 for drafting `drafts/07_abstract.md`. Source of truth:
> `PAPER_BRIEF_FILLED.md` Part 2, `_global_facts.md`, and the 6 prior drafts.

## Locked naming (must match all sections)
- Method: **SkillStrata** (NOT SkillLEGO). Type word: **system** ("curate a system, not a skill").
- Three-layer graph: **Skill Strata** (trace / capability / governance).
- 大终点词 (句1 ↔ 句7): **self-evolving agents**.
- LEGO = test-time assembly **metaphor** (kept).

## Three locked decisions
1. **句1 风格** = B (MemGen: memory/cognition/agent) — skill libraries refine themselves akin to a layered/stratified store.
2. **ORAL reframe 招式** = AgentFlow (modular verb-role naming) + **complex-networks** analogy:
   *hierarchical multilayer network* — raw evidence at bottom, higher layers *operate on top*. This analogy carries 句1 (light) → 句2.5 (full bridge claim) → 句5/句7 echo. SAME discipline throughout.
3. **句7 意外发现** = C (counter-intuitive) — bonus hook = the negative-transfer **false-confidence** finding (a distilled skill's own self-check verifies a tautology, not task semantics), motivating gate-as-governance at both train and inference (train/inference symmetry).

## Paradigm conflict (句2)
- Paradigm I = **monolithic skill** (Trace2Skill/SkillBrew/SkillOpt): merges into one ever-growing document → **skill bloat / full-load / negative transfer**.
- Paradigm II = **flat skill bank** (top-k retrieval): no dependency closure, no governance → **mis-routing** (omits prerequisites, admits conflicts).
- Named common flaw: **Skill Bloat versus Skill Governance**; both reduce evolution to ungoverned *accumulation*.

## ★ Bridge claim (句2.5) — the insight that resolves the conflict, BEFORE the method
The conflict is not fundamental: a *hierarchical multilayer network* already resolves exactly this — keep raw execution evidence at the bottom, and let governance layers *operate on top* to decide what each task should load — so structure, not bulk, governs use. (Same complex-networks discipline as 句1; no method name; no numbers.)

## Method (句3) + technique (句4)
- 句3: "Guided by this principle, we present **SkillStrata**, a stratified skill **system** that curates trace-to-skill evolution into a governed three-layer graph and assembles task-fit skills at test time."
- 句4 components (N=3, AgentFlow verb-roles): **Skill Strata** three-layer graph (organize) / **curate** lifecycle operators **SPLIT/MERGE/LINK/RETIRE** + **propose-then-verify gate** (govern, no-grad/no-RL) / test-time **LEGO assembly** = in-domain **ROUTE** the minimal executable subgraph + out-of-domain synthesis, plus a **node-local verify-loop**.
- Narrative concept words (resurface in 句7): *execution trace*, *governance*, *stratified*, *false confidence*, *self-check*.

## 句5 qualitative effect (NO numbers)
By this design SkillStrata splits a monolith into a governed graph, routes only what a task depends on, and casts missing skills on demand — turning ungoverned accumulation into a *governed, routable skill system*.

## 句6 empirical highlight (PROVENANCE-HONEST — do NOT state the 280-test number; it is [PENDING])
- [REAL] validation gate: on real SpreadsheetBench, from-zero curate — gate **rejects** a harmful distilled round (val 42.5% → 32.5%, −10pp, retiring 12 skills) and **accepts** the next (+5pp over the blank graph). Use this as the headline behavior.
- [SIM] efficiency/success: success **0.704 vs Trace2Skill 0.574**, at **~2× fewer** loaded tokens (365 vs 780). Mark [SIM].
- Hot baseline named: **Trace2Skill** (and/or SkillOpt as the published comparison target).
- DO NOT fabricate a 280-test number. The main 280 head-to-head is [PENDING].

## 句7 bonus hook (counter-intuitive)
Counter-intuitively, a distilled skill can *harm* an unseen task it would otherwise solve, because the skill's own self-check verifies a tautology rather than task semantics — manufacturing **false confidence** — which is exactly why governance must gate execution node-by-node, not only the library round-by-round (the same gate in two tenses). Echoes *governance* / *self-evolving agents*.

## Constraints
- PROSE ONLY. No \cite, no \ref, no \Cref, no \includegraphics.
- Word band: soft [180, 255]; hard outside ~[162, 280]. Target ~210.
- Forbidden words: novel / impressive / remarkable / SOTA / promising.
- Mark provenance honestly in prose where a number appears ([REAL]/[SIM]); do NOT mark the abstract with literal "[SIM]" brackets — instead phrase so provenance is honest (gate = real, simulator = "in controlled simulation").
