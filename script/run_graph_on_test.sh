#!/usr/bin/env bash
# =============================================================================
# Run an ARBITRARY graph json on the 280 held-out test set with the MAIN test-time
# config (router=agent, verify-loop=1) — used to test reconstructed INTERMEDIATE
# curate graphs (graph_r1/graph_r2) so we can draw the per-round improvement curve.
#
#   bash script/run_graph_on_test.sh <label> <graph_path> <keyname>
# Output dir: runs/curate_fromzero/<label>/  (+ eval + 280-subset score)
# Env: WORKERS (default 24)
# =============================================================================
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
LABEL="${1:?label}"; GRAPH="${2:?graph path}"; KEYNAME="${3:?keyname}"
KEYDIR=/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/_shared/LLM_apis
KEY="$(tr -d '\r\n' < "$KEYDIR/.xunfei_api_key_$KEYNAME")"
[ -f "$GRAPH" ] || { echo "FATAL: graph not found: $GRAPH"; exit 1; }
PY=/home/workspace/lww/project0412/Auto-claude-code-research-in-sleep/.venv/bin/python
WORK="$RUNS_DIR/curate_fromzero"; OUTDIR="$WORK/$LABEL"
WORKERS="${WORKERS:-24}"
mkdir -p "$OUTDIR/logs" "$OUTDIR/routes"
GENCFG="$OUTDIR/gen_config.json"
printf '{"temperature":%s,"extra_body":{"enable_thinking":%s,"reasoning_effort":"%s"}}' \
  "$TEMPERATURE" "$THINKING" "$REASONING_EFFORT" > "$GENCFG"
TEST_ID_CSV="$(paste -sd, "$TEST_IDS")"
export PYTHONPATH="$PROJECT_ROOT:$REPO/src:${PYTHONPATH:-}"
cd "$REPO"
echo "===== GRAPH-ON-TEST label=$LABEL graph=$GRAPH key=$KEYNAME workers=$WORKERS $(date '+%F %T') ====="
SKILLSTRATA_GRAPH_PATH="$GRAPH" SKILLSTRATA_ROUTE_DIR="$OUTDIR/routes" \
SKILLSTRATA_ROUTER=agent SKILLSTRATA_TYPE_BOOST=1.0 SKILLSTRATA_AGENT_THINK_BUDGET=1024 \
SKILLSTRATA_VERIFY_LOOP=1 OPENAI_API_KEY="$KEY" OPENAI_BASE_URL="$OPENAI_BASE_URL" \
"$PY" run_spreadsheetbench.py \
  --data_path "$DATA" --model "$MODEL" --llm_client openai --agent cli_skillstrata \
  --instance_ids "$TEST_ID_CSV" --workers "$WORKERS" --max_turns "$MAX_TURNS" \
  --generation_config "$GENCFG" --missing_only \
  --output_dir "$OUTDIR" --log_dir "$OUTDIR/logs" --results_file "$OUTDIR/results.json"
"$PY" evaluate_with_official.py --data_path "$DATA" --output_dir "$OUTDIR" > "$OUTDIR/eval_stdout.txt" 2>&1
SCORE="$("$PY" "$SCRIPT_DIR/score_on_split.py" "$OUTDIR/eval_official_results.json" "$TEST_IDS" 2>/dev/null)"
echo "===== GRAPH-ON-TEST label=$LABEL DONE 280held-out=$SCORE $(date '+%F %T') ====="
