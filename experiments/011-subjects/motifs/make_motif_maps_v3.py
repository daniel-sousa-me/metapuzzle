"""Motif maps v3 for "Field, Wood and Water" (docs/design/10-motif-vocabulary.md; experiment 011, v7).

Copy of make_motif_maps_v2.py with the v7 changes from evaluation-v6.md. The vocabulary, the six heroes (HEROES,
unchanged), the region preferences (REG, unchanged), the halo (carrier rule, HALO, unchanged), the spacing rule
(CHEB_MIN, unchanged), the lattice test (unchanged) and the tier-map readers are the v2 ones.

  density    placement follows a gradient by distance from the figure outline. The figure is the largest region of
             its tier plus the holes it encloses (figure_mask); the distance is Chebyshev, on both sides of the
             outline (figure_distance). Chance per plain cell (LADDER): 0 within 1 cell, 5% at 2, 10% at 3 and 4,
             15, 20, 25% at 5, 6, 7, and 30% from 8 on. A cell outside its class's region takes OFF_REGION of it.
  quotas     per picture each class is sampled with that chance (spacing and lattice checked as placed). The common
             count of a class is the mean of the three samples, and each picture is equalized to it (equalize_class):
             surplus cells farthest from the figure are dropped, missing cells are added farthest from the figure.
             Counts are identical in A, B and C by construction.
  band       B's cream top band (L cells in rows 0 to 9): within any 3 x 3 window at most one motif type (band_ok).
  clusters   v2's organic clusters are not used: at this density a class has one to three cells, placed one by one.
  coverage   cap MAX_COVER = 25% (v2: 18%).

Outputs (in HERE; the pipeline sets HERE to its pipeline-out-v7/ folder): motif-maps-v7.txt and
motif-counts-v7.txt. Run: python3 motifs/make_motif_maps_v3.py
"""
import math
import random
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIERS = HERE.parent / "27x38-v2"
ORDER = "DSMWL"
RK = {t: i for i, t in enumerate(ORDER)}
PICS = ["A", "B", "C"]
MAX_COVER = 0.25                 # motif cells per picture, as a fraction of 27 x 38 (v7 cap; v2: 0.18)
CHEB_MIN = 2                     # minimum Chebyshev distance between two motif cells of one class
HALO = 2                         # minimum Chebyshev distance of a regular motif from a tier boundary cell (as v2)
BOUNDARY = "carrier"             # boundary cells: the darker side of each tier boundary (see boundary_distance)
FIG_TIER = {"A": "M", "B": "D", "C": "L"}   # tier of each figure (make_targets.py FIGURE)
LADDER = {3: 0.15, 4: 0.25}     # chance per cell by silhouette distance (v7, coordinator decision)
FAR = 0.30                       # chance from silhouette distance 5 on; 0 within 2 cells
OFF_REGION = 0.25                # factor on the chance for a cell outside the class's region (weight < 2)
BAND = {"B": (0, 9)}             # v7: cream top band of B (L cells in these rows): one motif type per 3 x 3 window

# Regular classes (motif code, base tier), in assignment order (as v2). Counts are no longer fixed: see build_all.
SEQ = [("k", "D"), ("v", "D"), ("p", "D"), ("s", "D"),
       ("d", "M"), ("l", "M"), ("c", "M"), ("s", "M"),
       ("p", "L"), ("v", "L"), ("u", "L"), ("f", "L")]
PER_TIER = {t: sum(1 for _, u in SEQ if u == t) for t in "DML"}   # classes per base tier: a cell's chance is shared

