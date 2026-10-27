"""Motif maps v2 for "Field, Wood and Water" (docs/design/10-motif-vocabulary.md; experiment 011, v6).

Copy of make_motif_maps.py with the v6 changes from evaluation-v5.md. The vocabulary, the six heroes (HEROES,
unchanged), the region preferences (REG, unchanged) and the tier-map readers are the v5 ones.

  coverage   regular motif cells are COUNTS, 138 per picture (about 45% of v5), plus 9 hero cells: 147 of
             1026 = 14.3% (limit MAX_COVER = 18%). The counts are the largest that fit in all three pictures
             under the halo and spacing rules (see the capacity note in the report). Counts are identical in
             A, B and C by construction.
  clusters   each (motif, tier) class grows organic clusters (drifts of leaves, constellations of stars, beds
             of flowers): cluster centres come from the class's region, members are drawn from a Gaussian
             kernel round the centre (SPREAD) with a random factor per cell, so spacing is irregular.
  spacing    Poisson-disc-like within each class: two motif cells of one class are at least CHEB_MIN = 2
             apart (Chebyshev, no 8-neighbours of the same code); other classes and heroes may touch. A random
             factor and a penalty for a second member at distance 2 keep the spacing uneven. The lattice test
             in the report compares equally spaced triples with a chance baseline.
  halo       a regular motif is at least HALO = 2 (Chebyshev) from every boundary cell, where BOUNDARY =
             "carrier": the darker cell of every tier boundary (a cell with a lighter 8-neighbour, which
             carries the transition piece). The literal rule (both sides of a boundary, "any") leaves almost
             no room for the sky: 275 of the 280 L cells of picture C lie within one cell of a boundary. The
             report lists the any-side count as well. Heroes keep their v5 cells: G, E and Y sit on
             transition pieces by design, and the report lists the distance of every hero.
  density    the chance of a cell grows with its distance from the nearest tier boundary (0.35 at 2 cells,
             1.0 from 6 cells out): thinner next to a figure, denser in the open field and sky.

Outputs (in HERE; the pipeline sets HERE to its pipeline-out-v6/ folder): motif-maps-v6.txt and
motif-counts-v6.txt. The v5 files motif-maps.txt and motif-counts.txt are not written here.
Run: python3 motifs/make_motif_maps_v2.py
"""
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIERS = HERE.parent / "27x38-v4-draft"   # v4draft variant: reads the v4 draft tiers
ORDER = "DSMWL"
RK = {t: i for i, t in enumerate(ORDER)}
PICS = ["A", "B", "C"]
MAX_COVER = 0.18                 # motif cells per picture, as a fraction of 27 x 38
CHEB_MIN = 2                     # minimum Chebyshev distance between two motif cells
HALO = 1                         # v4draft: 2 in v6. The draft has M 271 cells (v2: 396), so only 47-76 M cells lie at distance >= 2 and the M classes do not fit; 1 places all counts

BOUNDARY = "carrier"             # boundary cells: the darker side of each tier boundary (see boundary_distance)
CLUSTER = 4                      # target members per cluster
SPREAD = {"s": 2.6, "c": 2.0, "u": 2.4, "f": 2.2, "d": 1.8, "v": 1.8, "l": 1.6, "k": 1.5, "p": 1.4}

# Regular classes (motif code, base tier) -> pieces per picture (v5: 22 12 10 14 / 32 40 34 28 / 30 28 26 34).
# D classes are capped by picture C (about 8 cells of D with a halo at all); M and L have room in all three.
COUNTS = {
    ("s", "D"): 4, ("p", "D"): 2, ("k", "D"): 2, ("v", "D"): 2,
    ("s", "M"): 18, ("c", "M"): 18, ("l", "M"): 18, ("d", "M"): 16,
    ("u", "L"): 15, ("v", "L"): 15, ("p", "L"): 14, ("f", "L"): 12,
}
# Assignment order: most region-constrained first (as v5).
SEQ = [("k", "D"), ("v", "D"), ("p", "D"), ("s", "D"),
       ("d", "M"), ("l", "M"), ("c", "M"), ("s", "M"),
       ("p", "L"), ("v", "L"), ("u", "L"), ("f", "L")]

