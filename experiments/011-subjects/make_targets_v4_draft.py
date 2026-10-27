"""Tier targets for experiment 011, version 4 DRAFT: recognition cues and scene cues for the animals.

Copy of make_targets.py (v2, natively drawn 27 x 38) with redrawn sketches after blind test v2
(blind-test-v2.md) and evaluation-v6.md (all three read as maps). Method unchanged (locked figure, S and
lower-case features; seeded annealer on background lines; budget_v2 pairs) except SOFT_RADIUS = 2 (cells
within two of a drawn boundary may move). Outputs: 27x38-v4-draft/ (tiers-A/B/C.txt, tiers-X-animal.txt
masks, budgets.txt, targets-preview.png and contours-preview.png without labels).
Usage: python3 make_targets_v4_draft.py [27x38]

        tier   A hare (dawn)                  B owl (dusk)                  C swan (midnight)
        D      hedge band, meadow shadows,    owl, branch, pupils, bat      night sky, near bank, ducks
               foreground shadow, ear tips,
               haunch and leg lines
        M      hare                           dusk sky, beak                lake, clouds, beak
        L      sky, sunlit meadow, tail       moon disc, eyes, snow         swan, moon, stars, glint
        S      starling band (2 x 5)          moon crater band (2 x 5)      wing line (2 x 5)
        W      cloud, meadow mist             wing lines, clouds            water band, reflection, cloud

Internal lines are bands at least two cells wide (one-cell strips are anomalies): hare: eye dot, dark
ear tip, haunch line and front-leg line (D), white tail (L); owl: ear tufts, 7-wide round eyes with
single-cell pupils, a 4-4-2 pointed beak (M), two stepped wing lines (W), legs gripping a branch that
lies on the snow, moon disc behind the head; swan: eye dot, olive (M) beak, wing line (S), raised wing
bump, pointed tail, a two-to-three-row W water band with a reflection drip. Dots matched per picture:
two D-on-L (A crows, B pupils, C eye and a duck on a glint) and one D-on-M (A hare eye, B bat, C duck).
animal_mask(): the figure with its holes, plus locked cells touching it (A ear tips, leg line, tail;
C beak); B without the branch rows.
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

PRIMARY = "27x38"   # COLSxROWS of the native drawings and primary deliverable (owner decision)
OUT_SUFFIX = "-v4-draft"  # outputs go to 27x38-v4-draft/
SMOOTH = 0.55       # Gaussian sigma (sketch cells) used when resampling the sketches
NAMES = ["A", "B", "C"]
TITLES = {"A": "A hare (dawn)", "B": "B owl (dusk)", "C": "C swan (midnight)"}
FIGURE = {"A": "M", "B": "D", "C": "L"}
# Tiers the balancer may paint in each picture (the figure tier only away from the figure).
BACKGROUND = {"A": "DLW", "B": "MLW", "C": "DMLW"}   # v2: W (mist, clouds, water) is background too
SEED = 11         # base seed; SEEDS runs are made and the lowest energy kept
SEEDS = 4
ITERS_PER_CELL = 400
POLISH_T0 = 1.0   # second, cooler annealing pass started from the best first-pass result
SOFT_RADIUS = 2   # v4 draft: 2 = cells on a drawn boundary and their neighbours (v2: 1)

SKETCHES = {}  # filled below

# Hand-drawn 27 x 38 sketches, rows top to bottom. D M S as themselves, '.' = L, 'w' = W.
# Lower case 'd' / 'm' / ',' = D / M / L locked: a drawn feature the balancer must not touch
# (the hare's tree, the swan's clouds, the dots and their neighbours). The figure and S are always
# locked.
SKETCHES["A"] = """
wwwwww....,,,..............
wwwwww....,d,..............
..........,,,..dd..SSSSS...
......dd.......dd..SSSSS...
..,,,.dd......MMMM.........
..,d,..MMM....MMMM.........
..,,,..MMMM...MMMMM........
.......MMMM...MMMMMDDD.....
..DD...MMMMM..MMMMMDDDD..DD
.DDDD..MMMMM..MMMMMDDDDDDDD
DDDDDDDDMMMMMMMMMMMMDDDDDDD
DDDDDDDDDMMMMMMMMMMMDDDDDDD
DDDDDDDDDMMMMMMMMdMMMDDDDDD
DDDDDDDDDMMMMMMMMMMMMMDDDDD
..DDDDDDDDMMMMMMMMMMMMDDDDD
......DDDDDMMMMMMMMMMMDDDDD
......DDDDDDMMMMMMMMMDDDDDD
......DDDDDDMMMMMMwwwDDDDDD
.......wwwMMMMMMMMwww......
.......wwwMMMMMMMMMww......
DDDD.....MMMMMMMMMMMDDDDDDD
DDDD.....MMMMMMMMMMMDDDDDDD
.......MMMMMddMMMMMMMwwwwww
......MMMMMMddMMMMMMMwwwwww
DDD..MMMMMMddMMMMMMMMwwwwww
DDD..MMMMMMddMMMMMMMMwwwwww
wwww,,MMMMddMMMddMMMMwwwwww
wwww,,MMMMddMMMddMMMwwwwwww
wwwMMMMMMMMMMMMddMMMwwwwwww
wwwMMMMMMMMMMMMddMMMwwwwwww
wwwDDDDDDDDDDDDDDDDDwwwwwww
DDDDDDDDDDDDDDDDDDDDDDDDDDD
DDDDDDDDDDDDDDDDDDDDDDDDDDD
DDDDDDDDDDDDDDDDDDDDDDDDDDD
DDDDDDDDDDDDDDDDDDDDDDDDDDD
DDDDDDDDDDDDDDDDDDDDDDDDDDD
DDDDDDDDDDDDDDDDDDDDDDDDDDD
DDDDDDDDDDDDDDDDDDDDDDDDDDD
"""

SKETCHES["B"] = """
wwwwwww..............mmmmmm
wwwwww................mmmmm
mmmm.....SSSSS.........mmmm
mmmm.....SSSSS.........mmmm
wwwwwww.................mmm
wwwwwww.................mmm
mmmm....................mmm
mmmm....................mmm
MMMMDD................DDMMM
MMMMDDD..............DDDMMM
MMMMDDDD............DDDDMMM
MMMMMDDDD..........DDDDMMMM
MMMMMDDDDDD......DDDDDDMMMM
MMMMDDDDDDDD....DDDDDDDDMMM
MMMMDDDD...DDDDDD...DDDDMMM
MMMMDDD.....DDDD.....DDDMMM
MMMMDD.......DD.......DDMMM
MMMMDD...d...DD...d...DDMMM
MMMMDD.......DD.......DDMMM
MMMMDDD.....DDDD.....DDDMMM
mmmMDDDD...DDDDDD...DDDDMMM
mdmMDDDDDDDDmmmmDDDDDDDDMMM
mmmMDDDDDDDDmmmmDDDDDDDDMMM
MMMMDDDDDDDDDmmDDDDDDDDDMMM
MMMMDDDDDDDDDDDDDDDDDDDDwww
wwwDDDwwDDDDDDDDDDDDwwDDwww
wwwDDDwwDDDDDDDDDDDDwwDDwww
wwwDDDDwwDDDDDDDDDDwwDDDwww
wwMMDDDwwDDDDDDDDDDwwDDDMMM
wwMMDDDDDDDDDDDDDDDDDDDDMMM
MMMMMDDDDDDDDDDDDDDDDDDMMMM
MMMMMMMDDDDDDDDDDDDDDMMMMMM
.....MMMMMDDDMMDDDMMMMMMMMM
.....MMMMMDDDMMDDDMMMMMMMMM
DDDDDDDDDDDDDDDDDDDwwwwwwww
DDDDDDDDDDDDDDDDDDDwwwwwwww
...........................
...........................
"""

SKETCHES["C"] = """
wwwDDDDDDDDDDDDDDDD,,,,,,DD
wwwDDDD.....DDDDDD,,,,,,,,D
DDDDDD......DDDDD,,,,,,,,,,
DDDDD....d..DDDDD,,,,,,,,,,
ddddd.......DDDDD,,,,,,,,,,
dmmm........DDDDD,,,,,,,,,,
dmmm........DDDDD,,,,,,,,,,
ddddd.......DDDDD,,,,,,,,,,
DDDDDD.....DDDDDDD,,,,,,,,D
DDDDDDD....DDDDDDDD,,,,,,DD
D..DDDDD....DDDDDDDDDDDDDDD
D..DDDDDD....DDmmmmDDDDDDDD
DDDDDDDDD....DDmmmmDDDwwwww
DDDDDDDDD....DDDDDDDDDwwwww
mmmmmDDDD....DDDDDDDDDDDDDD
mmmmmDDD....DDDD....DDDDDDD
DDDDDDDD....DDD......DD...D
DDDDDDD.....DDD......DD...D
MMMMM.....................M
MMMMM....................MM
MMMM........SSSSS........MM
MMM.........SSSSS.......MMM
MMM.....................MMM
MMM.....................MMM
MMMww.................wwMMM
MMMwwwwwwwwwwwwwwwwwwwwwMMM
MMMMMwwwwwwwwwwwwwwwwwMMMMM
MMMMMMMMwwMMMMMMMMMMMMMMMMM
MMMMMMMMwwMMMMMMMMMMMMMMMMM
MMMMMMMMMMMMMMMMMMMMMMMMMMM
MMMmmmMMMMMMMMMMMMMMMMMMMMM
MMMmdmMMMMMMMMMMMMMM.....MM
MMMmmmMMMMMMMMMMMMMM.,,,.MM
DDMMMMMMMMDDMMMMMMMM.,d,.MM
DDDDMMMMMMDDMMMMMMMM.,,,.MM
DDDDDDMMMMDDMMMMMMMM.....DD
DDDDDDDMMMDDMMMMMMMMDDDDDDD
DDDDDDDDDDDDMMMMMMDDDDDDDDD
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


