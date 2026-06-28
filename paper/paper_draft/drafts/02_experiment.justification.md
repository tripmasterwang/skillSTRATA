# Experiments draft — per-sentence justification

> Maps every sentence of `02_experiment.md` to its source-of-truth fact + provenance tag.
> Sources: BRIEF = PAPER_BRIEF_FILLED.md; GF = _global_facts.md; METHOD = drafts/01_method.md.
> ★ Provenance: [SIM] = simulator (pending real-benchmark replacement); [REAL] = SpreadsheetBench qwen3.6-35b-a3b official per-instance hard; [PENDING-280TEST] = not yet available.

## §E0 — RQ list opener (untagged)
| Sentence (gist) | Source | Tag | Note |
|---|---|---|---|
| Central hypothesis (italic): gains from stratifying/governing/routing, not a larger document | GF §Paradigm framing + BRIEF 0.3/2.2 | — | restates abstract central reframe; designed-to-validate phrasing |
| Structured around five RQs | GF §RQ list (RQ1–RQ5) | — | N=5 matches RQ list |
| RQ1 success@lower-token | GF RQ1; BRIEF 7.1 | — | \textbf{(RQ1)}; no benchmark named yet |
| RQ2 which operators (moving from outcome to mechanism) | GF RQ2; BRIEF 7.1 | — | CRV "moving from X to Y" framing |
| RQ3 governance stability safety net | GF RQ3; BRIEF 7.5 | — | \textbf{(RQ3)} |
| RQ4 routing precision + negative transfer | GF RQ4; BRIEF 7.1 | — | \textbf{(RQ4)} |
| RQ5 test-time assembly OOD recovery | GF RQ5; BRIEF 7.5.bis | — | "Finally" + exploratory framing |
| Explicit [REAL]/[SIM]/[PENDING] disclosure | task provenance requirement | all | surfaces tags up front, non-negotiable |

## §E1 — Setup (untagged, 2 paragraphs per Part 7.0 cap)
| Sentence | Source | Tag | Note |
|---|---|---|---|
| Backbone qwen3.6-35b-a3b, frozen ReAct executor, SKILL.md bodies | GF §Hot baseline names; BRIEF 7.2 + 2.6 | [REAL] | model id + reasoning_effort=medium |
| SpreadsheetBench verified-400, official per-instance hard, 80/40/280 split_seed=42 | BRIEF 2.6 + 7.2 | [REAL] | exact protocol |
| [SIM] simulator: 8 seeds, 400-task stream, 4-domain DAG; tab:setup | BRIEF 2.4 + 7.2; Part 12 T3 | [SIM] | marked pending replacement |
| Baselines: No-Skill/Trace2Skill (monolithic); Flat/Pruning (flat); SkillOpt target (curated) | BRIEF 7.2 baselines; GF | [REAL]/[SIM] | \ding{} grouped; SkillOpt is the real target |
| Metrics + arrows | BRIEF 7.2 Metric list | — | each metric carries ↑/↓ |
| [SIM] 8-seed means; ±std + paired test PENDING | BRIEF 7.10 | [SIM]/[PENDING] | honest stats status |
| Real protocol = SkillOpt; harness caveat (direct-chat vs ReAct) → compare lift over No-Skill | BRIEF 2.6 caveat | [REAL] | required caveat surfaced |

## §E2 — [RQ1] Main results (Register A; 2 paragraphs per Part 7.0 cap)
| Sentence | Source | Tag | Note |
|---|---|---|---|
| Sim results support central hypothesis; dominates every multi-skill baseline | BRIEF 7.3; GF [SIM] | [SIM] | hypothesis restate (要素1) + 总结 (要素2) |
| Baseline 对偶: Trace2Skill 0.574@780tok@0.219nt vs Flat 431tok/0.555 | BRIEF 7.3 table | [SIM] | 要素2.b dual antithesis, ≥2 paradigm classes |
| SkillStrata 0.704@365 (+13 vs T2S, 2.1×, +15 vs flat), NT halved to 0.105 | BRIEF 7.3/2.4 | [SIM] | highlight (要素3); 倍数 expressed |
| We hypothesize split→minimal subgraph; consequently strips irrelevant text | METHOD §M2/§M3 mechanism | [SIM] | why-机制 (要素4), "We hypothesize…Consequently" |
| [SIM] stands in for real head-to-head, pending replacement | task provenance | [SIM] | marks sim as placeholder evidence |
| SkillOpt target: 38.2→47.5(+9.3); Trace2Skill 33.2(−5.0 neg transfer); GEPA/Human/TextGrad | GF [REAL]; BRIEF 2.6 | [REAL] | real numbers verbatim |
| Bar SkillStrata must clear (+9.3, avoid −5.0) under hard metric/split_seed=42 | BRIEF 2.6 | [REAL] | frames target |
| Our 280-test no-skill vs with-SkillStrata is [PENDING-280TEST], not available; explicit placeholder, no substitution | GF §PENDING; task | [PENDING-280TEST] | ★ placeholder sentence; no fabrication |
| Bridge to §E3 (which operators responsible) | skill 桥接 | — | "Having established… a critical question is" |

