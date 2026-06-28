#!/usr/bin/env bash
# =============================================================================
# Run the from-zero SkillStrata graph under an EXTERNAL harness (Codex / Claude
# Code / mini-swe-agent) on the 280 held-out SpreadsheetBench split.
#
# Usage:
#   bash script/run_harness.sh <harness> <key_file> [port]
#     <harness>  : codex | claude | minisweagent
#     <key_file> : path to a one-line xf-yun API key file
#     [port]     : claude-only; cc proxy port (default 8790 + offset)
#
# Env overrides:
#   WORKERS (default 40)  INSTANCE_IDS (default = 280 test ids)  OUT_SUFFIX
#   HARNESS_STEP_LIMIT (default 30)  HARNESS_TIMEOUT (default 420)
# =============================================================================
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

HARNESS="${1:?need harness: codex|claude|minisweagent}"
KEY_FILE_ARG="${2:?need key file}"
PORT="${3:-}"

PY=/home/workspace/lww/project0412/Auto-claude-code-research-in-sleep/.venv/bin/python
WORK="$RUNS_DIR/curate_fromzero"
GRAPH="$WORK/trained_graph.json"
[ -f "$GRAPH" ] || { echo "FATAL: trained graph not found: $GRAPH"; exit 1; }
[ -f "$KEY_FILE_ARG" ] || { echo "FATAL: key file not found: $KEY_FILE_ARG"; exit 1; }
KEY="$(tr -d '\r\n' < "$KEY_FILE_ARG")"

case "$HARNESS" in
  codex)         AGENT=cli_skillstrata_codex ;;
  claude)        AGENT=cli_skillstrata_claude ;;
  minisweagent)  AGENT=cli_skillstrata_minisweagent ;;
  *) echo "FATAL: unknown harness $HARNESS"; exit 1 ;;
esac

WORKERS="${WORKERS:-40}"
OUT_SUFFIX="${OUT_SUFFIX:-$HARNESS}"
OUTDIR="$WORK/test_280_$OUT_SUFFIX"
mkdir -p "$OUTDIR/logs" "$OUTDIR/routes"
GENCFG="$OUTDIR/gen_config.json"
printf '{"temperature":%s,"extra_body":{"enable_thinking":%s,"reasoning_effort":"%s"}}' \
  "$TEMPERATURE" "$THINKING" "$REASONING_EFFORT" > "$GENCFG"

# instance ids: full 280 test split unless overridden
if [ -n "${INSTANCE_IDS:-}" ]; then
  TEST_ID_CSV="$INSTANCE_IDS"
else
  TEST_ID_CSV="$(paste -sd, "$TEST_IDS")"
fi

export PYTHONPATH="$PROJECT_ROOT:$REPO/src:${PYTHONPATH:-}"
# xf-yun creds for codex / mini-swe (and the router's seed LLM client)
export XFYUN_BASE_URL="$OPENAI_BASE_URL"
export XFYUN_API_KEY="$KEY"
export XFYUN_MODEL="$MODEL"
export XFYUN_EFFORT="$REASONING_EFFORT"
export OPENAI_BASE_URL="$OPENAI_BASE_URL"
export OPENAI_API_KEY="$KEY"
# SkillStrata routing (same router as the cli baseline: agent-seeded graph)
# NOSKILL=1 -> point at a non-existent graph so the agent builds a BLANK graph (0 routed skills):
# this is the "bare harness" baseline (their codex/claude with NO SkillStrata), same executor + prompt.
if [ "${NOSKILL:-0}" = "1" ]; then
  export SKILLSTRATA_GRAPH_PATH="$OUTDIR/__blank_graph__.json"   # intentionally not created -> blank graph
else
  export SKILLSTRATA_GRAPH_PATH="$GRAPH"
