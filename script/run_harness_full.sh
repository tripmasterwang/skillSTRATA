#!/usr/bin/env bash
# =============================================================================
# FULL pipeline for ONE external harness: curate (train+val, 4 rounds) a graph
# using THAT harness as the executor, then test on the 280 held-out split with
# the harness's OWN trained graph. Each harness gets its own work dir + key.
#
# Usage:
#   bash script/run_harness_full.sh <harness> <key_file> [proxy_port]
#     <harness> : codex | claude | minisweagent
#
# Env overrides: ROUNDS(4) WORKERS(40) HARNESS_STEP_LIMIT(30) HARNESS_TIMEOUT(420)
# =============================================================================
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

HARNESS="${1:?need harness: codex|claude|minisweagent}"
KEY_FILE_ARG="${2:?need key file}"
PORT="${3:-}"
[ -f "$KEY_FILE_ARG" ] || { echo "FATAL: key file not found: $KEY_FILE_ARG"; exit 1; }
KEY="$(tr -d '\r\n' < "$KEY_FILE_ARG")"

case "$HARNESS" in
  codex)         AGENT=cli_skillstrata_codex ;;
  claude)        AGENT=cli_skillstrata_claude ;;
  minisweagent)  AGENT=cli_skillstrata_minisweagent ;;
  *) echo "FATAL: unknown harness $HARNESS"; exit 1 ;;
esac

PY=/home/workspace/lww/project0412/Auto-claude-code-research-in-sleep/.venv/bin/python
ROUNDS="${ROUNDS:-4}"
WORKERS="${WORKERS:-40}"
WORK="$RUNS_DIR/curate_$HARNESS"          # per-harness work dir (its own graph + rounds)
GRAPH="$WORK/trained_graph.json"
mkdir -p "$WORK"
GENCFG="$WORK/gen_config.json"
printf '{"temperature":%s,"extra_body":{"enable_thinking":%s,"reasoning_effort":"%s"}}' \
  "$TEMPERATURE" "$THINKING" "$REASONING_EFFORT" > "$GENCFG"

export PYTHONPATH="$PROJECT_ROOT:$REPO/src:${PYTHONPATH:-}"
export XFYUN_BASE_URL="$OPENAI_BASE_URL"
export XFYUN_API_KEY="$KEY"
export XFYUN_MODEL="$MODEL"
export XFYUN_EFFORT="$REASONING_EFFORT"
export OPENAI_BASE_URL="$OPENAI_BASE_URL"
export OPENAI_API_KEY="$KEY"          # distill LLM + agent-seed router use this harness's key
export SKILLSTRATA_TYPE_BOOST="${SKILLSTRATA_TYPE_BOOST:-1.0}"
export SKILLSTRATA_AGENT_THINK_BUDGET="${SKILLSTRATA_AGENT_THINK_BUDGET:-1024}"
export HARNESS_STEP_LIMIT="${HARNESS_STEP_LIMIT:-30}"
export HARNESS_TIMEOUT="${HARNESS_TIMEOUT:-420}"

PROXY_PID=""
cleanup() { [ -n "$PROXY_PID" ] && kill "$PROXY_PID" 2>/dev/null; }
trap cleanup EXIT

# ---- harness-specific endpoint wiring (proxy stays up for BOTH train and test) ----
if [ "$HARNESS" = "codex" ]; then
  export CODEX_HOME="$SCRIPT_DIR/harness/codex_home"
  CPORT="${PORT:-8796}"   # must match base_url in codex_home/config.toml
  echo "[proxy] codex_responses_proxy on 127.0.0.1:$CPORT"
  PORT="$CPORT" "$PY" "$SCRIPT_DIR/harness/codex_responses_proxy.py" > "$WORK/codex_proxy.log" 2>&1 &
  PROXY_PID=$!
  for i in $(seq 1 30); do curl -s -o /dev/null "http://127.0.0.1:$CPORT/v1/responses" \
    -X POST -H 'content-type: application/json' -d '{"input":"hi","stream":false}' && break; sleep 1; done
