import json

from metapuzzle.board import mates, square_board
from metapuzzle.cli import main
from metapuzzle.connectors import class_summary, contacts, false_fit_count, mating_classes
from metapuzzle.metrics import shared_adjacencies
from metapuzzle.optimize import Solution, solve
from metapuzzle.pieces import Piece, make_inventory

ALL_ROTS = frozenset({0, 90, 180, 270})


def make_solution(boards, sides_by_piece, placements):
    """sides_by_piece[pid] = (N, E, S, W) profiles; placements as in solution JSON (pid -> (slot, rot))."""
    pieces = [Piece(pid, "interior", allowed_rotations=ALL_ROTS, sides=s) for pid, s in sorted(sides_by_piece.items())]
    return Solution(boards=list(boards), pieces=pieces, placements=[dict(p) for p in placements])


def brute_false_fits(sol):
    """Independent count: possible tab-blank pairs on different pieces, minus distinct actual contacts."""
    c = contacts(sol)
    actual = {(min(u, v), max(u, v)) for u, v in c.edges}
    total = 0
    for comp in mating_classes(sol):
        for u in comp:
            for v in comp:
                if u < v and u[0] != v[0] and mates(c.profile[u], c.profile[v]) and (u, v) not in actual:
                    total += 1
    return total


def test_identical_placements_2x2_give_classes_of_two():
    board = square_board(2, 2, "standard", "none")
    pieces = make_inventory(board)  # four corner pieces, asym connectors with flats on the border
    order = {p.home: p.piece_id for p in pieces}
    placement = {order[h]: (s, 0) for s, h in enumerate(["NW", "NE", "SW", "SE"])}
    sol = Solution(boards=[board] * 3, pieces=pieces, placements=[placement] * 3)
    classes = mating_classes(sol)
    assert len(classes) == 4 and all(len(c) == 2 for c in classes)
    s = class_summary(sol)
    assert s["sides"] == 8 and s["edges"] == 12 and s["flat_contacts"] == 0
    assert s["false_fits"] == 0 and s["edge_identity_ok"]


def test_disjoint_adjacencies_give_classes_of_at_least_six():
    board = square_board(8, 8, "standard", "none")
    boards = [board] * 3
    sol = solve(boards, make_inventory(boards), seed=0)
    assert sol.meta["valid"] and sum(sol.meta["shared"].values()) == 0  # the premise of the test
    c = contacts(sol)
    degree = {n: 0 for n in c.nodes}
    for u, v in c.edges:
        degree[u] += 1
        degree[v] += 1
    assert set(degree.values()) == {3}  # every non-flat side touches once per solution
    for comp in mating_classes(sol):
        tabs = sum(1 for n in comp if c.profile[n] == "tab")
        assert tabs >= 3 and len(comp) - tabs >= 3 and len(comp) >= 6  # bipartite, minimum degree 3


def test_edges_equal_intended_minus_flat_contacts():
    # tray 2x2: p3 is all flat, so two contacts per solution are flat seams
    board = square_board(2, 2, "tray", "none")
    tab_blank = ("blank", "tab", "tab", "blank")
    sides = {0: tab_blank, 1: tab_blank, 2: tab_blank, 3: ("flat",) * 4}
    placement = {0: (0, 0), 1: (1, 0), 2: (2, 0), 3: (3, 0)}
    sol = make_solution([board] * 3, sides, [placement] * 3)
    c = contacts(sol)
    assert c.flat_contacts == 6 and c.intended == 12 and len(c.edges) == 6
    assert len(c.edges) == c.intended - c.flat_contacts
    assert class_summary(sol)["edge_identity_ok"]


def test_solved_board_edge_identity_and_false_fits_match_brute_force():
    board = square_board(8, 8, "standard", "none")
    boards = [board] * 3
    sol = solve(boards, make_inventory(boards), seed=0)
    s = class_summary(sol)
    assert s["edge_identity_ok"] and s["mismatched"] == 0
    assert s["edges"] == 3 * board.n_adjacencies - s["flat_contacts"]
    assert false_fit_count(sol)["total"] == brute_false_fits(sol) == s["false_fits"]


def test_rotation_moves_contact_to_rotated_side():
    # 1x2 tray: piece 0 above piece 1. Rotated 90 clockwise, its E side faces south.
    board = square_board(1, 2, "tray", "quarter")
    sides = {0: ("blank", "tab", "blank", "blank"), 1: ("blank", "blank", "blank", "blank")}
    sol = make_solution([board], sides, [{0: (0, 90), 1: (1, 0)}])
    c = contacts(sol)
    assert c.edges == [((0, 1), (1, 0))] or c.edges == [((1, 0), (0, 1))]
    assert c.profile[(0, 1)] == "tab" and c.profile[(1, 0)] == "blank"
    assert mating_classes(sol) == [[(0, 1), (1, 0)]]


def test_cli_connectors_prints_summary(tmp_path, capsys):
    board = square_board(8, 8, "standard", "none")
    boards = [board] * 3
    path = tmp_path / "sol.json"
    solve(boards, make_inventory(boards), seed=0).save(path)
    capsys.readouterr()
    assert main(["connectors", str(path)]) == 0
    out = capsys.readouterr().out
    assert "mating classes:" in out and "false fits:" in out and "edge identity" in out
    assert "FAILED" not in out
    assert json.loads(path.read_text())["format"] == "metapuzzle-solution"
