#!/usr/bin/env python3
"""Self-contained, problem-driven HTML deep-dive for SkillStrata.
- figs auto-numbered via FIG_ORDER; reference in text with ref("name") -> 图N (always consistent)
- every figure carries a DETAILED caption (how to read + key numbers + what it proves)
- a per-round SKILL-TEXT TIMELINE shows what each round actually added (names + body excerpts)
Re-run after r2 lands to refresh. Output: experiments/analysis/SkillStrata_Report.html
"""
import os, base64, json, collections, html as _h

HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(HERE, "figs")
R = os.path.join(HERE, "..", "..", "external/repos/Trace2Skill/runs")
CF = os.path.join(R, "curate_fromzero")

# ---- figure registry (display order -> number); change order here only ----
FIG_ORDER = ["fig_radar", "fig_inference_ablation", "fig_test_usage", "fig_evo_content_themes",
             "fig_evo_val_growth", "fig_evo_lifecycle", "fig_perround_difficulty",
             "fig_perround_category", "fig_efficiency_context", "fig_convergence", "fig_evo_ablation"]
def NUM(stem): return FIG_ORDER.index(stem) + 1
def ref(stem): return '<span class=figref>图%d</span>' % NUM(stem)
def fig(stem, title, caption, w="100%"):
    n = NUM(stem); p = os.path.join(FIGS, stem + ".png")
    if not os.path.exists(p):
        inner = '<div class="missing">[图%d 待生成: %s]</div>' % (n, stem)
    else:
        b = base64.b64encode(open(p, "rb").read()).decode()
        inner = '<img style="max-width:%s" src="data:image/png;base64,%s"/>' % (w, b)
    return ('<figure id="fig%d">%s<figcaption><b>图%d · %s</b>'
            '<div class=cap>%s</div></figcaption></figure>') % (n, inner, n, title, caption)

def score(path):
    ids = set(open(os.path.join(HERE, "..", "..", "script/data/skillopt_test_ids.txt")).read().split())
    if not os.path.exists(path): return None
    d = json.load(open(path)); rs = {str(x["id"]): x["success"] for x in d["results"]}
    sel = [i for i in ids if i in rs]; c = sum(rs[i] for i in sel)
    return (c / len(sel) * 100, c, len(sel)) if sel else None
def evo(sub):
    s = score(os.path.join(R, sub, "test_280", "eval_official_results.json")); return "%.1f%% (%d/%d)" % s if s else "<i>跑中…</i>"
def evo_pct(sub):
    s = score(os.path.join(R, sub, "test_280", "eval_official_results.json")); return s[0] if s else None
def cf(sub):
    s = score(os.path.join(CF, sub, "eval_official_results.json")); return s[0] if s else None

nomerge = evo("evo_nomerge"); nm = evo_pct("evo_nomerge")
r2 = cf("evo_r2_test"); r2_str = "%.1f%%" % r2 if r2 else "跑中…"
def delta(v): return "%+.1f" % (v - r2) if (r2 and v is not None) else "—"

def Q(num, q, ans, evidence):
    return ('<div class=card><div class=q><span class=qn>Q%s</span>%s</div>'
            '<div class=ans>%s</div><div class=ev><span class=evh>📊 依据</span>%s</div></div>') % (num, q, ans, evidence)

# ---------------- per-round skill-text timeline (中文解读版) ----------------
# 英文技能名 -> (中文功能名, 一句"解决什么坑")。意译,不贴源码正文。
ZH = {
 "parse_text_range_for_inclusive_count": ("解析文本型区间", "把单元格里“2 to 5”这种文本拆成数字、算 end−start+1,并处理缺分隔符等边界"),
 "precompute_and_write_static_values": ("用 Python 算好、写死值", "复杂转换在 Python 里算完直接写静态值,不嵌入脆弱、难验证的 Excel 公式"),
 "targeted_column_population": ("只写目标列", "用 max_row 动态定范围,只改目标列,保留相邻列和原有格式"),
 "Dynamic Range Detection": ("动态探测数据边界", "用 worksheet.max_row 确定范围,不硬编码行号,适应不同大小的表"),
 "Safe Backward Row Deletion": ("倒序删行", "删行从后往前,避免正向删导致后面行号错位、漏删"),
 "Python Computation Over Live Formulas": ("用 Python 代替活公式", "日期比较、阈值、多步逻辑都在 Python 算成静态值,避开公式的类型坑"),
 "Detecting Excel Error Values in OpenPyXL": ("识别错误值", "#N/A 等常以字符串形式存,要用 str(cell)=='#N/A' 判断,否则漏判"),
 "Dynamic Formula Reference Adjustment": ("公式引用动态构造", "把公式写进多个格时要按格生成引用,否则每格都锁死同一个引用"),
 "Dictionary-Based Category Aggregation": ("字典分组聚合", "用 Python dict 按类别分组求和,一次扫完"),
 "Safe String Matching in Cells": ("稳健字符串匹配", "匹配前先归一化类型,防止类型不符直接报错"),
 "handle_openpyxl_datetimes": ("处理日期对象", "正确读写 openpyxl 的 datetime,不出格式错"),
 "openpyxl_max_column_attribute": ("正确取列数", "用对的属性拿工作表列维度"),
 "partial_case_insensitive_matching": ("模糊/不区分大小写匹配", "支持部分关键词、忽略大小写地匹配单元格"),
 "date_serialization_in_spreadsheet": ("日期序列化", "把 Python datetime 转成 Excel 序列号,日期才正确"),
 "Dynamic Range Determination": ("动态定范围(近义版)", "和“动态探测边界”是同一招的另一种措辞——这正是后面要合并的对象"),
 "openpyxl_cell_value_comparison": ("先取 .value 再比较", "比较前先取出 cell.value,避免拿对象去比"),
}
# 归并类(不逐条展开)
TOOLY = {"Verify Library Names Before Execution", "Use Heredocs for Multi-line Python", "Robust Script Execution",
         "Safe_Embedded_Code_Execution", "JSON Command Formatting for Bash Tool", "JSON Escaping for Embedded Scripts",
         "Action Schema Strictness", "avoid_literal_newlines_in_tool_json", "Verify Library Names Before Importing",
         "transition_from_exploration_to_execution", "guarantee_output_file_generation"}

