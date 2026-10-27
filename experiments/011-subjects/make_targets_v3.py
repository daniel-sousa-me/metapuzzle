"""Tier targets for experiment 011: "Field, Wood and Water" (version 3: class-level matching).

Copy of make_targets.py (v2) with one change to the objective and a different start. v2 matched the
boundary edges and corners per tier pair (budget_v2.py). The piece inventory is counted per merged
transition class (budget_v3.py, the classify stage of pipeline/run_from_tiers_v3.py: ordered tier pair x
pattern s straight, c corner, p cap, d dot), which is finer. v3 penalizes, per class, the spread of its
count over the three pictures (max minus min); the frame (border cells: corner and edge pools, plain
tiers and transition classes alike) is matched the same way. The surplus of a picture is the sum over classes of (max
over pictures minus its own count); the target is a total under 30.

v3 starts from the v2 pictures (27x38-v2/tiers-*.txt): the figures are not redrawn. Kept from v2: the
locked cells (sketch features, dots) and the figure, S and W rules (only background cells on a drawn
boundary move, to a neighbouring background tier), the anomaly penalties (caps, strips, dots, pinches),
tier totals equal in the three pictures (v3 target: exact; the penalty is the spread, reported in budgets.txt), straight runs, S touching only L, Euler numbers,
and the 45-degree runs per pair. Outputs: 27x38-v3/ (tiers-A/B/C.txt, budgets.txt, targets-preview.png and
contours-preview.png without text labels).

Usage: python3 make_targets_v3.py [27x38]   (about 15 min on 4 cores)
"""
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from budget_v2 import PAIRS, FORBIDDEN, budgets, table, anomaly_map, key as pair_key  # noqa: E402
from budget_v3 import (RANK, cell_class, cell_label, pool_of, class_counts, frame_counts,  # noqa: E402
                       frame_table, class_surplus, class_table)
from collections import Counter  # noqa: E402

PRIMARY = "27x38"   # COLSxROWS of the native drawings and primary deliverable (owner decision)
OUT_SUFFIX = "-v3"  # outputs go to 27x38-v3/ (v2 outputs are kept)
V2_DIR = HERE / "27x38-v2"  # the start: the v2 pictures
NAMES = ["A", "B", "C"]
TITLES = {"A": "A hare (dawn)", "B": "B owl (dusk)", "C": "C swan (midnight)"}
FIGURE = {"A": "M", "B": "D", "C": "L"}
# Tiers the balancer may paint in each picture (the figure tier only away from the figure).
BACKGROUND = {"A": "DLW", "B": "MLW", "C": "DMLW"}   # v2: W (mist, clouds, water) is background too
SEED = 11         # base seed; SEEDS runs are made and the lowest energy kept
SEEDS = 4
ITERS_PER_CELL = 2000  # v3: 5x the v2 budget (the class and frame terms converge slowly)
FIRST_T0 = 2.0   # v3: first pass from the v2 pictures (v2 started from the sketches at 6.0)
POLISH_T0 = 1.0  # second, cooler annealing pass started from the best first-pass result
SOFT_RADIUS = 1   # 1 = only cells on a drawn boundary; 2 = also their neighbours

SKETCHES = {}  # filled below

