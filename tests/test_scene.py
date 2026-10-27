import json

import pytest

from metapuzzle.board import square_board
from metapuzzle.optimize import solve, validate_solution
from metapuzzle.pieces import flat_dirs, rotations_for_piece
from metapuzzle.scene import ClassMap, SceneError, load_scenes, parse_text, parse_token, pieces_from_scenes, validate_scenes


def grid(cols, rows, f):
    return ClassMap.from_tokens([[f(x, y) for x in range(cols)] for y in range(rows)])


def test_parse_token():
    assert parse_token("sky") == ("sky", 0)
    assert parse_token("sky@0") == ("sky", 0)
    assert parse_token("sky@90") == ("sky", 90)
    for bad in ("sky@45", "@90", "sky@x", "a@1@2"):
        with pytest.raises(SceneError):
            parse_token(bad)


def test_parse_text_and_load(tmp_path):
    text = "# A\na b\nb a\n\nb a\na b\n\na a\nb b\n"
    maps = parse_text(text)
    assert len(maps) == 3 and maps[0].cls == [["a", "b"], ["b", "a"]]
    p = tmp_path / "s.txt"
    p.write_text(text)
    assert len(load_scenes([p])) == 3
    j = tmp_path / "s.json"
    j.write_text(json.dumps({"maps": [["a b", "b a"], ["b a", "a b"], ["a a", "b b"]]}))
    assert load_scenes(j)[2].cls == [["a", "a"], ["b", "b"]]
    with pytest.raises(SceneError):
        load_scenes([p, p])


def test_ragged_rows_rejected():
    with pytest.raises(SceneError):
        parse_text("a b\na\n")


def test_valid_scenes_and_inventory():
    b = square_board(4, 3, "tray")
    maps = [grid(4, 3, lambda x, y: "sky" if y == 0 else "sea"), grid(4, 3, lambda x, y: "sky" if y == 2 else "sea"),
            grid(4, 3, lambda x, y: "sky" if y == 1 else "sea")]
    validate_scenes(b, maps)
    inv = pieces_from_scenes(b, maps)
    assert len(inv) == 12 and sum(p.cls == "sky" for p in inv) == 4


def test_histogram_mismatch():
    b = square_board(4, 3, "tray")
    maps = [grid(4, 3, lambda x, y: "a"), grid(4, 3, lambda x, y: "a"), grid(4, 3, lambda x, y: "b" if x == 0 else "a")]
    with pytest.raises(SceneError, match="histograms"):
        validate_scenes(b, maps)


def test_dimension_mismatch():
    b = square_board(4, 3, "tray")
    maps = [grid(4, 3, lambda x, y: "a")] * 2 + [grid(3, 4, lambda x, y: "a")]
    with pytest.raises(SceneError, match="board"):
        validate_scenes(b, maps)


def test_border_side_counts_checked_without_rotation():
    b = square_board(5, 4)
    mk = lambda top: grid(5, 4, lambda x, y: "sky" if (y == 0 and top) or (y == 3 and not top) else "sea")
    maps = [mk(True), mk(False), mk(True)]
    # histograms match (5 sky each) but the top side holds different classes
    with pytest.raises(SceneError, match="border"):
        validate_scenes(b, maps)
    validate_scenes(b, maps, strict_border=False)


def test_border_pooled_under_quarter():
    b = square_board(5, 4, rotation="quarter")
    mk = lambda top: grid(5, 4, lambda x, y: "sky" if (y == 0 and 0 < x < 4) == top and 0 < x < 4 and y in (0, 3) else "sea")
    maps = [mk(True), mk(False), mk(True)]
    validate_scenes(b, maps)


def test_orientation_suffix_rules():
    b = square_board(4, 3, "tray")
    m = grid(4, 3, lambda x, y: "a@90" if (x, y) == (1, 1) else "a")
    with pytest.raises(SceneError, match="quarter"):
        validate_scenes(b, [m] * 3)
    bq = square_board(4, 3, "tray", "quarter")
    validate_scenes(bq, [m] * 3)
    bs = square_board(5, 4, "standard", "quarter")
    mb = grid(5, 4, lambda x, y: "a@90" if (x, y) == (0, 1) else "a")
    validate_scenes(bs, [mb] * 3)  # a frame cell may carry a forced rotation in quarter mode
    # Pooled border counts must still agree: "x" on a corner in A but not on the frame in B.
    on_corner = grid(5, 4, lambda x, y: "x" if (x, y) == (0, 0) else "y")
    inside = grid(5, 4, lambda x, y: "x" if (x, y) == (2, 2) else "y")
    with pytest.raises(SceneError, match="border"):
        validate_scenes(bs, [on_corner, inside, on_corner])


