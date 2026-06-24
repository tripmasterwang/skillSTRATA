# Paper Brief — SkillLEGO (stratified three-layer skill system)

> 据 `skillos_proposal.md` + 已实现代码（`skillos/`, `sim/`）+ 模拟实验结果（`results/RESULTS.md`）填写。
> 配套 `FINAL_PLAYBOOK.md` 使用。
>
> ⚠️ **两条必须先告知作者的 caveat（贯穿全 brief）**：
> 1. **命名 + 收编策略**：方法名 = **`SkillLEGO`**（2026-06-21 定；原 "SkillOS" 撞 arXiv 2605.06614）。注意三篇 **preprint** 已做"技能图+依赖路由+split"：SkillGraph-RL(2605.12039)、SkillGraph-ToolSeq(2604.19793)、Graph-of-Skills(2604.05333)，见 `external/competitors/`。**策略：不回避、用更高阶的三层 Skill Strata 框架把它们收编为特例**（它们=单层 skill 图+只路由现成技能；我们=三层系统 + 域内路由 + 域外乐高拼装）。投稿前仍需对 "SkillLEGO" 查新 + 对这几篇 head-to-head(Part 4)。
> 2. **实验目前是确定性模拟（simulation），不是真实 LLM benchmark**。所有数字来自 `sim/` 合成 harness（`results/main.json` / `ablations.json`）。真实 Trace2Skill/SpreadsheetBench 实跑尚未做（接口已留，见 Part 11）。**凡模拟数字一律标 `[SIM]`**；投 ORAL 必须补真实 benchmark。

---

## Part -1：Paper Root 与文件层级约定

### -1.1 $PAPER_ROOT 定义
- **本 brief 的 $PAPER_ROOT**：`/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/projects/skillSTRATA/`（即本项目目录；Part 12 file 列相对它）。

### -1.2 目录布局约定
- [x] **Custom**（当前是代码仓库，paper 资产待生成）：
  - `skillos/` → 引擎源码（method 实现，Part 11 引用）
  - `sim/` → 实验 harness（experiments 实现）
  - `results/` → `main.json` / `ablations.json` / `RESULTS.md`（raw results，paper-claim-audit 用）
  - `figures/` → **[待建]** 论文图（framework / ablation 曲线）尚未绘制
  - `tables/` → **[待建]** 由 `results/*.json` 生成的 `.tex` 表尚未生成
  - `external/` → 三个参考仓库 + arXiv 源码（建 `.bib` / 对照用）

### -1.3 自检
- Part 12 的 `figures/`、`tables/` 资产**目前不存在**（标 `[待生成]`）；正式交 `paper-from-brief` 前需先跑 `paper-figure` 生成，再回填真实文件名 + label。**现在不要让下游 skill 直接编译。**

---

## Part 0：故事定位 🔴 P0

### 0.1 一句话痛点
- **问题**：trace-to-skill 的演化产物是**一个技能（或一张单层技能图）**，而不是一个能在推理时**重组自身**的系统——遇到没有现成合适技能的**域外任务**就无能为力。（≤10 词：*evolve a system, not a skill; assemble for OOD*）
- **为什么现在重要**：绑当下热点 = **self-evolving / lifelong LLM agents** + **agent skill library** + **test-time adaptation / context budget**。

### 0.2 现有范式（把竞品收编为特例，不回避）
- **Paradigm I — monolithic skill**：trace→skill 层级合并成**一个大技能文档**（**Trace2Skill** / **SkillBrew** / **SkillOpt**）。缺陷：skill bloat、全量加载、negative transfer。
- **Paradigm II — single-layer skill graph + retrieval**：把技能组织成**单层图**、推理时检索/组合**现成技能**（**SkillGraph-RL** 2605.12039、**Graph-of-Skills** 2604.05333；均 **preprint**，见 `external/competitors/`）。缺陷：(i) 图是**单层**（只有技能节点，无 trace / 治理层）；(ii) 推理时只**路由/组合已固化技能**——库里没合适技能时失效；(iii) 演化靠 **RL**（SkillGraph-RL）或**不演化**（GoS）。
- **双范式共同盲区**：产物是"一个 skill / 一张单层图"，**没有把执行证据(trace)→能力(skill)→治理(governance)组织成一个递进的三层系统**，也**没有"域外任务时用子部件当场拼装新技能"的能力**。
- **Paradigm III**：无——我们不另立方向，而是用一个**更高阶、更通用的三层系统把 Paradigm II 收编为特例**（它们 = 我们"域内直接路由"那一半）。

### 0.3 我们的核心 reframe（8 招选 ≥1）

| 招式 | 选择 | 备注 |
|---|---|---|
| AgentFlow：模块化命名（多组件协调） | [x]（主）| **SkillLEGO**：把执行证据/能力/治理 curate 成三层 **Skill Strata**（trace→capability→governance），推理时用其子部件**拼装**适配技能 |
| MemGen：涌现 / 层级 framing | [x]（次）| 三层递进借复杂网络 **hierarchical multilayer network**（底层 raw 证据、上层 operate-on-top）；OS 式生命周期 **curate**（非梯度训练） |
| 其余 6 招 | [ ] | — |

> **核心 reframe（一句话）**：别人 evolve 出**一个 skill / 一张单层图**；我们 **curate 出一个三层 Skill Strata 系统**，并在推理时像乐高一样——**域内直接组合现成技能（= 竞品做的，被收编为特例），域外用三层里的子部件当场拼出一个/几个适配技能**。**核心叙事词**：*curate a system, not a skill* / *assemble skills like LEGO at test time*。
> **三层图命名**：**Skill Strata**（备选 Stratified Skill Graph / Skill Stack）。**离线**统一用 **curate**（不用"train"——我们 no-grad、no-RL）。

### 0.5 项目类型 🔴 P0
- [x] **A. 纯 method paper**：核心 = (1) **curate 一个三层 Skill Strata 系统**（非单个 skill）；(2) test-time **LEGO assembly**——域内路由现成技能、域外用子部件当场拼装。在 Trace2Skill 流水线上替换 monolithic merge。
  - 说明（遵守规则 3.0.5）：SkillLEGO 也是可运行 **system/library**，但**不把"框架/可插拔"当标题卖点**；主贡献种类 = method。

### 0.6 章节配置（opt-in overrides）🟢 P2
| 字段 | 默认 | 本文 |
|---|---|---|
| `preliminary_present` | yes | 保持默认（独立 §Preliminary 定义 skill graph 形式化）|
| `background_subsection_for_common_flaw` | no | [x] **yes** — 升格 §Background "Skill Bloat vs. Skill Governance" 子节（命名共同缺陷）|
| `related_work_position` | before-method | 保持默认 |
| `analysis_section_present` | no | 保持默认（机制分析揉进 §Experiments）|
| `subsection_title_style` | claim-title | 保持默认（实验子节用结论句）|
| `method_section_name` | Method | 保持默认 |