fi
export SKILLSTRATA_ROUTE_DIR="$OUTDIR/routes"
export SKILLSTRATA_ROUTER="${SKILLSTRATA_ROUTER:-agent}"
export SKILLSTRATA_TYPE_BOOST="${SKILLSTRATA_TYPE_BOOST:-1.0}"
export SKILLSTRATA_AGENT_THINK_BUDGET="${SKILLSTRATA_AGENT_THINK_BUDGET:-1024}"
export SKILLSTRATA_VERIFY_LOOP="${SKILLSTRATA_VERIFY_LOOP:-1}"   # node-local verify-or-rollback ON at test
export HARNESS_STEP_LIMIT="${HARNESS_STEP_LIMIT:-30}"
export HARNESS_TIMEOUT="${HARNESS_TIMEOUT:-420}"

PROXY_PID=""
cleanup() { [ -n "$PROXY_PID" ] && kill "$PROXY_PID" 2>/dev/null; }
trap cleanup EXIT

if [ "$HARNESS" = "codex" ]; then
  export CODEX_HOME="$SCRIPT_DIR/harness/codex_home"
  CODEX_PROXY_PORT="${PORT:-8796}"   # must match base_url in codex_home/config.toml
  echo "[proxy] starting codex_responses_proxy on 127.0.0.1:$CODEX_PROXY_PORT (model=$MODEL)"
  XFYUN_BASE_URL="$XFYUN_BASE_URL" XFYUN_API_KEY="$KEY" XFYUN_MODEL="$MODEL" \
  XFYUN_EFFORT="$REASONING_EFFORT" PORT="$CODEX_PROXY_PORT" \
    "$PY" "$SCRIPT_DIR/harness/codex_responses_proxy.py" > "$OUTDIR/codex_proxy.log" 2>&1 &
  PROXY_PID=$!
  for i in $(seq 1 30); do
    curl -s -o /dev/null "http://127.0.0.1:$CODEX_PROXY_PORT/v1/responses" \
      -X POST -H 'content-type: application/json' -d '{"input":"hi","stream":false}' && break
    sleep 1
  done
fi

if [ "$HARNESS" = "claude" ]; then
  PORT="${PORT:-8793}"
  echo "[proxy] starting cc_proxy_xfyun on 127.0.0.1:$PORT (model=$MODEL)"
  XFYUN_BASE_URL="$XFYUN_BASE_URL" XFYUN_API_KEY="$KEY" XFYUN_MODEL="$MODEL" \
  XFYUN_EFFORT="$REASONING_EFFORT" PORT="$PORT" \
    "$PY" "$SCRIPT_DIR/harness/cc_proxy_xfyun.py" > "$OUTDIR/cc_proxy.log" 2>&1 &
  PROXY_PID=$!
  # wait for the proxy to accept connections
  for i in $(seq 1 30); do
    curl -s -o /dev/null "http://127.0.0.1:$PORT/v1/messages/count_tokens" \
      -X POST -H 'content-type: application/json' -d '{"messages":[]}' && break
    sleep 1
  done
  export ANTHROPIC_BASE_URL="http://127.0.0.1:$PORT"
  export ANTHROPIC_AUTH_TOKEN="dummy"
  export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
fi

echo "===== HARNESS=$HARNESS  AGENT=$AGENT  WORKERS=$WORKERS  OUT=$OUTDIR  $(date '+%F %T') ====="
cd "$REPO"
"$PY" run_spreadsheetbench.py \
  --data_path "$DATA" --model "$MODEL" --llm_client openai --agent "$AGENT" \
  --instance_ids "$TEST_ID_CSV" --workers "$WORKERS" --max_turns "$MAX_TURNS" \
  --generation_config "$GENCFG" --missing_only \
  --output_dir "$OUTDIR" --log_dir "$OUTDIR/logs" --results_file "$OUTDIR/results.json"
RUN_RC=$?

echo "[eval] official eval -> $OUTDIR/eval_official_results.json"
"$PY" evaluate_with_official.py --data_path "$DATA" --output_dir "$OUTDIR" \
  > "$OUTDIR/eval_stdout.txt" 2>&1
if [ -f "$SCRIPT_DIR/score_on_split.py" ]; then
  SCORE="$("$PY" "$SCRIPT_DIR/score_on_split.py" "$OUTDIR/eval_official_results.json" "$TEST_IDS" 2>/dev/null)"
  echo "===== $HARNESS score on 280 held-out = $SCORE ====="
fi
echo "[done] harness=$HARNESS rc=$RUN_RC  $(date '+%F %T')"
