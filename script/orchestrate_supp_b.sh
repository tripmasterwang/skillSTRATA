#!/usr/bin/env bash
# =============================================================================
# Supplementary experiment B orchestrator (2026-06-29).
# Waits until ANY xunfei key frees up (a running evolution-ablation job exits),
# then launches the ROUND-2 ALL-COMPONENTS-ON evolution baseline so the 5
# evolution ablations (all round-2 early-stopped) can be quantified as Δpp
# instead of merely ranked. All-on = no --no-* flag (pass a single space so the
# launcher's ${3:?} check passes and $FLAGS word-splits to nothing).
# Self-exits after launching B. Safe to run in background.
# =============================================================================
set -uo pipefail
PROJ=/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/projects/skillSTRATA
KEYDIR=/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/_shared/LLM_apis
LOG="$PROJ/external/repos/Trace2Skill/runs/orchestrate_supp_b.log"

# last6 fragment of each key, for matching against running procs' env
declare -A KEY6
for n in lww lww2 lww3 lww4 wys; do
  k="$(tr -d '\r\n' < "$KEYDIR/.xunfei_api_key_$n")"
  KEY6[$n]="${k: -6}"
done

echo "[supp_b] start $(date '+%F %T'); waiting for a free key (lww4 reserved for A)" >> "$LOG"

while true; do
  # collect last6 of OPENAI_API_KEY for every running benchmark/curate proc
  busy=""
  for pid in $(pgrep -f "run_spreadsheetbench|curate_driver" 2>/dev/null); do
    e="$(tr '\0' '\n' < /proc/$pid/environ 2>/dev/null | grep '^OPENAI_API_KEY=' | head -1 | sed 's/.*=//')"
    [ -n "$e" ] && busy="$busy ${e: -6}"
  done
  # find a free key that is NOT lww4 (A owns lww4)
  free=""
  for n in lww wys lww2 lww3; do
    case " $busy " in
      *" ${KEY6[$n]} "*) : ;;            # busy
      *) free="$n"; break ;;             # free
    esac
  done
  if [ -n "$free" ]; then
    echo "[supp_b] $(date '+%F %T') key '$free' is free -> launching B (allon_r2, ROUNDS=2)" >> "$LOG"
    cd "$PROJ"
    ROUNDS=2 WORKERS=12 nohup bash script/run_evo_ablation.sh allon_r2 "$free" " " \
      >> "$PROJ/external/repos/Trace2Skill/runs/evo_allon_r2.log" 2>&1 &
    echo "[supp_b] launched B pid=$! on key=$free; orchestrator exiting" >> "$LOG"
    exit 0
  fi
  sleep 120
done
