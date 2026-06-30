#!/usr/bin/env python3
"""SkillStrata x OfficeQA — TRAJECTORY-CHAIN-GRAPH variant.

The 'draw chains -> merge -> select subgraph' paradigm (distinct from distill-into-nodes):
  A  rollout TRAIN items with no skill -> per-item conversation.json + results.jsonl(success)
  B  LLM draws each trajectory into a canonical operation-step CHAIN (running node registry)
  C  chains merge into one DiGraph (TEMPORAL_ORDER, success-weighted)  [skillos.trajgraph]
  D  per TEST item: seed by question -> consensus success-path SUBGRAPH -> render SKILL.md
  E  eval_only on that one item with its routed skill; compare to a no-skill baseline.

Usage:
  python officeqa_trajgraph.py rollout-train --n 50
  python officeqa_trajgraph.py build
  python officeqa_trajgraph.py eval --n 15
Engine/keys reuse officeqa_skel.py (SkillOpt eval_only, qwen3.6-35b wys via Xunfei MaaS).
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path("/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research")
SKILLSTRATA = ROOT / "projects/skillSTRATA"
SKILLOPT = ROOT / "projects/nonergodic-self-evolution/external/SkillOpt"
RUN = SKILLSTRATA / "runs/officeqa_trajgraph"
WKEY = (ROOT / "_shared/LLM_apis/.xunfei_api_key_wys").read_text().strip()
QWEN_BASE = "https://maas-api.cn-huabei-1.xf-yun.com/v2"
QWEN_MODEL = "xopqwen36v35b"

sys.path.insert(0, str(SKILLSTRATA))
from skillos.trajgraph import ChainGraph, draw_chain  # noqa: E402

RUN.mkdir(parents=True, exist_ok=True)
EMPTY_SKILL = RUN / "empty_skill.md"


def _qwen():
    from openai import OpenAI
    return OpenAI(base_url=QWEN_BASE, api_key=WKEY)


def _eval_env() -> dict:
    env = dict(os.environ)
    env.update(
        TARGET_QWEN_CHAT_BASE_URL=QWEN_BASE, TARGET_QWEN_CHAT_API_KEY=WKEY,
        TARGET_QWEN_CHAT_MODEL=QWEN_MODEL, TARGET_QWEN_CHAT_TEMPERATURE="0",
        TARGET_QWEN_CHAT_ENABLE_THINKING="false",
        OPTIMIZER_QWEN_CHAT_BASE_URL=QWEN_BASE, OPTIMIZER_QWEN_CHAT_API_KEY=WKEY,
        OPTIMIZER_QWEN_CHAT_MODEL=QWEN_MODEL)
    return env


def _ensure_empty_skill():
    if not EMPTY_SKILL.is_file():
        EMPTY_SKILL.write_text("# (no skill)\n")


def _eval_only(skill: Path, out: Path, split: str, n: int, split_dir: str | None = None):
    cmd = [sys.executable, "scripts/eval_only.py", "--config", "configs/officeqa/default.yaml",
           "--skill", str(skill), "--split", split,
           "--cfg-options", "env.data_dirs=data/officeqa_hf", "env.max_tool_turns=10",
           "env.exec_timeout=300"] + ([f"env.split_dir={split_dir}"] if split_dir else []) + [
           "--target_backend", "qwen_chat", "--target_model", QWEN_MODEL,
           "--optimizer_backend", "qwen_chat", "--optimizer_model", QWEN_MODEL,
           "--test_env_num", str(n), "--workers", "4", "--seed", "1", "--out_root", str(out)]
    subprocess.run(cmd, cwd=str(SKILLOPT), env=_eval_env(), check=False)


def _flatten(conv_path: Path) -> str:
    msgs = json.loads(conv_path.read_text())
    out = []
    for m in msgs:
        c = m.get("content")
        if isinstance(c, list):
            c = " ".join(str(p.get("text", p) if isinstance(p, dict) else p) for p in c)
        out.append(f"[{m.get('role')}] {c}")
    return "\n".join(out)


# ----------------------------------------------------------------- A: rollout
def rollout_train(n: int):
    _ensure_empty_skill()
    out = RUN / "train_rollout"
    print(f"=== STAGE A: rollout {n} TRAIN items (no skill) -> {out} ===")
    _eval_only(EMPTY_SKILL, out, "train", n)
    rj = out / "results.jsonl"
    print(f"  done. results.jsonl={'ok' if rj.is_file() else 'MISSING'}")


# ----------------------------------------------------- B+C: draw + merge graph
def build():
    out = RUN / "train_rollout"
    rj = out / "results.jsonl"
    if not rj.is_file():
        # fall back to the skeleton's existing train rollout if ours is absent
        alt = SKILLSTRATA / "runs/officeqa_skel/train_rollout"
        if (alt / "results.jsonl").is_file():
            out, rj = alt, alt / "results.jsonl"
            print(f"  [build] using existing rollout at {out}")
    rows = [json.loads(l) for l in rj.open()]
    pred = out / "predictions"
    client = _qwen()
    graph = ChainGraph()
    print(f"=== STAGE B+C: draw {len(rows)} trajectories -> chain graph ===")

    def _draw(question, trace_text, registry):
        with ThreadPoolExecutor(max_workers=1) as ex:
            try:
                return ex.submit(draw_chain, client, QWEN_MODEL, question, trace_text, registry).result(timeout=90)
            except Exception as e:
                print(f"    draw failed/timeout: {e}")
                return []

    drawn = 0
    for r in rows:
        uid = r.get("id")
        conv = pred / uid / "conversation.json"
        if not conv.is_file():
            continue
        success = str(r.get("hard", "0")) in ("1", "1.0", "True", "true")
        chain = _draw(r.get("question", ""), _flatten(conv), graph.registry_text())
        if not chain:
            continue
        graph.add_chain(chain, success=success, task_type=str(r.get("task_type", "")),
                        question=r.get("question", ""))
        drawn += 1
        print(f"  [{uid}] success={success} chain={[c['id'] for c in chain]}")
    graph.save(str(RUN / "graph.json"))
    st = graph.stats()
    print(f"  drawn={drawn} | nodes={st['nodes']} edges={st['edges']}")
    print(f"  hubs(top): {st['hub_nodes']}")
    # sample routed skill on test[0]
    test_items = json.loads((SKILLOPT / "data/officeqa_split/test/items.json").read_text())
    q0 = test_items[0].get("question", "")
    sub = graph.select_subgraph(q0)
    (RUN / "sample_routed_skill.md").write_text(graph.render_skill(sub, q0))
    print(f"  sample route for test[0] q={q0[:70]!r}\n    -> subgraph={sub}")


# --------------------------------------------------- D+E: route + eval per item
def evaluate(n: int):
    _ensure_empty_skill()
    graph = ChainGraph.load(str(RUN / "graph.json"))
    test_items = json.loads((SKILLOPT / "data/officeqa_split/test/items.json").read_text())[:n]
    base_split = SKILLOPT / "data/officeqa_split"
    skills_dir = RUN / "routed_skills"; skills_dir.mkdir(exist_ok=True)
    splits_dir = RUN / "item_splits"; splits_dir.mkdir(exist_ok=True)
    print(f"=== STAGE D+E: route + eval {len(test_items)} test items (routed vs no-skill) ===")

    routed_hard = []
    for i, item in enumerate(test_items):
        q = item.get("question", "")
        sub = graph.select_subgraph(q)
        skill_md = graph.render_skill(sub, q) or "# (empty route)\n"
        sp = skills_dir / f"item{i:02d}.md"; sp.write_text(skill_md)
        # one-item split dir
        isd = splits_dir / f"item{i:02d}"
        for s in ("train", "val", "test"):
            (isd / s).mkdir(parents=True, exist_ok=True)
            src = base_split / s / "items.json"
            (isd / s / "items.json").write_text(src.read_text())
        (isd / "test" / "items.json").write_text(json.dumps([item]))
        out = RUN / "eval_routed" / f"item{i:02d}"
        _eval_only(sp, out, "test", 1, split_dir=str(isd))
        res = out / "results.jsonl"
        hv = None
        if res.is_file():
            rr = [json.loads(l) for l in res.open()]
            if rr:
                hv = int(str(rr[0].get("hard", "0")) in ("1", "1.0", "True", "true"))
        routed_hard.append(hv)
        print(f"  [item{i:02d}] uid={item.get('uid')} sub={sub} hard={hv}")

    # no-skill baseline on the same first-n test items
    out_b = RUN / "eval_noskill"
    _eval_only(EMPTY_SKILL, out_b, "test", n)
    base_hard = []
    rb = out_b / "results.jsonl"
    if rb.is_file():
        base_hard = [int(str(x.get("hard", "0")) in ("1", "1.0", "True", "true"))
                     for x in (json.loads(l) for l in rb.open())]

    rh = [x for x in routed_hard if x is not None]
    summary = {
        "n": n,
        "routed_hard_mean": round(sum(rh) / len(rh), 4) if rh else None,
        "routed_hard": routed_hard,
        "noskill_hard_mean": round(sum(base_hard) / len(base_hard), 4) if base_hard else None,
        "noskill_hard": base_hard,
    }
    (RUN / "eval_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"=== SUMMARY ===\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["rollout-train", "build", "eval"])
    ap.add_argument("--n", type=int, default=15)
    a = ap.parse_args()
    if a.stage == "rollout-train":
        rollout_train(a.n)
    elif a.stage == "build":
        build()
    else:
        evaluate(a.n)
