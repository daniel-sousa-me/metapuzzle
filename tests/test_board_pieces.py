import pytest

from metapuzzle.board import mates, square_board
from metapuzzle.pieces import Piece, make_inventory, rotations_for_piece


def test_standard_20x25_counts():
    b = square_board(20, 25)
    assert b.kind_counts() == {"corner": 4, "edge": 82, "interior": 414}
    assert b.n_adjacencies == 955 == len(b.adjacencies)
    assert b.n_slots == 500


def test_tray_all_interior():
    b = square_board(10, 8, "tray")
    assert b.kind_counts() == {"corner": 0, "edge": 0, "interior": 80}
    assert all(s.type == "interior" for s in b.slots)


def test_neighbors_four_connected():
    b = square_board(5, 4)
    assert len(b.slots[0].neighbors) == 2
    assert len(b.slots[1].neighbors) == 3
    assert len(b.slots[b.slot_at(2, 2)].neighbors) == 4


def test_slot_types():
    b = square_board(6, 5)
    assert b.slots[0].type == "corner_NW"
    assert b.slots[5].type == "corner_NE"
    assert b.slots[b.slot_at(0, 4)].type == "corner_SW"
    assert b.slots[b.slot_at(5, 4)].type == "corner_SE"
    assert b.slots[2].type == "edge_N" and b.slots[b.slot_at(0, 2)].type == "edge_W"


def test_bad_params():
    with pytest.raises(ValueError):
        square_board(1, 5)
    with pytest.raises(ValueError):
        square_board(5, 5, border="x")


def test_mates():
    assert mates("tab", "blank") and mates("flat", "flat") and mates("andro", "andro")
    assert not mates("tab", "tab") and not mates("flat", "tab") and not mates("wild", "flat")
    assert mates("wild", "tab")


def test_no_rotation_compat():
    b = square_board(6, 5)
    inv = make_inventory(b)
    corner_nw = next(p for p in inv if p.home == "NW" and p.shape_type == "corner")
    assert rotations_for_piece(b, corner_nw, 0) == (0,)
    assert rotations_for_piece(b, corner_nw, 5) == ()  # NE corner slot
    edge_n = next(p for p in inv if p.shape_type == "edge" and p.home == "N")
    assert rotations_for_piece(b, edge_n, 2) == (0,)
    assert rotations_for_piece(b, edge_n, b.slot_at(0, 2)) == ()
    interior = next(p for p in inv if p.shape_type == "interior")
    assert rotations_for_piece(b, interior, b.slot_at(2, 2)) == (0,)
    assert rotations_for_piece(b, interior, 2) == ()


def test_quarter_compat_implies_orientation():
    b = square_board(6, 5, rotation="quarter")
    inv = make_inventory(b)
    edge = next(p for p in inv if p.shape_type == "edge")  # flat side N upright
    assert rotations_for_piece(b, edge, 2) == (0,)
    assert rotations_for_piece(b, edge, b.slot_at(5, 2)) == (90,)
    assert rotations_for_piece(b, edge, b.slot_at(2, 4)) == (180,)
    assert rotations_for_piece(b, edge, b.slot_at(0, 2)) == (270,)
    corner = next(p for p in inv if p.shape_type == "corner")
    assert rotations_for_piece(b, corner, 0) == (0,)
    assert rotations_for_piece(b, corner, 5) == (90,)
    interior = next(p for p in inv if p.shape_type == "interior")
    assert rotations_for_piece(b, interior, b.slot_at(2, 2)) == (0, 90, 180, 270)


def test_inventory_counts():
    b = square_board(20, 25)
    inv = make_inventory(b)
    assert len(inv) == 500
    assert sum(p.shape_type == "corner" for p in inv) == 4
    assert sum(p.shape_type == "edge" for p in inv) == 82
    assert len({p.piece_id for p in inv}) == 500


def test_extra_flat_and_free_corners():
    b = square_board(10, 8)
    inv = make_inventory(b, extra_flat_pieces=4, free_corners=True)
    assert len(inv) == 80
    assert sum(p.shape_type == "edge" for p in inv) == 28 + 4
    corners = [p for p in inv if p.shape_type == "corner"]
    assert all(p.allowed_rotations == {0, 90, 180, 270} for p in corners)
    assert all(len(rotations_for_piece(b, corners[0], s)) == 1 for s in (0, 9, 70, 79))


def test_inventory_for_mixed_boards():
    bs = [square_board(c, r) for c, r in [(8, 12), (12, 8), (16, 6)]]
    inv = make_inventory(bs)
    assert len(inv) == 96
    assert sum(p.shape_type == "edge" and p.home == "N" for p in inv) == 14
    assert sum(p.shape_type == "edge" and p.home == "W" for p in inv) == 10
    with pytest.raises(ValueError):
        make_inventory([square_board(8, 12), square_board(10, 10)])


def test_piece_validation():
    with pytest.raises(ValueError):
        Piece(0, "interior", allowed_rotations=frozenset({45}))
