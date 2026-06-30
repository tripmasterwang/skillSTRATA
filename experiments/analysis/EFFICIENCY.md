# 效率 / 开销分析 — 时间 & token,vs 竞品

> ⚠️ **诚实前提**:端到端 token **没有被直接记录**(我们 results.json 无 usage 字段、log 是对话文本;
> 竞品 SkillOpt eval 也只有分数)。所以下表区分**精确可算**与**估算/代理**两类,口径在每行标注。

## A. 上下文效率 —— 每题注入的 skill 上下文 token(✅ 精确可算,主指标)

SkillStrata 测试时只路由一个 ~3 技能子图;full-dump 和 SkillOpt(单体 doc)每题注入整个技能库。

| 方法 | 每题 skill 注入 | 相对我们 | 口径 |
|---|---|---|---|
| no-skill(SkillOpt base 模板) | 152 tok | 0.6× | harness_ms noskill 的 SKILL.md |
| **SkillStrata(选择性路由 ~3 技能)** | **239 tok** | 1× | route dump 的 nodes × body/4,280 题均值 |
| human(SkillOpt) | 537 tok | 2.2× | harness_ms human SKILL.md |
| skill-creator(SkillOpt) | 699 tok | 2.9× | harness_ms skillcreator SKILL.md |
| SkillOpt self-train | 1753 tok(q36同backbone 1615) | 7.3× | harness_ms self / best_skill.md 全注入 |
| full-dump(我们的 abl_full) | 2658 tok | 11.1× | 34 个 deployed body 全注入 |
| SkillOpt ckpt | 3471 tok(gpt5.5 3333) | 14.5× | harness_ms ckpt SKILL.md 全注入 |

→ **我们的注入量(239)夹在 no-skill(152)与 human(537)之间——几乎和"不给 skill"一样省**,却拿最高分;
比 SkillOpt 所有有内容 tier(human/creator/self/ckpt)都省,对 self-train 省 ~7×、对全塞省 11×。
配图 `figs/fig_efficiency_context.png`。
**与架构消融互证**:full-dump 既费 11× token、分还更低(43.6 vs 56.1)——选择性路由是"省 token 又涨分",非取舍。

## B. 端到端 token(⚠️ 估算,log 字符/4,含任务数据+多轮,非 API 计费)

| 阶段 | 题数 | 估算 token |
|---|---|---|
| 推理(test_280) | 280 | ~1.40M |
| 进化(train r1–3 + val r0–3) | 7 个 rollout | ~2.49M |
| **合计** | — | **~3.88M** |

- 偏差来源:log 是渲染后 markdown(有格式),比真实计费 token 偏大但同数量级。
- **修正**:SkillOpt self-train(q36 同 backbone)的 `history.json` **精确记了构建 token**(rollout+analyst+merge+rank 逐 step)——
  **构建总计 6.84M token / 85min(4 step)**,可作 apples-to-apples 的**构建成本**对比(见 `CONVERGENCE.md` §C)。
  我们的构建 ~2.49M 是 log 估算且只算 target 端,口径偏松,但数量级上我们构建更省。
- 推理期端到端 token 仍难 apples-to-apples(竞品推理跨 harness gpt5.5/codex、题量不同),只报自身量级。

## C. 时间(⚠️ wall-clock,口径不公平)

| 阶段 | wall-clock | workers |
|---|---|---|
| 进化(train+val 7 个 rollout) | ~12.7h | 80 / 40 |
| 推理(test_280) | ~3.8h | 40 |

- **不公平**:各 run 并发数不同(80/40/24),且多实验抢资源,墙钟不可直接横比。
- 更公平的时间代理 = **每题 LLM 轮数**(我们 max_turns=5;竞品 results.jsonl 有 `n_turns`),后续可补这个口径的对比。

## 结论(可写进论文的)
1. **上下文效率是硬卖点**:同 backbone 比 SkillOpt 省 **6.8×** 注入 token,比全塞省 11×,且分更高 —— 选择性路由"省 token 又涨分"。
2. 端到端 token / 时间因未记录、跨 harness,只给自身量级(~3.88M token 估算),**不夸大成端到端倍数**。
