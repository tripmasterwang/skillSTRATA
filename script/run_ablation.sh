#!/usr/bin/env bash
# =============================================================================
# Harness-level ablation for ONE harness: run the 280 held-out split TWICE on the
# SAME key/port (serial, so the proxy port + key are not contended):
#   1) BARE     = bare harness, NO SkillStrata (blank graph, 0 routed skills)
#   2) +SkillStrata = routed skills from the frozen ReAct-trained graph + verify-loop
# So the comparison is "their codex/claude/mini  vs  ours = that harness + SkillStrata".
#
# Usage:  bash script/run_ablation.sh <harness> <key_file> [proxy_port]
# Env:    WORKERS(40)
# =============================================================================
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
H="${1:?need harness}"; KEY="${2:?need key file}"; PORT="${3:-}"
WORKERS="${WORKERS:-40}"

echo "########## ABLATION [$H]  BARE first, then +SkillStrata  $(date '+%F %T') ##########"

echo "===== [$H] arm 1/2: BARE (no SkillStrata) ====="
NOSKILL=1 WORKERS="$WORKERS" OUT_SUFFIX="${H}_bare" \
  bash "$SCRIPT_DIR/run_harness.sh" "$H" "$KEY" $PORT

echo "===== [$H] arm 2/2: +SkillStrata (routed graph + verify-loop) ====="
NOSKILL=0 WORKERS="$WORKERS" OUT_SUFFIX="${H}_skill" \
  bash "$SCRIPT_DIR/run_harness.sh" "$H" "$KEY" $PORT

echo "########## ABLATION [$H] done  $(date '+%F %T') ##########"