def blur(a, sigma):
    """Separable Gaussian blur with edge padding (numpy only)."""
    rad = max(1, int(np.ceil(3 * sigma)))
    k = np.exp(-0.5 * (np.arange(-rad, rad + 1) / sigma) ** 2)
    k /= k.sum()
    p = np.pad(a, rad, mode="edge")
    p = np.stack([np.convolve(row, k, mode="valid") for row in p])[rad:-rad]
    p = np.pad(p, ((rad, rad), (0, 0)), mode="edge")
    return np.stack([np.convolve(col, k, mode="valid") for col in p.T]).T


def sample(a, rows, cols):
    """Bilinear samples of a (sketch grid) at the cell centres of a rows x cols grid."""
    ys = np.clip((np.arange(rows) + 0.5) * a.shape[0] / rows - 0.5, 0, a.shape[0] - 1)
    xs = np.clip((np.arange(cols) + 0.5) * a.shape[1] / cols - 0.5, 0, a.shape[1] - 1)
    y0, x0 = np.floor(ys).astype(int), np.floor(xs).astype(int)
    y1, x1 = np.minimum(y0 + 1, a.shape[0] - 1), np.minimum(x0 + 1, a.shape[1] - 1)
    fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
    return ((1 - fy) * ((1 - fx) * a[y0][:, x0] + fx * a[y0][:, x1])
            + fy * ((1 - fx) * a[y1][:, x0] + fx * a[y1][:, x1]))