## §E3 — [RQ2] Ablation (Mode C finding paragraphs; ANALYSIS; 2 paragraphs)
| Sentence | Source | Tag | Note |
|---|---|---|---|
| LOO reveals hierarchy; restructuring operators carry result | BRIEF 7.6 | [SIM] | tab:ablation |
| Finding-title: Routing most critical | BRIEF 7.6/2.5 | [SIM] | R55 paragraph-title-as-claim |
| Remove Route −0.18 (0.643→0.462), tokens 360→472, NT 0.116→0.213 | BRIEF 7.6 table | [SIM] | shallow observation |
| Why: closure $\mathcal{S}^\star$ loads prerequisites only (Eq:route) | METHOD §M3 / Eq:route | [SIM] | story-validation (S-class) |
| S9: route closure not top-k whenever latent prerequisite structure | analysis mandate | [SIM] | transferable principle (S9) |
| Finding-title: Split makes routing cheap | BRIEF 7.6/2.5 | [SIM] | R55 title |
| Remove Split −0.15, tokens 6.6× (360→2345), routeprec 0.081; Full Loading 3932@0.481 | BRIEF 7.6/2.4 | [SIM] | shallow obs; 6.6× from GF |
| Why: unsplit body forces full-load, conflict re-appears | METHOD §M2 Split rationale | [SIM] | story-validation |
| S9: atomic units precondition for any routing payoff | analysis mandate | [SIM] | transferable principle (S9) |
| Validation/governance individually barely move numbers → next subsection | BRIEF 7.6 table | [SIM] | bridge + sets up RQ3 |

## §E4 — [RQ4] Routing precision & negative transfer (ANALYSIS; 2 paragraphs)
| Sentence | Source | Tag | Note |
|---|---|---|---|
| Bridge: isolate why gain is safe not just larger | skill 桥接 | — | "Having shown… we now isolate" |
| RoutePrec 0.391 (1.2× flat, 6× T2S); NT 0.105 (<half of 0.219) | BRIEF 7.3/2.4 | [SIM] | shallow obs |
| Why: governance quarantines conflicting nodes; precision↔NT same mechanism | METHOD governance | [SIM] | story-validation |
| REAL gate: 42.5%→32.5%(−10pp)→reject/12 retired→47.5%(+5pp)/accept | GF [REAL]; BRIEF 2.6 + METHOD Eq:gate | [REAL] | real corroboration verbatim |
| This indicates autonomous screening at curation time, no gradient | METHOD §M2 gate | [REAL]/[SIM] | 升华 verdict (varied wording, not "This answers RQ4") |
| S9: held-out gate (succ non-decreasing ∧ NT non-increasing) for any lifelong library | analysis mandate; Eq:gate | — | transferable principle (S9) |

## §E5 — [RQ3] Governance/validation stability (ANALYSIS; 1 paragraph per Part 7.0 cap)
| Sentence | Source | Tag | Note |
|---|---|---|---|
| Bridge: individually small → probe joint role on long streams | BRIEF 7.5 | — | "Having found… we probe" |
| Remove either alone −0.004..−0.014; remove both → late-success 0.601→0.562 + least stable | BRIEF 7.5/7.6 | [SIM] | fig:stability; shallow obs |
| Safety-net signature: redundant while other holds; degrades on accumulated drift | BRIEF 7.5 | [SIM] | story-validation |
| Validates governance bounds late-life degradation; inference counterpart = verify-loop | METHOD §M3 Eq:verify | [SIM] | verdict (varied) |
| S9: stress-test by jointly disabling safety mechanisms over long stream | analysis mandate | [SIM] | transferable principle (S9) |

