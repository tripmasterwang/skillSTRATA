# SkillOS — Code Design & Provenance

This document maps every SkillOS module to the **reference codebase** it is grounded in,
and records the exact extension seams. The three references live under `external/repos/`:

| Ref | Paper | Repo | Role in SkillOS |
|---|---|---|---|
| **Trace2Skill** | arXiv 2603.25158 | `Qwen-Applications/Trace2Skill` | **Base pipeline.** We replace its monolithic `run_reduce_phase` merge with a graph store + routing. |
| **G-Memory** | arXiv 2506.07398 | `bingreeky/GMemory` | **3-layer graph design.** `TaskLayer` (networkx + k-hop) → capability graph; `InsightsManager` correlation back-refs → governance graph. |
| **MemoryOS** | arXiv 2506.06326 | `BAI-LAB/MemoryOS` | **Lifecycle/heat.** `compute_segment_heat` + promotion-gate + LFU eviction → skill lifecycle & RETIRE. |

## The one-sentence thesis (and where the code proves it)

> Trace2Skill compresses traces into one *monolithic* skill document via an LLM tree-merge
> (`run_reduce_phase`). SkillOS swaps that single seam for a **graph store** (`skillos.graph`)
> governed by **lifecycle operations** (`skillos.operations`, `skillos.lifecycle`) and queried
> at test time by **dependency-aware routing** (`skillos.router`) instead of full-load.

## Module → reference provenance

| SkillOS module | Borrows from | Specific source | What we changed / added |
|---|---|---|---|
| `skillos/schema.py` | Trace2Skill `PatchEdit`/`Patch`; proposal YAML | `parallel_evolving_agent.py:64`; `skillos_proposal.md` "Skill Node Example" | `SkillNode` gets **stable IDs**, granularity, lifecycle `status`, dependency/conflict edges, heat counters. `Patch`/`PatchEdit` mirrored verbatim so we can ingest Trace2Skill MAP output. |
| `skillos/heat.py` | MemoryOS | `mid_term.py:26 compute_segment_heat`, `utils.py:228 compute_time_decay` | Reinterpret factors for skills: `N_visit`→invocations, `L_interaction`→coverage, `R_recency`→decay since last use. Tunable α/β/γ/τ. |
| `skillos/graph.py` | G-Memory | `GMemory.py:352 TaskLayer`, `:404 retrieve_related_task` (k-hop via `nx.single_source_shortest_path_length`) | Three explicit `networkx` graphs (trace/capability/governance) with **stable node IDs** (G-Memory used fragile raw-task-string IDs). Cross-layer edges are first-class. |
| `skillos/operations.py` | proposal Core Operations; G-Memory merge; MemoryOS evict | `skillos_proposal.md`; `GMemory.py:551 _merge_rules`; `mid_term.py:71 evict_lfu` | The 7 ops INSERT/UPDATE/**SPLIT**/MERGE/LINK/RETIRE/ROUTE. SPLIT (refactor) is new — no reference implements it. |
| `skillos/lifecycle.py` | MemoryOS promotion gate; Trace2Skill VERIFY | `memoryos.py:126 _trigger_*_if_needed`; `parallel_evolving_agent.py:2889 run_verification_phase` | candidate→validated→deployed→retired with a **propose-then-verify** gate (replay tasks, accept iff success preserved while token/neg-transfer drop). |
| `skillos/router.py` | G-Memory traversal; Trace2Skill full-load | `GMemory.py:404`; `cli_skill_preloaded_agent.py:252 get_system_template` | **ROUTE** = activate minimal executable subgraph (dependency-closed). Baseline = flat BM25/embedding top-k (what Trace2Skill full-load / a flat bank would do). |
| `skillos/evolver.py` | Trace2Skill | `parallel_evolving_agent.py:2319 run_reduce_phase` | `GraphGovernedEvolver.reduce(skill_state, patches)` is the **drop-in replacement** for `run_reduce_phase`: same signature, routes each `PatchEdit` to a graph node instead of LLM tree-merge. |
| `skillos/embedding.py` | G-Memory / MemoryOS | `mas/utils.py:54 EmbeddingFunc`; `all-MiniLM-L6-v2` | Deterministic hashing embedder by default (offline, reproducible); optional sentence-transformers backend. |

## Experiment harness (`sim/`)

Running real LLM agents on SpreadsheetBench is slow/costly, so the harness ships a
**deterministic simulator** that models the mechanism the paper argues about (skill bloat →
token cost & negative transfer; routing precision → loaded tokens) so all 6 ablations and the
main table reproduce in seconds with `--seed`. The simulator's executor is intentionally a
thin stand-in; `sim/simulator.py` documents the exact place to swap in Trace2Skill's real
`BaseSpreadsheetAgent.run` + `evaluate_with_official` for a real-LLM run.

- `sim/tasks.py` — synthetic heterogeneous task stream + ground-truth skill universe with
  dependencies/conflicts (so negative transfer is well-defined).
- `sim/simulator.py` — maps (activated subgraph, task) → success / token cost / negative transfer.
- `sim/run_main.py` — main results table (proposal §"Expected Main Result").
- `sim/run_ablations.py` — the 6 ablations (§"Ablation Study").

## Real-LLM integration seam (documented, not run by default)

`evolver.py::GraphGovernedEvolver.reduce` matches `ParallelSkillEvolver.run_reduce_phase`'s
signature `(skill_state: dict[str,str], patches: list[Patch]) -> Patch | None`. To wire into
the real Trace2Skill run: subclass `ParallelSkillEvolver`, override `run_reduce_phase` to call
our evolver, and replace `cli_skill_preloaded_agent.get_system_template` injection with
`router.route(task).render()`. See `evolver.py` docstring for the patch.