# Hand-drawn 27 x 38 sketches, rows top to bottom. D M S as themselves, '.' = L, 'w' = W.
# Lower case 'd' / 'm' / ',' = D / M / L locked: a drawn feature the balancer must not touch
# (the hare's tree, the swan's clouds, the dots and their neighbours). The figure and S are always
# locked.
SKETCHES["A"] = """
...........................
....................wwwwww.
..SS...........MM...wwwwww.
.SSS..MM......MMMM.........
.SSS..MMM.....MMMM..,,,....
.SSS..MMMM....MMMM..,d,....
.SSS...MMMM...MMMMM.,,,....
.SSS...MMMM...MMMMM.....dd.
.SSSS..MMMMM..MMMMM....dddd
..SSS..MMMMM..MMMMM....dddd
..SSS...MMMMMMMMMMMM...dddd
.........MMMMMMMMMMM....ddd
.........MMMMMMMMdMMM...dd.
DDD......MMMMMMMMMMMMM..dd.
DDDD......MMMMMMMMMMMM..dd.
DDDDD......MMMMMMMMMMM..dd.
DDDDDD......MMMMMMMM....dd.
DDDDDDD.....MMMMMM......dd.
DDDDDDDD...MMMMMMM.....dddd
DDDDDDDD..MMMMMMMMM....dddd
DDDDDDDDDMMMMMMMMMMMDDDDDDD
DDDDDDDDDMMMMMMMMMMMDDD..DD
DDDDDDDMMMMMMMMMMMMMMDD..DD
..DDDDMMMMMMMMMMMMMMMDDDDDD
..DDDMMMMMMMMMMMMMMMMDDDDDD
DDDDDMMMMMMMMMMMMMMMMDDD..D
DDDDMMMMMMMMMMMMMMMMMDDD..D
DDDDMMMMMMMMMMMMMMMMDDDDDDD
DDDMMMMMMMMMMMMMMMMMDDDDDDD
DMMMMMMMMMMMMMMMMMMMDD..DDD
DMMMMMMMMMMMMMMDDMMMDD..DDD
DDDMMMMMMMMMMMMDDMMMDDDDDDD
DDDMMMMMMMMMMwwwwMMMDDDDDDD
DDDDMMMMMMMMMwwwwMMMDDDD..D
DDDDMMMMMMMMMMMwwMMMMDDD..D
DDDDDDDDMMMMMMMwwMMMMDDDDDD
..DDDDDDwwwwwwwwwwDDDDDDDDD
...DDDDDwwwwwwwwwwDDDDDDDDD
"""

SKETCHES["B"] = """
MMMMMMMMMMMMMMMMMMMMMMMMMMM
MMMMMMMMMMMMMMMMMMMMMMMMMMM
MMMMMMMMMMwwwwwwwMMMMMMMMMM
MMMMMMM...wwwwwww..MMMMMMMM
MMMMM................MMMMMM
MMMM..................MMMMM
MMMM......DDDDDD......MMMMM
MMM.....DDDDDDDDDD.....MMMM
MM....DDDDDDDDDDDDDD....MMM
MM...DDDDDDDDDDDDDDDD...MMM
MM..DDDD..DDDDDD..DDDD..MMM
MM..DDD....DDDD....DDD..MMM
MM..DD..DD..DD..DD..DD..MMM
MM..DD..DD..DD..DD..DD..MMM
mmmMDDD....DDDD....DDDMMMMM
mdmMDDDD..DDMMDD..DDDDMMMMM
mmmMMDDDDDDDMMDDDDDDDMMMMMM
MMMMMDDDDDDDMMDDDDDDDMMMMMM
MMMwwDDDDDDDDDDDDDDDDwwMMMM
MMMwwDDDDDDDDDDDDDDDDwwMMMM
MMMwwDDDDDDDDDDDDDDDDwwMMMM
MMMwwDDDDDDDDDDDDDDDDwwMMMM
MMMMMMMDDDDDDDDDDDDMMMMMMMM
MMMMMMMDDDDDDDDDDDDMMMMMMMM
MMMMMMMMDDDDDDDDDDMMMMMMMMM
MMMMMMMMDDDDDDDDDDMMMMMMMMM
MMMMMMDDDDDDDDDDDDDDDMMMMMM
MMMMMDDDDDDDDDDDDDDDDMMMMMM
MMMMMDDDDMMMDDMMMMMMMMMMMMM
MMMMMMMMMMMMMMMMMMMMMMMMMMM
..MMMMMMMMMMMMMMMMMMMMMMMMM
....MM....MMMMMM..MM.....MM
...........................
...........................
........SS.............,,,.
......SSSSS...SSSSS....,d,.
......SSSSS...SSSSS....,,,.
..............SSSSS........
"""