def timeline():
    L = json.load(open(os.path.join(HERE, "evolution_ledger.json")))
    by = collections.defaultdict(list)
    for s in L["skills"]:
        by[s["mint_round"]].append(s)
    META = {  # (标题, 颜色, 为什么这轮加, 为什么必要)
        0: ("R0 · 空图首跑 → 全军覆没", "#c0392b",
            "第 0 轮在<b>零技能</b>的空图上裸跑训练集,distill 出 12 个最初的猜测(条件过滤、安全字符串操作、反向删行、跨表匹配……和后面 R1 高度同义)。",
            "但这一轮验证分没涨(0.425),被门<b>整轮回滚</b>——说明只凭一次裸跑提炼的东西还不够稳,门在这里挡掉了一整轮噪声。"),
        1: ("R1 · 奠基 12 个主力", "#2e86de",
            "R0 裸跑暴露了一批<b>反复出现的翻车点</b>:用 Excel 公式算出脆弱结果、正向删行漏行、#N/A 当对象判断失败、文本区间解析出错……distill 把这些“踩坑→纠正”提炼成技能。",
            "这些都是 SpreadsheetBench <b>单元格级任务的高频操作</b>,不固化成守则,agent 每道题都要重踩一遍同样的坑(后面图1证明:这几个正是被路由最多的主力)。"),
        2: ("R2 · 去重 + 首次挂门", "#27ae60",
            "R1 的技能用了一轮后冒出两个问题:① “算死值”这套被<b>反复 distill 出近义版</b>(库要膨胀);② 几个高频技能成功率只有 ~0.5(等于掷硬币)。",
            "所以这轮做两件事:把近义的<b>合并</b>(2 次,都是 precompute-in-python 同源)防膨胀;给不靠谱的高频技能<b>挂验证门</b>(首批 6 个)做兜底——这正是“门”开始发挥作用的一轮。"),
        3: ("R3 · 收敛 + 补门", "#8e44ad",
            "验证分爬到 0.60、继续补长尾能力(跨表查找、内存映射、JSON 处理等),并再挂 5 个门(共 11)。",
            "但这一轮新增的<b>多数后续没被路由到</b>——最后一轮之后没有 rollout 去用它们,属于“插了但还没验证有没有用”(也是后面僵尸技能软肋的来源)。"),
    }
    out = ['<p class=lead>每轮分三块看:<b>💡 为什么这轮加 → ✅ 为什么必要 → 🔧 加了哪些</b>(中文功能名 + 一句它防的坑,英文原名作小字)。</p>']
    for r in [0, 1, 2, 3]:
        title, col, motive, need = META[r]
        items = sorted(by[r], key=lambda x: -(x["trials"] or 0))
        rows, tool_n, other = [], 0, []
        for s in items:
            nm = s["name"]
            if nm in TOOLY:
                tool_n += 1; continue
            zh = ZH.get(nm)
            if not zh:
                other.append(nm); continue
            cn, pit = zh
            st = s["status"]
            if st == "retired": badge = '<span class=bad-r>被门拒</span>'
            elif (s["trials"] or 0) > 0: badge = '<span class=bad-u>用过 %d 次</span>' % s["trials"]
            else: badge = '<span class=bad-z>未路由</span>'
            gate = ' <span class=gate>🔒门</span>' if s.get("checkpoint_round") is not None else ''
            rows.append('<div class=skrow><div class=skl><b>%s</b>%s%s</div>'
                        '<div class=skr>%s<div class=eng>%s</div></div></div>' % (
                        cn, gate, badge, pit, _h.escape(nm)))
        extra = []
        if tool_n: extra.append("%d 个<b>工具调用/执行环境类</b>(怎么写 JSON、调 bash、确认库名)——离最终答题太远,后续 0 次被路由" % tool_n)
        if other: extra.append("%d 个近义/特化重复(如 %s)" % (len(other), "、".join(_h.escape(o) for o in other[:3]) + ("…" if len(other) > 3 else "")))
        more = ('<div class=skmore>另:%s</div>' % "；".join(extra)) if extra else ""
        out.append(
            '<details %s><summary style="border-left:5px solid %s">%s <span class=muted>(共 %d 个)</span></summary>'
            '<div class=why><span class=wa>💡 为什么这轮加</span>%s</div>'
            '<div class=why><span class=wn>✅ 为什么必要</span>%s</div>'
            '<div class=addh>🔧 加了哪些</div>%s%s</details>' % (
            "open" if r in (1, 2) else "", col, title, len(items), motive, need, "".join(rows), more))
    return "".join(out)

