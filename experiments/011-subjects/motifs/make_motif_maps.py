"""Motif maps for "Field, Wood and Water" (docs/design/10-motif-vocabulary.md).

Reads the tier maps 27x38-v2/tiers-{A,B,C}.txt, places motif codes on plain cells by region
preference, and writes motif-maps.txt and motif-counts.txt next to this script.

Plain cell: a cell with no lighter tier in its 8-neighbourhood (order D < S < M < W < L, as in
pipeline/run_from_tiers_v4.py: the darker cell carries every transition), so every L cell is plain.
Regular motifs go on plain D, M and L cells. Hero motifs are placed by hand (HEROES); I and G sit on
the D-carried D-L transition pieces, E and Y on the designed dot pieces, O and N on plain cells.

Every (motif, tier) class gets the same count in A, B and C by construction (COUNTS); the script
checks that each class lands inside its intended regions (weight >= 2), reports any spill, and
prints the table.  Run: python3 make_motif_maps.py
"""
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIERS = HERE.parent / "27x38-v2"
ORDER = "DSMWL"
RK = {t: i for i, t in enumerate(ORDER)}
PICS = ["A", "B", "C"]

# Regular classes (motif code, base tier) -> pieces per picture.
COUNTS = {
    ("s", "D"): 22, ("p", "D"): 12, ("k", "D"): 10, ("v", "D"): 14,
    ("s", "M"): 32, ("c", "M"): 40, ("l", "M"): 34, ("d", "M"): 28,
    ("u", "L"): 30, ("v", "L"): 28, ("p", "L"): 26, ("f", "L"): 34,
}
# Assignment order: most region-constrained first.
SEQ = [("k", "D"), ("v", "D"), ("p", "D"), ("s", "D"),
       ("d", "M"), ("l", "M"), ("c", "M"), ("s", "M"),
       ("p", "L"), ("v", "L"), ("u", "L"), ("f", "L")]

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


def build(p, seed=11):
    rng = random.Random(f"{seed}{p}")
    g = load(p)
    R, C = len(g), len(g[0])
    m = [["." for _ in range(C)] for _ in range(R)]
    for code, r, c in HEROES[p]:
        m[r][c] = code
    spill = {}
    for cls in SEQ:
        code, tier = cls
        fns = REG[p][cls]
        cand = []
        for r in range(R):
            for c in range(C):
                if g[r][c] == tier and m[r][c] == "." and plain(g, r, c):
                    w = max(f(r, c) for f in fns)
                    far = all(g[rr][cc] == tier for rr in range(max(0, r - 1), min(R, r + 2))
                              for cc in range(max(0, c - 1), min(C, c + 2)))
                    # inside a region, prefer far cells (no foreign tier around): near cells stay plain
                    # because their transition neighbour already anchors them
                    cand.append((w + (0.6 if far and w >= 2 else 0) + rng.random() * 0.9, w, r, c))
        cand.sort(reverse=True)
        n, got = COUNTS[cls], 0
        for _, w, r, c in cand:
            if got == n:
                break
            if any(0 <= r + dr < R and 0 <= c + dc < C and m[r + dr][c + dc] == code
                   and g[r + dr][c + dc] == tier for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0))):
                continue                                  # no two same-class motifs side by side
            m[r][c] = code
            got += 1
            if w < 2:
                spill[cls] = spill.get(cls, 0) + 1
        assert got == n, (p, cls, got)
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


