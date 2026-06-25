# SkillStrata — standalone experiment runner

Run the SkillStrata routing-comparison suite on any server **without Claude Code**.
Everything is plain `bash` + `python3`.

## What it runs

For each variant: SpreadsheetBench (verified-400) → official per-instance eval →
scored on the SkillOpt **80/40/280** train/val/test splits → table in `runs/COMPARISON.md`.

| Variant | agent | what it is |
|---------|-------|-----------|
| `no-skill` | `cli_only` | floor, no skill injected |
| `monolithic-xlsx35B` | `cli_skill_preloaded` | Trace2Skill's single skill, whole-injected (baseline) |
| `skillstrata-graph` | `cli_skillstrata` `ROUTER=graph` | **ours**: BM25 seed → dependency closure → governance |
| `skillstrata-agent` | `cli_skillstrata` `ROUTER=agent` | **ours**: LLM (qwen3.6) picks seeds instead of BM25, then same graph |
| `monolithic-122B-full` | `cli_skillstrata` `ROUTER=full` | inject ALL 12 fragments (rich monolithic ablation) |
| `flat-bm25` | `cli_skillstrata` `ROUTER=bm25` | flat top-k retrieval, no graph (ablation) |

## Prerequisites

- Python deps: `pip install openpyxl networkx rank_bm25 openai` (pandas optional; agent may use it).
- The repo + data are already in place under `external/repos/Trace2Skill/` (incl. `data/spreadsheetbench_verified/spreadsheetbench_verified_400`). All code edits (verification protocol, retry loop, `cli_skillstrata` agent, pluggable agent retriever) are already applied in-tree.
- An OpenAI-compatible endpoint serving the model (e.g. a local vLLM/sglang server for `qwen3.6-35b-a3b`).

## Setup (on the isolated server)

1. Edit `script/config.sh`:
   - `OPENAI_BASE_URL` → your model endpoint (e.g. `http://localhost:8000/v1`).
   - API key: either `export OPENAI_API_KEY=...`, or put it in `script/.api_key`, or set `EMPTY` for an auth-less local server.
   - `MODEL`, `WORKERS`, `THINKING_BUDGET` as needed.
2. (Recommended) bump context window to **128k** when serving the model — observed max input ≈104k tokens; 64k truncates ~0.5% of the hardest tasks.

## Usage

```bash
bash script/run_all.sh                                   # all variants
bash script/run_all.sh skillstrata-agent skillstrata-graph   # only these
WORKERS=16 END_IDX=20 bash script/run_all.sh             # quick smoke (first 20 tasks)
RESUME=0 bash script/run_all.sh no-skill                 # force re-run a variant
```

Resume-safe: a variant whose `results.json` exists is skipped; a killed run is
backfilled with `--missing_only`. Long runs survive being re-launched.

## Output

- `external/repos/Trace2Skill/runs/<variant>/` — outputs, logs, `eval_official_results.json`.
- `external/repos/Trace2Skill/runs/COMPARISON.md` — the comparison table (full-400 + 280-test + 40-val + 80-train).

## Score an existing run on any split (no model needed)

```bash
python3 script/score_on_split.py runs/skillstrata-graph/eval_official_results.json script/data/skillopt_test_ids.txt
```

## Notes

- `skillstrata-agent` makes **one extra LLM call per task** (the seed selector) on top of the executor → ~roughly double the calls of `skillstrata-graph`. Falls back to BM25 if the call fails.
- The SkillOpt-comparable head-to-head is the **280 held-out test** column (same `split_seed=42`, 2:1:7 ids as SkillOpt). Train/val columns are for sanity only.
- **Not yet implemented here**: the "evolve the 3-layer network from a blank seed" curate pipeline (MAP→graph construction + validation gate). This runner uses the current hand-built capability graph + routing. The from-0 pipeline is the next build.