TL = timeline()

CSS = """*{box-sizing:border-box} body{font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;line-height:1.7;color:#1a2330;margin:0;background:#f4f6f9}
.wrap{max-width:1000px;margin:0 auto;padding:0 24px 80px}
header{background:linear-gradient(135deg,#16324f,#1f6f54);color:#fff;padding:46px 24px;text-align:center}
header h1{margin:0 0 6px;font-size:29px} header .sub{opacity:.85;font-size:14px}
.banner{display:flex;gap:16px;justify-content:center;margin:24px 0 4px;flex-wrap:wrap}
.stat{background:rgba(255,255,255,.12);border-radius:12px;padding:14px 24px;min-width:140px}
.stat .big{font-size:28px;font-weight:700} .stat .lbl{font-size:12px;opacity:.85}
h2{color:#16324f;border-bottom:3px solid #1f6f54;padding-bottom:6px;margin:46px 0 6px;font-size:22px}
.lead{color:#4a5a6a;font-size:14.5px;margin:8px 0 4px}
.card{background:#fff;border-radius:12px;padding:20px 24px;margin:14px 0;box-shadow:0 1px 5px rgba(0,0,0,.07)}
.q{font-size:17.5px;font-weight:700;color:#16324f;margin-bottom:10px}
.qn{display:inline-block;background:#1f6f54;color:#fff;border-radius:6px;padding:1px 9px;font-size:14px;margin-right:9px}
.ans{font-size:15px;margin-bottom:6px}
.ev{background:#eef4f9;border-left:4px solid #1f6f9f;padding:10px 14px;border-radius:6px;margin-top:12px;font-size:13.5px;color:#27424f}
.evh{font-weight:700;color:#1f6f9f;margin-right:8px}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:13.5px}
th,td{border:1px solid #dde3ea;padding:7px 10px;text-align:left} th{background:#eef3f8}
tr:nth-child(even) td{background:#f8fafc} .ours{background:#e3f5ec!important;font-weight:700}
.tldr{background:#fff8e6;border-left:5px solid #e0a800;padding:14px 20px;border-radius:6px;margin:18px 0}
.warn{background:#fdeef0;border-left:5px solid #c0392b;padding:12px 18px;border-radius:6px;margin:12px 0;font-size:13.5px}
figure{margin:16px 0;padding:0;background:#fafcfd;border:1px solid #e3e8ee;border-radius:10px;overflow:hidden}
figure img{display:block;margin:0 auto;max-width:100%;border:0;border-bottom:1px solid #eef1f4}
figcaption{padding:10px 16px;font-size:13px;color:#27424f;background:#f1f6fa}
figcaption b{color:#1f6f54;font-size:14px} .cap{color:#33424f;font-size:13px;margin-top:5px;line-height:1.6}
.figref{color:#1f6f54;font-weight:700;white-space:nowrap}
.map{background:#f0f5f2;border-radius:8px;padding:14px 18px;font-size:13.5px;margin:10px 0}
.muted{color:#69788a;font-size:12.5px} code{background:#eef1f4;padding:1px 5px;border-radius:4px;font-size:12.5px}
details{background:#fff;border-radius:10px;margin:10px 0;box-shadow:0 1px 4px rgba(0,0,0,.06);padding:4px 0}
summary{cursor:pointer;font-weight:700;font-size:15.5px;color:#16324f;padding:10px 16px}
.why{margin:8px 18px;padding:10px 14px;border-radius:8px;font-size:13.5px;line-height:1.65}
.why:nth-of-type(1){}
.wa,.wn{display:block;font-weight:700;margin-bottom:3px}
.why:has(.wa){background:#fff8e6;border-left:4px solid #e0a800} .wa{color:#a87b00}
.why:has(.wn){background:#eef7f0;border-left:4px solid #27ae60} .wn{color:#1f7a4d}
.addh{margin:12px 18px 4px;font-weight:700;color:#16324f;font-size:14px}
.skrow{display:flex;gap:14px;align-items:flex-start;border-top:1px solid #eef1f4;padding:8px 18px}
.skl{flex:0 0 200px;font-size:13.5px;color:#1f3147} .skl b{color:#16324f}
.skr{flex:1;font-size:12.8px;color:#3a4a59} .eng{color:#9aa7b4;font-size:11px;font-family:ui-monospace,Menlo,monospace;margin-top:2px}
.skmore{padding:9px 18px;color:#5a6b7a;font-size:12.5px;border-top:1px dashed #e3e8ee;background:#fafcfd}
.gate{color:#7a5fb0;font-size:11px;margin-left:4px}
.bad-u{background:#e3f5ec;color:#1f7a4d;border-radius:10px;padding:1px 8px;font-size:11px;margin-left:6px}
.bad-z{background:#eef1f4;color:#7a8694;border-radius:10px;padding:1px 8px;font-size:11px;margin-left:6px}
.bad-r{background:#fdeceb;color:#c0392b;border-radius:10px;padding:1px 8px;font-size:11px;margin-left:6px}"""

