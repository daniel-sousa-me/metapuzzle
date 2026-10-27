"""Negative searches for structured K4 schemes on tori (quarter rotation).

Run: python3 experiments/012-constructive-placements/k4_families.py
1. linear: placement B puts piece (x, y) at M (x, y) with rotation Q[x mod m][y mod m] (all M in
   GL2(Z_n), all period-m rotation patterns); C is forced by the Klein structure and reconstructed.
2. homogeneous: side involutions (g, i) -> (g + tau(i), phi(i)) with pieces g in Z_c x Z_r.
Both print the number of K4 schemes found (0 for every size tried).
Periodic SAT (translation symmetry of period p in the side involution) is `k4_periodic.py`.
"""
import itertools
import sys
DELTA = ((0, -1), (1, 0), (0, 1), (-1, 0))
def contacts(n, pl):
    # pl: piece -> (x, y, q); torus n x n; returns dict side->side
    at = {(x % n, y % n): (p, q) for p, (x, y, q) in pl.items()}
    out = {}
    for (x, y), (p, q) in at.items():
        for d in range(4):
            dx, dy = DELTA[d]
            p2, q2 = at[((x + dx) % n, (y + dy) % n)]
            out[(p, (d - q) % 4)] = (p2, (d + 2 - q2) % 4)
    return out
def reconstruct(n, partner):
    # partner: side -> side, build placement from piece 0 at (0,0,0)
    pl = {0: (0, 0, 0)}
    stack = [0]
    while stack:
        p = stack.pop()
        x, y, q = pl[p]
        for i in range(4):
            d = (i + q) % 4
            b, j = partner[(p, i)]
            qb = (d + 2 - j) % 4
            pos = ((x + DELTA[d][0]) % n, (y + DELTA[d][1]) % n, qb)
            if b in pl:
                if pl[b] != pos: return None
            else:
                pl[b] = pos; stack.append(b)
    if len({(x, y) for x, y, _ in pl.values()}) != n * n: return None
    # verify
    if contacts(n, pl) != partner: return None
    return pl
def search_linear(n, m):
    N = n * n
    A = {x + n * y: (x, y, 0) for x in range(n) for y in range(n)}
    cA = contacts(n, A)
    mats = [(a, b, c, d) for a, b, c, d in itertools.product(range(n), repeat=4)
            if len({((a * x + b * y) % n, (c * x + d * y) % n) for x in range(n) for y in range(n)}) == N]
    rotfns = list(itertools.product(range(4), repeat=m * m))
    found = 0
    for M in mats:
        a, b, c, d = M
        for Q in rotfns:
            B = {x + n * y: (a * x + b * y, c * x + d * y, Q[(x % m) + m * (y % m)]) for x in range(n) for y in range(n)}
            cB = contacts(n, B)
            # A u B must be disjoint 4-cycles: u -A- u' -B- v' -A- v -B- u
            ok = True; cC = {}
            for u in cA:
                v = cB[u]
                if v == cA[u]: ok = False; break
                # cycle: u -A- uA ; uA -B- w ; w -A- z ; need z -B- u  i.e. cB[cA[cB[cA[u]]]]... check 4-cycle
                uA = cA[u]; w = cB[uA]; z = cA[w]
                if cB[z] != u or z == u or w == u: ok = False; break
                # Klein: C pairs u with cA[v]
                cC[u] = cA[v]
            if not ok: continue
            if any(cC[cC[u]] != u for u in cC): continue
            C = reconstruct(n, cC)
            if C is None: continue
            found += 1
            yield M, Q, B, C
def search_homogeneous(c, r, want_rect=True, limit=5):
    G = [(x, y) for y in range(r) for x in range(c)]
    add = lambda a, b: ((a[0]+b[0]) % c, (a[1]+b[1]) % r)
    neg = lambda a: ((-a[0]) % c, (-a[1]) % r)
    tauA = [((DELTA[i][0]) % c, (DELTA[i][1]) % r) for i in range(4)]
    phiA = [(i+2) % 4 for i in range(4)]
    invols = []
    for sgn in (1, -1):
        for cc in range(4):
            f = [(sgn*i+cc) % 4 for i in range(4)]
            if all(f[f[i]] == i for i in range(4)) and all(f[(i+2) % 4] == (f[i]+2) % 4 for i in range(4)):
                invols.append(tuple(f))
    invols = sorted(set(invols))
    found = []
    for phiB in invols:
        # free tau values on representatives of phiB orbits
        reps = sorted({min(i, phiB[i]) for i in range(4)})
        for vals in itertools.product(G, repeat=len(reps)):
            tauB = [None]*4
            ok = True
            for i, v in zip(reps, vals):
                tauB[i] = v
                j = phiB[i]
                if j == i:
                    if add(v, v) != (0, 0): ok = False
                else:
                    tauB[j] = neg(v)
            if not ok: continue
            # commute: tauB(i)+tauA(phiB i) == tauA(i)+tauB(phiA i), and phiA phiB == phiB phiA (true)
            if any(add(tauB[i], tauA[phiB[i]]) != add(tauA[i], tauB[phiA[i]]) for i in range(4)): continue
            phiC = [phiA[phiB[i]] for i in range(4)]
            tauC = [add(tauB[i], tauA[phiB[i]]) for i in range(4)]
            # class members on 4 distinct pieces: 0, tauA, tauB, tauC distinct
            if any(len({(0, 0), tauA[i], tauB[i], tauC[i]}) < 4 for i in range(4)): continue
            pls = []
            for tau, phi in ((tauB, phiB), (tauC, phiC)):
                pl = develop_h(c, r, tau, phi, G, add)
                if pl is None: break
                pls.append(pl)
            else:
                found.append((phiB, tauB, phiC, tauC, pls))
                if len(found) >= limit: return found
    return found
def develop_h(c, r, tau, phi, G, add):
    """Placement on the c x r torus from the side involution (g,i)->(g+tau(i), phi(i)); None if not a c x r torus."""
    pos = {(0, 0): (0, 0, 0)}; stack = [(0, 0)]
    while stack:
        g = stack.pop(); x, y, q = pos[g]
        for i in range(4):
            d = (i+q) % 4; b = add(g, tau[i]); j = phi[i]
            np_ = ((x+DELTA[d][0]) % c, (y+DELTA[d][1]) % r, (d+2-j) % 4)
            if b in pos:
                if pos[b] != np_: return None
            else: pos[b] = np_; stack.append(b)
    if len(pos) != c*r or len({v[:2] for v in pos.values()}) != c*r: return None
    return pos


if __name__ == "__main__":
    for n, m in ((3, 1), (4, 2), (6, 2)):
        print(f"linear, {n}x{n} torus, rotation period {m}: {sum(1 for _ in search_linear(n, m))} schemes", flush=True)
    for c, r in ((4, 4), (6, 6), (8, 8), (4, 8), (6, 4), (12, 12)):
        print(f"homogeneous, {c}x{r} torus: {len(search_homogeneous(c, r))} schemes", flush=True)
