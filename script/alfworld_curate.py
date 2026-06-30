#!/usr/bin/env python3
"""SkillStrata x ALFWorld — FULL from-zero curate (train=39 / val=18 gate / test=134).

Mirrors officeqa_curate.py but targets SkillOpt's ALFWorld env (multi-turn embodied
text-game). Reuses SkillOpt's ALFWorldAdapter as the in-process rollout/eval engine and
drives PER-INSTANCE ROUTING over a SkillStrata graph with a 40-way thread pool. The curate
loop (rounds -> distill -> integrate -> validation_gate -> split) is skillos.curate.curate.

Splits come from SkillOpt's data/alfworld_path_split (train=39 / val=18 / test=134); test
eval uses the ENTIRE 134-item test split. Each item rolls out as its OWN single-env
ALFWorldBatchRun so it can carry its own routed skill.

LLM = qwen3.6-35b xopqwen36v35b via Xunfei MaaS (direct), LWW3 key, THINKING OFF (required:
alfworld parses literal <think>..</think><action>..</action>; thinking-on diverts CoT to
reasoning_content and BREAKS the parse -> 0 score). 90s call timeout.

Usage: alfworld_curate.py [--selftest] [--rounds N] [--workers W]
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path("/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research")
SKILLSTRATA = ROOT / "projects/skillSTRATA"
SKILLOPT = ROOT / "projects/nonergodic-self-evolution/external/SkillOpt"
WORK = SKILLSTRATA / "runs/alfworld_full"
WKEY = (ROOT / "_shared/LLM_apis/.xunfei_api_key_lww3").read_text().strip()
QWEN_BASE = "https://maas-api.cn-huabei-1.xf-yun.com/v2"
QWEN_MODEL = "xopqwen36v35b"
ALFWORLD_DATA = str(SKILLOPT / "data/alfworld_data")  # gamefiles are relative to this

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
    """In-process ALFWorld adapter on the LWW3 qwen_chat backend, thinking OFF."""
    os.environ["ALFWORLD_DATA"] = ALFWORLD_DATA
    for k, v in dict(
        # bare QWEN_CHAT_* mirror the harness's alfworld qwen_chat env exactly
        QWEN_CHAT_BASE_URL=QWEN_BASE, QWEN_CHAT_API_KEY=WKEY, QWEN_CHAT_MODEL=QWEN_MODEL,
        QWEN_CHAT_TEMPERATURE="0", QWEN_CHAT_ENABLE_THINKING="false",
        QWEN_CHAT_MAX_TOKENS="16384", QWEN_CHAT_TIMEOUT_SECONDS="90",
        TARGET_QWEN_CHAT_BASE_URL=QWEN_BASE, TARGET_QWEN_CHAT_API_KEY=WKEY,
        TARGET_QWEN_CHAT_MODEL=QWEN_MODEL, TARGET_QWEN_CHAT_TEMPERATURE="0",
        TARGET_QWEN_CHAT_ENABLE_THINKING="false", TARGET_QWEN_CHAT_MAX_TOKENS="16384",
        TARGET_QWEN_CHAT_TIMEOUT_SECONDS="90",
        OPTIMIZER_QWEN_CHAT_BASE_URL=QWEN_BASE, OPTIMIZER_QWEN_CHAT_API_KEY=WKEY,
        OPTIMIZER_QWEN_CHAT_MODEL=QWEN_MODEL, OPTIMIZER_QWEN_CHAT_TEMPERATURE="0",
        OPTIMIZER_QWEN_CHAT_ENABLE_THINKING="false", OPTIMIZER_QWEN_CHAT_TIMEOUT_SECONDS="90",
    ).items():
        os.environ[k] = v
    os.chdir(SKILLOPT)  # configs/data paths are relative to SkillOpt root
    import eval_only
    from skillopt.config import load_config, flatten_config, is_structured
    from skillopt.model import (configure_qwen_chat, set_target_backend, set_optimizer_backend,
                                set_target_deployment, set_optimizer_deployment, set_reasoning_effort)
    cfg = load_config("configs/alfworld/default.yaml")
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
    adapter.workers = 1            # one env per item; we parallelize across items ourselves
    adapter.max_api_workers = 1
    return adapter


# ---------------------------------------------------------------- rollout / route
def _single_run(adapter, item: dict):
    """Build a single-env ALFWorldBatchRun for one split item (carries one routed skill)."""
    from skillopt.envs.alfworld.adapter import ALFWorldBatchRun
    gf = str(item.get("gamefile") or "")
    eval_dataset, is_train = adapter._infer_dataset_from_gamefile(gf)
    enriched = adapter._comparison_items([item])
    return ALFWorldBatchRun(
        env_num=1, eval_dataset=eval_dataset, seed=1, is_train=is_train, workers=1,
        specific_gamefiles=[gf], result_ids=[str(item.get("id"))], items=enriched)


def _route_skill(graph: SkillGraph, item: dict) -> str:
    if not any(n.status in (Status.DEPLOYED, Status.VALIDATED) for n in graph.nodes.values()):
        return ""  # blank seed -> noskill rollout
    q = str(item.get("task_description") or item.get("task_type") or "")
    return GraphRouter(graph).route(q, item.get("task_type", "")).render()


def _trace_from_conv(conv_path: Path, task_desc: str) -> str:
    if not conv_path.is_file():
        return ""
    try:
        steps = json.loads(conv_path.read_text())
    except Exception:
        return ""
    lines = [f"Task: {task_desc}"] if task_desc else []
    for s in steps:
        act = s.get("action"); rsn = s.get("reasoning") or ""
        fb = (s.get("env_feedback") or "").strip()
        lines.append(f"[step {s.get('step')}] think={rsn} | action={act} | feedback={fb}"
                     f"{'  <<DONE>>' if s.get('done') else ''}")
    return "\n".join(lines)


def _rollout_one(adapter, item: dict, skill: str, tag: str) -> dict:
    uid = str(item.get("id"))
    safe = uid.replace(":", "_").replace("/", "_")
    out = WORK / tag / safe
    out.mkdir(parents=True, exist_ok=True)
    hard = 0
    try:
        res = adapter.rollout(_single_run(adapter, item), skill, str(out))
        r0 = res[0] if res else {}
        hard = int(r0.get("hard", 0) or 0)
    except Exception as e:
        log(f"  rollout EXC {uid}: {e}")
    task_desc = item.get("task_description") or item.get("task_type", "")
    # conversation lands under predictions/<result_id == uid>/conversation.json
    trace = _trace_from_conv(out / "predictions" / uid / "conversation.json", task_desc)
    return {"uid": uid, "hard": hard, "trace": trace, "question": task_desc,
            "task_type": item.get("task_type", "")}


def rollout_items(adapter, items, graph, tag, workers, phase_cap=7200) -> list[dict]:
    """Per-item routed rollouts on a thread pool. A phase barrier guard (phase_cap secs) stops any
    single hung qwen/env from wedging the whole curate: unfinished items are scored hard=0.
    alfworld episodes are multi-turn (<=50 steps) so phase_cap is generous but finite."""
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
                          "question": items[i].get("task_type", ""),
                          "task_type": items[i].get("task_type", "")}
    ex.shutdown(wait=False)
    return out


# ---------------------------------------------------------------- distill
_DISTILL_SYS = (
    "You distill REUSABLE ALFWorld embodied-agent skills from an execution trace. ALFWorld is a "
    "multi-turn text game where the agent must navigate a room and complete a household task "
    "(e.g. pick_and_place, pick_two_obj_and_place, look_at_obj_in_light, pick_heat/cool/clean_then_"
    "place_in_recep). Each turn the agent emits <think>...</think><action>...</action>. Extract "
    "TRANSFERABLE sub-task workflows and action-sequence lessons for FUTURE similar tasks — e.g. "
    "search order for finding objects, how to heat/cool/clean an object then place it, how to use a "
    "desklamp to examine, recovering from 'Nothing happens' feedback, valid action grammar (go to X, "
    "take X from Y, put X in/on Y, open/close, heat/cool/clean X with Y, use X) — NOT facts about "
    "this one room layout."
)
_OAI = None


def _client():
    global _OAI
    if _OAI is None:
        from openai import OpenAI
        _OAI = OpenAI(base_url=QWEN_BASE, api_key=WKEY, max_retries=3, timeout=90)
    return _OAI


_TASK_TYPES = ("pick_and_place|pick_two_obj_and_place|look_at_obj_in_light|"
               "pick_heat_then_place_in_recep|pick_cool_then_place_in_recep|"
               "pick_clean_then_place_in_recep|navigation|all")


def _distill_one(trace_text: str) -> list[Fragment]:
    if not trace_text.strip():
        return []
    user = ("Execution trace (truncated):\n---\n" + trace_text[:12000] + "\n---\n\n"
            "Return ONLY a JSON array (possibly empty) of lesson objects, each:\n"
            '{"name":"...","description":"...","body":"<concrete reusable workflow / action-sequence '
            'guidance>","task_types":["' + _TASK_TYPES.replace("|", '"|"') + '"],"kind":"skill"|"fix"}')
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


MAX_FRAG = 12  # cap per round so the library stays precise enough to pass the val gate.


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

    log("building adapter (qwen_chat / LWW3 / thinking OFF) ...")
    adapter = build_adapter()
    dl = adapter.get_dataloader()
    train = list(dl.train_items); val = list(dl.val_items); test = list(dl.test_items)
    log(f"splits: train={len(train)} val={len(val)} test={len(test)} (SkillOpt alfworld_path_split)")

    if args.selftest:
        # 1) verify skill injection lands in the agent prompt via a monkeypatched chat_target
        import skillopt.envs.alfworld.rollout as alf_roll
        captured = {"sys": [], "user": []}
        _orig = alf_roll.chat_target

        def _spy(system, user, **kw):
            captured["sys"].append(system); captured["user"].append(user)
            return _orig(system=system, user=user, **kw)
        alf_roll.chat_target = _spy
        DUMMY = "DUMMY_SKILL_MARKER_XYZ: always go to the most likely receptacle first."
        g = SkillGraph()
        # force a routed skill string regardless of graph state for the injection probe
        r = _rollout_one(adapter, train[0], DUMMY, "selftest")
        alf_roll.chat_target = _orig
        inj = any(DUMMY.split(":")[0] in (u or "") for u in captured["user"])
        # 2) confirm thinking-off: model emitted real <action> tags (not the missing-action fallback)
        conv_p = WORK / "selftest" / str(train[0].get("id")).replace(":", "_") / "predictions" / \
            str(train[0].get("id")) / "conversation.json"
        real_action = False
        if conv_p.is_file():
            steps = json.loads(conv_p.read_text())
            real_action = any("<action>" in (s.get("model_response") or "")
                              and "missing action tag" not in (s.get("model_response") or "")
                              for s in steps)
        log(f"SELFTEST rollout: uid={r['uid']} hard={r['hard']} trace_chars={len(r['trace'])} "
            f"steps={len(captured['user'])}")
        log(f"SELFTEST skill_injection={'OK' if inj else 'FAIL'}  "
            f"thinking_off_real_action={'OK' if real_action else 'FAIL'}  "
            f"scoring_field=hard(={r['hard']})")
        log("SELFTEST OK" if (r["trace"] and inj and real_action) else "SELFTEST: CHECK ABOVE")
        return

    W = args.workers
    graph = SkillGraph()

    def rollout_fn(g, tasks):
        return rollout_items(adapter, tasks, g, f"train_r{g.step}", W)

    def val_score_fn(g):
        rs = rollout_items(adapter, val, g, f"val_s{g.step}", W)
        return sum(r["hard"] for r in rs) / max(len(rs), 1)

    # noskill test baseline (blank graph) over the FULL 134-item test split
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
               "skillopt_claude_noskill_40": 0.775, "skillopt_claude_ckpt_40": 0.880,
               "skillopt_codex_noskill_40": 0.775, "skillopt_codex_ckpt_40": 0.875,
               "history": history}
    (WORK / "RESULT.json").write_text(json.dumps(summary, indent=2))
    log(f"=== DONE  noskill={base_acc:.4f}  skillstrata={ss_acc:.4f}  "
        f"delta={ss_acc-base_acc:+.4f}  deployed={deployed} ===")


if __name__ == "__main__":
    main()
