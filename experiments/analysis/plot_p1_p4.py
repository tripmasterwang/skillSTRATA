#!/usr/bin/env python3
"""问题1(进化趋势 vs 竞品直线) + 问题4(token效率) 两张图。只用白名单数据。"""
import json, glob, statistics, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/projects/skillSTRATA"
RUNS = f"{ROOT}/external/repos/Trace2Skill/runs"
OUT = f"{ROOT}/experiments/analysis/figs"
os.makedirs(OUT, exist_ok=True)

# ---------- 问题1: 进化趋势 ----------
# 我们(react from-zero): val acc per round (唯一有逐轮信号的方法)。来源 curate_fromzero/curate_history.json
hist = json.load(open(f"{RUNS}/curate_fromzero/curate_history.json"))
rounds = [h["round"] for h in hist]
ours = [h["val"] for h in hist]
rejected = [not h["accepted"] for h in hist]   # 被验证门拒的轮

# 竞品 SkillOpt-self: 真实逐步轨迹 (它自己的门分 best_score / 候选 selection_hard)
SK = "/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/projects/nonergodic-self-evolution/external/SkillOpt/outputs/spreadsheetbench_q36_selftrain_dsv32_seed42"
sk_h = json.load(open(f"{SK}/history.json"))
sk_steps = [s["step"]-1 for s in sk_h]                 # 0-based 对齐我们的 round
sk_best = [s.get("best_score") for s in sk_h]          # 门锁定的最优
sk_cand = [s.get("selection_hard") for s in sk_h]      # 每步候选分
sk_action = [s.get("action") for s in sk_h]
sk_len = [s.get("skill_len") for s in sk_h]            # 单体 doc 字符数(膨胀)
# 一次性 baseline 竞品(spreadsheetbench/codex, 5seed hard 均值) — 无逐轮 -> 直线
agg = json.load(open(f"{ROOT}/experiments/analysis/agg_results.json"))
mat = agg["skillopt_matrix"]["data"]["spreadsheetbench"]["codex"]
def tier_mean(t):
    d = mat.get(t, {})
    if "mean_hard" in d: return d["mean_hard"]
    seeds = d.get("seeds", {})
    return statistics.mean(v["hard"] for v in seeds.values()) if seeds else None
comp = {t: tier_mean(t) for t in ["noskill","human","skillcreator"]}

fig, ax = plt.subplots(figsize=(8.6,5.4))
# 我们的曲线(门接受->真涨)
ax.plot(rounds, ours, "-o", lw=2.8, ms=10, color="#1f77b4", label="SkillStrata 图 (门看到的 val/轮)", zorder=6)
for r,v,rej in zip(rounds,ours,rejected):
    if rej: ax.plot(r,v,"x",ms=13,mew=3,color="#d62728",zorder=7)
ax.annotate("r0 门拒", (rounds[0],ours[0]), textcoords="offset points", xytext=(6,-22), fontsize=8.5, color="#d62728")
ax.annotate(f"真涨 +{(ours[-1]-ours[0])*100:.1f}pt", (rounds[-1],ours[-1]), textcoords="offset points",
            xytext=(6,6), fontsize=11, color="#1f77b4", fontweight="bold")
# SkillOpt 自进化真曲线(门 step1 后全拒 -> 卡死)
ax.plot(sk_steps, sk_best, "-s", lw=2.6, ms=9, color="#8c564b", label="SkillOpt 单体doc (门锁定的 best)", zorder=5)
ax.plot(sk_steps, sk_cand, ":D", lw=1.6, ms=6, color="#c49a82", label="SkillOpt 每步候选(被门拒)", zorder=4)
for x,a in zip(sk_steps,sk_action):
    if a=="reject": ax.annotate("拒", (x,sk_best[x]), textcoords="offset points", xytext=(-4,8), fontsize=8, color="#8c564b")
ax.annotate("step1后卡死\ndoc却从6.5k→11.7k字符膨胀", (sk_steps[-1],sk_best[-1]), textcoords="offset points",
            xytext=(-150,18), fontsize=8.5, color="#8c564b",
            arrowprops=dict(arrowstyle="->",color="#8c564b"))
# 一次性 baseline 直线
for t,v in comp.items():
    if v is None: continue
    ax.hlines(v, min(rounds), max(rounds+sk_steps), colors="#aaa", linestyles="--", lw=1.2)
    ax.text(max(rounds+sk_steps), v, f" {t}", va="center", fontsize=7.5, color="#888")
