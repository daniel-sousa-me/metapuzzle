# Arrangement engine: interface spec

Scope: square lattice only (DECISIONS). Rotation is `none` first, `quarter` second. Pure Python 3.10+ and numpy, type hints, brief docstrings. Package `metapuzzle` under `src/`.

Conventions
- Sides: N=0, E=1, S=2, W=3. Corners: NW=0, NE=1, SE=2, SW=3. Rotation is clockwise degrees in {0, 90, 180, 270}.
- Slot id = `y * cols + x` (row-major, y=0 is the top row). Piece ids are ints.
- A **placement** is `dict[int, tuple[int, int]]`: `piece_id -> (slot_id, rotation_degrees)`, a bijection onto the slots of **that solution's board**.
- A solution set is exactly three placements A, B, C (indices 0, 1, 2) on **three boards** with equal slot counts, so all three use the same pieces. The boards may differ in shape (mixed frames: 20x24, 30x16, 40x12 for 480 pieces). Pairs: AB, AC, BC.

## Side profiles and validity (the general model)

Every piece has four side profiles `sides = (N, E, S, W)` in its upright frame, from `tab`, `blank`, `flat`, `andro`, `wild`.
- Mating (`board.mates`): `flat~flat`; `tab~blank`; `andro~andro`; `wild` mates with any non-flat profile (placeholder for keyed or custom connectors, an extension point).
- Rotated by `r` degrees (q = r/90 quarter turns), the profile facing board direction `d` is `sides[(d - q) % 4]`.
- **Slot-level fit** (`Board.rotations_for`): on a `standard` board every boundary side of the slot must present `flat`; on a `tray` board nothing is required at the boundary. Rotation must be in the piece's `allowed_rotations` (and equal to the cell's forced rotation, if any), and the class must match the class-map cell.
- **Pairwise validity**: for every two touching slots, the two facing sides must mate. A solution is **valid** when every piece fits its slot and no touching pair fails to mate. Flat sides inside the picture are therefore legal only against another flat side (a seam). Corner/edge/interior is a label, not the rule.
- `Slot.kind/home/type` (corner NW.., edge N.., interior) are still provided for generators, class-map border checks and reports.

Default connectors (`pieces.default_sides`): rotation none uses the asymmetric interior pattern blank N/W, tab S/E with `flat` replacing the sides that face the border (interior pieces mate with every neighbor); rotation quarter uses `andro` on all non-flat sides.

## Mixed frames: one board per solution

Each solution has its own board, and the boards may have different frames. The inventory is sized to the largest perimeter any board needs. A picture with a smaller frame therefore receives surplus flat-sided pieces in its interior, as seams.

- **Inventory** (`pieces.inventory_layout`): 4 corner pieces; edge pieces numbering the largest border need of any board (per side without rotation, pooled with rotation); `extra_flat_pieces` more flat edge pieces; the rest interior.
- **Seams.** A seam is one flat-flat contact inside a picture. Surplus edge pieces pair into **dominoes** (one seam). A surplus corner piece sits in an **L-tromino**: the corner piece plus two edge pieces (two seams). Two surplus corners can share a **2x2 block** (corner, corner, edge, edge: four seams), and four corners fill one (four seams). Without rotation the two flats of a domino must be opposite (N with S, W with E). With rotation an even count pairs freely. The pieces of a group need not share a class (see Cross-class seams below).
- **Constructed layouts.** `pieces.build_valid_layout(board, pieces, cls_at=None, forced_at=None, rng=None, tries=25)` builds one valid placement per board, seams included: exact-fit pieces on frame slots (a maximum matching on boundary sides), then corner-plus-two-edges and edge pairs on interior slots, then plain pieces by class. It returns `(slot_of, rotation_of, groups)`, or `None` after `tries` attempts (`diag={}` then receives `unplaced`, the pieces the best attempt could not seat). The seam groups come from `SeamSpace.plan`. `pieces.group_placements(board, parts, cls_at=None, forced_at=None)` lists every interior placement of a seam group (any shape above; each part shows exactly the flats that face another part of the group; the result is `(slot, rotation)` per part, in `parts` order).
- **Seam-aware mode in `solve`.** Used when some board has more flat-sided pieces than frame slots (standard border, no `distinct_corner_orders`). The start is built by `build_valid_layout`, and the moves keep it valid:
  - single swaps (both pieces fit each other's slot exactly);
  - group moves: a seam group goes to any of its placements (rotated when its pieces rotate), and the displaced pieces go to the vacated slots, one by one or as a whole group;
  - swaps of two groups.

  Displaced plain pieces go to the vacated slots they fit (matched by class, so groups whose pieces sit on cells of different classes stay movable).
- **Evidence.** `experiments/008-mixed-frames/README.md`, Round 2. Quarter rotation: valid, shared 0/0/0, 127 flat-sided pieces, 15 to 23 seams per board. Rotation none with 64 extra flat pieces: valid, shared 2/0/0, 245 flat-sided pieces. Without rotation, 137 to 161 interior pieces are flat-sided, so the seams will show in print; quarter is the better choice for those maps.

## Cross-class seams: frames with different class mixes

A standard (flat-edged) border needs a flat-sided piece of the right class at every frame cell, and the three pictures' frames can use different class mixes. A seam pair is two flat-sided pieces at adjacent interior cells with their flat sides touching. The scene prescribes the class of each cell, so the two partners only have to match the classes of those two cells, not each other (and, under forced rotations, the flat side must land on the shared edge: the cell's forced rotation fixes which home a piece needs for a given direction).

