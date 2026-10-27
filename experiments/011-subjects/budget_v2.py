"""Boundary budgets of a tier map with W and S as full tiers (experiment 011, version 2).

Extends budget.py (kept unchanged for version 1), following the pipeline's run_from_tiers_v2.py and
classes-v9: the tiers are D, M, W, L and S, every contact between two different tiers is a
transition, and the budget pairs are D-M, D-W, D-L, M-W, M-L, W-L and S-L (S chips have ragged
transitions against L). S must touch L only: S-D, S-M and S-W contacts (8-neighbourhood) must be 0.

Per pair X-Y:
  edges    4-neighbour cell edges between an X cell and a Y cell.
  corners  cells (of either tier) with the other tier on exactly two adjacent sides (convex),
           plus cells with the other tier on a diagonal only (concave).
  45deg    convex corners of one orientation chained diagonally (2+ cells): future diagonal tiles.
Anomalies (need rare tiles; see anomaly_map, against any other tier):
  cap      other tiers on three sides (a 1-cell tip);  strip  on two opposite sides (1 wide);
  dot      on all four sides;  pinch  on two opposite diagonals and no side.
Junction cells touch (by side or diagonal) two or more other tiers. run = longest boundary segment
along one grid line, in edges.

Usage: python3 budget_v2.py tiers-A.txt [tiers-B.txt ...]
"""
import sys

import numpy as np

TIERS = "DMWLS"
PAIRS = [("D", "M"), ("D", "W"), ("D", "L"), ("M", "W"), ("M", "L"), ("W", "L"), ("S", "L")]
FORBIDDEN = [("S", "D"), ("S", "M"), ("S", "W")]     # must be 0 (8-neighbourhood)
SIDES = [(-1, 0), (0, 1), (1, 0), (0, -1)]          # N E S W
DIAGS = [(-1, 1), (1, 1), (1, -1), (-1, -1)]        # NE SE SW NW (DIAGS[k] lies between SIDES[k], SIDES[k+1])


def load(path):
    return np.array([line.split() for line in open(path) if line.strip()], dtype="<U1")


def key(a, b):
    return "-".join(sorted((a, b), key=TIERS.index))


def shifted(t, dr, dc, fill="#"):
    out = np.full(t.shape, fill, dtype="<U1")
    R, C = t.shape
    out[max(dr, 0):R + min(dr, 0), max(dc, 0):C + min(dc, 0)] = t[max(-dr, 0):R + min(-dr, 0), max(-dc, 0):C + min(-dc, 0)]
    return out


def pair_stats(t, a, b):
    """Edges, convex / concave corners and 45-degree run cells between tiers a and b."""
    R, C = t.shape
    edges = int(((t[:, :-1] == a) & (t[:, 1:] == b)).sum() + ((t[:, :-1] == b) & (t[:, 1:] == a)).sum()
                + ((t[:-1] == a) & (t[1:] == b)).sum() + ((t[:-1] == b) & (t[1:] == a)).sum())
    side = [shifted(t, *o) for o in SIDES]
    diag = [shifted(t, *o) for o in DIAGS]
    convex = concave = diag45 = 0
    for own, oth in ((a, b), (b, a)):
        s = [x == oth for x in side]
        d = [x == oth for x in diag]
        mine = t == own
        ns = sum(s)
        opp = (d[0] & d[2]) | (d[1] & d[3])
        anyd = d[0] | d[1] | d[2] | d[3]
        concave += int((mine & (ns == 0) & anyd & ~opp).sum())
        for k in range(4):
            cv = mine & (ns == 2) & s[k] & s[(k + 1) % 4]
            convex += int(cv.sum())
            st = (SIDES[k][0] - SIDES[(k + 1) % 4][0], SIDES[k][1] - SIDES[(k + 1) % 4][1])
            cp = np.pad(cv, 1)
            fwd = cp[1 + st[0]:1 + st[0] + R, 1 + st[1]:1 + st[1] + C]
            back = cp[1 - st[0]:1 - st[0] + R, 1 - st[1]:1 - st[1] + C]
            diag45 += int((cv & (fwd | back)).sum())
    return {"edges": edges, "corners": convex + concave, "convex": convex, "concave": concave, "45deg": diag45}


