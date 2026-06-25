"""Server-side driver for FROM-ZERO curate (API-backed).

Wires the injected callables of ``skillos.curate`` to the real system:
  * rollout_fn  -> run the Trace2Skill agent on the TRAIN ids with the CURRENT graph (loaded from
                   disk via SKILLSTRATA_GRAPH_PATH); trajectories = the per-task chat logs.
  * distill_fn  -> qwen3.6 reads each trajectory and emits reusable skill Fragments (our MAP).
  * val_score_fn-> run the agent on the VAL ids with the candidate graph + official eval -> accuracy.

Each round saves the evolving graph to ``--graph-out``. After E rounds the trained graph is the
artifact the test phase routes over. Run via ``script/run_curate.sh`` (sets endpoint/ids/paths).

    python3 -m skillos.curate_driver --repo <Trace2Skill> --data <verified_400> \
        --train-ids ids.txt --val-ids ids.txt --rounds 4 --graph-out trained_graph.json \
        --model qwen3.6-35b-a3b --gen-config gen.json --workers 8
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess

from .curate import Fragment, curate
from .graph import SkillGraph
from .persist import load_graph, save_graph

_DISTILL_SYS = (
    "You distill REUSABLE spreadsheet skills from an agent's execution trace. Read the trace "
    "(task, the python it ran, errors, whether it succeeded) and extract 0-2 concise, GENERAL "
    "lessons that would help on FUTURE similar tasks — not facts about this one spreadsheet. "
    "Prefer lessons from mistakes/recoveries. Each lesson is a small skill module."
)


def _read_ids(path):
    with open(path, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip()]


def _run_agent(repo, data, ids, graph_path, out_dir, model, gen_config, workers, max_turns,
               router, env_extra):
    """Run run_spreadsheetbench on a subset of ids with the current graph; return the log dir."""
    os.makedirs(out_dir, exist_ok=True)
    env = dict(os.environ)
    env["SKILLSTRATA_GRAPH_PATH"] = graph_path
    env["SKILLSTRATA_ROUTER"] = router
    env.update(env_extra)
    cmd = [
        "python3", "run_spreadsheetbench.py",
        "--data_path", data, "--model", model, "--llm_client", "openai",
        "--agent", "cli_skillstrata", "--instance_ids", ",".join(ids),
        "--workers", str(workers), "--max_turns", str(max_turns),
        "--generation_config", gen_config,
        "--output_dir", out_dir, "--log_dir", os.path.join(out_dir, "logs"),
        "--results_file", os.path.join(out_dir, "results.json"),
    ]
    subprocess.run(cmd, cwd=repo, env=env, check=False)
    return os.path.join(out_dir, "logs")


def _eval_accuracy(repo, data, out_dir, ids):
    """Official eval restricted to ids -> instance accuracy (fully-correct / present)."""
    subprocess.run(["python3", "evaluate_with_official.py", "--data_path", data,
                    "--output_dir", out_dir], cwd=repo, check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    jf = os.path.join(out_dir, "eval_official_results.json")
    if not os.path.isfile(jf):
        return 0.0
    d = json.load(open(jf, encoding="utf-8"))
    idset = set(ids)
    rs = [r for r in d.get("results", []) if str(r.get("id")) in idset]
    if not rs:
        return 0.0
    return sum(1 for r in rs if r.get("success")) / len(rs)


def _distill_trace(client, model, log_text, gen_extra):
    """One qwen3.6 call: trajectory -> list[Fragment]."""
    user = (
        "Execution trace (truncated):\n---\n" + log_text[:12000] + "\n---\n\n"
        "Return ONLY a JSON array (possibly empty) of lesson objects, each:\n"
        '{"name": "...", "description": "...", "body": "<concrete guidance>", '
        '"task_types": ["cell"|"sheet"|"formula"|"lookup"|"data"|"all"], "kind": "skill"|"fix"}'
    )
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": _DISTILL_SYS},
                      {"role": "user", "content": user}],
            extra_body=gen_extra, max_tokens=2048, temperature=0.0)
        txt = r.choices[0].message.content or ""
    except Exception:
        return []
    out = []
    for frag in __import__("re").findall(r"\[[\s\S]*\]", txt):
        try:
            arr = json.loads(frag)
        except Exception:
            continue
        for o in arr:
            if isinstance(o, dict) and o.get("body"):
                out.append(Fragment(
                    name=str(o.get("name", "lesson"))[:80], description=str(o.get("description", "")),
                    body=str(o["body"]), task_types=list(o.get("task_types", []) or []),
                    kind=str(o.get("kind", "skill"))))
        if out:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--train-ids", required=True)
    ap.add_argument("--val-ids", required=True)
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--graph-out", required=True)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--model", default="qwen3.6-35b-a3b")
    ap.add_argument("--gen-config", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-turns", type=int, default=15)
    ap.add_argument("--max-fragments-per-round", type=int, default=12)
    args = ap.parse_args()

    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "EMPTY"),
                    base_url=os.environ.get("OPENAI_BASE_URL"))
    gen_extra = json.load(open(args.gen_config)).get("extra_body", {})
    train_ids, val_ids = _read_ids(args.train_ids), _read_ids(args.val_ids)
    os.makedirs(args.work_dir, exist_ok=True)

    graph = SkillGraph()                     # S0: blank seed
    save_graph(graph, args.graph_out)

    def rollout_fn(g, _tasks):
        save_graph(g, args.graph_out)        # agent loads the current graph from disk
        rnd = g.step
        logdir = _run_agent(args.repo, args.data, train_ids, args.graph_out,
                            os.path.join(args.work_dir, f"train_r{rnd}"), args.model,
                            args.gen_config, args.workers, args.max_turns, "graph", {})
        return sorted(glob.glob(os.path.join(logdir, "*.md")))

    def distill_fn(log_paths):
        frags = []
        for lp in log_paths:
            if len(frags) >= args.max_fragments_per_round:
                break
            txt = open(lp, encoding="utf-8", errors="ignore").read()
            frags.extend(_distill_trace(client, args.model, txt, gen_extra))
        return frags[: args.max_fragments_per_round]

    def val_score_fn(g):
        save_graph(g, args.graph_out)
        rnd = g.step
        outdir = os.path.join(args.work_dir, f"val_r{rnd}")
        _run_agent(args.repo, args.data, val_ids, args.graph_out, outdir, args.model,
                   args.gen_config, args.workers, args.max_turns, "graph", {})
        return _eval_accuracy(args.repo, args.data, outdir, val_ids)

    history = curate(graph, args.rounds, train_ids, distill_fn, rollout_fn, val_score_fn)
    save_graph(graph, args.graph_out)
    json.dump(history, open(os.path.join(args.work_dir, "curate_history.json"), "w"), indent=2)
    print("=== curate history ===")
    for h in history:
        print(h)
    print(f"trained graph -> {args.graph_out}")


if __name__ == "__main__":
    main()
