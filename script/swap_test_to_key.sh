#!/usr/bin/env bash
# Move a running test_280 to a different (idle) xunfei key to use its independent concurrency lane.
# Kills the current test run_spreadsheetbench + its parent, then resumes the SAME test_280 dir with
# --missing_only on the new key (already-finished instances are skipped, no progress lost), then
# evaluates + scores. Usage: bash script/swap_test_to_key.sh <work_subdir> <keyname>
#   e.g. bash script/swap_test_to_key.sh evo_nomerge lww4
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
SUB="${1:?work subdir e.g. evo_nomerge}"; KEYNAME="${2:?keyname}"
KEYDIR=/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/_shared/LLM_apis
KEY="$(tr -d '\r\n' < "$KEYDIR/.xunfei_api_key_$KEYNAME")"
PY=/home/workspace/lww/project0412/Auto-claude-code-research-in-sleep/.venv/bin/python
WORK="$RUNS_DIR/$SUB"; GRAPH="$WORK/trained_graph.json"; TESTDIR="$WORK/test_280"; GENCFG="$WORK/gen_config.json"
[ -f "$GRAPH" ] || { echo "FATAL: no graph $GRAPH"; exit 1; }

# kill current test run for this subdir + its parent shell
for pid in $(pgrep -f "run_spreadsheetbench.*$SUB/test_280"); do
  ppid=$(ps -o ppid= -p "$pid" | tr -d ' ')
  echo "[swap] killing test pid=$pid (parent $ppid) for $SUB"
  kill "$pid" 2>/dev/null; [ -n "$ppid" ] && kill "$ppid" 2>/dev/null
done
sleep 3
TEST_ID_CSV="$(paste -sd, "$TEST_IDS")"
export PYTHONPATH="$PROJECT_ROOT:$REPO/src:${PYTHONPATH:-}"
cd "$REPO"
echo "===== SWAP $SUB -> key=$KEYNAME resume test_280 $(date '+%F %T') ====="
SKILLSTRATA_GRAPH_PATH="$GRAPH" SKILLSTRATA_ROUTE_DIR="$TESTDIR/routes" \
SKILLSTRATA_ROUTER=agent SKILLSTRATA_TYPE_BOOST=1.0 SKILLSTRATA_AGENT_THINK_BUDGET=1024 \
SKILLSTRATA_VERIFY_LOOP=1 OPENAI_API_KEY="$KEY" OPENAI_BASE_URL="$OPENAI_BASE_URL" \
"$PY" run_spreadsheetbench.py \
  --data_path "$DATA" --model "$MODEL" --llm_client openai --agent cli_skillstrata \
  --instance_ids "$TEST_ID_CSV" --workers "${WORKERS:-24}" --max_turns "$MAX_TURNS" \
  --generation_config "$GENCFG" --missing_only \
  --output_dir "$TESTDIR" --log_dir "$TESTDIR/logs" --results_file "$TESTDIR/results.json"
"$PY" evaluate_with_official.py --data_path "$DATA" --output_dir "$TESTDIR" > "$TESTDIR/eval_stdout.txt" 2>&1
SCORE="$("$PY" "$SCRIPT_DIR/score_on_split.py" "$TESTDIR/eval_official_results.json" "$TEST_IDS" 2>/dev/null)"
echo "===== SWAP $SUB DONE 280held-out=$SCORE $(date '+%F %T') ====="
