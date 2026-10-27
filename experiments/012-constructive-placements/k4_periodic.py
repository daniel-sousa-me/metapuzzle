"""K4 on a c x r torus by SAT: Klein partner variables + per-piece coordinates (x mod c, y mod r, rotation) for B and C.

Run: python3 experiments/012-constructive-placements/k4_periodic.py 4x4:p2,2 6x6:p2,2   (needs python-sat)
Optional `pP,Q`: the side involution must commute with translations by (P, 0) and (0, Q).
Consistent coordinates imply a valid placement on the same c x r torus (degree-1 covering).
"""
import sys, time
from pysat.solvers import Cadical153
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
DELTA = ((0, -1), (1, 0), (0, 1), (-1, 0))
def run(cols, rows, no_shared=False, period=None):
    N = cols*rows
    def cell(x, y): return (y % rows)*cols + (x % cols)
    def step(c, d): return cell(c % cols + DELTA[d][0], c // cols + DELTA[d][1])
    sides = [(p, i) for p in range(N) for i in range(4)]
    piA = {(p, d): (step(p, d), (d+2) % 4) for p in range(N) for d in range(4)}
    pool = IDPool(); s = Cadical153()
    M = {}
    for u in sides:
        for v in sides:
            if u < v and len({u[0], v[0], piA[u][0], piA[v][0]}) == 4:
                M[u, v] = M[v, u] = pool.id(('m',) + u + v)
    part = {u: [v for v in sides if (u, v) in M] for u in sides}
    for u in sides:
        for cl in CardEnc.equals([M[u, v] for v in part[u]], 1, vpool=pool, encoding=EncType.seqcounter).clauses:
            s.add_clause(cl)
        for v in part[u]:
            if u < v: s.add_clause([-M[u, v], M[piA[u], piA[v]]])
    if period:
        px, py = period
        def sh(u, dx, dy):
            p, i = u
            return (cell(p % cols + dx, p // cols + dy), i)
        for (u, v), m in M.items():
            if u < v:
                for dx, dy in ((px, 0), (0, py)):
                    u2, v2 = sh(u, dx, dy), sh(v, dx, dy)
                    if (u2, v2) in M: s.add_clause([-m, M[u2, v2]])
                    else: s.add_clause([-m])
    X = lambda t, p, x: pool.id(('x', t, p, x)); Y = lambda t, p, y: pool.id(('y', t, p, y)); R = lambda t, p, q: pool.id(('r', t, p, q))
    for t in 'BC':
        for p in range(N):
            for lits in ([X(t, p, x) for x in range(cols)], [Y(t, p, y) for y in range(rows)], [R(t, p, q) for q in range(4)]):
                for cl in CardEnc.equals(lits, 1, vpool=pool, encoding=EncType.pairwise).clauses: s.add_clause(cl)
        s.add_clause([X(t, 0, 0)]); s.add_clause([Y(t, 0, 0)]); s.add_clause([R(t, 0, 0)])
    for u in sides:
        p, i = u
        for v in part[u]:
            m = M[u, v]
            for t, w in (('B', v), ('C', piA[v])):
                p2, j = w
                for q in range(4):
                    d = (i+q) % 4; q2 = (d+2-j) % 4
                    s.add_clause([-m, -R(t, p, q), R(t, p2, q2)])
                    dx, dy = DELTA[d]
                    for x in range(cols):
                        s.add_clause([-m, -R(t, p, q), -X(t, p, x), X(t, p2, (x+dx) % cols)])
                    for y in range(rows):
                        s.add_clause([-m, -R(t, p, q), -Y(t, p, y), Y(t, p2, (y+dy) % rows)])
    if no_shared:
        adjA = {frozenset((p, step(p, d))) for p in range(N) for d in range(4)}
        pairB, pairC = {}, {}
        for (u, v), m in M.items():
            if u < v:
                if frozenset((u[0], v[0])) in adjA or frozenset((u[0], piA[v][0])) in adjA: s.add_clause([-m])
                pairB.setdefault(frozenset((u[0], v[0])), []).append(m)
                pairC.setdefault(frozenset((u[0], piA[v][0])), []).append(m)
        for key in set(pairB) & set(pairC):
            for a in pairB[key]:
                for b in pairC[key]:
                    if a != b: s.add_clause([-a, -b])
    t0 = time.time(); ok = s.solve(); dt = time.time() - t0
    if not ok: return None, dt
    mdl = set(v for v in s.get_model() if v > 0)
    pls = [{p: (p, 0) for p in range(N)}]
    for t in 'BC':
        pl = {}
        for p in range(N):
            x = next(x for x in range(cols) if X(t, p, x) in mdl); y = next(y for y in range(rows) if Y(t, p, y) in mdl)
            q = next(q for q in range(4) if R(t, p, q) in mdl)
            pl[p] = (y*cols + x, 90*q)
        pls.append(pl)
    return pls, dt
if __name__ == '__main__':
    for arg in sys.argv[1:]:
        parts = arg.split(':'); c, r = map(int, parts[0].split('x'))
        per = next((tuple(map(int, q[1:].split(','))) for q in parts if q.startswith('p')), None)
        pls, dt = run(c, r, 'noshared' in parts, per)
        print(arg, 'SAT' if pls else 'UNSAT', f'{dt:.1f}s', flush=True)
        if pls:
            for k in (1, 2):
                print('  ', ' '.join(f'{pls[k][p][0]}@{pls[k][p][1]}' for p in range(c*r)), flush=True)
