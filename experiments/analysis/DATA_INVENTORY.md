# SkillStrata 实验产物 — 数据盘点 (DATA_INVENTORY)

> 只读聚合，生成于 2026-06-28。所有数值均可在标注的源文件中核对。
> 配套产物：`agg_results.json`（结构化全量）、`figs/fig1..fig4_*.png`。
>
> Backbone（ours 主干）= qwen3.6-35b-a3b。Benchmark = SpreadsheetBench official。
> 竞品矩阵 SkillOpt 由 codex/claude harness 直接驱动。

---

## A. Ours —— 进化轨迹（curate_history.json + trained_graph.json）

源目录：`external/repos/Trace2Skill/runs/curate_{fromzero,codex,claude,minisweagent}/`

每个 run 实际只跑了 **4 轮（round 0..3）**，不是描述里的 5 轮。

| seed harness | val r0 | r1 | r2 | r3 | 被门拒绝的轮(accepted=false) | 是否真正进化 |
|---|---|---|---|---|---|---|
| **fromzero** | 0.425 | 0.475✅ | 0.55✅ | 0.60✅ | r0 | **是**，0.425→0.60 单调上升 |
| codex | 0.30 | 0.30 | 0.30 | 0.35✅ | r0,r1,r2 | 几乎没动，只有 r3 接受 |
| claude | 0.35✅ | 0.35 | 0.35 | 0.35 | r1,r2,r3 | 没动，r0 后全被拒 |
| minisweagent | 0.425 | 0.425 | 0.425 | 0.425 | r0,r1,r2,r3 | **完全没动**，全程被门拒绝 |

源：各 `curate_*/curate_history.json`。`val` 字段可信；`checkpoints` 字段不可信（见质量标注）。

### 终态三层图（trained_graph.json，governance 真实计数）

| harness | skills | capability_edges | governance 条数 | **真实 checkpoint**(kind=='checkpoint') | governance kind 分布 |
|---|---|---|---|---|---|
| **fromzero** | 46 | 74 | 63 | **11** | insert_decision 46 / checkpoint 11 / accept 3 / merge_decision 2 / rejected_edit 1 |
| codex | 48 | 43 | 52 | **0** | insert_decision 48 / rejected_edit 3 / accept 1 |
| claude | 48 | 43 | 60 | **8** | insert_decision 48 / checkpoint 8 / rejected_edit 3 / accept 1 |
| minisweagent | 48 | 48 | 52 | **0** | insert_decision 48 / rejected_edit 4 |

源：各 `curate_*/trained_graph.json` 的 `governance[]`。

---

## B. Ours —— curate test_280（用各自进化出的 skillstrata 图做路由测试）

源：`curate_{h}/test_280/eval_official_results.json` 的 `summary`。

| harness | N（官方计分集） | passed | instance acc | 备注 |
|---|---|---|---|---|
| **fromzero** | 400 | 157 | **39.25%** | 进化最成功的图 |
| codex | 400 | 83 | 20.75% | 进化失败的图，弱 |
| claude | 400 | 103 | 25.75% | 进化失败的图 |
| minisweagent | 400 | 116 | 29.00% | 进化失败的图 |

> ⚠️ 口径冲突：目录名叫 `test_280`，但 `eval_official_results.json` 的 `total_instances=400`。
> 实际只 attempt 了 280 个 held-out 实例（见 `results.json` 的 `total_instances=280`），
> 官方评分把另外 120 个未跑实例补成 fail，所以分母=400。
> `curate_fromzero/RESULTS.md` 给的是 **280 分母**口径：noskill 30.7%(86/280)、withskill 56.1%(157/280)。
> 注意分子 157 完全一致——只是 RESULTS.md 用 280 分母（56.1%），eval_official 用 400 分母（39.25%）。
> **跨 harness 对比时统一用 400 分母（4 个 run 都一致），不要把 56.1% 和别的 39.25% 混着比。**

---

## C. Ours —— fromzero 跨 harness 三档对照（bare / skill / skillstrata）

源：`curate_fromzero/test_280_{harness}_{bare,skill,}` 各自的 `eval_official_results.json`（N=400 口径）。

| harness | bare | skill(flat) | skillstrata(graph路由) |
|---|---|---|---|
| codex | 37.5% | **49.2%** | 30.5% |
| claude | **52.5%** | 51.7% | 27.3% |
| minisweagent | **55.0%** | 53.2% | 33.0% |

辅助基线（同目录）：`test_280_noskill` = **21.5%**；`test_280`(qwen主干+skillstrata图) = **39.25%**。

> ⚠️ **重要真实发现（不是数据坏掉，是结果本身）**：把 fromzero 进化出的 skillstrata 图
> **迁移到 codex/claude/minisweagent 这三个强 harness 上时，skillstrata 路由反而显著低于它们的 bare/skill**。
> 即图在 qwen 主干上有效（21.5→39.25），但跨 harness 迁移时退化。这是一个需要在论文里诚实讨论的负向迁移现象。

---

## D. Ours —— strong-base verified-400 对照（COMPARISON.md）

源：`runs/COMPARISON.md`（N=400，qwen3.6-35b medium + verification + retry，**与 C/B 是不同的 run 配置**）。

