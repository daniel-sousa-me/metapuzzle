"""Tier targets for experiment 011: "Field, Wood and Water" (version 4: class surplus, outline moves).

Copy of make_targets_v3.py, changed as follows.
1. The frame-histogram objective is dropped (the product uses a tray border, docs/DECISIONS.md, 2026-10-27).
   The class counts are interior cells only, as the pipeline's classify stage counts them.
2. The class term is the SURPLUS that budget_v3 reports: per class, the sum over the pictures of
   (max over pictures minus own count). v3 minimized the spread (max minus min) instead.
3. Figure outlines move by one cell: an outline cell of the figure may become the background tier beside it,
   and a background cell beside the figure may become the figure tier. A changed figure cell costs FIG_W
   (background cells cost BG_W); at most FIG_CAP figure cells change per picture.
4. S chips and W regions move by one cell too: a chip on the outline may become L, an L cell beside a chip
   may become S, and W cells move as background tiers. Changes in the S/W zone cost SW_W. Chips stay enclosed
   by L (hard: no S touching D, M or W in the 8-neighbourhood).
5. Locked cells: the sketch's locked features, the 3x3 around each hero cell (docs/design/10-motif-vocabulary.md;
   a hero's class and plainness depend on its 8 neighbours), and the top rows of each hare ear and owl tuft.
6. Hard per move: no new anomaly (1-cell tip, 1-wide strip, isolated cell, diagonal-only contact) beyond the
   start's count (the two designed dots per picture), and no S touching D, M or W.
7. Restarts: the first pass starts from the v2 pictures (as v3); later passes start from the best result with
   a cooler start and new seeds, until the surplus is under TARGET or STALL_ROUNDS rounds stall.

Outputs: 27x38-v4/ (tiers-A/B/C.txt, budgets.txt, targets-preview.png and contours-preview.png without labels).
Usage: python3 make_targets_v4.py [27x38]
"""
import os
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from budget_v2 import PAIRS, FORBIDDEN, budgets, table  # noqa: E402
from budget_v3 import RANK, cell_class, class_counts, class_surplus, class_table  # noqa: E402

PRIMARY = "27x38"   # COLSxROWS of the native drawings and primary deliverable
OUT_SUFFIX = "-v4"  # outputs go to 27x38-v4/ (v2 and v3 outputs are kept)
V2_DIR = HERE / "27x38-v2"  # the start: the v2 pictures (as v3)
NAMES = ["A", "B", "C"]
TITLES = {"A": "A hare (dawn)", "B": "B owl (dusk)", "C": "C swan (midnight)"}
FIGURE = {"A": "M", "B": "D", "C": "L"}
BACKGROUND = {"A": "DLW", "B": "MLW", "C": "DMLW"}
SEED = 11
SEEDS = 4
ITERS_PER_CELL = 800   # v4: the runs plateau early (tested at 400k iterations per picture)
FIRST_T0 = 2.0      # first pass from the v2 pictures
RESTART_T0 = 0.6    # later passes start from the best result
MAX_ROUNDS = 6
STALL_ROUNDS = 2
TARGET = 30         # the surplus goal (total over the three pictures)
SOFT_RADIUS = 1
FIG_CAP = 25        # changed figure-outline cells per picture
FIG_W, SW_W, BG_W = 3.0, 1.5, 1.0   # energy cost per changed cell, by static kind
KIND_FIG, KIND_SW, KIND_BG = 0, 1, 2
KIND_W = np.array([FIG_W, SW_W, BG_W])
KIND_NAME = {KIND_FIG: "figure", KIND_SW: "S/W zone", KIND_BG: "background"}
CLS_LIN = 30.0      # energy per unit of class surplus (tested 1 to 30: 30 gave the lowest surplus)

