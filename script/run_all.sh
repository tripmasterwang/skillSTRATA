#!/usr/bin/env bash
# =============================================================================
# SkillStrata — run the full routing-comparison experiment suite on a server
# WITHOUT Claude Code. Edit script/config.sh first, then:
#     bash script/run_all.sh                 # run all variants in config
#     bash script/run_all.sh skillstrata-agent skillstrata-graph   # only these
#     WORKERS=16 END_IDX=20 bash script/run_all.sh                  # quick smoke
#
# For each variant it: runs SpreadsheetBench (resume-safe) -> official eval on
# full-400 -> scores on the SkillOpt 80/40/280 held-out splits -> appends to
# runs/COMPARISON.md. Safe to re-run; completed variants are skipped (RESUME=1).
# =============================================================================
set -uo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/config.sh"

SELECT=("$@")   # optional list of labels to run; empty = all

# ---- preflight --------------------------------------------------------------
echo "===== SkillStrata run_all  $(date '+%F %T') ====="
echo "REPO=$REPO"
echo "MODEL=$MODEL  ENDPOINT=$OPENAI_BASE_URL  WORKERS=$WORKERS  END_IDX=$END_IDX"
[ -d "$REPO" ]  || { echo "FATAL: Trace2Skill repo not found at $REPO"; exit 1; }
[ -d "$DATA" ]  || { echo "FATAL: data not found at $DATA"; exit 1; }
cd "$REPO"
python3 -c "import openpyxl, networkx, rank_bm25, openai" 2>/dev/null \
  || { echo "FATAL: missing python deps. Need: openpyxl networkx rank_bm25 openai (pip install)"; exit 1; }
if [ "$OPENAI_API_KEY" = "EMPTY" ]; then
  echo "NOTE: OPENAI_API_KEY=EMPTY (fine for an auth-less local server; set a key otherwise)."
fi

# ---- one-time setup: gen config + single-skill dir for monolithic-xlsx35B ----
mkdir -p "$RUNS_DIR"
GENCFG="$RUNS_DIR/gen_config.json"
printf '{"temperature":%s,"extra_body":{"enable_thinking":%s,"thinking_budget":%s}}' \
  "$TEMPERATURE" "$THINKING" "$THINKING_BUDGET" > "$GENCFG"
echo "gen_config: $(cat "$GENCFG")"

SKILLS_35B="$RUNS_DIR/skills_35b"            # cli_skill_preloaded needs a dir holding ONLY xlsx-35B
if [ ! -d "$SKILLS_35B/xlsx-35B" ]; then
  mkdir -p "$SKILLS_35B"
  cp -r "$REPO/spreadsheet_agent/skills/xlsx-35B" "$SKILLS_35B/xlsx-35B"
fi

n_outputs () { find "$1/spreadsheet" -name "*_output.xlsx" 2>/dev/null | wc -l; }
want () {  # is this label selected?
  [ ${#SELECT[@]} -eq 0 ] && return 0
  for s in "${SELECT[@]}"; do [ "$s" = "$1" ] && return 0; done
  return 1
}

# fresh comparison table
SUMMARY="$RUNS_DIR/COMPARISON.md"
{
  echo "# SkillStrata comparison — SpreadsheetBench (model=$MODEL, thinking_budget=$THINKING_BUDGET)"
  echo "Generated $(date '+%F %T'). Metric: official per-instance (hard)."
  echo ""
  echo "| Variant | full-400 | 280 held-out test | 40 val | 80 train |"
  echo "|---------|----------|-------------------|--------|----------|"
} > "$SUMMARY"

# ---- run + eval each variant ------------------------------------------------
for spec in "${VARIANTS[@]}"; do
  label="${spec%%|*}"; rest="${spec#*|}"; agent="${rest%%|*}"; extra="${rest#*|}"
  want "$label" || continue
  outdir="$RUNS_DIR/$label"
  echo ""
  echo "================= [$label]  agent=$agent  env=[$extra]  $(date '+%T') ================="

  skip_run=0
  if [ "$RESUME" = "1" ] && [ -f "$outdir/results.json" ]; then
    echo "  [$label] results.json present ($(n_outputs "$outdir") outputs) — skip run (RESUME=1), eval only."
    skip_run=1
  fi

  if [ "$skip_run" = "0" ]; then
    mkdir -p "$outdir/logs"
    skills_arg=()
    [ "$agent" = "cli_skill_preloaded" ] && skills_arg=(--skills_dir "$SKILLS_35B")
    missing_arg=(); [ "$MISSING_ONLY" = "1" ] && missing_arg=(--missing_only)
    # shellcheck disable=SC2086
    env $extra python3 run_spreadsheetbench.py \
      --data_path "$DATA" --model "$MODEL" --llm_client openai --agent "$agent" \
      --max_turns "$MAX_TURNS" --workers "$WORKERS" --end_idx "$END_IDX" \
      --generation_config "$GENCFG" "${skills_arg[@]}" "${missing_arg[@]}" \
      --output_dir "$outdir" --log_dir "$outdir/logs" --results_file "$outdir/results.json"
    echo "  [$label] run done $(date '+%T'); produced $(n_outputs "$outdir")/$END_IDX"
  fi

  # official eval on full-400
  python3 evaluate_with_official.py --data_path "$DATA" --output_dir "$outdir" \
      --end_idx "$END_IDX" > "$outdir/eval_stdout.txt" 2>&1
  EVAL_JSON="$outdir/eval_official_results.json"

  full=$(python3 "$SCRIPT_DIR/score_on_split.py" "$EVAL_JSON" --all 2>/dev/null)
  te=$(python3 "$SCRIPT_DIR/score_on_split.py" "$EVAL_JSON" "$TEST_IDS" 2>/dev/null)
  va=$(python3 "$SCRIPT_DIR/score_on_split.py" "$EVAL_JSON" "$VAL_IDS" 2>/dev/null)
  tr=$(python3 "$SCRIPT_DIR/score_on_split.py" "$EVAL_JSON" "$TRAIN_IDS" 2>/dev/null)
  echo "| $label | $full | $te | $va | $tr |" >> "$SUMMARY"
  echo "  [$label] full-400=$full | 280test=$te | 40val=$va | 80train=$tr"
done

echo ""
echo "===== DONE $(date '+%F %T') ====="
echo "===== $SUMMARY ====="
cat "$SUMMARY"
