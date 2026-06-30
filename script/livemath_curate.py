#!/usr/bin/env python3
"""SkillStrata x LiveMathematicianBench — FULL from-zero curate.

Adapted from officeqa_curate.py. Reuses SkillOpt's LiveMathematicianBench adapter as the
in-process rollout/eval engine and drives per-instance ROUTING over a SkillStrata graph with a
40-way thread pool. The curate loop (rounds -> distill -> integrate -> validation_gate -> split)
is skillos.curate.curate.

Env quirks vs officeqa:
  * math MCQ, max_turns=1 (single long generation), correctness via evaluator EM -> result["hard"].
  * max_completion_tokens=32768 (qwen3.6 reasoning); call timeout raised 90s -> 300s.
  * splits come from data/livemathematicianbench_split (train/val/test); test = FULL test split.
  * routing key = item theorem_type (math category list); id field = item["id"].

LLM = qwen3.6-35b xopqwen36v35b via Xunfei MaaS, LWW2 key.

SkillOpt qwen/xunfei ladder (n=124, test): noskill 0.339 / human(initial) 0.282 / selfgen 0.508 /
skopt s1 0.484 / s2 0.532 / s3 0.484 / s4 0.532.

Usage: livemath_curate.py [--selftest] [--rounds N] [--workers W]
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path("/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research")
SKILLSTRATA = ROOT / "projects/skillSTRATA"
SKILLOPT = ROOT / "projects/nonergodic-self-evolution/external/SkillOpt"
WORK = SKILLSTRATA / "runs/livemath_full"
WKEY = (ROOT / "_shared/LLM_apis/.xunfei_api_key_lww2").read_text().strip()
QWEN_BASE = "https://maas-api.cn-huabei-1.xf-yun.com/v2"
QWEN_MODEL = "xopqwen36v35b"

# Long-reasoning env: raise per-call output budget + timeout well above officeqa's 16384/90s.
MAX_TOK = "32768"
CALL_TIMEOUT = "300"

sys.path.insert(0, str(SKILLSTRATA))
sys.path.insert(0, str(SKILLOPT))
sys.path.insert(0, str(SKILLOPT / "scripts"))

from skillos.curate import Fragment, curate            # noqa: E402
from skillos.graph import SkillGraph                    # noqa: E402
from skillos.router import GraphRouter                  # noqa: E402
from skillos.persist import save_graph                  # noqa: E402
from skillos.schema import Status                       # noqa: E402

WORK.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------- engine setup
def build_adapter():
    """In-process LiveMathematicianBench adapter on the LWW2 qwen_chat backend (mirrors eval_only).

    Token budget floored at 32768 (qwen3.6 reasoning); call timeout raised to 300s so long
    generations don't spuriously fail. QWEN_CHAT_OUTPUT_FLOOR/MAX_TOKENS keep the backend >=32768.
    """
    for k, v in dict(
        QWEN_CHAT_OUTPUT_FLOOR=MAX_TOK, QWEN_CHAT_MAX_TOKENS=MAX_TOK, QWEN_CHAT_TIMEOUT_SECONDS=CALL_TIMEOUT,
        TARGET_QWEN_CHAT_BASE_URL=QWEN_BASE, TARGET_QWEN_CHAT_API_KEY=WKEY,
        TARGET_QWEN_CHAT_MODEL=QWEN_MODEL, TARGET_QWEN_CHAT_TEMPERATURE="0",
        TARGET_QWEN_CHAT_ENABLE_THINKING="false", TARGET_QWEN_CHAT_MAX_TOKENS=MAX_TOK,
        TARGET_QWEN_CHAT_TIMEOUT_SECONDS=CALL_TIMEOUT,
        OPTIMIZER_QWEN_CHAT_BASE_URL=QWEN_BASE, OPTIMIZER_QWEN_CHAT_API_KEY=WKEY,
        OPTIMIZER_QWEN_CHAT_MODEL=QWEN_MODEL, OPTIMIZER_QWEN_CHAT_TEMPERATURE="0",
        OPTIMIZER_QWEN_CHAT_MAX_TOKENS=MAX_TOK, OPTIMIZER_QWEN_CHAT_TIMEOUT_SECONDS=CALL_TIMEOUT,
    ).items():
        os.environ[k] = v
    os.chdir(SKILLOPT)  # configs/data paths are relative to SkillOpt root
    import eval_only
    from skillopt.config import load_config, flatten_config, is_structured
    from skillopt.model import (configure_qwen_chat, set_target_backend, set_optimizer_backend,
                                set_target_deployment, set_optimizer_deployment, set_reasoning_effort)
    cfg = load_config("configs/livemathematicianbench/default.yaml")
    if is_structured(cfg):
        cfg = flatten_config(cfg)
    # Force the long-reasoning token/timeout budget through the qwen_chat config too.
    cfg["max_completion_tokens"] = int(MAX_TOK)
    configure_qwen_chat(
        target_base_url=QWEN_BASE, target_api_key=WKEY, target_temperature=0,
        target_enable_thinking=False, target_max_tokens=int(MAX_TOK),
        target_timeout_seconds=int(CALL_TIMEOUT),
        optimizer_base_url=QWEN_BASE, optimizer_api_key=WKEY, optimizer_temperature=0,
        optimizer_enable_thinking=False, optimizer_max_tokens=int(MAX_TOK),
        optimizer_timeout_seconds=int(CALL_TIMEOUT))
    set_target_backend("qwen_chat"); set_optimizer_backend("qwen_chat")
    set_target_deployment(QWEN_MODEL); set_optimizer_deployment(QWEN_MODEL)
    try:
        set_reasoning_effort(cfg.get("model_reasoning_effort") or "medium")
    except Exception:
        pass
    cfg["target_backend"] = "qwen_chat"; cfg["optimizer_backend"] = "qwen_chat"
    eval_only._register_builtins()
    adapter = eval_only.get_adapter(cfg)
    adapter.setup(cfg)
    adapter.workers = 1  # we parallelize across items ourselves
    return adapter


# ---------------------------------------------------------------- rollout / route
def _route_key(item: dict) -> str:
    tt = item.get("theorem_type") or []
    return " ".join(str(t) for t in tt) if isinstance(tt, list) else str(tt)


def _route_skill(graph: SkillGraph, item: dict) -> str:
    # Route only over DEPLOYED/VALIDATED nodes; blank seed -> noskill rollout.
    if not any(n.status in (Status.DEPLOYED, Status.VALIDATED) for n in graph.nodes.values()):
        return ""
    return GraphRouter(graph).route(item.get("question", ""), _route_key(item)).render()


def _rollout_one(adapter, item: dict, skill: str, tag: str) -> dict:
    uid = str(item.get("id"))
    out = WORK / tag / re.sub(r"[^\w.:-]", "_", uid)
    out.mkdir(parents=True, exist_ok=True)
    hard = 0
    resp = ""
    fail = ""
    try:
        res = adapter.rollout([item], skill, str(out))
        r0 = res[0] if res else {}
        hard = int(r0.get("hard", 0) or 0)
        resp = str(r0.get("response", "") or "")
        fail = str(r0.get("fail_reason", "") or "")
    except Exception as e:
        log(f"  rollout EXC {uid}: {e}")
    # Trace for distillation: question + model reasoning + (if wrong) the EM failure reason.
    trace = f"[question] {item.get('question','')}\n[response] {resp}"
    if fail:
        trace += f"\n[outcome] hard={hard} {fail}"
    return {"uid": uid, "hard": hard, "trace": trace if resp else "",
            "question": item.get("question", "")}


def rollout_items(adapter, items, graph, tag, workers, phase_cap=5400) -> list[dict]:
    """Per-item routed rollouts on a 40-way pool. Phase barrier guard (phase_cap secs) prevents a
    hung qwen call from wedging curate: unfinished items scored hard=0. phase_cap sized generously
    for 32768-token reasoning (each call up to 300s) but finite."""
    out = [None] * len(items)
    ex = ThreadPoolExecutor(max_workers=workers)
    futs = {ex.submit(_rollout_one, adapter, it, _route_skill(graph, it), tag): i
            for i, it in enumerate(items)}
    done = 0
    try:
        for f in as_completed(futs, timeout=phase_cap):
            out[futs[f]] = f.result(); done += 1
            if done % 10 == 0 or done == len(items):
                acc = sum(r["hard"] for r in out if r) / done
                log(f"  [{tag}] {done}/{len(items)} acc={acc:.3f}")
    except TimeoutError:
        stuck = [str(items[i].get("id")) for f, i in futs.items() if out[i] is None]
        log(f"  [{tag}] PHASE-CAP {phase_cap}s hit: {len(stuck)} stuck -> hard=0 ({stuck})")
        for i in range(len(items)):
            if out[i] is None:
                out[i] = {"uid": str(items[i].get("id")), "hard": 0, "trace": "",
                          "question": items[i].get("question", "")}
    ex.shutdown(wait=False)
    return out


# ---------------------------------------------------------------- distill
_DISTILL_SYS = (
    "You distill REUSABLE mathematical-reasoning skills from an agent's attempt at a math "
    "multiple-choice question (LiveMathematicianBench: research-level theorem/identity MCQs). "
    "Extract TRANSFERABLE tactics for FUTURE similar problems — sub-problem decomposition, "
    "theorem/identity/lemma application patterns, quantifier & equality-case checks, and common "
    "math mistakes with concrete guards (e.g. overstating a conclusion, dropping a hypothesis, "
    "sign/domain errors). Do NOT extract the specific answer or facts about this one question."
)
_OAI = None


def _client():
    global _OAI
    if _OAI is None:
        from openai import OpenAI
        _OAI = OpenAI(base_url=QWEN_BASE, api_key=WKEY, max_retries=3, timeout=int(CALL_TIMEOUT))
    return _OAI


def _distill_one(trace_text: str) -> list[Fragment]:
    if not trace_text.strip():
        return []
    user = ("Execution trace (truncated):\n---\n" + trace_text[:12000] + "\n---\n\n"
            "Return ONLY a JSON array (possibly empty) of lesson objects, each:\n"
            '{"name":"...","description":"...","body":"<concrete guidance>",'
            '"task_types":["decomposition"|"theorem-application"|"mistake-guard"|"reasoning"|"all"],'
            '"kind":"skill"|"fix"}')
    try:
        r = _client().chat.completions.create(
            model=QWEN_MODEL, messages=[{"role": "system", "content": _DISTILL_SYS},
                                        {"role": "user", "content": user}],
            extra_body={"enable_thinking": False}, max_tokens=2048, temperature=0.0)
        txt = r.choices[0].message.content or ""
    except Exception as e:
        log(f"  distill EXC: {e}"); return []
    for frag in re.findall(r"\[[\s\S]*\]", txt):
        try:
            arr = json.loads(frag)
        except Exception:
            continue
        out = [Fragment(name=str(o.get("name", "lesson"))[:80], description=str(o.get("description", "")),
                        body=str(o["body"]), task_types=list(o.get("task_types", []) or []),
                        kind=str(o.get("kind", "skill")))
               for o in arr if isinstance(o, dict) and o.get("body")]
        if out:
            return out
    return []


MAX_FRAG = 12  # cap per round; failures-first so the library stays precise enough to pass the gate.


def distill_fn(trajectories) -> list[Fragment]:
    """Distill FAILURES first (targeted fixes), then successes, capped at MAX_FRAG."""
    objs = (trajectories if (trajectories and isinstance(trajectories[0], dict))
            else [{"trace": t, "hard": 1} for t in trajectories])
    ordered = sorted(objs, key=lambda t: t.get("hard", 1))  # hard==0 (failed) first
    frags: list[Fragment] = []
    used = 0
    for t in ordered:
        if len(frags) >= MAX_FRAG:
            break
        if not (t.get("trace") or "").strip():
            continue
        frags += _distill_one(t["trace"]); used += 1
    frags = frags[:MAX_FRAG]
    log(f"  distilled {len(frags)} fragment(s) (cap {MAX_FRAG}) from {used} trace(s) [failures-first]")
    return frags


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=40)
    args = ap.parse_args()

    log("building adapter (qwen_chat / LWW2, max_tok=32768, timeout=300s) ...")
    adapter = build_adapter()
    dl = adapter.get_dataloader()
    train = list(dl.train_items); val = list(dl.val_items)
    full_test = dl.get_split_items("test")
    test = adapter.build_eval_env(env_num=len(full_test), split="test", seed=1)
    log(f"splits: train={len(train)} val={len(val)} test={len(test)} (FULL test split)")

    if args.selftest:
        g = SkillGraph()
        r = rollout_items(adapter, train[:1], g, "selftest", 1, phase_cap=600)
        log(f"SELFTEST rollout: id={r[0]['uid']} hard={r[0]['hard']} trace_chars={len(r[0]['trace'])}")
        log("SELFTEST OK (trace + scored hard via EM)" if r[0]["trace"]
            else "SELFTEST: no trace (check adapter)")
        return

    W = args.workers
    graph = SkillGraph()

    def rollout_fn(g, tasks):
        return rollout_items(adapter, tasks, g, f"train_r{g.step}", W)

    def val_score_fn(g):
        rs = rollout_items(adapter, val, g, f"val_s{g.step}", W)
        return sum(r["hard"] for r in rs) / max(len(rs), 1)

    # noskill test baseline (blank graph)
    log(f"=== noskill test baseline ({len(test)}) ===")
    base = rollout_items(adapter, test, SkillGraph(), "test_noskill", W)
    base_acc = sum(r["hard"] for r in base) / len(base)
    log(f"noskill test hard = {base_acc:.4f} ({sum(r['hard'] for r in base)}/{len(base)})")

    log(f"=== curate from zero: rounds={args.rounds} workers={W} ===")
    history = curate(graph, args.rounds, train, distill_fn, rollout_fn, val_score_fn,
                     do_split=True, do_merge=True, do_gate=True)
    save_graph(graph, str(WORK / "trained_graph.json"))
    (WORK / "history.json").write_text(json.dumps(history, indent=2))
    log(f"curate history: {json.dumps(history)}")

    # final skillstrata test (per-item routed over deployed graph)
    log(f"=== skillstrata test ({len(test)}, routed) ===")
    final = rollout_items(adapter, test, graph, "test_skillstrata", W)
    ss_acc = sum(r["hard"] for r in final) / len(final)
    deployed = len([n for n in graph.nodes.values() if n.status == Status.DEPLOYED])
    summary = {"noskill_hard": base_acc, "skillstrata_hard": ss_acc, "delta": ss_acc - base_acc,
               "deployed_nodes": deployed, "n_test": len(test), "rounds": args.rounds,
               "skillopt_ladder_n124": {"noskill": 0.3387, "human_initial": 0.2823,
                                        "selfgen": 0.5081, "skopt_s1": 0.4839, "skopt_s2": 0.5323,
                                        "skopt_s3": 0.4839, "skopt_s4": 0.5323},
               "history": history}
    (WORK / "RESULT.json").write_text(json.dumps(summary, indent=2))
    log(f"=== DONE  noskill={base_acc:.4f}  skillstrata={ss_acc:.4f}  "
        f"delta={ss_acc-base_acc:+.4f}  deployed={deployed} ===")


if __name__ == "__main__":
    main()