---

## Part 1：Title

### 1.1 Method 缩写名
- **主名：`SkillLEGO`** ✅（2026-06-21 选定）。**语义钉死**：测试时即使没有现成最合适的技能，也能用三层 **Skill Strata** 的子部件（trace 证据 + 原子技能）**当场拼出一个/几个适配技能**——是"缺件当场组装"，**不是"组合现成积木"**。
- 三层图系统名：**Skill Strata**（stratified three-layer skill graph: trace / capability / governance）。
- ⚠️ 阴影：已有 **LEGO（2604.23355）** 用过 "LLM skill + composable"；靠副标题把语义钉在 *test-time assembly / casting missing skills* 区分。

### 1.2 Evocative 词候选（决策记录 — 已选 SkillLEGO）
- 曾考虑：SkillLoom（织造）/ SkillAtlas（图谱+导航）/ SkillForge（锻造拆分）/ GraphSkill / SkillFabric。
- **最终选 `SkillLEGO`**：钉死语义为 *test-time assembly*（缺件当场拼），与竞品的 *retrieve/compose existing skills* 形成对比。曾考虑 SkillGraph（撞 2605.12039，弃）。

### 1.3 标题结构（5 选 1）
- [x] **D. 缩写命名**："<NewName>: A Hierarchical Graph-Governed Skill System for LLM Agents"（沿用 proposal 副标题结构）
- 备选 [x] **A. 动词开头**："Refactoring Monolithic Skills into a Governed Skill Graph"

### 1.4 候选 title（主名 SkillLEGO）
1. **SkillLEGO: Curating a Stratified Skill System and Assembling Skills at Test Time for Self-Evolving Agents** ✅ **采用**
2. **SkillLEGO: From a Single Skill to a Three-Layer Skill System that Assembles Itself for Out-of-Domain Tasks**
3. **Assemble, Don't Just Retrieve: Test-Time Skill Composition from a Stratified Skill Graph**
4. （强调收编）**Beyond Single-Layer Skill Graphs: Routing In-Domain and Assembling Out-of-Domain**

---

## Part 2：Abstract

### 2.1 Hook 数据
- 大领域名：LLM agents（self-evolving，从轨迹中累积技能）。
- 大终点词：**self-evolving / lifelong skill learning**。
- 外部学科类比（可选）：**operating system**（技能的存储/调度/回收）+ **software refactoring**（把单体技能拆分为模块）。

### 2.2 范式数据
- Paradigm I：trace→skill 把经验**层级合并成单体大文档**（Trace2Skill / SkillBrew），bloat + 全量加载。
- Paradigm II：扁平技能库 + top-k 检索，**无依赖/组合/治理结构**。
- 双范式**共同盲区**：技能演化的终点被默认成"更大、更全的文档"，缺**可拆分、可组合、可路由、可治理**的模块化技能系统。（可命名新概念："**Skill Bloat**" / "**ungoverned skill accumulation**"）

### 2.3 Method 核心数据
- Method 名 + 类型词：**SkillLEGO** = curate 一个三层 **Skill Strata** 系统 + 推理时按需拼装技能（替换 Trace2Skill 的 monolithic merge）。
- **核心组件 3 个**：
  1. **Skill Strata（三层图）** — trace graph（执行证据 + 子能力共现）/ capability graph（模块技能 + depends_on/composes_with/conflicts_with）/ governance graph（split/merge/retire/route 规则）。借复杂网络 **hierarchical multilayer network**（底层 raw 证据、上层 operate-on-top）。
  2. **Curate（离线，no-RL）** — 7 算子 INSERT/UPDATE/**SPLIT**/MERGE/LINK/RETIRE + propose-then-verify 门 + 热度生命周期，把三层图 **curate** 出来（非梯度训练、非 RL）。
  3. **LEGO assembly（推理）** — **域内**：ROUTE 现成技能的最小可执行子图（= 单层图方法做的，被收编为特例）；**域外**：从三层子部件（trace 证据 + 原子技能）**当场拼出一个/几个适配技能**（test-time synthesis）。
- **核心叙事词**：①*curate a system, not a skill*；②*assemble skills like LEGO at test time*。
- B 型集成算法：N/A（A 型）。

### 2.4 实验数据 highlight 🔴 P0 — **全部 `[SIM]`，待真实 benchmark 替换**
- 实验规模 `[SIM]`：确定性模拟 harness，**8 seeds × 400-task heterogeneous/OOD 流 × 4 领域合成技能宇宙**；6 baseline + 6 消融。**[真实版需：≥3 benchmark（取 §7.2 的 6 个主流：ALFWorld / SpreadsheetBench / ScienceWorld …）× ≥2 backbone]**
- 主结果 highlight（带 baseline 名）`[SIM]`：
  - vs **Trace2Skill**（单体全量加载）：success **0.704 vs 0.574**（+13pp），token cost **365 vs 780**（≈2.1× fewer），negative transfer **0.105 vs 0.219**（≈2.1× lower）。
  - vs **Flat Skill Bank**（top-k 检索）：success **0.704 vs 0.555**（+15pp），routing precision **0.391 vs 0.317**。
  - 倍数表达：≈**2× fewer loaded tokens** 且 **success 最高**。
- 次维度 highlight `[SIM]`：routing precision 最高（0.391，约为 flat 的 1.2×、monolith 的 6×）。
- 效率双赢句 `[SIM]`：多技能方法中 **token cost 最低**（365）且 **success 最高**（0.704）→ *最高成功率 + 最低加载成本*。
- 跨域 / 泛化 highlight `[SIM]`：**OOD transfer gain 最高**（+0.256，相对 No-Skill 基线的 OOD success 提升），高于 flat（+0.119）与 Trace2Skill（+0.163）。

### 2.5 句 7 "意外发现钩" 🟡 P1
- [x] **C. 反直觉发现** `[SIM]`：消融显示 **SPLIT 与 ROUTE 是最大贡献项**（去掉各掉 0.15 / 0.18 success；去掉 SPLIT 还使 token 成本暴涨 ~6.6×），而 governance/validation 是**互补安全网**——单独移除影响小、**同时移除**才显著拉低 late-stream 成功率与稳定性。即"技能系统的收益主要来自**拆分与路由**，而非堆更多技能"。

---

## Part 3：Introduction

