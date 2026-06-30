#!/usr/bin/env bash
# Speed up the last run (evo_r2_test) by sharding its remaining instances across 4 idle keys.
# Kills the current single-key r2 run, splits the 280 test ids into 4 shards, runs each shard with
# --missing_only on a different key (already-finished instances skipped, shards disjoint -> no dup),
# waits for all, then evaluates + scores. Output dir unchanged.
set -uo pipefail
SD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; source "$SD/config.sh"
PY=/home/workspace/lww/project0412/Auto-claude-code-research-in-sleep/.venv/bin/python
KEYDIR=/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/_shared/LLM_apis
GRAPH="$RUNS_DIR/curate_fromzero/graph_r2.json"; OUT="$RUNS_DIR/curate_fromzero/evo_r2_test"
[ -f "$GRAPH" ] || { echo "FATAL no $GRAPH"; exit 1; }
KEYS=(lww lww3 lww4 wys)

echo "[turbo] killing current r2 single-key run…"
pkill -f "run_spreadsheetbench.*evo_r2_test" 2>/dev/null; sleep 3

mapfile -t ALL < "$TEST_IDS"; N=${#ALL[@]}; PER=$(( (N + 3) / 4 ))
export PYTHONPATH="$PROJECT_ROOT:$REPO/src:${PYTHONPATH:-}"; cd "$REPO"
echo "[turbo] $N ids -> 4 shards of ~$PER, keys: ${KEYS[*]}  $(date '+%T')"
pids=()
for i in 0 1 2 3; do
  shard=("${ALL[@]:$((i*PER)):$PER}"); [ ${#shard[@]} -eq 0 ] && continue
  csv=$(IFS=,; echo "${shard[*]}")
  KEY="$(tr -d '\r\n' < "$KEYDIR/.xunfei_api_key_${KEYS[$i]}")"
  SKILLSTRATA_GRAPH_PATH="$GRAPH" SKILLSTRATA_ROUTE_DIR="$OUT/routes" \
  SKILLSTRATA_ROUTER=agent SKILLSTRATA_TYPE_BOOST=1.0 SKILLSTRATA_AGENT_THINK_BUDGET=1024 \
  SKILLSTRATA_VERIFY_LOOP=1 OPENAI_API_KEY="$KEY" OPENAI_BASE_URL="$OPENAI_BASE_URL" \
  "$PY" run_spreadsheetbench.py --data_path "$DATA" --model "$MODEL" --llm_client openai \
    --agent cli_skillstrata --instance_ids "$csv" --workers 12 --max_turns "$MAX_TURNS" \
    --generation_config "$OUT/gen_config.json" --missing_only \
    --output_dir "$OUT" --log_dir "$OUT/logs" --results_file "$OUT/results_shard$i.json" \
    >> "$OUT/turbo_shard$i.log" 2>&1 &
  pids+=($!); echo "[turbo] shard$i key=${KEYS[$i]} ${#shard[@]} ids pid=$!"
done
wait "${pids[@]}"
echo "[turbo] all shards done, evaluating…  $(date '+%T')"
"$PY" evaluate_with_official.py --data_path "$DATA" --output_dir "$OUT" > "$OUT/eval_stdout.txt" 2>&1
SC="$("$PY" "$SD/score_on_split.py" "$OUT/eval_official_results.json" "$TEST_IDS" 2>/dev/null)"
echo "[turbo] DONE r2 280held-out=$SC  $(date '+%T')"
