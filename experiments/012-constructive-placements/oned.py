"""Frame sides in rotation none: three orderings of n pieces with fixed ends whose E/W contacts form K(3,3) blocks.

Run: python3 experiments/012-constructive-placements/oned.py [n ...]   (needs python-sat)

A standard-border side of length n (corners included) keeps its pieces in rotation none, so its
horizontal contacts are a one-dimensional problem: orderings P_0, P_1, P_2 of pieces 0..n-1 with
piece 0 first and n-1 last, whose successor relation is a disjoint union of K(3,3) (each E side
meets three distinct W sides and blocks close). Options: no shared adjacency (no pair adjacent in
two orderings in either order), no fixed piece other than the ends. Prints the orderings.
Also used as a library by construct.py: `sequence(n)` gives exact orderings for every n = 1 mod 3,
n >= 7 (base cases 7, 10, 13, 16; longer ones by concatenation at a fixed junction piece, n -> n + 9).
"""
from __future__ import annotations

import itertools
import sys

# verified solutions (no shared adjacency, no fixed piece except the ends), found by search() below
SEQ: dict[int, list[list[int]]] = {}


def is_exact(orders: list[list[int]]) -> bool:
    n = len(orders[0])
    succ = [{o[i]: o[i + 1] for i in range(n - 1)} for o in orders]
    tabs = [p for p in range(n) if p != orders[0][-1]]
    seen = set()
    for a in tabs:
        if a in seen:
            continue
        bs = {succ[k][a] for k in range(3)}
        if len(bs) != 3:
            return False
        a_block = {x for x in tabs for k in range(3) if succ[k][x] in bs}
        if len(a_block) != 3 or any({succ[k][x] for k in range(3)} != bs for x in a_block):
            return False
        seen |= a_block
    return all(o[0] == orders[0][0] and o[-1] == orders[0][-1] for o in orders)


def shared_pairs(orders) -> int:
    pairs = [{frozenset(o[i:i + 2]) for i in range(len(o) - 1)} for o in orders]
    return len(pairs[0] & pairs[1]) + len(pairs[0] & pairs[2]) + len(pairs[1] & pairs[2])


def concat(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    """Join two solutions at a fixed junction piece: last of a = first of b."""
    na = len(a[0])
    return [oa + [na - 1 + x for x in ob[1:]] for oa, ob in zip(a, b)]


def sequence(n: int) -> list[list[int]]:
    """Exact orderings for any n = 1 mod 3, n >= 7, from the base solutions for 7 and 10."""
    if n % 3 != 1 or n < 7:
        raise ValueError("needs n = 1 mod 3 and n >= 7")
    if n in SEQ:
        return SEQ[n]
    return concat(SEQ[10], sequence(n - 9))


def search(n: int, no_shared=True, no_fixed=True):
    from pysat.card import CardEnc, EncType
    from pysat.formula import IDPool
    from pysat.solvers import Cadical153

    pool = IDPool()
    s = Cadical153()
    X = lambda k, p, i: pool.id(("x", k, p, i))
    S = lambda k, a, b: pool.id(("s", k, a, b))
    Y = lambda a, b: pool.id(("y", a, b))
    P = range(n)
    for i in P:
        s.add_clause([X(0, i, i)])  # ordering 0 is the identity
    for k in range(3):
        for p in P:
            for cl in CardEnc.equals([X(k, p, i) for i in P], 1, vpool=pool, encoding=EncType.seqcounter).clauses:
                s.add_clause(cl)
        for i in P:
            for cl in CardEnc.equals([X(k, p, i) for p in P], 1, vpool=pool, encoding=EncType.seqcounter).clauses:
                s.add_clause(cl)
        s.add_clause([X(k, 0, 0)])
        s.add_clause([X(k, n - 1, n - 1)])
        for a in P:
            for b in P:
                if a == b:
                    s.add_clause([-S(k, a, b)])
                    continue
                for i in range(n - 1):
                    s.add_clause([-X(k, a, i), -X(k, b, i + 1), S(k, a, b)])
                for i in P:
                    s.add_clause([-S(k, a, b), -X(k, a, i)] + ([X(k, b, i + 1)] if i < n - 1 else []))
    for a in P:
        for b in P:
            for cl in CardEnc.atmost([S(k, a, b) for k in range(3)], 1, vpool=pool).clauses:
                s.add_clause(cl)
            s.add_clause([-Y(a, b)] + [S(k, a, b) for k in range(3)])
            for k in range(3):
                s.add_clause([-S(k, a, b), Y(a, b)])
            if no_shared and a < b:
                s.add_clause([-Y(a, b), -Y(b, a)])
    for a, a2, b, b2 in itertools.product(P, repeat=4):
        if a != a2 and b != b2:
            s.add_clause([-Y(a, b), -Y(a2, b), -Y(a, b2), Y(a2, b2)])
    if no_fixed:
        for p in range(1, n - 1):
            s.add_clause([-X(1, p, p), -X(2, p, p)])
    if not s.solve():
        return None
    m = set(v for v in s.get_model() if v > 0)
    return [[p for i in P for p in P if X(k, p, i) in m] for k in range(3)]


def multiplicative(n: int) -> list[list[int]]:
    """n = 9j + 1: position i < n-1 holds piece mu_k * i mod (n-1), mu_k = 1 + k (n-1)/3; piece n-1 last."""
    m3 = n - 1
    if n % 9 != 1:
        raise ValueError("needs n = 1 mod 9")
    return [[(1 + k * (m3 // 3)) * i % m3 for i in range(m3)] + [m3] for k in range(3)]


# n = 7 exists only with shared adjacencies and fixed pieces (no solution avoids either; SAT)
SEQ[7] = [[0, 2, 3, 1, 4, 5, 6], [0, 1, 3, 5, 4, 2, 6], [0, 5, 3, 2, 4, 1, 6]]
SEQ[10] = multiplicative(10)
# SAT (search(n), no shared adjacency, no fixed piece except the ends)
SEQ[13] = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [0, 8, 3, 7, 11, 5, 9, 4, 2, 6, 10, 1, 12],
           [0, 11, 2, 9, 7, 1, 5, 3, 10, 8, 6, 4, 12]]
SEQ[16] = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
           [0, 6, 10, 3, 9, 2, 8, 14, 5, 13, 4, 12, 1, 7, 11, 15],
           [0, 13, 9, 7, 3, 14, 12, 6, 2, 11, 5, 1, 10, 8, 4, 15]]

if __name__ == "__main__":
    ns = [int(a) for a in sys.argv[1:]] or [4, 7, 10, 13]
    for n in ns:
        sol = search(n)
        print(n, sol, "exact" if sol and is_exact(sol) else "", "shared", shared_pairs(sol) if sol else "-", flush=True)
