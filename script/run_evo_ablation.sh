#!/usr/bin/env bash
# =============================================================================
# EVOLUTION-PHASE ablation (task #8): from-zero curate with ONE evolution
# component disabled (LOO) or only-INSERT (LOI), REACT executor, then test on
# the 280 held-out split with that ablated graph. The full-system baseline is
# the existing runs/curate_fromzero. Isolates which evolution mechanism is
# load-bearing for the no-skill -> SkillStrata gain.
#
# Usage:
#   bash script/run_evo_ablation.sh <label> <keyname> "<curate_flags>"
#     <label>       : nomerge | nosplit | nogate | nockpt | onlyinsert | ...
#     <keyname>     : lww | lww2 | lww3 | lww4 | wys
#     <curate_flags>: e.g. "--no-gate"   "--no-merge --no-split --no-gate --no-checkpoint"
# Env: ROUNDS(4) WORKERS(12)
# =============================================================================
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

LABEL="${1:?label}"; KEYNAME="${2:?keyname}"; FLAGS="${3:?curate flags}"
KEYDIR=/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/_shared/LLM_apis
KEY_FILE="$KEYDIR/.xunfei_api_key_$KEYNAME"
[ -f "$KEY_FILE" ] || { echo "FATAL: key file not found: $KEY_FILE"; exit 1; }
KEY="$(tr -d '\r\n' < "$KEY_FILE")"

PY=/home/workspace/lww/project0412/Auto-claude-code-research-in-sleep/.venv/bin/python
ROUNDS="${ROUNDS:-4}"; WORKERS="${WORKERS:-12}"
WORK="$RUNS_DIR/evo_$LABEL"
GRAPH="$WORK/trained_graph.json"
mkdir -p "$WORK"
GENCFG="$WORK/gen_config.json"
printf '{"temperature":%s,"extra_body":{"enable_thinking":%s,"reasoning_effort":"%s"}}' \
  "$TEMPERATURE" "$THINKING" "$REASONING_EFFORT" > "$GENCFG"

export PYTHONPATH="$PROJECT_ROOT:$REPO/src:${PYTHONPATH:-}"
export OPENAI_API_KEY="$KEY"; export OPENAI_BASE_URL="$OPENAI_BASE_URL"
cd "$REPO"
echo "===== EVO-ABL label=$LABEL flags='$FLAGS' key=$KEYNAME rounds=$ROUNDS workers=$WORKERS  $(date '+%F %T') ====="

# ---- Phase 1: from-zero curate with the ablation flag(s) ----
if [ -f "$GRAPH" ] && [ "${RETRAIN:-0}" != "1" ]; then
  echo "[$LABEL][train] $GRAPH exists — skip (RETRAIN=1 to redo)."
else
  "$PY" -m skillos.curate_driver \
    --repo "$REPO" --data "$DATA" \
    --train-ids "$TRAIN_IDS" --val-ids "$VAL_IDS" \
    --rounds "$ROUNDS" --graph-out "$GRAPH" --work-dir "$WORK" \
    --model "$MODEL" --gen-config "$GENCFG" --workers "$WORKERS" --max-turns "$MAX_TURNS" \
    $FLAGS
fi
[ -f "$GRAPH" ] || { echo "FATAL: [$LABEL] training produced no graph"; exit 1; }
"$PY" -c "import json;d=json.load(open('$GRAPH'));print('[$LABEL] nodes',len(d['skills']),'edges',len(d['capability_edges']),'gov',len(d['governance']))"

# ---- Phase 2: test on 280 held-out with the ablated graph (same router/verify as main) ----
TESTDIR="$WORK/test_280"
mkdir -p "$TESTDIR/logs" "$TESTDIR/routes"
TEST_ID_CSV="$(paste -sd, "$TEST_IDS")"
SKILLSTRATA_GRAPH_PATH="$GRAPH" SKILLSTRATA_ROUTE_DIR="$TESTDIR/routes" \
SKILLSTRATA_ROUTER=agent SKILLSTRATA_TYPE_BOOST=1.0 SKILLSTRATA_AGENT_THINK_BUDGET=1024 \
SKILLSTRATA_VERIFY_LOOP=1 \
"$PY" run_spreadsheetbench.py \
  --data_path "$DATA" --model "$MODEL" --llm_client openai --agent cli_skillstrata \
  --instance_ids "$TEST_ID_CSV" --workers "$WORKERS" --max_turns "$MAX_TURNS" \
  --generation_config "$GENCFG" --missing_only \
  --output_dir "$TESTDIR" --log_dir "$TESTDIR/logs" --results_file "$TESTDIR/results.json"
"$PY" evaluate_with_official.py --data_path "$DATA" --output_dir "$TESTDIR" > "$TESTDIR/eval_stdout.txt" 2>&1
SCORE="$("$PY" "$SCRIPT_DIR/score_on_split.py" "$TESTDIR/eval_official_results.json" "$TEST_IDS" 2>/dev/null)"
echo "===== EVO-ABL label=$LABEL DONE  280held-out=$SCORE  $(date '+%F %T') ====="
