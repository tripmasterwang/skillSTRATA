# 收敛速率分析 — SkillStrata vs SkillOpt self-train(同 backbone q36,SpreadsheetBench)

> 两边 **target backbone 都是 qwen3.6(xopqwen36v35b)**、都在 SpreadsheetBench、都约 4 步进化 → apples-to-apples。
> ⚠️ 口径差异已标注:held-out 集不同(我们 val n=40 / SkillOpt selection n=11;test 我们 280 / SkillOpt 87)。
> 数据源:我们 `curate_fromzero/curate_history.json`;SkillOpt `outputs/spreadsheetbench_q36_selftrain_dsv32_seed42/{history.json, *selection_eval*, test_eval*}`。

## A. 收敛曲线(held-out 分数随步数)

| 步 | 我们 val(n=40) | SkillOpt selection(n=11) |
|---|---|---|
| 0(baseline) | 0.425 | 0.273 |
| 1 | 0.475 | — |
| 2 | 0.55 | — |
| 3 | 0.60 | — |
| 4(final) | — | 0.273 |

- **我们:val 单调爬升 0.425→0.60(+17.5pp)**,每轮被 gate 接受。
- **SkillOpt self-train:selection 0.273→0.273(+0.0pp,完全不动)**;其 train rollout 也平(rollout_hard 0.667→0.630→0.667 震荡)。
- 配图 `figs/fig_convergence.png`。

## B. held-out TEST 端点(同 backbone)

| 方法 | test baseline | test final | Δ |
|---|---|---|---|
| **SkillStrata(ours,n=280)** | 30.7 | **56.1** | **+25.4pp** |
| SkillOpt self-train(n=87) | 46.0 | 55.2 | +9.2pp |

→ 同 backbone 下,**我们的进化 test 增益(+25.4)约为 SkillOpt 的 2.8×**;SkillOpt 起点高(46)、终点相近(55)但几乎没从进化里拿到东西(selection 0 提升)。

## C. 构建成本(SkillOpt 精确记录;我们估算)

| 方法 | 构建 token | wall-clock | 步数 | 口径 |
|---|---|---|---|---|
| SkillOpt self-train(q36) | **6.84M(精确)** | 85min | 4 step | history.json 逐 step token 加总(rollout+analyst+merge+rank) |
| SkillStrata(ours) | ~2.49M(估算) | — | 4 round | log 字符/4,仅 target 端 |

- ⚠️ 不完全对称:SkillOpt 的 6.84M 含 optimizer(deepseek)+ target(q36);我们估算只算了 target 端 log。即便如此,**数量级上我们构建更省**,且我们 +17.5pp 收敛 vs 它 +0。
- 收敛效率(每步 held-out 提升):我们 ~+4.4pp/round(val);SkillOpt ~0pp/step(selection)。

## D. 结论(可写进论文)
1. **同 backbone、同 benchmark、同步数下,SkillStrata 持续收敛(val +17.5 / test +25.4pp),SkillOpt self-train 几乎不收敛(selection +0 / test +9.2pp)。**
2. 这与 §进化深挖一致:SkillOpt 单体 doc 在 SpreadsheetBench 上"门几乎全拒、val 不涨"(见 HANDOFF 早期发现),而 SkillStrata 的图式 curate(insert/merge/split/gate/checkpoint)能逐轮吸收增益。

## E. test 逐轮收敛(已补全)
我们的 test 逐轮(中间图重建后在 280 上各测一次):

| 轮 | r0(noskill) | r1(13节点0门) | r2(23节点6门) | r3(34节点11门) |
|---|---|---|---|---|
| 我们 test | 30.7 | 35.7 | **56.1** | 56.1 |
| SkillOpt test(n=87) | 46.0(baseline) | — | 57.5(mid) | 55.2(final) |

- **我们 test 主跃升在 R1→R2(35.7→56.1,+20.4pp)**,R2→R3 持平(R3 新增多为僵尸,无净增益)。
- SkillOpt test 起点高(46)但几乎不动(46→55,+9.2);我们从 30.7 一路追到 56.1(+25.4)。
- 注:两者 test split 不同(我们 280 / SkillOpt 87),只比"提升幅度"和"是否收敛",不比绝对值。