def resample(t, locked, rows, cols, sigma=SMOOTH):
    """The sketch at another grid size: blurred one-hot labels, bilinear, argmax (smooth outlines).
    The sketch's own size is returned unchanged."""
    if (rows, cols) == t.shape:
        return t.copy(), locked.copy()
    fields = np.stack([sample(blur((t == k).astype(float), sigma), rows, cols) for k in range(5)])
    lk = sample(blur(locked.astype(float), sigma), rows, cols) > 0.5
    return fields.argmax(0).astype(np.int8), lk


def clean(t, max_rounds=30):
    """Remove caps, 1-wide strips, dots and pinches left by resampling. A cap, strip or dot cell
    takes the most common label among its 4 neighbours; for a pinch, the diagonal cell with the
    fewest same-label neighbours takes the pinched cell's label (the corner contact is cut)."""
    t = t.copy()
    R, C = t.shape
    inside = lambda r, c: 0 <= r < R and 0 <= c < C
    four = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for _ in range(max_rounds):
        am = anomaly_map(CHARS[t])
        bad = list(zip(*np.nonzero(am != "")))
        if not bad:
            break
        for r, c in bad:
            if am[r, c] == "pinch":
                cands = [(r + dr, c + dc) for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))
                         if inside(r + dr, c + dc) and BUDGET_TIER[t[r + dr, c + dc]] != BUDGET_TIER[t[r, c]]]
                same = lambda y, x: sum(inside(y + a, x + b) and t[y + a, x + b] == t[y, x] for a, b in four)
                y, x = min(cands, key=lambda yx: same(*yx))
                t[y, x] = t[r, c]
            else:
                nb = [t[r + dr, c + dc] for dr, dc in four if inside(r + dr, c + dc)]
                vals, cnt = np.unique(nb, return_counts=True)
                t[r, c] = vals[cnt.argmax()]
    return t


