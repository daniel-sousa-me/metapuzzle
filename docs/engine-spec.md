# Arrangement engine: interface spec

Scope: square lattice only (DECISIONS). Rotation is `none` first, `quarter` second. Pure Python 3.10+ and numpy, type hints, brief docstrings. Package `metapuzzle` under `src/`.

Conventions
- Sides: N=0, E=1, S=2, W=3. Corners: NW=0, NE=1, SE=2, SW=3. Rotation is clockwise degrees in {0, 90, 180, 270}.
- Slot id = `y * cols + x` (row-major, y=0 is the top row). Piece ids are ints.
- A **placement** is `dict[int, tuple[int, int]]`: `piece_id -> (slot_id, rotation_degrees)`, a bijection onto the slots of **that solution's board**.
- A solution set is exactly three placements A, B, C (indices 0, 1, 2) on **three boards** (equal slot counts, possibly different aspect ratios, e.g. 8x12, 12x8, 16x6). Pairs: AB, AC, BC.

## Side profiles and validity (the general model)

Every piece has four side profiles `sides = (N, E, S, W)` in its upright frame, from `tab`, `blank`, `flat`, `andro`, `wild`.
- Mating (`board.mates`): `flat~flat`; `tab~blank`; `andro~andro`; `wild` mates with any non-flat profile (placeholder for keyed or custom connectors, an extension point).
- Rotated by `r` degrees (q = r/90 quarter turns), the profile facing board direction `d` is `sides[(d - q) % 4]`.
- **Slot-level fit** (`Board.rotations_for`): on a `standard` board every boundary side of the slot must present `flat`; on a `tray` board nothing is required at the boundary. Rotation must be in the piece's `allowed_rotations` (and equal to the cell's forced rotation, if any), and the class must match the class-map cell.
- **Pairwise validity**: for every two touching slots, the two facing sides must mate. A solution is **valid** when every piece fits its slot and no touching pair fails to mate. Flat sides inside the picture are therefore legal only against another flat side (a seam). Corner/edge/interior is a label, not the rule.
- `Slot.kind/home/type` (corner NW.., edge N.., interior) are still provided for generators, class-map border checks and reports.

Default connectors (`pieces.default_sides`): rotation none uses the asymmetric interior pattern blank N/W, tab S/E with `flat` replacing the sides that face the border (interior pieces mate with every neighbor); rotation quarter uses `andro` on all non-flat sides.

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
rotations_for_piece(board, piece, slot_id, forced=None) -> tuple[int, ...]
inventory_layout(boards, extra_flat_pieces=0, free_corners=False) -> list[(shape_type, home)]
make_inventory(boards, cls="any", extra_flat_pieces=0, free_corners=False) -> list[Piece]
piece_to_dict(p) / piece_from_dict(d)
```
`boards` is one Board or a list of boards with equal slot counts. Inventory composition: 4 corner pieces; edge pieces numbering the **maximum any board needs** (rotation none: per side, `max(cols-2)` for N and S, `max(rows-2)` for W and E; quarter: pooled `max(edge slots)`); plus `extra_flat_pieces` more flat-sided edge pieces (without rotation they cycle N, S, W, E, so use an even count); the rest interior. On a board with a smaller frame the surplus flat-sided pieces sit inside the picture in flat-flat seams, so a frame piece in one solution can be interior in another. `free_corners=True`: corner pieces get all four rotations and `wild` inner sides even in rotation none.

## scene.py

```python
class SceneError(ValueError)
@dataclass
class ClassMap: cls, rot (grids); cols, rows; histogram(); tokens(); from_tokens(rows)
parse_token(tok) -> (cls, rot); parse_text(text) -> list[ClassMap]; load_scenes(paths) -> list[ClassMap]
validate_scenes(boards, maps, free_corners=False, strict_border=None) -> None   # raises SceneError
pieces_from_scenes(boards, maps, extra_flat_pieces=0, free_corners=False) -> list[Piece]
```
- `boards` is one board or three; maps are per solution and have that solution's shape.
- Text format: one row per line, whitespace-separated tokens, blank line between maps, `#` comments. JSON: a list of 3 grids, or `{"maps": [...]}`. `load_scenes` takes three paths or one file with three maps.
- `cls@R` (R in {0,90,180,270}): a nonzero suffix forces that placement rotation at that cell in that solution. `@0` is the default and adds no constraint. Needs rotation `quarter` and an interior cell, else `SceneError`.
- `validate_scenes` checks: three maps; each matches its board's dimensions; identical class histograms; border-side class counts match (per side and corner for rotation none, pooled for quarter or free corners) **only when all three boards have the same shape** (or `strict_border=True`); pass `strict_border=False` when extras make the border inventory larger than the perimeter.
- `pieces_from_scenes`: one piece per cell of map A carrying its class. Piece types come from `inventory_layout`: A's frame cells receive fitting flat-sided pieces, the remaining cells (interior pieces and evenly spread extras) fill the rest.

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
Adjacency means any slot contact, including flat-flat seams. Report keys: `boards`, `n_pieces`, `n_adjacencies`, `pairs` (AB/AC/BC with `shared`, `fraction`, `clusters`, `largest_component`, `familiar_pieces`, `max_familiarity`, `mean_familiarity`), `total_shared`, `cluster_penalty`, `rotated_pieces`, `corner_orders`, `meta`, `text`.