## §E6 — [RQ5] Test-time assembly + REAL case study (ANALYSIS + case; 1 paragraph cap, extended for REAL case)
| Sentence | Source | Tag | Note |
|---|---|---|---|
| Exploratory: cast missing skill from trace co-occurrence (Eq:tta) | METHOD §M3 Eq:tta | — | "Finally" exploratory framing |
| Withhold 3 atomic skills/domain; covered 0.296→0.473 (~54% gap), succ +0.056, OOD +0.044, tokens +88%, 2.6 synth/task | BRIEF 7.5.bis table; GF [SIM] | [SIM] | tab:tta; honest cost caveat surfaced |
| Why: trace layer participates at inference vs single-layer graphs route only fixed skills | METHOD §M3; BRIEF 7.5.bis | [SIM] | story-validation |
| REAL case 416-15: no-skill solves; round0 skills break it; mis-route + self_verification tautology → "All checks passed!" overrides date hint | GF [REAL]; BRIEF 2.6 case study | [REAL] | real trace verbatim; names method-internal concept (verify-loop) — satisfies R-5 |
| Closed-loop evidence: false confidence via tautology; verify-loop writes postcondition at task-semantic layer; opening direction | METHOD §M3 verify-loop; BRIEF 2.6 | [REAL] | Register-B 升华 (S3 closed-loop triple) |
| S9: self-check only as trustworthy as its condition semantics; anchor to task-level postconditions | analysis mandate; BRIEF 2.6 paper句 | — | transferable principle (S9) |

## §E7 — Efficiency (untagged)
| Sentence | Source | Tag | Note |
|---|---|---|---|
| 365 tok vs 780 (2.1×) vs 3932 (10.8×) | BRIEF 7.9 | [SIM] | double-win setup |
| Highest success at lowest loaded-token cost; latency/API deferred + pending | BRIEF 7.9/2.4 | [SIM]/[PENDING] | double-win句; matches abstract efficiency promise |

## Global checklist results
- G1 word count: ~1180 rendered prose words (within tier band; Part 7.0 caps each subsection at 2/2/2/1/1 paragraphs).
- G2 subsections: E0 + Setup + 5 RQ subsections + Efficiency paragraph = matches Part 7.0 author-declared 5 result subsections + infra.
- G15a RQ-tag binding: every result/analysis subsection carries exactly ONE [RQ_N]; RQ1–RQ5 each claimed by exactly one subsection; no multi-RQ tags (RQ2/RQ4 ablation lump SPLIT into §E3/§E4 per ONE-RQ HARD rule). PASS.
- RQ-scaffolding budget: each RQ a literal question only in §E0; no "RQ_N asks" openers; literal "This answers RQ_N" used 0× (all verdicts folded into varied 升华). PASS.
- G2g shallow→deep: every ANALYSIS subsection (E3/E4/E5/E6) carries story-validation + S9 transferable principle (5 S9 sentences total). Superiority §E2 + efficiency exempt. PASS.
- Number provenance: every number carries [SIM]/[REAL]; [PENDING-280TEST] kept as explicit placeholder, no substitution. PASS.
- Asset gate: WAIVED; \Cref{tab:main,tab:ablation,tab:setup,tab:tta,fig:stability} kept, each wrapped with a TODO comment (no _asset_inventory.json on disk). Did not halt (intentional per task).

## Honest notes on per-sentence steps
- Mode-C tier templates (T1 finding paragraphs) applied to §E3; the SIM world is a single synthetic benchmark so there is NO §E2b per-env split and NO SIM case gallery — only the one REAL case study (416-15) exists, placed in §E6. This is faithful to brief 7.3.bis ("[SIM] single synthetic world, 1 paragraph") and 7.8 ("[SIM] no case study; real version can add").
- Register A enforced on §E2 main + §E7 efficiency (≥5 numbers, ≤1 升华). Register B enforced on the §E6 case study (S3 closer + method-internal concept name).
- §E2 is split into two functional-label paragraphs (Simulator evidence / Real-benchmark target) to keep the [SIM] evidence and the [REAL]+[PENDING] target visibly separate — required by the provenance mandate, within the Part 7.0 2-paragraph cap.
