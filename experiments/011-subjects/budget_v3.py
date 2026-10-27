"""Transition-class counts of a tier map (experiment 011, version 3).

The pipeline (pipeline/run_from_tiers_v3.py, stage classify) gives every transition cell a merged
class: the darker tier hosts, the lighter 8-neighbours decide the pattern, and the class name is the
ordered pair of tiers plus a pattern letter: s straight, c corner, p cap (three sides), d dot (four
sides), i a convex corner merged into c with the tiers swapped. A class is one piece type, so the three
pictures need the same count of every class. This module copies the pipeline's classify() and
merged() (class names only: rotations do not change the count) so that make_targets_v3.py can count
the classes the pipeline will see. Frame cells (first and last row and column) are plain and have
no class. The class of a cell depends on its 8 neighbours only.

class_counts(tiers) -> {class: count} over the interior; frame_counts(tiers) -> the frame labels (plain
tier letters and classes, with the outside counted as the own tier) as corner and edge pools;
budgets_v3(tiers) adds the pair edges and corners of budget_v2.

Usage: python3 budget_v3.py tiers-A.txt [tiers-B.txt ...]
"""
import sys
from collections import Counter

import numpy as np

from budget_v2 import budgets as pair_budgets, load

ORDER = "DSMWL"                                       # darker first (the pipeline's ORDER)
RANK = {t: i for i, t in enumerate(ORDER)}
SIDE_OFF = [(0, -1), (1, 0), (0, 1), (-1, 0)]         # T, R, B, L as (dx, dy)
CORNER_OFF = [(-1, -1), (1, -1), (1, 1), (-1, 1)]     # TL, TR, BR, BL
OPPOSITE = (frozenset({0, 2}), frozenset({1, 3}))


def ranks(tiers):
    """Integer array of ORDER ranks from rows of tier letters (list of lists or a char array)."""
    return np.array([[RANK[t] for t in row] for row in tiers], dtype=np.int16)


def _from_neighbours(own, sides, corners):
    """Merged class from the own rank and the 4 side and 4 corner ranks (pipeline classify + merged)."""
    differing = [x for x in sides + corners if x > own]     # only lighter neighbours count
    if not differing:
        return None
    count = Counter(differing)
    n = max(count, key=lambda x: (count[x], x))             # ties go to the lighter tier
    S = frozenset(k for k in range(4) if sides[k] == n)
    Q = [k for k in range(4) if corners[k] == n and k not in S and (k + 3) % 4 not in S]
    t, nbr = ORDER[own], ORDER[n]
    if len(S) == 4:
        return nbr + t + "d"
    if len(S) == 3:
        pattern = "p"
    elif len(S) == 2:
        pattern = "s" if S in OPPOSITE else "c"
    elif len(S) == 1:
        pattern = "s"
    else:
        assert Q, "a lighter neighbour must be a side or a corner"
        pattern = "i"
    if pattern == "s":                                      # straight: darker tier first
        return "".join(sorted((t, nbr), key=ORDER.index)) + "s"
    if pattern == "c":
        return t + nbr + "c"
    if pattern == "i":
        return nbr + t + "c"
    return t + nbr + "p"


def is_frame(R, C, r, c):
    return r in (0, R - 1) or c in (0, C - 1)


def pool_of(R, C, r, c):
    """'corner', 'edge' (other frame cells) or 'int' (interior)."""
    if r in (0, R - 1) and c in (0, C - 1):
        return "corner"
    return "edge" if is_frame(R, C, r, c) else "int"


def cell_class(rk, r, c):
    """Merged class of an interior cell (r, c) of a rank array; None for a plain cell or a frame cell
    (the pipeline's classify: frame cells are plain)."""
    R, C = rk.shape
    if is_frame(R, C, r, c):
        return None
    own = int(rk[r, c])
    sides = [int(rk[r + dy, c + dx]) for dx, dy in SIDE_OFF]
    corners = [int(rk[r + dy, c + dx]) for dx, dy in CORNER_OFF]
    return _from_neighbours(own, sides, corners)


def frame_label(rk, r, c):
    """Label of a frame cell: its class with the outside of the picture counted as its own tier (as
    the pipeline's classify does for the neighbours), or its plain tier letter."""
    R, C = rk.shape
    own = int(rk[r, c])

    def at(dx, dy):
        y, x = r + dy, c + dx
        return int(rk[y, x]) if 0 <= y < R and 0 <= x < C else own
    cls = _from_neighbours(own, [at(dx, dy) for dx, dy in SIDE_OFF], [at(dx, dy) for dx, dy in CORNER_OFF])
    return cls if cls else ORDER[own]