### 3.1 段 1 大环境
- 开篇句风格：[x] 大趋势 + ref dump（LLM agents 从轨迹自我演化技能）。
- 段 1 ref（≥5–7，真实文件均在 `paper-reading/` 或 `external/`）：`trace2skill`(Trace2Skill 2603.25158), `skillopt`(SkillOpt 2605.23904), `skillbrew`(SkillBrew 2605.29440), `evoskill`(EvoSkill 2603.02766), `gmemory`(G-Memory 2506.07398), `memoryos`(MemoryOS 2506.06326), `skillos_ouyang`(SkillOS 2605.06614)。
- 当下最热 model 名：Qwen3.5（Trace2Skill 用）、GPT/Claude 系（agent 主干）。

### 3.2 段 2 范式对立
- **段 2 引子 / 路线转向动机**：trace→skill 方法默认 "skill 越完整、merge 越多越强"，短期成立，但长 horizon 下 → **单体文档膨胀 + local rules 污染**，故需**从"做大文档"转向"治理模块化技能"**。〔substantive motivation，保留。〕
- Paradigm I 代表 ref + 缺陷：`trace2skill`, `skillbrew`, `skillopt`（monolithic merge / curation — bloat、全量加载、negative transfer）。
- Paradigm II 代表 ref + 缺陷：flat skill bank / top-k 检索类（无依赖结构、漏装前置、检索精度低）。
- 共同缺陷命名候选：**"Skill Bloat"** / **"ungoverned skill accumulation"**（升格 §Background 子节，见 0.6）。

### 3.3 段 3 第三方向 + RQ
- 第三方向代表 ref：图式记忆组织（`gmemory`）+ OS 式生命周期（`memoryos`）—— 但它们做的是 **memory**，不是 **skill 治理 + routing**。
- 第三方向自身缺陷：(i) G-Memory 节点用 raw-task-string，无稳定 ID、无 skill 拆分；(ii) MemoryOS 只对 memory 做 promotion/eviction，无 skill 依赖路由；(iii) 均未把"refactor-style SPLIT + dependency-aware ROUTE"作为一等算子。
- **RQ 核心反问**（≤30 词）：*Should skill evolution end in ever-larger documents, or in a governable, composable, routable skill graph?* （用 obsbox）
- 外部学科类比：**operating system**（存储/调度/回收）+ **software refactoring**（拆单体）。
- 类比核心概念词："skill graph"、"minimal executable subgraph"、"skill lifecycle"。

### 3.4 段 4 方法 + callback
- 方法类型词：hierarchical / graph-governed / lifecycle-aware。
- 组件 + 动词角色：**organize**（三层图）→ **govern**（SPLIT/MERGE/LINK/RETIRE + verify 门）→ **route**（激活最小可执行子图）。
- 显式 callback："Unlike (I) monolithic merge and (II) flat top-k retrieval, ours **splits monoliths into a governed graph and routes a minimal executable subgraph**。"

### 3.5 段 5 Empirical Highlights 🔴 P0（全部 `[SIM]`）
- 5.1：8 seeds × 400-task heterogeneous/OOD 流 × 4 域合成技能宇宙；6 baseline + 6 消融。**[真实版待补 benchmark]**
- 5.2 vs 最热 baseline（Trace2Skill）：success **+13pp**、token **≈2.1× fewer**、negative transfer **≈2.1× lower**。
- 5.3 次维度：routing precision 最高（≈monolith 的 6×）。
- 5.4 效率双赢：多技能法中 token 最低且 success 最高。
- 5.5 泛化：OOD transfer gain 最高（+0.256）。
- 5.6 "More importantly" 钩：消融揭示 **SPLIT/ROUTE 主导收益**，治理/校验是互补安全网（反直觉，见 2.5）。

### 3.6 段 6 Contributions（threefold）
- **Contrib 1 — 系统级**（We propose）：**SkillLEGO**，把 trace→skill 的产物从"一个 skill / 单层图"升级为 curate 出的**三层 Skill Strata 系统**（trace/capability/governance），把已有单层图方法统一收编为特例。
- **Contrib 2 — 推理级**（We introduce）：**test-time LEGO assembly**——域内路由现成技能、**域外用三层子部件当场拼装新技能**、无需 RL 重训；这是单层图 / 检索类方法所缺。
- **Contrib 3 — 效果**（We demonstrate）`[SIM]`：模拟 harness 上取得**最高 success + 最低 token + 最低 negative transfer + 最高 routing precision + 最高 OOD gain**；held-out 实验证明域外拼装补回 **~54% 覆盖 gap**。**[真实 benchmark 待补]**
- Contrib 4 — release（可选）：开源 `skillos/` 引擎 + `sim/` harness（已实现，见 Part 11）。
- 核心条↔RQ：①↔§Method+§Preliminary；②↔§M3+§E5(TTA)；③↔§E2 主结果+§E3 消融。

---

## Part 4：Related Work（真实引用，按方向分类）🔴 P0

> ⚠️ 诚实标注：下表中 **Trace2Skill / G-Memory / MemoryOS** 我已**逐行精读源码**，描述可靠；其余 `paper-reading/` 论文**仅依据标题 + 摘要级信息**，"一句话做了啥"为**保守推断，标 `[据标题/摘要，待核实原文]`**，写论文前需 `/research-lit` 或读 PDF 确认。**最关键：`skillos_ouyang`（同名 SkillOS）必须读全文做 head-to-head 区分。**

### 4.1 三个 subsection 主题
- **Direction A（核心机制对齐）= Trace-to-Skill / Self-Evolving Skill Libraries**：从轨迹蒸馏技能并持续 update/merge/curate（Trace2Skill, SkillBrew, SkillOpt, EvoSkill, SkillOS-Ouyang …）。我们落在此线但**做图治理 + 路由**。
- **Direction B（building block）= Hierarchical Graph Memory & OS-style Lifecycle**：G-Memory（层级图记忆 + k-hop 检索）、MemoryOS（热度/promotion/eviction 生命周期）。我们**借其图组织 + 生命周期框架**，迁移到 skill 治理。
- **Direction C（可选，应用/背景）= Agent Skill Composition / Evaluation**：SkillComposer, SkillCAT, OpenSkillEval, SkillsOnTheFly 等组合/评测工作。

### 4.2 每个 subsection 的分类细节
#### Direction A
- 分类 3 类：(a) **monolithic merge**（Trace2Skill, SkillBrew）；(b) **optimization/curation gate**（SkillOpt）；(c) **同名 SkillOS-Ouyang = skill curation**。
- 我们落在：跨越三类——**用图治理替换 merge，用 routing 替换全量加载**。
- 与 prior 的 **2 差异维度**：① 一等的 **refactor-style SPLIT**（无人实现）；② **dependency-aware ROUTE = 最小可执行子图**（非 top-k 文本）。