SKETCHES["C"] = """
DDDDDDDDDDDDDDDDDDDDDDDDDDD
DDmmmmmDDDDDDDDDDDDDD...DDD
mmmmmmmDDDDDDDDDDDDD.....DD
mmmmmmDDDDD...DDDDD.......D
DDDDDDDDD......DDDD.......D
DDDDDDDDD..d...DDDDD.....DD
DDDDD...........DDDDD...DDD
DDDDD...........DDDDDDDDDDD
DDDDDDDDDDD.......DDDDDDDDD
DDD..DDDDDDDDD....DDDDDDDDD
DDD..DDDDDDDDDD...DDDDDDDDD
DDDDDDDD..DDDDD...DDDDDDDDD
DDDDDDDD..DDDD....DDDwwwwww
DDDDDDDDDDDDDD...DDDDwwwwww
MMMMMMDDDDDDD....DDDMMMMMMM
MMMMMMMMMMMM....MMMMMMMMMMM
MMMMMMMMMMMM...MMMMMMMMMMMM
MMMMMMMMMM.....MMM...MM...M
MMMMMMMMM......MM.........M
MMMMMMM...................M
MMMMMM.............SS.....M
MMMMM.......SSSSSSSSS.....M
MMMMM.......SSSSSSSSS....MM
MMMMM........SSSSSSS.....MM
MMMMM...................MMM
MMMMMM.................MMMM
MMMMMMMww.......wwwwwwwMMMM
MMMMMMMwwwwwwwwwwwwwwwwMMMM
MMMMMMMMMwwwwwwwMMMMMMMMMMM
MMMMMMMMMMMMMMMMMMMMMMMMMMM
MMMMMMMMMMMMMMMMMMMMMM...MM
MMMMmmmMMMMMMMMMMMMMMM...MM
MMMMmdmMMMMMMMMMM...MMMMMMM
MMMMmmmMMMMMMMMMM...MMMMMMM
MMMMMMMMMMMMMMMMMMMMM...MMM
DDDMMMMMMMMMMMMMMMMMM...MMD
DDDDDMMMMMMMMMMMMMMMMMMMMDD
DDDDDDDDMMMMMMMDDDDMMMMMDDD
"""


# ---- parsing, resampling, cleaning ------------------------------------------------------
CODE = {"D": 0, "M": 1, "L": 2, "S": 3, "W": 4}
CHARS = np.array(list("DMLSW"))
BUDGET_TIER = np.array([0, 1, 2, 3, 4])           # v2: every token is a tier of its own (W too)
PAIR_ID = -np.ones((5, 5), int)
NB = len(PAIRS)                                   # budget pairs; then the forbidden S pairs
for i, (a, b) in enumerate(PAIRS + FORBIDDEN):
    PAIR_ID[CODE[a], CODE[b]] = PAIR_ID[CODE[b], CODE[a]] = i
NP = len(PAIRS) + len(FORBIDDEN)
SKETCH_ROWS, SKETCH_COLS = 38, 27   # native size of the sketches
SKETCH_CHAR = {".": "L", ",": "L", "d": "D", "m": "M", "w": "W", "D": "D", "M": "M", "S": "S"}


def parse(text):
    """(tier codes, locked mask) of a sketch."""
    rows = [r.strip() for r in text.strip().splitlines()]
    assert len(rows) == SKETCH_ROWS and all(len(r) == SKETCH_COLS for r in rows), [len(r) for r in rows]
    t = np.array([[CODE[SKETCH_CHAR[ch]] for ch in r] for r in rows], np.int8)
    locked = np.array([[ch in "dm," for ch in r] for r in rows])
    return t, locked


def components(mask):
    """4-connected component labels of a boolean mask (0 = background)."""
    R, C = mask.shape
    lab = np.zeros(mask.shape, int)
    n = 0
    for r, c in zip(*np.nonzero(mask)):
        if lab[r, c]:
            continue
        n += 1
        stack = [(r, c)]
        lab[r, c] = n
        while stack:
            y, x = stack.pop()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < R and 0 <= xx < C and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    stack.append((yy, xx))
    return lab, n


def figure_mask(t, fig):
    """Largest 4-connected region of the figure tier plus the holes it encloses (eyes, beak)."""
    lab, n = components(BUDGET_TIER[t] == CODE[fig])
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    sizes[0] = 0
    main = lab == sizes.argmax()
    outside, _ = components(~main)
    border = set(outside[0]) | set(outside[-1]) | set(outside[:, 0]) | set(outside[:, -1])
    holes = ~main & ~np.isin(outside, list(border - {0}))
    return main, main | holes


# ---- fast statistics for the annealer ---------------------------------------------------
def pad(b, v=-1):
    return np.pad(b, 1, constant_values=v)


def is_boundary(x, y):
    return x != y