def contacts8(t, a, b):
    """8-neighbour contacts between tiers a and b (each unordered cell pair once)."""
    n = 0
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        x, y = t, shifted(t, dr, dc)
        n += int(((x == a) & (y == b)).sum() + ((x == b) & (y == a)).sum())
    return n


def anomaly_map(t):
    """Per cell: '' or the anomaly kind, against any other tier (see module docstring)."""
    t = np.asarray(t, dtype="<U1")
    R, C = t.shape
    out = np.full((R, C), "", dtype=object)
    side = [shifted(t, *o) for o in SIDES]
    diag = [shifted(t, *o) for o in DIAGS]
    fs = [(x != "#") & (x != t) for x in side]
    fd = [(x != "#") & (x != t) for x in diag]
    n = sum(fs)
    out[n == 4] = "dot"
    out[n == 3] = "cap"
    out[(n == 2) & ((fs[0] & fs[2]) | (fs[1] & fs[3]))] = "strip"
    out[(n == 0) & ((fd[0] & fd[2]) | (fd[1] & fd[3]))] = "pinch"
    return out


def longest_run(t):
    best = 0
    R, C = t.shape
    for r in range(R - 1):
        run = 0
        for c in range(C):
            run = run + 1 if t[r, c] != t[r + 1, c] else 0
            best = max(best, run)
    for c in range(C - 1):
        run = 0
        for r in range(R):
            run = run + 1 if t[r, c] != t[r, c + 1] else 0
            best = max(best, run)
    return best


def budgets(tiers):
    t = np.asarray(tiers, dtype="<U1")
    out = {"count": {k: int((t == k).sum()) for k in TIERS}}
    for a, b in PAIRS:
        out[key(a, b)] = pair_stats(t, a, b)
    out["forbidden8"] = {key(a, b): contacts8(t, a, b) for a, b in FORBIDDEN}
    am = anomaly_map(t)
    out["anomaly"] = {k: int((am == k).sum()) for k in ("cap", "strip", "dot", "pinch")}
    junction = 0
    R, C = t.shape
    for r in range(R):
        for c in range(C):
            others = {t[r + dr, c + dc] for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                      if (dr or dc) and 0 <= r + dr < R and 0 <= c + dc < C and t[r + dr, c + dc] != t[r, c]}
            junction += len(others) >= 2
    out["junction"] = junction
    out["run"] = longest_run(t)
    return out


def table(named):
    names = list(named)
    bs = [named[n] for n in names]
    lines = [f"{'':24s}" + "".join(f"{n:>9s}" for n in names) + "   spread"]
    def row(label, vals):
        lines.append(f"{label:24s}" + "".join(f"{v:9d}" for v in vals) + f"{max(vals) - min(vals):9d}")
    for k in TIERS:
        row(f"cells {k}", [b["count"][k] for b in bs])
    for a, b2 in PAIRS:
        k = key(a, b2)
        row(f"{k} edges", [b[k]["edges"] for b in bs])
        row(f"{k} corners", [b[k]["corners"] for b in bs])
        lines.append(f"{'  convex/concave':24s}" + "".join(f"{str(b[k]['convex']) + '/' + str(b[k]['concave']):>9s}" for b in bs))
        row(f"{k} 45deg-run cells", [b[k]["45deg"] for b in bs])
    for a, b2 in FORBIDDEN:
        row(f"{key(a, b2)} contacts (8-nb)", [b["forbidden8"][key(a, b2)] for b in bs])
    for k in ("cap", "strip", "dot", "pinch"):
        row(f"anomaly {k}", [b["anomaly"][k] for b in bs])
    row("junction cells", [b["junction"] for b in bs])
    row("longest straight run", [b["run"] for b in bs])
    return "\n".join(lines)


if __name__ == "__main__":
    named = {p.rsplit("/", 1)[-1].replace(".txt", ""): budgets(load(p)) for p in sys.argv[1:]}
    print(table(named))
