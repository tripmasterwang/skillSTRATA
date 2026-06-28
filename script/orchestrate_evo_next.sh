#!/usr/bin/env bash
# =============================================================================
# Orchestrator (one-shot, run in background):
#  A) evo round-2 stop: when evo_<e>/train_r3 appears (=> round-2 graph已存盘),
#     pkill the curate_driver for that lane; the parent run_evo_ablation.sh keeps
#     going (set -uo pipefail, no -e) and auto-runs test_280 on the round-2 graph.
#  B) when abl_graph eval done (=> lww/lww4 freed), launch the 3 missing evo
#     ablations with ROUNDS=2 (nomerge / nockpt / onlyinsert), each on its own key.
# =============================================================================
set -uo pipefail
ROOT=/home/workspace/lww/project0412/projects/multiagent/multi-agent-memory-research/projects/skillSTRATA
R=$ROOT/external/repos/Trace2Skill/runs
CF=$R/curate_fromzero
LOG=$R/orchestrate_evo_next.log
echo "===== orchestrator start $(date '+%F %T') =====" >> "$LOG"

# ---- A) round-2 watchdog for the two in-flight evo lanes ----
for e in nogate nosplit; do
  (
    while [ ! -d "$R/evo_$e/train_r3" ]; do sleep 60; done
    echo "[$(date '+%T')] evo_$e: train_r3 appeared -> round-2 graph saved; killing curate_driver" >> "$LOG"
    pkill -f "skillos.curate_driver.*evo_$e/trained_graph" 2>/dev/null
    sleep 5
    pkill -f "$R/evo_$e/train_r3" 2>/dev/null   # orphaned round-3 rollout workers
    echo "[$(date '+%T')] evo_$e: killed; parent run_evo_ablation.sh will now run test_280" >> "$LOG"
  ) &
done

# ---- B) launch 3 missing evo ablations once abl_graph frees a key ----
(
  while [ ! -f "$CF/abl_graph/eval_official_results.json" ]; do sleep 60; done
  echo "[$(date '+%T')] abl_graph done -> launching 3 evo ablations (ROUNDS=2)" >> "$LOG"
  cd "$ROOT"
  ROUNDS=2 nohup bash script/run_evo_ablation.sh nomerge    lww  "--no-merge"                                   > "$R/evo_nomerge.log"    2>&1 &
  sleep 3
  ROUNDS=2 nohup bash script/run_evo_ablation.sh nockpt     lww2 "--no-checkpoint"                              > "$R/evo_nockpt.log"     2>&1 &
  sleep 3
  ROUNDS=2 nohup bash script/run_evo_ablation.sh onlyinsert lww3 "--no-merge --no-split --no-gate --no-checkpoint" > "$R/evo_onlyinsert.log" 2>&1 &
  echo "[$(date '+%T')] 3 evo ablations launched (nomerge=lww nockpt=lww2 onlyinsert=lww3)" >> "$LOG"
) &

wait
echo "===== orchestrator done $(date '+%F %T') =====" >> "$LOG"
