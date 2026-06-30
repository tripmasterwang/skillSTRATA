# 进化逐轮账本 (EVOLUTION_LEDGER) — 每 step 采纳/抛弃了什么、为什么

> 真实重建自 `runs/curate_fromzero/{curate_history.json, trained_graph.json}`，
> 提取脚本 `extract_evolution_ledger.py` → `evolution_ledger.json`，配图见 `figs/fig_evo_*.png`。
> from-zero / react / 4 轮（r0–r3）。**所有技能名、succ、trials、sim、val 均来自产物，未杜撰。**

终态：**46 mint → 34 deployed / 12 retired；74 边全 `alternative_to`；11 个 verify 门。**

---

## 如何读这三张图（图解，先看这里）

### 图 A：`fig_evo_val_growth.png`（宏观：每轮涨没涨、库怎么长）
- **横轴** = curate 轮次 0–3。
- **红线（左轴）** = val 准确率，点上标数字(0.425→0.475→0.55→0.60)；点下标 **ACCEPT / REJECT**
  —— gate 是否接受该轮。R0 标 REJECT(该轮 12 个全回滚)。
- **浅蓝柱（右轴）** = 累计 deployed 技能数(库大小)：0→12→22→34。
- **每轮顶部灰字** = 该轮事件：`+N mint`(新插入)、`N merged`(合并)、`+N gates`(新挂门)。
- **一句话**：val 单调爬升、库在 gate 把关下增长；R0 那个 REJECT 证明 gate 真会拒绝无效轮。

### 图 B：`fig_evo_lifecycle.png`（微观：每个技能的命运）
- **每一行 = 一个技能**(左侧是技能名)；**横轴 = 轮次**，最右一档 `final graph` = 终图。
- **条的起点** = 该技能哪一轮被 mint；**条延伸到 final** = 它存活进了终图(deployed)。
- **颜色 = 出生轮**：蓝=R1、绿=R2、紫=R3；**红色 xx 块(只在 R0)** = R0 整轮被 gate 拒绝、retired。
- **实心条** = 被实际路由过(右侧标 `succ X (n=trials)`，n=训练 rollout 里被路由次数)。
- **斜纹条 `////`(浅色)** = **真僵尸**：出生后有过 1–2 轮 rollout 机会、却从没被路由到(n=0)。
- **点纹条 `....`(紫)** = **未测量**：R3(最后一轮)出生，之后没有 rollout 去给它记 n，**不能判定有没有用**(见下方 Round 3 / 软肋)。
- **黑钻石 ◆** = 该技能被挂了 verify 门(checkpoint),钻石的横向位置 = 哪一轮挂的。
- **怎么读出故事**：上半实心蓝/绿条 = 真正扛活的主力(n 高);右下点纹紫块 = 最后一轮的未测量技能;
  左下红块 = 第一轮全军覆没;钻石集中在 succ 0.46–0.60 的高频主力上 = 门挂得准。

### 图 C：`fig_evo_content_themes.png`（语义：进化出的内容是什么）
- **每一行 = 一个内容主题**(把 34 个 deployed 技能按正文 body 归的 8 类，人工归类、锚定真实正文)。
- **横轴 = 该主题的总路由次数(trials)** = 这类内容**实际被用了多少**(不是技能个数，是使用量)。条越深越吃重。
- **红色斜纹条(底部)** = "工具调用/执行环境踩坑"类 11 个技能**总 trials=0**(全僵尸/未测量)。
- **和图 B 的关系**：图 B 里 n 最高的那几条实心条(parse_text_range、precompute、targeted_column…)，
  在图 C 里被**按内容归并**成主题条——图 C 是图 B 的"语义聚合视角"。

---

## 进化在进化什么内容（RQ1 正面回答，配图 C）

**一句话：进化出来的不是"领域知识"，而是一批"用 Python/openpyxl 稳健操作 Excel 的防坑套路"。**
34 个 deployed 技能的正文几乎全是"怎么操作表格别翻车"的工程经验，按内容归 8 类、按实际使用量(trials)排：

