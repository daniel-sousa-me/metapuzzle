"""Algebraic constructions of three placements with minimal mating classes, as metapuzzle Solutions.

Library + check: python3 experiments/012-constructive-placements/construct.py
Every construction is verified with metapuzzle.connectors.class_summary (classes, false fits),
metapuzzle.metrics.shared_adjacencies and optimize.validate_solution.

Constructions (pieces are named by their cell in placement A, so A is the identity):
- product_standard(cols, rows): standard border, rotation none. P_k(i, j) = (alpha_k(i), beta_k(j)),
  alpha / beta exact 1D frame orderings (oned.sequence). Exact K(3,3) everywhere when
  cols, rows = 1 mod 3 and >= 7.
- group_tray(cols, rows, hh, hv): tray, rotation none (experiment 010 generalized). Piece g in Z_c x Z_r
  sits at phi_k^{-1}(g) with phi_k = [e1 + k hh | e2 + k hv], hh, hv of order 3. Classes are K(3,3)
  minus the contacts that would wrap around (tray boundary).
- checkerboard_standard(cols, rows, orbits): standard border, rotation none, cols, rows = 1 mod 6.
  Cells with x + y even never move; the other cells are grouped into triples (orbits) whose pieces
  cycle: piece at orbit[j] in A sits at orbit[j + k] in placement k. Any grouping is exact as long as
  frame triples stay on one side.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from metapuzzle.board import square_board  # noqa: E402
from metapuzzle.connectors import class_summary  # noqa: E402
from metapuzzle.metrics import PAIR_INDEX, shared_adjacencies  # noqa: E402
from metapuzzle.optimize import Solution, validate_solution  # noqa: E402
from metapuzzle.pieces import Piece, default_sides  # noqa: E402

import oned  # noqa: E402


def cell_pieces(board, connectors="asym", allowed=frozenset({0})):
    """One piece per cell of `board` (piece id = slot id), typed by the cell (standard frame or tray)."""
    out = []
    for s in board.slots:
        shape = s.kind if board.border == "standard" else "interior"
        home = s.home if board.border == "standard" else None
        out.append(Piece(s.id, shape, "any", allowed, home, default_sides(shape, home, connectors)))
    return out


def solution_from_maps(board, maps, pieces=None):
    """maps[k][cell_of_A] = (cell, rotation) in placement k; pieces default to cell_pieces(board)."""
    pieces = pieces or cell_pieces(board)
    placements = [{p.piece_id: tuple(maps[k][p.piece_id]) for p in pieces} for k in range(3)]
    return Solution([board] * 3, pieces, placements)


# ---- standard border, rotation none: product of 1D sequences ------------------------------------

def product_maps(cols, rows):
    a, b = oned.sequence(cols), oned.sequence(rows)
    # a[k][position] = piece index along the row; invert: piece i -> position in ordering k
    pos_a = [{p: x for x, p in enumerate(a[k])} for k in range(3)]
    pos_b = [{p: y for y, p in enumerate(b[k])} for k in range(3)]
    # piece named by its A cell: A uses ordering 0, so A-cell (x, y) holds piece (a0[x], b0[y])
    maps = []
    for k in range(3):
        m = {}
        for y in range(rows):
            for x in range(cols):
                i, j = a[0][x], b[0][y]
                m[y * cols + x] = (pos_b[k][j] * cols + pos_a[k][i], 0)
        maps.append(m)
    return maps


def product_standard(cols, rows):
    board = square_board(cols, rows, "standard", "none")
    return solution_from_maps(board, product_maps(cols, rows))


# ---- tray, rotation none: group translations (010) -------------------------------------------

def order3(cols, rows):
    return [(a, b) for a in range(cols) for b in range(rows) if (a, b) != (0, 0) and (3 * a % cols, 3 * b % rows) == (0, 0)]


def group_params(cols, rows):
    """All (hh, hv) giving bijective phi_k and six distinct contact translations up to sign."""
    out = []
    for hh, hv in itertools.product(order3(cols, rows), repeat=2):
        hs = [((1 + k * hh[0]) % cols, (k * hh[1]) % rows) for k in range(3)]
        vs = [((k * hv[0]) % cols, (1 + k * hv[1]) % rows) for k in range(3)]
        canon = lambda u: min(u, ((-u[0]) % cols, (-u[1]) % rows))
        if len({canon(t) for t in hs + vs}) != 6:
            continue
        ok = True
        for h, v in zip(hs, vs):
            if len({((h[0] * x + v[0] * y) % cols, (h[1] * x + v[1] * y) % rows) for x in range(cols) for y in range(rows)}) != cols * rows:
                ok = False
        if ok:
            out.append((hh, hv))
    return out


def group_maps(cols, rows, hh, hv, shifts=((0, 0), (0, 0), (0, 0))):
    """Piece g (= A cell) sits in placement k at the cell c with phi_k(c - t_k) = g."""
    maps = []
    for k in range(3):
        h = ((1 + k * hh[0]) % cols, (k * hh[1]) % rows)
        v = ((k * hv[0]) % cols, (1 + k * hv[1]) % rows)
        tx, ty = shifts[k]
        m = {}
        for y in range(rows):
            for x in range(cols):
                g = ((h[0] * x + v[0] * y) % cols, (h[1] * x + v[1] * y) % rows)
                m[g[1] * cols + g[0]] = (((y + ty) % rows) * cols + (x + tx) % cols, 0)
        maps.append(m)
    # make A the identity by renaming pieces
    inv0 = {c: g for g, (c, _) in maps[0].items()}
    return [{inv0[c]: maps[k][g] for c, g in ((c, inv0[c]) for c in range(cols * rows))} for k in range(3)] if False else _rename(maps, cols * rows)


def _rename(maps, n):
    """Rename pieces so that placement 0 is the identity (piece id = its A cell)."""
    name = {g: maps[0][g][0] for g in range(n)}
    return [{name[g]: maps[k][g] for g in range(n)} for k in range(3)]


def group_tray(cols, rows, hh=None, hv=None):
    if hh is None:
        params = group_params(cols, rows)
        if not params:
            return None
        hh, hv = params[0]
    board = square_board(cols, rows, "tray", "none")
    return solution_from_maps(board, group_maps(cols, rows, hh, hv))


# ---- standard border, rotation none: fixed checkerboard + cycling triples -------------------

def default_orbits(cols, rows):
    """Moving (x + y odd) cells grouped into triples: each frame side and the interior separately,
    members a third of the list apart (so no two share a neighbour)."""
    groups = {"N": [], "S": [], "W": [], "E": [], "I": []}
    for y in range(rows):
        for x in range(cols):
            if (x + y) % 2 == 0:
                continue
            side = "N" if y == 0 else "S" if y == rows - 1 else "W" if x == 0 else "E" if x == cols - 1 else "I"
            groups[side].append(y * cols + x)
    orbits = []
    for cells in groups.values():
        if len(cells) % 3:
            raise ValueError("moving cells per side and in the interior must be multiples of 3 (cols, rows = 1 mod 6)")
        t = len(cells) // 3
        orbits += [(cells[i], cells[i + t], cells[i + 2 * t]) for i in range(t)]
    return orbits


def checkerboard_maps(cols, rows, orbits=None):
    orbits = orbits or default_orbits(cols, rows)
    maps = [{c: (c, 0) for c in range(cols * rows)} for _ in range(3)]
    for orb in orbits:
        for j, c in enumerate(orb):
            for k in range(3):
                maps[k][c] = (orb[(j + k) % 3], 0)
    return maps


def checkerboard_standard(cols, rows, orbits=None):
    board = square_board(cols, rows, "standard", "none")
    return solution_from_maps(board, checkerboard_maps(cols, rows, orbits))


# ---- checks -----------------------------------------------------------------------------------

def check(sol, m=6) -> dict:
    s = class_summary(sol)
    shared = [shared_adjacencies(sol.placements[i], sol.placements[j], sol.boards[i], sol.boards[j])[0] for i, j in PAIR_INDEX]
    fixed = sum(1 for p in sol.pieces if len({sol.placements[k][p.piece_id][0] for k in range(3)}) == 1)
    sizes = [r["size"] for r in s["per_class"]]
    complete = sum(1 for r in s["per_class"] if r["size"] == m and r["false"] == 0)
    return {
        "valid": not validate_solution(sol), "sides": s["sides"], "classes": s["classes"], "largest": s["size"]["max"],
        "smallest": s["size"]["min"], "complete": complete, "false": s["false_fits"], "ratio": s["false_ratio"],
        "shared": shared, "fixed": fixed, "sizes": sorted(set(sizes)),
    }


def row(name, r) -> str:
    return (f"| {name} | {'yes' if r['valid'] else 'NO'} | {r['sides']} | {r['classes']} | {r['sizes']} | {r['complete']} | "
            f"{r['false']} | {r['ratio']:.3f} | {'/'.join(map(str, r['shared']))} | {r['fixed']} |")


HEADER = ("| construction | valid | sides | classes | class sizes | complete minimal classes | false fits | ratio | shared AB/AC/BC | fixed pieces |\n"
          "|---|---|---|---|---|---|---|---|---|---|")


def main():
    lines = [HEADER]
    for c, r in [(7, 7), (10, 10), (13, 13), (19, 25), (22, 22), (16, 31)]:
        lines.append(row(f"product {c}x{r} standard none", check(product_standard(c, r))))
    for c, r in [(6, 6), (9, 9), (21, 24), (24, 21), (21, 21)]:
        sol = group_tray(c, r)
        if sol:
            lines.append(row(f"group {c}x{r} tray none ({len(group_params(c, r))} parameter sets)", check(sol)))
    for c, r in [(13, 13), (19, 25)]:
        lines.append(row(f"checkerboard {c}x{r} standard none", check(checkerboard_standard(c, r))))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