def main():
    hero_cls = check_heroes()
    maps, out, tab = {}, [], {}
    for p in PICS:
        g, m, spill = build(p)
        maps[p] = (g, m, spill)
    hdr = ["# Motif maps, 27 columns x 38 rows, aligned to 27x38-v2/tiers-{A,B,C}.txt (make_motif_maps.py).",
           "# '.' = no motif. Regular motifs (base tier = the tier map's cell): s star/glint, p pebble cluster,",
           "# k streak, v chevron, c curl, l leaf, d seed head, u cloud puff, f snowflake. Heroes: I amber wedge and",
           "# G catchlight (on D-L transition pieces), O crater, E amber eye (D-on-M dot), Y eye/catchlight",
           "# (D-on-L dot), N beak/nose. See docs/design/10-motif-vocabulary.md."]
    out += hdr
    names = {"A": "hare at dawn", "B": "owl at dusk", "C": "swan at midnight"}
    for p in PICS:
        out.append("")
        out.append(f"# {p} {names[p]}")
        out += [" ".join(row) for row in maps[p][1]]
    (HERE / "motif-maps.txt").write_text("\n".join(out) + "\n")

    # counts
    classes = {}
    plainc = {}
    for p in PICS:
        g, m, _ = maps[p]
        for r, row in enumerate(m):
            for c, code in enumerate(row):
                t = g[r][c]
                if code != ".":
                    key = (code, "hero" if code.isupper() else t)
                    classes.setdefault(key, {q: 0 for q in PICS})[p] += 1
                elif plain(g, r, c):
                    plainc.setdefault(t, {q: 0 for q in PICS})[p] += 1
    lines = ["# Motif class counts per picture (make_motif_maps.py). Class = (motif, base tier); heroes counted",
             "# per code. 'in region' = pieces placed in a cell of weight >= 2 for that class (spill shown).",
             "", f"{'class':<14}{'A hare':>8}{'B owl':>8}{'C swan':>8}{'spread':>8}   spill A/B/C"]
    order = [k for k in SEQ] + [(h, "hero") for h in "IGOEYN"]
    lab = {"s": "star", "p": "pebbles", "k": "streak", "v": "chevron", "c": "curl", "l": "leaf",
           "d": "seedhead", "u": "cloud", "f": "snowflake", "I": "amberwedge", "G": "catchlight",
           "O": "crater", "E": "ambereye", "Y": "dot-eye", "N": "beak/nose"}
    for k in order:
        v = classes[k]
        sp = "/".join(str(maps[p][2].get(k, 0)) for p in PICS) if k[1] != "hero" else "-"
        lines.append(f"{lab[k[0]] + ' ' + k[1]:<14}{v['A']:>8}{v['B']:>8}{v['C']:>8}"
                     f"{max(v.values()) - min(v.values()):>8}   {sp}")
    tot = {p: sum(v[p] for v in classes.values()) for p in PICS}
    lines.append("# hero piece classes (same in A, B, C): " + ", ".join(
        f"{k} on {'/'.join(v)}" for k, v in hero_cls.items()))
    lines.append(f"{'all motifs':<14}{tot['A']:>8}{tot['B']:>8}{tot['C']:>8}")
    lines += ["", "# Plain cells left without a motif (per base tier), and share of all 1026 pieces"]
    for t in "DMLWS":
        v = plainc.get(t, {q: 0 for q in PICS})
        lines.append(f"{'plain ' + t:<14}{v['A']:>8}{v['B']:>8}{v['C']:>8}")
    left = {p: sum(v[p] for v in plainc.values()) for p in PICS}
    far = {p: 0 for p in PICS}
    for p in PICS:
        g, m, _ = maps[p]
        R, C = len(g), len(g[0])
        for r in range(R):
            for c in range(C):
                if m[r][c] == "." and plain(g, r, c) and all(
                        g[rr][cc] == g[r][c] for rr in range(max(0, r - 1), min(R, r + 2))
                        for cc in range(max(0, c - 1), min(C, c + 2))):
                    far[p] += 1
    lines.append(f"{'plain total':<14}{left['A']:>8}{left['B']:>8}{left['C']:>8}")
    lines.append(f"{'% of 1026':<14}" + "".join(f"{100 * left[p] / 1026:>8.1f}" for p in PICS))
    lines.append(f"{'  of which far':<14}{far['A']:>8}{far['B']:>8}{far['C']:>8}"
                 "   (no other tier in the 8-neighbourhood: not anchored by a transition neighbour)")
    lines.append(f"{'far % of 1026':<14}" + "".join(f"{100 * far[p] / 1026:>8.1f}" for p in PICS))
    # largest group of identical plain pieces within one connected same-tier area is not computed here;
    # the per-tier totals above are the upper bound of an interchangeable set.
    lines += ["", "# Remaining plain D/M/L pieces: share with >= 2 distinctive 4-neighbours (motif or transition",
              "# piece; the frame counts as none), and the largest motif-free same-tier patch (4-connected)"]
    for p in PICS:
        g, m, _ = maps[p]
        R, C = len(g), len(g[0])
        free = lambda r, c: m[r][c] == "." and plain(g, r, c) and g[r][c] in "DML"
        cells = [(r, c) for r in range(R) for c in range(C) if free(r, c)]
        anch = sum(1 for r, c in cells if sum(
            1 for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0))
            if 0 <= r + dr < R and 0 <= c + dc < C and not (m[r + dr][c + dc] == "." and plain(g, r + dr, c + dc))) >= 2)
        seen, best = set(), 0
        for start in cells:
            if start in seen:
                continue
            stack, n = [start], 0
            seen.add(start)
            while stack:
                a_, b_ = stack.pop()
                n += 1
                for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                    x, y = a_ + dr, b_ + dc
                    if 0 <= x < R and 0 <= y < C and (x, y) not in seen and free(x, y) and g[x][y] == g[a_][b_]:
                        seen.add((x, y))
                        stack.append((x, y))
            best = max(best, n)
        lines.append(f"{p}: {len(cells)} plain D/M/L, anchored {anch} ({100 * anch / len(cells):.0f}%), largest patch {best}")
    (HERE / "motif-counts.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
