import json
import random

import pytest

from metapuzzle.board import square_board
from metapuzzle.metrics import corner_order
from metapuzzle.optimize import DEFAULT_ITERS, Solution, solve, validate_solution
from metapuzzle.pieces import make_inventory
from metapuzzle.scene import ClassMap, pieces_from_scenes

MIXED = [(8, 12), (12, 8), (16, 6)]


def run(sizes, border="standard", rotation="none", seed=0, **kw):
    boards = [square_board(c, r, border, rotation) for c, r in sizes]
    inv_kw = {k: kw.pop(k) for k in ("extra_flat_pieces", "free_corners") if k in kw}
    pieces = make_inventory(boards, **inv_kw)
    return solve(boards, pieces, seed=seed, **kw)


def test_10x8_standard_none_reaches_zero_default_iters():
    sol = run([(10, 8)] * 3)
    assert sol.meta["shared"] == {"AB": 0, "AC": 0, "BC": 0}
    assert sol.meta["iters_used"] <= DEFAULT_ITERS
    assert validate_solution(sol) == []


@pytest.mark.parametrize("border,rotation", [("standard", "quarter"), ("tray", "none"), ("tray", "quarter")])
def test_other_modes_reach_zero(border, rotation):
    sol = run([(10, 8)] * 3, border, rotation)
    assert sum(sol.meta["shared"].values()) == 0 and validate_solution(sol) == []


def test_deterministic_and_seed_sensitive():
    a, b = run([(10, 8)] * 3, seed=3), run([(10, 8)] * 3, seed=3)
    assert a.placements == b.placements
    assert run([(10, 8)] * 3, seed=4).placements != a.placements


def test_zero_iters_still_valid_placement():
    sol = run([(10, 8)] * 3, iters=0)
    assert validate_solution(sol) == []  # initial placement respects border types
    assert sum(sol.meta["shared"].values()) > 0


def test_border_pieces_stay_on_border_without_rotation():
    sol = run([(10, 8)] * 3)
    kinds = {p.piece_id: p.shape_type for p in sol.pieces}
    for pl in sol.placements:
        for pid, (slot, rot) in pl.items():
            assert rot == 0
            assert (sol.boards[0].slots[slot].kind == "interior") == (kinds[pid] == "interior")


def test_quarter_rotation_uses_all_sides():
    sol = run([(10, 8)] * 3, rotation="quarter")
    assert any(r for pl in sol.placements for _, r in pl.values())


def test_validate_solution_detects_problems():
    sol = run([(6, 5)] * 3, iters=0)
    bad = Solution(sol.boards, sol.pieces, [dict(p) for p in sol.placements], None, {})
    ids = list(bad.placements[0])
    a, b = ids[0], ids[-1]  # a corner piece and an interior piece
    bad.placements[0][a], bad.placements[0][b] = bad.placements[0][b], bad.placements[0][a]
    assert validate_solution(bad)


def test_large_25x20_fast():
    sol = run([(25, 20)] * 3)
    assert sum(sol.meta["shared"].values()) == 0
    assert sol.meta["elapsed_s"] < 30 and validate_solution(sol) == []


# ---- mixed aspect ratios -----------------------------------------------------------------
@pytest.mark.parametrize("rotation", ["none", "quarter"])
def test_mixed_frames_96_pieces(rotation):
    sol = run(MIXED, rotation=rotation)
    assert [b.cols for b in sol.boards] == [8, 12, 16]
    assert sol.meta["valid"] and validate_solution(sol) == []
    assert sol.meta["shared"] == {"AB": 0, "AC": 0, "BC": 0}


def test_mixed_frames_flat_pieces_sit_inside():
    sol = run(MIXED, rotation="none")
    inside = 0
    for pl, b in zip(sol.placements, sol.boards):
        kinds = {p.piece_id: p.shape_type for p in sol.pieces}
        inside += sum(1 for pid, (s, _) in pl.items() if kinds[pid] == "edge" and b.slots[s].kind == "interior")
    assert inside > 0  # seams appear inside at least one picture


def test_mixed_frames_with_extra_flat_pieces():
    sol = run(MIXED, rotation="quarter", extra_flat_pieces=6)
    assert sol.meta["valid"] and sum(sol.meta["shared"].values()) == 0
    assert validate_solution(sol) == []