class Stats:
    """Per picture: edges, corners, diagonal-run cells per pair; tier counts; tips (caps) and
    other anomalies; straight-run excess; junction cells; Euler numbers per tier."""

    def __init__(self, t, run_limit):
        b = BUDGET_TIER[t]
        self.edges = np.zeros(NP, int)
        for x, y in ((b[:, :-1], b[:, 1:]), (b[:-1], b[1:])):
            pid = PAIR_ID[x, y]
            self.edges += np.bincount(pid[pid >= 0], minlength=NP)
        p = pad(b)
        R, C = b.shape
        sh = lambda dr, dc: p[1 + dr:1 + dr + R, 1 + dc:1 + dc + C]
        side_off = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        side = [sh(*o) for o in side_off]
        diag = [sh(-1, 1), sh(1, 1), sh(1, -1), sh(-1, -1)]
        self.corners = np.zeros(NP, int)
        self.diag = np.zeros(NP, int)
        self.tips = 0
        self.anomalies = 0
        others = np.zeros(b.shape, int)
        for y in range(5):
            pid = PAIR_ID[b, y]
            valid = pid >= 0
            s = [x == y for x in side]
            d = [x == y for x in diag]
            ns = sum(s)
            adj = [s[k] & s[(k + 1) % 4] for k in range(4)]
            adj2 = adj[0] | adj[1] | adj[2] | adj[3]
            opp = (d[0] & d[2]) | (d[1] & d[3])
            anyd = d[0] | d[1] | d[2] | d[3]
            corner = valid & (((ns == 2) & adj2) | ((ns == 0) & anyd & ~opp))
            self.corners += np.bincount(pid[corner], minlength=NP)
                # 45-degree runs: convex corners with the same orientation, chained diagonally
            for k in range(4):
                cv = valid & (ns == 2) & adj[k]
                a, bb = side_off[k], side_off[(k + 1) % 4]
                st = (a[0] - bb[0], a[1] - bb[1])
                cp = np.pad(cv, 1)
                fwd = cp[1 + st[0]:1 + st[0] + R, 1 + st[1]:1 + st[1] + C]
                back = cp[1 - st[0]:1 - st[0] + R, 1 - st[1]:1 - st[1] + C]
                inrun = cv & (fwd | back)
                self.diag += np.bincount(pid[inrun], minlength=NP)
            others += valid & ((ns > 0) | anyd)
        # anomalies against any foreign tier (a neighbour needing a transition)
        fs = [(x >= 0) & (x != b) for x in side]
        fd = [(x >= 0) & (x != b) for x in diag]
        nf = sum(fs)
        fopp = (fs[0] & fs[2]) | (fs[1] & fs[3])
        self.tips = int((nf == 3).sum())
        self.anomalies = int(((nf == 4) | ((nf == 2) & fopp) | ((nf == 0) & ((fd[0] & fd[2]) | (fd[1] & fd[3])))).sum())
        self.counts = np.bincount(b.ravel(), minlength=5)
        self.raw_counts = np.bincount(t.ravel(), minlength=5)
        self.run = run_excess(b, run_limit)
        self.junction = int((others >= 2).sum())
        self.regions = tuple(euler(b == k) for k in range(5))


def euler(m):
    """Euler number (regions minus holes, 4-connectivity) of a mask: a cheap, local proxy that
    changes whenever a flip creates or removes an island or a hole."""
    return int(m.sum() - (m[:, 1:] & m[:, :-1]).sum() - (m[1:] & m[:-1]).sum()
               + (m[1:, 1:] & m[:-1, 1:] & m[1:, :-1] & m[:-1, :-1]).sum())


def run_excess(b, limit):
    """Sum over straight boundary segments of (length - limit) where positive."""
    ex = 0
    for line in list(is_boundary(b[:-1], b[1:])) + list(is_boundary(b[:, :-1], b[:, 1:]).T):
        run = 0
        for v in list(line) + [False]:
            if v:
                run += 1
            else:
                ex += max(0, run - limit)
                run = 0
    return ex


ANOMALY_W = 1000.0   # v2: the drawings have no anomalies but the locked dots; the balancer adds none
DIAG_TOL, DIAG_W = 4, 0.3   # 45-degree runs are tracked, matched more loosely than edges and corners
RUN_W = 25.0      # v2: per edge of a straight run above the limit (6 in v1; W cells now move)
CLS_W, CLS_TOL, CLS_LIN = 3.0, 0, 0.3   # v3: per merged class, CLS_W * excess^2 + CLS_LIN * spread
TIER_TOL, TIER_W = 0, 4.0               # v3: tier totals (D M W L S) equal in the three pictures


def class_terms(cc_list):
    """Over the merged classes: the sum of the spread (max minus min over the pictures) of each class
    count, and the sum of its squared excess over CLS_TOL."""
    tot, sq = 0, 0.0
    for k in set().union(*cc_list):
        vals = [c.get(k, 0) for c in cc_list]
        sp = max(vals) - min(vals)
        tot += sp
        sq += max(0, sp - CLS_TOL) ** 2
    return tot, sq


