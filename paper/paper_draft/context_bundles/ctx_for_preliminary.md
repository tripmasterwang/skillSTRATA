# Context Bundle for paper-preliminary — SkillStrata

> Assembled for the §Preliminary / Problem Formulation drafting pass.
> Method (§Method, drafts/01_method.md) and §Experiments (drafts/02_experiment.md) already exist; reuse their symbols verbatim. Invent NO numbers/refs/claims beyond the pointers below.

## Pointers (source of truth)
- BRIEF Part 5 (Preliminary): `.../PAPER_BRIEF_FILLED.md`
  - 5.1 main variable; 5.2 prior values; 5.3 our value; 5.4 evocative concept name + formal def.
- BRIEF Part 6 (Method) — for symbol consistency only.
- GLOBAL FACTS (LOCKED): `.../_global_facts.md`
- PRIOR DRAFTS: `drafts/01_method.md`, `drafts/02_experiment.md`.

## Three locked decisions (Phase 1)
1. **Main variable** = *skill granularity*, instantiated as the stratified skill graph $\mathcal{G}=(\mathcal{G}_{\text{trace}},\mathcal{G}_{\text{cap}},\mathcal{G}_{\text{gov}})$. The granularity of the nodes that $\mathcal{G}$ admits IS the sweep variable (atomic / functional / plan). Symbol $\mathcal{G}$ is locked across abstract/intro/method/experiments — DO NOT rename.
2. **Number of prior paradigms** N=2 (matches global_facts + experiments §E1):
   - Paradigm I = **monolithic skill** (Trace2Skill / SkillBrew / SkillOpt) — one plan-level node, no edges, full-load.
   - Paradigm II = **flat skill bank** (top-k retrieval) — atomic nodes, no edges (E=∅), top-k subset load.
3. **Evocative concept name** = *minimal executable skill subgraph* $\mathcal{S}^\star$ (first formally named here; reused ≥5× in method/experiments). (italic first use)

## 8 facts
1. Global stage: an agent solving tasks $t$ drawn from a task distribution / domain, with a **frozen** backbone LLM $\pi$ and a frozen ReAct executor $E$.
2. Trajectory object: solved task → distilled patches → recorded as execution evidence in $\mathcal{G}_{\text{trace}}$.
3. Main variable: the **stratified skill graph** $\mathcal{G}=(\mathcal{G}_{\text{trace}},\mathcal{G}_{\text{cap}},\mathcal{G}_{\text{gov}})$ with skill nodes $v$, $\text{status}(v)\in\{\text{candidate},\text{validated},\text{deployed},\text{retired}\}$; the regulated quantity is **skill granularity** = the level (atomic/functional/plan) of the nodes $\mathcal{G}$ admits.
4. Evocative concept: *minimal executable skill subgraph* $\mathcal{S}^\star$.
5. Objective: maximize task success at minimal loaded-token cost; injected library $=$ a subset/subgraph of $\mathcal{G}$ that conditions the frozen executor.
6. Generation/selection mechanism: routing $\mathcal{S}^\star = \text{closure}_{\text{depends\_on}}(\text{seed}_k(t)) \setminus \text{blocked}(\mathcal{G}_{\text{gov}})$ (Eq. route, locked from method Eq:route).
7. Paradigm I value: $\mathcal{G}$ collapses to a single plan-level node $d$, no edges → load = full $d$. Paradigm II value: $\mathcal{V}$ = atomic nodes, $\mathcal{E}=\varnothing$ → load = top-$k$ slice.
8. Our value: full stratified $\mathcal{G}$ across all granularities; load = dependency-closed minimal subgraph $\mathcal{S}^\star$ (not full doc, not flat top-$k$).

## Symbols locked from prior drafts (reuse verbatim)
- $\mathcal{G}=(\mathcal{G}_{\text{trace}},\mathcal{G}_{\text{cap}},\mathcal{G}_{\text{gov}})$ — three-layer skill graph (method Eq:node/route).
- $v$, $\text{status}(v)$; $\text{seed}_k(t)$ top-$k$ BM25 seeds; $\text{closure}_{\text{depends\_on}}(\cdot)$; $\text{blocked}(\mathcal{G}_{\text{gov}})$; $\mathcal{S}^\star$ minimal executable subgraph (Eq:route).
- $\pi$ frozen backbone, $E$ frozen ReAct executor (method §M0, alg:ops).
- Citation keys available: `trace2skill`, `skillopt` (no others invented).

## §Preliminary spec
- 3 paragraphs: Notation → Problem Formalization → Unified View / Granularity Sweep.
- Main-variable unification: monolithic = single plan-level node; flat bank = atomic nodes no edges; SkillStrata = full stratified graph across all granularities (subsume as special cases of ONE variable).
- Routing formalized as selecting minimal executable subgraph = seed dependency closure − governance-blocked.
- Word band 200–300 (hard fail >330). ≤8 symbols. 2 equations (objective + route), both \label'd.
- Paradigm names MUST match intro/§Background: monolithic skill (I), flat skill bank (II).