HEADER = """<header><h1>SkillStrata 实验综合报告</h1>
<div class=sub>SpreadsheetBench · 280 道留出题 · backbone qwen3.6-35b-a3b · 全部分数为官方评分器重算真值</div>
<div class=banner>
<div class=stat><div class=big>30.7%</div><div class=lbl>不给技能 (no-skill)</div></div>
<div class=stat><div class=big>56.1%</div><div class=lbl>用了 SkillStrata</div></div>
<div class=stat><div class=big>+25.4pp</div><div class=lbl>提升</div></div>
</div></header>"""

RADAR = '<h2>0. 一张图看全局</h2>' + fig("fig_radar",
"综合能力雷达 — 加技能前(灰)后(绿)的能力画像",
"这是同一个 backbone、同一批 280 道题下,<b>不给技能(灰)</b> 与 <b>SkillStrata(绿)</b> 在 6 个维度上的对比。"
"外圈=满分。前 5 维是准确率(总分 / Cell-Level / Sheet-Level / 难题 / 简单题),第 6 维是省 token(注入越少越靠外)。"
"<b>怎么读</b>:绿色面积几乎把灰色整个包住=全面更强。两处最该看:"
"① <b>难题维</b>(no-skill 答错的 194 道题)从 0 撑到 <b>44</b>——技能的主要功劳是去救本来不会做的题;"
"② <b>简单题维</b>绿(84)反而比灰(100)略缩——这是诚实代价:技能把少数本来会做的题带歪了。"
"省 token 维两条都很靠外(都比全塞省),no-skill 略高是因为它根本不塞技能。"
"这张是全局总览,后面每个维度都有专图深挖。")

TLDR = """<div class=tldr><b>这份报告只回答一个问题:这 +25 分到底从哪来、靠不靠谱?</b><br>
办法是<b>消融</b>——把部件一个个关掉看分数掉多少。下面每节是一个小问题,答案后都附 “📊 依据”,每张图都有详细图解。一句话结论:<br>
<b>这 25 分主要来自“会挑会组织技能”(不是技能写得多好),加一个“做完自检重试”的验证门兜底;
进化学到的是一批“用 Python 稳操 Excel 的防坑套路”。同 backbone 下它比竞品 SkillOpt 又省 token 又真在涨分。</b></div>
<div class=map><b>阅读地图</b>:图0 总览 → Q1–Q4 推理时(用图时)增益从哪来 → Q5–Q7 + 逐轮文本时间线(训练时图怎么长出来、每轮加了什么) → Q8 和竞品比 → Q9 老实说软肋。</div>"""

S1 = "<h2>一、推理时:增益从哪来</h2><p class=lead>图已练好,只改“怎么用这张图”,看分数怎么变。本节四个问题都看 " + ref("fig_inference_ablation") + " 这张条形图。</p>"

