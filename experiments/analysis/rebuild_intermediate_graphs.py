#!/usr/bin/env python3
"""Reconstruct the INTERMEDIATE curate graphs (end of round r1, r2) from the final trained_graph +
evolution_ledger, so we can test them and draw the per-round improvement curve on the held-out 280.

A skill is in the round-r graph iff it is finally DEPLOYED and was minted in round <= r (curate has
no exit gate: once deployed it stays). A verify-gate is present iff its checkpoint_round <= r.
Capability edges kept iff both endpoints are kept. Output: graph_r1.json, graph_r2.json next to the
final graph. (r0 graph == empty == noskill; r3 graph == final trained_graph == the 56.1 run.)
"""
import json, os, re

R = os.path.join(os.path.dirname(__file__), "..", "..", "external/repos/Trace2Skill/runs/curate_fromzero")
g = json.load(open(os.path.join(R, "trained_graph.json")))
led = json.load(open(os.path.join(os.path.dirname(__file__), "evolution_ledger.json")))
skills = g["skills"]; skills = list(skills.values()) if isinstance(skills, dict) else skills
gov = g["governance"]; gov = list(gov.values()) if isinstance(gov, dict) else gov
edges = g["capability_edges"]

mint = {s["id"]: s["mint_round"] for s in led["skills"]}
ckr = {s["id"]: s["checkpoint_round"] for s in led["skills"]}
deployed_final = {s["id"] for s in led["skills"] if s["status"] == "deployed"}

def build(r):
    keep = {sid for sid in deployed_final if mint.get(sid) is not None and mint[sid] <= r}
    sk = [s for s in skills if s["id"] in keep]
    for s in sk: s["status"] = "deployed"
    ed = [e for e in edges if e["src"] in keep and e["dst"] in keep]
    gv = [n for n in gov if n.get("kind") == "checkpoint"
          and n.get("targets") and n["targets"][0] in keep
          and ckr.get(n["targets"][0]) is not None and ckr[n["targets"][0]] <= r]
    out = {"skills": sk, "capability_edges": ed, "governance": gv, "stats": {}}
    path = os.path.join(R, f"graph_r{r}.json")
    json.dump(out, open(path, "w"), ensure_ascii=False, indent=2)
    return path, len(sk), len(gv), len(ed)

print("=== reconstructed intermediate graphs ===")
print("(expected: r1=12 nodes/0 gates, r2=22 nodes/6 gates; final trained=34/11)")
for r in (1, 2):
    p, ns, ng, ne = build(r)
    print(f"  r{r}: {ns} nodes, {ng} gates, {ne} edges  -> {os.path.basename(p)}")
# sanity: final
print(f"  r3(final trained_graph): {len(deployed_final)} deployed, "
      f"{sum(1 for n in gov if n.get('kind')=='checkpoint')} gates")