def test_bad_label():
    with pytest.raises(SceneError):
        parse_text("a@b\n")


def test_pieces_from_scenes_standard_mixed_frames():
    bs = [square_board(c, r) for c, r in [(8, 12), (12, 8), (16, 6)]]
    maps = [grid(c, r, lambda x, y: "sky" if y < r // 2 else "sea") for c, r in [(8, 12), (12, 8), (16, 6)]]
    maps[1] = grid(12, 8, lambda x, y: "sky" if x < 6 else "sea")
    maps[2] = grid(16, 6, lambda x, y: "sky" if x < 8 else "sea")
    inv = pieces_from_scenes(bs, maps)
    assert len(inv) == 96 and sum(p.cls == "sky" for p in inv) == 48


ALL_ROTATIONS = frozenset({0, 90, 180, 270})


def _frame_scene(rails, suns):
    """4x5 map: canopy frame, `rail` cells (directional when allowed), `sun` and `sea` inside."""
    return grid(4, 5, lambda x, y: "rail" if (x, y) in rails else
                "canopy" if x in (0, 3) or y in (0, 4) else "sun" if (x, y) in suns else "sea")


def _every_cell_fits(boards, maps, pieces):
    for b, m in zip(boards, maps):
        for s in b.slots:
            cls = m.cls[s.y][s.x]
            forced = m.rot[s.y][s.x] or None
            assert any(rotations_for_piece(b, p, s.id, forced) for p in pieces if p.cls == cls), (s.x, s.y, cls)


def test_directional_border_class_solves_in_quarter_mode():
    # "rail" is directional: the N-edge cell (1,0) and the W-edge cell (0,2) in every map.
    rails = {(1, 0), (0, 2)}
    maps = [_frame_scene(rails, {(1, 1), (2, 3)}), _frame_scene(rails, {(2, 1), (1, 3)}),
            _frame_scene(rails, {(1, 2), (2, 2)})]
    boards = [square_board(4, 5, rotation="quarter")] * 3
    allowed = {"rail": {0}, "canopy": ALL_ROTATIONS, "sun": ALL_ROTATIONS, "sea": ALL_ROTATIONS}
    pieces = pieces_from_scenes(boards, maps, allowed_rotations=allowed)
    rail_pieces = sorted((p.shape_type, p.home) for p in pieces if p.cls == "rail")
    assert rail_pieces == [("edge", "N"), ("edge", "W")]
    assert all(p.allowed_rotations == {0} for p in pieces if p.cls == "rail")
    _every_cell_fits(boards, maps, pieces)


def test_directional_side_mismatch_is_impossible_and_named():
    # A needs an N-edge and a W-edge "rail" piece; B needs two N-edge ones, so 2 pieces cannot do both.
    boards = [square_board(4, 5, rotation="quarter")] * 3
    maps = [_frame_scene({(1, 0), (0, 2)}, {(1, 1), (2, 3)}), _frame_scene({(1, 0), (2, 0)}, {(2, 1), (1, 3)}),
            _frame_scene({(1, 0), (0, 2)}, {(1, 2), (2, 2)})]
    allowed = {"rail": {0}}
    with pytest.raises(SceneError, match=r"class 'rail'.*map B cell \(2,0\).*N side"):
        pieces_from_scenes(boards, maps, allowed_rotations=allowed)
    # The same class rotatable pools its border cells, so the case is solvable.
    pieces = pieces_from_scenes(boards, maps, allowed_rotations={"rail": ALL_ROTATIONS})
    assert sum(p.cls == "rail" and p.shape_type == "edge" for p in pieces) == 2
    _every_cell_fits(boards, maps, pieces)


def _solver_view(m):
    """Rotation per cell as the solver reads it: None = unconstrained, else the forced degrees."""
    return [[r or None for r in row] for row in m.rot]


# Orientation rule, end to end: 4x5 standard frame, three maps, quarter rotation.
# `sun` carries @90 in map A only, so its bare cells in B and C are forced to 0.
_SUN_SCENES = """\
canopy canopy canopy canopy
canopy sun@90 sea canopy
canopy sea sea canopy
canopy sea sun canopy
canopy canopy canopy canopy

canopy canopy canopy canopy
canopy sea sun canopy
canopy sea sea canopy
canopy sun sea canopy
canopy canopy canopy canopy

canopy canopy canopy canopy
canopy sea sea canopy
canopy sun sun canopy
canopy sea sea canopy
canopy canopy canopy canopy
"""


def _sun_case(text=_SUN_SCENES):
    maps = parse_text(text)
    boards = [square_board(4, 5, rotation="quarter")] * 3
    validate_scenes(boards, maps)
    sol = solve(boards, pieces_from_scenes(boards, maps), maps, seed=0)
    return boards, maps, sol


def test_forced_class_keeps_its_rotation_in_every_placement():
    boards, maps, sol = _sun_case()
    assert validate_solution(sol) == []
    for k, (b, m) in enumerate(zip(boards, maps)):
        placed = {slot: (pid, rot) for pid, (slot, rot) in sol.placements[k].items()}
        for s in b.slots:
            if m.cls[s.y][s.x] != "sun":
                continue
            pid, rot = placed[s.id]
            assert sol.pieces[pid].cls == "sun"
            # Only A's (1,1) is written @90; every other sun cell is forced to rotation 0.
            assert rot == (90 if (k, s.x, s.y) == (0, 1, 1) else 0), (k, s.x, s.y)


def test_unsuffixed_class_stays_unconstrained():
    boards, maps, sol = _sun_case()
    b, m = boards[0], maps[0]
    sea_cells = [s for s in b.slots if m.cls[s.y][s.x] == "sea"]
    assert all(_solver_view(m)[s.y][s.x] is None for s in sea_cells)
    piece = next(p for p in sol.pieces if p.cls == "sea")
    assert {90, 180, 270} <= set(rotations_for_piece(b, piece, sea_cells[0].id, None))
    # Sea pieces are not pinned: some are placed turned.
    turned = [rot for k in range(3) for pid, (_, rot) in sol.placements[k].items()
              if sol.pieces[pid].cls == "sea" and rot]
    assert turned


def test_any_rotation_escape_leaves_one_cell_free():
    text = _SUN_SCENES.replace("canopy sea sun canopy", "canopy sea sun@* canopy", 1)  # map A, cell (2,3)
    boards, maps, sol = _sun_case(text)
    assert validate_solution(sol) == []
    assert _solver_view(maps[0])[3][2] is None  # `@*` inside a forced class: unconstrained
    assert maps[0].tokens()[3][2] == "sun@*" and maps[0].tokens()[1][1] == "sun@90"
    assert maps[1].tokens()[1][2] == "sun@0"  # bare cells of the forced class stay forced
    piece = next(p for p in sol.pieces if p.cls == "sun")
    assert set(rotations_for_piece(boards[0], piece, boards[0].slot_at(2, 3), None)) == {0, 90, 180, 270}


def test_orientation_rule_spans_all_three_maps(tmp_path):
    # `sun@90` in A forces every sun in B and C; `sun@*` is free; `sea` never has a suffix.
    maps = parse_text("sun@90 sea\nsea sea\n\nsun sea\nsea sun@*\n\nsea sun\nsun sea")
    a, b, c = (_solver_view(m) for m in maps)
    assert a[0][0] == 90 and a[1][1] is None
    assert b[0][0] == 0 and b[1][1] is None
    assert c[0][1] == 0 and c[1][0] == 0 and c[0][0] is None and c[1][1] is None
    assert maps[0].tokens() == [["sun@90", "sea"], ["sea", "sea"]]
    assert maps[1].tokens() == [["sun@0", "sea"], ["sea", "sun@*"]]
    assert maps[2].tokens() == [["sea", "sun@0"], ["sun@0", "sea"]]
    # Written back as one scene file and reloaded, the solver view is unchanged.
    path = tmp_path / "scenes.txt"
    path.write_text("\n\n".join("\n".join(" ".join(r) for r in m.tokens()) for m in maps), encoding="utf-8")
    again = load_scenes(path)
    assert [_solver_view(m) for m in again] == [a, b, c]
    assert [m.cls for m in again] == [m.cls for m in maps]


# Frame transitions, quarter mode, 4x5. "tn" fills the top edge at @180 and "tw" the left edge at @90:
# in both the tier neighbour sits toward the interior, and a piece turned that way lands its flat
# side on its own edge. Each map has the same histogram and the same frame counts per class.
_FRAME_TRANSITION_SCENES = """\
sea tn@180 tn@180 sea
tw@90 sky sky sea
tw@90 sea sky sea
sea sea sea sea
sea sea sea sea

sea tn@180 tn@180 sea
sea sea sea sea
tw@90 sky sea sea
tw@90 sky sky sea
sea sea sea sea

sea tn@180 tn@180 sea
tw@90 sea sky sea
sea sea sky sea
tw@90 sky sea sea
sea sea sea sea
"""


def test_forced_frame_transitions_solve_with_rotation_toward_the_interior():
    maps = parse_text(_FRAME_TRANSITION_SCENES)
    boards = [square_board(4, 5, rotation="quarter")] * 3
    validate_scenes(boards, maps)
    pieces = pieces_from_scenes(boards, maps)
    # Both transition classes need two pieces, each with its flat on the side that turns onto the edge.
    assert sorted((p.cls, p.home) for p in pieces if p.cls in ("tn", "tw")) == [("tn", "S"), ("tn", "S"), ("tw", "S"), ("tw", "S")]
    sol = solve(boards, pieces, maps, seed=0)
    assert validate_solution(sol) == []
    for k, (b, m) in enumerate(zip(boards, maps)):
        placed = {slot: (pid, rot) for pid, (slot, rot) in sol.placements[k].items()}
        for s in b.slots:
            cls = m.cls[s.y][s.x]
            if cls not in ("tn", "tw"):
                continue
            pid, rot = placed[s.id]
            assert sol.pieces[pid].cls == cls
            assert rot == (180 if cls == "tn" else 90), (k, s.x, s.y)
            assert flat_dirs(sol.pieces[pid].sides, rot) == frozenset(s.boundary_sides), (k, s.x, s.y)


def test_frame_class_needing_conflicting_sides_raises_naming_class_and_side():
    # "t" needs a side-S piece on A's top cell (@180) and a side-W piece on A's left cell (@0).
    # B's top cell is @0 (side N), so the same two pieces cannot serve B: three homes, two cells.
    a = "sea t@180 sea sea\nt@0 sea sea sea\nsea sea sea sea\nsea sea sea sea\nsea sea sea sea\n"
    b = "sea t@0 sea sea\nt@0 sea sea sea\nsea sea sea sea\nsea sea sea sea\nsea sea sea sea\n"
    boards = [square_board(4, 5, rotation="quarter")] * 3
    maps = parse_text(f"{a}\n{b}\n{a}")
    with pytest.raises(SceneError, match=r"class 't'.*map B cell \(1,0\).*N side"):
        pieces_from_scenes(boards, maps)


def test_one_frame_piece_serves_a_top_cell_and_a_left_cell():
    # "u" is on the top edge at @180 in A and C, and on the left edge at @90 in B. Both need home S,
    # so one physical piece serves all three maps.
    a = "sea u@180 sea sea\nsea sea sea sea\nsea sea sea sea\nsea sea sea sea\nsea sea sea sea\n"
    b = "sea sea sea sea\nu@90 sea sea sea\nsea sea sea sea\nsea sea sea sea\nsea sea sea sea\n"
    c = "sea sea u@180 sea\nsea sea sea sea\nsea sea sea sea\nsea sea sea sea\nsea sea sea sea\n"
    boards = [square_board(4, 5, rotation="quarter")] * 3
    maps = parse_text(f"{a}\n{b}\n{c}")
    pieces = pieces_from_scenes(boards, maps)
    assert [(p.cls, p.home) for p in pieces if p.cls == "u"] == [("u", "S")]
    _every_cell_fits(boards, maps, pieces)
