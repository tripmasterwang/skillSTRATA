# Global Facts (locked from brief — DO NOT change across chapters)

## Naming convention (must match across all sections)
- Method name: **SkillStrata** (NOT SkillLEGO — renamed 2026-06-24; method name = three-layer system name)
- Three-layer system: **Skill Strata** (stratified three-layer skill graph: trace / capability / governance)
- Method type word: **system** ("curate a system, not a skill")
- Code package: `skillos/` (unchanged)

## Paradigm framing
- §2 route-shift motivation: monolithic/flat skill products → a stratified, governed skill *system* (barrier: skill bloat + negative transfer + no dependency/governance structure)
- Paradigm I: **monolithic skill** (Trace2Skill / SkillBrew / SkillOpt) — flaw: **skill bloat / full-load / negative transfer**
- Paradigm II: **flat skill bank** (top-k retrieval) — flaw: **no dependency closure / no governance → mis-routing**
- Common flaw (named concept, §Background subsection): **"Skill Bloat vs. Skill Governance"**
- Third direction: **stratified three-layer skill graph + test-time assembly**

## Core variable + concept words
- Main object: the **Skill Strata** graph $\mathcal{G} = (\mathcal{G}_{\text{trace}}, \mathcal{G}_{\text{cap}}, \mathcal{G}_{\text{gov}})$
- Main variable subsuming prior methods: **skill granularity** (atomic / functional / plan) — monolithic = one plan-level node; flat bank = atomic nodes no edges; ours = full stratified graph
- Evocative concept words: *execution trace*, *capability graph*, *governance*, *stratified skill graph*

## Components (abstract 句4 / intro 段4.3 / method §M2.x / conclusion 句2)
- Component 1: **Skill Strata** (three-layer graph) — trace (execution evidence + sub-capability co-occurrence) / capability (modular skills + depends_on/composes_with/conflicts_with) / governance (split/merge/retire/route rules)
- Component 2: **Curate** (offline, no-grad / no-RL) — 7 operators INSERT/UPDATE/**SPLIT**/MERGE/LINK/RETIRE + **propose-then-verify gate** (held-out validation) + heat lifecycle
- Component 3: **LEGO assembly** (test-time) — in-domain: ROUTE the minimal executable subgraph; out-of-domain: TTA synthesizes a fit skill from sub-parts
- Component 4 (this session, governance sub-mechanism): **node-local verify-loop** — checkpoint guards on error-prone nodes (learned from trace failure stats); execute→verify(sub-goal)→rollback→retry. Governance gates the library at train time (validation_gate) AND execution at inference time (verify-loop).

## Big aspiration (abstract 句1 ↔ intro 段1.1 ↔ conclusion 句4)
- 大终点词: **self-evolving agents**

## ORAL reframe 招式
- Selected: **AgentFlow** (modular naming, multi-component coordination)

## External analogy (intro 段3.5 + method §M0)
- Discipline: **complex networks** — *hierarchical multilayer network* (raw evidence at the bottom, higher layers operate on top)
- Thought-core word (italic): *stratified* / *operate-on-top*

## Hot baseline names (abstract 句6 / intro 段5.2 / experiments §E1.B)
- Trace2Skill (monolithic full-load), Flat skill bank (top-k embedding/BM25), **SkillOpt** (prune + validation gate)
- also: SkillBrew, G-Memory, MemoryOS, EvoSkill, Graph-of-Skills (GoS), SkillGraph-RL
- backbone: **qwen3.6-35b-a3b** (xf-yun MaaS, reasoning_effort=medium)

## Locked numbers (★ MIXED provenance — mark every number's status)
### REAL (verified this session, 2026-06-27)
- **Comparison target — SkillOpt paper (arXiv 2605.23904 Table 1, Qwen3.6-35B-A3B, SpreadsheetBench, direct-chat harness, native hard / exact-match)**:
  no-skill **38.2** → **SkillOpt 47.5 (+9.3)**; Trace2Skill **33.2 (−5.0, negative transfer)**; GEPA 45.4 / Human 44.3 / LLM-skill 42.9 / TextGrad 22.9. (caveat: harness differs from ours → compare gain-over-no-skill or run same harness.)
- **Our from-zero curate, validation gate (real, 40 val, official per-instance hard)**: S0 blank graph **42.5%** → round0 distilled skills **32.5% (−10pp) → gate REJECTS, 12 skills retired** → round1 **47.5% (+5pp) → gate ACCEPTS, 12 skills deployed**.
- **Negative-transfer case study (real trace, task 416-15)**: no-skill solves it; injecting round0 skills breaks it (datetime→string via strftime; self-verification skill verifies a tautology → false confidence "All checks passed"). 6/40 val regressions in the rejected round; 3 = "Output file not found" (over-engineering), 3 = wrong value/format.
### PENDING (run still going, Phase 2 not done)
- **280-test head-to-head: no-skill vs with-skill (SkillStrata) on the SkillOpt 280 split** — THE main result, NOT yet available. → [PENDING-280TEST] placeholder in §Experiments main table.
### [SIM] (deterministic simulator — to be replaced by real benchmark)
- main: success **0.704** vs Trace2Skill 0.574 / flat 0.555; tokens **365** vs 780 / 3932; negative transfer 0.105 vs 0.219; OOD gain +0.256; routing precision 0.391.
- ablation: SPLIT and ROUTE are the largest contributors (−0.15 / −0.18 success when removed; removing SPLIT inflates tokens ~6.6×); governance/validation = complementary safety net (impact mainly when both removed → late-stream degradation).
- TTA: out-of-domain assembly recovers ~54% of the coverage gap.

## RQ list (intro 段6 ↔ experiments §E0 ↔ subsection titles)
- RQ1: Can graph governance + routing reach higher success at lower token cost? → §E2 main results (tab:main)
- RQ2: Which operators drive the gains (SPLIT/ROUTE vs more skills)? → §E3 ablation (tab:ablation)
- RQ3: What role do governance/validation play (stability / safety net)? → §E4 (fig:stability)
- RQ4: Routing precision / negative-transfer reduction? → §E2/§E3
- RQ5: Can test-time assembly recover out-of-domain coverage (TTA)? → §E5 (tab:tta)

## Framework figure
- Path: `figures/framework.pdf` — ★ [ASSET PENDING — gate waived; ref kept, env deferred]
- Caption draft: SkillStrata data flow traj→patch→graph governance→ROUTE→executor; three layers side by side; frozen grey, governance components colored.
- Other planned assets (all PENDING): fig:routing, fig:stability, tab:main, tab:ablation, tab:setup, tab:tta.
