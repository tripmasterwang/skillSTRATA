#!/usr/bin/env bash
# =============================================================================
# FROM-ZERO SkillStrata: learn the 3-layer skill graph from scratch on TRAIN,
# then test on the 280 held-out split using the REACT-AGENT retriever.
# No Claude Code needed. Edit script/config.sh (endpoint/key) first, then:
#     bash script/run_curate.sh
#
# Phase 1 (TRAIN / curate): start from an EMPTY graph -> for E rounds: run the agent on the
#   80 train ids, distill trajectories into skill fragments (qwen3.6), INSERT/MERGE/SPLIT them
#   into the capability graph + governance, and keep a round's edits only if the 40 val score
#   improves (validation gate). Output: a trained graph JSON.
# Phase 2 (TEST): freeze the trained graph; route over it with the LLM (react-agent) seed
#   selector on the 280 held-out test ids; official per-instance score.
# =============================================================================
set -uo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/config.sh"

ROUNDS="${ROUNDS:-4}"                       # curate epochs
WORK="${WORK:-$RUNS_DIR/curate_fromzero}"   # all curate artifacts
GRAPH="$WORK/trained_graph.json"            # the learned 3-layer graph
SKILLOS_ROOT="$PROJECT_ROOT"               # contains skillos/

echo "===== FROM-ZERO SkillStrata  $(date '+%F %T') ====="
echo "REPO=$REPO  MODEL=$MODEL  ENDPOINT=$OPENAI_BASE_URL  ROUNDS=$ROUNDS  WORKERS=$WORKERS"
[ -d "$REPO" ] || { echo "FATAL: repo not found: $REPO"; exit 1; }
[ -d "$DATA" ] || { echo "FATAL: data not found: $DATA"; exit 1; }
cd "$REPO"
python3 -c "import openpyxl,networkx,rank_bm25,openai" 2>/dev/null \
  || { echo "FATAL: pip install openpyxl networkx rank_bm25 openai"; exit 1; }
mkdir -p "$WORK"

# generation config (Qwen thinking control)
GENCFG="$WORK/gen_config.json"
printf '{"temperature":%s,"extra_body":{"enable_thinking":%s,"thinking_budget":%s}}' \
  "$TEMPERATURE" "$THINKING" "$THINKING_BUDGET" > "$GENCFG"

export PYTHONPATH="$SKILLOS_ROOT:${PYTHONPATH:-}"   # so curate_driver can import skillos

# ---- Phase 1: TRAIN (build the 3-layer graph from zero) ---------------------
if [ -f "$GRAPH" ] && [ "${RETRAIN:-0}" != "1" ]; then
  echo "[train] $GRAPH exists — skip (set RETRAIN=1 to redo)."
else
  echo "===== PHASE 1: curate from zero ($ROUNDS rounds) ====="
  python3 -m skillos.curate_driver \
    --repo "$REPO" --data "$DATA" \
    --train-ids "$TRAIN_IDS" --val-ids "$VAL_IDS" \
    --rounds "$ROUNDS" --graph-out "$GRAPH" --work-dir "$WORK" \
    --model "$MODEL" --gen-config "$GENCFG" --workers "$WORKERS" --max-turns "$MAX_TURNS"
fi
[ -f "$GRAPH" ] || { echo "FATAL: training did not produce $GRAPH"; exit 1; }
echo "[train] trained graph: $GRAPH"
python3 -c "import json;d=json.load(open('$GRAPH'));print('  nodes:',len(d['skills']),'| capability edges:',len(d['capability_edges']),'| governance:',len(d['governance']))"

# ---- Phase 2: TEST on 280 held-out with the REACT-AGENT retriever ------------
echo "===== PHASE 2: test on 280 held-out (react-agent retriever) ====="
TESTDIR="$WORK/test_280"
mkdir -p "$TESTDIR/logs"
TEST_ID_CSV="$(paste -sd, "$TEST_IDS")"
SKILLSTRATA_GRAPH_PATH="$GRAPH" \
SKILLSTRATA_ROUTER=agent SKILLSTRATA_TYPE_BOOST=1.0 SKILLSTRATA_AGENT_THINK_BUDGET=1024 \
python3 run_spreadsheetbench.py \
  --data_path "$DATA" --model "$MODEL" --llm_client openai --agent cli_skillstrata \
  --instance_ids "$TEST_ID_CSV" --workers "$WORKERS" --max_turns "$MAX_TURNS" \
  --generation_config "$GENCFG" --missing_only \
  --output_dir "$TESTDIR" --log_dir "$TESTDIR/logs" --results_file "$TESTDIR/results.json"

python3 evaluate_with_official.py --data_path "$DATA" --output_dir "$TESTDIR" > "$TESTDIR/eval_stdout.txt" 2>&1
SCORE="$(python3 "$SCRIPT_DIR/score_on_split.py" "$TESTDIR/eval_official_results.json" "$TEST_IDS")"
echo ""
echo "===== RESULT: from-zero SkillStrata + react-agent retriever on 280 held-out = $SCORE ====="

# ---- assemble a single self-contained RESULTS.md (text-transferable) --------
REPORT="$WORK/RESULTS.md"
python3 "$SCRIPT_DIR/make_report.py" --out "$REPORT" \
  --graph "$GRAPH" --history "$WORK/curate_history.json" \
  --eval-json "$TESTDIR/eval_official_results.json" --test-ids "$TEST_IDS" \
  --meta "model=$MODEL,endpoint=$OPENAI_BASE_URL,rounds=$ROUNDS,workers=$WORKERS,thinking_budget=$THINKING_BUDGET,date=$(date '+%F %T'),test=280held-out,result=$SCORE"
echo ""
echo "================= COPY EVERYTHING BELOW (this is $REPORT) ================="
cat "$REPORT"
echo "================= END OF $REPORT ================="
