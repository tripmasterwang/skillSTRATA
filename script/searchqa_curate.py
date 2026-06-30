#!/usr/bin/env python3
"""SkillStrata x SearchQA — FULL from-zero curate (train=400 / val=200 gate / test=1400).

Reuses SkillOpt's SearchQA adapter as the in-process rollout/eval engine and drives
per-instance ROUTING over a SkillStrata graph with a 40-way thread pool. The curate
loop (rounds -> distill -> integrate -> validation_gate -> split) is skillos.curate.curate.

Splits = SkillOpt's data/searchqa_split (train=400/val=200/test=1400); test eval uses
the ENTIRE test split (env_num = adapter.get_dataloader().test_items size).
LLM = qwen3.6-35b xopqwen36v35b via Xunfei MaaS, lww key. SearchQA is inherently
offline: each item ships its own `context` passages, no external search tool/auth.
Per-item scoring field is `hard` (Exact Match as int), same as officeqa.

Same-engine SkillOpt comparison (qwen_chat xopqwen36v35b):
  self-train full test(1400) hard=0.7857; val(200) noskill 0.72 -> selfgen 0.75.

Usage: searchqa_curate.py [--selftest] [--rounds N] [--workers W]
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path("/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research")
SKILLSTRATA = ROOT / "projects/skillSTRATA"
SKILLOPT = ROOT / "projects/nonergodic-self-evolution/external/SkillOpt"
WORK = SKILLSTRATA / "runs/searchqa_full"
WKEY = (ROOT / "_shared/LLM_apis/.xunfei_api_key_lww").read_text().strip()
QWEN_BASE = "https://maas-api.cn-huabei-1.xf-yun.com/v2"
QWEN_MODEL = "xopqwen36v35b"

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
    """In-process SearchQA adapter on the lww qwen_chat backend (mirrors eval_only)."""
    for k, v in dict(
        TARGET_QWEN_CHAT_BASE_URL=QWEN_BASE, TARGET_QWEN_CHAT_API_KEY=WKEY,
        TARGET_QWEN_CHAT_MODEL=QWEN_MODEL, TARGET_QWEN_CHAT_TEMPERATURE="0",
        TARGET_QWEN_CHAT_ENABLE_THINKING="false", TARGET_QWEN_CHAT_MAX_TOKENS="16384",
        TARGET_QWEN_CHAT_TIMEOUT_SECONDS="90",
        OPTIMIZER_QWEN_CHAT_BASE_URL=QWEN_BASE, OPTIMIZER_QWEN_CHAT_API_KEY=WKEY,
        OPTIMIZER_QWEN_CHAT_MODEL=QWEN_MODEL, OPTIMIZER_QWEN_CHAT_TEMPERATURE="0",
        OPTIMIZER_QWEN_CHAT_TIMEOUT_SECONDS="90",
    ).items():
        os.environ[k] = v
    os.chdir(SKILLOPT)  # configs/data paths are relative to SkillOpt root
    import eval_only
    from skillopt.config import load_config, flatten_config, is_structured
    from skillopt.model import (configure_qwen_chat, set_target_backend, set_optimizer_backend,
                                set_target_deployment, set_optimizer_deployment, set_reasoning_effort)
    cfg = load_config("configs/searchqa/default.yaml")
    if is_structured(cfg):
        cfg = flatten_config(cfg)
    configure_qwen_chat(
        target_base_url=QWEN_BASE, target_api_key=WKEY, target_temperature=0,
        target_enable_thinking=False, target_max_tokens=16384, target_timeout_seconds=90,
        optimizer_base_url=QWEN_BASE, optimizer_api_key=WKEY, optimizer_temperature=0,
        optimizer_enable_thinking=False, optimizer_timeout_seconds=90)
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
def _route_skill(graph: SkillGraph, item: dict) -> str:
    if not any(n.status in (Status.DEPLOYED, Status.VALIDATED) for n in graph.nodes.values()):
        return ""  # blank seed -> noskill rollout
    return GraphRouter(graph).route(item.get("question", ""),
                                    item.get("task_type", "")).render()


def _rollout_one(adapter, item: dict, skill: str, tag: str) -> dict:
    uid = str(item.get("id") or item.get("uid"))
    out = WORK / tag / uid
    out.mkdir(parents=True, exist_ok=True)
    try:
        res = adapter.rollout([item], skill, str(out))
        r0 = res[0] if res else {}
        hard = int(r0.get("hard", 0) or 0)
    except Exception as e:
        log(f"  rollout EXC {uid}: {e}")
        hard = 0
    conv = out / "predictions" / uid / "conversation.json"
    trace = ""
    if conv.is_file():
        try:
            msgs = json.loads(conv.read_text())
            trace = "\n".join(f"[{m.get('role') or m.get('type')}] {m.get('content')}" for m in msgs)
        except Exception:
            pass
    return {"uid": uid, "hard": hard, "trace": trace, "question": item.get("question", "")}


def rollout_items(adapter, items, graph, tag, workers, phase_cap=1500) -> list[dict]:
    """Per-item routed rollouts on a 40-way pool. A phase barrier guard (phase_cap secs) prevents
    any single hung qwen call from wedging the whole curate: unfinished items are scored hard=0."""
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
        stuck = [str(items[i].get("id") or items[i].get("uid")) for f, i in futs.items() if out[i] is None]
        log(f"  [{tag}] PHASE-CAP {phase_cap}s hit: {len(stuck)} stuck -> hard=0 ({stuck})")
        for i in range(len(items)):
            if out[i] is None:
                out[i] = {"uid": str(items[i].get("id") or items[i].get("uid")),
                          "hard": 0, "trace": "", "question": items[i].get("question", "")}
    ex.shutdown(wait=False)
    return out


# ---------------------------------------------------------------- distill
_DISTILL_SYS = (
    "You distill REUSABLE SearchQA retrieval-QA skills from an agent's execution trace. SearchQA gives "
    "a question plus a set of retrieved context passages ([DOC] chunks) and asks for a short factual "
    "answer scored by Exact Match. Extract transferable tactics for FUTURE similar questions: "
    "query/keyword formulation against the passages, evidence reconciliation across conflicting or "
    "redundant DOCs, grounding the answer strictly in the passages, and ANSWER-FORMAT guards (return the "
    "minimal exact span inside <answer>...</answer>, no extra words, match the gold surface form). "
    "Distill transferable lessons and common failure fixes — NOT facts specific to this one question."
)
_OAI = None


def _client():
    global _OAI
    if _OAI is None:
        from openai import OpenAI
        _OAI = OpenAI(base_url=QWEN_BASE, api_key=WKEY, max_retries=3, timeout=90)
    return _OAI


def _distill_one(trace_text: str) -> list[Fragment]:
    if not trace_text.strip():
        return []
    user = ("Execution trace (truncated):\n---\n" + trace_text[:12000] + "\n---\n\n"
            "Return ONLY a JSON array (possibly empty) of lesson objects, each:\n"
            '{"name":"...","description":"...","body":"<concrete guidance>",'
            '"task_types":["query-formulation"|"evidence-reconciliation"|"grounding"|"answer-format"|"all"],'
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


MAX_FRAG = 12  # cap per round (mirror reference curate_driver --max-fragments-per-round=12);
               # an uncapped run dumps too many/round -> noisy library -> gate rejects every round.


def distill_fn(trajectories) -> list[Fragment]:
    """Distill FAILURES first (targeted fixes), then successes, capped at MAX_FRAG so the library
    stays precise enough to pass the val gate."""
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

    log("building adapter (qwen_chat / lww) ...")
    adapter = build_adapter()
    dl = adapter.get_dataloader()
    train = list(dl.train_items); val = list(dl.val_items)
    n_test = len(dl.test_items)
    test = adapter.build_eval_env(env_num=n_test, split="test", seed=1)
    log(f"splits: train={len(train)} val={len(val)} test={len(test)} (full SearchQA split)")

    if args.selftest:
        g = SkillGraph()
        r = rollout_items(adapter, train[:1], g, "selftest", 1)
        log(f"SELFTEST rollout: {r[0]['uid']} hard={r[0]['hard']} trace_chars={len(r[0]['trace'])}")
        log("SELFTEST OK" if r[0]["trace"] else "SELFTEST: no trace (check adapter)")
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
               "skillopt_qwen_selftrain_test1400": 0.7857,
               "skillopt_qwen_val_noskill": 0.72, "skillopt_qwen_val_selfgen": 0.75,
               "history": history}
    (WORK / "RESULT.json").write_text(json.dumps(summary, indent=2))
    log(f"=== DONE  noskill={base_acc:.4f}  skillstrata={ss_acc:.4f}  "
        f"delta={ss_acc-base_acc:+.4f}  deployed={deployed} ===")


if __name__ == "__main__":
    main()
