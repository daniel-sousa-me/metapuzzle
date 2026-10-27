"""Round 2: does the mating penalty shrink the mating classes? Prints markdown tables.

Run from anywhere: python3 experiments/010-connector-classes/round2.py [--iters N] [--jobs J] [--out FILE]
Each case is solved with the mating penalty off, and on with max shared fraction 0.05 and 0.10, same
seed and iteration budget. Columns: mating classes (connected components of the side-mating graph),
largest class, share of sides that sit in a class of at most m sides (m = 6 for tab/blank, 4 for
andro; the K(3,3) / K4 target), false-fit ratio (false fits / intended contacts), shared adjacencies
per pair, solver wall time. Times are measured with several runs in parallel on a shared machine.

The last table is a proof of concept for the joint construction of the three tray solutions
(group translations); it is not part of the solver.
"""
from __future__ import annotations

import argparse
import itertools
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from metapuzzle.board import square_board  # noqa: E402
from metapuzzle.classes import load_class_spec  # noqa: E402
from metapuzzle.connectors import class_summary, mating_penalty  # noqa: E402
from metapuzzle.metrics import PAIR_INDEX, shared_adjacencies  # noqa: E402
from metapuzzle.optimize import Solution, solve, validate_solution  # noqa: E402
from metapuzzle.pieces import make_inventory  # noqa: E402
from metapuzzle.prototype import _allowed_rotations  # noqa: E402
from metapuzzle.scene import load_scenes, pieces_from_scenes  # noqa: E402

HYBRID = ROOT / "experiments/005-hybrid-tones"
CASES = [
    # name, kind, cols, rows, border, rotation
    ("10x8 tray none", "plain", 10, 8, "tray", "none"),
    ("10x8 tray quarter", "plain", 10, 8, "tray", "quarter"),
    ("25x20 standard none", "plain", 25, 20, "standard", "none"),
    ("25x20 standard quarter", "plain", 25, 20, "standard", "quarter"),
    ("005 scenes-v3 20x25 quarter", "scenes", 20, 25, "standard", "quarter"),
]
SETTINGS = [("off", 0.0, None), ("on, max shared 0.05", 1.0, 0.05), ("on, max shared 0.10", 1.0, 0.10)]


def build(kind: str, cols: int, rows: int, border: str, rotation: str):
    if kind == "scenes":
        maps = load_scenes(HYBRID / "scenes-v3.txt")
        boards = [square_board(m.cols, m.rows, border, rotation) for m in maps]
        spec = load_class_spec(HYBRID / "classes.json")
        rots = {cls: _allowed_rotations(spec, cls, rotation) for cls in maps[0].histogram()}
        return boards, pieces_from_scenes(boards, maps, allowed_rotations=rots), maps
    board = square_board(cols, rows, border, rotation)
    return board, make_inventory(board), None


def summarize(sol: Solution, m: int) -> dict:
    s = class_summary(sol)
    small = sum(r["size"] for r in s["per_class"] if r["size"] <= m)
    shared = [shared_adjacencies(sol.placements[i], sol.placements[j], sol.boards[i], sol.boards[j])[0] for i, j in PAIR_INDEX]
    fracs = [
        c / min(sol.boards[i].n_adjacencies, sol.boards[j].n_adjacencies) for c, (i, j) in zip(shared, PAIR_INDEX)
    ]
    return {
        "classes": s["classes"], "max": s["size"]["max"], "small": small / s["sides"], "ratio": s["false_ratio"],
        "shared": shared, "max_frac": max(fracs), "valid": not validate_solution(sol),
    }


def job(args):
    (name, kind, cols, rows, border, rotation), (label, weight, cap), iters, seed = args
    boards, pieces, maps = build(kind, cols, rows, border, rotation)
    t0 = time.perf_counter()
    sol = solve(boards, pieces, maps, seed=seed, iters=iters, mating_weight=weight, max_shared_fraction=cap)
    wall = time.perf_counter() - t0
    row = summarize(sol, 4 if rotation == "quarter" else 6)
    row.update(name=name, label=label, wall=wall, penalty=mating_penalty(sol), iters_used=sol.meta["iters_used"])
    return row