# Hero motifs: (code, row, col) per picture; counts I2 G2 O2 E1 Y1 N1 in each.
# v4draft: hero cells re-anchored to the v4 draft tiers (equalized tiles of the run). Each entry keeps its v2 piece
# class and moves to the nearest cell of that class in its picture (rarest class first, Chebyshev distance >= 2 from
# the other heroes). The v2 cell is in brackets; the comment is the v2 intent.
HEROES = {
    "A": [("I", 11, 0), ("I", 9, 1),       # [v2 11,0 / 11,1] rising sun's rim, low sky above the left horizon (plain L)
          ("G", 8, 21), ("G", 10, 25),      # [v2 6,24 / 6,25] frost sparkle on the hedge-tree crown (D-L convex corners)
          ("O", 3, 11), ("O", 21, 24),     # [v2 3,11 / 25,24] pale daytime moon between the ears; its reflection in a puddle
          ("E", 12, 17),                   # [v2 12,17] hare's amber eye (D-on-M dot)
          ("Y", 1, 11),                    # [v2 5,21] a rook in the dawn sky (D-on-L dot)
          ("N", 14, 20)],                  # [v2 14,20] hare's nose
    "B": [("I", 14, 8), ("I", 12, 15),     # [v2 12,7 / 12,15] owl's amber irises, beside the pupils (plain L)
          ("G", 11, 8), ("G", 12, 17),     # [v2 12,8 / 12,16] owl's catchlights on the pupils (D-L convex corners)
          ("O", 4, 15), ("O", 5, 9),       # [v2 4,15 / 5,9] craters on the moon
          ("E", 21, 1),                    # [v2 15,1] a crow at the sky's edge (D-on-M dot)
          ("Y", 17, 18),                   # [v2 35,24] a blackbird on the snow (D-on-L dot)
          ("N", 21, 12)],                  # [v2 16,12] owl's beak tip
    "C": [("I", 6, 5), ("I", 8, 6),        # [v2 6,5 / 7,5] swan's orange bill tip (plain L)
          ("G", 4, 19), ("G", 2, 24),      # [v2 1,19 / 1,24] two stars hugging the moon's rim (D-L convex corners)
          ("O", 3, 21), ("O", 5, 23),      # [v2 3,21 / 5,23] craters on the moon
          ("E", 31, 4),                    # [v2 32,5] a coot on the lake (D-on-M dot)
          ("Y", 3, 9),                     # [v2 5,11] swan's eye (D-on-L dot)
          ("N", 15, 4)],                   # [v2 16,5] the bill's reflection in the lake
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
    t = own = g[r][c]     # own tier kept: t is rebound to the junction label below (v4draft fix)
    lighter = lambda rr, cc: 0 <= rr < R and 0 <= cc < C and RK[g[rr][cc]] > RK[own]
    sides = [lighter(r - 1, c), lighter(r, c + 1), lighter(r + 1, c), lighter(r, c - 1)]
    n = sum(sides)
    nb = sorted({g[rr][cc] for rr in range(max(0, r - 1), min(R, r + 2))
                 for cc in range(max(0, c - 1), min(C, c + 2)) if RK[g[rr][cc]] > RK[own]})
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


def density(d):
    return 0.35 + 0.65 * min(d, 6) / 6.0


def split(n, k, rng):
    sizes = [n // k + (1 if i < n % k else 0) for i in range(k)]
    rng.shuffle(sizes)
    return sizes


def place_class(p, g, m, dist, cls, n, rng):
    """Place n cells of class cls = (code, tier) in clusters. Returns (cells, spill): spill counts cells whose
    region weight is below 2 (outside the class's region)."""
    code, tier = cls
    R, C = len(g), len(g[0])
    regs = REG[p][cls]
    pool = [(r, c) for r in range(R) for c in range(C) if g[r][c] == tier and dist[r][c] >= HALO]
    raw = {q: region_raw(regs, *q) for q in pool}
    weight = {q: (raw[q] / 3.0) ** 2 + 0.01 for q in pool}          # 1 at weight 3, 0.44 at 2, 0.11 at 1
    base = {q: weight[q] * density(dist[q[0]][q[1]]) for q in pool}
    k = max(1, round(n / CLUSTER))
    sizes = split(n, k, rng)
    centres = []
    for _ in range(k):
        free = [q for q in pool if same_free(m, *q, code)]
        cand = [q for q in free if raw[q] >= 2] or free
        def score(q):
            spread = 1.0
            if centres:
                dmin = min(math.hypot(q[0] - a, q[1] - b) for a, b in centres)
                spread = 0.2 + min(dmin, 8.0) / 8.0
            return base[q] * spread * (0.5 + rng.random())
        centres.append(rng.choices(cand, weights=[score(q) for q in cand])[0])
    placed, spill = [], 0
    for (cy, cx), size in zip(centres, sizes):
        sig = SPREAD[code]
        for _ in range(size):
            cand = [q for q in pool if same_free(m, *q, code)]
            if not cand:
                raise SystemExit(f"{p}: no room for {code} on {tier} (placed {len(placed)} of {n})")
            ws = []
            for r, c in cand:
                kern = math.exp(-((r - cy) ** 2 + (c - cx) ** 2) / (2 * sig * sig))
                near = sum(1 for a, b in placed if max(abs(r - a), abs(c - b)) == 2)
                triple = makes_triple(placed, r, c)                    # no lattice: no equal spacing
                ws.append((base[(r, c)] * kern * 0.5 ** near * (0.5 + rng.random()), triple))
            good = [i for i, (_, t) in enumerate(ws) if not t]
            if good:                                                  # exclude equal spacing where possible
                cand = [cand[i] for i in good]
                ws = [ws[i][0] for i in good]
            else:
                ws = [w for w, _ in ws]
            q = rng.choices(cand, weights=ws)[0]
            m[q[0]][q[1]] = code
            placed.append(q)
            if raw[q] < 2:
                spill += 1
    assert len(placed) == n, (p, cls, len(placed), n)
    return placed, spill


def build(p, seed=11):
    """Motif map of picture p on the tiles load(p): (g, m, spill). m holds the motif code or '.' per cell."""
    rng = random.Random(f"{seed}{p}")
    g = load(p)
    R, C = len(g), len(g[0])
    dist = boundary_distance(g)
    m = [["." for _ in range(C)] for _ in range(R)]
    for code, r, c in HEROES[p]:
        m[r][c] = code
    spill = {}
    for cls in SEQ:
        _, sp = place_class(p, g, m, dist, cls, COUNTS[cls], rng)
        if sp:
            spill[cls] = sp
    return g, m, spill


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


def main():
    hero_cls = check_heroes()
    maps, lines_out, tab = {}, [], {}
    for p in PICS:
        maps[p] = build(p)
    hdr = ["# Motif maps v6, 27 columns x 38 rows, aligned to 27x38-v4-draft/tiers-{A,B,C}.txt (make_motif_maps_v2.py).",
           "# '.' = no motif. Regular motifs (base tier = the tier map's cell): s star/sparkle, p pebble cluster,",
           "# k streak, v chevron, c curl, l leaf, d seed head, u cloud puff, f snowflake. Heroes: I amber wedge and",
           "# G catchlight (on D-L transition pieces), O crater, E amber eye (D-on-M dot), Y eye/catchlight",
           "# (D-on-L dot), N beak/nose. See docs/design/10-motif-vocabulary.md and evaluation-v5.md."]
    lines_out += hdr
    names = {"A": "hare at dawn", "B": "owl at dusk", "C": "swan at midnight"}
    for p in PICS:
        lines_out.append("")
        lines_out.append(f"# {p} {names[p]}")
        lines_out += [" ".join(row) for row in maps[p][1]]
    (HERE / "motif-maps-v6.txt").write_text("\n".join(lines_out) + "\n")

    classes, plainc = {}, {}
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
    rep = ["# Motif class counts per picture, v6 (make_motif_maps_v2.py). Class = (motif, base tier); heroes counted",
           "# per code. spill = cells outside the class region (weight < 2).", "",
           f"{'class':<14}{'A hare':>8}{'B owl':>8}{'C swan':>8}{'spread':>8}   spill A/B/C"]
    order = list(SEQ) + [(h, "hero") for h in "IGOEYN"]
    for k in order:
        v = classes[k]
        sp = "/".join(str(maps[p][2].get(k, 0)) for p in PICS) if k[1] != "hero" else "-"
        rep.append(f"{lab[k[0]] + ' ' + k[1]:<14}{v['A']:>8}{v['B']:>8}{v['C']:>8}"
                   f"{max(v.values()) - min(v.values()):>8}   {sp}")
    tot = {p: sum(v[p] for v in classes.values()) for p in PICS}
    rep.append(f"{'all motifs':<14}{tot['A']:>8}{tot['B']:>8}{tot['C']:>8}")
    rep.append(f"{'coverage %':<14}" + "".join(f"{100 * tot[p] / 1026:>8.1f}" for p in PICS)
               + f"   (limit {100 * MAX_COVER:.0f}%)")
    rep.append("# hero piece classes (same in A, B, C): " + ", ".join(
        f"{k} on {'/'.join(v)}" for k, v in hero_cls.items()))
    if any(tot[p] > MAX_COVER * 1026 for p in PICS):
        raise SystemExit(f"coverage above {MAX_COVER:.0%}: {tot}")

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
        dist_any = boundary_distance(g, "any")
        any_bad = sum(1 for r, c in reg if dist_any[r][c] < HALO)
        rep.append(f"{p}: literal any-side halo: {any_bad} regular motifs within one cell of a boundary cell on "
                   f"either side (the carrier rule allows these)")
        same = sum(1 for r in range(R) for c in range(C) if m[r][c] != "." and not m[r][c].isupper()
                   for rr, cc in neighbours(R, C, r, c) if m[rr][cc] == m[r][c])
        rep.append(f"{p}: regular motifs {len(reg)}, within HALO of a boundary {halo_bad}; "
                   f"same-class pairs at Chebyshev 1: {same}; all motif pairs at Chebyshev 1 (classes may touch): {close}; "
                   f"mean boundary distance motifs {mean_m:.2f} "
                   f"vs open D/M/L cells {sum(free_mean) / max(len(free_mean), 1):.2f}")
        rep.append("   heroes (boundary distance): " + ", ".join(f"{h}{r},{c}:{dist[r][c]}" for r, c, h in hero))
    rep += ["", "# Remaining plain D/M/L cells without a motif, per picture (only cells with no boundary within HALO"
            " can take a motif)"]
    for p in PICS:
        g, m, _ = maps[p]
        dist = boundary_distance(g)
        free = sum(1 for r in range(len(g)) for c in range(len(g[0])) if m[r][c] == "." and dist[r][c] >= HALO)
        rep.append(f"{p}: {free} motif-eligible cells left unused (of {sum(1 for r in range(len(g)) for c in range(len(g[0])) if dist[r][c] >= HALO)} eligible)")
    (HERE / "motif-counts-v6.txt").write_text("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
