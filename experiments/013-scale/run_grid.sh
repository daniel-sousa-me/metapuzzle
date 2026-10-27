#!/usr/bin/env bash
# Experiment 013: the 005 pipeline at one grid size, then both renders.
# usage: run_grid.sh COLSxROWS CELL_PX     e.g. run_grid.sh 25x30 27
# Outputs: g<COLS>x<ROWS>/ (timings.txt holds the wall time of each step).
set -euo pipefail
G=$1
CELL=$2
HERE=/home/user/metapuzzle/experiments/013-scale
CLS=/home/user/metapuzzle/experiments/005-hybrid-tones
W=$HERE/g$G
export GRID=$G PYTHONHASHSEED=0
cd "$HERE"
mkdir -p "$W"
: > "$W/timings.txt"

timed() {  # timed NAME COMMAND...   (stdout of COMMAND goes to the caller's redirection)
    local name=$1 t0 t1
    shift
    t0=$(date +%s.%N)
    "$@"
    t1=$(date +%s.%N)
    awk -v n="$name" -v a="$t0" -v b="$t1" 'BEGIN { printf "%s %.1f s\n", n, b - a }' >> "$W/timings.txt"
}

SIZES="$G,$G,$G"
timed make_targets python3 make_targets.py -v2 > "$W/make-targets-report.txt"
timed quantize python3 quantize.py -v2 > "$W/quantize-report-v2.txt"
timed quantize_v5 python3 quantize_v5.py > "$W/quantize-report-v5.txt"
timed make_roles python3 make_roles_v5.py > "$W/roles-report.txt"
timed build_scenes python3 build_scenes_v5.py > "$W/build-scenes-report.txt"
metapuzzle scene-metrics "$W/scenes.txt" > "$W/scene-metrics.txt" || true
timed prototype_full metapuzzle prototype --scenes "$W/scenes.txt" --classes "$CLS/classes-v4.json" \
    --out "$W/run-full" --sizes "$SIZES" --border standard --rotation quarter --seed 0 --iters 300000 \
    --cell "$CELL" > "$W/run-full.log"
timed prototype_ink metapuzzle prototype --scenes "$W/scenes.txt" --classes "$CLS/classes-ink.json" \
    --out "$W/run-ink" --sizes "$SIZES" --border standard --rotation quarter --seed 0 --iters 300000 \
    --cell "$CELL" > "$W/run-ink.log"
echo "done $G" >> "$W/timings.txt"
cat "$W/timings.txt"
