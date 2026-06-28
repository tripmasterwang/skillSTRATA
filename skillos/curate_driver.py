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
from .verify import mint_checkpoints_from_traces

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
               router, env_extra, agent="cli_skillstrata", python_exe="python3"):
    """Run run_spreadsheetbench on a subset of ids with the current graph; return the log dir."""
    os.makedirs(out_dir, exist_ok=True)
    env = dict(os.environ)
    env["SKILLSTRATA_GRAPH_PATH"] = graph_path
    env["SKILLSTRATA_ROUTER"] = router
    env["SKILLSTRATA_ROUTE_DIR"] = os.path.join(out_dir, "routes")  # per-instance routed nodes
    env.update(env_extra)
    cmd = [
        python_exe, "run_spreadsheetbench.py",
        "--data_path", data, "--model", model, "--llm_client", "openai",
        "--agent", agent, "--instance_ids", ",".join(ids),
        "--workers", str(workers), "--max_turns", str(max_turns),
        "--generation_config", gen_config,
        "--output_dir", out_dir, "--log_dir", os.path.join(out_dir, "logs"),
        "--results_file", os.path.join(out_dir, "results.json"),
    ]
    subprocess.run(cmd, cwd=repo, env=env, check=False)
    return os.path.join(out_dir, "logs")


def _eval_accuracy(repo, data, out_dir, ids, python_exe="python3"):
    """Official eval restricted to ids -> instance accuracy (fully-correct / present)."""
    subprocess.run([python_exe, "evaluate_with_official.py", "--data_path", data,
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


def _attribute_heat(graph, out_dir, ids):
    """Tick per-skill heat from one rollout: each instance's ROUTED nodes get a success/failure
    credit from the official eval. This is the trace-layer signal ``mint_checkpoints_from_traces``
    reads to discover which nodes are error-prone (so checkpoints are LEARNED, not hand-set).
    Requires the route dump (SKILLSTRATA_ROUTE_DIR) + eval json to both exist for ``out_dir``."""
    jf = os.path.join(out_dir, "eval_official_results.json")
    rdir = os.path.join(out_dir, "routes")
    if not os.path.isfile(jf) or not os.path.isdir(rdir):
        return
    succ = {str(r.get("id")): bool(r.get("success"))
            for r in json.load(open(jf, encoding="utf-8")).get("results", [])}
    idset = set(ids)
    for rf in glob.glob(os.path.join(rdir, "*.json")):
        try:
            rj = json.load(open(rf, encoding="utf-8"))
        except Exception:
            continue
        iid = str(rj.get("id", ""))
        if iid not in idset or iid not in succ:
            continue
        for nid in rj.get("nodes", []):
            n = graph.nodes.get(nid)
            if n is None:
                continue
            if succ[iid]:
                n.heat.success_count += 1
            else:
                n.heat.failure_count += 1
            n.heat.last_used_step = graph.step


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
    # ---- ablation knobs (leave-one-out on the evolution mechanism; default = full system) ----
    ap.add_argument("--no-merge", action="store_true", help="INSERT-only: never consolidate near-dups")
    ap.add_argument("--no-split", action="store_true", help="disable SPLIT of divergent nodes")
    ap.add_argument("--no-gate", action="store_true", help="accept every round (disable validation gate)")
    ap.add_argument("--no-checkpoint", action="store_true", help="never mint verify-loop checkpoints")
    ap.add_argument("--agent", default="cli_skillstrata",
                    help="executor agent for train/val rollouts (e.g. cli_skillstrata_codex)")
    ap.add_argument("--python", default="python3",
                    help="python interpreter for the run_spreadsheetbench/eval subprocess")
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
        out = os.path.join(args.work_dir, f"train_r{rnd}")
        logdir = _run_agent(args.repo, args.data, train_ids, args.graph_out, out, args.model,
                            args.gen_config, args.workers, args.max_turns, "graph",
                            {"SKILLSTRATA_VERIFY_LOOP": "0"},  # OFF in train: keep failure signal honest
                            agent=args.agent, python_exe=args.python)
        _eval_accuracy(args.repo, args.data, out, train_ids, python_exe=args.python)  # writes eval json
        _attribute_heat(g, out, train_ids)                    # teach heat -> error-prone signal
        return sorted(glob.glob(os.path.join(logdir, "*.md")))

    def postcondition_fn(node):
        """qwen3.6 authors a concrete, workbook-checkable sub-goal for an error-prone skill."""
        try:
            r = client.chat.completions.create(
                model=args.model,
                messages=[{"role": "system", "content":
                           "You write ONE concrete, checkable success criterion (a postcondition) "
                           "for a spreadsheet sub-skill — verifiable by inspecting the resulting "
                           "workbook. One sentence, no preamble."},
                          {"role": "user", "content":
                           f"Skill: {node.name}\nGuidance:\n{node.body[:1500]}\n\n"
                           "Postcondition the agent's output must satisfy after applying this skill:"}],
                extra_body=gen_extra, max_tokens=200, temperature=0.0)
            return (r.choices[0].message.content or "").strip()
        except Exception:
            return ""

    def checkpoint_fn(g):
        return mint_checkpoints_from_traces(g, postcondition_fn=postcondition_fn)

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
                   args.gen_config, args.workers, args.max_turns, "graph",
                   {"SKILLSTRATA_VERIFY_LOOP": "1"},  # ON in val: gate under deployment conditions
                   agent=args.agent, python_exe=args.python)
        return _eval_accuracy(args.repo, args.data, outdir, val_ids, python_exe=args.python)

    history = curate(graph, args.rounds, train_ids, distill_fn, rollout_fn, val_score_fn,
                     do_split=not args.no_split, do_merge=not args.no_merge,
                     do_gate=not args.no_gate,
                     checkpoint_fn=(None if args.no_checkpoint else checkpoint_fn))
    save_graph(graph, args.graph_out)
    json.dump(history, open(os.path.join(args.work_dir, "curate_history.json"), "w"), indent=2)
    print("=== curate history ===")
    for h in history:
        print(h)
    print(f"trained graph -> {args.graph_out}")


if __name__ == "__main__":
    main()
