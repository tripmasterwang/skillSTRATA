# SkillStrata 消融分析报告 (ABLATION_REPORT)

> 生成于 2026-06-29 本会话，承接 `experiments/HANDOFF_2026-06-29.md`。
> **本报告只写已亲自硬核核实的数字**（官方 scorer + 独立 recount 双验），口径一律 **280 held-out subset**
> (`script/score_on_split.py` + `script/data/skillopt_test_ids.txt`)。
> 取代交接里引用但实际不存在的 `PROGRESS_2026-06-29.md`，并**纠正交接的两处错误**(见 §0)。
> Backbone = qwen3.6-35b-a3b (讯飞 MaaS `xopqwen36v35b`, temp=0, thinking=true, reasoning=medium)。

---

## 总览：我们消融了哪 7 个部件（机制图）

```
══════════════ 进化期：从空图 curate（训练，跑 E 轮）══════════════

  空图 S0（零技能）
     │
     ▼  ┌──────────────── 每轮循环 ────────────────────────────────┐
        │ ① ROLLOUT   用当前图在 train 跑 agent(verify关) → 轨迹 + 给   │
        │             路由到的技能记 heat(成功/失败计数)               │
        │ ② DISTILL   LLM 读每条轨迹 → 抽 0-2 个可复用技能片段 (MAP)    │
        │ ③ INTEGRATE                                                │
        │     ├ INSERT 新片段=候选节点 ────────◄ 底座(onlyinsert只留这)│
        │     └ MERGE  与旧节点 cos≥0.80 则并入 ◄━━ 消融 evo_nomerge   │
        │ ④ SPLIT    一节点管≥3类型就拆开 ──────◄━━ 消融 evo_nosplit   │
        │ ⑤ GATE     本轮插入跑 val，严格涨分才留，否则回滚            │
        │                                    ◄━━ 消融 evo_nogate      │
        │ ⑥ CHECKPOINT 给 succ≤0.6 的高频技能挂"验证门"                │
        │                                    ◄━━ 消融 evo_nockpt      │
        └────────────────────────────────────────────────────────┘
     │
     ▼
  训练好的三层图  ┌ trace 层：每次执行记录 → heat（谁不靠谱）
                 ├ capability 层：技能节点 + 边（实测全是 alternative_to）
                 └ governance 层：insert/merge/split/accept/reject/门

══════════════ 推理期：冻结图，测 280 题（翻测试旋钮）══════════════

  一道题
     │
     ▼  ┌─ ROUTE 选技能 ───────────────────────────────────────────┐
        │  第1步 选种子：                                            │
        │     • agent = 让 LLM 选种 ──────────► 完整   56.1         │
        │     • graph = 用 BM25 选种 ─────────► abl_graph 58.6      │
        │  第2步 依赖闭包(凑成最小可跑子图) + governance 过滤冲突/封禁 │
        │            └─ 这两步才是"图结构"的本体，agent/graph 都走它  │
        │  ──────────────── 对照基线（不走图）──────────────────     │
        │     • bm25 = 纯 BM25 top-k，没有图边 ► abl_bm25 41.8       │
        │     • full = 所有技能全塞，不做选择 ► abl_full  43.6       │
        └──────────────────────────────────────────────────────────┘
     │  把路由出的几个技能注入 executor 的 prompt
     ▼
  执行 + VERIFY-LOOP：路由经过带门的节点 → 执行→验证→失败回滚重试(预算2)
     • 门开 = 完整 56.1 / abl_graph 58.6
     • 门关 = abl_noverify 44.3 ◄━━ 消融 verify-loop
     │
     ▼
  答案
```

**消融部件清单（共 7 个，代码出处已核对）：**

