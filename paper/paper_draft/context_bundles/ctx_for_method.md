# Context Bundle for paper-method — SkillStrata

> Assembled for the Method section drafting pass (method-first; Intro does NOT exist yet).
> This bundle concatenates the two source-of-truth pointers below. Invent NO numbers/refs/claims beyond them.

## Pointers (source of truth)
- BRIEF: `/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/projects/skillSTRATA/paper/paper_draft/PAPER_BRIEF_FILLED.md`
  - Part 6 = method components (subsection list 6.0, framework fig 6.1, M0 narrative 6.2, metaphor table 6.3, per-component detail 6.4, algorithm box 6.5, properties 6.6)
  - Part 5 = formalization (5.1–5.4: $\mathcal{G}=(\mathcal{G}_{\text{trace}},\mathcal{G}_{\text{cap}},\mathcal{G}_{\text{gov}})$, status(v), minimal executable subgraph $\mathcal{S}^\star=\text{closure}_{\text{depends\_on}}(\text{seed}(t))\setminus\text{blocked}$)
  - Part 2.3 = core method data (3 components + governance verify-loop sub-mechanism)
  - Part 11 = code mapping (skillos/ engine; tta.py; graph.py)
  - Part 3.4 = method narrative (organize → govern → route)
- GLOBAL FACTS (LOCKED names/numbers — use verbatim): `/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/projects/skillSTRATA/paper/paper_draft/_global_facts.md`

## Locked decisions extracted for this pass
- Method name = **SkillStrata** (NOT SkillLEGO). Three-layer system = **Skill Strata** (trace / capability / governance). Method type word = **system**. Code package `skillos/`.
- §Method subsection list (author-declared, brief Part 6.0) — USE EXACTLY, do not default to 4:
  - §M0  Overview: Curate a Stratified Skill System, Assemble Skills at Test Time  (claim-title)  — fig:framework
  - §M1  Skill Strata: a Three-Layer Skill Graph (trace / capability / governance)  (descriptive)  — fig:framework
  - §M2  Curating the Strata: Lifecycle Operators (SPLIT/MERGE/LINK/RETIRE + verify gate), no RL  (claim-title)  — alg:ops
  - §M3  Test-Time LEGO Assembly: In-Domain Routing + Out-of-Domain Synthesis  (claim-title)  — fig:routing
  - §M4  Properties / Complexity & Trace2Skill Integration  (descriptive)
- component_type (brief Part 6.4): ALL THREE core components = ④ **hard_rule** → single `\paragraph{}` + exactly 1 scoring/decision Eq with `\underbrace{}_{\text{语义}}`, NO training loss. (no-grad / no-RL).
- preliminary_present = yes → a separate §Preliminary owns formalization. §M0 may stay narrative-style but MUST still end with the pipeline-figure-anchored method-flow overview.
- External-discipline analogy (brief Part 6.2 + global facts): **complex networks — hierarchical multilayer network** (raw evidence at bottom, higher layers operate-on-top). Thought-core word (italic): *stratified* / *operate-on-top*. Authoritative ref placeholder: Boccaletti et al. 2014 (multilayer networks); Fowler *Refactoring*. [待补准确文献项 — emit \citep TODO if not in bundle].
- ORAL reframe: **AgentFlow** (modular naming, multi-component coordination).
- Big aspiration word: **self-evolving agents**.

## METHOD-FIRST constraints (from task)
- Intro does NOT exist yet. §M0: state analogy in ONE recall sentence; do NOT re-describe problem/paradigm-conflict at length; lead with method-specific content. End §M0 with pipeline-anchored method-flow overview.
- §M2/§M3 per-component motivation REQUIRED at implementation/mechanism level (do NOT hollow out) — G16/G17.
- Asset gate WAIVED: may \Cref{fig:framework} though figures/framework.pdf does not exist on disk yet (intentional). Same for fig:routing, alg:ops.
- Numbers: few/none in Method. Only numbers from global facts, tagged [SIM] or [REAL] as marked there.

## Components to cover (global facts §Components)
1. **Skill Strata** three-layer graph: trace (execution evidence + sub-capability co-occurrence) / capability (modular skills + depends_on/composes_with/conflicts_with) / governance (split/merge/retire/route rules + checkpoint guards).
2. **Curate** (offline, no-grad/no-RL): 7 operators INSERT/UPDATE/SPLIT/MERGE/LINK/RETIRE + propose-then-verify held-out gate (validation_gate) + heat lifecycle $H(v)=\alpha N_{\text{visit}}+\beta\,\text{coverage}+\gamma e^{-\Delta/\tau}$.
3. **Test-time LEGO assembly**: in-domain ROUTE minimal executable subgraph $\mathcal{S}^\star=\text{closure}_{\text{depends\_on}}(\text{seed}_k(t))\setminus\text{blocked}(\mathcal{G}_{\text{gov}})$; out-of-domain TTA synthesis $\mathcal{S}^\star \leftarrow \mathcal{S}^\star \cup \text{synth}(\text{cooc}(\mathcal{S}^\star)\setminus\text{deployed})$.
4. **Governance sub-mechanism — node-local verify-loop**: checkpoint guards on error-prone nodes (mined from trace failure stats: low heat.success_rate, trials≥k); execute→verify(sub-goal)→rollback→retry within budget. Train/inference symmetry: governance gates the library at train time (validation_gate) AND execution at inference (verify-loop).

## Heat / scoring formulas available (brief 6.4)
- should_split(v) = body large ∧ task_types heterogeneous.
- heat H(v)=α·N_visit + β·coverage + γ·e^{-Δ/τ} (from MemoryOS).
- verify gate: accept iff success non-decreasing ∧ token/negative-transfer decreasing.
- closure(S) = union of transitive depends_on.

## Numbers usable in Method (sparingly, tagged)
- [REAL] propose-then-verify gate working: S0 blank 42.5% → round0 distilled 32.5% (−10pp) → gate REJECTS, 12 skills retired → round1 47.5% (+5pp) → gate ACCEPTS, 12 deployed.
- [SIM] SPLIT and ROUTE largest contributors (−0.15 / −0.18 success when removed; removing SPLIT inflates tokens ~6.6×). governance/validation = complementary safety net.
- [SIM] TTA recovers ~54% of coverage gap.
- Trainable params: 0 (pure symbolic governance). Inference overhead: BM25 seed + dependency-closure BFS, O(|S^star|).
