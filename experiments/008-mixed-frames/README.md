# 008 mixed frames

**Question.** Can three images with different aspect ratios share one 480-piece set? A tree 20x24 (portrait), B sailboat 30x16 (landscape), C panorama 40x12.

**Setup.** `make_targets.py` draws the tone maps. `quantize.py` ranks each map into T0..T5 with counts 58/86/96/96/86/58. The brief's 60/90/100/100/90/60 sums to 500, not 480, so it was scaled. No shared frame is computed: `validate_scenes` checks border counts only for equal shapes. `scenes.txt` holds three blocks of different sizes, and `load_scenes` accepts it. Class spec: `classes.json` from 004.

**Feasibility.**
- `run-quarter/` (`--rotation quarter --cell 24`): invalid, 3 violations (one per map). Piece gates PASS, scene gates FAIL. Still 3 violations at 1M iterations.
- `run-flat/` (rotation none, 64 extra flat pieces): invalid, 41 violations. The prototype CLI has no `--extra-flat` option, so `run_flat.py` wraps `pieces_from_scenes` with `extra_flat_pieces` and calls `run_prototype`. 64 matches the surplus: 141 edge and 7 corner pieces against 84 frame cells. A scratch sweep (0/40/64/96/128/160 extras) gave 83/57/41/40/33/27 violations. 1M iterations at 64 still gave 41.
- `meta.energy` counts shared adjacencies only. Mismatches are separate, so energy 0.0 does not mean valid.

**Piece-level shared adjacencies** (both variants): AB 0, AC 0, BC 0. Neither solution is valid, so these are indicative only.

**Scene metrics** (`scene-metrics.txt`). Same-position overlap: "n/a (shapes differ)". 2x2 window reuse, plain/rotated: A-B 0.61/0.84, A-C 0.72/0.83, B-C 0.74/0.81. Transferable blob: 15 cells (3.1% of A), 11 (2.3% of A), 18 (3.8% of B). Scene gates fail on 2x2 reuse for every pair.

**Visual assessment** (`run-quarter/triptych.png`, invalid solution).
- Tree: the dark round canopy and trunk read. It is the most recognizable.
- Sailboat: the dark hull band reads, and a light patch suggests the sail. The mast is not clear.
- Panorama: a dark lower band under a light sky reads as a landscape. Peaks and sun do not read.
- Different pictures? Layouts differ, but all three share one dapple texture and mid-light blend, so they read as one family.

**Verdict.** Mixed frames run through the pipeline, but neither variant gives a valid solution. The 2x2 reuse gate fails for every pair.