def equalize_label(maps, code, grow_into):
    """Make the count of one locked label (S or W) equal in all pictures by trimming the larger
    regions at their edges (cells with the most foreign neighbours first)."""
    target = min(int((m == code).sum()) for m in maps.values())
    for n, t in maps.items():
        while (t == code).sum() > target:
            R, C = t.shape
            best = None
            for r, c in zip(*np.nonzero(t == code)):
                nb = [t[r + dr, c + dc] for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                      if 0 <= r + dr < R and 0 <= c + dc < C]
                foreign = [v for v in nb if v != code]
                if foreign and (best is None or len(foreign) > best[0]):
                    repl = grow_into if grow_into in foreign else foreign[0]
                    best = (len(foreign), r, c, repl)
            _, r, c, repl = best
            t[r, c] = repl
    return target


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


def energy(st, changes, ref_regions):
    e = 0.0
    for s, ref in zip(st, ref_regions):
        e += 40.0 * sum(abs(a - b) for a, b in zip(s.regions, ref))
    E = np.array([s.edges[:NB] for s in st])
    K = np.array([s.corners[:NB] for s in st])
    G = np.array([s.diag[:NB] for s in st])
    N = np.array([s.counts for s in st])
    for arr, tol, w in ((E, 2, 3.0), (K, 2, 3.0), (G, DIAG_TOL, DIAG_W), (N, 1, 4.0)):
        spread = arr.max(0) - arr.min(0)
        e += w * (np.maximum(0, spread - tol) ** 2).sum() + 0.3 * spread.sum()
    J = np.array([s.junction for s in st])
    e += 0.5 * max(0, J.max() - J.min() - 6) ** 2
    e += sum(ANOMALY_W * (s.tips + s.anomalies) + RUN_W * s.run for s in st)
    e += sum(30.0 * (s.edges[NB:].sum() + s.corners[NB:].sum()) for s in st)   # S touches only L (8-nb)
    e += 0.08 * K.sum()                      # mild preference for smooth lines
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


def balance(start, locked, run_limit, iters, seed, T0=6.0):
    """Seeded annealing of the unprotected boundary cells (see module docstring)."""
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
    changes = 0
    cur = energy([st[n] for n in NAMES], changes, ref)
    best = (cur, {n: maps[n].copy() for n in NAMES})
    T1 = 0.05
    for it in range(iters):
        T = T0 * (T1 / T0) ** (it / iters)
        n = NAMES[rng.integers(3)]
        t = maps[n]
        fixed, near_main = prot[n]
        r, c = rng.integers(R), rng.integers(C)
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
        for y, x in cells:
            t[y, x] = new
        s_new = Stats(t, run_limit)
        d_change = sum(int(new != start[n][y, x]) - int(o != start[n][y, x]) for (y, x), o in zip(cells, olds))
        cand = {**st, n: s_new}
        e = energy([cand[k] for k in NAMES], changes + d_change, ref)
        if e <= cur or rng.random() < np.exp((cur - e) / T):
            st[n], cur = s_new, e
            changes += d_change
            if e < best[0]:
                best = (e, {k: maps[k].copy() for k in NAMES})
        else:
            for (y, x), o in zip(cells, olds):
                t[y, x] = o
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


_NATIVE = {}


def run_limit_for(cols):
    """Straight boundary runs above 5 edges per 20 columns are penalized (7 at 27 columns)."""
    return max(5, round(5 * cols / 20))


def make(rows, cols):
    """Returns (start, balanced, run limit) at a grid size. Stage 1 balances the hand sketches at
    their own size (27 x 38). Other sizes resample the stage-1 maps (and the locks), clean the
    anomalies resampling leaves, equalize the S and W counts, and balance again at that size."""
    parsed = {n: parse(SKETCHES[n]) for n in NAMES}
    locked = {n: parsed[n][1] for n in NAMES}
    if not _NATIVE:
        start = {n: parsed[n][0] for n in NAMES}
        _NATIVE["start"] = start
        lim = run_limit_for(SKETCH_COLS)
        first = best_of_seeds(start, locked, SKETCH_ROWS, SKETCH_COLS, lim)
        _NATIVE["maps"] = best_of_seeds(first, locked, SKETCH_ROWS, SKETCH_COLS, lim, T0=POLISH_T0)
    if (rows, cols) == (SKETCH_ROWS, SKETCH_COLS):
        return _NATIVE["start"], _NATIVE["maps"], run_limit_for(SKETCH_COLS)
    start, lk = {}, {}
    for n in NAMES:
        t, lk[n] = resample(_NATIVE["maps"][n], locked[n], rows, cols)
        start[n] = clean(t)
    equalize_label(start, CODE["S"], CODE["L"])
    equalize_label(start, CODE["W"], CODE["M"])
    run_limit = run_limit_for(cols)
    first = best_of_seeds(start, lk, rows, cols, run_limit)
    return start, best_of_seeds(first, lk, rows, cols, run_limit, T0=POLISH_T0), run_limit


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


