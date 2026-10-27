# 011 subjects: "Field, Wood and Water"

**Goal:** hare, owl and swan in value inversion on a tray border with quarter rotation (the subject set).
**Result:** the 27x38-v2 renders share 0/0/1 and pass the piece gate. Blind test: distinctiveness 4/5, hare 4/5, owl 4/5 (read as a skull), swan 3/5. T9 is 2/5 on v2 and v4. The v5 motif render is in progress (see `docs/HANDOVER.md`).

Hare at dawn (vertical), owl at dusk (moon halo, radial), swan at midnight (horizontal). Value
inversion: D = field / owl / night sky, M = hare / dusk sky / lake, L = sky / moon and snow /
swan. S (chips on L, always enclosed by L): flock, bramble, wing feathers. W: cloud bank, cloud
bars, swell. Design notes: `docs/design/08-subjects.md`.

**Run:** `python3 make_targets.py [COLSxROWS ...]` (default 27x38 primary, then 20x25; about 25 min
on 4 cores). The primary size is written here, and every size to `<COLS>x<ROWS>/`:
`tiers-{A,B,C}.txt`, `budgets.txt`, `targets-preview.png`, `contours-preview.png` (ink, 16 px/cell).
`python3 budget.py tiers-*.txt` prints the budget table for any tier maps.

**Pipeline:** hand-drawn 20 × 25 sketches (figures locked) → annealer moves only background-line
cells → resample to the target size → clean → re-balance.

**Budgets at 27 × 38:** counts D/M/L 318/366/293, 318/366/293, 312/373/292; S 49 and W 39 each.
Edges (and corners) D-M 63/58/62 (55/52/58), D-L 75/77/75 (82/80/83), M-L 94/88/91
(113/108/105). S-D and S-M 0. Tips, strips, dots and pinches 0. 45° run cells within 7.

**Worries:**
- Ink recognition is untested: the hare's ears (about 3 cells) and the owl's cat-like tufts are
  the weak points. The swan reads.
- The shapes are resampled pixel art (stepped outlines, 12 % vertical stretch at 27 × 38).
- 10–18 three-tier junction cells per picture, with no tile class yet.
- The frames differ, so a tray or frameless cut is needed.

`prev-attempt/` holds the earlier hare/owl/whale run (quantize, roles, render), kept for
reference; it is not part of this pipeline.

## Hare v2

`make_targets.py` v2 (v1 kept as `make_targets_v1.py`) draws all three pictures natively at 27 × 38
and writes `27x38-v2/` and `20x25-v2/`. Hare: sitting profile, two separate ears 4–5 cells wide,
nape and throat notches, haunch, front leg, paw, tail and a dot eye; the body is in the dark field,
the head in the light sky. Following blind test 1, the owl got octagonal eyes, a beak, a moon
disc, a branch and a tail, and the swan a "2" neck, a beak, an eye and a wing on a W band. W and S
are full tiers (`budget_v2.py`). Each picture has one D-on-L and one D-on-M dot. Everything
matches within 5, except M–W edges (18/24/24) and 45° runs (eyes). 20x25-v2 is a rough downsample
(W and dots lost) and is not matched.

## Redrawn tiers run (27x38-v2)

`pipeline/run_from_tiers_v3.py --in-dir 27x38-v2 --out-dir 27x38-v2 --render-tag ""` (cell 21; the
options were added, the logic is unchanged). Equalize: surplus 73/58/62 (193) to 50/36/41 (127) for
A/B/C, with 8/22/6 cells changed. The run stopped in roles (exit 1): the hare needs 11 D hosts but
only 10 far D cells exist, and the swan needs 21 with 1. The host check counts D cells next to a
transition (near), which `pick()` never uses for D, so no scenes, renders or solution JSON were
written. Log: `27x38-v2/pipeline-out/run-main.log`.

## v3: class-level matching

`make_targets_v3.py` (a copy of make_targets.py) starts from the v2 pictures and matches the transition
classes the pipeline counts (`budget_v3.py`, checked cell by cell against the classify stage of
`run_from_tiers_v3.py`). The energy penalizes each class's spread over the three pictures, and the frame
corner and edge pools the same way. Figures and locked cells are unchanged; 44, 63 and 82 cells moved.
Class surplus 193 to 107 (51/26/30): the target under 30 is not met. Frame edge surplus 330 to 258,
corners 15 unchanged: the owl's frame has no D and D is not a background tier for the owl. Tier totals
are not exact (D 285/287/286). Log: `27x38-v3/budgets.txt`.

## v4 to v7: solvability layers on the v2 tiers

All on `27x38-v2`, tray border, quarter rotation, cell 21; full and ink renders each.

- **v4, chip sub-classes** (`pipeline/run_from_tiers_v4.py`, `gen_classes_v10.py`): Lr/Lb/Lo/Lx and
  Mr/Mb/Mc per picture. Shared 0/1/0; T9 stays 2/5 (`ambiguity-v4.md`): sub-classes do not make the
  plain fields solvable.
- **v5, motif layer** (`run_from_tiers_v5.py`, `gen_classes_v11.py`, `motifs/make_motif_maps.py`):
  31% of pieces carry motifs; scene gates pass for the first time but blind recognition halves
  (`evaluation-v5.md`, FINDINGS 36).
