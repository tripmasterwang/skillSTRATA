# Context Bundle — Introduction (paper-intro skill)

> Generated 2026-06-27. Source of truth: PAPER_BRIEF_FILLED.md Part 3 (intro plan) / 0.2 / 0.3 (paradigm) / 2 (abstract data),
> _global_facts.md, and prior drafts {01_method, 02_experiment, 03_preliminary, 04_related-work, 05_conclusion}.md.
> FINAL_PLAYBOOK §3 = 6 paragraphs, ~22–28 sentences, ~500–700 words.
> Reframe 招式 (locked, _global_facts.md): **AgentFlow** (modular naming, multi-component coordination).

## Three decisions (locked)
1. **段1 风格**: **A. trend-dump** — LLM agents self-evolving skills from execution traces, 5–7 ref dump.
2. **段3 RQ 实现方式**: **A. obsbox 黄底框** (brief 3.3 explicitly says "用 obsbox").
3. **段5 句1.3/1.4/1.5 (排除相邻子领域 / scope 锁 / 热模型点名)**: 段1 内弱化 1.3/1.4 (scope clear from title+1.1); KEEP 句1.1b external-discipline anchor (HARD, analogy used in §M0/conclusion).

## External-discipline anchor (★ CANONICAL HERE — 段1.1b / recalled 段3.5)
- Discipline (spell out): **complex networks** — *hierarchical multilayer network* (raw evidence at the bottom, higher layers *operate on top*).
- Authoritative cite: `\citep{boccaletti2014multilayer}` (SAME cite-key §M0 uses — line 12 of 01_method.md).
- italic thought-core words: *stratified* / *operate on top* (reused in §M0/§M1/conclusion).
- 段1 MUST name "complex networks" + cite boccaletti2014multilayer; §M0 only recalls it.

## 15 facts
1. **Big trend / domain**: LLM agents that self-evolve skills from execution traces (self-evolving / lifelong agents).
2. **段1 ref dump (≥5–7, real keys)**: `trace2skill`, `skillopt`, `skillbrew`, `evoskill`, `gmemory`, `memoryos`, `skillos_ouyang`.
3. **Core concept (段1.2)**: the agent's **skill library** distilled from traces (trace-to-skill evolution).
4. **Hot models (段1.5 optional)**: Qwen3.x (Trace2Skill backbone), GPT/Claude agent stacks — keep light, optional.
4b. **段2 引子 / 路线转向动机 (brief 3.2, NON-`[无]` → 句2.0 REQUIRED)**: trace→skill defaults to "bigger/more-merged skill = stronger"; holds short-term, but at long horizon → monolithic-document bloat + local-rule pollution; so the shift is "from making a bigger document to GOVERNING modular skills". Barrier Z = **skill bloat + negative transfer + no dependency/governance structure**.
5. **Paradigm I (段2.2/2.3)**: **(I) monolithic skill** — Trace2Skill / SkillBrew / SkillOpt; refs `trace2skill, skillbrew, skillopt`. Flaw: **skill bloat / full-load / negative transfer**.
6. **Paradigm II (段2.4/2.5)**: **(II) flat skill bank** (top-k retrieval); refs flat-bank / single-layer skill-graph `skillgraph_rl, gos`. Flaw: **no dependency closure / no governance → mis-routing**.
7. **共同缺陷 命名 (段2.6)**: **Skill Bloat vs. Skill Governance** (升格 §Background subsection per brief 0.6). Named concept = *ungoverned skill accumulation*.
8. **第三方向 (段3.1)**: stratified, governed skill graph + OS-style lifecycle; reps `gmemory` (graph memory), `memoryos` (OS lifecycle).
9. **第三方向自身缺陷 (段3.3, 2–3 dims)**: (i) they govern **memory not skills** (raw-task-string nodes, no stable skill IDs / no SPLIT); (ii) no **dependency-aware routing** of a minimal executable subgraph; — both diverge from a governable, composable, routable **skill** graph.
10. **RQ 反问 (段3.6, ≤30 词, obsbox)**: *Should skill evolution end in ever-larger documents, or in a governable, composable, routable skill graph?*
11. **外部学科类比 (段3.5 recall of 段1.1b)**: complex networks — hierarchical multilayer network; `\citep{boccaletti2014multilayer}`. (introduced 段1, recalled 段3.)
12. **Method 名 + 组件 (段4, AgentFlow verb-role naming)**: **SkillStrata** = **organize** (three-layer Skill Strata) → **govern** (SPLIT/MERGE/LINK/RETIRE + propose-then-verify gate) → **route** (minimal executable subgraph) + test-time **assemble** (LEGO: in-domain ROUTE, out-of-domain synthesis). Type word = **system**.
13. **段5 数字 — ★ RESPECT PROVENANCE (global_facts §42–53)**:
    - 句5.1 scale: [REAL] SpreadsheetBench verified-400 (qwen3.6-35b-a3b, SkillOpt 80/40/280 split) + [SIM] deterministic harness (8 seeds, 400-task stream, 4 domains).
    - 句5.2 hot baseline: [REAL] SkillOpt target — No-Skill **38.2 → SkillOpt 47.5 (+9.3)**; Trace2Skill **33.2 (−5.0 negative transfer)**. [SIM] vs Trace2Skill success **0.704 vs 0.574 (+13pp)**, tokens **365 vs 780 (≈2.1× fewer)**.
    - 句5.3/5.4 win: [SIM] highest success + lowest tokens; routing precision 0.391 (≈6× monolith).
    - 句5.4 gate (REAL ★): from-zero curate val **42.5 → reject 32.5 (−10pp, 12 skills retired) → accept 47.5 (+5pp)**; harmful batch rejected, beneficial accepted.
    - 句5.6 意外发现 (反直觉, [SIM]): ablation — **SPLIT and ROUTE are the dominant contributors** (−0.18/−0.15 success; removing SPLIT inflates tokens ~6.6×); governance/validation = complementary safety net. "gains come from splitting+routing, not amassing more skills."
    - **280-test head-to-head = [PENDING]** — DO NOT fabricate. Name it as in-progress.
