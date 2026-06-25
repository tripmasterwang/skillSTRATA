#!/usr/bin/env bash
# =============================================================================
# SkillStrata experiment config — EDIT THIS on the isolated server, then run:
#     bash script/run_all.sh
# Everything else (run_all.sh) reads from here. No Claude Code needed.
# =============================================================================

# ---- paths (auto-derived; usually no need to change) -------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"             # .../projects/skillSTRATA
REPO="$PROJECT_ROOT/external/repos/Trace2Skill"          # run_spreadsheetbench.py lives here
DATA="$REPO/data/spreadsheetbench_verified/spreadsheetbench_verified_400"
RUNS_DIR="$REPO/runs"                                    # all outputs go here

# ---- LLM endpoint (OpenAI-compatible) — *** SET THESE ON THE NEW SERVER *** --
# The model is called via an OpenAI-compatible API. Point it at your qwen3.6 server.
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-http://localhost:8000/v1}"   # e.g. your vLLM/sglang endpoint
MODEL="${MODEL:-qwen3.6-35b-a3b}"

# API key: prefer the OPENAI_API_KEY env var; otherwise read this file (one line).
# For a local vLLM/sglang server with no auth, set OPENAI_API_KEY=EMPTY.
KEY_FILE="${KEY_FILE:-$SCRIPT_DIR/.api_key}"
if [ -z "${OPENAI_API_KEY:-}" ] && [ -f "$KEY_FILE" ]; then
  OPENAI_API_KEY="$(tr -d '\r\n' < "$KEY_FILE")"
fi
export OPENAI_API_KEY="${OPENAI_API_KEY:-EMPTY}"

# ---- generation config (Qwen thinking control) ------------------------------
# Matches SkillOpt's setting: enable_thinking + thinking_budget; max output unbounded.
THINKING="${THINKING:-true}"            # true|false
THINKING_BUDGET="${THINKING_BUDGET:-4096}"
TEMPERATURE="${TEMPERATURE:-0.0}"

# ---- run scale --------------------------------------------------------------
WORKERS="${WORKERS:-8}"                 # concurrency. 8 was stable; raise if your server allows.
MAX_TURNS="${MAX_TURNS:-15}"
END_IDX="${END_IDX:-400}"               # 400 = full verified set; set smaller for a smoke run.

# ---- which variants to run --------------------------------------------------
# Format per line: "label|agent|extra_env"
#   agent ∈ { cli_only, cli_skill_preloaded, cli_skillstrata }
#   SKILLSTRATA_ROUTER ∈ { graph, agent, full, bm25 }  (only for cli_skillstrata)
# Comment out any line you don't want. Order = run order.
VARIANTS=(
  "no-skill|cli_only|"
  "monolithic-xlsx35B|cli_skill_preloaded|"
  "skillstrata-graph|cli_skillstrata|SKILLSTRATA_ROUTER=graph SKILLSTRATA_TYPE_BOOST=1.0"
  "skillstrata-agent|cli_skillstrata|SKILLSTRATA_ROUTER=agent SKILLSTRATA_TYPE_BOOST=1.0 SKILLSTRATA_AGENT_THINK_BUDGET=1024"
  "monolithic-122B-full|cli_skillstrata|SKILLSTRATA_ROUTER=full"
  "flat-bm25|cli_skillstrata|SKILLSTRATA_ROUTER=bm25 SKILLSTRATA_K=5"
)

# ---- held-out scoring (SkillOpt-comparable) ---------------------------------
# After full-400 eval, also score each run on the SkillOpt 80/40/280 splits.
TEST_IDS="$SCRIPT_DIR/data/skillopt_test_ids.txt"      # 280 held-out test ids
VAL_IDS="$SCRIPT_DIR/data/skillopt_val_ids.txt"        # 40
TRAIN_IDS="$SCRIPT_DIR/data/skillopt_train_ids.txt"    # 80

# ---- behaviour --------------------------------------------------------------
RESUME="${RESUME:-1}"      # 1 = skip a variant whose results.json exists; 0 = always re-run
MISSING_ONLY="${MISSING_ONLY:-1}"   # 1 = only run instances without an output (resume a killed run)