Q1 = Q(1, "增益是因为“技能攒得好”,还是因为“会挑着用”?",
"<b>是“会挑着用”。</b> 把同一批练好的技能<b>全塞</b>给模型只有 43.6 分;按图谱只<b>挑 3 个相关的</b>用反而 58.6 分——同样的技能、只换用法,差 15 分。所以涨分不是技能内容写得好,是<b>会挑、会组织</b>(" + ref("fig_inference_ablation") + " 绿条 vs 灰条)。",
"同一张图、同一批技能,只改路由方式:<b>全塞 full 43.6%</b> vs <b>图路由 graph 58.6%</b> = +15.0pp;再比关键词检索 <b>BM25 41.8%</b>,图路由 +16.8pp。三者技能内容完全一样,差别只在挑不挑、按不按图组织。<br>"
+ fig("fig_inference_ablation", "推理消融:6 种测试时配置的分数(Q1–Q4 都看这张)",
"横条=每种配置在 280 道题上的分数,<b>红色虚线=不给技能的 30.7</b>。"
"<b>绿条</b>=我们带图的路由(graph 58.6 / agent 57.1 / 原始完整 56.1);<b>灰条</b>=去掉图或验证的对照(关验证 44.3 / 全塞 43.6 / BM25 41.8)。"
"这一张图同时回答 4 个问题:<br>"
"① <b>绿 ≫ 灰</b>:同一批技能,按图挑着用比全塞、比关键词检索高 15–17 分 → 增益在“会挑会组织”,不在技能本身(Q1);<br>"
"② <b>绿条内部 graph 58.6 ≈ agent 57.1</b>:用死规则挑和用 LLM 挑几乎一样 → 不必花钱请 LLM 当调度员(Q2);<br>"
"③ <b>关验证 44.3 vs 完整 57.1 = −12.8</b>:验证门一关就掉一大截 → 它是承重部件(Q4);<br>"
"④ 所有绿灰条都远高于红虚线 30.7 → 整套系统确实有用。"))

Q2 = Q(2, "那“挑技能”需要请一个聪明的 LLM 来挑吗?",
"<b>不需要,死规则挑就够好。</b> 让 LLM 挑种子(agent)得 57.1,用 BM25+图谱死规则挑(graph)得 58.6,<b>统计打平</b>。代码上这俩只差“选种子”那一步,后面依赖闭包、冲突过滤完全一样,所以贵的 LLM 路由可省掉(" + ref("fig_inference_ablation") + " 上面两条绿条几乎一样长)。",
"控制变量到极致:agent 与 graph <b>只差选种子用 LLM 还是 BM25</b>,其余代码一字不差。同批次 <b>agent 57.1% vs graph 58.6%</b>,McNemar p≈0.5(不显著)= 打平。")

Q3 = Q(3, "既然“挑着用”是关键,它顺带省了多少开销?",
"<b>省很多,而且又省又好。</b> 全塞要把 34 个技能正文都喂进去(约 2658 token/题);我们每题平均只路由 <b>3 个</b>技能、约 239 token——<b>省 11 倍</b>,同时分数还更高(58.6 vs 43.6,见 " + ref("fig_inference_ablation") + ")。",
"读 280 题每题实际路由记录(" + ref("fig_test_usage") + "):平均 <b>3.0 个/题</b>、约 239 token;全塞 2658 token/题;34 个技能只有 20 个被用过。<br>"
+ fig("fig_test_usage", "测试时每个技能被路由的次数",
"横条=该技能在 280 道题里被选中几次,从多到少排。<b>蓝条</b>=被用过的 20 个技能(条上数字=次数),<b>黑钻石</b>=该技能带验证门,<b>右下红框</b>=14 个从没被用过的技能(含 11 个“工具调用”类)。"
"<b>三个要点</b>:① 极少数主力扛活——前 6 个(Python Computation 171 次、parse_text 133 次…)占了绝大多数路由,呼应“每题只用 3 个”;"
"② 几乎每条被用的技能都带黑钻石(门),门覆盖 277/280=99% 的题,这解释了 Q4 关门为何掉 12.8 分;"
"③ 那 14 个 0 使用的(尤其 11 个工具类)是纯库膨胀——路由拿任务描述去匹配技能正文,任务里不会出现“JSON/heredoc”这种词,所以永远选不中。"))

Q4 = Q(4, "“做完自检、不对就重试”的验证门有用吗?",
"<b>很有用,值约 13 分。</b> 关掉验证门,分数从 57.1 掉到 44.3(−12.8)。而且它几乎管每道题——280 题里 277 题(99%)都路由经过了带门技能(" + ref("fig_test_usage") + " 的黑钻石)。它不是可有可无的兜底,是<b>承重部件</b>。",
"同代码开关门:<b>开 57.1% → 关 44.3% = −12.8pp</b>(" + ref("fig_inference_ablation") + ");门覆盖 <b>277/280=99%</b>(" + ref("fig_test_usage") + ")。注:57.1 是当前代码重跑的同批次完整基准,≈原主结果 56.1(只差 1 分)→ 跨批次波动仅 ~1 分,数字可靠。")

S2 = "<h2>二、训练时:图怎么长出来、学到了什么</h2><p class=lead>从空图开始一轮轮 curate,把每轮、每个技能的命运和正文都扒出来看。</p>"

