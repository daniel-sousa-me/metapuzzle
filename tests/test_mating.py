"""Mating penalty: incremental bookkeeping, solver integration, CLI flags."""
import random

import pytest

from metapuzzle.board import square_board
from metapuzzle.cli import main
from metapuzzle.connectors import MatingPenalty, class_summary, mating_penalty, target_block_size
from metapuzzle.metrics import PAIR_INDEX, shared_adjacencies
from metapuzzle.optimize import Solution, solve, validate_solution
from metapuzzle.pieces import make_inventory


def brute_penalty(edges, m, hops=2):
    adj = {}
    for u, v in edges:
        adj.setdefault(u, set()).add(v)
        adj.setdefault(v, set()).add(u)
    total = 0
    for u in adj:
        ball, frontier = {u}, {u}
        for _ in range(hops):
            frontier = {y for x in frontier for y in adj[x]} - ball
            ball |= frontier
        total += max(0, len(ball) - m)
    return total


def test_target_block_size():
    assert target_block_size(["tab", "blank", "flat"]) == 6
    assert target_block_size(["andro", "flat"]) == 4


def test_perfect_blocks_have_zero_penalty():
    k33 = [(a, 10 + b) for a in range(3) for b in range(3)]
    k4 = [(a, b) for a in range(4) for b in range(a + 1, 4)]
    assert MatingPenalty(6).build(k33) == 0
    assert MatingPenalty(4).build(k4) == 0
    assert MatingPenalty(4).build(k33) == 6 * (6 - 4)  # K(3,3) is too big for andro


@pytest.mark.parametrize("hops", [2, 3])
def test_incremental_matches_rebuild(hops):
    rng = random.Random(5)
    nodes = list(range(40))
    live = []
    for _ in range(70):
        live.append(tuple(rng.sample(nodes, 2)))
    mp = MatingPenalty(4, hops)
    mp.build(live)
    assert mp.total == brute_penalty(live, 4, hops)
    for _ in range(300):
        k = min(rng.randint(1, 3), len(live))
        old = [live.pop(rng.randrange(len(live))) for _ in range(k)]
        new = [tuple(rng.sample(nodes, 2)) for _ in range(rng.randint(1, 3))]
        before = mp.total
        delta = mp.propose(old, new)
        if rng.random() < 0.5:
            mp.commit()
            live += new
            assert mp.total == before + delta
        else:
            mp.rollback()
            live += old
            assert mp.total == before
        assert mp.total == brute_penalty(live, 4, hops)
        assert sum(mp.f.values()) == mp.total and sorted(mp.bad) == sorted(mp.f)


def test_default_leaves_solver_unchanged():
    board = square_board(6, 6, "tray", "none")
    pieces = make_inventory(board)
    a = solve(board, pieces, seed=3, iters=2000)
    b = solve(board, pieces, seed=3, iters=2000, mating_weight=0.0)
    assert a.placements == b.placements and a.meta["mating_penalty"] is None


def run_tray(rotation, weight, seed=0, iters=40_000, **kw):
    board = square_board(6, 6, "tray", rotation)
    sol = solve(board, make_inventory(board), seed=seed, iters=iters, mating_weight=weight, **kw)
    assert validate_solution(sol) == []
    return sol


def max_shared_fraction(sol):
    return max(
        shared_adjacencies(sol.placements[i], sol.placements[j], sol.boards[i], sol.boards[j])[0]
        / min(sol.boards[i].n_adjacencies, sol.boards[j].n_adjacencies)
        for i, j in PAIR_INDEX
    )


@pytest.mark.parametrize("rotation", ["none", "quarter"])
def test_mating_on_shrinks_classes_and_false_fits(rotation):
    off = run_tray(rotation, 0.0)
    on = run_tray(rotation, 1.0)
    s_off, s_on = class_summary(off), class_summary(on)
    assert s_on["size"]["max"] < s_off["size"]["max"]
    assert s_on["false_ratio"] < s_off["false_ratio"]
    assert mating_penalty(on) < mating_penalty(off)
    assert on.meta["mating_penalty"] == mating_penalty(on) and on.meta["mating_hops"] == 3
    assert 0 < max_shared_fraction(on) <= 0.10 and max_shared_fraction(off) == 0


def test_shared_fraction_guard_is_respected():
    sol = run_tray("none", 1.0, iters=30_000, max_shared_fraction=0.05)
    assert max_shared_fraction(sol) <= 0.05
    assert sol.meta["max_shared_fraction"] == 0.05


@pytest.mark.parametrize("rotation", ["none", "quarter"])
def test_mating_with_standard_border_and_seam_pieces_stays_valid(rotation):
    # mixed frames: surplus flat-sided pieces sit inside as seams (the solver's strict-layout branch)
    boards = [square_board(c, r, "standard", rotation) for c, r in [(8, 12), (12, 8), (16, 6)]]
    sol = solve(boards, make_inventory(boards), seed=1, iters=20_000, mating_weight=1.0)
    assert validate_solution(sol) == [] and max_shared_fraction(sol) <= 0.10
    assert sol.meta["mating_penalty"] == mating_penalty(sol)


def test_cli_solve_mating_flags(tmp_path, capsys):
    out = tmp_path / "s.json"
    assert main(["solve", "--cols", "5", "--rows", "4", "--border", "tray", "--iters", "3000",
                 "--mating-weight", "1", "--max-shared-fraction", "0.1", "--out", str(out)]) == 0
    meta = Solution.load(out).meta
    assert meta["mating_weight"] == 1.0 and meta["max_shared_fraction"] == 0.1 and meta["mating_penalty"] is not None
    assert "mating penalty" in capsys.readouterr().out


def test_prototype_summary_has_connectors_section(tmp_path):
    from metapuzzle.classes import SAMPLE_SPEC_PATH
    from metapuzzle.prototype import run_prototype
    from test_prototype import TINY_SCENES

    scenes = tmp_path / "tiny.txt"
    scenes.write_text(TINY_SCENES)
    res = run_prototype(scenes, SAMPLE_SPEC_PATH, tmp_path / "out", iters=3000, mating_weight=1.0)
    text = (tmp_path / "out" / "summary.md").read_text()
    assert res["valid"] and "## Connectors" in text and "mating classes:" in text and "false fits:" in text
    assert "mating_weight: 1.0" in text