| 内容主题 | 总 trials | 技能数 | 代表技能正文(真实摘录) |
|---|---|---|---|
| 动态探边界(用 `max_row`，别硬编码行号) | **135** | 7 | *"用 worksheet.max_row 动态确定范围，别写死行数"* |
| **算死值，弃 Excel 公式**(用 Python 算好写静态值) | **114** | 3 | *"在 Python 里算好，把静态值写进单元格……公式脆弱、难验证、类型易错"* |
| 文本解析与稳健匹配 | 102 | 3 | *"'2 to 5' 切分、strip、转 int、算 end-start+1，校验边界"* |
| 安全改行(删/插**倒序**迭代) | 46 | 3 | *"删行要倒着删，正着删会索引位移、漏行"* |
| openpyxl 取值/类型/错误值/日期处理 | 45 | 4 | *"#N/A 常以字符串存，用 str(cell)=='#N/A' 判断"* |
| 公式引用动态构造 | 23 | 1 | *"写公式到多格要按格动态构造引用，否则全锁死同一格"* |
| 聚合/分组计算 | 15 | 2 | *"用 Python dict 分组求和"* |
| **工具调用/执行环境踩坑**(JSON/heredoc/库名) | **0** | 11 | 全是"怎么调 bash/JSON"的 meta 技能 → **全僵尸/未测量** |

**本质**：它把"**qwen 这个 backbone 在 SpreadsheetBench 上反复踩的同几个坑**"，蒸馏成几条"下次别这么干"的操作守则——
把**脆弱写法**(Excel 公式、硬编码行号、正向删行)系统替换成**稳健写法**(Python 死值、动态边界、倒序删除)。

**两根正交支柱**(占 480 trials 的一半)：① "怎么定位操作区域" = 动态范围(135)；② "怎么产出值" = 算死值弃公式(114)。
后者还被 R2 的两次 merge 印证为同源(`python_computation_over_formulas`→`precompute…` sim 0.84)。

**三图互证(回答用户"内容和图的关系")**：
- 图 A 说**进化在涨分**(0.425→0.60)；图 B 说**谁扛活**(少数主力实心条 n 高)；图 C 说**扛的是什么内容**(动态范围 + 算死值两支柱)。
- 串起来：进化涨的那 25pp，主要来自"把 Cell 级操作从脆弱写法换成这两类稳健套路"——
  与 case 分析的 **Cell-Level +30.1pp** 主战场完全吻合。

**新洞察 + 诚实边界**：
- 图 C 底部那条红斑很说明问题：进化也会 distill "怎么用工具(JSON 转义/heredoc/确认库名)"这类 **meta 技能，但 11 个全 0 trials** ——
  对最终答题没帮上，或路由不命中。这是"距离最终奖励远的知识进化不起来"的证据。
- 内容主题为**人工归类**(锚定真实正文，归类脚本与映射见 `plot_evolution_content.py`)，非自动聚类；归类边界有一定主观性。
- 这些是 **spreadsheet 领域 + qwen backbone** 的踩坑经验，非通用智能——换模型/benchmark 坑会变(亦即跨-harness 负迁移的根源)。

---

## Round 0 — 空图首跑，全军覆没（gate 拒整轮）
- agent 在**零技能**图上跑 train，distill 出 **12 个候选**。
- val = **0.425**，未超基线 0.425 → **gate 拒绝整轮 → 12 个全部 retired**。
- 被抛弃的 12 个：Conditional Filtering & Sequential Mapping / Safe Reverse-Order Row Deletion /
  Float-Tolerant Cross-Sheet Matching / Bulk String Index Manipulation via Slicing /
  Explicit Column Index Mapping / Strict Range Mapping & Self-Verification / …（共 12）。
- **洞察**：这些被拒的与后来 R1 留下的**高度同义**（"Safe **Reverse-Order** Row Deletion" ↔ R1 的
  "Safe **Backward** Row Deletion"）。→ **不是知识错，是 val 没涨、gate 保守回滚**；同一知识换轮次/措辞后才通过。

## Round 1 — 第一次涨分，12 个奠基技能
- 插入 **12**，val 0.425 → **0.475** → **ACCEPT**，部署累计 **12**；本轮 **0 门**。
- 奠基主力（后来扛起绝大多数路由）：`parse_text_range_for_inclusive_count`(后 n=83)、
  `precompute_and_write_static_values`(n=73)、`targeted_column_population`(n=70)、
  `Safe Backward Row Deletion`(n=46)。
- 同轮也插入了 2 个从未被路由的 `Verify Library Names Before Execution` / `Use Heredocs…`(n=0)。

## Round 2 — 去重 + 第一次挂门
- 插入 **10**，**合并 2**（两次 merge 全发生在本轮）：
  - `python_computation_over_formulas` → 并入 `precompute_and_write_static_values`（**sim 0.84**）
  - `Backward Iteration for Row Operations` → 并入 `safe_backward_row_deletion`（**sim 0.81**）