# Hero motifs: (code, row, col) per picture; counts I2 G2 O2 E1 Y1 N1 in each.
HEROES = {
    "A": [("I", 11, 0), ("I", 11, 1),      # rising sun's rim, low sky above the left horizon (plain L)
          ("G", 6, 24), ("G", 6, 25),      # frost sparkle on the hedge-tree crown (D-L convex corners)
          ("O", 3, 11), ("O", 25, 24),     # pale daytime moon between the ears; its reflection in a puddle
          ("E", 12, 17),                   # hare's amber eye (D-on-M dot)
          ("Y", 5, 21),                    # a rook in the dawn sky (D-on-L dot)
          ("N", 14, 20)],                  # hare's nose
    "B": [("I", 12, 7), ("I", 12, 15),     # owl's amber irises, beside the pupils (plain L)
          ("G", 12, 8), ("G", 12, 16),     # owl's catchlights on the pupils (D-L convex corners)
          ("O", 4, 15), ("O", 5, 9),       # craters on the moon
          ("E", 15, 1),                    # a crow at the sky's edge (D-on-M dot)
          ("Y", 35, 24),                   # a blackbird on the snow (D-on-L dot)
          ("N", 16, 12)],                  # owl's beak tip
    "C": [("I", 6, 5), ("I", 7, 5),        # swan's orange bill tip (plain L)
          ("G", 1, 19), ("G", 1, 24),      # two stars hugging the moon's rim (D-L convex corners)
          ("O", 3, 21), ("O", 5, 23),      # craters on the moon
          ("E", 32, 5),                    # a coot on the lake (D-on-M dot)
          ("Y", 5, 11),                    # swan's eye (D-on-L dot)
          ("N", 16, 5)],                   # the bill's reflection in the lake
}


def box(r0, r1, c0, c1, w):
    return lambda r, c: w if (r0 <= r <= r1 and c0 <= c <= c1) else 0

# Region preferences: list of weight functions per (picture, class); a cell's weight is the max.
REG = {
  "A": {
    ("v", "L"): [box(0, 10, 8, 18, 3), box(0, 3, 19, 26, 2)],                # gulls, high sky over the ears
    ("p", "L"): [box(0, 12, 0, 7, 3), box(0, 4, 8, 13, 2)],                  # flock stragglers by the starlings
    ("u", "L"): [box(0, 10, 19, 26, 3), box(0, 3, 13, 18, 2)],               # cloudlets by the cloud bank
    ("f", "L"): [box(11, 20, 0, 26, 3), box(21, 37, 0, 26, 3)],              # snow flurries over the field, frost on puddles
    ("s", "D"): [box(12, 26, 0, 10, 3), box(5, 18, 20, 26, 3), box(27, 31, 0, 3, 2)],  # frost glints: horizon edge, hedge-tree
    ("k", "D"): [box(19, 33, 0, 9, 3)],                                      # furrow ridges, left field
    ("p", "D"): [box(30, 37, 0, 26, 3)],                                     # pebbles, foreground
    ("v", "D"): [box(12, 35, 19, 26, 3)],                                    # seedlings / rook tracks, right strip
    ("s", "M"): [box(2, 19, 0, 26, 3)],                                      # dew on ears and head
    ("l", "M"): [box(18, 28, 8, 20, 3)],                                     # tawny flames: back and shoulder
    ("c", "M"): [box(22, 35, 1, 11, 3)],                                     # fur whorls: haunch
    ("d", "M"): [box(27, 35, 9, 20, 3)],                                     # burrs: belly and legs
  },
  "B": {
    ("s", "M"): [lambda r, c: 3.5 - r / 6 if r <= 8 else 0, box(9, 14, 0, 26, 2)],   # evening stars, top
    ("l", "M"): [box(6, 23, 0, 7, 3), box(6, 23, 19, 26, 3)],                # leaves falling beside the owl
    ("c", "M"): [box(17, 28, 0, 8, 3), box(17, 28, 18, 26, 3)],              # wind curls, low sides
    ("d", "M"): [box(26, 31, 0, 26, 3)],                                     # thistledown over the snow line
    ("s", "D"): [box(6, 11, 0, 26, 3), box(14, 19, 4, 9, 3), box(14, 19, 17, 22, 3),
                 box(26, 28, 0, 26, 3), box(9, 15, 9, 17, 2)],           # crown, brow and shoulder spots; frost on the branch
    ("k", "D"): [box(14, 21, 8, 18, 3)],                                     # breast streaks
    ("v", "D"): [box(20, 25, 7, 19, 3)],                                     # belly barring
    ("p", "D"): [box(17, 27, 4, 9, 3), box(17, 27, 17, 22, 3)],              # wing speckles
    ("u", "L"): [box(2, 9, 0, 26, 3)],                                       # maria on the moon
    ("f", "L"): [box(8, 15, 0, 26, 3), box(30, 37, 0, 26, 2)],               # snow falling through moonlight
    ("v", "L"): [box(31, 37, 0, 13, 3)],                                     # bird tracks in the snow
    ("p", "L"): [box(31, 37, 13, 26, 3)],                                    # hare tracks in the snow
  },
  "C": {
    ("s", "D"): [lambda r, c: 3.5 - r / 8 if r <= 13 else 0],                # stars, dense at the top
    ("p", "D"): [box(0, 8, 0, 12, 3), box(34, 37, 0, 26, 3)],                # star clusters; shore pebbles
    ("k", "D"): [box(6, 13, 0, 17, 3)],                                      # meteors
    ("v", "D"): [box(6, 14, 14, 26, 3), box(0, 5, 14, 26, 2)],               # geese skein around the moon
    ("s", "M"): [box(26, 37, 14, 26, 3), box(15, 27, 21, 26, 2), box(29, 37, 10, 13, 2)],  # the moon path on the water
    ("c", "M"): [box(1, 3, 0, 7, 3), box(14, 28, 0, 7, 3), box(14, 18, 15, 26, 3)],  # cloud curls; eddies by the swan
    ("l", "M"): [box(29, 37, 0, 12, 3)],                                     # floating leaves, near shore
    ("d", "M"): [box(28, 37, 6, 18, 3), box(19, 28, 0, 5, 3)],               # thistledown on the water
    ("u", "L"): [box(1, 7, 17, 26, 3), box(23, 27, 5, 24, 3)],               # moon maria; shadow under the wing
    ("v", "L"): [box(17, 26, 0, 12, 3), box(17, 25, 20, 26, 2)],             # feather scallops on the wing
    ("p", "L"): [box(3, 16, 3, 18, 3)],                                      # droplets on head and neck
    ("f", "L"): [box(16, 23, 13, 26, 3), box(29, 37, 0, 26, 3)],             # snow on the swan's back; on ice floes
  },
}