## optimize.py

```python
@dataclass
class Solution:
    boards: list[Board]; pieces: list[Piece]; placements: list[dict]; class_maps: list[ClassMap] | None; meta: dict
    board (property, boards[0]); to_dict(); from_dict(d); save(path); load(path)

DEFAULT_ITERS = 300_000
solve(boards, pieces, class_maps=None, seed=0, iters=None, cluster_weight=0.25,
      mismatch_weight=1.5, distinct_corner_orders=False) -> Solution
validate_solution(solution) -> list[str]     # empty means valid
```
- `boards`: one Board (used three times) or three Boards with equal slot counts. Deterministic given `seed`.
- Energy = sum over pairs of shared adjacencies + `cluster_weight` * cluster penalty + `mismatch_weight` * side mismatches. The returned solution is the best state with zero mismatches (falls back to the lowest-energy state; `meta["valid"]` tells).
- Start: random placements satisfying slot-level fit. Moves: swap two pieces of one solution (both must fit each other's slot; rotation of each is re-chosen to minimize mismatches); re-roll one piece's rotation; focused swaps on pieces in shared adjacencies; **seam moves** that bring a piece able to show a complementary flat side next to a mismatched flat side. Simulated annealing, incremental deltas, early stop at zero.
- `distinct_corner_orders=True`: needs exactly 4 pieces that fit every corner (use `free_corners=True`); the three solutions get three different corner classes fixed up front and corner slots are never swapped.
- `meta`: `seed, iters, iters_used, energy, shared{AB,AC,BC}, cluster_penalty, valid, violations, distinct_corner_orders, elapsed_s`.

## cli.py (`metapuzzle` entry point)

```
metapuzzle solve [--cols N] [--rows N] [--sizes CxR,CxR,CxR] [--border standard|tray]
                 [--rotation none|quarter] [--seed N] [--iters N] [--scenes PATH ...]
                 [--extra-flat N] [--free-corners] [--distinct-corner-orders] [--out sol.json]
metapuzzle report sol.json [--json]
```
Defaults 10x8 standard none seed 0. `--sizes` gives per-solution sizes (cols x rows; one entry is repeated three times; piece counts must be equal). With `--scenes`, sizes come from the maps (a conflicting `--sizes` is an error). Exit code 2 when the result is not valid.

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
`placements[k]` maps the piece id (string) to `[slot_id, rotation_degrees]` on `boards[k]`. `class_maps`, when present, is a list of 3 grids of tokens (`"cls"` or `"cls@90"`). A legacy single `"board"` object is read as three identical boards.

## Extension points (not implemented)

- Profile dialects for shape deviation: new profile ids plus entries in `mates`; slot-level fit and pairwise mating already read them.
- Per-solution rotation groups and per-piece art tags beyond `allowed_rotations`.
- Odd `extra_flat_pieces` cannot pair into seams without rotation; the solver then reports `valid=False`.
