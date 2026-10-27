"""Cross-class seams: frames with different class mixes on a standard border, absorbed by interior seams."""
import random

import pytest

from metapuzzle.board import square_board
from metapuzzle.cli import main
from metapuzzle.optimize import solve, validate_solution
from metapuzzle.pieces import Piece, SeamSpace, default_sides, flat_dirs, group_placements
from metapuzzle.prototype import seam_counts
from metapuzzle.scene import ClassMap, SceneError, pieces_from_scenes, seam_report

MIXES = [(10, 7, 3), (7, 10, 3), (8, 8, 4)]  # frame edge cells of class a, b, c per map; the corners are all c


def frame_mix_map(cols, rows, edges, seed, suffix=""):
    """Corners class c; frame edge cells hold `edges` (a, b, c) counts; each class has 16 cells in all."""
    rng = random.Random(seed)
    cells = [(x, y) for y in range(rows) for x in range(cols)]
    corner = {(0, 0), (cols - 1, 0), (0, rows - 1), (cols - 1, rows - 1)}
    edge = [c for c in cells if (c[0] in (0, cols - 1) or c[1] in (0, rows - 1)) and c not in corner]
    inner = [c for c in cells if c not in corner and c not in edge]
    on_frame = ["a"] * edges[0] + ["b"] * edges[1] + ["c"] * edges[2]
    inside = ["a"] * (16 - edges[0]) + ["b"] * (16 - edges[1]) + ["c"] * (16 - edges[2] - 4)
    rng.shuffle(on_frame)
    rng.shuffle(inside)
    g = [[""] * cols for _ in range(rows)]
    for x, y in corner:
        g[y][x] = "c"
    for (x, y), lab in zip(edge, on_frame):
        g[y][x] = lab
    for (x, y), lab in zip(inner, inside):
        g[y][x] = lab
    if suffix:  # orientation suffix on every cell of class a
        g = [[t + suffix if t == "a" else t for t in row] for row in g]
    return ClassMap.from_tokens(g)


def scene(suffix=""):
    boards = [square_board(6, 8, "standard", "quarter") for _ in range(3)]
    return boards, [frame_mix_map(6, 8, m, i, suffix) for i, m in enumerate(MIXES)]


def test_strict_border_still_rejects_different_frame_mixes():
    boards, maps = scene()
    with pytest.raises(SceneError, match="border class counts"):
        pieces_from_scenes(boards, maps, strict_border=True)


def test_inventory_sized_to_largest_frame_need_and_seams_reported():
    boards, maps = scene()
    pieces = pieces_from_scenes(boards, maps)
    flat = [p for p in pieces if "flat" in p.sides]
    # per class: the largest frame need over the maps (a 10, b 10, c 4 edges + 4 corners)
    assert sum(p.cls == "a" for p in flat) == 10 and sum(p.cls == "b" for p in flat) == 10
    assert sum(p.cls == "c" and p.shape_type == "edge" for p in flat) == 4 and sum(p.shape_type == "corner" for p in flat) == 4
    rep = seam_report(boards, maps, pieces)
    assert all(r is not None and r["flat_inside"] == 4 and r["seams"] == 2 for r in rep)
    # maps A and B have an odd surplus in two classes, which only a cross-class seam can pair
    assert rep[0]["cross_class"] >= 1 and rep[1]["cross_class"] >= 1


@pytest.mark.parametrize("suffix", ["", "@0"])
def test_three_scenes_with_different_frame_mixes_solve_validly(suffix):
    boards, maps = scene(suffix)
    pieces = pieces_from_scenes(boards, maps)
    sol = solve(boards, pieces, maps, seed=0)
    assert sol.meta["valid"] and validate_solution(sol) == []
    assert sum(sol.meta["shared"].values()) <= 3
    counts = seam_counts(sol)
    if suffix:  # forced rotations need more flat pieces (one home per frame side); only validity is fixed
        assert all(c["seams"] >= 2 for c in counts)
    else:
        assert [c["seams"] for c in counts] == [2, 2, 2] and counts[0]["cross_class"] >= 1 and counts[1]["cross_class"] >= 1
    for k, pl in enumerate(sol.placements):  # classes follow the maps
        for pid, (s, _) in pl.items():
            sl = boards[k].slots[s]
            assert sol.pieces[pid].cls == maps[k].cls[sl.y][sl.x]


