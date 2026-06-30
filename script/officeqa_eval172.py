#!/usr/bin/env python3
"""Clean head-to-head: SkillStrata vs SkillOpt on officeqa, FULL 172 test, same engine+backend.

Reuses officeqa_curate's in-process qwen_chat OfficeQA adapter and per-item routed rollout, on the
full 172-item test split (== SkillOpt oqa_xmodel/xopqwen36v35b N=172). Evaluates two arms with the
ALREADY-curated v2 graph (12 deployed nodes): noskill (empty) vs SkillStrata (per-item routed).
Comparable SkillOpt qwen_chat numbers: initial 0.453 / opt 0.465 / optfull 0.506 (n=172).
"""
from __future__ import annotations
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import officeqa_curate as oc  # noqa: E402
from skillos.graph import SkillGraph  # noqa: E402
from skillos.persist import load_graph  # noqa: E402
from skillos.schema import Status  # noqa: E402

WORK = oc.WORK
GRAPH = WORK / "trained_graph.json"
W = 40


def main():
    oc.log("building adapter (qwen_chat / WYS) for 172-test head-to-head ...")
    adapter = oc.build_adapter()
    test = adapter.build_eval_env(env_num=172, split="test", seed=1)
    oc.log(f"test items = {len(test)} (full officeqa test split, SkillOpt-aligned)")

    graph = load_graph(str(GRAPH))
    dep = len([n for n in graph.nodes.values() if n.status == Status.DEPLOYED])
    oc.log(f"loaded v2 graph: {len(graph.nodes)} nodes, {dep} deployed")

    oc.log("=== ARM 1: noskill (172) ===")
    ns = oc.rollout_items(adapter, test, SkillGraph(), "test172_noskill", W)
    ns_acc = sum(r["hard"] for r in ns) / len(ns)
    oc.log(f"noskill_172 hard = {ns_acc:.4f} ({sum(r['hard'] for r in ns)}/{len(ns)})")

    oc.log("=== ARM 2: SkillStrata routed (172) ===")
    ss = oc.rollout_items(adapter, test, graph, "test172_skillstrata", W)
    ss_acc = sum(r["hard"] for r in ss) / len(ss)
    oc.log(f"skillstrata_172 hard = {ss_acc:.4f} ({sum(r['hard'] for r in ss)}/{len(ss)})")

    out = {
        "n_test": len(test), "deployed_nodes": dep,
        "ours_noskill_172": ns_acc, "ours_skillstrata_172": ss_acc,
        "ours_delta": ss_acc - ns_acc,
        "skillopt_qwen_initial_172": 0.4535, "skillopt_qwen_opt_172": 0.4651,
        "skillopt_qwen_optfull_172": 0.5058,
    }
    (WORK / "RESULT_172.json").write_text(json.dumps(out, indent=2))
    oc.log(f"=== DONE 172  noskill={ns_acc:.4f}  skillstrata={ss_acc:.4f}  delta={ss_acc-ns_acc:+.4f} "
           f"| SkillOpt initial=0.453 opt=0.465 optfull=0.506 ===")


if __name__ == "__main__":
    main()