# Hero cells (row, col) from motifs/make_motif_maps.py HEROES, the same grid as the v2 pictures.
HERO_CELLS = {
    "A": [(11, 0), (11, 1), (6, 24), (6, 25), (3, 11), (25, 24), (12, 17), (5, 21), (14, 20)],
    "B": [(12, 7), (12, 15), (12, 8), (12, 16), (4, 15), (5, 9), (15, 1), (35, 24), (16, 12)],
    "C": [(6, 5), (7, 5), (1, 19), (1, 24), (3, 21), (5, 23), (32, 5), (5, 11), (16, 5)],
}
# Ears (hare, top three rows) and tufts (owl, top two rows) as inclusive boxes; the figure tier cells are locked.
EAR_BOXES = {"A": [(2, 4, 5, 9), (2, 4, 13, 18)], "B": [(10, 11, 3, 7), (10, 11, 18, 22)], "C": []}

SKETCHES = {}  # filled below
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
        # S touching D, M or W in the 8-neighbourhood (hard in v4); outside the picture counts as L
        bad_nb = np.pad((b == CODE["D"]) | (b == CODE["M"]) | (b == CODE["W"]), 1)
        touch = np.zeros(b.shape, bool)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    touch |= bad_nb[1 + dr:1 + dr + R, 1 + dc:1 + dc + C]
        self.s_bad = int(((b == CODE["S"]) & touch).sum())


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




ANOMALY_W = 1000.0   # anomalies are also a hard constraint (see balance); the weight is a backstop
DIAG_TOL, DIAG_W = 4, 0.3   # 45-degree runs are tracked, matched more loosely than edges and corners
RUN_W = 25.0      # per edge of a straight run above the limit
TIER_TOL, TIER_W = 0, 0.5     # tier totals (D M W L S) near equal (v3: 4.0; relaxed, the spreads are reported)
DOMINO = 0.5      # share of background moves that flip two adjacent cells together
SIDE4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
RANK_OF_CODE = np.array([RANK[ch] for ch in "DMLSW"])   # code (CODE order) -> rank in budget_v3's ORDER
SW_CODES = (CODE["S"], CODE["W"])


def class_surplus_total(cc):
    """Surplus over the pictures (budget_v3 sense): per class, sum over pictures of (max minus own)."""
    keys = set().union(*[set(c) for c in cc])
    tot = 0
    for k in keys:
        vals = [c.get(k, 0) for c in cc]
        tot += len(vals) * max(vals) - sum(vals)
    return tot


def energy(st, changes, ref_regions, cc):
    """st: per picture Stats; cc: per picture Counter of interior class labels; changes: weighted cell cost."""
    e = 0.0
    for s, ref in zip(st, ref_regions):
        e += 40.0 * sum(abs(a - b) for a, b in zip(s.regions, ref))
    e += CLS_LIN * class_surplus_total(cc)
    G = np.array([s.diag[:NB] for s in st])
    N = np.array([s.counts for s in st])
    for arr, tol, w in ((G, DIAG_TOL, DIAG_W), (N, TIER_TOL, TIER_W)):
        spread = arr.max(0) - arr.min(0)
        e += w * (np.maximum(0, spread - tol) ** 2).sum() + 0.3 * spread.sum()
    J = np.array([s.junction for s in st])
    e += 0.5 * max(0, J.max() - J.min() - 6) ** 2
    e += sum(ANOMALY_W * (s.tips + s.anomalies) + RUN_W * s.run for s in st)
    e += sum(30.0 * (s.edges[NB:].sum() + s.corners[NB:].sum()) for s in st)   # S touches only L
    e += 0.08 * sum(s.corners[:NB].sum() for s in st)   # mild preference for smooth lines
    e += changes
    return e


def soft_band(t):
    """Cells on a tier boundary (4-neighbour): the only cells the balancer may change."""
    b = BUDGET_TIER[t]
    edge = np.zeros(b.shape, bool)
    h = is_boundary(b[:, :-1], b[:, 1:])
    v = is_boundary(b[:-1], b[1:])
    edge[:, :-1] |= h; edge[:, 1:] |= h; edge[:-1] |= v; edge[1:] |= v
    return edge


def near4(mask):
    out = np.zeros_like(mask)
    out[1:] |= mask[:-1]; out[:-1] |= mask[1:]
    out[:, 1:] |= mask[:, :-1]; out[:, :-1] |= mask[:, 1:]
    return out