| Run | Instance Acc (hard) |
|---|---|
| no-skill | 25.0% (100/400) |
| monolithic-xlsx35B | 41.0% (164/400) |
| **SkillStrata-graph** | **45.0% (180/400)** |
| monolithic-122B-full | **0.0% (0/400)** ⛔ 坏 |
| flat-bm25 | **0.0% (0/400)** ⛔ 坏 |

> ⚠️ 这里的 SkillStrata-graph=45.0% 跟 B 表的 fromzero/test_280=39.25% **不是同一个 run**（强基线版 vs from-zero 版），不能当作同一条线。

---

## E. 竞品 SkillOpt 矩阵（harness_ms）

源：`nonergodic-self-evolution/external/SkillOpt/outputs/harness_ms/<bench>_<harness>_<tier>_s<seed>/eval_summary.json`，取 `hard` 字段，5 seed 求均值。

mean hard (%) over seeds（括号内为 n_items / n_seeds）：

| bench | harness | noskill | human | skillcreator | skillopt_ckpt | skillopt_self |
|---|---|---|---|---|---|---|
| officeqa | codex | 52.7 | 49.0 | 45.0 | 47.0 | 44.0 |
| officeqa | claude | 39.3 | 56.0 | 53.0 | 48.0 | 47.0 |
| spreadsheetbench | codex | 44.0 | 47.0 | 41.0 | 50.0 | 51.0 |
| spreadsheetbench | claude | 36.0 | 37.0 | 35.0 | 36.0 | 29.0 |
| searchqa | codex | 86.0 | 82.5 | 85.5 | 86.5 | 80.5 |
| searchqa | claude | 69.0 | 71.0 | 80.5 | 72.5 | 81.5 |
| alfworld | codex | 77.5 | 79.5 | ⛔缺 | 87.5 | ⛔缺 |
| alfworld | claude | 77.5 | 81.5 | ⛔缺 | 88.0 | ⛔缺 |

- 全部格子都是 5 seeds（n_seeds=5），除了 alfworld 的 skillcreator / skillopt_self 两档**完全缺失**（两个 harness 都缺）。
- n_items 各 bench 不同：officeqa noskill=15、其余 tier=20；spreadsheetbench=20；searchqa=40；alfworld=40。**officeqa 的 noskill 用 15 题、其它档用 20 题，分母不同，不能直接横比同一行**。
- 命名异常：`spreadsheetbench_claude-skillopt_{ckpt,self}_s2`（连字符）只有 s2 一个，是 underscore 版（s1-s5 齐全）的冗余/误命名重复，已忽略，不影响计数。

---

## 【数据质量诚实标注】

1. **真实跑出来、可信的**：
   - fromzero 进化轨迹（val 0.425→0.60，单调，r0 被门拒）—— 唯一一个真正完成自进化的 run。
   - fromzero 终态三层图结构（skills 46 / edges 74 / gov 63 / 真实 checkpoint 11）。
   - B 表 4 个 curate test（400 分母 instance acc：39.25 / 20.75 / 25.75 / 29.00）。
   - C 表跨 harness 三档（含负向迁移现象）。
   - D 表 strong-base（noskill 25 / mono35B 41 / skillstrata 45）。
   - E 矩阵除 alfworld 两档外，全部 5-seed 真实。

2. **0% / 坏掉的格子**：
   - D 表 `monolithic-122B-full` = 0.0%、`flat-bm25` = 0.0%（COMPARISON.md 明确，整 run 失败，不可用）。
   - E 矩阵 alfworld 的 `skillcreator`、`skillopt_self`（codex+claude 共 4 格）**完全没有产物**。

3. **进化没起来的 run（不是坏，但要标注弱）**：
   - codex / claude / minisweagent 三个 seed-harness 的 curate，val 几乎不动、绝大多数轮被验证门拒绝，
     终态图测试分（20-29%）远低于 fromzero（39.25%）。其中 codex、minisweagent 的 governance 里
     **真实 checkpoint=0**（说明从未通过验证门固化检查点）。

4. **不可信字段**：
   - `curate_history.json` 的 `checkpoints` 字段为已知埋点 bug（漏记/错记）。**真实 checkpoint 数一律以
     `trained_graph.json` 的 `governance[]` 里 `kind=='checkpoint'` 计数为准**（fromzero=11, claude=8, codex=0, minisweagent=0）。
   - `results.json` 的 `successful_instances/success_rate`（如 fromzero 243/280=86.8%）是「agent 跑完没崩」的比例，
     **不是答题正确率**，别当成 accuracy。

5. **口径不一致、不能直接横比的地方**：
   - **test_280 目录名 vs total_instances=400**：fromzero RESULTS.md 用 280 分母（56.1%），eval_official 用 400 分母（39.25%），分子同为 157。统一取 400 分母做跨 run 比较。
   - **D 表（strong-base 400）vs B 表（fromzero curate 400）**：是不同 run 配置，SkillStrata 45.0% ≠ 39.25%。
   - **E 矩阵 officeqa noskill n=15 vs 同 bench 其它档 n=20**：同一行分母不同，横比需注明。
   - SkillOpt 各 bench 题量不同（15/20/40），跨 bench 的绝对分不可直接比较，只能比同 bench 内 tier 差。
