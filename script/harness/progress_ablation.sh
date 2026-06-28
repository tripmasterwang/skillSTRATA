#!/usr/bin/env bash
W=external/repos/Trace2Skill/runs/curate_fromzero
echo "===== harness ablation 进度 ($(date '+%F %T')) ====="
for h in codex claude minisweagent; do
  alive=$(ps -ef|grep "run_ablation.sh $h"|grep -v grep|wc -l)
  printf "[%s] alive=%s\n" "$h" "$alive"
  for arm in bare skill; do
    d="$W/test_280_${h}_${arm}"
    n=$(ls $d/logs/*.md 2>/dev/null|wc -l)
    sc=$(grep -hoE "FINAL.*|score on 280 held-out = [0-9.]+% \([0-9]+/280\)" script/harness/runlogs/abl_$h.out 2>/dev/null | grep -oE "[0-9.]+% \([0-9]+/280\)" | tail -1)
    printf "   %-6s %3s/280  %s\n" "$arm" "$n" "$sc"
  done
done