def table(rows: list[dict]) -> str:
    out = [
        "| case | mating | classes | largest class | sides in classes <= m | false-fit ratio | shared AB/AC/BC (max %) | wall s | valid |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(
            f"| {r['name']} | {r['label']} | {r['classes']} | {r['max']} | {100 * r['small']:.0f}% | {r['ratio']:.1f} | "
            f"{'/'.join(map(str, r['shared']))} ({100 * r['max_frac']:.1f}) | {r['wall']:.0f} | {'yes' if r['valid'] else 'NO'} |"
        )
    return "\n".join(out)


# ---- joint construction of three tray solutions (proof of concept) --------------------------------

def construct_tray_none(cols: int, rows: int):
    """Three tray placements whose side-mating classes are all K(3,3) or subsets, or None.

    Pieces are the elements of G = Z_cols x Z_rows. Solution k puts piece M_k (x, y) mod (cols, rows) at
    cell (x, y), M_k a 2x2 integer matrix that is bijective on G. A piece then touches piece u + h_k on its
    east side and u + v_k on its south side (h_k, v_k the columns of M_k). When {h_k} and {v_k} are cosets
    of subgroups of order 3, every N side meets the S sides of one coset of v-translates, so each class
    is K(3,3): the three solutions are three perfect matchings of the same block (a 1-factorization).
    Needs 3 | cols * rows. Contacts that would wrap around the group are simply not contacts.
    """
    order3 = [(a, b) for a in range(cols) for b in range(rows)
              if (a, b) != (0, 0) and ((3 * a) % cols, (3 * b) % rows) == (0, 0)]
    if not order3:
        return None

    def add(u, v):
        return ((u[0] + v[0]) % cols, (u[1] + v[1]) % rows)

    def bijective(cols_xy):
        h, v = cols_xy
        seen = {((h[0] * x + v[0] * y) % cols, (h[1] * x + v[1] * y) % rows) for x in range(cols) for y in range(rows)}
        return len(seen) == cols * rows

    def canon(u):
        n = ((-u[0]) % cols, (-u[1]) % rows)
        return min(u, n)

    for h0, v0 in (((1, 0), (0, 1)), ((0, 1), (1, 0))):
        for hh, hv in itertools.product(order3, order3):
            for perm in ((0, 1, 2), (0, 2, 1)):
                maps = []
                for j in perm:
                    h, v = h0, v0
                    for _ in range(j):
                        h, v = add(h, hh), add(v, hv)
                    maps.append((h, v))
                if len({canon(t) for hv_ in maps for t in hv_}) == 6 and all(bijective(m) for m in maps):
                    return maps
    return None


def constructed_solution(cols: int, rows: int):
    maps = construct_tray_none(cols, rows)
    if maps is None:
        return None
    board = square_board(cols, rows, "tray", "none")
    pieces = make_inventory(board)
    placements = []
    for h, v in maps:
        pl = {}
        for x in range(cols):
            for y in range(rows):
                g = ((h[0] * x + v[0] * y) % cols, (h[1] * x + v[1] * y) % rows)
                pl[pieces[g[0] * rows + g[1]].piece_id] = (y * cols + x, 0)
        placements.append(pl)
    return Solution([board] * 3, pieces, placements)


def construction_rows(sizes) -> list[dict]:
    rows = []
    for cols, rows_ in sizes:
        t0 = time.perf_counter()
        sol = constructed_solution(cols, rows_)
        wall = time.perf_counter() - t0
        if sol is None:
            continue
        r = summarize(sol, 6)
        r.update(name=f"{cols}x{rows_} tray none", label="joint construction", wall=wall)
        rows.append(r)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=300_000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--out", help="also write the tables here")
    a = ap.parse_args()
    jobs = [(c, s, a.iters, a.seed) for c in CASES for s in SETTINGS]
    with Pool(a.jobs) as pool:
        rows = pool.map(job, jobs, chunksize=1)
    text = f"Solver, {a.iters} iterations, seed {a.seed}.\n\n" + table(rows)
    cons = construction_rows([(6, 6), (9, 9), (10, 9), (12, 9), (24, 20), (21, 24), (30, 16)])
    text += "\n\nJoint construction (no search; see `construct_tray_none`).\n\n" + table(cons)
    print(text)
    if a.out:
        Path(a.out).write_text(text + "\n")


if __name__ == "__main__":
    main()