#### Direction B
- 分类 2 类：(a) **graph memory**（G-Memory）；(b) **OS lifecycle memory**（MemoryOS, 及 MemOS `li2025memos`）。
- 差异维度：它们治理 **memory**；我们治理 **skill**，并新增 SPLIT + 依赖路由；用**稳定节点 ID** 修正 G-Memory 的 raw-task-string 节点。

#### Direction C
- 用于 §Intro 背景 + §Experiments baseline 选择。

### 4.3 Differentiation 视觉武器（A/B 二选一）
- [x] 选 **B. Differentiation Table**（布尔属性差异，≥4 维）：
  - 维度：`modular skills?` / `dependency edges?` / `refactor SPLIT?` / `dependency-aware routing?` / `lifecycle governance?`
  - 竞品行：Trace2Skill(单体merge) / Flat skill bank / SkillOpt(prune+gate) / SkillBrew(curation) / G-Memory(graph,但 memory) / **Ours**。
- (可选) R32 "first to"：据我们所知，**首个把 refactor-style SPLIT + dependency-aware subgraph routing 作为一等技能治理算子**的系统。（⚠️ 需先排除 skillos_ouyang 已做。）

### 4.4 行业现状 / Landscape 🔴 P0
- **闭源前沿**：N/A（本工作非比拼前沿模型，而是技能治理机制）。
- **开源对手**：Trace2Skill（`Qwen-Applications/Trace2Skill`）、SkillOpt、SkillBrew、SkillOS-Ouyang。
- **现有开源基建**（建在其上，含 commit）：
  - **Trace2Skill** `Qwen-Applications/Trace2Skill` @ commit `3d0b52a`（base 流水线；我们替换其 `run_reduce_phase`）。
  - **G-Memory** `bingreeky/GMemory` @ commit `7b581c5`（图组织参考）。
  - **MemoryOS** `BAI-LAB/MemoryOS` @ commit `1d71706`（生命周期参考）。
- **空白点**：技能演化普遍止于"更大文档"或"扁平库"；无人把技能组织成**可拆分/可路由/可治理的图**。

### 4.4.bis 基建继承与扩展点
- N/A（A 型）。若改 B 型 framework：继承 Trace2Skill 的 ReAct agent + LLM client + 评测，新增三大扩展 = 图存储 / 生命周期治理 / 依赖路由（见 `CODE_DESIGN.md`）。

### 4.5 参考文献清单（真实条目 + 一句话）🔴 P0
> cite-key 暂定；正式投稿需用 `download_arxiv_latex.sh` 抽各文 `.bib` 或 `/semantic-scholar` 核验后落 `references.bib`。

**方向 A — Trace-to-Skill / Self-Evolving Skills：**

| 简称 | cite-key | arXiv / 出处 | 一句话该工作做了啥 | 用在哪 |
|---|---|---|---|---|
| Trace2Skill | `trace2skill` | 2603.25158 | **[已精读]** 从轨迹并行抽 patch、层级合并成单体技能目录；测试时全量加载 SKILL.md | A 主 / Paradigm I / base |
| SkillOS-Ouyang | `skillos_ouyang` | 2605.06614 | **[同名！待精读]** "Learning Skill Curation for Self-Evolving Agents"——学技能 curation | A / **命名+novelty 区分** |
| SkillOpt | `skillopt` | 2605.23904 | [据标题/摘要，待核实] 带量化 validation gate 的技能优化（Microsoft） | A 优化/门控 |
| SkillBrew | `skillbrew` | 2605.29440 | [据标题/摘要，待核实] 技能 curation/酿造式整理 | A curation / Paradigm I |
| EvoSkill | `evoskill` | 2603.02766 | [据标题/摘要，待核实] 技能进化 | A self-evolving |
| SkillEvolver | `skillevolver` | 2605.10500 | [据标题/摘要，待核实] 技能演化器 | A self-evolving |
| RawExp2Skill | `rawexp2skill` | 2605.23899 | [据标题/摘要，待核实] 原始经验→技能消费 | A trace→skill |

**方向 B — Graph Memory & OS Lifecycle：**

| 简称 | cite-key | arXiv | 一句话该工作做了啥 | 用在哪 |
|---|---|---|---|---|
| G-Memory | `gmemory` | 2506.07398 | **[已精读]** 三层层级图记忆（insight/query/interaction）+ k-hop 双向遍历 | B 主 / 图组织来源 |
| MemoryOS | `memoryos` | 2506.06326 | **[已精读]** OS 式分层记忆 + 热度 H=α·N+β·L+γ·R 的 promotion/eviction | B 主 / 生命周期来源 |
| MemOS | `memos` | (paper-reading 外，需补) | [待核实] 记忆增强生成的"OS" | B OS framing |

**方向 C — Skill Composition / Evaluation（可选）：**

| 简称 | cite-key | arXiv | 一句话该工作做了啥 | 用在哪 |
|---|---|---|---|---|
| SkillComposer | `skillcomposer` | 2606.06079 | [据标题，待核实] 技能组合 | C 组合 |
| SkillCAT | `skillcat` | 2606.13317 | [据标题，待核实] 技能 catalog/分类 | C |
| OpenSkillEval | `openskilleval` | 2605.23657 | [据标题，待核实] 技能评测基准 | C 评测 |
| SkillsOnTheFly | `skillsonthefly` | 2605.16986 | [据标题，待核实] 在线即时技能 | C |

> ⚠️ 表内除 4 条 `[已精读]` 外，**cite-key 与"做了啥"均待核实**；建 `references.bib` 前必须逐条确认，否则 citation-audit 会挂。

---

## Part 5：Preliminary

### 5.1 主变量定义
- **核心调控对象**：技能库的**组织结构**——从单体文档 → 技能图。
- **主变量符号**：技能图 $\mathcal{G} = (\mathcal{V}, \mathcal{E})$，三层 $\mathcal{G}_{\text{trace}}, \mathcal{G}_{\text{cap}}, \mathcal{G}_{\text{gov}}$；技能节点 $v$ 带状态 $\text{status}(v)\in\{$candidate,validated,deployed,retired$\}$。

### 5.2 前人方法在主变量上的取值
- Paradigm I（monolithic）：$\mathcal{G}$ 退化为**单节点大文档** $d$，无边；加载 = 全量 $d$。
- Paradigm II（flat bank）：$\mathcal{V}$ = 一堆独立技能、$\mathcal{E}=\varnothing$；加载 = top-k 检索子集。