elif [ "$HARNESS" = "claude" ]; then
  CPORT="${PORT:-8795}"
  echo "[proxy] cc_proxy_xfyun on 127.0.0.1:$CPORT"
  PORT="$CPORT" "$PY" "$SCRIPT_DIR/harness/cc_proxy_xfyun.py" > "$WORK/cc_proxy.log" 2>&1 &
  PROXY_PID=$!
  for i in $(seq 1 30); do curl -s -o /dev/null "http://127.0.0.1:$CPORT/v1/messages/count_tokens" \
    -X POST -H 'content-type: application/json' -d '{"messages":[]}' && break; sleep 1; done
  export ANTHROPIC_BASE_URL="http://127.0.0.1:$CPORT"
  export ANTHROPIC_AUTH_TOKEN="dummy"
  export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
fi

echo "===== [$HARNESS] FULL pipeline  agent=$AGENT  rounds=$ROUNDS  workers=$WORKERS  $(date '+%F %T') ====="
cd "$REPO"

# ---- Phase 1: curate (train + val gate) using THIS harness as executor -------
if [ -f "$GRAPH" ] && [ "${RETRAIN:-0}" != "1" ]; then
  echo "[$HARNESS][train] $GRAPH exists — skip (RETRAIN=1 to redo)."
else
  echo "[$HARNESS][train] curate from zero ($ROUNDS rounds)"
  "$PY" -m skillos.curate_driver \
    --repo "$REPO" --data "$DATA" \
    --train-ids "$TRAIN_IDS" --val-ids "$VAL_IDS" \
    --rounds "$ROUNDS" --graph-out "$GRAPH" --work-dir "$WORK" \
    --model "$MODEL" --gen-config "$GENCFG" --workers "$WORKERS" --max-turns "$MAX_TURNS" \
    --agent "$AGENT" --python "$PY"
fi
[ -f "$GRAPH" ] || { echo "FATAL: [$HARNESS] training did not produce $GRAPH"; exit 1; }
"$PY" -c "import json;d=json.load(open('$GRAPH'));print('[$HARNESS] graph nodes:',len(d['skills']),'edges:',len(d['capability_edges']),'gov:',len(d['governance']))"

# ---- Phase 2: TEST on 280 held-out with THIS harness's own graph -------------
echo "[$HARNESS][test] 280 held-out with own graph"
TESTDIR="$WORK/test_280"
mkdir -p "$TESTDIR/logs" "$TESTDIR/routes"
TEST_ID_CSV="$(paste -sd, "$TEST_IDS")"
SKILLSTRATA_GRAPH_PATH="$GRAPH" SKILLSTRATA_ROUTE_DIR="$TESTDIR/routes" \
SKILLSTRATA_ROUTER=agent SKILLSTRATA_VERIFY_LOOP=1 \
"$PY" run_spreadsheetbench.py \
  --data_path "$DATA" --model "$MODEL" --llm_client openai --agent "$AGENT" \
  --instance_ids "$TEST_ID_CSV" --workers "$WORKERS" --max_turns "$MAX_TURNS" \
  --generation_config "$GENCFG" --missing_only \
  --output_dir "$TESTDIR" --log_dir "$TESTDIR/logs" --results_file "$TESTDIR/results.json"
"$PY" evaluate_with_official.py --data_path "$DATA" --output_dir "$TESTDIR" > "$TESTDIR/eval_stdout.txt" 2>&1
if [ -f "$SCRIPT_DIR/score_on_split.py" ]; then
  SCORE="$("$PY" "$SCRIPT_DIR/score_on_split.py" "$TESTDIR/eval_official_results.json" "$TEST_IDS" 2>/dev/null)"
  echo "===== [$HARNESS] FINAL score on 280 held-out = $SCORE ====="
fi
echo "[$HARNESS][done] $(date '+%F %T')"
