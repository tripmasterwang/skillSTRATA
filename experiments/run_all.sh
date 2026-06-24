#!/usr/bin/env bash
# Reproduce the SkillOS paper tables (main results + ablation study).
# Deterministic; no GPU / no API budget. ~10s total.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

SEEDS="${SEEDS:-0 1 2 3 4 5 6 7}"
mkdir -p results

echo "== unit tests =="
python3 -m pytest tests/ -q

echo; echo "== main results (proposal Expected Main Result) =="
python3 -m sim.run_main --seeds $SEEDS --out results/main.json

echo; echo "== ablation study (proposal Ablation Study) =="
python3 -m sim.run_ablations --seeds $SEEDS --out results/ablations.json

echo; echo "[done] tables saved under results/"
