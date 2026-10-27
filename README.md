# metapuzzle

A design toolkit for a "multi-solution jigsaw puzzle": one physical set of printed pieces
that can be rearranged into three distinct images. The pieces are printed once and never
change. Each solution uses every piece exactly once, and the arrangements are chosen so
that few neighboring pairs in one solution are still neighbors in another.

The toolkit generates piece arrangements, procedural artwork (SVG and raster), renders of
all three solutions, and adjacency metrics. The working product is a 27x38 set of 1026
pieces. The original target was 500; the owner has since freed the piece count
(`docs/DECISIONS.md`, 2026-10-27).

**Resuming work? Read [docs/HANDOVER.md](docs/HANDOVER.md) first.** It holds the current
status, the pipeline, the working method and a file map. Then read `docs/DECISIONS.md`,
`docs/FINDINGS.md` and `gallery/README.md`.

## Where we are

Status as of 2026-10-27, 14:30 UTC. Sources are given in each item.

- **Working grid: 27x38 (1026 pieces), tray border.** Adopted 2026-10-27 after experiment
  013 (`docs/DECISIONS.md`). The tray (no flat-edged frame) follows from the value-inversion
  subjects, whose three frames have different tone mixes.
- **Subject set: "Field, Wood and Water"** (`experiments/011-subjects`): a hare at dawn (A),
  an owl at dusk (B) and a swan at midnight (C), in value inversion. Latest blind test
  (`blind-test-v2.md`, 27x38-v2 `run-full`): hare 4/5, owl read as a skull 4/5, swan 3/5;
  distinctiveness 4/5; grid 2 / 2 / 3. In ink the hare falls to 2/5.
- **Uniqueness: from artwork, not connector algebra.** Experiment 012 showed that exact
  minimal mating classes need both board dimensions = 1 (mod 3) with no rotation, and they
  force B and C to be fixed shuffles of A. Uniqueness rests on distinct cuts and distinguishing
  artwork, judged by the visual-ambiguity test (T9), not the false-fit ratio (DECISIONS, 2026-10-27).
- **Motif vocabulary for background pieces.** Chip sub-classes did not make the plain fields
  solvable: T9 scored 2/5 on v2 and v4, with about 70% of pieces interchangeable
  (`docs/FINDINGS.md`, entries 25 and 26). The next layer is legible motifs assigned by
  region: 9 regular motifs and 6 heroes (`docs/design/10-motif-vocabulary.md`).
- **Motif layer, v5 and v6.** Pipeline v5 put motifs on 31% of pieces: the scene gates pass, but
  blind recognition halved (owl 2/5, swan 2/5), so v6 (14% coverage, organic clusters, silhouette
  halo) is in evaluation (`docs/design/10-motif-vocabulary.md`, `experiments/011-subjects/evaluation-v5.md`).
  T9 is still 2/5 across v2, v4 and v5, because plain fields are the hard part; motif pieces are
  placeable against the box image, which shows them faithfully.
- **Owner steers (2026-10-27).** Lines first (ink before the full render). Each image must
  have a unique solution with few wrong local ones. Shared adjacency per pair is below about
  10%, with no transferable cluster larger than 3 pieces; zero is a stretch.
- **Current best.** 011 `27x38-v2/run-full-v6` and `run-ink-v6` (pipeline v6, sparse motifs,
  14% coverage): shared adjacency AB/AC/BC 1/1/0, piece and scene gates pass, T9 3/5
  (`evaluation-v6.md`). Recognition is limited by figure detail and scene cues, not by motifs
  (`docs/FINDINGS.md`, entry 37): blind readers of v6 see "top-down maps".
- **Standard border is feasible again.** Cross-class seams (`docs/engine-spec.md`) seat surplus
  flat-sided pieces in small blocks across classes; the subject set solves with a standard border,
  0 mismatches, shared 0/1/1 (`experiments/011-subjects/border-check/round2/run-standard`). The
  tray stays the default until a side-by-side on the v4 tiers (DECISIONS, 14:30 UTC). The
  `--cut-overlay` render draws piece outlines and reports straight seam runs for that comparison
  (one run of 3 on the standard-border check).
- **Pipeline v7 (motif density gradient) is a negative result:** the tone tiers cannot separate the
  animal from its landmass, and the fallback reached 5.2% coverage. v6 stays the motif baseline;
  the design pass now exports an animal mask (FINDINGS 38).