Q5 = Q(5, "进化到底在“学”什么内容?",
"<b>学的不是领域知识,是一批“用 Python/openpyxl 稳操 Excel 的防坑套路”。</b> 把最常用的技能正文一条条读了,高度一致:<b>动态探边界(别写死行号)、把结果用 Python 算成死值写进去(别用脆弱 Excel 公式)、删行倒着删</b>……都是怎么操作表格不翻车的工程经验。两条最吃重:动态范围、算死值(" + ref("fig_evo_content_themes") + ")。",
"把 34 个 deployed 技能按正文内容归 8 类、按实际被用次数排(" + ref("fig_evo_content_themes") + ")。<br>"
+ fig("fig_evo_content_themes", "进化出的技能按内容主题 × 实际被用次数",
"横条=该主题下所有技能在测试时被路由的总次数(越长=这类内容越吃重);每条标了该主题有几个技能。"
"<b>怎么读</b>:最长的两条是<b>动态范围(135 次)</b>和<b>算死值代替公式(114 次)</b>=两根支柱,正是 Q5 说的核心套路;"
"中间是文本解析、安全删行、错误值处理等防坑技巧;<b>最底下红条“工具调用踩坑”11 个技能 0 次使用</b>——说明离最终答题奖励太远的元知识(怎么写 JSON、怎么调 bash)进化也会顺手学,但根本用不上。"
"这张图把“进化在学什么”从一句话变成可量化的内容分布。"))

Q6 = Q(6, "它是怎么一轮轮学出来的?是不是瞎攒?",
"<b>不是瞎攒,有个“涨分才留”的门把着。</b> 第 0 轮在空图上瞎试,distill 出 12 个,但验证分没涨,被门<b>整轮打回</b>(12 个全扔);第 1–3 轮每轮涨分才被接受,库 0→12→22→34,验证分 0.425→0.60(" + ref("fig_evo_val_growth") + ");每个技能的命运见 " + ref("fig_evo_lifecycle") + "。",
"逐轮记录:R0 插 12、val 0.425、<b>gate 拒→12 个全 retired</b>;R1 +12→0.475;R2 +10→0.55;R3 +12→0.60。<br>"
+ fig("fig_evo_val_growth", "逐轮验证分爬升 + 技能库增长",
"<b>红线(左轴)</b>=验证集准确率,点下标 ACCEPT/REJECT;<b>浅蓝柱(右轴)</b>=累计部署的技能数。"
"读法:红线从 0.425 单调爬到 0.60,蓝柱 0→12→22→34 同步长高;<b>R0 那个点标着 REJECT</b>——那一轮 distill 的 12 个因为没让验证分涨,被门整轮回滚(所以蓝柱在 R0 还是 0)。"
"这张图证明库不是越攒越多地瞎长,而是“这一轮新技能能让验证分涨,才保留”地长出来的。")
+ fig("fig_evo_lifecycle", "每个技能的一生(哪轮生、活到最后还是被弃、哪轮挂门)",
"每一行是一个技能,横轴=轮次;<b>颜色=出生轮</b>(蓝 R1/绿 R2/紫 R3),<b>实心条</b>=被实际路由过(右侧标 succ 和次数),<b>斜纹条</b>=部署了但没被用过,<b>黑钻石</b>=挂了验证门,<b>底部红色一排</b>=R0 整轮被门拒的 12 个。"
"读法:上方实心蓝/绿条就是主力(次数最高);黑钻石集中落在 succ 0.5 左右的高频技能上——说明门是“学”出来精准挂在不靠谱技能上的,不是均匀加的;右下大片斜纹紫条=R3 最后一轮新增、之后没机会被用的技能。"))

S3 = '<h2>三、逐轮到底加了什么技能(从文本看)</h2><p class=lead>上面是统计视角,这里直接给你每轮新增技能的<b>名字 + 描述 + 正文片段</b>,点开就能看每步加的东西具体长什么样、彼此差在哪。</p>' + TL

S4 = "<h2>四、学的过程有代价吗</h2>"

Q7 = Q(7, "学的过程一帆风顺吗?有没有代价?",
"<b>有阵痛,而且正好暴露了“门”的真正作用。</b> 按难度拆:<b>难题</b>(本来不会的)从第一轮就被持续救起(0→27→44);但<b>简单题</b>(本来就会的)走 V 形——早期(R1 还没加门)新技能把简单题<b>带歪了</b>(100 掉到 55),直到后面加 11 个门才修回来(→84)。所以门的真正作用是<b>防止新技能帮倒忙、把会做的题做坏</b>(" + ref("fig_perround_difficulty") + ")。",
"逐轮把 280 题按 no-skill 是否做对分易/难看;V 形拐点正好对上“加门”这一步,和 Q4(关门 −12.8)、" + ref("fig_test_usage") + " 门覆盖 99% 三处互证。<br>"
+ fig("fig_perround_difficulty", "逐轮 × 难度:难题持续被救,简单题走 V 形",
"横轴=进化轮次 r0→r3,纵轴=该组题的准确率。<b>红线=难题</b>(no-skill 答错的 194 道),<b>绿线=简单题</b>(no-skill 已会的 86 道)。"
"读法:红线单调上升 0→27→44——技能从第一轮起就在稳定地救难题;<b>绿线走 V 形 100→55→84</b> 是关键:R1 只有 13 个技能、<b>还没有门</b>,新技能把本来会做的简单题做坏了(掉到 55),等到 R2/R3 加了 11 个验证门,简单题才被保护回来(回到 84)。"
"这条 V 形是“门=防止帮倒忙”最直接的证据。" + ("" if r2 else "(r2 第 4 点跑完会补上,看拐点是否在 R2 已回升。)"))
+ fig("fig_perround_category", "逐轮 × 类别:Cell / Sheet 各自的提升轨迹",
"横轴同上,按 SpreadsheetBench 的 Cell-Level / Sheet-Level 分两条线。辅助看不同类别的题在哪一轮起来,和按难度的视角(上一张)互补;Cell-Level 是主战场(提升幅度最大)。"))

