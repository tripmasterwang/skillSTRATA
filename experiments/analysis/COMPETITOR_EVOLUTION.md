# 竞品 SkillOpt 进化机制解剖（RQ1 核心对比）

来源（真实产物，2026-06-28 核对）：
`nonergodic-self-evolution/external/SkillOpt/outputs/spreadsheetbench_q36_selftrain_dsv32_seed42/`
（`history.json` 逐步轨迹 / `skills/skill_v0000-v0004.md` 版本快照 / `summary.json` 配置+token）

## SkillOpt 怎么进化的（拆解自 history.json）
每步循环：`rollout → reflect(analyst) → aggregate(merge edits) → select(rank, edit_budget) → update(apply到单体doc) → evaluate(selection gate)`。
- **进化对象 = 单个技能文档**（一坨 markdown），每步往里加若干条 edit（merge/rank 后取 top-k）。
- **有门**：`gate_metric=hard`，算 `candidate_gate_score`，`action ∈ {accept_new_best, reject}`，锁 `best_score`。
- 配置：optimizer=deepseek-v3.2，target=qwen3.6（`xopqwen36v35b`），num_epochs=4，train_size=27，seed=42。

## 真实逐步轨迹（spreadsheetbench seed42）
| step | action | 候选 selection_hard | best | rollout | doc 字符数 |
|---|---|---|---|---|---|
| 1 | **accept_new_best** | 0.364 | 0.364 | 0.667 | 6451 |
| 2 | reject | 0.364 | 0.364 | 0.667 | 6504 |
| 3 | reject | 0.364 | 0.364 | 0.630 | 9796 |
| 4 | reject | 0.364 | 0.364 | 0.667 | 11731 |

- **step1 之后就卡死**：best 锁死 0.364，连拒 3 步。
- **doc 单调膨胀**：6451 → 11731 字符（+82%），但选择分一步没涨 → "越堆越肥却不变强"。
- 版本快照 token：v0000≈399 → v0004≈3554 tok。
- **训练烧 token：prompt 6,286,468 + completion 550,134 = 6.84M**（单 bench 单 seed）。

## 头对头：SkillStrata vs SkillOpt（同 qwen3.6 target）
| 维度 | SkillStrata（我们） | SkillOpt（竞品） |
|---|---|---|
| 进化对象 | 多节点技能**图**（trace/capability/governance） | **单个**技能文档 |
| 操作算子 | INSERT / MERGE / **SPLIT** / checkpoint / route | 对 doc 加 edit → merge → rank |
| 有没有门 | ✅ val gate | ✅ selection gate（**两家都有**） |
| 本基准进化结果 | 门接受3轮，**真涨** 0.475→0.55→0.60 | 门 step1 后**全拒，卡死** 0.364 |
| 库/doc 随轮 | 图受控生长（34节点可路由） | doc 膨胀 +82% 但分不涨 |
| 测试时载入 | 路由 ~3 技能 = **239 tok/题** | 整个 doc = **~1600 tok/题** |
| 训练 token | 待埋点测 | **6.84M**（单 bench·单 seed） |

## RQ1 能写的结论（诚实版）
1. **"有验证门"不是差异点**——SkillOpt 也是 propose→gate→accept_best。论文别把门当独有卖点。
2. **差异点 = 把技能组织成"可路由的图" vs "一坨单体 doc"**。这带来两个竞品做不到的东西：
   (a) **进化能复利**：图能 INSERT/SPLIT 局部增长，被接受的轮真正叠加（我们 +pt 上行）；单体 doc 改一处牵动全身，本基准上 step1 后门再也接受不了，膨胀但不涨。
   (b) **测试时省 token**：路由最小子图（239 tok）vs 单体全载（~1600 tok），~6.7×。
3. ⚠️ 口径：我方 val(40)/轮、SkillOpt selection(11)/步，不同集，纵轴绝对值不严格可比，**看趋势**（我们上行 vs 它平台）。要做到严格可比需把每轮图存下、同一 280 test 重测（待补）。

## 待补（让这个对比更硬）
- [ ] 量我们 curate 的训练 token（埋点），和 SkillOpt 6.84M 比训练成本。
- [ ] SkillOpt 在 searchqa/alfworld 的 selftrain 轨迹（那里技能更有用，可能它真涨——要诚实并列）。
- [ ] 每轮图快照 + 同 280 test 重测 → 纵轴严格可比的逐轮 test 曲线。
