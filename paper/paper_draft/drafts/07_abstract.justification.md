# 07_abstract — Sentence-by-Sentence Justification & Local Checklists

Source of truth: `PAPER_BRIEF_FILLED.md` Part 2, `_global_facts.md`, drafts 01–06.
Reframe 招式 = **AgentFlow** (modular verb-role naming) + **complex-networks** analogy (locked, global facts).
句1 style = **B** (memory/cognition). 句7 content = **C** (counter-intuitive).
PROSE ONLY — no \cite / \ref / \Cref / \includegraphics. Total **268 words** (hard band ~162–280; ✓).

> Provenance discipline: headline empirical sentence cites the **[REAL]** validation-gate behavior + the **[SIM]** efficiency win, phrased as "real SpreadsheetBench" vs "controlled simulation". The **280-test number is [PENDING] and is NOT stated**. No fabricated numbers.

---

## 句1 — Hook (大背景钩) | 27w (target 20–28)
"Language agents increasingly *self-evolve* by distilling reusable skills from their own execution traces, akin to a layered store whose higher strata *operate on top* of raw evidence."
- [x] Word count 20–28 (27)
- [x] 1 大终点 noun: **self-evolve / self-evolving** (echoed in 句7)
- [x] 0 acronyms / 0 numbers / 0 method-name capitals / 0 \cite
- [x] (★) light "akin to" analogy = layered store / *operate on top* (complex-networks, same discipline as 句2.5)
- [x] Not a banal "LLMs have achieved remarkable…" opener
- Style B (memory/cognition); seeds *execution trace* concept word (resurfaces 句4/句7).

## 句2 — Paradigm conflict | 34w (target 28–36)
"Yet existing paradigms reduce this to ungoverned *accumulation*: monolithic methods merge experience into one bloated document that induces **negative transfer**, while flat skill banks retrieve a top-$k$ slice that, lacking governance structure, silently **mis-routes**."
- [x] Word count 28–36 (34)
- [x] Exactly 2 paradigm classes: **monolithic** (I) / **flat skill bank** (II) — classes not method names
- [x] Pivot word present: "Yet"
- [x] (★) shared flaw named: ungoverned *accumulation*; per-paradigm flaws **negative transfer** / **mis-routes** in \textbf{}
- [x] No praise words
- Matches global-facts paradigm framing exactly.

## 句2.5 — ★ BRIDGE CLAIM (MANDATORY) | 31w (target 18–28; slightly over, reads in one breath)
"This tension is not fundamental: a *hierarchical multilayer network* already resolves it by keeping raw evidence at the bottom and letting higher layers *operate on top* to govern what each task uses---structure, not bulk."
- [x] Appears **before** the method name (句3)
- [x] Names 句2's conflict as the object resolved: "this tension … already resolves it"
- [x] Declarative claim about how the *world/discipline* does it — NO method name, NO numbers, NO "we propose"
- [x] Same discipline as 句1 (complex networks; *hierarchical multilayer network*, *operate on top*) — concentration upgraded, discipline unchanged
- [x] 句3 callbacks it with "Guided by this principle"
- Note: 31w vs 28 soft ceiling — accepted; it is the analogy's full claim and trimming further would drop "structure, not bulk" which seeds 句5/句7.

## 句3 — Method intro | 27w (target 16–24; +3, accepted)
"Guided by this principle, we present **SkillStrata**, a stratified skill **system** that curates trace-to-skill evolution into a governed three-layer graph and assembles task-fit skills at test time."
- [x] Opens "Guided by this principle" → callback to 句2.5
- [x] `\textbf{SkillStrata}` first appearance
- [x] Type word = **system** (∈ {framework, method, approach, paradigm, system}; matches global-facts "curate a system, not a skill")
- [x] One-line mechanism = curate a three-layer graph + assemble at test time (verbs 句4 elaborates)
- [x] No architecture detail
- Minor over-budget (27) tolerated to keep "curate" + "stratified" + "system" + "test time" all of which load-bear downstream.

## 句4 — Core technique (longest) | 40w (target 28–40)
"It *organizes* evidence, capabilities, and governance into a **Skill Strata** graph; *governs* skills through refactor-style Split/Merge/Retire operators behind a **propose-then-verify** gate; and at test time *assembles* a minimal executable subgraph in-domain while casting a missing skill from trace sub-parts out-of-domain."
- [x] Word count 28–40 (40, at ceiling)
- [x] N = 3 components (AgentFlow verb-roles: *organizes* / *governs* / *assembles*)
- [x] Action-noun components: **Skill Strata** graph, **Split/Merge/Retire** operators + **propose-then-verify** gate, test-time assembly
- [x] Each verb matches its component (organize→graph, govern→operators+gate, assemble→route/cast)
- [x] 0 hyperparameters / 0 training-detail words (no-grad implied via "operators")
- [x] (★) narrative concept words seeded: *execution trace* (→ "trace sub-parts"), *governance* → resurface in 句7
- Faithful to drafts 01 (§M1–M3) and global-facts Components 1–4.

