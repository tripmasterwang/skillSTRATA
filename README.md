# SkillOS — Code Materials

A hierarchical, graph-governed skill system for LLM agents — the code backing
`skillos_proposal.md`. SkillOS turns trajectory-derived experience from one *monolithic* skill
document into a **three-layer skill graph** (trace / capability / governance) curated by
**lifecycle operations** (INSERT/UPDATE/SPLIT/MERGE/LINK/RETIRE) and queried at test time by
**dependency-aware routing** (ROUTE) — a minimal executable subgraph instead of full-load.

> *SkillOS does not store more skills; it learns to load less, compose better, and transfer more safely.*

## Built on three references

This implementation is grounded in three real codebases (downloaded under `external/`):

| Reference | arXiv | Repo | Contributes |
|---|---|---|---|
| **Trace2Skill** | 2603.25158 | `Qwen-Applications/Trace2Skill` | Base trace→skill pipeline; we replace its monolithic `run_reduce_phase` merge. |
| **G-Memory** | 2506.07398 | `bingreeky/GMemory` | Hierarchical graph + k-hop traversal (→ capability/trace/governance graphs). |
| **MemoryOS** | 2506.06326 | `BAI-LAB/MemoryOS` | OS-style lifecycle: heat scoring, promotion gate, eviction (→ skill lifecycle, RETIRE). |

`CODE_DESIGN.md` maps every module to its source file + line, and documents the seam for
wiring SkillOS into a real-LLM Trace2Skill run.

## Layout

```
skillos/            # the engine (pure library, reference-grounded)
  schema.py         # SkillNode (proposal YAML) + Trace2Skill Patch/PatchEdit interchange
  graph.py          # three-layer networkx graph, stable IDs, dependency closure, k-hop
  heat.py           # MemoryOS heat: H = α·N_visit + β·coverage + γ·recency
  operations.py     # INSERT / UPDATE / SPLIT / MERGE / LINK / RETIRE  (+ should_split)
  router.py         # GraphRouter (ROUTE = minimal subgraph) vs FlatRouter (BM25/embed/full)
  lifecycle.py      # candidate→validated→deployed→retired; propose-then-verify gate; govern
  evolver.py        # GraphGovernedEvolver = drop-in replacement for Trace2Skill REDUCE
  embedding.py      # deterministic hash embedder (default) | sentence-transformers (opt-in)
sim/                # deterministic experiment harness (no GPU / no API budget)
  tasks.py          # synthetic world: atomic skills + dependency DAG + heterogeneous/OOD stream
  simulator.py      # executor model: (subgraph, task) → success / tokens / negative transfer
  builders.py       # construct each baseline's skill store from the same world
  harness.py        # streaming eval loop + metrics + harmful-skill injection
  run_main.py       # main results table
  run_ablations.py  # the six ablations + safety-net study
  report.py         # render results/*.json → results/RESULTS.md
tests/              # pytest unit tests for the engine
results/            # generated tables (main.json, ablations.json, RESULTS.md)
external/           # downloaded papers (LaTeX src) + cloned reference repos
```

## Run

```bash
pip install -r requirements.txt
bash experiments/run_all.sh           # tests + main table + ablations  (~10s, deterministic)
python3 -m sim.report                 # write results/RESULTS.md
```

Individual pieces:
```bash
python3 -m pytest tests/ -q
python3 -m sim.run_main      --seeds 0 1 2 3 4 5 6 7 --out results/main.json
python3 -m sim.run_ablations --seeds 0 1 2 3 4 5 6 7 --out results/ablations.json
```

## What the results show

See `results/RESULTS.md`. Headline: SkillOS gives the **highest success** at the **lowest token
cost** among multi-skill methods, with the **lowest negative transfer**, **highest routing
precision**, and **largest OOD gain**. Ablations confirm the proposal's claim that **SPLIT** and
**ROUTE** are the most important operations (their removal causes the largest drops; removing
SPLIT also makes token cost explode), while lifecycle validation + governance act as
complementary safety nets whose value shows in long-horizon stability.

## Using the engine directly

```python
from skillos import SkillGraph, SkillNode, EdgeType, insert, link, split, GraphRouter

g = SkillGraph()
insert(g, SkillNode.make(name="parse table", body="...", dependencies=["tokenize"]))
insert(g, SkillNode.make(name="tokenize", body="..."))
link(g, "parse_table", "tokenize", EdgeType.DEPENDS_ON)
for n in g.nodes.values(): n.status = n.status.DEPLOYED
route = GraphRouter(g).route("parse this table")   # minimal executable subgraph
print(route.nodes, route.loaded_tokens)
```

## Real-LLM integration

The simulator is a deterministic stand-in. To run against real Trace2Skill / SpreadsheetBench,
override `ParallelSkillEvolver.run_reduce_phase` with `GraphGovernedEvolver.absorb` and inject
`GraphRouter(graph).route(task).render()` into the executor system prompt instead of the full
`SKILL.md`. Exact patch in `skillos/evolver.py` and `sim/simulator.py` docstrings.
