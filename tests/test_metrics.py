import pytest

from metapuzzle.board import square_board
from metapuzzle.metrics import (
    PIECE_GATES,
    components,
    corner_order,
    familiarity,
    format_report,
    piece_gates,
    report,
    shared_adjacencies,
    shared_fraction,
    transferable_clusters,
)
from metapuzzle.optimize import Solution, solve
from metapuzzle.pieces import make_inventory


def place(order, cols=3):
    """order[i] = piece id in slot i"""
    return {p: (s, 0) for s, p in enumerate(order)}


B = square_board(3, 2, "tray")  # slots 0 1 2 / 3 4 5; 7 adjacencies


def test_identical_placements_share_everything():
    a = place([0, 1, 2, 3, 4, 5])
    count, pairs = shared_adjacencies(a, a, B)
    assert count == 7 == len(pairs)
    assert shared_fraction(a, a, B) == 1.0


def test_hand_built_example():
    a = place([0, 1, 2, 3, 4, 5])
    b = place([0, 1, 3, 2, 5, 4])  # row 0: 0 1 3 / row 1: 2 5 4
    count, pairs = shared_adjacencies(a, b, B)
    # A edges: 01 12 34 45 03 14 25 ; B edges: 01 13 25 54 02 15 34
    expected = {(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)} & {(0, 1), (1, 3), (2, 5), (4, 5), (0, 2), (1, 5), (3, 4)}
    assert set(pairs) == expected
    assert count == len(expected) == 4


def test_cross_board_comparison():
    b32 = square_board(3, 2, "tray")
    b23 = square_board(2, 3, "tray")
    a = place([0, 1, 2, 3, 4, 5])
    c = {p: (s, 0) for s, p in enumerate([0, 1, 2, 3, 4, 5])}  # 2x3: rows 0 1 / 2 3 / 4 5
    count, pairs = shared_adjacencies(a, c, b32, b23)
    # edges of 2x3: 01 23 45 02 13 24 35 ; of 3x2: 01 12 34 45 03 14 25 -> common: 01 45
    assert pairs == [(0, 1), (4, 5)]


def test_familiarity_and_clusters():
    a = place([0, 1, 2, 3, 4, 5])
    b = place([0, 1, 2, 4, 3, 5])
    fam = familiarity(a, b, B)
    count, pairs = shared_adjacencies(a, b, B)
    assert sum(fam.values()) == 2 * count
    assert transferable_clusters([(0, 1), (1, 2), (5, 6)]) == [[0, 1, 2]]
    assert components([(0, 1), (5, 6)]) == [[0, 1], [5, 6]]
    assert transferable_clusters([(0, 1), (5, 6)]) == []


def test_corner_order_classes():
    b = square_board(4, 3, "standard")
    corners = [0, 3, 11, 8]
    pl = {i: (s, 0) for i, s in enumerate(range(12))}
    pl = {p: (corners[p], 0) for p in range(4)}
    for p, s in zip(range(4, 12), [s for s in range(12) if s not in corners]):
        pl[p] = (s, 0)
    assert corner_order(pl, b) == (0, 1, 2, 3)
    # rotating the whole board (corners cycle) keeps the class
    pl2 = {p: (corners[(p + 1) % 4], 0) for p in range(4)} | {p: pl[p] for p in range(4, 12)}
    assert corner_order(pl2, b) == (0, 1, 2, 3)
    pl3 = {p: (corners[(-p) % 4], 0) for p in range(4)} | {p: pl[p] for p in range(4, 12)}
    assert corner_order(pl3, b) == (0, 3, 2, 1)


def test_report_dict_and_text():
    boards = [B, B, B]
    pieces = make_inventory(B)
    a = place(list(range(6)))
    sol = Solution(boards, pieces, [a, a, place([0, 1, 3, 2, 5, 4])], None, {"seed": 0})
    rep = report(sol)
    assert rep["pairs"]["AB"]["shared"] == 7
    assert rep["pairs"]["AC"]["shared"] == 4
    assert rep["total_shared"] == 7 + 4 + 4
    assert rep["pairs"]["AB"]["largest_component"] == 6
    assert "AB: shared=7" in rep["text"] and rep["text"] == format_report(rep)


BIG = square_board(10, 8, "standard")  # 80 pieces, 142 adjacencies


def _stride(k):
    return {p: ((p * k) % 80, 0) for p in range(80)}


def _chain():
    """Pieces 0-3 keep slots 0-3 (a row of four); the others are scattered by a stride."""
    pl = {p: (p, 0) for p in range(4)}
    for i, p in enumerate(range(4, 80)):
        pl[p] = (4 + (3 * i) % 76, 0)
    return pl


def _solution(placements):
    return Solution([BIG, BIG, BIG], make_inventory(BIG), placements, None, {})


def test_piece_gates_pass_on_solver_output():
    sol = solve([BIG, BIG, BIG], make_inventory(BIG), None, seed=0)
    assert piece_gates(sol) == (True, [])
    assert report(sol)["text"].splitlines()[-1] == "piece gates: PASS"


def test_piece_gates_fail_on_a_shared_cluster_of_four_or_more():
    ident = {p: (p, 0) for p in range(80)}
    sol = _solution([ident, _stride(3), _chain()])
    # 4 shared adjacencies (2.8% < 5%) form one run of five pieces: only the cluster gate fails
    assert piece_gates(sol) == (False, ["AC largest shared cluster 5 pieces ≥ 4"])
    rep = report(sol)
    assert rep["gates"] == {"ok": False, "failures": ["AC largest shared cluster 5 pieces ≥ 4"]}
    assert rep["text"].splitlines()[-1] == "piece gates: FAIL (AC largest shared cluster 5 pieces ≥ 4)"


def test_piece_gates_fail_on_shared_fraction():
    ident = {p: (p, 0) for p in range(80)}
    ok, failures = piece_gates(_solution([ident, ident, _stride(3)]))
    assert not ok
    assert "AB shared 100.0% ≥ 5%" in failures


def test_piece_gate_limits_are_a_tunable_dict(monkeypatch):
    assert PIECE_GATES == {"shared_fraction_below": 0.05, "largest_cluster_below": 4}
    ident = {p: (p, 0) for p in range(80)}
    sol = _solution([ident, _stride(3), _chain()])
    monkeypatch.setitem(PIECE_GATES, "largest_cluster_below", 6)
    assert piece_gates(sol) == (True, [])
