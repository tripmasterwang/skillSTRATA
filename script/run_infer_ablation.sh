#!/usr/bin/env bash
# =============================================================================
# INFERENCE-PHASE ablation (task #9): freeze the from-zero REACT SkillStrata
# graph and only flip the two test-time knobs — SKILLSTRATA_ROUTER and
# SKILLSTRATA_VERIFY_LOOP — on the SAME 280 held-out ids. Zero code change.
#
# Isolates: routing benefit (full), graph structure (bm25), test-time
# governance/verify-loop (noverify), agent-seed vs type-boost router (graph).
#
# Usage (one cell):
#   bash script/run_infer_ablation.sh <label> <router> <verify> <keyname>
#     <router>  : agent | graph | bm25 | full
#     <verify>  : 0 | 1
#     <keyname> : lww | lww2 | lww3 | lww4 | wys   (raw xf-yun key, hits gateway directly)
# Env: WORKERS (default 24)
# =============================================================================
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

LABEL="${1:?label}"; ROUTER="${2:?router}"; VERIFY="${3:?verify 0|1}"; KEYNAME="${4:?keyname}"
KEYDIR=/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/_shared/LLM_apis
KEY_FILE="$KEYDIR/.xunfei_api_key_$KEYNAME"
[ -f "$KEY_FILE" ] || { echo "FATAL: key file not found: $KEY_FILE"; exit 1; }
KEY="$(tr -d '\r\n' < "$KEY_FILE")"

PY=/home/workspace/lww/project0412/Auto-claude-code-research-in-sleep/.venv/bin/python
WORK="$RUNS_DIR/curate_fromzero"
GRAPH="$WORK/trained_graph.json"
[ -f "$GRAPH" ] || { echo "FATAL: graph not found: $GRAPH"; exit 1; }
WORKERS="${WORKERS:-24}"
OUTDIR="$WORK/abl_$LABEL"
mkdir -p "$OUTDIR/logs" "$OUTDIR/routes"
GENCFG="$OUTDIR/gen_config.json"
printf '{"temperature":%s,"extra_body":{"enable_thinking":%s,"reasoning_effort":"%s"}}' \
  "$TEMPERATURE" "$THINKING" "$REASONING_EFFORT" > "$GENCFG"
TEST_ID_CSV="$(paste -sd, "$TEST_IDS")"

export PYTHONPATH="$PROJECT_ROOT:$REPO/src:${PYTHONPATH:-}"
cd "$REPO"
echo "===== INFER-ABL label=$LABEL router=$ROUTER verify=$VERIFY key=$KEYNAME workers=$WORKERS  $(date '+%F %T') ====="

SKILLSTRATA_GRAPH_PATH="$GRAPH" SKILLSTRATA_ROUTE_DIR="$OUTDIR/routes" \
SKILLSTRATA_ROUTER="$ROUTER" SKILLSTRATA_TYPE_BOOST=1.0 SKILLSTRATA_AGENT_THINK_BUDGET=1024 \
SKILLSTRATA_VERIFY_LOOP="$VERIFY" \
OPENAI_API_KEY="$KEY" OPENAI_BASE_URL="$OPENAI_BASE_URL" \
"$PY" run_spreadsheetbench.py \
  --data_path "$DATA" --model "$MODEL" --llm_client openai --agent cli_skillstrata \
  --instance_ids "$TEST_ID_CSV" --workers "$WORKERS" --max_turns "$MAX_TURNS" \
  --generation_config "$GENCFG" --missing_only \
  --output_dir "$OUTDIR" --log_dir "$OUTDIR/logs" --results_file "$OUTDIR/results.json"
RC=$?

"$PY" evaluate_with_official.py --data_path "$DATA" --output_dir "$OUTDIR" > "$OUTDIR/eval_stdout.txt" 2>&1
SCORE="$("$PY" "$SCRIPT_DIR/score_on_split.py" "$OUTDIR/eval_official_results.json" "$TEST_IDS" 2>/dev/null)"
echo "===== INFER-ABL label=$LABEL DONE  280held-out=$SCORE  rc=$RC  $(date '+%F %T') ====="