LONGTAIL = ('<h2>四之二、长尾在哪、为什么救不动</h2>'
'<div class=card><div class=ans>“长尾” = 技能没帮上的题。280 题拆开:救活 85、都对 72,但 <b>硬骨头 109 道(39%,怎么都做不对)</b> + 拖垮 14 道 = <b>123 道(44%)</b>技能没帮上或帮倒忙。</div>'
'<table><tr><th>分组</th><th>题数</th><th>Cell占比</th><th>答案单格占比</th><th>中位答案格数</th></tr>'
'<tr class=ours><td>硬骨头(都错)</td><td>109 (39%)</td><td>77%</td><td>78%</td><td>1</td></tr>'
'<tr><td>救活(skill 救起)</td><td>85</td><td>78%</td><td>77%</td><td>1</td></tr>'
'<tr><td>都对(本来就会)</td><td>72</td><td>49%</td><td>50%</td><td>4</td></tr></table>'
'<div class=ev><span class=evh>📊 为什么长尾</span>'
'<b>硬骨头和能被救活的题,表面特征几乎一模一样</b>(都是 Cell 类约 78%、答案单格约 78%、中位 1 格)——'
'所以它们难<b>不是因为“题大 / 类型特殊”,而是任务内在的逻辑复杂度</b>(需要的多步计算 / 特定领域逻辑)。'
'对照“都对”组(本来就会的)答案明显更大(单格仅 50%、中位 4 格),是另一类题。'
'<br><b>这正对应进化的局限</b>:它长出的是<b>宽平的“防坑套路池”(74 条边全是 alternative_to、没有组合边)</b>,'
'能救“套用某个现成套路就行”的题(救活 85),救不了“需要把多个能力组合起来”的题(硬骨头 109)——而这两类从表面特征分不出来。'
'<br>(运行时也是这批题最慢:agent 反复试错跑满 5 轮还过不了,所以补跑总卡在尾部。)</div></div>')

S5 = "<h2>五、和竞品比 & 老实说软肋</h2>"

Q8 = Q(8, "同样的 backbone,比竞品 SkillOpt 强在哪?",
"<b>又省 token、又真的在涨分。</b> (1) 省:我们每题注入 239 token,SkillOpt(同 backbone)要把整篇技能文档 1615 token 全塞,<b>省 6.8 倍</b>(" + ref("fig_efficiency_context") + ");(2) 涨:同跑 4 步,我们验证分单调涨 +17.5pp,SkillOpt self-train 验证分<b>纹丝不动(+0)</b>,留出测试集也只 +9.2(我们 +25.4,见 " + ref("fig_convergence") + ")。",
"两张图分别支撑“省”和“涨”。<br>"
+ fig("fig_efficiency_context", "每题注入 skill 上下文 token(越短越省)",
"横条=各方法每题塞进模型的技能文档 token,从短(省)到长(费)。<b>绿条=我们 239</b>,夹在 no-skill(152)和 human(537)之间——几乎和“完全不给技能”一样省;"
"SkillOpt 同 backbone 的 self-train 要 1615(我们的 <b>6.8 倍</b>),它的 ckpt 版 3471、我们自己的全塞消融 2658 都更费。"
"关键是:我们注入最少却拿最高分(56.1),所以是“又省又好”,不是省钱换性能。")
+ fig("fig_convergence", "收敛对比:我们持续涨,SkillOpt 几乎不动",
"横轴=进化步数,纵轴=留出验证分。<b>绿线=我们</b> 0.425→0.60(+17.5pp,单调爬);<b>红线=SkillOpt self-train</b> 0.273→0.273(+0,纹丝不动)。"
"两者是<b>同一个 backbone(q36)、同一个 benchmark、同样约 4 步</b>,所以可比。读法:我们的进化每轮都吸收到增益,SkillOpt 的单体技能文档在 SpreadsheetBench 上几乎学不动(它的训练日志精确记了 token,构建花了 6.84M)。"))