### 5.3 我们方法在主变量上的取值
- 我们：$\mathcal{E}$ 含 depends_on/composes_with/conflicts_with/parent_child 等；加载 = **依赖闭包子图** $\text{closure}(\text{seeds})$（最小可执行集），而非全量或 top-k。

### 5.4 核心概念命名
- evocative 概念词：**"minimal executable skill subgraph"**（最小可执行技能子图）。
- 形式化定义（1 句）：给定任务 $t$，ROUTE 返回 $\mathcal{S}^\star = \text{closure}_{\text{depends\_on}}(\text{seed}(t)) \setminus \text{blocked}$，即种子技能在依赖边下的传递闭包减去被治理图屏蔽的节点。

### 5.5 (B 型) 集成算法清单
- N/A（A 型）。

---

## Part 6：Method

### 6.0 §Method subsection 清单声明（author-declared）🟡 P1

| § | 子节标题 | 风格 | 主要内容 | 主 figure/table |
|---|---|---|---|---|
| §M0 | Overview: Curate a Stratified Skill System, Assemble Skills at Test Time | claim-title | 6.2 narrative + 6.1 framework fig | fig:framework |
| §M1 | Skill Strata: a Three-Layer Skill Graph (trace / capability / governance) | descriptive | 6.4 Component 1 | fig:framework |
| §M2 | Curating the Strata: Lifecycle Operators (SPLIT/MERGE/LINK/RETIRE + verify gate), no RL | claim-title | 6.4 Component 2 + 6.3 隐喻表 | alg:ops |
| §M3 | Test-Time LEGO Assembly: In-Domain Routing + Out-of-Domain Synthesis | claim-title | 6.4 Component 3 | fig:routing |
| §M4 | Properties / Complexity & Trace2Skill Integration | descriptive | 6.6 | — |

### 6.1 Framework Figure 骨架 🔴 P0 — **[图待绘制]**
- 数据流向：左 = task trajectories → **curate**：extract patches → split/merge/link → **三层 Skill Strata**（trace 底 / capability 中 / governance 顶）→ 右 = **推理 LEGO assembly**：域内 ROUTE 现成技能 / 域外从子部件 synthesize → executor。
- frozen 模块（灰）：LLM backbone、Trace2Skill ReAct agent。
- 我们的组件（彩）：三层 Skill Strata、curate 算子、LEGO assembly（均 **no-grad / no-RL**，符号系统）。
- 关键变量：三层 $\mathcal{G}_{\text{trace/cap/gov}}$、技能节点 $v$、子图 $\mathcal{S}^\star$、合成技能、热度 $H(v)$。
- 草图文件路径：**[待生成]** 建议 `figures/framework.pdf`；可由 `paper-figure` 据 `CODE_DESIGN.md` 的模块图生成。

### 6.2 §M0 Narrative 段所需
- 外部学科 framing：**hierarchical multilayer network**（复杂网络，底层 raw 证据 / 上层 operate-on-top）+ **LEGO assembly**（缺件当场拼）。
- 权威引用：multilayer network（如 Boccaletti et al. 2014, *The structure and dynamics of multilayer networks*）/ refactoring（Fowler, *Refactoring*）—— **[待补准确文献项]**。
- 主张句："SkillLEGO curates a three-layer skill system and, at test time, assembles task-fit skills from its sub-parts like LEGO — routing existing skills in-domain and casting missing ones out-of-domain。"

### 6.3 工程动作 → 隐喻词对照表 🟢 P2

| # | 工程动作 | 隐喻词 |
|---|---|---|
| 1 | 把大技能拆成原子技能 | **SPLIT / refactor** |
| 2 | 合并冗余技能 | **MERGE / consolidate** |
| 3 | 建依赖/组合/冲突边 | **LINK / wire** |
| 4 | 选最小可执行子图 | **ROUTE / activate** |
| 5 | 低效技能退役 | **RETIRE / evict** |
| 6 | 候选→部署的校验门 | **promote / propose-then-verify** |
| 7 | 屏蔽有害技能 | **govern / quarantine** |
| 8 | 热度调度 | **heat / schedule** |

### 6.4 每个 Component 的细节

#### Component 1 — Three-Layer Skill Graph $\mathcal{G}$
- **组件类型**：[x] **④ hard_rule**（确定性符号结构，无梯度）。
- 架构：networkx 有向图 ×3（trace/capability/governance）+ 稳定 slug ID（修正 G-Memory raw-string）。
- 输入/输出：输入 = Trace2Skill `Patch`/`PatchEdit`；输出 = 技能节点 + 跨层边。
- scoring/decision 公式：依赖闭包 $\text{closure}(S)=\bigcup$ 传递 depends_on。
- 数据来源：轨迹 → patch（沿用 Trace2Skill MAP 阶段）。

#### Component 2 — Lifecycle Governance Operators
- **组件类型**：[x] **④ hard_rule**（INSERT/UPDATE/SPLIT/MERGE/LINK/RETIRE 为符号算子）+ propose-then-verify 门。
- scoring/decision：(a) `should_split(v)` = body 大 ∧ task_types 异构；(b) 热度 $H(v)=\alpha\,N_{\text{visit}}+\beta\,\text{coverage}+\gamma\,e^{-\Delta/\tau}$（源自 MemoryOS）；(c) verify 门 = 接受当且仅当 success 不降且 token/negative-transfer 下降。
- 训练算法：no-grad（纯符号 + replay 校验）。
- 数据来源：replay/validation 任务集触发。

#### Component 3 — Inference: Dependency-Aware Routing (ROUTE) + Test-Time Skill Synthesis
- **组件类型**：[x] **④ hard_rule**（推理时确定性子图选择 + 当场合成）。
- **第一步 ROUTE**：$\mathcal{S}^\star=\text{closure}_{\text{depends\_on}}(\text{seed}_k(t))\setminus\text{blocked}(\mathcal{G}_{\text{gov}})$；种子用与 baseline **同一** retriever（BM25）以隔离图的贡献。
- **第二步 test-time skill synthesis（推理阶段，非主卖点、是机制补全）**：当任务与历史高度重叠但不全同、某需要的子能力**尚无固化技能**时，沿 capability→trace 下钻该次激活技能的 trace 共现证据（`trace_cooccurring`），把缺口能力**当场拼成一个 ephemeral 技能**注入 $\mathcal{S}^\star$，用完即弃。触发只用**历史** trace 统计 + 当前种子，不看当前任务 ground-truth（非 oracle）。形式化：$\mathcal{S}^\star \leftarrow \mathcal{S}^\star \cup \text{synth}(\text{cooc}(\mathcal{S}^\star) \setminus \text{deployed})$。
- 输入/输出：任务 $t$ → 激活子图 $\mathcal{S}^\star$（含 0–k 个合成技能）→ 注入 executor system prompt。
- 代码：`skillos/tta.py:synthesize_gapfill`、`graph.py:record_trace`/`trace_cooccurring`、`GraphRouter(tta=True)`。