def test_extra_flat_single_frame_no_rotation():
    sol = run([(10, 8)] * 3, extra_flat_pieces=4)
    assert sol.meta["valid"] and sum(sol.meta["shared"].values()) == 0
    kinds = {p.piece_id: p.shape_type for p in sol.pieces}
    b = sol.boards[0]
    assert all(
        sum(1 for pid, (s, _) in pl.items() if kinds[pid] == "edge" and b.slots[s].kind == "interior") == 4
        for pl in sol.placements
    )


def test_mixed_frames_480_pieces():
    sol = run([(20, 24), (30, 16), (40, 12)], rotation="quarter")
    assert sol.meta["valid"] and sum(sol.meta["shared"].values()) == 0


def test_unequal_slot_counts_rejected():
    with pytest.raises(ValueError):
        solve([square_board(8, 12), square_board(8, 12), square_board(8, 11)], make_inventory(square_board(8, 12)))


# ---- corner order ----------------------------------------------------------------------
def test_distinct_corner_orders():
    sol = run([(10, 8)] * 3, free_corners=True, distinct_corner_orders=True)
    orders = [corner_order(pl, b) for pl, b in zip(sol.placements, sol.boards)]
    assert len(set(orders)) == 3
    assert sol.meta["valid"] and validate_solution(sol) == []
    assert any(r for pl in sol.placements for pid, (_, r) in pl.items() if sol.pieces[pid].shape_type == "corner")


def test_distinct_corner_orders_requires_free_corners():
    boards = [square_board(10, 8)] * 3
    with pytest.raises(ValueError):
        solve(boards, make_inventory(boards), distinct_corner_orders=True)