EVO_TABLE = ('<h2>五之二、进化消融:每个进化部件值多少</h2>'
'<div class=card><div class=ans>从零 curate、每次关一个进化部件、跑到 round-2 看分数。基准 = 全部件都开、同样到 round-2(r2)= <b>'
+ r2_str + '</b>(' + ref("fig_evo_ablation") + ')。</div>'
+ fig("fig_evo_ablation", "进化消融:关掉每个进化部件后掉多少",
"横条=每种“关掉一个进化部件、从零跑到 round-2”的图在 280 题上的分数;<b>蓝条=全部件都开的基准(r2)</b>,<b>橙条=各关一个部件</b>,红虚线=no-skill 30.7。"
"读法(从差到好):<b>只插入(全关)32.1 ≈ no-skill</b>——光往库里塞、不做合并/拆分/把关/挂门,几乎等于没进化;关验证门(33.2)也掉得很惨;关 gate(44.6)、关合并(40.0)、关拆分(45.4)影响依次减小。"
"结论:<b>组织(合并)和验证门最关键,拆分影响最小</b>。" + ("各条上标了 Δ(相对全开基准掉多少分)。" if r2 else "⚠️ 全开基准 r2 仍在跑,补上后每条会标 Δ。"))
+ '<table><tr><th>关掉哪个部件</th><th>分数</th><th>vs 全开基准</th><th>大白话</th></tr>'
+ '<tr><td>关拆分 (nosplit)</td><td>45.4%</td><td>' + delta(45.4) + '</td><td>影响最小</td></tr>'
+ '<tr><td>关验证gate (nogate)</td><td>44.6%</td><td>' + delta(44.6) + '</td><td></td></tr>'
+ '<tr><td>关合并 (nomerge)</td><td>' + nomerge + '</td><td>' + (delta(nm) if nm else "—") + '</td><td></td></tr>'
+ '<tr><td>关验证门 (nockpt)</td><td>33.2%</td><td>' + delta(33.2) + '</td><td>门很关键,关了大掉</td></tr>'
+ '<tr><td>全关 (只插入)</td><td>32.1%</td><td>' + delta(32.1) + '</td><td>≈no-skill,只塞不组织几乎=没进化</td></tr>'
+ '</table></div>')

Q9 = ('<div class=card><div class=q><span class=qn>Q9</span>哪些地方不靠谱 / 是软肋?(老实说)</div>'
'<div class=warn><ul>'
'<li><b>只有“准入门”没有“退出门”</b>:技能一旦被接受就永久留库,没机制清理 → 库只增不减、攒下从没被用过的“僵尸技能”(' + ref("fig_test_usage") + ' 右下那 14 个)。代码里写了清理函数,但没接进主流程。</li>'
'<li><b>近义技能没合并干净</b>:合并阈值偏松,“动态范围检测”一个概念长出 4 个名字略不同的节点(见逐轮文本时间线 R2/R3)。</li>'
'<li><b>技能会帮倒忙</b>:280 题里救活 85 道、但拖垮 14 道、还有 109 道(39%)怎么都做不对。</li>'
'<li><b>跨 harness 负迁移</b>:这张图换到 codex/claude 等更强 harness 上反而退化——学到的套路和 backbone 绑定,泛化性有限。</li>'
'</ul></div>'
'<div class=ev><span class=evh>📊 口径</span>分数一律 280-subset(非 400 分母);进化消融是 round-2 早停,用同口径 r2 当基准算 Δ,不和 4 轮的 56.1 比绝对值;逐轮中间图按 governance 记录重建;端到端 token/时间是估算,上下文效率(6.8×)与构建 token 是精确值。交接文档的进化消融旧估值(50.x)已证伪作废。</div></div>')

FOOT = '<p class=muted style="margin-top:36px">数据源:experiments/analysis/{ABLATION_REPORT, EVOLUTION_LEDGER, DIFFICULTY_BREAKDOWN, EFFICIENCY, CONVERGENCE}.md + figs/。本页由 build_report.py 生成,数据刷新可重跑。</p>'

HTML = ("<!doctype html><html lang=zh><head><meta charset=utf-8><title>SkillStrata 实验综合报告</title><style>"
        + CSS + "</style></head><body>" + HEADER + "<div class=wrap>"
        + RADAR + TLDR + S1 + Q1 + Q2 + Q3 + Q4 + S2 + Q5 + Q6 + S3 + S4 + Q7 + LONGTAIL + S5 + Q8 + EVO_TABLE + Q9 + FOOT
        + "</div></body></html>")

out = os.path.join(HERE, "SkillStrata_Report.html")
open(out, "w", encoding="utf-8").write(HTML)
print("wrote", out, "(%d KB) | nomerge=%s r2=%s | figs=%d" % (len(HTML) // 1024, nomerge, r2_str, len(FIG_ORDER)))