> component 数 = 3（推理组件含 ROUTE + TTA 两步）。这一步让**三层图的 trace 层在推理时真正参与**（否则 trace 层只是离线日志）。

### 6.5 Algorithm box
- [x] 要 algorithm box：**ROUTE**（inference loop）+ **GraphGovernedEvolver.absorb**（替换 Trace2Skill REDUCE 的离线 loop）。label `alg:ops` / `alg:route`。

### 6.6 Properties / Complexity
- Trainable params：**0**（纯符号治理，无参数训练）。
- Inference overhead：路由 = BM25 种子 + 依赖闭包 BFS，$O(|\mathcal{S}^\star|)$；远小于全量加载的 token 成本。
- 大 O：与 flat 检索同 order，额外加依赖闭包遍历（线性于子图大小）。

---

## Part 7：Experiments 🔴 — **当前全部 `[SIM]`；真实 benchmark 待补**

### 7.0 §Experiments subsection 清单声明

| § | 子节标题 | 风格 | brief 字段 | 主 fig/table | 段上限 |
|---|---|---|---|---|---|
| §E1 | Setup (simulation harness) | descriptive | 7.2 | tab:setup | 2 |
| §E2 | Main Results: SkillLEGO attains highest success at lowest token cost | claim | 7.3 | tab:main | 2 |
| §E3 | Routing & Split are the dominant contributors | claim | 7.6 | tab:ablation | 2 |
| §E4 | Governance & validation as complementary safety nets | claim | 7.5 | fig:stability | 1 |
| §E5 | Test-time synthesis recovers held-out capabilities | claim | 7.5.bis | tab:tta | 1 |

### 7.1 RQ 列表 ↔ 证据映射 🔴 P0

| RQ # | 问题句 | contrib | §E | 主 table/fig | 一句话主结论 `[SIM]` |
|---|---|---|---|---|---|
| RQ1 | 图治理 + 路由能否在更低 token 下取得更高 success？ | C2/C3 | §E2 | tab:main | SkillLEGO 0.704 success @ 365 tok vs Trace2Skill 0.574 @ 780 tok |
| RQ2 | 各算子贡献几何？ | C2 | §E3 | tab:ablation | 去 ROUTE −0.18、去 SPLIT −0.15（最大两项）|
| RQ3 | 治理/校验对长程稳定性的作用？ | C2 | §E4 | fig:stability | 同时移除 valid+govern → late-success/稳定性最低 |
| RQ4 | 跨域/OOD 迁移？ | C3 | §E2 | tab:main | OOD gain 最高（+0.256）|
| RQ5 | 推理时能否当场合成补回未固化的子能力？ | C3 | §E5 | tab:tta | TTA 把 held-out 覆盖率 gap 补回 ~54%（0.296→0.473），OOD +0.044 |

### 7.2 Setup 数据 🔴 P0
- **Backbone**：`[SIM]` 无 LLM（确定性执行器）。**[真实版 — 统计自 25 篇报告的模型提及]**：
  - 首选 **Qwen-3.x**（开源，提及 **32 次断层第一**；base Trace2Skill 即 Qwen 团队/Qwen3.5；开源利于多轮 self-evolution 的大量 rollout/curate）；
  - + 1 个闭源 **GPT-5.x**（15 次，跨 model family 泛化）；其后 Gemini-2.x / GLM-4 / Claude(各 4–6)。
- **Agent 架构**：**ReAct**（25 篇里提及 **8 次断层第一**，也是 **Trace2Skill base 的架构** `src/react_agent/`）→ 我们沿用 **ReAct executor**，保证与 base/竞品可比；可选 planner / multi-agent（各 3 次）作为扩展。
- **执行脚手架 / 技能格式（已选定）**：采用 **Claude Code** 作脚手架（作者拍板）。理由：25 篇里 Claude Code(7)/Codex(8) 是事实标准脚手架，无人用 OpenHands/AutoGen/LangGraph；技能用 **Anthropic Skill（SKILL.md）** 格式，与 **base Trace2Skill 的 SKILL.md + skill-creator 原生兼容**，且 SkillLEGO 的 capability 技能 = SKILL.md body。→ 可直接在 Claude Code 上跑、与竞品（CoEvoSkills/SkillEvolver/GoS 等）head-to-head。（单脚手架，不做 Codex 对照，避免无关变量。）
- **Benchmark**：`[SIM]` 合成世界（4 域 × 12 原子技能 + 依赖 DAG + 24 task-type，含 OOD）。
  - **[真实版 — 选 self-evolving-skill 领域最主流的 6 个**（统计自 `paper-reading/reports/self_evolving_skills_25papers.html` 25 篇的 Benchmark 字段，按使用篇数排）**]**：

  | # | Benchmark | 用了的篇数 | 域 | 选它的理由 |
  |---|---|--:|---|---|
  | 1 | **ALFWorld** | 8/25 | embodied/text agent | 领域事实标准；**竞品 SkillGraph-RL + GoS 都用 → 直接 head-to-head** |
  | 2 | **SpreadsheetBench** | 6/25 | spreadsheet | **Trace2Skill(base) 用的**；数据已在 `external/repos/Trace2Skill/data/` |
  | 3 | **MATH** | 3/25 | math reasoning | 推理类、技能复用明显 |
  | 4 | **ScienceWorld** | 3/25 | science interactive | 长 horizon、强 OOD 维度 |
  | 5 | **AppWorld** | 3/25 | app 自动化 | 工具/技能组合密集 |
  | 6 | **WebShop** | 2/25 | web 购物 | 也是 SkillGraph-RL 用的，补 web 域对标 |

  - 首选落地顺序：**ALFWorld（对标竞品）→ SpreadsheetBench（接 base）→ 其余补域**。`run-experiment` 可下载 ALFWorld/ScienceWorld 环境。
- **Metric**：Task Success Rate、Avg Token Cost、Loaded Skill Count、Negative Transfer Rate、OOD Transfer Gain、Routing Precision、Bank Size、Stability（per-window std）。
- **Baselines（6，分 3 类）**：
  - I monolithic：**No Skill** / **Trace2Skill**（单体全量）
  - II flat：**Flat Skill Bank**（BM25 top-k）
  - III pruning：**Pruning-only**（flat + 冷技能 prune）
  - IV ours：**SkillLEGO full**
- Oracle upper-bound：可加"全依赖已知"上界（待补）。

