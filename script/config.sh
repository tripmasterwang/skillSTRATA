#!/usr/bin/env bash
# =============================================================================
# SkillStrata experiment config — EDIT THIS on the isolated server, then run:
#     bash script/run_curate.sh
# run_curate.sh reads from here. No Claude Code needed.
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

# ---- the single experiment --------------------------------------------------
# The one experiment is run_curate.sh: from-zero curate on TRAIN -> test on the 280 held-out.
# ROUNDS = curate epochs (default 4, override inline). No baseline/ablation matrix here.

# ---- held-out scoring (SkillOpt-comparable) ---------------------------------
# After full-400 eval, also score each run on the SkillOpt 80/40/280 splits.
TEST_IDS="$SCRIPT_DIR/data/skillopt_test_ids.txt"      # 280 held-out test ids
VAL_IDS="$SCRIPT_DIR/data/skillopt_val_ids.txt"        # 40
TRAIN_IDS="$SCRIPT_DIR/data/skillopt_train_ids.txt"    # 80

# ---- behaviour --------------------------------------------------------------
RETRAIN="${RETRAIN:-0}"    # 1 = redo Phase-1 curate even if trained_graph.json exists; 0 = reuse it
VERIFY_LOOP="${VERIFY_LOOP:-1}"   # 1 = node-local verify-loop ON at test (deployed); 0 = off
