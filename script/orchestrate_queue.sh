#!/usr/bin/env bash
# =============================================================================
# Priority queue orchestrator (2026-06-29). Launches, in order, as keys free up:
#   1) evo_r1_test  : reconstructed round-1 graph on test_280  (per-round curve)
#   2) evo_r2_test  : reconstructed round-2 graph on test_280  (per-round curve)
#   3) allon_r2     : round-2 all-components-on evolution baseline (supp B)
# Each task grabs one free xunfei key; the orchestrator then waits for the NEXT
# free key before launching the next task. Self-exits after all are launched.
# =============================================================================
set -uo pipefail
PROJ=/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/projects/skillSTRATA
KEYDIR=/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/_shared/LLM_apis
RUNS="$PROJ/external/repos/Trace2Skill/runs"; CF="$RUNS/curate_fromzero"
LOG="$RUNS/orchestrate_queue.log"
declare -A KEY6
for n in lww lww2 lww3 lww4 wys; do KEY6[$n]="$(tr -d '\r\n' < "$KEYDIR/.xunfei_api_key_$n" | tail -c 6)"; done

launch() {  # $1=index
  case "$1" in
    0) cd "$PROJ"; WORKERS=24 nohup bash script/run_graph_on_test.sh evo_r1_test "$CF/graph_r1.json" "$2" >> "$RUNS/evo_r1_test.log" 2>&1 & ;;
    1) cd "$PROJ"; WORKERS=24 nohup bash script/run_graph_on_test.sh evo_r2_test "$CF/graph_r2.json" "$2" >> "$RUNS/evo_r2_test.log" 2>&1 & ;;
    2) cd "$PROJ"; ROUNDS=2 WORKERS=12 nohup bash script/run_evo_ablation.sh allon_r2 "$2" " " >> "$RUNS/evo_allon_r2.log" 2>&1 & ;;
  esac
  echo "[queue] $(date '+%F %T') launched task#$1 on key=$2 pid=$!" >> "$LOG"
}
NAMES=(evo_r1_test evo_r2_test allon_r2)
echo "[queue] start $(date '+%F %T'); tasks: ${NAMES[*]}" >> "$LOG"
i=0
while [ $i -lt 3 ]; do
  busy=""
  for pid in $(pgrep -f "run_spreadsheetbench|curate_driver" 2>/dev/null); do
    e="$(tr '\0' '\n' < /proc/$pid/environ 2>/dev/null | grep '^OPENAI_API_KEY=' | head -1 | sed 's/.*=//')"
    [ -n "$e" ] && busy="$busy $(printf '%s' "$e" | tail -c 6)"
  done
  free=""
  for n in lww3 wys lww2 lww lww4; do
    case " $busy " in *" ${KEY6[$n]} "*) : ;; *) free="$n"; break ;; esac
  done
  if [ -n "$free" ]; then
    launch $i "$free"; i=$((i+1)); sleep 45   # let the new proc occupy its key before next scan
  else
    sleep 120
  fi
done
echo "[queue] all launched, exiting $(date '+%F %T')" >> "$LOG"