- **In progress (14:30 UTC).** A design pass (`make_targets_v4_draft.py` -> `27x38-v4-draft/`:
  owl cues, hare background, swan water, internal lines, animal masks) and matcher v4
  (`make_targets_v4.py` -> `27x38-v4/`, figure-edge nudges, surplus under 30).
- **Open items:**
  - **Solvability.** T9 is 2/5 for the plain fields. The v5 motif render needs a full render,
    blind tests and T9 before it counts.
  - **Surplus.** Transition pieces left after equalization still show as stray blocks.
    Class-level matching (v3) cut the class surplus from 193 to 107 (51/26/30); the target of
    under 30 is not met (`experiments/011-subjects/README.md`, FINDINGS 27).
  - **Standard border.** Not achieved and no longer the goal; the tray is the product form.
    Standard-border runs with extra flat pieces fail validation (`011-subjects/border-check`).
    An exact standard frame would need a board such as 28x37 under rotation none (DECISIONS, 2026-10-27).
  - **Connectors (T8).** The 005 v3 solution has one mating class holding 91% of sides and a
    false-fit ratio of 530 (FINDINGS 11). The connector minimum is no longer a gate (DECISIONS, 2026-10-27).

## Pipeline

The current pipeline is in `experiments/011-subjects`. Stage numbers match `docs/HANDOVER.md`, section 2.

1. **Subject tiers.** `make_targets_v4.py` (latest; v2 holds the native drawings, v3 the
   class-level matching) draws tier maps at 27x38 with tokens D, M, L, S (chips) and W (wave
   or cloud). Budgets per tier and per boundary pair come from `budget_v3.py`.
2. **Classify, budgets, equalize, roles.** `pipeline/run_from_tiers_v3.py`. Transitions come
   from the 8-neighbourhood, with the darker tier hosting each boundary. Surplus pieces go by
   a per-pair policy (S edge, figure interior, ground interior).
3. **Chip sub-classes.** `pipeline/run_from_tiers_v4.py` and `gen_classes_v10.py`: Lr, Lb, Lo,
   Lx on light ground and Mr, Mb, Mc on mid ground, each with a per-picture pattern.
4. **Motif classes.** `pipeline/run_from_tiers_v5.py`, `gen_classes_v11.py` (writes
   `classes-v11.json` and `classes-ink-v11.json`) and `motifs/make_motif_maps.py`; v6 (`run_from_tiers_v6.py`,
   `gen_classes_v12.py`, `motifs/make_motif_maps_v2.py`) lowers coverage to 14% with a silhouette halo.
5. **Scenes.** `metapuzzle roles-to-scenes` turns the role grids into three class maps with one common histogram.
6. **Prototype.** `metapuzzle prototype --rotation quarter --border tray --cell 21`, once with the
   ink spec and once with the full spec. Annealing minimizes shared adjacencies, clusters and side mismatches.
7. **Checks** (`docs/EVALUATION.md`). Piece-level gate, `metapuzzle scene-metrics` (difficulty
   indicators), then blind recognition (T1, ink first), grid review (T2) and visual ambiguity (T9).

Origin: the 005 placeholder pipeline (cat, sailboat, tree as tone maps, `experiments/005-hybrid-tones`)
used the same design with `quantize_v5.py` and `make_roles_v5.py`; its steps are in that README.

## Quick start

```bash
pip install -e ".[dev]"
pytest                                  # 627 tests
```

Run these from the repository root. Outputs go to `experiments/**/out/`, which is git-ignored.
Experiment 011 writes into its own folders; `experiments/011-subjects/pipeline/run_from_tiers_v4.py --help`
lists its options. Its defaults write into `27x38-v2/` and overwrite the `-v4` folders there,
so pass a new `--out-dir` before a re-run.

Placeholder example (005), from the repository root:

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

Each prototype run writes `solution.json`, `solution-A/B/C` (PNG and SVG), `solution-pieces.png`,
`triptych.png`, `metrics.txt`, `scene-metrics.txt` and `summary.md`.

## Modules