def figure_sets(start_map, n):
    """figcat: the figure's main region plus its 4-neighbours outside the figure (the figure-outline zone);
    holes: the cells enclosed by the figure (fixed)."""
    main, filled = figure_mask(start_map, FIGURE[n])
    holes = filled & ~main
    figcat = main | (near4(main) & ~filled)
    return figcat, holes


def cell_kinds(start_map, figcat):
    """Static kind per cell of the start picture: figure zone, S/W zone (an S or W cell or beside one), or
    background. The energy cost of a change is KIND_W of the cell's kind."""
    sw = (start_map == CODE["S"]) | (start_map == CODE["W"])
    return np.where(figcat, KIND_FIG, np.where(sw | near4(sw), KIND_SW, KIND_BG))


def locked_mask(n, sketch_locked, start_map):
    """The sketch's locked features, the 3x3 around each hero cell, and the figure-tier cells of each ear."""
    lock = sketch_locked.copy()
    for r, c in HERO_CELLS[n]:
        lock[max(0, r - 1):r + 2, max(0, c - 1):c + 2] = True
    for r0, r1, c0, c1 in EAR_BOXES[n]:
        lock[r0:r1 + 1, c0:c1 + 1] |= start_map[r0:r1 + 1, c0:c1 + 1] == CODE[FIGURE[n]]
    return lock


def nb_codes(t, r, c):
    R, C = t.shape
    return {int(t[y, x]) for y in range(max(0, r - 1), min(R, r + 2))
            for x in range(max(0, c - 1), min(C, c + 2)) if (y, x) != (r, c)}


def side_codes(t, r, c):
    R, C = t.shape
    return [int(t[y, x]) for y, x in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)) if 0 <= y < R and 0 <= x < C]


def candidates(t, n, figcat_n, r, c):
    """New tiers one step away for cell (r, c): tiers of its 8 neighbours that the picture may use here.
    Chips move only to L; an L cell beside a chip may become a chip; figure-zone cells may take the figure tier."""
    cur = int(t[r, c])
    if cur == CODE["S"]:
        return nb_codes(t, r, c) & {CODE["L"]}
    allowed = {CODE[ch] for ch in BACKGROUND[n]}
    if figcat_n[r, c]:
        allowed.add(CODE[FIGURE[n]])
    if cur == CODE["L"] and CODE["S"] in side_codes(t, r, c):
        allowed.add(CODE["S"])
    return (nb_codes(t, r, c) & allowed) - {cur}


def class_state(rk):
    """Interior class label of every cell (None for plain and frame cells) and the count of each class."""
    R, C = rk.shape
    grid = np.empty((R, C), object)
    cnt = Counter()
    for r in range(R):
        for c in range(C):
            lab = cell_class(rk, r, c)
            grid[r, c] = lab
            if lab:
                cnt[lab] += 1
    return grid, cnt


def class_delta(rk, grid, cells):
    """Labels of the cells within one step of the changed cells (a label depends on the 8 neighbours),
    and the change of the class counts they cause."""
    R, C = rk.shape
    aff = {(y + dy, x + dx) for y, x in cells for dy in (-1, 0, 1) for dx in (-1, 0, 1)
           if 0 <= y + dy < R and 0 <= x + dx < C}
    new = {p: cell_class(rk, *p) for p in aff}
    delta = Counter()
    for p, k in new.items():
        old = grid[p]
        if old != k:
            if old:
                delta[old] -= 1
            if k:
                delta[k] += 1
    return new, delta


