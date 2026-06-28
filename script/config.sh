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

# ---- LLM endpoint (OpenAI-compatible) ---------------------------------------
# qwen3.6-35b-a3b is served via the xf-yun MaaS gateway. NOTE: the gateway's model id is the
# opaque "xopqwen36v35b" (verified via /v2/models) — NOT "qwen3.6-35b-a3b", which 404s.
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://maas-api.cn-huabei-1.xf-yun.com/v2}"
MODEL="${MODEL:-xopqwen36v35b}"   # xf-yun gateway model id for qwen3.6-35b-a3b

# API key: prefer the OPENAI_API_KEY env var; otherwise read this file (one line). Default points at
# the xunfei key, which lives OUTSIDE this git repo so its value never gets committed.
KEY_FILE="${KEY_FILE:-/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/_shared/LLM_apis/.xunfei_api_key_wys}"
if [ -z "${OPENAI_API_KEY:-}" ] && [ -f "$KEY_FILE" ]; then
  OPENAI_API_KEY="$(tr -d '\r\n' < "$KEY_FILE")"
fi
export OPENAI_API_KEY="${OPENAI_API_KEY:-EMPTY}"

# ---- generation config (Qwen thinking control) ------------------------------
# thinking effort = medium. NOTE on the xf-yun gateway: reasoning_effort alone does NOT engage
# thinking (it answers directly, reasoning_content empty); you MUST pass enable_thinking=true
# TOGETHER with reasoning_effort to actually get medium-depth thinking. Verified 2026-06-26.
THINKING="${THINKING:-true}"                  # true|false (must be true for reasoning_effort to bite)
REASONING_EFFORT="${REASONING_EFFORT:-medium}"  # low|medium|high
TEMPERATURE="${TEMPERATURE:-0.0}"

# ---- run scale --------------------------------------------------------------
WORKERS="${WORKERS:-8}"                 # concurrency. 8 was stable; raise if your server allows.
MAX_TURNS="${MAX_TURNS:-5}"

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
