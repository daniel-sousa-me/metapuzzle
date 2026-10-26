# metapuzzle

A design toolkit for a "multi-solution jigsaw puzzle": one physical set of 500
printed pieces that can be rearranged into three distinct images. The pieces are
printed once and never change. Each solution uses every piece exactly once, and
the arrangements are chosen so that almost no pair of neighboring pieces in one
solution is still a neighboring pair in another.

The toolkit generates piece arrangements, procedurally drawn artwork (SVG and
raster), rendered images of all three solutions, and adjacency metrics. Work
starts at roughly 60 to 100 pieces and scales toward 500.

## Pipeline

1. **Design brief** (`docs/design/`): visual grammar, piece classes and the three scenes.
2. **Class spec** (`experiments/002-direction-a/classes.json`): texture layers and rotations per piece class.
3. **Scene files** (`docs/design/scenes-8x10.txt`): three grids of class codes with identical class histograms.
4. **`metapuzzle prototype`**: pieces come from scene A's cells; annealing places them on all three boards to minimize shared adjacencies, clusters and side mismatches.
5. **Render**: each piece is drawn once from the class spec and placed three times, once per solution.
6. **Outputs**: solution JSON, piece and scene metrics, A/B/C images, triptychs, and a summary.

## Quick start

```bash
pip install -e ".[dev]"
pytest
metapuzzle prototype --scenes docs/design/scenes-8x10.txt \
  --classes experiments/002-direction-a/classes.json \
  --out experiments/002-direction-a/run-none \
  --sizes 8x10,8x10,8x10 --border standard --rotation none \
  --seed 0 --iters 300000 --cell 48
```

That command rewrites the committed `run-none` directory; pass another `--out` to compare runs. Outputs:

- `solution.json`: the three placements (piece to slot and rotation) and validity.
- `metrics.txt`: piece-level shared adjacencies and clusters per solution pair.
- `scene-metrics.txt`: class carry-over between the three class maps.
- `solution-A.png`, `solution-B.png`, `solution-C.png` (plus `.svg`): the three solutions.
- `solution-pieces.png`: the piece sheet, one artwork per piece.
- `triptych.png`: A, B and C side by side.
- `grid-faint/` and `triptych-grid.png`: the same renders with faint cell outlines.
- `summary.md`: parameters, both metric reports and the file list.

`experiments/**/out/` is git-ignored; `gallery/` holds renders meant to be committed.

## Modules

`src/metapuzzle/`:

- `board.py`: square-lattice board model, slots, neighborhoods, borders and side mating.
- `pieces.py`: piece inventory with shape type, side profiles and allowed rotations.
- `scene.py`: parses and validates class-map scene files and derives the piece inventory.
- `optimize.py`: simulated-annealing solver for three placements.
- `metrics.py`: piece-level shared adjacencies, clusters, familiarity and solution reports.
- `scene_metrics.py`: class carry-over between class maps.
- `textures.py`: seeded procedural texture primitives as SVG fragments.
- `classes.py`: data-driven piece drawer that turns a class spec into texture layers.
- `render.py`: SVG and PNG rendering of solutions and piece sheets.
- `prototype.py`: end-to-end run from scenes to solution, metrics, renders and summary.
- `cli.py`: the `metapuzzle` subcommands `solve`, `report`, `render`, `scene-metrics` and `prototype`.

## Metrics

**Piece-level shared adjacencies.** Two pieces are neighbors in a solution when their slots touch on that solution's board, flat seams included. A shared adjacency is a pair of pieces that are neighbors in both solutions of a pair (A-B, A-C or B-C). Per pair the report gives the count, its fraction of all adjacencies, the clusters of three or more shared pieces, and per-piece familiarity. The targets in `docs/HANDOFF.md` section 2.3 are zero shared adjacencies as a stretch goal, under 5% per solution pair as the acceptable initial target, and no large transferable clusters.

**Scene-level class carry-over.** Pieces of one class look the same, so a region can stay visually assembled across two solutions even with no shared piece pairs, as long as the class layout matches. `scene_metrics` compares the class maps directly. Per pair it reports the same-position overlap (cells with the same class at the same row and column), window reuse for 1x2, 2x1, 2x2 and 3x3 windows (plain and rotated), and the largest transferable blob (the biggest single-class region of A that fits in B by translation). Low carry-over is a separate goal from piece-level overlap, and it is the harder one here.

## Documents

- [docs/HANDOFF.md](docs/HANDOFF.md): project goal, core principles and open questions.
- [docs/DECISIONS.md](docs/DECISIONS.md): decision log agreed with the project owner.
- [docs/IDEAS.md](docs/IDEAS.md): backlog of ideas not yet adopted.
- [docs/engine-spec.md](docs/engine-spec.md): interface spec for the arrangement engine.
- [docs/design/](docs/design/): design notes 01 to 06 and the 8x10 scene file.

## Status

Early prototyping. Experiment 002 (`experiments/002-direction-a/run-none/`) is the first end-to-end render: 80 pieces on three 8x10 boards, no rotation, seed 0. Its piece-level shared adjacencies are 7.8% to 10.6% per pair, above the 5% initial target. Between 66% and 71% of cells keep their class at the same position in each pair, which is the problem the different-frame variants in `docs/design/06-aspect-ratio-variants.md` are meant to address.