ax.set_xlabel("进化轮/步 (round / step)", fontsize=12)
ax.set_ylabel("门/验证看到的准确率", fontsize=12)
ax.set_xticks(sorted(set(rounds+sk_steps)))
ax.set_title("问题1: 两家都有'门', 但我们的图越攒越强, SkillOpt 单体doc膨胀却卡死", fontsize=11.8)
ax.legend(fontsize=8.5, loc="center left", bbox_to_anchor=(1.01,0.5))
ax.grid(alpha=0.3)
ax.text(0.5,-0.16,"我方=react val(40)/轮; SkillOpt=spreadsheetbench seed42 selection(11) 逐步(真实 history.json); 灰线=一次性竞品最终test。"
        "纵轴各自口径, 看趋势不死磕绝对值。", transform=ax.transAxes, ha="center", va="top", fontsize=7.4, color="#555")
plt.tight_layout()
plt.savefig(f"{OUT}/fig_p1_evolution_trend.png", dpi=140, bbox_inches="tight")
plt.close()
print("SkillOpt traj best:",sk_best,"cand:",sk_cand,"action:",sk_action,"doc_len:",sk_len)

# ---------- 问题4: token 效率 ----------
g = json.load(open(f"{RUNS}/curate_fromzero/trained_graph.json"))
bodies = {s["id"]: s.get("body","") for s in g["skills"]}
def est(txt): return max(1,len(txt)//4)   # ~4 chars/token
route_files = glob.glob(f"{RUNS}/curate_fromzero/test_280/routes/*.json")
graph_load = [sum(est(bodies.get(n,"")) for n in json.load(open(f)).get("nodes",[])) for f in route_files]
graph_mean = statistics.mean(graph_load)
graph_k = statistics.mean(len(json.load(open(f)).get("nodes",[])) for f in route_files)
full_load = sum(est(b) for b in bodies.values())   # 全量加载: 每题塞所有部署技能
# Trace2Skill 单体 SKILL.md (若找得到)
mono_files = glob.glob(f"{ROOT}/external/repos/Trace2Skill/**/xlsx-35B/**/*.md", recursive=True) + \
             glob.glob(f"{RUNS}/skills_35b/**/*.md", recursive=True)
mono_load = max((est(open(m,encoding='utf-8',errors='ignore').read()) for m in mono_files), default=0)

fig, ax = plt.subplots(figsize=(7.2,5))
labels = ["SkillStrata\n图路由 (~%.1f技能)"%graph_k, "全量加载\n(34技能全塞)"]
vals = [graph_mean, full_load]
colors = ["#1f77b4","#ff7f0e"]
if mono_load>0:
    labels.append("Trace2Skill\n单体SKILL.md"); vals.append(mono_load); colors.append("#9467bd")
bars = ax.bar(labels, vals, color=colors, width=0.6)
for b,v in zip(bars,vals):
    ax.text(b.get_x()+b.get_width()/2, v+max(vals)*0.01, f"{v:.0f} tok", ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_ylabel("每题加载的技能 token 数", fontsize=12)
ax.set_title(f"问题4: 图路由每题只加载 {graph_mean:.0f} tok vs 全量 {full_load} tok  (省 ~{full_load/graph_mean:.0f}×)", fontsize=12)
ax.grid(axis="y", alpha=0.3)
ax.text(0.5,-0.13,"来源: test_280/routes/*.json 实际路由的技能 × trained_graph.json 技能正文 (~4字符/token)。"
        "精度匹配(全量加载的准确率)由 abl_full 实验给出, 跑完补'准确率vs token'散点。",
        transform=ax.transAxes, ha="center", va="top", fontsize=7.6, color="#555")
plt.tight_layout()
plt.savefig(f"{OUT}/fig_p4_token_efficiency.png", dpi=140, bbox_inches="tight")
plt.close()

print("OURS val trajectory:", list(zip(rounds,ours)), "rejected:", rejected)
print("competitors (sb/codex 5seed mean hard):", comp)
print(f"TOKEN: graph={graph_mean:.0f} tok/题 (~{graph_k:.1f}技能), full={full_load} tok, mono={mono_load} tok, 省={full_load/graph_mean:.1f}x")
print("figs ->", OUT)