### 7.3 主表（RQ1）实际数字 🔴 P0 `[SIM]`
- 主表来源：`results/main.json`（8 seeds 均值）；可由 `sim/report.py` 转 `.tex`。
- 我们 vs 最强 baseline 最大 gap：success vs Trace2Skill **+13pp**；token **2.1× fewer**。
- 我们 vs 最热 baseline gap：见 2.4。

| Method | Success↑ | Tokens↓ | NegTransfer↓ | OOD Gain↑ | RoutePrec↑ |
|---|--:|--:|--:|--:|--:|
| No Skill | 0.428 | 0 | 0 | 0 | 0 |
| Trace2Skill | 0.574 | 780 | 0.219 | 0.163 | 0.234 |
| Flat Skill Bank | 0.555 | 431 | 0.175 | 0.119 | 0.317 |
| Pruning-only | 0.557 | 432 | 0.175 | 0.118 | 0.317 |
| **SkillLEGO** | **0.704** | **365** | **0.105** | **0.256** | **0.391** |

### 7.3.bis Per-Benchmark Detailed Results 🔴 — **[真实版必须；当前 SIM 单一合成世界，仅 1 段]**
- `[SIM]` 单一合成 benchmark，无法拆多 benchmark 段。**真实版需对 §7.2 的 6 个主流 benchmark（ALFWorld / SpreadsheetBench / …）各独立成段。**

### 7.4 跨域 / 泛化（RQ4）`[SIM]`
- OOD：task 流后段混入 OOD task-type（复用 in-distribution 原子技能的新组合）；SkillLEGO OOD success 0.674 vs flat 0.538，gain +0.256（相对 No-Skill OOD 基线）。

### 7.5 机制 / 现象段（RQ3）`[SIM]`
- claim：治理/校验作为**互补安全网**——注入"有害的过度泛化冒名技能"后，单独移除 validation 或 governance 影响小（各 −0.004～−0.014），**同时移除**则 late-stream success 与 stability 最低。
- 量化 evidence：late_success（流末 30%）+ window stability（10 窗 success std）。

### 7.5.bis Test-Time Skill Synthesis（RQ5）`[SIM]`
- setup：每域**扣留 K=3 个最常用原子技能**（任务仍需要、但没固化成可路由技能 = capability gap），对比 无 TTA vs +TTA。数据 `results/tta.json`（`sim/run_tta.py`，5 seeds），label `tab:tta`。
- 数字：

| 变体 | success | OOD success | covered | tokens | synth/task |
|---|--:|--:|--:|--:|--:|
| 全技能（上界参考） | 0.711 | 0.677 | 0.621 | 357 | 0 |
| 扣留, 无 TTA | 0.501 | 0.408 | 0.296 | 325 | 0 |
| 扣留, **+TTA** | 0.557 | 0.452 | **0.473** | 611 | 2.6 |

- 结论：从 trace 共现证据当场合成，把覆盖率 gap 补回 **~54%**（0.296→0.473）、success +0.056、OOD +0.044——trace 层在推理时真正参与（vs SkillGraph-RL/GoS 只路由已建技能）。
- 诚实 caveat：**恢复不完全**（covered 0.473 vs 上界 0.621，只补 trace 证据支持的部分）；**token +88%**（合成加载完整 body；优化方向：摘要化 body / 更严触发阈值）。
- 写作指令：本段 1 段即可，**不拔高为主卖点**——作为 §M3 推理机制的实证补全。

### 7.6 Ablation 数据 🟡 P1 `[SIM]` — 勾选类型
- [x] **Leave-one-out（LOO）**：逐组件移除。来源 `results/ablations.json`，label `tab:ablation`。

| Variant | Success | Tokens | NegTransfer | RoutePrec | LateSucc | Stability |
|---|--:|--:|--:|--:|--:|--:|
| SkillLEGO (full) | 0.643 | 360 | 0.116 | 0.445 | 0.601 | 0.925 |
| w/o Graph Routing | 0.462 | 472 | 0.213 | 0.380 | 0.387 | 0.907 |
| w/o Split | 0.489 | 2345 | 0.236 | 0.081 | 0.495 | 0.924 |
| w/o Lifecycle Validation | 0.629 | 359 | 0.121 | 0.450 | 0.582 | 0.923 |
| w/o Governance Graph | 0.638 | 362 | 0.119 | 0.445 | 0.587 | 0.923 |
| w/o Valid.+Govern. | 0.623 | 362 | 0.125 | 0.451 | 0.562 | 0.919 |
| Full Skill Loading | 0.481 | 3932 | 0.238 | 0.062 | 0.489 | 0.923 |
| Flat Skill Bank | 0.428 | 479 | 0.231 | 0.394 | 0.329 | 0.891 |

- 写作指令：每条独立一段；**ROUTE / SPLIT 两项为主导**（Δ −0.18 / −0.15），token 暴涨见 w/o Split 与 Full Loading。

### 7.7 难度 scaling（可选）
- 可加 "skill bank 规模 sweep"（proposal Finding #4：治理收益随库规模增长）。**[待补]**

### 7.8 涌现 / 干预（RQ6，可选）🟡 — **[当前无；真实版可加]**
- `[SIM]` 暂无 case study；真实版可对 SpreadsheetBench 给 ≥3 正 + 2 失败 case（含 SPLIT 前后对比）。

### 7.9 Efficiency 数据 `[SIM]`
- token cost：SkillLEGO 365 vs Trace2Skill 780（≈2.1× fewer）vs Full-Loading 3932（≈10× fewer）。
- 真实版补 latency / API calls。

### 7.10 统计 rigor
- seeds：**8**（main + ablation 均 8 seeds 均值）。
- 待补 ±std 列与 paired test（当前 report 只出均值；harness 已存 per-seed，可加）。

---

## Part 8：Conclusion / Discussion
- 1 句总结：SkillLEGO 把单体技能演化升级为**三层 Skill Strata 系统 + 测试时乐高拼装**，*load less, compose better, transfer more safely*。
- 3 条 contributions 简版：见 3.6。
- broader implication：为 self-evolving agent 的**技能生命周期治理**提供 OS 式范式。
- Future work（1 句）：接入真实 Trace2Skill/SpreadsheetBench 实跑；扩展到更大技能库验证 Finding #4（治理收益随规模增长）。

---

## Part 9：Appendix
- [x] **A 实现细节**：A.1 7 算子伪代码（`skillos/operations.py`）；A.2 热度公式 + 路由算法；A.3 模拟世界生成协议（`sim/tasks.py`）；A.4 评测协议 + metric 定义。
- [x] **C 补充实验**：skill-bank scaling sweep（待补，支撑 Finding #4）；±std 多 seed 表。
- [x] **F 声明**：Reproducibility ☑（`bash experiments/run_all.sh` 确定性复现）；Code release ☑。
- 正文锚点：§Method §M2 → `app:ops`；§Experiments §E1 → `app:sim_protocol`。