def cell_label(rk, r, c):
    """Interior cell: its merged class or None. Frame cell: frame_label."""
    R, C = rk.shape
    return frame_label(rk, r, c) if is_frame(R, C, r, c) else cell_class(rk, r, c)


def frame_counts(tiers):
    """{'corner': Counter, 'edge': Counter} of the frame labels (corner cells and the other frame cells)."""
    rk = ranks(tiers)
    R, C = rk.shape
    out = {"corner": Counter(), "edge": Counter()}
    for r in range(R):
        for c in range(C):
            pool = pool_of(R, C, r, c)
            if pool != "int":
                out[pool][frame_label(rk, r, c)] += 1
    return out


def frame_table(counts):
    """Text table of the frame histograms: per pool, each label with its count per picture, spread."""
    names = list(counts)
    lines = []
    for pool in ("corner", "edge"):
        labels = sorted({k for n in names for k in counts[n][pool]}, key=lambda k: (len(k), k))
        lines.append(f"frame {pool} cells: " + "  ".join(f"{n} {sum(counts[n][pool].values())}" for n in names))
        lines.append(f"{'label':10s}" + "".join(f"{n:>9s}" for n in names) + f"{'spread':>8s}")
        for k in labels:
            vals = [counts[n][pool].get(k, 0) for n in names]
            lines.append(f"{k:10s}" + "".join(f"{v:9d}" for v in vals) + f"{max(vals) - min(vals):8d}")
    return "\n".join(lines)


def class_map(tiers):
    """Per cell: its merged class or None (plain or frame)."""
    rk = ranks(tiers)
    R, C = rk.shape
    return [[cell_class(rk, r, c) for c in range(C)] for r in range(R)]


def class_counts(tiers):
    """{merged class: number of cells} over the whole map (frame excluded)."""
    rk = ranks(tiers)
    R, C = rk.shape
    counts = Counter()
    for r in range(R):
        for c in range(C):
            k = cell_class(rk, r, c)
            if k:
                counts[k] += 1
    return dict(counts)


def pair_of(cls):
    return "".join(sorted(cls[:2], key=ORDER.index))


def class_key(cls):
    return (ORDER.index(cls[0]), ORDER.index(cls[1]), cls[2:])


def class_surplus(counts):
    """counts: {picture: {class: n}}. Returns (per-class max over pictures, surplus per picture)."""
    classes = sorted({c for d in counts.values() for c in d}, key=class_key)
    top = {c: max(d.get(c, 0) for d in counts.values()) for c in classes}
    sur = {p: {c: top[c] - d.get(c, 0) for c in classes} for p, d in counts.items()}
    return top, sur


def class_table(counts):
    """Text table per class and pair: counts per picture, max, surplus per picture (pipeline layout)."""
    names = list(counts)
    top, sur = class_surplus(counts)
    lines = [f"{'class':7s}{'pair':>5s} " + "".join(f"{n:>9s}" for n in names)
             + f"{'max':>6s}" + "".join(f"{'sur_' + n:>8s}" for n in names)]
    for pair in sorted({pair_of(c) for c in top}, key=lambda p: (ORDER.index(p[0]), ORDER.index(p[1]))):
        block = [c for c in top if pair_of(c) == pair]
        for c in sorted(block, key=class_key):
            lines.append(f"{c:7s}{pair:>5s} " + "".join(f"{counts[n].get(c, 0):9d}" for n in names)
                         + f"{top[c]:6d}" + "".join(f"{sur[n][c]:8d}" for n in names))
        lines.append(f"{'total':7s}{pair:>5s} " + "".join(f"{sum(counts[n].get(c, 0) for c in block):9d}"
                                                       for n in names)
                     + f"{sum(top[c] for c in block):6d}" + "".join(
                         f"{sum(sur[n][c] for c in block):8d}" for n in names))
    tot = {n: sum(sur[n].values()) for n in names}
    lines.append("class surplus (max minus own, summed over classes): "
                 + ", ".join(f"{n} {tot[n]}" for n in names) + f"; total {sum(tot.values())}")
    return "\n".join(lines)


def budgets_v3(tiers):
    """Pair edges and corners (budget_v2) plus the class counts of one tier map."""
    out = pair_budgets(np.asarray(tiers, dtype="<U1"))
    out["classes"] = class_counts(tiers)
    out["frame"] = frame_counts(tiers)
    return out


if __name__ == "__main__":
    named = {p.rsplit("/", 1)[-1].replace(".txt", ""): class_counts(load(p)) for p in sys.argv[1:]}
    print(class_table(named))