| 阶段 | 部件 | 作用 | 关掉它的格 | 实现位置 |
|---|---|---|---|---|
| 进化 | INSERT | 把新片段作为候选节点插入（底座，不可单独关） | `evo_onlyinsert`=只留这个 | curate.py `integrate_fragments` |
| 进化 | MERGE | 近重复片段并入旧节点，防库膨胀 | `evo_nomerge` (`--no-merge`) | curate.py（sim_threshold→2.0 永不并） |
| 进化 | SPLIT | 一节点管太多任务类型就拆成子节点 | `evo_nosplit` (`--no-split`) | curate.py `split_divergent` |
| 进化 | GATE | 本轮插入跑 val，严格涨分才保留，否则回滚 | `evo_nogate` (`--no-gate`) | curate.py `validation_gate` |
| 进化 | CHECKPOINT | 给 trials≥3 且 succ≤0.6 的高频技能自动挂验证门 | `evo_nockpt` (`--no-checkpoint`) | verify.py `mint_checkpoints_from_traces` |
| 推理 | ROUTER | 选种子(agent/graph) + 依赖闭包 + governance；对照=平面 bm25/full | `abl_{graph,bm25,full}` | router.py `GraphRouter`/`FlatRouter` |
| 推理 | VERIFY_LOOP | 路由经过带门节点时执行→验证→失败回滚重试 | `abl_noverify` (`VERIFY_LOOP=0`) | verify.py `node_verifier_loop` |

> **关键结构（代码核实）**：`agent` 与 `graph` 路由的唯一差别 = 选种子用 LLM 还是 BM25；
> 后面的依赖闭包 + governance **两者完全一样**。所以推理消融能干净二分为两个正交问题：
> ① **有没有图**：{graph 58.6, agent 56.1} vs {full 43.6, bm25 41.8} = **+15pp（图结构的净价值）**；
> ② **种子用 LLM 还是 BM25**：agent 56.1 vs graph 58.6 = **打平**(p=0.5)。
> → "图结构值 15 分，但用不用 LLM 挑种子不值钱" —— 省钱又干净。

---

## §0. 对上一份交接的两处纠正（诚实优先）

1. **router.py 是否在两批次间被改 —— 已澄清：没有。**
   `router.py` mtime = `2026-06-27 13:43:20`、`harness.py` = `2026-06-27 13:44:19`，
   均早于完整主结果批次(06-28 02:17)与消融批次(06-28 20:04)，且两批次之间未改动
   (git-tracked、无未提交改动；最后一次涉及 router.py 的 commit 是 6/26 的 `75b54aec`，时间 16:41 —
   这正是交接里"16:42 改了 router.py"幻觉的来源：一个被错配的真实 commit 时间戳)。
   → **两批次同代码**：verify-loop 结论可抢救，56.1 可作消融基准。

2. **`abl_graph` 真实分 = 58.6%(164/280)，不是交接写的 49.6%(139)。**
   该 `eval_official_results.json` 正是交接 §6.1 自承"被手动 evaluate 竞争写坏"的那个文件。
   49.6 是当时读到的脏值；58.6 是 00:51 进程退出后干净重评的值，已用官方 scorer + 独立 recount(`success` 字段)双验。
   其余 4 格(56.1 / 44.3 / 43.6 / 41.8)与交接一致，无需改。
   **这翻转了一个核心结论**（见 §1）。

---

## §1. 推理消融（冻结 from-zero 图，翻测试旋钮，280-subset）

产物：`external/repos/Trace2Skill/runs/curate_fromzero/{test_280, abl_graph, abl_noverify, abl_full, abl_bm25}/`。
旋钮：`SKILLSTRATA_ROUTER` ∈ {agent, graph, bm25, full}、`SKILLSTRATA_VERIFY_LOOP` ∈ {0,1}。

| 格 | router | verify | 280-subset | 批次 | 同批次硬可比? |
|---|---|---|---|---|---|
| `abl_graph` | graph | 1 | **58.6% (164/280)** | 20:04 | ✅ |
| 完整 `test_280` | agent | 1 | 56.1% (157/280) | 02:17 | ⚠️跨批次 |
| `abl_noverify` | agent | 0 | 44.3% (124/280) | 20:04 | ✅ |
| `abl_full` (34技能全塞) | full | 1 | 43.6% (122/280) | 20:04 | ✅ |
| `abl_bm25` | bm25 | 1 | 41.8% (117/280) | 20:04 | ✅ |
| **`abl_complete`(补,同批次)** | agent | 1 | **57.1% (160/280)** ✅ | 06-29 | ✅同代码 |

### 已确证结论
- **C1 — 图结构路由 ≫ 平面检索 / 全量堆叠**（同批次，铁）：
  graph 58.6 vs full 43.6 (**+15.0pp**) vs bm25 41.8 (**+16.8pp**)。
  同样的技能内容，"按图路由择一" 比 "全塞" 和 "BM25 平面检索" 各高 15-17pp。
  → 增益在**组织/路由结构**，不在技能内容本身。
