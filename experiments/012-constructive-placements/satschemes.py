"""SAT search for three placements whose mating classes are all minimal (K(3,3) or K4).

Run: python3 experiments/012-constructive-placements/satschemes.py   (needs `pip install python-sat`)

Model. Pieces are the cells of placement A (identity, rotation 0; no loss of generality).
Placements B and C are searched. A side is (piece, upright side index). Exact minimal classes:
- every side used in A is used in B and C, and unused sides stay unused (they face the wall);
- K(3,3) sides (rotation none; ring sides of a standard frame in quarter mode, cw = tab):
  with A's partner beta(u) of a tab u and alpha(v) of a blank v,
  B(u)=v => C(alpha(v)) = beta(u);  C(u)=w => B(alpha(w)) = beta(u);  B(u)=v & C(u)=w => B(alpha(v)) = w.
  These force each block {a1,a2,a3} x {b1,b2,b3} to be closed with a Latin square of partners.
- K4 sides (andro, quarter): B(u)=v => B(beta u) = beta v and C(u) = beta v (Klein structure).
Options: forbid pieces that sit in the same cell in all three placements; forbid shared adjacency.
"""
from __future__ import annotations

import argparse
import itertools
import sys
import time

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Cadical153, Glucose4

DELTA = ((0, -1), (1, 0), (0, 1), (-1, 0))  # N E S W


class Grid:
    def __init__(self, cols, rows, topo):
        self.cols, self.rows, self.topo = cols, rows, topo
        self.N = cols * rows

    def nb(self, c, d):
        x, y = c % self.cols, c // self.cols
        dx, dy = DELTA[d]
        x2, y2 = x + dx, y + dy
        if self.topo == "torus":
            return (y2 % self.rows) * self.cols + (x2 % self.cols)
        if 0 <= x2 < self.cols and 0 <= y2 < self.rows:
            return y2 * self.cols + x2
        return None

    def wall(self, c):
        return frozenset(d for d in range(4) if self.nb(c, d) is None)


