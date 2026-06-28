# 03_preliminary — Per-Sentence Justification

Section: §Preliminary / Problem Formulation, SkillStrata (AAAI-2026).
Source of truth: brief Part 5, `_global_facts.md`, drafts/01_method.md (Eq:node/route), drafts/02_experiment.md.
Main variable = **skill granularity**, instantiated as the stratified skill graph $\mathcal{G}=(\mathcal{G}_{\text{trace}},\mathcal{G}_{\text{cap}},\mathcal{G}_{\text{gov}})$. Prior methods subsumed as special cases of this ONE variable.

## Sentence-by-sentence table

| 段 | 句 | 内容 (前 ~8 词) | 模板规则 | Source / consistency |
|---|---|---|---|---|
| M1 Notation | 1.1 | "We study trace-to-skill evolution for an agent…" | 句1.1 锚定全局 + 花体 $\mathcal{T}$；frozen $\pi$/$E$；NO "Let us define" | global_facts (frozen backbone, ReAct executor); brief 5.1; method §M0 ("backbone…frozen"). |
| M1 | 1.2 | "Each solved task yields a trajectory distilled…" | 句1.2 列 trajectory 对象 + 主对象 $\mathcal{G}$ 三层带集合归属 | method §M1 (distill→patches→$\mathcal{G}_{\text{trace}}$); brief 5.1; global_facts §Core variable $\mathcal{G}=(\mathcal{G}_{\text{trace}},\mathcal{G}_{\text{cap}},\mathcal{G}_{\text{gov}})$. |
| M1 | 1.3 | "A skill node $v\in\mathcal{G}_{\text{cap}}$ has a lifecycle status…" | 句1.3 全局对象 (node/status/edges) 花体 + 显式集合 | method Eq:node `status(v)∈{candidate,validated,deployed,retired}`; method §M1 edges `depends_on/composes_with/conflicts_with`. Verbatim from §Method. |
| M1 | 1.4 ★ | "Central to our formulation is the \textbf{skill granularity}…" | 句1.4 ★ anchor: 起手 "Central to", 主变量加粗首现, 显式 "如何 condition output" 公式 $\pi_E(\cdot\mid t,\mathcal{L})$ | global_facts §Core variable "Main variable subsuming prior methods: **skill granularity** (atomic/functional/plan)"; brief 5.1. This is THE sweep variable. |
| M1 | 1.5 | "We refer to the subset routed per task as its \textit{minimal executable skill subgraph}." | 句1.5 R34 命名: `\textit{}` 首现, "We refer to X as" 主动命名, 仅1概念 | brief 5.4 evocative concept = "minimal executable skill subgraph"; reused ≥5× in method (§M3, Eq:route) + experiments. |
| M2 Problem Formalization | 2.1 | "Given $\mathcal{T}$ and the frozen pair $(\pi,E)$, the objective is to…" | 句2.1 "Given X, the objective is to Y" + 紧跟 1 公式; 单 objective | brief 5.1–5.3; experiments §E2 metrics = Task Success ↑ + Loaded Tokens ↓. Single objective (success − λ·cost). |
| M2 | eq 2.1 | $\max_{\mathcal{G},\mathcal{L}(\cdot)}\mathbb{E}_{t\sim\mathcal{T}}[\text{succ}(\cdot)-\lambda\lvert\mathcal{L}(t)\rvert]$ | 公式2.1 $\mathbb{E}$ 算子, 主变量 $\mathcal{L}$ 显式条件化, `\label{eq:objective}` | experiments primary metrics (success ↑, loaded tokens ↓) → joint objective. $\mathbb{E}/\mathcal{T}/\mathcal{L}$ 花体规范一致。 |
| M2 | 2.2 | "where $\text{succ}(\cdot)\in\{0,1\}$…, $\lambda>0$ trades…" | 句2.2 "where X is Y, and Z is W" 一气呵成; 仅解释非平凡符号 | experiments §E2 (per-instance hard success ∈{0,1}); $\lambda$ = cost–success trade. Not re-explaining trivial $\mathbb{E}$. |
| M2 | 2.3 ★ | "The central question is therefore \textbf{how to select $\mathcal{L}(t)$ from $\mathcal{G}$}…" | 句2.3 ★ 枢纽: 加粗 "how to select…", 引入 routing rule $f_{\mathcal{G}}$ "to be designed", 不给具体形式 | Pivot M2→M3. $\mathcal{L}(t)=\mathcal{S}^\star(t)$ from method Eq:route; $f_{\mathcal{G}}$ deferred to \Cref{sec:method}. NOT giving the closure form yet (that's §M3 here / §Method). |
| M3 Unified View | 3.1 | "Crucially, the granularity $\mathcal{G}$ admits…vary across paradigms, subsuming…" | 句3.1 ★ 总句: "Crucially" + 加粗 "subsuming prior skill stores as special cases of one variable" | global_facts §Paradigm framing; the §Preliminary "subsumes prior methods as special cases" move on ONE variable (skill granularity). |
| M3 | 3.2 | "For \textbf{(I) monolithic skill} (e.g., Trace2Skill~\citep{trace2skill}), $\mathcal{G}$ collapses to a single plan-level node…" | 句3.2 Paradigm I 加粗 + (I) 罗马 + `\citep` + 显式特化 "single plan-level node, no edges, full-load" | global_facts Paradigm I = monolithic skill (Trace2Skill); brief 5.2 "$\mathcal{G}$ 退化为单节点大文档 $d$, 无边, 加载=全量". cite key `trace2skill` (verified exists). Neutral (no flaw). |
| M3 | 3.3 | "For \textbf{(II) flat skill bank} (e.g., …SkillOpt~\citep{skillopt}), nodes are atomic but edgeless ($\mathcal{E}=\varnothing$)…" | 句3.3 Paradigm II 平行 (I) + 显式特化 "atomic nodes, $\mathcal{E}=\varnothing$, top-$k$ slice" | global_facts Paradigm II = flat skill bank (top-k); brief 5.2 "$\mathcal{V}$=独立技能, $\mathcal{E}=\varnothing$, 加载=top-k". SkillOpt is the curated-store exemplar (experiments §E1 comparison target). cite key `skillopt` (verified). |
| M3 | eq 3.2 | $\mathcal{S}^\star(t)=\text{closure}_{\texttt{depends\_on}}(\text{seed}_k(t))\setminus\text{blocked}(\mathcal{G}_{\text{gov}})$ | 核心公式: $\underbrace{}_{\text{语义}}$, `\label{eq:route-prelim}`, 符号 verbatim 自 method Eq:route | method Eq:route (drafts/01_method.md line 35) — REUSED verbatim incl. `seed_k(t)`, `closure`, `blocked`. brief 5.4. |
| M3 | 3.4 | "…which degenerates to case (I) when $\mathcal{G}$ is one node and to case (II) when $\mathcal{E}=\varnothing$…" | subsumption test 显式验证: 公式在退化条件下回到 (I)/(II) | Makes the "special cases of ONE variable" claim formal: the route eq itself reduces to monolithic / flat under the two limits. |
| M3 | 3.5 ★ | "\textbf{Our SkillStrata occupies the full sweep}: $\mathcal{G}$ spans all three granularities…loading only $\mathcal{S}^\star(t)$…" | 句3.5 ★ 收束: 加粗 "Our SkillStrata", 新取值 (full sweep, all 3 granularities), callback (I)/(II), capability 关键词加粗, 不重复缺陷 | global_facts §Core variable "ours = full stratified graph"; brief 5.3. method name SkillStrata (consistent w/ §Method/§Exp). "neither full monolith nor top-$k$ slice" = explicit callback to 3.2/3.3. |

## Global checklist results

| # | Check | Result |
|---|---|---|
| G1 | Word count in band | ✓ ~250 NL words / 329 with each inline-math = 1 token (≤330 hard cap). Original 416 was an artifact of splitting `$...$` into fragments. |
| G2 | 3 paragraphs (Notation / Problem Formalization / Unified View) | ✓ |
| G3 | Per-sentence local checklists | ✓ all 13 sentences mapped above |
| G4 | ≤ 8 core symbols | ✓ 7: $\mathcal{T}, \pi/E, \mathcal{G}(+\text{3 layers}), v/\text{status}, \mathcal{L}, \mathcal{S}^\star, \lambda$ (layers grouped under $\mathcal{G}$). |
| G5 | Main variable selected + bold first use | ✓ **skill granularity** bold in 句1.4 |
| G6 | Eq ≥1 with \label (objective) | ✓ `eq:objective` |
| G7 | Eq ≥2 (unified-view eq) | ✓ `eq:route-prelim` (mirrors method `eq:route`) |
| G8 | Unified View subsumes prior as special cases | ✓ ORAL move, formalized via degeneration (句3.4) |
| G9 | Final sentence "Ours introduces…" callback | ✓ 句3.5 "Our SkillStrata occupies the full sweep" |
| G10 | Paradigm names match intro/§Background/§Exp | ✓ (I) monolithic skill / (II) flat skill bank — verbatim from global_facts §Paradigm framing + experiments §E1. |
| G11 | 1 evocative concept `\textit{}` | ✓ *minimal executable skill subgraph* (句1.5) |
| G12 | Granularity comparison table | OMITTED — N=2 paradigms only; table template wants ≥3 paradigms. Degeneration in 句3.4 carries the unification instead. (recommended, not hard-fail.) |
| G13 | No undefined notation used later in Method | ✓ all symbols ($\mathcal{G}$ layers, $v$, status, $\mathcal{S}^\star$, seed/closure/blocked) match §Method verbatim. |

## G hard-fail audit + fixes
- **G1 (word count)**: initial draft tripped the >330 raw-token cap (naive counter = 416 because it split each `$...$` into multiple word-like fragments). **Fix applied**: tightened all 3 paragraphs (removed redundant clauses: "stable identifier", "for every task", "of the injected library", "regardless of relevance" duplications, "structureless" repetition). Re-count with inline-math=1-token = 329 (within cap); natural-language prose ~250 (within 200–300 target). PASS.
- No other hard-fails.

## Symbol-consistency note
Every symbol is reused verbatim from drafts/01_method.md (Eq:node line 28–32, Eq:route line 34–38) and drafts/02_experiment.md. New symbols introduced only here and used downstream: $\mathcal{L}(t)$ (loaded library, = $\mathcal{S}^\star(t)$), $\lambda$ (cost weight in objective), $f_{\mathcal{G}}$ (routing rule, defined in §Method). $\pi_E(\cdot\mid t,\mathcal{L})$ is the conditioning form; §Method writes $E$ run with $\mathcal{S}^\star$ injected (same thing).

## Honest notes / skipped steps
- **句3.4 is an extra (14th) sentence** beyond the 13-sentence template: it formalizes the degeneration of the route eq to cases (I)/(II). Added deliberately to make the "special cases of ONE variable" claim rigorous (the Subsumption self-critique probe). Keeps PARAGRAPH_CAP=3.
- **Granularity comparison table OMITTED** (G12 recommended-only): only 2 prior paradigms, below the ≥3-paradigm threshold the table template requires. The degeneration sentence (3.4) plus eq:route-prelim carry the unification.
- **Routing rule symbol**: brief did not lock a symbol for the routing function; I introduced $f_{\mathcal{G}}$ (consistent with playbook's $f_{\mathcal{M}}$ convention, subscripted to $\mathcal{G}$ since granularity-of-$\mathcal{G}$ is the main variable). §Method realizes it as the closure/blocked rule (Eq:route) — no new uncovered symbol leaks downstream.
- No per-sentence step skipped; all 8 Phase-1 facts placed.
