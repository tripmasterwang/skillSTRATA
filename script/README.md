# SkillStrata — the experiment runner

Runs **one experiment** on any server **without Claude Code** — plain `bash` + `python3`.

## The experiment: `run_curate.sh`

From-zero SkillStrata, with exactly **two arms** compared on the same 280 held-out test:

- **Phase 1 (TRAIN / curate)** — start from an EMPTY graph; for `ROUNDS` epochs run the agent on
  the 80 train ids, distill trajectories into skill fragments (qwen3.6), INSERT/MERGE/SPLIT them
  into the 3-layer capability graph + governance, and keep a round's edits only if the 40 val score
  improves (validation gate). Error-prone nodes get a node-local verify-loop checkpoint. Output: a
  trained graph JSON. (Only the with-skill arm needs this.)
- **Phase 2 (TEST)** — two arms on the SAME 280 held-out ids + official eval:
  1. **no-skill** (`cli_only`) — nothing injected; the floor.
  2. **with-skill** (`cli_skillstrata`) — the frozen trained graph routed by the react-agent
     retriever, node-local verify-loop ON. **Ours.**

**Only these two** — no other baselines, no ablation matrix.

## Prerequisites

- Python deps: `pip install openpyxl networkx rank_bm25 openai`.
- Repo + data already in place under `external/repos/Trace2Skill/` (incl.
  `data/spreadsheetbench_verified/spreadsheetbench_verified_400`). All code edits are applied in-tree.
- An OpenAI-compatible endpoint serving `qwen3.6-35b-a3b` (e.g. a local vLLM/sglang server).

## Setup (on the isolated server)

Edit `script/config.sh`:
- `OPENAI_BASE_URL` → your model endpoint (e.g. `http://localhost:8000/v1`).
- API key: `export OPENAI_API_KEY=...`, or put it in `script/.api_key`, or `EMPTY` for an auth-less server.
- `MODEL`, `WORKERS`, `THINKING_BUDGET` as needed.

(Recommended) bump the served context window to **128k** — observed max input ≈104k tokens.

## Usage

```bash
bash script/run_curate.sh                 # the one experiment (train -> test 280)
ROUNDS=4 bash script/run_curate.sh        # override curate epochs (default 4)
RETRAIN=1 bash script/run_curate.sh       # redo Phase-1 even if a trained graph exists
VERIFY_LOOP=0 bash script/run_curate.sh   # turn the test-time verify-loop off
```

## Output

- `external/repos/Trace2Skill/runs/curate_fromzero/trained_graph.json` — the learned 3-layer graph.
- `.../curate_fromzero/test_280_noskill/` — no-skill arm outputs, logs, `eval_official_results.json`.
- `.../curate_fromzero/test_280/` — with-skill arm outputs, logs, `eval_official_results.json`.
- `.../curate_fromzero/RESULTS.md` — self-contained report (graph + curate history + both scores).

The console prints the head-to-head at the end:
```
===== RESULT on 280 held-out =====
  no-skill   (floor) = ...
  with-skill (ours)  = ...
```

## Score an existing run on a split (no model needed)

```bash
python3 script/score_on_split.py runs/curate_fromzero/test_280/eval_official_results.json script/data/skillopt_test_ids.txt
```

## Notes

- The SkillOpt-comparable head-to-head is the **280 held-out test** (same `split_seed=42`, 2:1:7 ids
  as SkillOpt). Train/val are used only to build and gate the graph.
- Verify-loop gating per phase: train rollout OFF (honest failure signal), val ON (faithful gate),
  test ON (deployed). Set via `SKILLSTRATA_VERIFY_LOOP` / `VERIFY_LOOP`.