def load(p):
    return [l.split() for l in open(TIERS / f"tiers-{p}.txt") if l.strip()]

def plain(g, r, c):
    R, C = len(g), len(g[0])
    return all(RK[g[rr][cc]] <= RK[g[r][c]]
               for rr in range(max(0, r - 1), min(R, r + 2)) for cc in range(max(0, c - 1), min(C, c + 2)))

def piece_class(g, r, c):
    """Tier, lighter neighbour tier(s) and transition pattern of a cell: s (one lighter side), c (two
    adjacent lighter sides), i (lighter diagonal only), d (dot: all four sides lighter), x (other);
    a bare tier letter is a plain cell."""
    R, C = len(g), len(g[0])
    t = g[r][c]
    lighter = lambda rr, cc: 0 <= rr < R and 0 <= cc < C and RK[g[rr][cc]] > RK[t]
    sides = [lighter(r - 1, c), lighter(r, c + 1), lighter(r + 1, c), lighter(r, c - 1)]
    n = sum(sides)
    nb = sorted({g[rr][cc] for rr in range(max(0, r - 1), min(R, r + 2))
                 for cc in range(max(0, c - 1), min(C, c + 2)) if RK[g[rr][cc]] > RK[t]})
    t = t + "".join(nb)
    if n == 0:
        diag = any(lighter(r + a, c + b) for a in (-1, 1) for b in (-1, 1))
        return t + ("i" if diag else "")
    if n == 1:
        return t + "s"
    if n == 2 and not (sides[0] and sides[2]) and not (sides[1] and sides[3]):
        return t + "c"
    return t + ("d" if n == 4 else "x")



def neighbours(R, C, r, c):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if (dr or dc) and 0 <= r + dr < R and 0 <= c + dc < C:
                yield r + dr, c + dc


