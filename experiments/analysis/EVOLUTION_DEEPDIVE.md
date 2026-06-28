# 我们自己进化过程的深挖（RQ1 "主要在进化什么" + case 级表现）

来源（真实产物，2026-06-28 逐文件核对）：`runs/curate_fromzero/`
`curate_history.json`（逐轮）/ `trained_graph.json`（46节点终图+governance）/
`test_280/` vs `test_280_noskill/` 的 `eval_official_results.json`（逐题 success）/
`test_280/routes/*.json`（每题实际路由）。所有口径 = 280 held-out subset。

---

## 一、进化产物的结构（不是"加门"，是"攒同质替代策略 + 给薄弱环节挂门"）

终图：**46 技能 mint → 34 部署 / 12 retired（被 merge 吃掉）**，全 atomic 粒度。
governance 63 条 = 46 insert_decision（溯源）+ 2 merge_decision + 3 accept + 1 rejected_edit + **11 checkpoint（=测试时 verify-loop 门）**。

### 发现 1：74 条 capability 边**全是 `alternative_to`**，0 条组合/依赖边
→ 进化发现的是**同一类任务的多种"替代打法"（并联冗余）**，不是搭深层组合层级。
这是诚实的结构画像：SkillStrata 在 SpreadsheetBench 上长成的是"宽而平的策略池 + 路由择一"，
而非"depth-wise 技能组合"。论文别夸成层级组合，要如实说"可路由的替代策略冗余"。

### 发现 2：进化收敛到一个**主导元策略**——"Python 预计算、写静态值、别用脆弱 Excel 公式"
救活主力技能的原始正文高度同源：
- `Python Computation Over Live Formulas`：*"compute the final result in Python and write it as a static value… Avoid embedding complex Excel formulas, as they are fragile, difficult to verify…"*
- `precompute_and_write_static_values`：*"compute the result in Python and write the static value directly… avoids the fragility of complex Excel formulas, ensures exact control over data types…"*
- `parse_text_range_for_inclusive_count`：*"split on delimiter, strip, int, end-start+1, validate edge cases…"*

→ 这正解释了为什么边全是 `alternative_to`：它们是**同一个制胜策略的多种措辞/特化**。
"主要在进化什么" 的真答案 = **把一条反复奏效的元策略，蒸馏成多个可路由的具体化身**。

### 发现 3：门（verify-loop checkpoint）**精准挂在"高频但成功率只有 ~50% 的不靠谱技能"上**
11 个 checkpoint 的守护成功率全落在 **0.46–0.60**，且挂的都是高 trials 的高频技能：
`parse_text_range`(succ0.51/53trials)、`precompute_static`(0.51/53)、`python_computation`(0.46/41)、
`dynamic_range_detection`(0.51/51)、`safe_backward_row_deletion`(0.57/46)、`targeted_column_population`(0.54/46)…
→ 门不是均匀加的，是**算法自动把 retry 安全网挂在最薄弱的承重环节**。
部署的 34 技能里 **62%(21个) 正文已自带验证语义**——进化同时在让技能"内生自检"。

> 闭环（RQ1 一句话）：**进化发现"高价值但成功率掷硬币"的元策略 → 蒸馏成多个可路由化身 → 自动给它们挂 verify 门 → 测试时门把掷硬币的那一半救回来。** 这是 SkillOpt 单体 doc 给不了的：它没有"按技能粒度挂门 + 路由择一"的结构。

---

## 二、case 级表现（280 held-out，skill-react vs noskill-react）

总账：**noskill 86/280=30.7% → skill 157/280=56.1%（+25.4pp）**。逐题拆开：

| 类别 | 题数 | noskill | skill | Δ |
|---|---|---|---|---|
| **救活**（✗→✓） | **85** | — | — | 主增量 |
| 拖垮（✓→✗，软肋） | **14** | — | — | 负面 |
| **净提升** | **+71** | | | |
| 都对 | 72 | | | |
| **硬骨头**（都错，RQ3 改进空间） | **109 (39%)** | | | |

### 发现 4：增益**极不均匀，主战场是 Cell-Level**
- **Cell-Level Manipulation：22.3% → 52.3%（+30.1pp）**，n=193 ← 技能在这里爆发
- Sheet-Level Manipulation：49.4% → 64.4%（+14.9pp），n=87
→ 和进化出的技能完全对得上：救活的 85 题里 66 题是 Cell-Level，路由的全是
`python_computation / parse_text_range / precompute`——**Cell 级的"算好再写"正是这批技能的拿手**。
Sheet 级 noskill 本来就有 49%（结构性操作 LLM 自己会），技能锦上添花。

### 发现 5：救活题平均只路由 **3.0 个技能/题**，且高度集中
top 命中：Python Computation Over Live Formulas 62×、parse_text_range 48×、precompute 37×、
Dynamic Range Detection 24×、Safe Backward Row Deletion 19×。
→ **少数几个技能扛起绝大多数救活**（长尾很瘦），呼应"省 token"（每题只载 ~3 技能）。

### 发现 6（软肋，必须诚实写）：
- **拖垮 14 题**：技能引入了 8 Cell + 6 Sheet 的净负面（路由进了不该用的策略 / 门没拦住）。
- **硬骨头 109 题（39%）技能完全没救**：Cell 84 + Sheet 25。这是 RQ3 的改进面——
  当前进化池对这部分要么没蒸馏出对的策略，要么路由没命中、要么门修不动。

---

## 三、这次深挖给三个 RQ 补的硬证据
- **RQ1（在进化什么）**：宽平替代策略池（全 `alternative_to`）+ 一个主导元策略的多化身 + 门精准挂薄弱环节。**不是"加门"那么简单，是"发现元策略→蒸馏化身→挂门兜底"三步闭环。**
- **RQ2（哪个组件承重）**：门挂在 succ 0.46–0.60 的技能上 → verify-loop 的边际价值应集中在这批；abl_noverify 跑完即可量化（预览 143/228≈63% running）。
- **RQ3（还需改进）**：109 题硬骨头 + 14 题被拖垮 = 38% 的题进化没帮上或帮倒忙，软肋清晰。

## 待补
- [ ] 救活/拖垮/硬骨头三组的**逐题清单**导出（给论文做 case study 附录）。
- [ ] abl_noverify 跑完：对"挂门的 11 个技能所覆盖的题"单独算 verify-loop 净贡献。
- [ ] 把"主导元策略 precompute-in-Python"做成一张技能正文聚类图（佐证 alternative_to 同源）。