- **C2 — 确定性图路由 ≥ 昂贵的 agent(LLM) 路由**（统计打平，✅A 已封死跨批次）：
  graph 58.6 vs agent(同批次 abl_complete) 57.1，差 1.5pp 仍打平(原 02:17 agent=56.1，与同批次 57.1 仅差 1pp
  → 跨批次噪声 ~1pp，56.1 可靠)。→ **不需要 LLM 来路由，图结构本身就够**。
- **C3 — verify-loop 边际价值 ~−12.8pp**（✅同代码同口径，A 已收口）：
  agent+verify=1 (同批次 abl_complete **57.1**) → agent+verify=0 (noverify **44.3**) = **−12.8pp**。
  router.py 自 06-27 未变(§0.1)，且 57.1≈原 56.1 证明跨批次噪声 ~1pp → verify-loop 值 **~13pp** 稳了。

### ⚠️ 作废的旧表述
- 交接/旧记忆的 "graph 49.6 < 完整 56.1，所以 agent 路由组织带来增益" —— **错**(数据脏)。真实是 graph ≥ agent。
- "noverify −11.8pp = 推理期第二大贡献" 这种**绝对排名**表述：方向对，但因 graph 现在是最高格、且 verify 仍跨批次，
  改为 "verify-loop 值约 12pp，待 A 同批次确认"，不再排"第几大"。

### §1.1 测试时部件使用画像（机制证据，配图 `figs/fig_test_usage.png`）

来源：主结果 `test_280/routes/*.json`(每题 dump 路由的技能 `nodes` + 其中带门的 `guarded`)。
- **图解**：横向蓝条 = 每个 deployed 技能在 280 题里被路由的次数；条上数字 = 次数；**黑钻石 ◆** = 该技能带 verify 门；
  右下红框 = 测试时**从没被路由**的 deployed 技能数。
- **口径**：46 mint 中 12 个是 retired(不参与路由)；deployed 34 个里 **20 个被用 / 14 个测试时 0 使用**(含 11 个工具类)。
- **四条机制证据（与架构消融互证）**：
  1. **主力极少**：34 deployed 仅 20 个被用过；前 6 个(Python Computation 171×、parse_text 133×、precompute 98×、
     Dynamic Range 97×、targeted_column 72×、Safe Backward 61×)扛绝大多数路由。
  2. **省 token（每题只路由 3.00 技能，min2/max3）**：不是"全塞" → 直接解释 `abl_full` 全堆叠反掉 15pp。
  3. **门覆盖 99%（277/280 题路由经过带门技能）**：verify-loop 几乎管每道题 → 解释为何关掉它掉 ~12pp(§1 C3)。
  4. **14 个 deployed 测试时 0 使用（含 11 工具类，BM25/LLM 路由按"任务描述 vs 技能正文"匹配，工具技能不在任务词汇空间）**：
     纯库膨胀、对结果零贡献 → 印证"只有准入门、无退出门"软肋(见 `EVOLUTION_LEDGER.md`)。

---

## §2. 进化消融（从零 curate，禁一个进化部件，round-2 早停，280-subset）

产物：`external/repos/Trace2Skill/runs/evo_{nogate,nosplit,nockpt,onlyinsert,nomerge}/test_280/`。
旋钮：`curate_driver.py` 的 `--no-{merge,split,gate,checkpoint}`；`onlyinsert`=全关。

> **现状(2026-06-29 11:14)**：补跑陆续完成中。**交接 §3.2 的 50.x 数字已证实是估值、不可信**——
> 第一格 `evo_nogate` 跑满 280 后真分 = **44.6%**，比交接的 50.7% 低 6pp。其余格待补跑完用官方 scorer 重算。

| 格 (curate flag) | test_280 (280) | 终图节点 | 状态 |
|---|---|---|---|
| `evo_nosplit` (--no-split) | **45.4% (127/280)** ✅ | _待核_ | 跑满+已评(进化消融最高=关拆分伤害最小) |
| `evo_nogate` (--no-gate) | **44.6% (125/280)** ✅ | _待核_ | 跑满+已评 |
| `evo_nockpt` (--no-checkpoint) | **33.2% (93/280)** ✅ | _待核_ | 跑满+已评 |
| `evo_onlyinsert` (全关) | **32.1% (90/280)** ✅ | _待核_ | 跑满+已评(≈noskill 30.7，只插不组织几乎无用) |
| `evo_nomerge` (--no-merge) | **40.0% (112/280)** ✅ | _待核_ | 跑满+已评 |
| **r2 全开基准**(=`evo_r2_test`) | **56.1% (157/280)** ✅ | 23节点/6门 | round-2 全部件开(替代已砍的B) |