def search(cols, rows, topo, mode, no_fixed=False, no_shared=False, seed=0, verbose=True, maps=None, timeout=None):
    g = Grid(cols, rows, topo)
    N = g.N
    pool = IDPool()
    s = Cadical153() if not timeout else Glucose4()
    rots = (0,) if mode == "none" else (0, 1, 2, 3)
    # flats (standard) / dead sides (tray): the upright sides facing the wall in A
    dead = {p: g.wall(p) if topo != "torus" else frozenset() for p in range(N)}

    def fits(p, c, q, k=None):
        # the sides facing the wall at c must be exactly p's dead sides rotated by q; classes must match
        if maps is not None and k is not None and maps[k][c] != maps[0][p]:
            return False
        return frozenset((i + q) % 4 for i in dead[p]) == g.wall(c)

    X = {}
    for k in (1, 2):
        for p in range(N):
            for c in range(N):
                for q in rots:
                    if fits(p, c, q, k):
                        X[k, p, c, q] = pool.id(("x", k, p, c, q))
    for k in (1, 2):
        for p in range(N):
            lits = [X[k, p, c, q] for c in range(N) for q in rots if (k, p, c, q) in X]
            for cl in CardEnc.equals(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses:
                s.add_clause(cl)
        for c in range(N):
            lits = [X[k, p, c, q] for p in range(N) for q in rots if (k, p, c, q) in X]
            for cl in CardEnc.equals(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses:
                s.add_clause(cl)
    used = [(p, i) for p in range(N) for i in range(4) if i not in dead[p]]
    # partner in A
    beta = {}
    for p in range(N):
        for d in range(4):
            c2 = g.nb(p, d)
            if c2 is not None:
                beta[(p, d)] = (c2, (d + 2) % 4)
    # side kinds: ring sides of a frame piece (both neighbours along the boundary) are bipartite
    def kind(u):
        p, i = u
        if mode == "none":
            return "h" if i in (1, 3) else "v"
        if topo == "standard" and dead[p]:
            if len(dead[p]) == 2 or (i + 2) % 4 not in dead[p]:
                return "ring"
        return "k4"

    def is_tab(u):  # tab side of a bipartite pair
        p, i = u
        if mode == "none":
            return i in (1, 2)
        f = dead[p]
        if len(f) == 1:
            (h,) = f
            return i == (h + 1) % 4
        h = next(d for d in f if (d + 1) % 4 in f)
        return i == (h + 2) % 4

    T = {}

    def tv(k, u, v):
        key = (k,) + tuple(sorted((u, v)))
        if key not in T:
            T[key] = pool.id(("t",) + key)
        return T[key]

    # contacts implied by placements
    for k in (1, 2):
        for c in range(N):
            for d in (1, 2):
                c2 = g.nb(c, d)
                if c2 is None:
                    continue
                for p in range(N):
                    for q in rots:
                        if (k, p, c, q) not in X:
                            continue
                        u = (p, (d - q) % 4)
                        for p2 in range(N):
                            if p2 == p:
                                continue
                            for q2 in rots:
                                if (k, p2, c2, q2) not in X:
                                    continue
                                v = (p2, (d + 2 - q2) % 4)
                                if kind(u) != kind(v) or (kind(u) in ("h", "v", "ring") and is_tab(u) == is_tab(v)):
                                    s.add_clause([-X[k, p, c, q], -X[k, p2, c2, q2]])
                                    continue
                                s.add_clause([-X[k, p, c, q], -X[k, p2, c2, q2], tv(k, u, v)])
    # each used side has exactly one partner per placement
    by_side = {u: {1: [], 2: []} for u in used}
    for (k, a, b), var in T.items():
        by_side[a][k].append((b, var))
        by_side[b][k].append((a, var))
    for u in used:
        for k in (1, 2):
            lits = [var for _, var in by_side[u][k]]
            if not lits:
                s.add_clause([])
                continue
            for cl in CardEnc.equals(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses:
                s.add_clause(cl)
    def tget(k, u, v):
        return T.get((k,) + tuple(sorted((u, v))))

    for (k, a, b), var in list(T.items()):
        if beta.get(a) == b:
            s.add_clause([-var])
    for u in used:
        for v, var1 in by_side[u][1]:
            var2 = tget(2, u, v)
            if var2:
                s.add_clause([-var1, -var2])
    # closure
    for u in used:
        ku = kind(u)
        if ku == "k4":
            for v, var1 in by_side[u][1]:
                for need in ((1, beta[u], beta[v]), (2, u, beta[v])):
                    w = tget(*need)
                    s.add_clause([-var1] + ([w] if w else []))
        else:
            if not is_tab(u):
                continue
            for v, var1 in by_side[u][1]:
                w = tget(2, beta[v], beta[u])
                s.add_clause([-var1] + ([w] if w else []))
            for w_side, var2 in by_side[u][2]:
                w = tget(1, beta[w_side], beta[u])
                s.add_clause([-var2] + ([w] if w else []))
            for v, var1 in by_side[u][1]:
                for w_side, var2 in by_side[u][2]:
                    w = tget(1, beta[v], w_side)
                    s.add_clause([-var1, -var2] + ([w] if w else []))
    if no_fixed:
        for p in range(N):
            a = [X[1, p, p, q] for q in rots if (1, p, p, q) in X]
            b = [X[2, p, p, q] for q in rots if (2, p, p, q) in X]
            for x in a:
                for y in b:
                    s.add_clause([-x, -y])
    if no_shared:
        # piece pair adjacent in A cannot be adjacent in B or C; pairs adjacent in B not in C
        adjA = {(min(p, beta[(p, d)][0]), max(p, beta[(p, d)][0])) for p in range(N) for d in range(4) if (p, d) in beta}
        pair_vars = {1: {}, 2: {}}
        for (k, a, b), var in T.items():
            key = (min(a[0], b[0]), max(a[0], b[0]))
            pair_vars[k].setdefault(key, []).append(var)
        for k in (1, 2):
            for key, vs in pair_vars[k].items():
                if key in adjA:
                    for v in vs:
                        s.add_clause([-v])
        for key in set(pair_vars[1]) & set(pair_vars[2]):
            for v1 in pair_vars[1][key]:
                for v2 in pair_vars[2][key]:
                    s.add_clause([-v1, -v2])
    t0 = time.time()
    if timeout:
        import threading
        timer = threading.Timer(timeout, s.interrupt)
        timer.start()
        ok = s.solve_limited(expect_interrupt=True)
        timer.cancel()
    else:
        ok = s.solve()
    dt = time.time() - t0
    if ok is None:
        return "timeout", dt
    if not ok:
        return None, dt
    m = set(v for v in s.get_model() if v > 0)
    pl = [{p: (p, 0) for p in range(N)}]
    for k in (1, 2):
        pl.append({p: (c, q * 90) for (kk, p, c, q), var in X.items() if kk == k and var in m})
    return pl, dt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*", help="COLSxROWS:topo:mode[:nofixed][:noshared]")
    a = ap.parse_args()
    for case in a.cases:
        parts = case.split(":")
        cols, rows = map(int, parts[0].split("x"))
        pl, dt = search(cols, rows, parts[1], parts[2], "nofixed" in parts, "noshared" in parts)
        print(f"{case}: {'SAT' if pl else 'UNSAT'} ({dt:.1f}s)")
        if pl:
            for k in (1, 2):
                print("  ", " ".join(f"{pl[k][p][0]}@{pl[k][p][1]}" for p in range(cols * rows)))


if __name__ == "__main__":
    main()