def energy(st, changes, ref_regions, cc):
    """cc: per picture, {pool: Counter} of the labels (class_state). Edges and corners per pair are
    no longer matched (v2); they are reported in budgets.txt."""
    e = 0.0
    for s, ref in zip(st, ref_regions):
        e += 40.0 * sum(abs(a - b) for a, b in zip(s.regions, ref))
    for pool in POOLS:                       # interior classes, then the frame corner and edge pools
        tot, sq = class_terms([c[pool] for c in cc])
        e += CLS_W * sq + CLS_LIN * tot
    G = np.array([s.diag[:NB] for s in st])
    N = np.array([s.counts for s in st])
    for arr, tol, w in ((G, DIAG_TOL, DIAG_W), (N, TIER_TOL, TIER_W)):
        spread = arr.max(0) - arr.min(0)
        e += w * (np.maximum(0, spread - tol) ** 2).sum() + 0.3 * spread.sum()
    J = np.array([s.junction for s in st])
    e += 0.5 * max(0, J.max() - J.min() - 6) ** 2
    e += sum(ANOMALY_W * (s.tips + s.anomalies) + RUN_W * s.run for s in st)
    e += sum(30.0 * (s.edges[NB:].sum() + s.corners[NB:].sum()) for s in st)   # S touches only L (8-nb)
    e += 0.08 * sum(s.corners[:NB].sum() for s in st)   # mild preference for smooth lines
    e += 1.0 * changes
    return e


def soft_band(t, radius=SOFT_RADIUS):
    """Cells within `radius` (Chebyshev) of a boundary: the only cells the balancer may change."""
    b = BUDGET_TIER[t]
    R, C = b.shape
    edge = np.zeros(b.shape, bool)
    h = is_boundary(b[:, :-1], b[:, 1:])
    v = is_boundary(b[:-1], b[1:])
    edge[:, :-1] |= h; edge[:, 1:] |= h; edge[:-1] |= v; edge[1:] |= v
    band = edge.copy()
    for _ in range(radius - 1):
        p = np.pad(band, 1)
        band = np.zeros_like(band)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                band |= p[1 + dr:1 + dr + R, 1 + dc:1 + dc + C]
    return band


DOMINO = 0.5      # v2: share of moves that flip two adjacent cells together
SIDE4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


RANK_OF_CODE = np.array([RANK[ch] for ch in "DMLSW"])   # code (CODE order) -> rank in budget_v3's ORDER


POOLS = ("int", "corner", "edge")   # interior classes, frame corners, other frame cells


def class_state(rk):
    """Label of every cell (interior: merged class or None; frame: plain tier or class) and the count of
    each label per pool."""
    R, C = rk.shape
    grid = np.empty((R, C), object)
    cnt = {k: Counter() for k in POOLS}
    for r in range(R):
        for c in range(C):
            lab = cell_label(rk, r, c)
            grid[r, c] = lab
            if lab:
                cnt[pool_of(R, C, r, c)][lab] += 1
    return grid, cnt


def class_delta(rk, grid, cells):
    """Labels of the cells within one step of the changed cells (a label depends on the 8 neighbours),
    and the change of each pool's label counts they cause."""
    R, C = rk.shape
    aff = {(y + dy, x + dx) for y, x in cells for dy in (-1, 0, 1) for dx in (-1, 0, 1)
           if 0 <= y + dy < R and 0 <= x + dx < C}
    new = {p: cell_label(rk, *p) for p in aff}
    delta = {k: Counter() for k in POOLS}
    for p, k in new.items():
        old = grid[p]
        if old != k:
            pool = pool_of(R, C, *p)
            if old:
                delta[pool][old] -= 1
            if k:
                delta[pool][k] += 1
    return new, delta