def test_cli_standard_border_with_different_frame_mixes(tmp_path):
    _, maps = scene()
    p = tmp_path / "scenes.txt"
    p.write_text("\n\n".join("\n".join(" ".join(row) for row in m.tokens()) for m in maps) + "\n")
    assert main(["solve", "--border", "standard", "--rotation", "quarter", "--scenes", str(p), "--seed", "1"]) == 0
    assert main(["solve", "--border", "standard", "--rotation", "quarter", "--scenes", str(p), "--strict-border"]) == 1


def _edge(i, cls, home="N", rots=(0, 90, 180, 270)):
    return Piece(i, "edge", cls, frozenset(rots), home, default_sides("edge", home, "andro"))


def _corner(i, cls, rots=(0, 90, 180, 270)):
    return Piece(i, "corner", cls, frozenset(rots), "NW", default_sides("corner", "NW", "andro"))


def test_group_placements_cross_class_domino_follows_cell_classes():
    b = square_board(6, 6, "standard", "quarter")
    cls_at = ["a" if s.x <= 2 else "b" for s in b.slots]  # a on the left, b on the right
    parts = [_edge(0, "a"), _edge(1, "b")]
    placements = group_placements(b, parts, cls_at)
    assert placements
    for (sa, ra), (sb, rb) in placements:
        assert cls_at[sa] == "a" and cls_at[sb] == "b"
        da = flat_dirs(parts[0].sides, ra)
        db = flat_dirs(parts[1].sides, rb)
        (d,) = da
        assert db == {(d + 2) % 4}
    assert {(b.slots[sa].x, b.slots[sb].x) for (sa, _), (sb, _) in placements} == {(2, 3)}


def test_group_placements_l_tromino_and_blocks():
    b = square_board(8, 8, "standard", "quarter")
    cls_at = ["a"] * b.n_slots
    corner, e1, e2 = _corner(0, "a"), _edge(1, "a"), _edge(2, "a")
    for slots in group_placements(b, [corner, e1, e2], cls_at):
        assert len({s for s, _ in slots}) == 3
    assert group_placements(b, [corner, e1, e2], cls_at)
    two_corners = [_corner(0, "a"), _corner(1, "a"), _edge(2, "a"), _edge(3, "a")]
    plan = group_placements(b, two_corners, cls_at)
    assert plan and all(len({s for s, _ in g}) == 4 for g in plan)
    four = [_corner(i, "a") for i in range(4)]
    assert group_placements(b, four, cls_at)
    # every flat side of every group piece faces a flat side of a neighbour in the group
    for g in plan[:20]:
        pos = {s: (r, p) for (s, r), p in zip(g, two_corners)}
        for s, (r, p) in pos.items():
            for d in flat_dirs(p.sides, r):
                dx, dy = ((0, -1), (1, 0), (0, 1), (-1, 0))[d]
                t = b.slot_at(b.slots[s].x + dx, b.slots[s].y + dy)
                assert t in pos and (d + 2) % 4 in flat_dirs(pos[t][1].sides, pos[t][0])


def test_seam_space_plan_pairs_odd_classes_across_classes():
    b = square_board(8, 8, "standard", "quarter")
    cls_at = ["a" if s.x < 4 else "b" for s in b.slots]
    pieces = [_edge(0, "a"), _edge(1, "b")]
    groups, unplaced = SeamSpace(b, cls_at).plan(pieces, [0, 1], random.Random(0))
    assert unplaced == [] and len(groups) == 1
    cls_far = ["a" if s.x == 1 else "b" if s.x == 5 else "c" for s in b.slots]  # a and b never touch
    groups, unplaced = SeamSpace(b, cls_far).plan(pieces, [0, 1], random.Random(0))
    assert groups == [] and sorted(unplaced) == [0, 1]