ANIMAL_FLOOD = {"A": "DL", "B": "", "C": "M"}   # locked tiers that belong to the animal when touching it
BRANCH_ROWS = (34, 35)                           # B: the branch rows of the owl's figure region
LEG_ROWS = slice(32, 34)                         # B: the legs; the sky between them is not the owl


def animal_mask(n, t, locked):
    """The animal only: figure plus enclosed holes (eyes, beak, lines), plus locked cells of the
    listed tiers 4-connected to it (A ear tips, leg line and tail; C beak); B minus the branch."""
    _, a = figure_mask(t, FIGURE[n])
    a = a.copy()
    if n == "B":
        a[list(BRANCH_ROWS)] = False
        a[LEG_ROWS] &= t[LEG_ROWS] == CODE["D"]
    R, C = t.shape
    grow = True
    while grow:
        grow = False
        for r, c in zip(*np.nonzero(locked & ~a)):
            if CHARS[t[r, c]] in ANIMAL_FLOOD[n] and any(
                    0 <= r + dr < R and 0 <= c + dc < C and a[r + dr, c + dc] for dr, dc in SIDE4):
                a[r, c] = grow = True
    return a


def write_outputs(start, maps, out, rows, cols, run_limit):
    out.mkdir(parents=True, exist_ok=True)
    for n in NAMES:
        write_tiers(maps[n], out / f"tiers-{n}.txt")
        if (rows, cols) == (SKETCH_ROWS, SKETCH_COLS):
            a = animal_mask(n, maps[n], parse(SKETCHES[n])[1])
            (out / f"tiers-{n}-animal.txt").write_text(
                "\n".join(" ".join("A" if v else "." for v in row) for row in a) + "\n")
    named = {TITLES[n].split(" (")[0]: budgets(CHARS[maps[n]]) for n in NAMES}
    moved = {n: int((maps[n] != start[n]).sum()) for n in NAMES}
    report = [
        f"# Boundary budgets, experiment 011 (Field, Wood and Water), {cols} columns x {rows} rows.",
        "# Columns: A hare, B owl, C swan. edges = 4-neighbour cell edges between the two tiers;",
        "# corners = cells with the other tier on two adjacent sides (convex) or on a diagonal only",
        "# (concave), both tiers counted. W and S are full tiers (budget_v2.py, as pipeline v2 and",
        "# classes-v9): S-L is a budget pair, S-D, S-M and S-W contacts (8-neighbourhood) must be 0.",
        "# Anomalies need rare tiles (target 0; the dots are designed: one D-on-L and one D-on-M dot per",
        "# picture). Tips = 1-cell protrusions (caps). 45deg-run cells =",
        "# convex corners chained diagonally (staircases of single steps, 2+ cells), per pair.",
        f"# Straight runs are penalized above {run_limit} edges. Cells moved by the balancer from the",
        "# start map (sketch or resampled map): " + ", ".join(f"{n} {moved[n]}" for n in NAMES),
        "",
        table(named),
        extra_rows(maps),
    ]
    (out / "budgets.txt").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    up = 16
    sheet([[tier_image(maps[n], up) for n in NAMES]], out / "targets-preview.png")
    sheet([[contour_image(maps[n], up) for n in NAMES]], out / "contours-preview.png")


def main(argv):
    """Usage: make_targets_v4_draft.py [COLSxROWS ...]   (default: 27x38 only).
    Every size is written to <COLS>x<ROWS>-v4-draft/."""
    sizes = argv or [PRIMARY]
    for size in sizes:
        cols, rows = (int(v) for v in size.lower().split("x"))
        print(f"== {cols}x{rows}", flush=True)
        start, maps, run_limit = make(rows, cols)
        write_outputs(start, maps, HERE / f"{cols}x{rows}{OUT_SUFFIX}", rows, cols, run_limit)


if __name__ == "__main__":
    main(sys.argv[1:])
