#!/usr/bin/env python3
"""Reconstruct the from-zero curate evolution ledger (per-round, per-skill: adopted/discarded/why)
from the real artifacts. Outputs a structured JSON + prints a human-readable ledger for review.

Sources (all under runs/curate_fromzero/):
  curate_history.json   per-round aggregate (inserted/merged/accepted/val/deployed/checkpoints)
  trained_graph.json    final 3-layer graph: skills{} + governance{} + capability_edges[]

governance step is 1-indexed (graph.tick() runs before round r -> step = r+1).
"""
import json, re, collections, os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..",
                    "external/repos/Trace2Skill/runs/curate_fromzero")
hist = json.load(open(os.path.join(ROOT, "curate_history.json")))
g = json.load(open(os.path.join(ROOT, "trained_graph.json")))
skills = g["skills"]; gov = g["governance"]; edges = g["capability_edges"]
gv = list(gov.values()) if isinstance(gov, dict) else gov

def step_of(gid):
    m = re.findall(r'_(\d+)(?:_\d+)?$', gid)
    return int(m[-1]) if m else None

# ---- per-skill ledger ----
mint_step = {}          # skill id -> step it was inserted
checkpoint = {}         # skill id -> (step, succ, trials) from checkpoint statement
merged_targets = []     # merge_decision statements (which fragment folded into which node)
accept_reject = {}      # step -> 'accept'|'reject'
for n in gv:
    kind = n.get("kind"); gid = n.get("id", ""); st = step_of(gid); tg = n.get("targets", [])
    stmt = n.get("statement", "")
    if kind == "insert_decision" and tg:
        mint_step.setdefault(tg[0], st)
    elif kind == "checkpoint" and tg:
        m = re.search(r"succ ([\d.]+) over (\d+) trials", stmt)
        checkpoint[tg[0]] = (st, float(m.group(1)) if m else None, int(m.group(2)) if m else None)
    elif kind == "merge_decision":
        merged_targets.append((st, stmt))
    elif kind == "accept":
        accept_reject[st] = "accept"
    elif kind == "rejected_edit":
        accept_reject[st] = "reject"

rows = []
_sk_items = skills.items() if isinstance(skills, dict) else [(s.get("id"), s) for s in skills]
for sid, s in _sk_items:
    h = s.get("heat", {})
    trials = h.get("success_count", 0) + h.get("failure_count", 0)
    succ = (h.get("success_count", 0) / trials) if trials else None
    cp = checkpoint.get(sid)
    rows.append({
        "id": sid, "name": s.get("name"), "status": s.get("status"),
        "mint_step": mint_step.get(sid), "mint_round": (mint_step.get(sid) - 1) if mint_step.get(sid) else None,
        "task_types": s.get("task_types", []),
        "trials": trials, "succ": round(succ, 2) if succ is not None else None,
        "checkpoint_round": (cp[0] - 1) if cp else None,
        "checkpoint_succ": cp[1] if cp else None,
    })

# ---- summary ----
by_status = collections.Counter(r["status"] for r in rows)
deployed = [r for r in rows if r["status"] == "deployed"]
retired = [r for r in rows if r["status"] == "retired"]
gated = [r for r in rows if r["checkpoint_round"] is not None]

print("=== STATUS ===", dict(by_status), "| total", len(rows))
print(f"deployed={len(deployed)} retired={len(retired)} gated={len(gated)}")
print("\n=== retired skills (which round minted) ===")
print(collections.Counter(r["mint_round"] for r in retired))
print("\n=== per-round accept/reject ===")
for st in sorted(accept_reject): print(f"  round {st-1}: {accept_reject[st]}")
print("\n=== merge decisions ===")
for st, stmt in merged_targets: print(f"  round {st-1}: {stmt}")
print("\n=== DEPLOYED skills (round minted, succ, gated?) ===")
for r in sorted(deployed, key=lambda x: (x["mint_round"] or 0, -(x["trials"] or 0))):
    lock = f" GATE@r{r['checkpoint_round']}(succ{r['checkpoint_succ']})" if r["checkpoint_round"] is not None else ""
    print(f"  r{r['mint_round']} | {r['name'][:46]:46s} | trials={r['trials']:>3} succ={r['succ']}{lock}")
print("\n=== RETIRED skills (discarded) ===")
for r in sorted(retired, key=lambda x: (x["mint_round"] or 0)):
    print(f"  r{r['mint_round']} | {r['name'][:50]:50s} | (round rejected by gate)")

out = {"history": hist, "skills": rows, "merges": merged_targets,
       "accept_reject": {str(k): v for k, v in accept_reject.items()},
       "edge_types": collections.Counter(e.get("type") for e in edges)}
json.dump(out, open(os.path.join(os.path.dirname(__file__), "evolution_ledger.json"), "w"),
          ensure_ascii=False, indent=2)
print("\n-> wrote evolution_ledger.json")