- **v6, sparse motifs** (`run_from_tiers_v6.py`, `gen_classes_v12.py`, `motifs/make_motif_maps_v2.py`):
  14% coverage, organic clusters, 2-cell halo on the carrier side, per-piece jitter. Shared 1/1/0,
  gates pass, T9 3/5; blind readers see "top-down maps" (`evaluation-v6.md`, FINDINGS 37). Current best.
- **v7, density gradient** (`run_from_tiers_v7.py`, `motifs/make_motif_maps_v3.py`): placement by
  distance from the figure was not computable (the figure tier merges the hare with its landmass; no
  animal mask in the tiers), and the fallback (carrier halo plus 10/20/30% by distance from any
  non-plain cell) reached only 5.2% coverage. Shared 2/1/0; piece gates pass; scene gate B-C 31.3%.
  Fields read as nearly bare. Negative result; v6 stays the baseline (FINDINGS 38). The counts file
  `27x38-v2/pipeline-out-v7/motif-counts-v7.txt` holds the pool histograms and ASCII distance maps.
- **Standard border with cross-class seams** (`border-check/round2/run-standard`, pipeline-out-v5
  scenes, classes-v11): valid, 0 mismatches, shared 0/1/1, piece and scene gates pass; 68 seams per
  board, 41 to 56 of them joining two classes; 256 flat-sided pieces, 130 inside each picture, 12
  added by padding. Seams are invisible in the render (no cut lines); they would show as straight cuts
  in the physical puzzle. Supersedes the round-1 result (FINDINGS 29).
- **Cut overlay of the standard-border run** (`border-check/round2/run-standard-cuts/`, `--cut-overlay`
  re-rendered from the saved solution): 68 interior flat seams per board; straight runs of 3 or more
  seams: A 1 (one vertical run of 3), B 0, C 0. The seams are scattered as dominoes, L-trominoes and
  2x2 blocks, so the physical grid tell from seams is small. Andro profiles draw as outward bumps.

## v4 draft (27x38-v4-draft)

`python3 make_targets_v4_draft.py` (about 7 min on 4 cores) is a copy of v2 with redrawn animals and
scene cues, following blind-test-v2.md and evaluation-v6.md. The method is unchanged, except that the
annealer may move cells within 2 of a drawn line (SOFT_RADIUS 2), and `~` in a sketch now marks a locked
W cell. Internal lines are bands at least 2 cells wide, because 1-cell strips are anomalies.
- **Owl (B):** slanted ear tufts, 7-wide round eyes with single-cell pupils (dot pieces), a 4-4-2
  pointed M beak, two stepped W wing lines (the W chest read as a mouth, so it was dropped), and legs
  gripping a branch that lies on the snow. The moon disc is behind the head, with a crater band (S).
- **Hare (A):** the dark tier is a hedge band with a crown skyline above it, long shadow stripes across
  a sunlit meadow, and a foreground shadow band. Mist (W) lies beside the hare. The hare has a dark
  ear tip, haunch, shoulder and leg lines (D), a white tail (L) and the dot eye. It is cropped at row 29.
- **Swan (C):** redrawn facing left, with an S neck, an olive M beak, a dot eye, a raised wing bump, a
  pointed tail and an S wing line. It floats in a 2–3-row W water band with a reflection drip.
- **S set:** one 2 × 5 band per picture: starlings (A), moon craters (B), wing line (C).
- **Dots:** per picture, two D-on-L dots (crows; pupils; eye and a duck on a glint) and one D-on-M
  dot (hare eye; bat; duck).
- **Budgets:** counts D/M/W/L/S are 362/271/91/292/10, with a spread of 1 or less. Edge spreads are
  D-M 6, W-L 5 and 4 or less for every other pair; corner spreads are 4 or less. S-L is 14/8 in every
  picture. There are no caps, strips or pinches.
- **Animal masks:** `tiers-X-animal.txt` (A = animal). Each is the figure with its holes (eyes, beak,
  lines), plus the locked lines touching it (hare ear tip, leg line and tail; swan beak). The owl's
  mask excludes the branch and the sky between its legs.
- **Risks:** the annealer moved 121/64/134 cells and roughens the background shapes: the hedge is
  ragged, the owl's moon is a wide cap rather than a round disc, and the swan's moon is scalloped.
  Straight runs are up to 19 (the locked branch), 45° runs in D-L are 37/64/37, and there are 72–83
  junction cells. Not yet blind-tested.

## v4 matching

`make_targets_v4.py` (a copy of v3) drops the frame objective and matches the class surplus that
`budget_v3.py` reports. Figure outlines, chips and water may move one cell; hero cells, the 3x3 around
them and the ear tops are locked; no move may add an anomaly or touch S to D, M or W. Restarts stop on
stall. Result: surplus 193 to 78 (A 42, B 22, C 14), target under 30 not met. Figure cells changed
7/13/15. Tier totals drift (W 36/30/36). The block-move run (`--block`, `27x38-v4-blocks/`) gives 83 and does
not help. Outputs: `27x38-v4/` and `27x38-v4-blocks/`; log: `27x38-v4/budgets.txt`.