def balance(init, start, locked, run_limit, iters, seed, T0):
    """Seeded annealing from `init`. Moves: background cells on a tier boundary (with domino flips), figure
    outline cells (one cell, FIG_CAP per picture), chips and the cells beside them. Hard constraints per move:
    no new anomaly beyond the start's count, no S touching D, M or W, figure cap. The class surplus is kept
    up to date cell by cell; a rejected move restores the tiers, ranks and classes."""
    rng = np.random.default_rng(seed)
    maps = {n: init[n].copy() for n in NAMES}
    R, C = maps[NAMES[0]].shape
    figcat, holes, kind, movable, base = {}, {}, {}, {}, {}
    for n in NAMES:
        figcat[n], holes[n] = figure_sets(start[n], n)
        kind[n] = cell_kinds(start[n], figcat[n])
        movable[n] = soft_band(maps[n]) & ~locked[n] & ~holes[n]
        s0 = Stats(start[n], run_limit)
        base[n] = s0.tips + s0.anomalies
    st = {n: Stats(maps[n], run_limit) for n in NAMES}
    ref = [st[n].regions for n in NAMES]
    rk = {n: RANK_OF_CODE[maps[n]] for n in NAMES}
    grid, cnt = {}, {}
    for n in NAMES:
        grid[n], cnt[n] = class_state(rk[n])
    changes = 0.0
    figs = {n: int((figcat[n] & (maps[n] != start[n])).sum()) for n in NAMES}
    cur = energy([st[n] for n in NAMES], changes, ref, [cnt[n] for n in NAMES])
    best = (cur, {n: maps[n].copy() for n in NAMES})
    T1 = 0.05
    for it in range(iters):
        T = T0 * (T1 / T0) ** (it / iters)
        n = NAMES[rng.integers(3)]
        t = maps[n]
        fig = CODE[FIGURE[n]]
        r, c = int(rng.integers(R)), int(rng.integers(C))
        if not movable[n][r, c]:
            continue
        cands = candidates(t, n, figcat[n], r, c)
        if not cands:
            continue
        new = int(rng.choice(sorted(cands)))
        cells = [(r, c)]
        if kind[n][r, c] == KIND_BG and int(t[r, c]) not in (CODE["S"], fig) and new not in (CODE["S"], fig) \
                and rng.random() < DOMINO:
            dr, dc = SIDE4[rng.integers(4)]
            r2, c2 = r + dr, c + dc
            if not (0 <= r2 < R and 0 <= c2 < C) or not movable[n][r2, c2] or kind[n][r2, c2] != KIND_BG \
                    or t[r2, c2] != t[r, c] or t[r2, c2] in (CODE["S"], fig):
                continue
            cells.append((r2, c2))
        olds = [int(t[y, x]) for y, x in cells]
        olds_rk = [int(rk[n][y, x]) for y, x in cells]
        d_change, d_fig = 0.0, 0
        for (y, x), o in zip(cells, olds):
            s0c = start[n][y, x]
            dv = int(new != s0c) - int(o != s0c)
            d_change += KIND_W[kind[n][y, x]] * dv
            if figcat[n][y, x]:
                d_fig += dv

        def restore():
            for (y, x), o, ok in zip(cells, olds, olds_rk):
                t[y, x] = o
                rk[n][y, x] = ok

        for y, x in cells:
            t[y, x] = new
            rk[n][y, x] = RANK_OF_CODE[new]
        if figs[n] + d_fig > FIG_CAP:
            restore()
            continue
        s_new = Stats(t, run_limit)
        if s_new.s_bad or s_new.tips + s_new.anomalies > base[n]:
            restore()
            continue
        new_cls, delta = class_delta(rk[n], grid[n], cells)
        cand_cnt = cnt[n].copy()
        cand_cnt.update(delta)
        cc = [cand_cnt if k == n else cnt[k] for k in NAMES]
        cand_st = [s_new if k == n else st[k] for k in NAMES]
        e = energy(cand_st, changes + d_change, ref, cc)
        if e <= cur or rng.random() < np.exp((cur - e) / T):
            st[n], cur = s_new, e
            changes += d_change
            figs[n] += d_fig
            cnt[n] = cand_cnt
            for p, k in new_cls.items():
                grid[n][p] = k
            if e < best[0]:
                best = (e, {k: maps[k].copy() for k in NAMES})
        else:
            restore()
    return best[1], best[0]


def _balance_job(args):
    return balance(*args)


def best_of_seeds(init, start, locked, rows, cols, run_limit, T0, seed0):
    iters = ITERS_PER_CELL * rows * cols
    jobs = [(init, start, locked, run_limit, iters, seed0 + k, T0) for k in range(SEEDS)]
    with Pool(min(SEEDS, os.cpu_count() or 1)) as pool:
        runs = pool.map(_balance_job, jobs)
    for k, (_, e) in enumerate(runs):
        print(f"  {cols}x{rows} T0 {T0} seed {seed0 + k}: energy {e:.1f}", flush=True)
    return min(runs, key=lambda r: r[1])[0]