`src/metapuzzle/`: `board.py`, `pieces.py`, `scene.py`, `roles.py` (role-map solver), `optimize.py`
(annealing), `metrics.py`, `scene_metrics.py`, `grid_metric.py`, `connectors.py`, `textures.py`,
`classes.py`, `spec_tools.py`, `render.py`, `prototype.py`, `texture_demo.py` and `cli.py`
(the `metapuzzle` subcommands: `solve`, `report`, `render`, `scene-metrics`, `prototype`,
`gen-transitions`, `prune-spec`, `roles-to-scenes`, `grid-metric`, `connectors`).

## Documents

- [docs/HANDOVER.md](docs/HANDOVER.md): start here. Status, working method, pipeline and file map.
- [docs/HANDOFF.md](docs/HANDOFF.md): the original concept brief (500 pieces). Its goal and principles hold; its status and piece count are superseded.
- [docs/DECISIONS.md](docs/DECISIONS.md): decision log agreed with the project owner.
- [docs/FINDINGS.md](docs/FINDINGS.md): measured results from the prototypes.
- [docs/IDEAS.md](docs/IDEAS.md): backlog of ideas not yet adopted.
- [docs/EVALUATION.md](docs/EVALUATION.md): gates and the blind, grid and uniqueness tests.
- [docs/engine-spec.md](docs/engine-spec.md): interface spec for the arrangement engine.
- [docs/design/](docs/design/): design notes 01 to 10 and the scene and budget files.
- [docs/reference/](docs/reference/) and [docs/image-prompts.md](docs/image-prompts.md): reference notes and the image-model prompts.
- [gallery/README.md](gallery/README.md): at-a-glance table of committed prototype renders.

## Experiments

One folder per experiment under `experiments/`, each with a README (003 has a stub).

- **001 adjacency-baseline**: without class maps, zero shared adjacencies at every board, border and rotation mode.
- **002 direction-a**: first 8x10 render (Dapple Mosaic). Quarter rotation gives 4/5/4 shared; 66 to 71% of cells keep their class; distinctiveness 2/5. Retired.
- **003 scene-strategies**: `fill.py` fills intent files into class maps. Inversion passes the scene gates; skyline and frames fail. Metrics only.
- **004 density-fields**: six rank-quantized tone classes. Quarter rotation gives 0/0/0 shared and distinctiveness 4/5; the grid is fully visible (5/5).
- **005 hybrid-tones**: the carry-forward grammar. 0/0/0 shared at 20x25. At v5 the tree is recognized 5/5, the boat partly, and the cat is never named. Budgets and equalizers (v5, v5eq2, v6) follow.
- **006 direction-b**: Garden Terrazzo. Passes the scene gates but scores distinctiveness 2/5, no subject recognized. Retired.
- **007 solver-limits**: residual shared adjacency is a constraint limit, not a search limit.
- **008 mixed-frames**: 480 pieces on 20x24, 30x16 and 40x12 boards. Round 1 invalid; round 2 valid with 0/0/0 (quarter) and 2/0/0 (none). Scene gates fail; not evaluated.
- **009 grid-metric-calibration**: the automatic grid score does not reproduce the human ranking. Not used as a gate.
- **010 connector-classes**: current solutions are far from minimal mating classes (largest class 46 to 91% of sides). The connector minimum is no longer a gate.
- **011 subjects**: "Field, Wood and Water" (hare, owl, swan) in value inversion on a tray border with quarter rotation. The 27x38-v2 renders have shared 0/0/1 (v2) and 1/1/0 (v6); T9 is 2/5 on v2, v4 and v5 and 3/5 on v6.
- **012 constructive-placements**: algebraic minimal mating classes (K(3,3), K4) and SAT searches. Exact classes need both dimensions = 1 (mod 3) with no rotation and force B and C to be shuffles of A.
- **013 scale**: the 005 pipeline at 500, 750, 1026 and 1536 pieces. Recognition improves from 750 up, so 27x38 became the working grid. A blind test at 27x38 names the boat 5/5 but not the cat.

## Status

The piece-level gate passes for every 27x38 render. The scene-level gates fail for every
render up to v4, by design (difficulty indicators, DECISIONS 2026-10-26); the v5 and v6
renders pass them. Evaluated so far: T1 on 27x38 v1, v2, v5 and v6 (full and ink), grid
reviews on v2, and T9 on v2, v4, v5 and v6. T8 fails on every run measured so far, and the
grid metric is not calibrated (009). Next milestone: v4 tiers (design pass plus matcher) through
pipeline v6 or v7, blind tests passing for all three animals, surplus under 30, T9 at least 3/5.