def boundary_distance(g, mode=BOUNDARY):
    """Chebyshev distance of every cell to the nearest tier boundary cell (distance 0). mode "carrier": a cell
    with a lighter 8-neighbour (the darker side of every tier boundary, which carries the transition piece).
    mode "any": a cell with any 8-neighbour of another tier (both sides). The board edge is not a boundary."""
    R, C = len(g), len(g[0])
    dist = [[None] * C for _ in range(R)]
    frontier = []
    for r in range(R):
        for c in range(C):
            if mode == "carrier":
                hit = any(RK[g[rr][cc]] > RK[g[r][c]] for rr, cc in neighbours(R, C, r, c))
            else:
                hit = any(g[rr][cc] != g[r][c] for rr, cc in neighbours(R, C, r, c))
            if hit:
                dist[r][c] = 0
                frontier.append((r, c))
    d = 0
    while frontier:
        d += 1
        nxt = []
        for r, c in frontier:
            for rr, cc in neighbours(R, C, r, c):
                if dist[rr][cc] is None:
                    dist[rr][cc] = d
                    nxt.append((rr, cc))
        frontier = nxt
    return dist


def spaced(m, r, c, mind=CHEB_MIN):
    """True when no motif cell lies within Chebyshev distance mind - 1 of (r, c)."""
    R, C = len(m), len(m[0])
    return all(m[rr][cc] == "." for rr in range(max(0, r - mind + 1), min(R, r + mind))
               for cc in range(max(0, c - mind + 1), min(C, c + mind)))


def same_free(m, r, c, code):
    """True when (r, c) is free and no cell within Chebyshev distance 1 holds the same motif code: each class
    keeps a minimum distance of CHEB_MIN = 2 from itself (Poisson-disc-like), other classes may touch."""
    R, C = len(m), len(m[0])
    return m[r][c] == "." and all(m[rr][cc] != code for rr in range(max(0, r - 1), min(R, r + 2))
                                  for cc in range(max(0, c - 1), min(C, c + 2)))


def makes_triple(cells, r, c):
    """True when adding (r, c) to the class cells makes an equally spaced triple in its row or column."""
    for axis in (0, 1):
        fixed = (r, c)
        line = {q[axis] for q in cells if q[1 - axis] == fixed[1 - axis]}
        x = fixed[axis]
        for a in line:
            if 2 * a - x in line or (x + a) % 2 == 0 and (x + a) // 2 in line:
                return True
    return False


def region_raw(regs, r, c):
    return max(f(r, c) for f in regs)


def density(fd):
    """Chance of a regular motif on a plain cell at silhouette distance fd (LADDER); 0 within 2 cells."""
    if fd is None or fd < 3:
        return 0.0
    return FAR if fd >= 5 else LADDER[fd]


def figure_mask(g, tier):
    """The figure: the largest 4-connected region of its tier plus the holes it encloses (eyes, beak)."""
    R, C = len(g), len(g[0])

    def components(pred):
        lab = [[-1] * C for _ in range(R)]
        sizes = []
        for r in range(R):
            for c in range(C):
                if lab[r][c] < 0 and pred(r, c):
                    k = len(sizes)
                    sizes.append(0)
                    lab[r][c] = k
                    q = deque([(r, c)])
                    while q:
                        y, x = q.popleft()
                        sizes[k] += 1
                        for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                            if 0 <= yy < R and 0 <= xx < C and lab[yy][xx] < 0 and pred(yy, xx):
                                lab[yy][xx] = k
                                q.append((yy, xx))
        return lab, sizes

    lab, sizes = components(lambda r, c: g[r][c] == tier)
    big = max(range(len(sizes)), key=lambda k: sizes[k])
    main = [[lab[r][c] == big for c in range(C)] for r in range(R)]
    out, _ = components(lambda r, c: not main[r][c])
    border = {out[r][c] for r in range(R) for c in range(C) if (r in (0, R - 1) or c in (0, C - 1)) and out[r][c] >= 0}
    return [[main[r][c] or (out[r][c] >= 0 and out[r][c] not in border) for c in range(C)] for r in range(R)]


def figure_distance(g, fm):
    """Chebyshev distance of every cell to the figure outline (cells with a neighbour on the other side), both sides."""
    R, C = len(g), len(g[0])
    dist = [[None] * C for _ in range(R)]
    q = deque()
    for r in range(R):
        for c in range(C):
            if any(fm[rr][cc] != fm[r][c] for rr, cc in neighbours(R, C, r, c)):
                dist[r][c] = 0
                q.append((r, c))
    while q:
        r, c = q.popleft()
        for rr, cc in neighbours(R, C, r, c):
            if dist[rr][cc] is None:
                dist[rr][cc] = dist[r][c] + 1
                q.append((rr, cc))
    return dist