def run_limit_for(cols):
    """Straight boundary runs above 5 edges per 20 columns are penalized (7 at 27 columns)."""
    return max(5, round(5 * cols / 20))


def v2_start(n):
    """The v2 picture of tier n (27x38-v2/tiers-n.txt) as a code map: the start of v4."""
    rows = [ln.split() for ln in (V2_DIR / f"tiers-{n}.txt").read_text().splitlines() if ln.strip()]
    assert len(rows) == SKETCH_ROWS and all(len(r) == SKETCH_COLS for r in rows), n
    return np.array([[CODE[ch] for ch in r] for r in rows], np.int8)


def surplus_total(maps):
    top, sur = class_surplus({n: class_counts(CHARS[maps[n]]) for n in NAMES})
    return sum(sum(v.values()) for v in sur.values())


def make():
    """(start, balanced, locked, run limit, history) at 27 x 38. The start is the v2 pictures; the sketches
    give the locked features, and the v2 pictures must agree with them there (checked)."""
    parsed = {n: parse(SKETCHES[n]) for n in NAMES}
    sketch_locked = {n: parsed[n][1] for n in NAMES}
    start = {n: v2_start(n) for n in NAMES}
    for n in NAMES:
        assert (start[n][sketch_locked[n]] == parsed[n][0][sketch_locked[n]]).all(), f"{n}: a locked cell differs"
    locked = {n: locked_mask(n, sketch_locked[n], start[n]) for n in NAMES}
    lim = run_limit_for(SKETCH_COLS)
    best, best_s, stall, history, maps = None, None, 0, [], start
    for rnd in range(MAX_ROUNDS):
        T0 = FIRST_T0 if rnd == 0 else RESTART_T0
        out = best_of_seeds(maps, start, locked, SKETCH_ROWS, SKETCH_COLS, lim, T0, SEED + 100 * rnd)
        s = surplus_total(out)
        history.append((rnd, T0, s))
        print(f"round {rnd} (T0 {T0}): surplus {s}", flush=True)
        if best is None or s < best_s:
            improved = best is None or best_s - s >= 1
            best, best_s = out, s
            stall = 0 if improved else stall + 1
        else:
            stall += 1
        maps = best
        if best_s < TARGET or stall >= STALL_ROUNDS:
            break
    return start, best, locked, lim, history


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
    st = [Stats(maps[n], 10 ** 6) for n in NAMES]
    vals = [s.tips for s in st]
    return f"{'tips (1-cell caps)':24s}" + "".join(f"{v:9d}" for v in vals) + f"{max(vals) - min(vals):9d}"


def moved_by_kind(start, maps):
    """Changed cells per picture by kind: figure (figure-zone cell), S (start or new tier S), W (start or new
    tier W), background (the rest). Priority in that order."""
    out = {}
    for n in NAMES:
        figcat, _ = figure_sets(start[n], n)
        changed = maps[n] != start[n]
        s_inv = changed & ((start[n] == CODE["S"]) | (maps[n] == CODE["S"]))
        w_inv = changed & ((start[n] == CODE["W"]) | (maps[n] == CODE["W"]))
        fig = changed & figcat
        out[n] = {"background": int((changed & ~figcat & ~s_inv & ~w_inv).sum()),
                  "figure": int(fig.sum()), "W": int((w_inv & ~figcat & ~s_inv).sum()),
                  "S": int((s_inv & ~figcat).sum())}
    return out