def balance(start, locked, run_limit, iters, seed, T0=6.0):
    """Seeded annealing of the unprotected boundary cells (see module docstring). The class counts
    are kept up to date cell by cell; a rejected move restores the tiers, ranks and classes."""
    rng = np.random.default_rng(seed)
    maps = {n: start[n].copy() for n in NAMES}
    R, C = maps[NAMES[0]].shape
    prot = {}
    for n in NAMES:
        main, fig = figure_mask(maps[n], FIGURE[n])
        near_main = np.zeros_like(main)
        near_main[1:] |= main[:-1]; near_main[:-1] |= main[1:]
        near_main[:, 1:] |= main[:, :-1]; near_main[:, :-1] |= main[:, 1:]
        fixed = fig | locked[n] | (maps[n] == CODE["S"])          # v2: W cells may move
        prot[n] = (fixed | ~soft_band(maps[n]), near_main)
    st = {n: Stats(maps[n], run_limit) for n in NAMES}
    ref = [st[n].regions for n in NAMES]
    rk = {n: RANK_OF_CODE[maps[n]] for n in NAMES}
    grid, cnt = {}, {}
    for n in NAMES:
        grid[n], cnt[n] = class_state(rk[n])
    changes = 0
    cur = energy([st[n] for n in NAMES], changes, ref, [cnt[n] for n in NAMES])
    best = (cur, {n: maps[n].copy() for n in NAMES})
    T1 = 0.05
    for it in range(iters):
        T = T0 * (T1 / T0) ** (it / iters)
        n = NAMES[rng.integers(3)]
        t = maps[n]
        fixed, near_main = prot[n]
        r, c = int(rng.integers(R)), int(rng.integers(C))
        if fixed[r, c]:
            continue
        nb = {int(BUDGET_TIER[t[rr, cc]]) for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1),
                                                         (r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1))
              if 0 <= rr < R and 0 <= cc < C}
        nb = {k for k in nb if CHARS[k] in BACKGROUND[n] and k != BUDGET_TIER[t[r, c]]}
        if near_main[r, c]:
            nb.discard(CODE[FIGURE[n]])
        if not nb:
            continue
        new = rng.choice(sorted(nb))
        cells = [(r, c)]
        if rng.random() < DOMINO:     # v2: flip a domino (two side neighbours of one tier) together,
            dr, dc = SIDE4[rng.integers(4)]          # so a straight line can move by a 2-wide bump
            r2, c2 = r + dr, c + dc
            if not (0 <= r2 < R and 0 <= c2 < C) or fixed[r2, c2] or t[r2, c2] != t[r, c] \
                    or (near_main[r2, c2] and new == CODE[FIGURE[n]]):
                continue
            cells.append((r2, c2))
        olds = [t[y, x] for y, x in cells]
        olds_rk = [rk[n][y, x] for y, x in cells]
        for y, x in cells:
            t[y, x] = new
            rk[n][y, x] = RANK_OF_CODE[new]
        s_new = Stats(t, run_limit)
        d_change = sum(int(new != start[n][y, x]) - int(o != start[n][y, x]) for (y, x), o in zip(cells, olds))
        new_cls, delta = class_delta(rk[n], grid[n], cells)
        cand_cnt = {k: Counter(v) for k, v in cnt[n].items()}
        for k in POOLS:
            cand_cnt[k].update(delta[k])
        cc = [cand_cnt if k == n else cnt[k] for k in NAMES]
        cand = {**st, n: s_new}
        e = energy([cand[k] for k in NAMES], changes + d_change, ref, cc)
        if e <= cur or rng.random() < np.exp((cur - e) / T):
            st[n], cur = s_new, e
            changes += d_change
            cnt[n] = cand_cnt
            for p, k in new_cls.items():
                grid[n][p] = k
            if e < best[0]:
                best = (e, {k: maps[k].copy() for k in NAMES})
        else:
            for (y, x), o, ok in zip(cells, olds, olds_rk):
                t[y, x] = o
                rk[n][y, x] = ok
    return best[1], best[0]


def _balance_job(args):
    return balance(*args)


def best_of_seeds(start, locked, rows, cols, run_limit, T0=6.0):
    iters = ITERS_PER_CELL * rows * cols
    jobs = [(start, locked, run_limit, iters, SEED + k, T0) for k in range(SEEDS)]
    with Pool(min(SEEDS, os.cpu_count() or 1)) as pool:
        runs = pool.map(_balance_job, jobs)
    for k, (_, e) in enumerate(runs):
        print(f"  {cols}x{rows} T0 {T0} seed {SEED + k}: energy {e:.1f}", flush=True)
    return min(runs, key=lambda r: r[1])[0]


def run_limit_for(cols):
    """Straight boundary runs above 5 edges per 20 columns are penalized (7 at 27 columns)."""
    return max(5, round(5 * cols / 20))


