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