## 句5 — Qualitative effect | 19w (target 18–26)
"By this design, SkillStrata loads only what a task depends on, turning ungoverned accumulation into a self-correcting skill system."
- [x] Opens "By this design" → attributes effect to 句3–4 design
- [x] 0 numbers / 0 baselines / 0 metrics
- [x] Specific verbs ("loads only what depends on", "turning … into")
- [x] Ends on qualitative phrase: *self-correcting skill system* (sets up the gate result in 句6)
- Callback: "ungoverned accumulation" echoes 句2's named flaw, closing the conflict.

## 句6 — Empirical highlight (hot baseline + multiplier) | combined gate+efficiency, ≥2 numbers (target 32–44; runs ~49 as one ;-joined sentence)
"On real **SpreadsheetBench**, its gate autonomously **rejects** a harmful distilled round that drops validation accuracy by $10$ points and **accepts** the next that recovers it, with no gradient signal; in controlled simulation it reaches the highest success at the lowest cost---$0.704$ versus **Trace2Skill**'s $0.574$ at roughly $\textbf{2}\times$ fewer tokens."
- [x] Hot baseline NAMED with \textbf{}: **Trace2Skill** (also benchmark **SpreadsheetBench**)
- [x] Multiplier form present: **2×** fewer tokens; plus two-digit-style absolute (0.704 vs 0.574; −10pp gate)
- [x] ≥2 distinct highlights: (a) [REAL] gate reject/accept behavior; (b) [SIM] success+token double-win
- [x] ★ PROVENANCE HONEST: gate = "real SpreadsheetBench"; efficiency = "controlled simulation"; **280-test [PENDING] NOT stated**; no fabricated number
- [x] §Experiments §E1.B + §E2 + §E4 actually compare Trace2Skill and run the gate — claim is backed
- Note: single sentence carries both provenance tiers via ";" so the abstract never laundering [SIM] as real. Over the 44 soft cap as one sentence, but it is the mandated ≥2-number empirical sentence; total abstract stays in band.

## 句7 — Bonus hook (counter-intuitive) | 38w (target 22–32; +6, accepted)
"**Most strikingly**, a distilled skill can *harm* a task it would otherwise solve when its own self-check verifies a tautology rather than task semantics, manufacturing **false confidence**---revealing why **self-evolving agents** must govern execution itself, not only their library."
- [x] Lead-in = "Most strikingly" (∈ allowed set; best with counter-intuitive content)
- [x] Content type C (counter-intuitive): a distilled skill HARMS a task it would otherwise solve via tautological self-check = **false confidence** (REAL case study 416-15)
- [x] (★ ORAL closure) echoes 句1 大终点词 **self-evolving agents** + 句4 *governance*/self-check
- [x] 0 new numbers
- [x] Does NOT restate 句6 — adds the false-confidence mechanism + train/inference governance symmetry ("govern execution … not only their library")
- Sourced from global-facts REAL negative-transfer case study + draft 01 §M3 verify-loop symmetry; +6 over soft cap accepted to land the mechanism cleanly.

---

## Global checklist (Phase 3)
| # | Check | Result |
|---|---|---|
| G1 | Word count 268 ∈ hard band ~[162,280] | ✓ (above 255 soft ceiling but within ±10% hard ceiling) |
| G2 | Sentence count = 8 (7 core + 句2.5) | ✓ |
| G3 | All per-sentence local checklists pass | ✓ |
| G3b | ★ 句2.5 bridge present, BEFORE method; 句3 "Guided by this principle" callback; same discipline as 句1 | ✓ |
| G4 | Inter-sentence echoes: self-evolving 句1↔句7; trace/governance 句4↔句7; 句5 qualitative ↔ 句6 quantitative | ✓ |
| G5 | ≥1 italic thought-core word (*self-evolve*, *operate on top*, *accumulation*, *harm*) | ✓ |
| G6 | ≥1 external-discipline analogy (complex networks / multilayer network) | ✓ |
| G7 | Bold numbers + bold baseline name (**Trace2Skill**, **2×**) | ✓ |
| G8 | No forbidden words (novel/impressive/remarkable/SOTA/promising) | ✓ |
| G9 | 句7 passes surprise test (false-confidence tautology finding) | ✓ |
| G10 | Reads in one breath | ✓ |
| — | PROVENANCE: 280-test [PENDING] not stated; gate=[REAL], efficiency=[SIM] phrased honestly | ✓ |

**Hard-fail count: 0.** ORAL-soft: 5/5.

## Minor soft-band notes (not hard fails)
- Total 268w sits in the 255–280 acceptable window (skill: hard fail only outside ~280), driven by the mandatory 句2.5 bridge + the two-tier provenance-honest empirical sentence. Acceptable; further cuts would drop load-bearing provenance or the bridge's "structure, not bulk."
- 句2.5 (31), 句3 (27), 句7 (38) run a few words over their per-sentence soft targets; kept because each carries a required callback/echo. No single sentence is grammatically overloaded.