def in_band(p, r, tier):
    return p in BAND and BAND[p][0] <= r <= BAND[p][1] and tier == "L"


def band_ok(p, g, m, r, c, code):
    """v7: inside the band, no other motif type within Chebyshev 2 (so every 3 x 3 window holds one type at most)."""
    if not in_band(p, r, g[r][c]):
        return True
    R, C = len(m), len(m[0])
    return not any(m[rr][cc] not in (".", code) and in_band(p, rr, g[rr][cc])
                   for rr in range(max(0, r - 2), min(R, r + 3)) for cc in range(max(0, c - 2), min(C, c + 3)))


def free_cell(p, S, r, c, code):
    return same_free(S["m"], r, c, code) and band_ok(p, S["g"], S["m"], r, c, code)


def candidates(p, S, cls):
    """Plain cells of the class's tier outside the halo with a non-zero chance, free for this class."""
    code, tier = cls
    g, dist, fd = S["g"], S["dist"], S["fd"]
    R, C = len(g), len(g[0])
    return [(r, c) for r in range(R) for c in range(C)
            if g[r][c] == tier and dist[r][c] >= HALO and density(fd[r][c]) > 0 and free_cell(p, S, r, c, code)]


def sample_class(p, S, cls):
    """Per-picture quota by sampling: each candidate is taken with its figure-distance chance (times OFF_REGION
    outside the class's region), in random order; spacing and the lattice test are checked as each cell is placed."""
    code, tier = cls
    regs = REG[p][cls]
    cells = S["placed"].setdefault(cls, [])
    cand = candidates(p, S, cls)
    S["rng"].shuffle(cand)
    for r, c in cand:
        if not free_cell(p, S, r, c, code) or makes_triple(cells, r, c):
            continue
        in_region = region_raw(regs, r, c) >= 2
        chance = density(S["fd"][r][c]) * (1.0 if in_region else OFF_REGION) / PER_TIER[tier]
        if S["rng"].random() < chance:
            S["m"][r][c] = code
            cells.append((r, c))


def equalize_class(p, S, cls, target):
    """Equalize one class in one picture to the common count: drop the placed cells farthest from the figure, or add
    the free candidates farthest from it (cells in the class's region and off the lattice first)."""
    code, tier = cls
    cells = S["placed"].setdefault(cls, [])
    rng, fd, m = S["rng"], S["fd"], S["m"]
    if len(cells) > target:
        for q in sorted(cells, key=lambda q: (-fd[q[0]][q[1]], rng.random()))[:len(cells) - target]:
            m[q[0]][q[1]] = "."
            cells.remove(q)
    regs = REG[p][cls]
    while len(cells) < target:
        cand = candidates(p, S, cls)
        if not cand:
            raise SystemExit(f"{p}: no room for {code} on {tier} (placed {len(cells)} of {target})")
        q = min(cand, key=lambda q: (makes_triple(cells, *q), region_raw(regs, *q) < 2,
                                     -fd[q[0]][q[1]], rng.random()))
        m[q[0]][q[1]] = code
        cells.append(q)


def build_all(seed=11):
    """Motif maps of the three pictures: {picture: (g, m, spill)}; m holds the motif code or '.' per cell. Each class
    is sampled in every picture, its common count is the mean of the three samples, and each picture is equalized
    to it. spill counts cells whose region weight is below 2."""
    S = {}
    for p in PICS:
        g = load(p)
        R, C = len(g), len(g[0])
        fm = figure_mask(g, FIG_TIER[p])                      # v7: this picture's own figure (make_targets FIGURE)
        m = [["." for _ in range(C)] for _ in range(R)]
        for code, r, c in HEROES[p]:
            m[r][c] = code
        S[p] = {"g": g, "m": m, "dist": boundary_distance(g), "fd": figure_distance(g, fm),
                "placed": {}, "rng": random.Random(f"{seed}{p}"), "spill": {}}
    for cls in SEQ:
        for p in PICS:
            sample_class(p, S[p], cls)
        target = round(sum(len(S[p]["placed"].get(cls, [])) for p in PICS) / len(PICS))
        for p in PICS:
            equalize_class(p, S[p], cls, target)
            regs = REG[p][cls]
            spill = sum(1 for q in S[p]["placed"][cls] if region_raw(regs, *q) < 2)
            if spill:
                S[p]["spill"][cls] = spill
    return {p: (S[p]["g"], S[p]["m"], S[p]["spill"]) for p in PICS}