14. **段6 Contributions (3 core, brief 3.6, semantic order task→method→effect)**:
    - ① [任务/系统级] We introduce the **stratified-skill-system problem** + **SkillStrata**: lift trace→skill's product from "one skill / single-layer graph" to a curated three-layer Skill Strata system, subsuming single-layer skill-graph methods as a special case.
    - ② [方法级] We propose **curate** (SPLIT/ROUTE + propose-then-verify gate) + test-time **LEGO assembly** (in-domain routing, out-of-domain synthesis) + **node-local verify-loop**, no RL.
    - ③ [效果] We show: [REAL] the validation gate autonomously rejects a harmful batch and accepts a beneficial one; [SIM] highest success + lowest tokens + recovers OOD coverage; the real-benchmark 280-test head-to-head is in progress.
    - (NO release 4th item — 全篇 3 条; brief lists it as optional, keep core 3.)
15. **Framework figure (段4/段5 teaser)**: `\Cref{fig:framework}` — asset PENDING, gate WAIVED (env deferred). ref_home = method §M0 owns the figure float; intro MAY \Cref it as a forward teaser. Path `figures/framework.pdf`.

## 大终点词 (echo abstract句1 ↔ intro段1.1/段5/段6 ↔ conclusion句4)
- **self-evolving agents** (exact phrase — locked, do NOT swap).

## Inter-paragraph consistency (must hold)
- 段2 (I)(II) roman → 段4 callback "Unlike (I) monolithic merge and (II) flat top-k retrieval, ours splits monoliths into a governed graph and routes a minimal executable subgraph" (brief 3.4 verbatim direction).
- 段2 共同缺陷 "Skill Bloat / ungoverned accumulation" → 段4 "inherently mitigates skill bloat (I) / moves beyond ungoverned mis-routing (II)".
- 段3 concept words (skill graph / minimal executable subgraph / lifecycle) → 段4 components organize/govern/route echo them.
- 段1.1b complex-networks anchor → 段3.5 recall (shorthand) → §M0 only recalls (no new discipline).
- 段5.2 hot baseline SkillOpt → §Experiments §E2 [REAL] target (already in 02_experiment.md).
- 段6 ③ effect contrib ↔ §E2 main results.

## Forbidden words: novel / impressive / remarkable / SOTA / promising (except "promising path/direction")

## Cite-keys available (from prior drafts, real): trace2skill, skillopt, skillbrew, evoskill, skillos_ouyang, gmemory, memoryos, memos, skillgraph_rl, gos, skillgraph_toolseq, boccaletti2014multilayer, qwen36
