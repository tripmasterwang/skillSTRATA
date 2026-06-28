# §Method — Per-Sentence Justification (paper-method Phase 4)

Draft: `drafts/01_method.md`. Method name = **SkillStrata**; three-layer system = **Skill Strata** (trace/capability/governance). Method-first pass (Intro not yet drafted). All three core components are brief-Part-6.4 type ④ **hard_rule** → single `\paragraph{}` + exactly 1 scoring/decision equation, NO training loss. A separate §Preliminary owns full formalization, so §M0 stays narrative + flow overview.

## Sentence-by-sentence table

| 节 | 句 | 内容 (前 ~8 词) | 模板规则 | 风格选择 |
|---|---|---|---|---|
| M0 | 0.1 | "Just as a hierarchical multilayer network places…" | 句 M0.1 method-first first-appearance analogy (ONE sentence, ≤32w) + external-discipline `\citep` | complex-networks framing; *stratified* / *operate-on-top* italic thought-core; method name bold first appearance |
| M0 | 0.2 | "This separates three concerns that single-layer…" | 句 M0.2 structural-mismatch echo of prior paradigm (no perf language) | trace/capability/governance separation; emph triad |
| M0 | flow | "The framework runs in two phases over…" | §M0 OVERVIEW CONTENT RULE element 3 (pipeline-figure-anchored method-flow overview) + G4d | names $\mathcal{G}$ + $\mathcal{S}^\star$ on the arrows; frozen boundary stated; `\Cref{fig:framework}` (asset gate waived, % TODO tag) |
| M1 | 1.1 | "As shown in \Cref{fig:framework}, skill evolution…" | 句 M1.1 mandatory "As shown in \Cref{fig:framework}" opener + "unfolds + adverb" + frozen/trained | descriptive subsection; *unfolds hierarchically*; **frozen**/**stratified** bold |
| M1 | 1.2 | "For each solved task, the curate loop distills…" | 句 M1.2 core action + I/O ($\mathcal{G}_{\text{trace}}$) | narrative verb **distills**; trace layer = evidence + co-occurrence |
| M1 | 1.3 | "The middle capability layer organizes these…" | 句 M1.3 component action w/ concrete verb, colon → Eq | **organizes**; edge types `depends_on/composes_with/conflicts_with`; status set |
| M1 | eq:node | status($v$) ∈ {candidate,…,retired} | 公式 M1.1 anchor (node-state); `\label` | Preliminary main-variable symbol reused verbatim |
| M1 | 1.4 | "The top governance layer operates on top…" | 句 M1.4 if-then / colon → 2nd anchor Eq | **operates on top** (analogy callback); checkpoint guards named |
| M1 | eq:route | $\mathcal{S}^\star=\text{closure}\setminus\text{blocked}$ | 公式 M1.2 anchor (routing decision) + `\underbrace` semantic labels | minimal executable subgraph = Preliminary 5.4 def verbatim |
| M1 | 1.4b | "where $\text{seed}_k(t)$ are the top-$k$…" | G14 "where X is Y" gloss | BM25 seed = same retriever as flat baseline (isolates graph contribution) |
| M1 | 1.5 | "This stratification elevates the library…" | 句 M1.5 "elevates X from Y to Z" + "without altering [frozen]" | **elevates** flat bag → **governed, routable graph**; double-win frozen close |
| M2 | 2.0 | "The curator acts as a librarian over…" | 句 M2.x.0 narrative-role 定调 + 7-operator roster | **curator/librarian** role; *no gradient / no RL* nailed |
| M2 | 2.A (Split) | "The signature operator is Split: a distilled…" | type-④ hard_rule single `\paragraph` + impl-layer motivation (G16: WHY split = full-load + negative transfer) | **refactored**; mechanism token = should_split predicate |
| M2 | eq:split | $\textsc{Split}(v)$ fires ⟺ oversized ∧ heterogeneous | 公式 (hard_rule decision, exactly 1) + `\underbrace` labels | deterministic predicate read off $\mathcal{G}_{\text{trace}}$ |
| M2 | 2.A.gloss | "where $|\text{body}(v)|$ is the skill's token…" | G14 gloss; Merge/Link/Retire + heat $H(v)$ formula | heat $H(v)=\alpha N+\beta\text{cov}+\gamma e^{-\Delta/\tau}$ (MemoryOS-adapted) |
| M2 | 2.B (gate) | "Because a distilled batch can actively harm…" | type-④ hard_rule `\paragraph` + impl-layer motivation (G16: WHY gate = harm evidence) | [REAL] 42.5→32.5 harm number as motivation |
| M2 | eq:gate | promote(ΔG) ⟺ succ∧tok∧nt non-worse | 公式 (gate decision) + 3 `\underbrace` labels | propose-then-verify; held-out replay |
| M2 | 2.B.close | "In that run the gate rejected the harmful…" | G16 outcome / self-correction | [REAL] reject-12 / accept→47.5; "no gradient signal" |
| M3 | 3.0 | "At test time the router assembles a task-fit…" | 句 M2.x.0 narrative-role 定调 (router) + LEGO metaphor | **router**; **routes** / **casts**; assembly metaphor |
| M3 | 3.A (route) | "For an in-domain task, routing returns the…" | type-④ hard_rule `\paragraph` + impl motivation (G16: WHY closure>top-k = silent prereqs) | subsumes single-layer methods as in-domain half; **pull in** prereqs |
| M3 | 3.B (TTA) | "When the seeds need a sub-capability with no…" | type-④ hard_rule `\paragraph` + 1 decision Eq + impl motivation | **drills down** / **synthesizes**; non-oracle trigger; trace layer participates |
| M3 | eq:tta | $\mathcal{S}^\star\leftarrow\mathcal{S}^\star\cup\text{synth}(\text{cooc}\setminus\text{deployed})$ | 公式 (TTA decision) + `\underbrace` | [SIM] ~54% coverage-gap recovery as effect |
| M3 | 3.C (verify) | "Governance also guards execution, not only…" | type-④ hard_rule `\paragraph` + 1 decision Eq + impl motivation (node-local repair) | guards mined from trace (low success_rate, trials≥k); **repaired locally** |
| M3 | eq:verify | retry($v$) ⟺ ¬verify(g_v) ∧ budget | 公式 (verify-loop decision) + 2 `\underbrace` | sub-goal (not final answer) catches [REAL] tautology self-check |
| M3 | 3.C.close | "Governance thus shows a train/inference…" | G16 symmetry payoff sentence | **train/inference symmetry**: eq:gate (train) ↔ eq:verify (inference) |
| M4 | 4.1 | "SkillStrata introduces zero trainable…" | 句 M3.1 params statement (zero on frozen backbone) | "only X on top of Y" win; 0 params |
| M4 | 4.2 | "At inference, routing costs a BM25 seed…" | 句 M3.2 inference overhead + 句 M3.3 big-O | $O(|\mathcal{S}^\star|)$, same order as flat top-k |
| M4 | 4.3 | "Integration is drop-in: SkillStrata replaces…" | §M4 Trace2Skill integration (brief 6.6) | replaces only monolithic merge; ReAct executor untouched; `\Cref{alg:ops}` |
| Alg | alg:ops | curate (absorb) + route loop | Algorithm box R22 (5–12 lines, vars = eqs, inference+offline) | `\tcp*` ties each line to Eq.~ref; matches eq:split/gate/route/tta/verify |
| Fig | fig:framework | Overview caption (5–8 lines) | Framework figure caption R18 (left→right flow, frozen gray / curated colored, vars on arrows, differentiation close) | asset PENDING, gate waived; `% TODO` + commented `\includegraphics` |

## G16 per-component impl-layer-motivation check (反掏空两件套)

| Component | ① concrete mechanism token | ② implementation-layer motivation ("具体这样做,是因为…") | pass |
|---|---|---|---|
| Skill Strata graph (§M1) | $\mathcal{G}_{\text{trace/cap/gov}}$, edge types, status set, eq:node, eq:route closure | "separates where-from / what / whether-to-use that single-layer stores collapse"; closure makes activation dependency-complete | ✓ |
| Split / refactor (§M2) | should_split predicate eq:split ($\tau_b,\tau_h$, entropy $\mathcal{H}_{\text{type}}$ off trace) | "because a monolithic body forces full-load injection and invites negative transfer when only one behavior is relevant" | ✓ |
| Heat / Retire (§M2) | $H(v)=\alpha N+\beta\text{cov}+\gamma e^{-\Delta/\tau}$ | "so visitation, coverage, and recency jointly decide what fades" | ✓ |
| Propose-then-verify gate (§M2) | eq:gate (succ∧tok∧nt), held-out replay, rollback | "because a distilled batch can actively harm unseen tasks" + [REAL] 42.5→32.5 | ✓ |
| In-domain ROUTE (§M3) | closure minus blocked, depends_on edges | "because a relevant seed silently depends on prerequisites that flat retrieval omits" | ✓ |
| TTA synthesis (§M3) | eq:tta synth(cooc∖deployed), historical-only trigger | "non-oracle; lets the otherwise-offline trace layer participate at inference" | ✓ |
| Node-local verify-loop (§M3) | eq:verify (sub-goal $g_v$, budget $B_v$), guards mined low success_rate∧trials≥k | "repaired locally rather than restarting the whole task"; sub-goal (not final answer) catches false-confidence self-check | ✓ |

## G17 Intro-differentiation check
Each §M2/§M3 concept sentence carries ≥1 mechanism token absent from any (future) Intro abstract framing: predicate thresholds $\tau_b/\tau_h$ + entropy (Split), three-clause gate inequality (gate), dependency-closure-minus-blocked (route), cooc∖deployed synth op (TTA), sub-goal/budget retry inequality (verify-loop). Method-first: Intro does not yet exist, so C7a (§M0↔Intro lexical+paraphrase) is deferred to orchestrator Phase 9; §M0 written thin (analogy = ONE recall sentence, no paradigm-conflict re-description) to pass it.

## Checklist results
- M0–M4 body prose word count: **~1104** / target band [600, 900] → **SOFT-FAIL (over)**. Cause: brief Part 6.0 declares **5** author-declared subsections (G7a overrides default-4 budget) and G16 mandates a motivated `\paragraph` per operator/mechanism (8 blocks). Two compression passes already applied; further cuts would delete mechanism tokens / motivation clauses and fail G16/G17 (also HARD). Documented tension G1 ↔ G7a+G16; chose to honor G16/G17 (content integrity) over the length band. Algorithm + caption excluded from this count.
- Subsections: **5** / author-declared 5 (G7a) [✓]
- Equations: **6** (eq:node, eq:route, eq:split, eq:gate, eq:tta, eq:verify) — within method range; all `\label`ed [✓]
- `\underbrace{}_{\text{语义}}` tags: **10** across 4 equations [✓ G10]
- Narrative / human-ish verbs: stratifies, assembles, operates-on-top, distills, organizes, elevates, refactored, consolidates, wires, evicts, fades, proposed, promoted, routes, casts, drills down, synthesizes, pull in, repaired, guards, gates, unfolds — well over 20% verb density [✓ G12]
- Component naming = narrative roles (curator/librarian, router) [✓ G8]
- Algorithm box: 1, 12 content lines, vars match eqs, `\tcp*` cross-refs [✓ G9]
- frozen vs trained explicit (backbone + ReAct executor frozen; governance symbolic, 0 params) [✓ §C-3]
- Numbers: only [REAL] (42.5/32.5/47.5/12-skills; tautology self-check) and [SIM] (~54% coverage gap) from global facts, tagged inline [✓]
- Hard-fail count: **0 content hard-fails**; **1 soft band overrun (G1)** documented above.

## G1–G15 hard-gate disposition
- G1 (word band): SOFT-FAIL over (1104 vs 900) — documented tension with G7a (5 declared subsections) + G16 (per-mechanism motivated paragraphs). Not resolvable without violating G16/G17.
- G2 (subsections + alg + fig): PASS (5 subsections + Algorithm + caption).
- G4 (§M0 narrative; purity OK since separate §Preliminary owns formalization): PASS.
- G4a (§M0 analogy `\citep` co-occurs in abstract/intro): N/A method-first — analogy first appearance here; `boccaletti2014multilayer` is a placeholder cite-key [TODO: confirm bib entry]; orchestrator Phase 9 must re-anchor in Intro. Did NOT halt (method-first carve-out).
- G4b (discipline first-named in Intro): deferred to Intro (method-first); §M0 is the legitimate first appearance, kept to ONE sentence.
- G4c (method-first thinness, §M0 ≤1 analogy sentence + no paradigm-conflict): PASS.
- G4d (§M0 ends with pipeline-figure-anchored flow overview): PASS (the "framework runs in two phases…" sentence).
- G5 (§M1 "As shown in \Cref{fig:framework}" opener): PASS.
- G6 (framework figure left→right + frozen/colored): caption authored to spec; figure asset PENDING (gate waived).
- G7 (component_type ④ hard_rule dispatch: single paragraph + 1 decision Eq, no loss): PASS — no training-loss equations anywhere; each mechanism = 1 scoring/decision Eq.
- G7a (subsection count/titles/style match brief 6.0): PASS (5 titles verbatim from Part 6.0; M2/M3/M0 claim-title, M1/M4 descriptive).
- G7b (Part 6.0.bis anchors): N/A — brief has no 6.0.bis anchor registry.
- G8/G9/G10/G11/G12/G13/G14: PASS (see checklist).
- G15 (2–3 pages): the 1104-word body + 6 eqs + algorithm + full-width figure likely runs ~3 pages double-column — at/above the upper bound, consistent with the G1 overrun note.
- G16/G17: PASS (tables above).

## Deviations from the brief
1. **Length over band.** Honored brief Part 6.0's 5-subsection declaration and Part 6.4's per-mechanism hard_rule structure; this pushes the body to ~1104 words, above the skill's 600–900 band. Deliberate: G16/G17 (content) outrank the soft band. Flagged for the orchestrator — if a hard 2.5-page limit is needed, the cut should drop §M0 sentence 0.2 and merge §M4's three sentences, NOT thin §M2/§M3 mechanisms.
2. **Citation placeholder.** `\citep{boccaletti2014multilayer}` for the multilayer-network analogy is a placeholder (brief Part 6.2 marks the exact ref "[待补准确文献项]"). Must be resolved before citation-audit; Fowler *Refactoring* (SPLIT analogy) not cited inline to keep §M0 to one analogy sentence.
3. **Asset references kept despite missing files.** `\Cref{fig:framework}`, `\Cref{fig:routing}` (folded into the framework caption rather than a second figure, since §M3 had no separate routing figure authored here), `\Cref{alg:ops}` — `_asset_inventory.json` absent, so each carries a `% TODO: add Part 12 row` comment per asset-rule item 4. Asset gate explicitly waived by the task. Note: brief 6.0 lists fig:routing for §M3; I did not emit a separate `\Cref{fig:routing}` to avoid an unused dangling ref — the routing visual is described in the framework caption. Orchestrator may add fig:routing if a dedicated routing panel is drawn.
4. **No §Preliminary symbols re-derived.** Per inter-subsection dependency map, $\mathcal{G}$, $\mathcal{S}^\star$, status($v$) are used verbatim assuming §Preliminary defines them; eq:node/eq:route restate them as anchors only.