# ---- class maps ------------------------------------------------------------------------
def band_maps(cols, rows):
    rowsA = [["sky" if y < rows // 2 else "sea" for _ in range(cols)] for y in range(rows)]
    colsB = [["sky" if x < cols // 2 else "sea" for x in range(cols)] for _ in range(rows)]
    diag = [["sky" if (x + y) % 2 == 0 else "sea" for x in range(cols)] for y in range(rows)]
    return [ClassMap.from_tokens(g) for g in (rowsA, colsB, diag)]


def test_class_maps_respected_tray():
    boards = [square_board(8, 6, "tray")] * 3
    maps = band_maps(8, 6)
    pieces = pieces_from_scenes(boards, maps)
    sol = solve(boards, pieces, maps, seed=1)
    assert validate_solution(sol) == []
    assert sum(sol.meta["shared"].values()) == 0
    by_id = {p.piece_id: p for p in pieces}
    for k, pl in enumerate(sol.placements):
        for pid, (s, _) in pl.items():
            sl = boards[k].slots[s]
            assert by_id[pid].cls == maps[k].cls[sl.y][sl.x]


def test_class_maps_standard_with_forced_rotation():
    boards = [square_board(8, 6, "standard", "quarter")] * 3
    maps = band_maps(8, 6)
    maps[1].rot[2][3] = 90
    maps[2].rot[3][4] = 270
    pieces = pieces_from_scenes(boards, maps)
    sol = solve(boards, pieces, maps, seed=2)
    assert validate_solution(sol) == []
    b = boards[1]
    pid = next(p for p, (s, r) in sol.placements[1].items() if s == b.slot_at(3, 2))
    assert sol.placements[1][pid][1] == 90


def test_class_maps_mixed_frames():
    sizes = [(8, 6), (6, 8), (12, 4)]
    boards = [square_board(c, r, "standard", "quarter") for c, r in sizes]
    maps = [band_maps(c, r)[i] for i, (c, r) in enumerate(sizes)]
    pieces = pieces_from_scenes(boards, maps)
    sol = solve(boards, pieces, maps, seed=0)
    assert sol.meta["valid"] and sum(sol.meta["shared"].values()) == 0


# ---- class maps with mixed frames: flat-sided surplus pieces sit inside as seams --------------
def concentric_map(cols, rows, counts, labels="fab"):
    """Classes by depth from the border: the first counts[0] cells (outermost) get labels[0], and so on."""
    cells = sorted((min(x, y, cols - 1 - x, rows - 1 - y), y, x) for y in range(rows) for x in range(cols))
    grid = [[""] * cols for _ in range(rows)]
    i = 0
    for lab, n in zip(labels, counts):
        for _, y, x in cells[i:i + n]:
            grid[y][x] = lab
        i += n
    return ClassMap.from_tokens(grid)


def tone_map(cols, rows, counts, seed):
    """Light at the top, dark at the bottom, with noise; classes T5..T0 hold counts[0..] cells."""
    rng = random.Random(seed)
    cells = sorted((y / (rows - 1) + rng.uniform(-0.45, 0.45), x, y) for y in range(rows) for x in range(cols))
    grid = [[""] * cols for _ in range(rows)]
    i = 0
    for c, n in enumerate(counts):
        for _, x, y in cells[i:i + n]:
            grid[y][x] = f"T{c}"
        i += n
    return ClassMap.from_tokens(grid)


def interior_flat(sol):
    """Per board: flat-sided pieces that sit off the frame."""
    out = []
    for pl, b in zip(sol.placements, sol.boards):
        out.append(sum(1 for pid, (s, _) in pl.items() if "flat" in sol.pieces[pid].sides and not b.slots[s].boundary_sides))
    return out


@pytest.mark.parametrize("rotation", ["none", "quarter"])
def test_mixed_frames_96_with_class_maps(rotation):
    boards = [square_board(c, r, "standard", rotation) for c, r in MIXED]
    maps = [concentric_map(c, r, [64, 16, 16]) for c, r in MIXED]
    pieces = pieces_from_scenes(boards, maps)
    perimeters = [sum(1 for s in b.slots if s.boundary_sides) for b in boards]
    assert sum("flat" in p.sides for p in pieces) >= max(perimeters)
    sol = solve(boards, pieces, maps, seed=0)
    assert sol.meta["valid"] and validate_solution(sol) == []
    assert sum(sol.meta["shared"].values()) <= 3
    assert all(n > 0 for n in interior_flat(sol)[:2])  # the smaller frames hold seams
    for k, pl in enumerate(sol.placements):  # classes follow the maps
        for pid, (s, _) in pl.items():
            sl = boards[k].slots[s]
            assert sol.pieces[pid].cls == maps[k].cls[sl.y][sl.x]


@pytest.mark.parametrize("rotation", ["none", "quarter"])
def test_mixed_frames_class_maps_valid_before_annealing(rotation):
    boards = [square_board(c, r, "standard", rotation) for c, r in MIXED]
    maps = [concentric_map(c, r, [64, 16, 16]) for c, r in MIXED]
    sol = solve(boards, pieces_from_scenes(boards, maps), maps, iters=0)
    assert sol.meta["valid"] and validate_solution(sol) == []


@pytest.mark.parametrize("rotation", ["none", "quarter"])
def test_mixed_frames_480_with_class_maps(rotation):
    sizes = [(20, 24), (30, 16), (40, 12)]
    counts = [58, 86, 96, 96, 86, 58]
    boards = [square_board(c, r, "standard", rotation) for c, r in sizes]
    maps = [tone_map(c, r, counts, i) for i, (c, r) in enumerate(sizes)]
    pieces = pieces_from_scenes(boards, maps)
    sol = solve(boards, pieces, maps, seed=0)
    assert sol.meta["valid"] and validate_solution(sol) == []
    assert sol.meta["iters_used"] <= DEFAULT_ITERS
    assert sum(sol.meta["shared"].values()) <= 6
    assert min(interior_flat(sol)) > 0


def test_extra_flat_pieces_with_class_maps_stay_valid():
    sizes = [(8, 12), (12, 8), (16, 6)]
    for rotation in ("none", "quarter"):
        boards = [square_board(c, r, "standard", rotation) for c, r in sizes]
        maps = [concentric_map(c, r, [64, 16, 16]) for c, r in sizes]
        base = pieces_from_scenes(boards, maps)
        more = pieces_from_scenes(boards, maps, extra_flat_pieces=6)
        assert sum("flat" in p.sides for p in more) >= sum("flat" in p.sides for p in base) + 6
        sol = solve(boards, more, maps, seed=1)
        assert sol.meta["valid"] and validate_solution(sol) == []


def test_json_roundtrip():
    sol = run(MIXED, rotation="quarter", seed=5)
    again = Solution.from_dict(json.loads(json.dumps(sol.to_dict())))
    assert again.placements == sol.placements and again.pieces == sol.pieces
    assert [b.params() for b in again.boards] == [b.params() for b in sol.boards]
    assert validate_solution(again) == []
