# Experiment 006: Direction B (Garden Terrazzo), first render

## Goal

First render of design direction B, "Garden Terrazzo": 14 non-directional piece classes (`docs/design/alt-b/02-piece-classes.md`) fill three 8x10 scenes: A The Sunflower (radial), B Sunset Bay (bands), C Koi Pond (top-down). It tests the gates and recognisability.

**Result:** passes the scene gates (9 to 14% same position) and the piece gate at quarter rotation (1/0/0), but distinctiveness is 2/5 and no subject is named. Retired.

## Setup

- Scenes: `docs/design/alt-b/scenes-8x10-b.txt`. Classes: `classes.json` (see `NOTES.md`).
- Runs: `run-none/` and `run-quarter/`, seed 0, 300000 iterations, cell 48. They differ only in rotation. `summary.md` records parameters, not the command line.
- Scene gates: `metapuzzle scene-metrics FILE`. Scoring: `docs/EVALUATION.md`.
- Evaluation: `blind-test-1.md` (T1), `grid-visibility-1.md` (T2).

## Results

Triptych impression (`run-quarter/triptych.png`): one palette across three layouts, with C reading as a quilt.

**Piece-level shared adjacencies** (gate: under 5% per pair)

| Pair | run-none | run-quarter |
|---|---|---|
| AB | 7 (4.93%) | 1 (0.70%) |
| AC | 2 (1.41%) | 0 |
| BC | 4 (2.82%) | 0 |

Largest cluster: 2 in both.

**Scene-level carry-over** (from the scene file, same in both runs)

| Pair | Same position (under 25%) | 2x2 reuse (under 30%) | Transferable blob (under 10%) |
|---|---|---|---|
| AB | 11 (13.8%) | 0.27 | 6 cells (7.5%) |
| AC | 7 (8.8%) | 0.03 | 5 cells (6.2%) |
| BC | 7 (8.8%) | 0.06 | 4 cells (5.0%) |

**Scorecard**

| Check | Gate | Value | Result |
|---|---|---|---|
| T1 subjects | 3+ confidence | none named | Fail |
| T1 distinctiveness | 4+ | 2 | Fail |
| T1 tile grid | 2 or lower | A 3, B 4, C 5 | Fail |
| T2 verdict | 2 or lower | A 3, C 5 | Fail |
| T2 invisible lines | 12 of 16 | 15-20% (solution A) | Fail |

## Interpretation

- Scene gates pass for the first time.
- Quarter rotation brings piece-level sharing to 1/0/0, down from 7/2/4. Without rotation, AB clears the 5% gate by a hair.
- The blind evaluator saw "variations of one picture" (distinctiveness 2/5) and named no subject.
- The shared palette and motifs dominate perception, so layout differences barely register.
- Subjects need bold macro silhouettes. At 8x10, a sunflower, a bay and a pond cannot read; the pond became a patchwork.
- Grid visibility is worse than direction A (15-20% invisible, against 44%). Every texture field ends on a piece edge; the speckle binder hides same-texture seams, not colour steps.
- Keep from B: context-dependent class readings, role maps as the authored artefact, and distinct layouts.

## Next

- Hybrid tone-field experiment (005).
- Mixed frames (008).
- Generated transitions for every class pair.
