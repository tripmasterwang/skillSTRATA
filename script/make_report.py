#!/usr/bin/env python3
"""Assemble a single self-contained RESULTS.md from the from-zero curate artifacts.

Designed for an isolated server that can only transfer TEXT: the report embeds the curate
history, the learned 3-layer graph summary + skill list, the held-out test score, and the full
trained-graph JSON (so the graph can be reconstructed by pasting the text back).

    python3 make_report.py --out RESULTS.md --graph trained_graph.json \
        --history curate_history.json --eval-json test_280/eval_official_results.json \
        --test-ids skillopt_test_ids.txt --meta "model=...,endpoint=...,rounds=4,date=..."
"""
import argparse
import json
import os


def _load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--graph", default="")
    ap.add_argument("--history", default="")
    ap.add_argument("--eval-json", default="")
    ap.add_argument("--test-ids", default="")
    ap.add_argument("--meta", default="")
    ap.add_argument("--include-graph-json", type=int, default=1)
    args = ap.parse_args()

    L = ["# SkillStrata (from-zero) — RESULTS", ""]

    # ---- run config ----
    L += ["## Run config", ""]
    for kv in args.meta.split(","):
        if "=" in kv:
            k, v = kv.split("=", 1)
            L.append(f"- **{k.strip()}**: {v.strip()}")
    L.append("")

    # ---- curate history (per-round self-evolution evidence) ----
    hist = _load(args.history)
    L += ["## Curate history (3-layer graph grown from a blank seed)", ""]
    if hist:
        L += ["| round | inserted | merged | accepted | val acc | deployed |",
              "|------:|---------:|-------:|:--------:|--------:|---------:|"]
        for h in hist:
            acc = "✅" if h.get("accepted") else "❌"
            L.append(f"| {h.get('round')} | {h.get('inserted')} | {h.get('merged')} | {acc} "
                     f"| {h.get('val')} | {h.get('deployed')} |")
        L.append("")
        L.append("> val acc ↑ over rounds = self-evolution is working; ❌ = round rejected by the "
                 "validation gate (no val improvement).")
    else:
        L.append("_(no curate_history.json — training may not have completed)_")
    L.append("")

    # ---- trained graph summary + learned skills ----
    g = _load(args.graph)
    L += ["## Trained 3-layer graph", ""]
    if g:
        skills = g.get("skills", [])
        by_status = {}
        for s in skills:
            by_status[s.get("status", "?")] = by_status.get(s.get("status", "?"), 0) + 1
        L.append(f"- nodes: **{len(skills)}** " +
                 ", ".join(f"{k}={v}" for k, v in sorted(by_status.items())))
        L.append(f"- capability edges: **{len(g.get('capability_edges', []))}** "
                 f"| governance decisions: **{len(g.get('governance', []))}**")
        L.append("")
        L += ["### Learned skills (capability layer)", "",
              "| id | status | task_types | description |",
              "|----|--------|-----------|-------------|"]
        for s in skills:
            desc = (s.get("description", "") or "").replace("|", "\\|")[:90]
            tt = ",".join(s.get("task_types", []))
            L.append(f"| `{s.get('id')}` | {s.get('status')} | {tt} | {desc} |")
        L.append("")
    else:
        L.append("_(no trained graph JSON)_")
    L.append("")

    # ---- held-out test result ----
    ev = _load(args.eval_json)
    L += ["## Test result — 280 held-out (react-agent retriever)", ""]
    if ev:
        results = ev.get("results", [])
        ids = set()
        if args.test_ids and os.path.isfile(args.test_ids):
            ids = {ln.strip() for ln in open(args.test_ids, encoding="utf-8") if ln.strip()}
        sub = [r for r in results if (not ids) or str(r.get("id")) in ids]
        n = len(sub)
        correct = sum(1 for r in sub if r.get("success"))
        L.append(f"- **Instance accuracy: {correct / n * 100:.1f}%  ({correct}/{n})**" if n
                 else "- _(no instances scored)_")
        # by type
        bt = {}
        for r in sub:
            t = (r.get("instruction_type") or "?").split()[0]
            bt.setdefault(t, [0, 0])
            bt[t][1] += 1
            bt[t][0] += 1 if r.get("success") else 0
        for t, (c, tot) in sorted(bt.items()):
            L.append(f"  - {t}: {c / tot * 100:.1f}% ({c}/{tot})")
        L.append("")
        L.append("> Compare to SkillOpt's number on the SAME 280 split + same backbone.")
    else:
        L.append("_(no test eval — test phase may not have completed)_")
    L.append("")

    # ---- full trained graph JSON (for reconstruction over a text-only channel) ----
    if args.include_graph_json and g is not None:
        L += ["## Trained graph JSON (paste back to reconstruct)", "",
              "<details><summary>trained_graph.json</summary>", "",
              "```json", json.dumps(g, ensure_ascii=False, indent=1), "```", "", "</details>", ""]

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"[report] wrote {args.out} ({os.path.getsize(args.out)} bytes)")


if __name__ == "__main__":
    main()