def v2_start(n):
    """The v2 picture of tier n (27x38-v2/tiers-n.txt) as a code map: the start of v3."""
    rows = [ln.split() for ln in (V2_DIR / f"tiers-{n}.txt").read_text().splitlines() if ln.strip()]
    assert len(rows) == SKETCH_ROWS and all(len(r) == SKETCH_COLS for r in rows), n
    return np.array([[CODE[ch] for ch in r] for r in rows], np.int8)


def make():
    """(start, balanced, run limit) at 27 x 38. The start is the v2 pictures. The sketches give the
    locked cells, and the v2 pictures must agree with them there (checked)."""
    parsed = {n: parse(SKETCHES[n]) for n in NAMES}
    locked = {n: parsed[n][1] for n in NAMES}
    start = {n: v2_start(n) for n in NAMES}
    for n in NAMES:
        assert (start[n][locked[n]] == parsed[n][0][locked[n]]).all(), f"{n}: a locked cell differs from its sketch"
    lim = run_limit_for(SKETCH_COLS)
    first = best_of_seeds(start, locked, SKETCH_ROWS, SKETCH_COLS, lim, T0=FIRST_T0)
    return start, best_of_seeds(first, locked, SKETCH_ROWS, SKETCH_COLS, lim, T0=POLISH_T0), lim


# ---- output -----------------------------------------------------------------------------
INK = (0, 0, 0)
PAL = {0: (43, 50, 98), 1: (138, 140, 76), 2: (236, 227, 200), 3: (236, 227, 200), 4: (138, 140, 76)}


def tier_image(t, up=16):
    R, C = t.shape
    img = Image.new("RGB", (C * up, R * up))
    d = ImageDraw.Draw(img)
    for r in range(R):
        for c in range(C):
            x, y = c * up, r * up
            d.rectangle([x, y, x + up - 1, y + up - 1], fill=PAL[int(t[r, c])])
            if t[r, c] == 3:                                      # S: navy chips on cream
                for j in range(2, up, 5):
                    for k in range(1 + (j % 2) * 2, up, 5):
                        d.rectangle([x + k, y + j, x + k + 1, y + j + 1], fill=PAL[0])
            if t[r, c] == 4:                                      # W: cream lenses on olive
                for j in (4, 11):
                    d.line([x + 3 + j % 3, y + j, x + 10 + j % 3, y + j], fill=PAL[2], width=2)
    return img


def contour_image(t, up=16, width=2):
    """Ink mode: tier boundaries (budget pairs only) as black lines on white; S dots, W dashes."""
    b = BUDGET_TIER[t]
    R, C = b.shape
    img = Image.new("RGB", (C * up + 1, R * up + 1), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, C * up, R * up], outline=(170, 170, 170))
    for r in range(R):
        for c in range(C):
            if c + 1 < C and is_boundary(b[r, c], b[r, c + 1]):
                d.line([(c + 1) * up, r * up, (c + 1) * up, (r + 1) * up], fill=INK, width=width)
            if r + 1 < R and is_boundary(b[r, c], b[r + 1, c]):
                d.line([c * up, (r + 1) * up, (c + 1) * up, (r + 1) * up], fill=INK, width=width)
            if t[r, c] == 3:
                for j, k in ((4, 4), (10, 7), (5, 11)):
                    d.ellipse([c * up + k - 1, r * up + j - 1, c * up + k + 1, r * up + j + 1], fill=INK)
            if t[r, c] == 4:
                d.line([c * up + 4, r * up + 8, c * up + 11, r * up + 8], fill=INK, width=1)
    return img


def sheet(rows_of_images, path, gap=14):
    """Panels side by side on white, with no text (the previews double as blind-test material)."""
    w, h = rows_of_images[0][0].size
    n = len(rows_of_images[0])
    can = Image.new("RGB", (n * w + (n + 1) * gap, len(rows_of_images) * (h + gap) + gap), (255, 255, 255))
    for i, row in enumerate(rows_of_images):
        for j, im in enumerate(row):
            can.paste(im, (gap + j * (w + gap), gap + i * (h + gap)))
    can.save(path)


def write_tiers(t, path):
    path.write_text("\n".join(" ".join(CHARS[v] for v in row) for row in t) + "\n")


def extra_rows(maps):
    """Table row for the tile item the coordinator asked to track beyond budget_v2: tips."""
    st = [Stats(maps[n], 10 ** 6) for n in NAMES]
    vals = [s.tips for s in st]
    return f"{'tips (1-cell caps)':24s}" + "".join(f"{v:9d}" for v in vals) + f"{max(vals) - min(vals):9d}"