- **Derivation** (`pieces_from_scenes(..., strict_border=False)`, the default). Frame class counts are no longer required to agree (`strict_border=True` and CLI `--strict-border` restore the old check). The flat-sided pool of each class is sized to the largest frame need of that class over the three maps (per home with forced rotations; see Class maps). In map `k` the surplus of class `c` is the pool minus map `k`'s own frame need; those pieces become seam pieces on interior cells of class `c` of map `k`, each paired with any other surplus flat piece on an adjacent interior cell, whatever its class. After the existing padding, the derivation checks every map with the seam planner. If some surplus piece cannot be seated (a class with an odd surplus and no neighbouring class with surplus, a corner without two usable neighbours), it adds flat edge pieces of classes that border the unseated pieces (a single piece, else a pair), scored by the pieces left unseated summed over the three maps, until all three maps seat their surplus or no candidate helps. Failure raises `SceneError` when the frames differ (it stays silent, as before, when they agree).
- **Planner** (`pieces.SeamSpace.plan`). For one map it lists every group placement on interior cells (shapes: domino, L-tromino, corner pair plus edge pair, four corners) and runs an ejection-chain search: an unseated piece takes a placement whose other positions are filled from unseated pieces or from the groups it displaces (any piece of a fitting class and flat count may be taken, displacing its group); displaced pieces become unseated; a worsening move is accepted with probability exp(-cost/0.7). It returns the groups or the unseated pieces of the best state. `build_valid_layout` uses it for the leftover pieces after the frame matching.
- **Report.** `scene.seam_report(boards, maps, pieces)` gives, per map, the flat-sided pieces inside the picture, the seams, how many join different classes (`cross_class`) and the group sizes. `prototype.seam_counts(solution)` gives the same for a solved board; the prototype `summary.md` lists "interior seams" and "cross-class seams" per board.
- **Limits.** Groups have at most four pieces and only the shapes above (no chains of three edge pieces, no 3x2 blocks). Every non-flat profile must mate with every other (the seam-aware solver mode assumes it). The planner is a heuristic: a feasible scene can be reported infeasible, and the padding search is greedy, so it can add more flat pieces than the minimum. A class needs spare cells to hold padding pieces (pool at most the class's cell count). Without rotation the pairs must be opposite flats at adjacent cells, so cross-class partners are rarer. Groups of cross-class pieces have fewer placements than same-class groups (they live on class boundaries), which limits how far the solver can move them and can leave a few shared adjacencies.

## Class maps: derivation (`scene.pieces_from_scenes`)

`pieces_from_scenes(boards, maps, extra_flat_pieces=0, free_corners=False, allowed_rotations=None, strict_border=False)` returns one piece per cell of map A, carrying A's class. Maps B and C supply the needs that size the border pool.

1. **Per-class border matching.** Each border cell of class `c`, in each of the three maps, needs a piece of class `c` whose flat side covers that cell at one of the class's allowed rotations (a forced cell: at its forced rotation). A piece with canonical flat home `h` shows that flat on side `(h + r/90) mod 4` when turned by `r`, so a cell on side `key` needs `h = (key - r/90) mod 4`. Corners use the same rule on corner indices, with the two flats turned together.
2. **Directional vs rotatable.** A directional class (allowed rotations `{0}`) and a forced cell admit one home. A rotatable class admits all four homes, so its border cells pool. Each map is matched class by class against one physical pool: the pool grows to the most any map needs per home, and rotatable needs take what is left. Leftover pieces and the plain interior pieces fill the rest of A's cells of the class. When a class has too few cells, `SceneError` names the class, map, cell and side.
3. **Seam padding.** Flat edge pieces are added, with classes chosen to suit all three maps (a flow over the class pairs that touch in each map), until each map's leftover flat pieces can pair up: opposite flats without rotation, an even count with rotation. Automatic padding applies only when every class is rotation-free or every class is fully rotatable. The count is conservative about forced rotations (it ignores the turns of leftover pieces), and `_layouts_exist` confirms each map afterwards.
4. **Extra flat pieces.** `extra_flat_pieces` adds that many flat edge pieces on top, spread over the classes: without rotation as N/S then W/E pairs (opposite-side pairs); an odd count gets one more partner.
5. **Defaults.** Allowed rotations: all four in quarter mode, `{0}` otherwise. With `free_corners`, corners get all four, and their inner sides are `wild`.
6. **Histogram and border checks** (`validate_scenes`). Three maps, each the shape of its board, identical class histograms. Border class counts per side (rotation none) or pooled (quarter, free corners) must match only when all boards have the same shape or `strict_border=True`. `pieces_from_scenes` relaxes this by default (frame mixes may differ, seams absorb the difference, see above) and checks it only when called with `strict_border=True` and no extras.

## Forced rotations and orientation suffixes

Tokens: `cls` (rotation unconstrained unless forced), `cls@R` (R in 0, 90, 180, 270), and `cls@*` (the cell is free).

- **Class-wide rule across the three maps** (`load_scenes`, `parse_text`). If ANY token of a class in ANY map has an explicit suffix (`@0` counts), every token of that class is forced across the set: bare and `@0` force rotation 0, `@R` forces R, and `@*` frees that one cell. A class with no suffix anywhere stays unconstrained and may rotate in quarter mode.
- **Validation.** A nonzero suffix needs rotation `quarter`, on any cell, frame cells included; otherwise `SceneError`. A forced 0 is legal on any cell. In rotation none, a forced-0 frame cell is matched by side.
- **Representation.** `ClassMap.rot`: plain 0 = unconstrained; `FORCED_ZERO` = forced 0 (truthy and equal to 0); 90, 180, 270 = forced. `rot or None` gives the solver its constraint. `ClassMap.forced` is the set of orientation-forced classes, and `tokens()` writes `@0` and `@*`, so the text round-trips.
- **Frame cells with canonical flat homes.** A forced frame cell on side `key` with rotation `R` takes a piece whose home is `h = (key - R/90) mod 4` (corners: the same rule on corner indices), so its flat lands on its own edge. Matching runs per class and per home across the three maps: one-home needs first, rotatable needs by augmenting paths. A pool that would exceed the class's cells raises `SceneError` naming the class, map, cell and side.
- **Roles pass-through** (`roles.py`). A suffix on a role token is copied unchanged to the cell's class token in every map (`dark_edge_m@90` becomes `DM@90`); plain roles emit none.

## Roles (`roles.py`)

- **Input.** A roles file in scene layout, with role names as tokens. A roles spec (JSON) lists, per role, the allowed classes with optional weights, plus optional `fixed` counts (per class) and `target_counts` (the whole histogram). Without `target_counts`, the solver picks a histogram that all three maps can realise.
- **Output.** `assign_classes(role_maps, roles_spec, rotation="none", seed=0, iters=20000, restarts=1, pref_weight=0.25, max_same_neighbour=None, adjacency_weight=1.0)` returns three class maps that pass `validate_scenes`: one histogram; with rotation none, identical border counts per side and the same corner class per slot; with quarter, edges and corners pooled. `metapuzzle roles-to-scenes` wraps it.
- **Method.** A skeleton (a class multiset per group, the same in all three maps) is annealed on a violation count, with Hall's condition checked by max-flow. A second anneal swaps classes inside a group, which keeps the groups and the histogram exact.

## Solver options (`optimize.solve`)

```python
solve(boards, pieces, class_maps=None, seed=0, iters=None, cluster_weight=0.25,
      mismatch_weight=1.5, distinct_corner_orders=False,
      mating_weight=0.0, max_shared_fraction=None, mating_hops=3) -> Solution
```

- **Mating penalty** (`mating_weight` > 0; `connectors.MatingPenalty(m, hops)`). For every non-flat side `s`, add `max(0, |B(s)| - m)`, where `B(s)` is the set of sides within `mating_hops` steps of `s` in the side-mating graph (nodes are `piece * 4 + upright side`; one count per contact, so a pair touching in two solutions has multiplicity two). `m = 6` (K(3,3) for tab/blank), or `m = 4` (K4) when every non-flat side is andro (`connectors.target_block_size`). The default `mating_hops=3` sees degree-2 chains that two hops miss. The graph is updated per move through `propose`, `commit` and `rollback`; only sides within `hops - 1` of a changed side are re-evaluated.
- **Off by default.** `mating_weight=0.0` leaves the solver as it was. CLI: `--mating-weight W` on `solve` and `prototype` (0 off; 1 on). `mating_hops` is a function argument only.
- **Max shared fraction guard** (`max_shared_fraction`). A move is rejected when it would raise a pair's shared adjacencies above `floor(F * min(adjacencies of the two boards))`. The default F is 0.10 when mating is on and the guard is off otherwise, unless an explicit value is passed. CLI: `--max-shared-fraction F`.
- **Meta.** `meta` adds `mating_penalty` (None when off), `mating_weight` and `max_shared_fraction`.

## Connectors (`connectors.py`)

- `contacts(solution)` builds the side-mating graph: a node is a non-flat piece side, and every contact between two non-flat sides in any solution is an edge. Flat contacts are seams, not nodes.
- `mating_classes(solution)` returns the connected components, largest first. The smallest possible class is 6 sides (K(3,3), tab/blank) or 4 (K4, andro).
- `false_fit_count(solution)`: for each class, possible tab-blank pairs minus distinct actual contacts. `ratio = total / intended contacts`, where intended contacts are 3 times the internal adjacencies.
- `class_summary(solution)` and `format_summary` give the headline numbers. `mating_penalty(solution, m=None, hops=3)` recomputes the solver's penalty for a finished solution (0 when every block is at most m).

## Metrics, gates and checks

- **Piece level** (`metrics.report`). Shared adjacencies per pair (any contact, seams included), clusters of 3 or more pieces, familiarity, corner orders, cluster penalty. The code gate (`metrics.PIECE_GATES`) is shared fraction below 5% per pair and largest cluster below 4 pieces.
- **Scene level** (`scene_metrics.py`, `metapuzzle scene-metrics`). Same-position overlap, 2x2 window reuse (plain and rotated) and transferable blobs. These are difficulty indicators, not hard gates; they fail by design for current runs.
- **Prototype `summary.md`.** A `Gates` section gives the piece and scene lines, with failures listed as `piece: ...` or `scene: ...`. Gate failures do not change `valid`. A `Connectors` section gives the mating classes and the false-fit ratio.
- **Full protocol.** `docs/EVALUATION.md`: the automatic gates (section 2), the blind recognition test (T1), the grid review (T2), the carry-over test (T7), mechanical uniqueness (T8, `metapuzzle connectors`) and visual ambiguity (T9).

## board.py

```python
ROTATION_DEGREES = (0, 90, 180, 270); SIDES; CORNERS; SIDE_DELTA; PROFILES; mates(a, b) -> bool

@dataclass(frozen=True)
class Slot: id, x, y, kind, home, type, neighbors (4-neighborhood ids), boundary_sides (side indices)

@dataclass
class Board:
    cols, rows, border ("standard"|"tray"), rotation ("none"|"quarter"), slots
    n_slots; rotations; adjacencies (slot pairs a<b); n_adjacencies; slot_at(x, y)
    kind_counts() -> {"corner","edge","interior"}; params() -> dict
    rotations_for(sides, allowed, slot_id, forced=None) -> tuple[int, ...]   # slot-level fit

square_board(cols, rows, border="standard", rotation="none") -> Board
```
Standard: 4 corner slots, edge slots on each side, interior rest (needs cols, rows >= 2). Tray: every slot interior. 20x25 standard: 4 corners, 82 edges, 414 interior, 955 adjacencies. `board.rotation` selects the inventory defaults and the class-map border policy; per-piece `allowed_rotations` decides what actually rotates.

## pieces.py

```python
@dataclass(frozen=True)
class Piece:
    piece_id: int; shape_type: str ("corner"|"edge"|"interior"); cls: str = "any"
    allowed_rotations: frozenset[int] = frozenset({0})
    home: str | None = None      # upright side/corner carrying the flat sides
    sides: tuple[str, ...] | None = None   # derived from shape_type/home when None

default_sides(shape_type, home, connectors="asym", inner=None) -> tuple[str, ...]
flat_side_indices(shape_type, home) -> tuple[int, ...]
rotations_for_piece(board, piece, slot_id, forced=None) -> tuple[int, ...]
flat_dirs(sides, rotation) -> frozenset                       # directions showing flat
exact_rotations(piece, flats, cls_at=None, forced=None) -> tuple[int, ...]
group_placements(board, parts, cls_at=None, forced_at=None, space=None) -> list[tuple]
class SeamSpace(board, cls_at=None, forced_at=None): placements(parts); plan(pieces, left, rng, steps=0)
build_valid_layout(board, pieces, cls_at=None, forced_at=None, rng=None, tries=25, space=None, diag=None, steps=0)
inventory_layout(boards, extra_flat_pieces=0, free_corners=False) -> list[(shape_type, home)]
make_inventory(boards, cls="any", extra_flat_pieces=0, free_corners=False) -> list[Piece]
piece_to_dict(p) / piece_from_dict(d)
```
`boards` is one Board or a list of boards with equal slot counts. Inventory composition: see Mixed frames above. Without rotation, extras cycle N, S, W, E, so use an even count. `free_corners=True`: corner pieces get all four rotations and `wild` inner sides even in rotation none.

## scene.py

```python
class SceneError(ValueError)
FORCED_ZERO                                        # rot value for a forced 0
@dataclass
class ClassMap: cls, rot (grids), forced; cols, rows; histogram(); tokens(); from_tokens(rows)
parse_token(tok) -> (cls, rot); parse_text(text) -> list[ClassMap]; load_scenes(paths) -> list[ClassMap]
validate_scenes(boards, maps, free_corners=False, strict_border=None) -> None   # raises SceneError
pieces_from_scenes(boards, maps, extra_flat_pieces=0, free_corners=False, allowed_rotations=None, strict_border=False) -> list[Piece]
seam_report(boards, maps, pieces) -> list[dict | None]   # flat_inside, seams, cross_class, groups per map
```
- `boards` is one board or three; maps are per solution and have that solution's shape.
- Text format: one row per line, whitespace-separated tokens, blank line between maps, `#` comments. JSON: a list of 3 grids, or `{"maps": [...]}`. `load_scenes` takes three paths or one file with three maps.
- The orientation rule and class derivation are in the sections above.

## metrics.py

```python
piece_edges(placement, board) -> set[(p, q)]
shared_adjacencies(pa, pb, board_a, board_b=None) -> (count, sorted pairs)   # board-independent: piece-pair neighbor sets
shared_fraction(pa, pb, board_a, board_b=None) -> float                      # count / min(adjacencies of the two boards)
components(edges); transferable_clusters(pairs, min_size=3); cluster_penalty(pairs)  # sum of sizes of 3+ components
familiarity(pa, pb, board_a, board_b=None) -> dict[piece, int]
corner_order(placement, board) -> tuple   # clockwise from NW, rotated so the smallest id leads (6 classes)
report(solution) -> dict (key "text" holds the readable summary); format_report(rep)
```
Adjacency means any slot contact, including flat-flat seams. Report keys: `boards`, `n_pieces`, `n_adjacencies`, `pairs` (AB/AC/BC with `shared`, `fraction`, `clusters`, `largest_component`, `familiar_pieces`, `max_familiarity`, `mean_familiarity`), `total_shared`, `cluster_penalty`, `rotated_pieces`, `corner_orders`, `gates`, `meta`, `text`.

## optimize.py

```python
@dataclass
class Solution:
    boards: list[Board]; pieces: list[Piece]; placements: list[dict]; class_maps: list[ClassMap] | None; meta: dict
    board (property, boards[0]); to_dict(); from_dict(d); save(path); load(path)

DEFAULT_ITERS = 300_000
solve(boards, pieces, class_maps=None, seed=0, iters=None, cluster_weight=0.25,
      mismatch_weight=1.5, distinct_corner_orders=False,
      mating_weight=0.0, max_shared_fraction=None, mating_hops=3) -> Solution
validate_solution(solution) -> list[str]     # empty means valid
```
- `boards`: one Board (used three times) or three Boards with equal slot counts. Deterministic given `seed`.
- Energy = sum over pairs of shared adjacencies + `cluster_weight` * cluster penalty + `mismatch_weight` * side mismatches (per solution) + the mating term when on. The returned solution is the best state with zero mismatches (falls back to the lowest-energy state; `meta["valid"]` tells).
- Start: random placements satisfying slot-level fit, or the seam-aware layouts above. Moves: swap two pieces of one solution (both must fit each other's slot; rotation of each re-chosen to minimize mismatches); re-roll one piece's rotation; focused swaps on pieces in shared adjacencies; seam moves that bring a piece able to show a complementary flat side next to a mismatched flat side; group moves in seam-aware mode. Simulated annealing, incremental deltas, early stop at zero.
- `distinct_corner_orders=True`: needs exactly 4 pieces that fit every corner (use `free_corners=True`); the three solutions get three different corner classes fixed up front, and corner slots are never swapped.
- `meta`: `seed, iters, iters_used, energy, shared{AB,AC,BC}, cluster_penalty, valid, violations, distinct_corner_orders, elapsed_s`, plus `mating_penalty, mating_weight, max_shared_fraction`.

## prototype.py

```python
run_prototype(scenes_path, classes_path, out_dir, *, sizes=None, border="standard", rotation="none",
              seed=0, iters=None, cell=48, grid="none", labels=False, extra_flat=0,
              mating_weight=0.0, max_shared_fraction=None, strict_border=False) -> dict
```
Loads the class maps, derives the inventory (with `extra_flat` added to the automatic seams), restricts rotations by the class spec (pinned to 0 in none mode), solves, and writes the outputs. Returns `valid`, `violations`, `shared`, `gates` (`{"piece", "scene", "failures"}`), `gate_lines`, `files` and `out_dir`. Invalid solutions still write their outputs.

**Parameter ranges in class specs (`classes.py`).** A numeric layer parameter may be sampled per piece instead of fixed. `{"range": [lo, hi]}` works for any numeric parameter; a plain `[lo, hi]` pair works only where the primitive's default is a number (`scale`, `density`, `length`), so list-valued parameters such as `offset`, `kinds` and `radius` stay literal. The value is drawn uniformly (inclusive integers when both bounds are integers) from the piece seed mixed with the layer index and the parameter name, so it is fixed for a piece, identical on every call, and independent of the render size. `ClassSpec.validate()` requires numeric bounds with `lo < hi` and checks each layer at both ends. Mask parameters cannot be ranges. The pipeline's three scale variants per motif (`gen_classes_v12.py`) could be replaced by one `{"range": [0.8, 1.2]}` class, but the variants also scale offsets and margins, so that change is not made here.

## cli.py (`metapuzzle` entry point)

```
metapuzzle solve [--cols N] [--rows N] [--sizes CxR,CxR,CxR] [--border standard|tray]
                 [--rotation none|quarter] [--seed N] [--iters N] [--scenes PATH ...]
                 [--extra-flat N] [--strict-border] [--free-corners] [--distinct-corner-orders]
                 [--mating-weight W] [--max-shared-fraction F] [--out sol.json]
metapuzzle prototype --scenes FILE --classes SPEC.json --out DIR [--sizes ...] [--rotation ...]
                 [--seed N] [--iters N] [--cell N] [--extra-flat N] [--strict-border] [--mating-weight W] [--max-shared-fraction F]
metapuzzle report sol.json [--json]
```
Defaults 10x8 standard none seed 0. `--sizes` gives per-solution sizes (cols x rows; one entry is repeated three times; piece counts must be equal). With `--scenes`, sizes come from the maps (a conflicting `--sizes` is an error). Exit code 2 when the result is not valid. `metapuzzle connectors` exits 2 when some contacts do not mate.

## Solution JSON (version 1)

```json
{
  "format": "metapuzzle-solution", "version": 1,
  "boards": [{"cols": 8, "rows": 12, "border": "standard", "rotation": "none"}, {"...": "..."}, {"...": "..."}],
  "pieces": [{"piece_id": 0, "shape_type": "corner", "home": "NW", "cls": "any",
              "allowed_rotations": [0], "sides": ["flat", "tab", "tab", "flat"]}],
  "placements": [{"0": [0, 0], "1": [5, 0]}, {"...": "..."}, {"...": "..."}],
  "class_maps": null,
  "meta": {"seed": 0, "iters": 300000, "iters_used": 4210, "energy": 0.0,
           "shared": {"AB": 0, "AC": 0, "BC": 0}, "valid": true, "elapsed_s": 0.4}
}
```
`placements[k]` maps the piece id (string) to `[slot_id, rotation_degrees]` on `boards[k]`. `class_maps`, when present, is a list of 3 grids of tokens (`"cls"`, `"cls@90"`, `"cls@0"`, `"cls@*"`). A legacy single `"board"` object is read as three identical boards.

## Known limits

- **Seam padding without rotation is heuristic.** Classes are picked per class pair, leftover flats are counted without their turns, and `_layouts_exist` only confirms afterwards. Automatic padding needs every class rotation-free or every class fully rotatable.
- **Odd extra flat counts.** `make_inventory` and `inventory_layout` want an even count without rotation (an odd count leaves one flat piece unpaired). The scene path adds one partner for an odd count.
- **Tight class maps.** A class with too few cells for its border pieces raises `SceneError`. Padding cannot add cells, so the scene needs more cells of that class, or a different rotation or suffix. Forced frame cells make the per-home pools larger, so they are the usual cause.
- **Constructed layouts assume mating.** `build_valid_layout` gives up after `tries` attempts (returns `None`). Its validity, and seam mode, assume every non-flat profile mates with every other non-flat profile the pieces present. `meta["valid"]` and `validate_solution` check the actual mating.
- **Mating penalty is a bound.** The 3-hop ball is a lower bound on the class, so a zero penalty does not prove small classes. Check with `connectors.class_summary`. Hops of 2 miss long chains of degree-2 sides.
- **Roles histogram search is heuristic.** A failed search reports the closest violations within `iters` and does not prove that no histogram exists. Some infeasible inputs are proved infeasible and their errors name the roles and classes.
- **Gate thresholds differ.** The code gate is 5% per pair (`metrics.PIECE_GATES`); `docs/EVALUATION.md` section 2 says below 10%, stretch 0.
- **Stale docstring.** `roles.py` says suffixes need interior cells; `validate_scenes` allows them on frame cells in quarter mode, which this spec follows.

## Extension points (not implemented)

- Profile dialects for shape deviation: new profile ids plus entries in `mates`; slot-level fit and pairwise mating already read them.
- Per-solution rotation groups and per-piece art tags beyond `allowed_rotations`.
- Keyed or custom connectors through the `wild` profile, once a dialect defines what mates with what.