def write_outputs(start, maps, locked, out, rows, cols, run_limit, history):
    from budget_v2 import load
    out.mkdir(parents=True, exist_ok=True)
    for n in NAMES:
        write_tiers(maps[n], out / f"tiers-{n}.txt")
    named = {TITLES[n].split(" (")[0]: budgets(CHARS[maps[n]]) for n in NAMES}
    now = {n: class_counts(CHARS[maps[n]]) for n in NAMES}
    before = {n: class_counts(CHARS[start[n]]) for n in NAMES}
    sur_before = {n: sum(v.values()) for n, v in class_surplus(before)[1].items()}
    sur_now = {n: sum(v.values()) for n, v in class_surplus(now)[1].items()}
    cls_names = {n: TITLES[n].split(" (")[0] for n in NAMES}
    moved = {n: int((maps[n] != start[n]).sum()) for n in NAMES}
    kinds = moved_by_kind(start, maps)
    # hero classes and locked cells unchanged
    hero_changed = {n: sum(cell_class(RANK_OF_CODE[maps[n]], r, c) != cell_class(RANK_OF_CODE[start[n]], r, c)
                           for r, c in HERO_CELLS[n]) for n in NAMES}
    locked_changed = {n: int((locked[n] & (maps[n] != start[n])).sum()) for n in NAMES}
    # the written files, read back and counted with budget_v3's class_counts (the pipeline's classify copy)
    reread = {n: class_counts(load(out / f"tiers-{n}.txt")) for n in NAMES}
    match = all(reread[n] == now[n] for n in NAMES)
    report = [
        f"# Boundary budgets, experiment 011 (Field, Wood and Water), {cols} columns x {rows} rows, v4.",
        "# Columns: A hare, B owl, C swan. v4 matches the transition CLASSES (budget_v3.py, the pipeline's",
        "# classify stage; interior cells, frame excluded): per ordered tier pair and pattern s, c, p, d.",
        "# The surplus of a picture is the sum over classes of (max over pictures minus its own count).",
        "# The frame histogram is not matched (tray border). The pair edges and corners are reported, not matched.",
        "# Hard per move: no anomaly beyond the start (two designed dots per picture), no S touching D, M or W,",
        f"# figure outline cells changed at most {FIG_CAP} per picture. Locked: sketch features, 3x3 around the heroes, ear tops.",
        f"# Straight runs are penalized above {run_limit} edges.",
        "# Cells changed from the v2 start: " + ", ".join(f"{n} {moved[n]}" for n in NAMES),
        "# By kind (figure / S / W / background): " + "; ".join(
            f"{n} {kinds[n]['figure']} / {kinds[n]['S']} / {kinds[n]['W']} / {kinds[n]['background']}" for n in NAMES),
        "# Class surplus, v2 start: " + ", ".join(f"{n} {sur_before[n]}" for n in NAMES)
        + f" (total {sum(sur_before.values())}); v4: " + ", ".join(f"{n} {sur_now[n]}" for n in NAMES)
        + f" (total {sum(sur_now.values())}), target under {TARGET}",
        "# Rounds (round, T0, total surplus): " + ", ".join(f"({a}, {b}, {c})" for a, b, c in history),
        "# Hero cells whose class changed: " + ", ".join(f"{n} {hero_changed[n]}" for n in NAMES)
        + "; locked cells changed: " + ", ".join(f"{n} {locked_changed[n]}" for n in NAMES),
        "# budget_v3 class_counts of the written tiers files equal the in-memory counts: " + str(match),
        "",
        table(named),
        extra_rows(maps),
        "",
        "# Transition classes (merged, as the pipeline's classify stage counts them), interior cells:",
        class_table({cls_names[n]: now[n] for n in NAMES}),
    ]
    (out / "budgets.txt").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    up = 16
    sheet([[tier_image(maps[n], up) for n in NAMES]], out / "targets-preview.png")
    sheet([[contour_image(maps[n], up) for n in NAMES]], out / "contours-preview.png")


def main(argv):
    """Usage: make_targets_v4.py [27x38]   Writes 27x38-v4/ (tiers, budgets, two previews, no text)."""
    for size in argv or [PRIMARY]:
        cols, rows = (int(v) for v in size.lower().split("x"))
        assert (cols, rows) == (SKETCH_COLS, SKETCH_ROWS), "v4 balances the 27 x 38 pictures only"
        print(f"== {cols}x{rows}", flush=True)
        start, maps, locked, run_limit, history = make()
        write_outputs(start, maps, locked, HERE / f"{cols}x{rows}{OUT_SUFFIX}", rows, cols, run_limit, history)


if __name__ == "__main__":
    main(sys.argv[1:])