---

## Part 10：风格 / 命名 / Reviewer 偏好
### 10.1 命名约定
- 方法名：**SkillLEGO**（2026-06-21 已定）。三层图 = Skill Strata（trace/capability/governance）；算子 SPLIT/ROUTE + 推理期 LEGO assembly。
- 概念词：*minimal executable skill subgraph* / *Skill Bloat*。
### 10.2 核心 framing 句
- "Skill evolution should not end in larger documents, but in a governable, composable, routable skill graph."（<20 词）
### 10.3 已有文件 / 资料
- 实验数据：`results/main.json`, `results/ablations.json`, `results/RESULTS.md`。
- framework figure 草稿：**无**（待 `paper-figure` 生成）。
- related work 笔记：`paper-reading/`（24 篇 skill 论文 PDF）+ `external/papers/`（三参考 LaTeX 源）。
- prior draft：`skillos_proposal.md`（完整 proposal）。
- LaTeX template：**[待定]**（建议 ICLR）。

## Part 11：项目级元信息
- **方法目录**：`skillos/`（引擎，2400+ LOC，11 tests 通过）；推理阶段 TTA = `skillos/tta.py` + `graph.py:record_trace/trace_cooccurring` + `GraphRouter(tta=True)`；TTA 实验 `sim/run_tta.py` → `results/tta.json`。
- **实验结果目录**：`results/`（raw json + RESULTS.md）。
- **作者列表**：**[待填]**。
- **致谢/资助**：**[待填]**。
- **允许搜笔记补充**：是（`paper-reading/`, `external/`, `CODE_DESIGN.md`）。

---

## Part 12：图表放置索引 🔴 P0 — **⚠️ 全部 `[待生成]`，现不可编译**

> 当前 `figures/`、`tables/` 为空。下表是**目标规划**；交 `paper-from-brief` 前须先用 `paper-figure` / `sim/report.py` 生成真实资产并回填真实文件名 + label，再跑 -1.3 自检。

### 12.1 图索引（规划）
| # | file（待生成） | label | 类型&宽度 | 摆放 | caption 骨架（≥5 元素）| 支撑 |
|---|---|---|---|---|---|---|
| F1 | `figures/framework.pdf` `[待生成]` | `fig:framework` | figure* teaser, \textwidth | §Method §M0 顶 | (1) SkillLEGO 整体数据流 traj→patch→图治理→ROUTE→executor；(2) 三层：trace/capability/governance 图横向排列；(3) frozen 灰、我们的治理组件彩，箭头标 $\mathcal{G},\mathcal{S}^\star$；(4) 数据来自方法设计（非实验）；(5) 读者应看出 monolith 被 SPLIT 成图、ROUTE 只取子图 | RQ1 overview |
| F2 | `figures/routing.pdf` `[待生成]` | `fig:routing` | figure, 0.48\textwidth | §Method §M3 | (1) ROUTE 示例：种子技能 + 依赖闭包 = 最小子图；(2) 节点=技能、实线=depends_on、灰=被屏蔽；(3) 高亮激活子图 vs 排除技能；(4) 数据来自 `sim` 一个 task 的真实路由；(5) 读者看出漏装前置技能被图补回；虚线框 = 测试时从 trace 当场合成的临时技能（TTA）| RQ1/RQ5/§M3 |
| F3 | `figures/stability.pdf` `[待生成]` | `fig:stability` | figure, 0.48\textwidth | §Experiments §E4 | (1) 各变体 late-stream success 曲线；(2) 横轴 task 流位置、纵轴 success；(3) full vs w/o valid+govern 双线；(4) 数据来自 `results/ablations.json` per-window；(5) 读者看出移除安全网后流末退化 | RQ3 |

### 12.2 表索引（规划）
| # | file（待生成）| `\input{}` | label | 类型 | 摆放 | 含义 | 支撑 |
|---|---|---|---|---|---|---|---|
| T1 | `tables/tab_main.tex` `[待生成]` | `tables/tab_main` | `tab:main` | table | §E2 主表段 | 行=6 方法、列=Success/Tokens/NegTransfer/OODGain/RoutePrec；ours 加粗 | RQ1/RQ4 |
| T2 | `tables/tab_ablation.tex` `[待生成]` | `tables/tab_ablation` | `tab:ablation` | table | §E3 | 行=8 变体、列=同上+LateSucc/Stability | RQ2/RQ3 |
| T3 | `tables/tab_setup.tex` `[待生成]` | `tables/tab_setup` | `tab:setup` | table | §E1 | 模拟世界配置（域/技能/task-type/seeds）| §E1 |
| T4 | `tables/tab_tta.tex` `[待生成]` | `tables/tab_tta` | `tab:tta` | table | §E5 | 行=3 变体（全技能/扣留无TTA/扣留+TTA），列=success/OOD/covered/tokens/synth；来源 `results/tta.json` | RQ5 |

> 生成命令：`python3 -m sim.report` 已出 markdown 表；转 `.tex` 需补一个小脚本或手转。

---

## Part 13：Anti-Compression（沿用模板默认硬约束）
- 遵守模板 13.1 不许压缩清单（Per-Benchmark 真实版每 benchmark 独立段、Ablation 每条独立段、Case study ≥3）。
- 遵守 13.1.ter `\paragraph{}` 上限。
- **本 brief 特有**：所有 `[SIM]` / `[待生成]` / `[待核实]` 标记**不得被下游 skill 当成已完成事实**——遇到必须 halt + 回问，不许凭空补真实 benchmark 数字或图。

---

## ⚠️ 提交前 TODO（P0 阻断项）
1. **查新 + 区分**：对已定名 SkillLEGO 做 arXiv 查新；精读 SkillOS-Ouyang(2605.06614) 做 head-to-head → Part 1/4。
2. **精读 skillos_ouyang 全文**做 head-to-head novelty 区分 → Part 4。
3. **核实 Part 4.5 所有非 `[已精读]` 引用**的 cite-key 与"做了啥" → 建 `references.bib`。
4. **补真实 benchmark 实验**替换所有 `[SIM]` → Part 7（接口见 `sim/simulator.py` / `skillos/evolver.py`）。
5. **生成 figures/ + tables/ 资产**并回填 Part 12 真实文件名 → 跑 -1.3 自检。
6. 补作者/资助/LaTeX template → Part 1/10/11。