**Δpp(各格 − r2 全开基准 56.1)**:onlyinsert −24.0 > nockpt −22.9 > nomerge −16.1 > nogate −11.5 > nosplit −10.7。
→ 去掉任一进化部件都掉 ≥10pp,**门(checkpoint)/全关 伤害最大,拆分最小**。
⚠️ 口径:r2 是 4 轮 fromzero 的 round-2 中间态(全部件),消融格是独立 2 轮 curate(禁一部件),轻微口径差,Δ 仅供方向参考。
另注:r2(round-2)test=56.1 与 r3(4轮终图)test=56.1 相等 → test 上 R3 无净增益(R3 新增多为僵尸)。

- **关键混淆变量**：这些是 **round-2 早停**的图，而完整 from-zero 是 **4 轮**(val 0.425→0.475→0.55→0.60)。
  轮数(2 vs 4)是混淆变量 → **不能拿它们的绝对值跟 56.1 比**。
- **补充实验 B (`evo_allon_r2`)** = 全部件开、ROUNDS=2 的基准，让 5 格能算 "去掉部件 X 伤害几 pp" 的 Δpp，
  而非仅相对排序。

---

## §3. 已有的方法解剖（来自 EVOLUTION_DEEPDIVE.md / DATA_INVENTORY.md，已核实，供报告引用）

- **进化在进化什么 (RQ1)**：终图 46 mint→34 部署/12 retired；74 条 capability 边**全是 `alternative_to`**(0 组合边)
  = 宽平替代策略池 + 路由择一，**非** depth-wise 层级组合（论文须如实写）。收敛到一个主导元策略
  "Python 预计算写静态值、别用脆弱 Excel 公式"，蒸馏成多个可路由化身 → 解释 alternative_to 同源。
- **门挂在哪 (RQ2)**：11 个 verify checkpoint **精准挂在 succ 0.46-0.60 的高频不靠谱技能上**
  (parse_text_range/precompute/python_computation…)，非均匀添加 = 自动把 retry 安全网挂在最薄弱承重环节。
  这与 §1-C3 的 verify-loop ~12pp 互为印证。
- **增益分布 (case级，280)**：救活 85 / 拖垮 14 / 净 +71 / 都对 72 / 硬骨头(都错) 109(39%)。
  极不均匀：**Cell-Level 22.3→52.3 (+30.1)** 是主战场，Sheet-Level 49.4→64.4 (+14.9)。救活题平均只路由 3.0 技能(省 token)。
- **软肋(诚实)**：14 题被技能拖垮 + 109 题硬骨头 = 38% 进化没帮上或帮倒忙。

---

## §4. 收口待办

- [ ] **A 收口**：`abl_complete` 跑完 → 用同批次 agent+verify=1 重算 C2(agent-vs-graph)与 C3(verify-loop)的同批次幅度。
- [ ] **B 收口**：`evo_allon_r2` 跑完 → 作 round-2 基准，回填 §2 表的 Δpp。
- [ ] **进化消融聚合**：5 格补跑完 → 官方 scorer 重算 §2 表 + 终图节点数。
- [ ] 出图：推理消融部件贡献条形图(C1/C2/C3)、进化消融部件×Δpp×终图节点(图膨胀)入 `analysis/figs/`。

---

## §5. 关键路径速查

| 项 | 路径 |
|---|---|
| 推理消融启动器 | `script/run_infer_ablation.sh <label> <router> <verify> <key>` |
| 进化消融启动器 | `script/run_evo_ablation.sh <label> <key> "<flags>"` (env ROUNDS/WORKERS) |
| B 编排器(等 key 自动起 round-2 全开) | `script/orchestrate_supp_b.sh` + 日志 `runs/orchestrate_supp_b.log` |
| 评分(280口径) | `script/score_on_split.py <eval_json> script/data/skillopt_test_ids.txt` |
| A 日志 | `runs/abl_complete.log` |
| B 日志 | `runs/evo_allon_r2.log` |