def write_outputs(start, maps, out, rows, cols, run_limit):
    out.mkdir(parents=True, exist_ok=True)
    for n in NAMES:
        write_tiers(maps[n], out / f"tiers-{n}.txt")
    named = {TITLES[n].split(" (")[0]: budgets(CHARS[maps[n]]) for n in NAMES}
    moved = {n: int((maps[n] != start[n]).sum()) for n in NAMES}
    now = {n: class_counts(CHARS[maps[n]]) for n in NAMES}
    before = {n: class_counts(CHARS[start[n]]) for n in NAMES}
    frame_now = {n: frame_counts(CHARS[maps[n]]) for n in NAMES}
    frame_before = {n: frame_counts(CHARS[start[n]]) for n in NAMES}
    fsur = lambda fc: {pool: sum(max(fc[n][pool].get(k, 0) for n in NAMES) - fc[m][pool].get(k, 0)
                                 for k in {k for n in NAMES for k in fc[n][pool]} for m in NAMES)
                       for pool in ("corner", "edge")}
    sur_now = {n: sum(v.values()) for n, v in class_surplus(now)[1].items()}
    sur_before = {n: sum(v.values()) for n, v in class_surplus(before)[1].items()}
    cls_names = {n: TITLES[n].split(" (")[0] for n in NAMES}
    report = [
        f"# Boundary budgets, experiment 011 (Field, Wood and Water), {cols} columns x {rows} rows, v3.",
        "# Columns: A hare, B owl, C swan. v3 matches the transition CLASSES (budget_v3.py, the pipeline's",
        "# classify stage): per ordered tier pair and pattern s (straight), c (corner), p (cap), d (dot).",
        "# The surplus of a picture is the sum over classes of (max over pictures minus its own count);",
        "# v3 target: total under 30. The pair edges and corners below are reported, not matched.",
        "# Tier totals: target equal in the three pictures (spread in the cells rows; not exact in v3). Anomalies need rare tiles (target 0; the dots are",
        "# designed: one D-on-L and one D-on-M dot per picture). Tips = 1-cell protrusions (caps).",
        f"# Straight runs are penalized above {run_limit} edges. Cells moved by the balancer from the v2",
        "# picture: " + ", ".join(f"{n} {moved[n]}" for n in NAMES),
        "# Class surplus, v2 start: " + ", ".join(f"{n} {sur_before[n]}" for n in NAMES)
        + f" (total {sum(sur_before.values())}); v3: " + ", ".join(f"{n} {sur_now[n]}" for n in NAMES)
        + f" (total {sum(sur_now.values())})",
        f"# Frame (border) surplus, v2 start: corner {fsur(frame_before)['corner']}, edge {fsur(frame_before)['edge']};"
        f" v3: corner {fsur(frame_now)['corner']}, edge {fsur(frame_now)['edge']}",
        "",
        table(named),
        extra_rows(maps),
        "",
        "# Transition classes (merged, as the pipeline's classify stage counts them), interior cells:",
        class_table({cls_names[n]: now[n] for n in NAMES}),
        "",
        "# Frame histogram, v2 start (before):",
        frame_table({cls_names[n]: frame_before[n] for n in NAMES}),
        "",
        "# Frame histogram, v3 (after): corner pool (4 cells) and edge pool; labels are plain tiers or classes:",
        frame_table({cls_names[n]: frame_now[n] for n in NAMES}),
    ]
    (out / "budgets.txt").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    up = 16
    sheet([[tier_image(maps[n], up) for n in NAMES]], out / "targets-preview.png")
    sheet([[contour_image(maps[n], up) for n in NAMES]], out / "contours-preview.png")


def main(argv):
    """Usage: make_targets_v3.py [27x38]   Writes 27x38-v3/ (tiers, budgets, two previews, no text)."""
    for size in argv or [PRIMARY]:
        cols, rows = (int(v) for v in size.lower().split("x"))
        assert (cols, rows) == (SKETCH_COLS, SKETCH_ROWS), "v3 balances the 27 x 38 pictures only"
        print(f"== {cols}x{rows}", flush=True)
        start, maps, run_limit = make()
        write_outputs(start, maps, HERE / f"{cols}x{rows}{OUT_SUFFIX}", rows, cols, run_limit)


if __name__ == "__main__":
    main(sys.argv[1:])