def build(p, seed=11):
    """Motif map of picture p on the tiles load(p): (g, m, spill)."""
    return build_all(seed)[p]


def check_heroes():
    """Each hero code must sit on the same piece class (tier + transition pattern) in A, B and C."""
    sig = {}
    for p in PICS:
        g = load(p)
        for code, r, c in HEROES[p]:
            sig.setdefault(code, {}).setdefault(p, []).append(piece_class(g, r, c))
    for code, per in sig.items():
        vals = {tuple(sorted(v)) for v in per.values()}
        assert len(vals) == 1, (code, per)
    return {code: sorted(per["A"]) for code, per in sig.items()}


def equal_triples(cells):
    """Triples of one class in one row or one column at equal spacing: (a, a+d, a+2d)."""
    count = 0
    for axis in (0, 1):
        lines = {}
        for cell in cells:
            lines.setdefault(cell[1 - axis], set()).add(cell[axis])
        for vals in lines.values():
            v = sorted(vals)
            for i in range(len(v)):
                for j in range(i + 1, len(v)):
                    if 2 * v[j] - v[i] in vals:
                        count += 1
    return count


def chance_cells(g, dist, tier, n, rng, code="x"):
    """Chance baseline for the lattice test: n cells drawn one at a time, uniformly among the tier's cells
    at distance >= HALO, with the same spacing rule and no clustering."""
    R, C = len(g), len(g[0])
    m = [["." for _ in range(C)] for _ in range(R)]
    pool = [(r, c) for r in range(R) for c in range(C) if g[r][c] == tier and dist[r][c] >= HALO]
    out = []
    for _ in range(n):
        cand = [q for q in pool if same_free(m, *q, code)]
        q = rng.choice(cand)
        m[q[0]][q[1]] = code
        out.append(q)
    return out


def motif_distance(m):
    """Chebyshev distance of every cell to the nearest motif cell (heroes included); None when there is none."""
    R, C = len(m), len(m[0])
    dist = [[None] * C for _ in range(R)]
    q = deque()
    for r in range(R):
        for c in range(C):
            if m[r][c] != ".":
                dist[r][c] = 0
                q.append((r, c))
    while q:
        r, c = q.popleft()
        for rr, cc in neighbours(R, C, r, c):
            if dist[rr][cc] is None:
                dist[rr][cc] = dist[r][c] + 1
                q.append((rr, cc))
    return dist


def pool_histogram(g, fm, halo=HALO):
    """Plain cells (DML, not a transition carrier) by figure distance 1, 2, 3, 4, 5+, before any sampling; and the
    eligible ones (carrier distance >= halo)."""
    dist = boundary_distance(g)
    fd = figure_distance(g, fm)
    R, C = len(g), len(g[0])
    def bucket(d):
        return min(d, 5)
    plain = [0] * 6
    elig = [0] * 6
    for r in range(R):
        for c in range(C):
            if g[r][c] in "DML" and dist[r][c] >= 1 and fd[r][c] is not None and fd[r][c] >= 1:
                plain[bucket(fd[r][c])] += 1
                if dist[r][c] >= halo:
                    elig[bucket(fd[r][c])] += 1
    return plain, elig