- val 0.475 → **0.55** → **ACCEPT**，部署累计 **22**。
- **首次挂 6 个门**，全挂在 succ 0.51–0.60 的高频技能：parse_text_range(succ0.51)、precompute(0.51)、
  targeted_column(0.54)、Dynamic Formula Reference Adjustment(0.57)、openpyxl_max_column(0.57)、
  partial_case_insensitive_matching(0.60)。
- **洞察**：merge 全在这轮，且都是**主导元策略 precompute-in-Python 的同源去重** → 直接解释"边全是 alternative_to"。

## Round 3 — 收敛到 0.60，但库开始膨胀
- 插入 **11**，val 0.55 → **0.60** → **ACCEPT**，部署累计 **34**；再挂 **5 门**（共 **11**）。
- 新挂门：Dynamic Range Detection(succ0.51)、Python Computation Over Live Formulas(0.46)、
  handle_openpyxl_datetimes(0.56)、Dynamic Range Determination(0.60)、Safe Backward Row Deletion(0.57)。
- **R3 的 11 个 trials=0 是"未测量"，不是"没用"（关键澄清）**：
  `heat`(trials) **只在 train rollout 阶段累计**，而 rollout 跑在每轮开头、用上一轮的图——
  本轮新技能在 rollout 之后才插入。所以第 r 轮出生的技能只能在 r+1, r+2… 轮挣 trials；
  **R3 是最后一轮，没有 R4 → 它的技能 trials 必然=0**。但 val 0.55→0.60 的涨幅，正是 gate 把 R3 新技能
  暂时部署后**在 val 集上跑出来的**(涨了才 accept)——它们在自己那轮的 **val 评测**里确实被路由、确实起了作用，
  只是 **val 路由不计入 trials**。所以图上 R3 点纹条标 **"unmeasured"** 而非 "zombie"。
  → 诚实边界：**R3 那 +0.05 无法精确归因到具体技能**(缺 train 侧测量，可能少数有用、可能混入 val 噪声)。

---

## 终图为什么长成这个结构（三句话）
1. **宽平替代池，非层级组合**：74 边全 `alternative_to`。近义技能被反复 distill 成多个节点
   （"Dynamic Range Detection" 出现 **4 次**：Detection / Determination / dynamic_range_detection /
   DynamicRangeDetection），merge 阈值 0.80 偏松没能合并 → 同源化身并联。
2. **主力极少、长尾极瘦**：parse_text_range / precompute / targeted_column / Safe Backward 4 个技能
   trials 46–83，扛起绝大多数路由；其余多为 n=0 的僵尸。呼应"救活题平均只路由 3 个技能"。
3. **门是学出来的、精准挂载**：11 门全落在 trials≥3 且 succ 0.46–0.60 的承重技能上；
   trials=0 或 succ=1.0 的一个门都不挂。

## 诚实软肋（图上已如实呈现，不掩盖）
- **真僵尸 6 个**（不是之前误说的"R3 全是僵尸"）：只有出生后**有过 rollout 机会、仍 n=0** 的才算僵尸 ——
  R1 的 2 个(Verify Library Names Before Execution、Use Heredocs)+ R2 的 4 个(Robust Script Execution、
  Safe_Embedded_Code_Execution、JSON Command Formatting for Bash Tool、dynamic_range_detection)。这 6 个是真"插了没用上"。
- **R3 的 11 个是"未测量"**：缺最后一轮之后的 rollout，无法判定是否僵尸(见 Round 3 澄清)。
  → 启示：评估进化时，**最后一轮的产物需要一次额外 rollout 才能公平判定**，否则 trials=0 会被误读成僵尸。
- **只有准入门、没有退出门（关键结构软肋）**：`curate.py` 主循环里技能变 RETIRED 只发生在 gate 拒绝
  **本轮新插入**那一处；技能一旦活过出生轮就**永久留库**，后续 trials=0 / succ 低也不会被删。
  → 这就是库只增不减(12→22→34)、6 个真僵尸累积的根因。
  注：`lifecycle.py` 其实写好了 `retire_sweep`(retire_floor=0.15)/`cold_prune`/`govern_sweep`，
  但**没接进 curate 主循环**(`prune_cold` 默认 False)，等于"写了退出门没装上"。
  **改进方向(近乎零成本)**：把 `cold_prune`/`retire_sweep` 接进主循环 → 库自我清理僵尸。
- **去重不足**：merge 阈值 0.80 太松，同概念近义技能没合并（Dynamic Range Detection 系列 ×4 个节点）。
- **轮数短**：只 4 轮，r0 还整轮被拒，有效进化只有 r1–r3 三步。
