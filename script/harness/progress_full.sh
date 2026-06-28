#!/usr/bin/env bash
W=external/repos/Trace2Skill/runs
PY=/home/workspace/lww/project0412/Auto-claude-code-research-in-sleep/.venv/bin/python
echo "===== SkillStrata 三 harness 全流程进度 ($(date '+%F %T')) ====="
for h in codex claude minisweagent; do
  d="$W/curate_$h"
  alive=$(pgrep -f "run_harness_full.sh $h\b" >/dev/null && echo yes || echo no)
  echo "[$h]  alive=$alive  (work: curate_$h)"
  for r in $(ls -d $d/train_r* $d/val_r* 2>/dev/null | sort -V); do
    printf "   %-9s %s\n" "$(basename $r)" "$(ls $r/logs/*.md 2>/dev/null|wc -l)"
  done
  [ -d "$d/test_280" ] && printf "   %-9s %s/280\n" "test_280" "$(ls $d/test_280/logs/*.md 2>/dev/null|wc -l)"
  if [ -f "$d/curate_history.json" ]; then
    echo "   >> 训练完成. 验证曲线: $($PY -c "import json;print([(x['round'],x['val'],x['accepted']) for x in json.load(open('$d/curate_history.json'))])" 2>/dev/null)"
  fi
  # 最终分数（test 跑完才有）
  grep -hoE "FINAL score on 280 held-out = .*" script/harness/runlogs/full_$h.out 2>/dev/null | tail -1 | sed 's/^/   /'
done