def main():
    hero_cls = check_heroes()
    maps = build_all()
    lines_out, tab = [], {}
    hdr = ["# Motif maps v7, 27 columns x 38 rows, aligned to 27x38-v2/tiers-{A,B,C}.txt (make_motif_maps_v3.py).",
           "# '.' = no motif. Regular motifs (base tier = the tier map's cell): s star/sparkle, p pebble cluster,",
           "# k streak, v chevron, c curl, l leaf, d seed head, u cloud puff, f snowflake. Heroes: I amber wedge and",
           "# G catchlight (on D-L transition pieces), O crater, E amber eye (D-on-M dot), Y eye/catchlight",
           "# (D-on-L dot), N beak/nose. See docs/design/10-motif-vocabulary.md and evaluation-v6.md."]
    lines_out += hdr
    names = {"A": "hare at dawn", "B": "owl at dusk", "C": "swan at midnight"}
    for p in PICS:
        lines_out.append("")
        lines_out.append(f"# {p} {names[p]}")
        lines_out += [" ".join(row) for row in maps[p][1]]
    (HERE / "motif-maps-v7.txt").write_text("\n".join(lines_out) + "\n")

    classes = {}
    for p in PICS:
        g, m, _ = maps[p]
        for r, row in enumerate(m):
            for c, code in enumerate(row):
                t = g[r][c]
                if code != ".":
                    key = (code, "hero" if code.isupper() else t)
                    classes.setdefault(key, {q: 0 for q in PICS})[p] += 1
    lab = {"s": "star", "p": "pebbles", "k": "streak", "v": "chevron", "c": "curl", "l": "leaf",
           "d": "seedhead", "u": "cloud", "f": "snowflake", "I": "amberwedge", "G": "catchlight",
           "O": "crater", "E": "ambereye", "Y": "dot-eye", "N": "beak/nose"}
    rep = ["# Motif class counts per picture, v7 (make_motif_maps_v3.py). Class = (motif, base tier); heroes counted",
           "# per code. spill = cells outside the class region (weight < 2).", "",
           f"{'class':<14}{'A hare':>8}{'B owl':>8}{'C swan':>8}{'spread':>8}   spill A/B/C"]
    order = list(SEQ) + [(h, "hero") for h in "IGOEYN"]
    for k in order:
        v = classes.get(k, {q: 0 for q in PICS})
        sp = "/".join(str(maps[p][2].get(k, 0)) for p in PICS) if k[1] != "hero" else "-"
        rep.append(f"{lab[k[0]] + ' ' + k[1]:<14}{v['A']:>8}{v['B']:>8}{v['C']:>8}"
                   f"{max(v.values()) - min(v.values()):>8}   {sp}")
    tot = {p: sum(v[p] for v in classes.values()) for p in PICS}
    cells = 27 * 38
    rep.append(f"{'all motifs':<14}{tot['A']:>8}{tot['B']:>8}{tot['C']:>8}")
    rep.append(f"{'coverage %':<14}" + "".join(f"{100 * tot[p] / cells:>8.1f}" for p in PICS)
               + f"   (cap {100 * MAX_COVER:.0f}%)")
    rep.append("# hero piece classes (same in A, B, C): " + ", ".join(
        f"{k} on {'/'.join(v)}" for k, v in hero_cls.items()))
    if any(tot[p] > MAX_COVER * cells for p in PICS):
        raise SystemExit(f"coverage above {MAX_COVER:.0%}: {tot}")

    rep += ["", "# Density gradient by figure distance: regular motifs per eligible plain cell (DML, carrier distance >= HALO)",
            "# in each band of figure distance, with the nominal chance of the band"]
    bands = [(2, 2, "5%"), (3, 4, "10%"), (5, 7, "15-25%"), (8, 999, "30%")]
    for p in PICS:
        g, m, _ = maps[p]
        R, C = len(g), len(g[0])
        dist = boundary_distance(g)
        fd = figure_distance(g, figure_mask(g, FIG_TIER[p]))
        parts = []
        for lo, hi, nom in bands:
            elig = [(r, c) for r in range(R) for c in range(C)
                    if g[r][c] in "DML" and dist[r][c] >= HALO and lo <= fd[r][c] <= hi]
            reg = sum(1 for r, c in elig if m[r][c] != "." and not m[r][c].isupper())
            parts.append(f"fig {lo}{'+' if hi == 999 else ('-' + str(hi) if hi != lo else '')}: "
                         f"{reg}/{len(elig)} ({100 * reg / max(len(elig), 1):.0f}%, nominal {nom})")
        rep.append(f"{p}: " + "; ".join(parts))
    rep += ["", "# Plain cells: DML cells with no motif and not a transition carrier; how many lie more than 3 cells from",
            "# any motif (heroes included)"]
    for p in PICS:
        g, m, _ = maps[p]
        R, C = len(g), len(g[0])
        dist = boundary_distance(g)
        md = motif_distance(m)
        plain = [(r, c) for r in range(R) for c in range(C) if m[r][c] == "." and g[r][c] in "DML" and dist[r][c] >= 1]
        far = sum(1 for r, c in plain if md[r][c] is None or md[r][c] > 3)
        rep.append(f"{p}: plain cells {len(plain)}, more than 3 cells from any motif {far}")

    rep += ["", "# Lattice test: equally spaced triples of one class in a row or column (regular motifs, all classes)",
            "# chance = mean over 300 draws of the same counts placed uniformly under the same spacing rule"]
    rnd = random.Random("lattice")
    for p in PICS:
        g, m, _ = maps[p]
        dist = boundary_distance(g)
        cells = {}
        for r, row in enumerate(m):
            for c, code in enumerate(row):
                if code != "." and not code.isupper():
                    cells.setdefault((code, g[r][c]), []).append((r, c))
        actual = {k: equal_triples(v) for k, v in cells.items()}
        draws = []
        for _ in range(300):
            tot_d = 0
            for (code, tier), v in cells.items():
                tot_d += equal_triples(chance_cells(g, dist, tier, len(v), rnd))
            draws.append(tot_d)
        mean = sum(draws) / len(draws)
        below = sum(1 for d in draws if d <= sum(actual.values())) / len(draws)
        rep.append(f"{p}: actual {sum(actual.values())} triples, chance mean {mean:.1f} "
                   f"(share of draws at or below actual {below:.2f}); ratio {sum(actual.values()) / max(mean, 1e-9):.2f}")

    rep += ["", "# Band (B cream top band, one motif type per 3 x 3 window): pairs of different types within Chebyshev 2"]
    for p in PICS:
        g, m, _ = maps[p]
        R, C = len(g), len(g[0])
        bad = 0
        for r in range(R):
            for c in range(C):
                if m[r][c] == "." or not in_band(p, r, g[r][c]):
                    continue
                for rr in range(max(0, r - 2), min(R, r + 3)):
                    for cc in range(max(0, c - 2), min(C, c + 3)):
                        if (rr, cc) > (r, c) and m[rr][cc] not in (".", m[r][c]) and in_band(p, rr, g[rr][cc]):
                            bad += 1
        rep.append(f"{p}: {bad} pairs" + ("" if p in BAND else " (no band in this picture)"))

    rep += ["", "# Halo and spacing (all pictures): regular motif cells closer than HALO to a tier boundary cell,",
            "# pairs of motif cells closer than CHEB_MIN, and the mean boundary distance of motifs vs plain cells"]
    for p in PICS:
        g, m, _ = maps[p]
        dist = boundary_distance(g)
        R, C = len(g), len(g[0])
        reg = [(r, c) for r in range(R) for c in range(C) if m[r][c] != "." and not m[r][c].isupper()]
        hero = [(r, c, m[r][c]) for r in range(R) for c in range(C) if m[r][c].isupper()]
        halo_bad = sum(1 for r, c in reg if dist[r][c] < HALO)
        close = sum(1 for r in range(R) for c in range(C) if m[r][c] != "."
                    for rr, cc in neighbours(R, C, r, c) if m[rr][cc] != "." and (rr, cc) > (r, c))
        free_mean = [dist[r][c] for r in range(R) for c in range(C) if m[r][c] == "." and g[r][c] in "DML"]
        mean_m = sum(dist[r][c] for r, c in reg) / max(len(reg), 1)
        same = sum(1 for r in range(R) for c in range(C) if m[r][c] != "." and not m[r][c].isupper()
                   for rr, cc in neighbours(R, C, r, c) if m[rr][cc] == m[r][c])
        rep.append(f"{p}: regular motifs {len(reg)}, within HALO of a boundary {halo_bad}; "
                   f"same-class pairs at Chebyshev 1: {same}; all motif pairs at Chebyshev 1 (classes may touch): {close}; "
                   f"mean boundary distance motifs {mean_m:.2f} "
                   f"vs open D/M/L cells {sum(free_mean) / max(len(free_mean), 1):.2f}")
        rep.append("   heroes (boundary distance): " + ", ".join(f"{h}{r},{c}:{dist[r][c]}" for r, c, h in hero))
    (HERE / "motif-counts-v7.txt").write_text("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
