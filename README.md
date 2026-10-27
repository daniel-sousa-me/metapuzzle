# metapuzzle

A design toolkit for a "multi-solution jigsaw puzzle": one physical set of 500
printed pieces that can be rearranged into three distinct images. The pieces are
printed once and never change. Each solution uses every piece exactly once, and
the arrangements are chosen so that almost no pair of neighboring pieces in one
solution is still a neighboring pair in another.

The toolkit generates piece arrangements, procedurally drawn artwork (SVG and
raster), rendered images of all three solutions, and adjacency metrics. Work
starts at roughly 60 to 100 pieces and scales toward 500.

## Where we are

- **Grammar.** The carry-forward grammar is the hybrid tone-field. Each subject is a bold three-tier tone map (dark, mid, light), and every tier boundary lies inside a marching-tile transition piece, so no colour step lands on a cut.
- **Texture.** Scatter (S) and wave (W) tiers and motif pieces carry the texture inside a tier. The frame cells are still plain (an engine limit).
- **Lines first.** Ink mode (black contours on white) is the first render of every scene, used to judge shape and piece mapping before fills.
- **Role maps.** Each subject is authored as a role grid; the class solver (`roles-to-scenes`) gives the three class maps one histogram and matching border counts.
- **Boundary budgets.** Each tier pair needs as many transition pieces as the subject has boundary edges of that pair. The budgets are a shared inventory across the three subjects.
- **Connectors.** Each side should fall into a minimal mating class (3 tabs and 3 blanks, or 4 sides when symmetric). This is not met yet; see Status.
- **Owner steers (2026-10-27).** Lines first. Each image must have a unique solution with few wrong local ones. Piece-level shared adjacency is relaxed to below 10% per pair, with no transferable cluster larger than 3 pieces; zero is a stretch.
- **Best result.** Experiment 005, carry-forward run (`run-quarter`, 20x25 at 500 pieces): 0/0/0 shared adjacencies, distinctiveness 4/5, tree recognized blind. The cat and boat were not named.

## Pipeline

1. **Subject tone maps** (`experiments/005-hybrid-tones/make_targets.py`): cat, sailboat and tree as tone maps; each cell is tiered D, M or L by fixed thresholds.
2. **Quantize** (`quantize_v5.py`): marching-tile transition codes per cell and boundary budgets per tone pair (`boundary-budgets-v5.txt`).
3. **Roles** (`make_roles_v5.py`): role grids for the three subjects. Surplus transition pieces go to interior cells next to their own boundary.
4. **Scenes** (`metapuzzle roles-to-scenes`): the class solver turns the role grids into three class maps with one common histogram.
5. **Prototype** (`metapuzzle prototype`): run once with the ink spec and once with the full spec. Annealing places the pieces on three boards to minimize shared adjacencies, clusters and side mismatches.
6. **Checks**, as set out in `docs/EVALUATION.md`: `metapuzzle scene-metrics` (difficulty indicators), `metapuzzle connectors` (T8 mechanical uniqueness) and `metapuzzle grid-metric` (automatic grid score, not yet a gate). Then the blind recognition test (T1), the grid review (T2) and the visual ambiguity check (T9).

## Quick start

```bash
pip install -e ".[dev]"
pytest                                  # 522 tests, about 50 s
```

Run these from the repository root. Outputs go to `experiments/**/out/`, which is git-ignored.

```bash
# 1. Prototype, 005 v3 scenes, ink spec (then repeat with --classes experiments/005-hybrid-tones/classes.json
#    and --out experiments/005-hybrid-tones/out/full-v3 for the full spec). Exit 0 when valid.
metapuzzle prototype --scenes experiments/005-hybrid-tones/scenes-v3.txt \
  --classes experiments/005-hybrid-tones/classes-ink.json \
  --out experiments/005-hybrid-tones/out/ink-v3 \
  --sizes 20x25,20x25,20x25 --border standard --rotation quarter \
  --seed 0 --iters 300000 --cell 32

# 2. Scene gates on the three class maps. Exit 3 when a gate fails, which it does for 005 v3.
metapuzzle scene-metrics experiments/005-hybrid-tones/scenes-v3.txt

# 3. Mating classes and false fits of the committed 005 v3 solution. Exit 2 when some contacts do not mate.
metapuzzle connectors experiments/005-hybrid-tones/run-quarter-v3/solution.json
```

Each prototype run writes `solution.json`, `solution-A/B/C` (PNG and SVG), `solution-pieces.png`, `triptych.png`, `metrics.txt`, `scene-metrics.txt` and `summary.md`.

## Modules

`src/metapuzzle/`:

- `board.py`: square-lattice board model, slots, neighborhoods, borders and side mating.
- `pieces.py`: piece inventory with shape type, side profiles and allowed rotations.
- `scene.py`: parses and validates class-map scene files and derives the piece inventory.
- `roles.py`: role-map solver that picks concrete classes for a grid of roles.
- `optimize.py`: simulated-annealing solver for three placements.
- `metrics.py`: piece-level shared adjacencies, clusters, familiarity and solution reports.
- `scene_metrics.py`: class carry-over between class maps and the scene gates.
- `grid_metric.py`: automatic grid visibility score from the solution PNGs.
- `connectors.py`: side-mating graph, mating classes and false fits of a solution.
- `textures.py`: seeded procedural texture primitives as SVG fragments.
- `classes.py`: data-driven piece drawer that turns a class spec into texture layers.
- `spec_tools.py`: generates transition classes for a class spec and prunes a spec to the classes scenes use.
- `render.py`: SVG and PNG rendering of solutions and piece sheets.
- `prototype.py`: end-to-end run from class maps and a class spec to a solved, rendered and summarized set.
- `cli.py`: the `metapuzzle` subcommands: `solve`, `report`, `render`, `scene-metrics`, `prototype`, `gen-transitions`, `prune-spec`, `roles-to-scenes`, `grid-metric` and `connectors`.

## Documents

- [docs/HANDOFF.md](docs/HANDOFF.md): project goal, core principles and open questions.
- [docs/DECISIONS.md](docs/DECISIONS.md): decision log agreed with the project owner.
- [docs/FINDINGS.md](docs/FINDINGS.md): measured results from the prototypes.
- [docs/IDEAS.md](docs/IDEAS.md): backlog of ideas not yet adopted.
- [docs/EVALUATION.md](docs/EVALUATION.md): gates and the blind, grid and uniqueness tests for every run.
- [docs/engine-spec.md](docs/engine-spec.md): interface spec for the arrangement engine.
- [docs/design/](docs/design/): design notes 01 to 07 and the 8x10 scene file.
- [docs/reference/](docs/reference/): reference notes and returned image-model references.
- [docs/image-prompts.md](docs/image-prompts.md): prompts sent for the occasional image-model reference channel.
- [gallery/README.md](gallery/README.md): at-a-glance table of committed prototype renders.

## Experiments

One folder per experiment under `experiments/`, each with a README unless noted.

- **001 adjacency-baseline**: without class maps, zero shared adjacencies at every board, border and rotation mode, in under a second.
- **002 direction-a**: first 8x10 render (Dapple Mosaic). Quarter rotation gives 4/5/4 shared, but 66 to 71% of cells keep their class in place and distinctiveness is 2/5. Retired.
- **003 scene-strategies**: `fill.py` fills intent files (frames, inversion, skyline) into class maps with one histogram. Scene metrics only; no README.
- **004 density-fields**: six rank-quantized tone classes. Quarter rotation gives 0/0/0 shared and distinctiveness 4/5, but the grid is fully visible (5/5).
- **005 hybrid-tones**: the current grammar. 0/0/0 shared at 20x25 with the tree recognized; ink-mode diagnostic (`run-ink-v3`) and boundary budgets (v5) follow.
- **006 direction-b**: Garden Terrazzo. Passes the scene gates (9 to 14% same-position) but scores distinctiveness 2/5 with no subject recognized. Retired.
- **007 solver-limits**: residual shared adjacency is a constraint limit, not a search limit. About seven times the iterations and five seeds change nothing (37 total with no rotation, 13 with quarter).
- **008 mixed-frames**: 480 pieces on 20x24, 30x16 and 40x12 boards. Round-2 runs are valid with 0/0/0 (quarter) and 2/0/0 (none); scene gates fail; not yet evaluated.
- **009 grid-metric-calibration**: the automatic grid score does not reproduce the human ranking (it puts 004 last, humans first). Not used as a gate.
- **010 connector-classes**: current solutions are far from minimal mating classes. The largest class holds 46 to 91% of sides, with a false-fit ratio of 60 to 530.
- **011 subjects**: hare, owl and whale tone maps on a tray border with quarter rotation. Valid, 0/0/0 shared at 20x25. No README.

## Status

Early prototyping on the tone-field grammar. The piece-level gate passes at about 500 pieces (004, 005 v3 and 011; 008 round 2 at 480), and the scene gates fail by design, since they are difficulty indicators only. Open items:

- **Connectors (T8) fail.** The 005 v3 solution has one mating class holding 91% of sides, with a false-fit ratio of 530. The solver needs an objective that closes partner sets into minimal blocks.
- **Subjects.** The cat and boat were not named in the first blind test. The v2 and v3 subject fixes and the v5 boundary budgets have no blind test yet, and there is no `scenes-v5.txt`.
- **Engine.** `validate_scenes` rejects transition suffixes on frame cells, so frame boundaries are coded plain.
- **Evaluation.** T9 (visual ambiguity) is not yet recorded for any run, and the grid metric is not calibrated.
