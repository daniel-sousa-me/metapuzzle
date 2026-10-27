"""Boundary budgets of a tier map (experiment 011).

A tier map is ROWS x COLS tokens: D (dark), M (mid), L (light), S (dark chips scattered on light)
and W (mid with wave lenses, counted as M). Transition pieces are a shared inventory (FINDINGS 12),
so the three pictures need matching budgets per unordered tier pair. S-L needs no transition
(S is already a mixture), so it is not a budget pair.

Per pair X-Y:
  edges    4-neighbour cell edges between an X cell and a Y cell.
  corners  cells (of either tier) with the other tier on exactly two adjacent sides (convex),
           plus cells with the other tier on a diagonal only (concave).
Anomalies (need rare tiles, so the designs avoid them; see anomaly_map, any foreign tier):
  cap      foreign tier on three sides (a 1-cell tip);  strip  on two opposite sides (1 wide);
  dot      on all four sides;  pinch  on two opposite diagonals and no side.
45-degree runs (diagonal_runs): convex corners chained diagonally, the future diagonal tile.
Junction cells touch (by side or diagonal) two or more other budget tiers: three-tier points.
run      longest boundary segment along one grid line (any pair), in edges.

Usage: python3 budget.py tiers-A.txt [tiers-B.txt ...]
"""
import sys

import numpy as np

TIERS = "DMLS"
PAIRS = [("D", "M"), ("D", "L"), ("M", "L"), ("D", "S"), ("M", "S")]  # S-L is free
FREE = {frozenset("SL")}
SIDES = [(-1, 0), (0, 1), (1, 0), (0, -1)]          # N E S W
DIAGS = [(-1, 1), (1, 1), (1, -1), (-1, -1)]        # NE SE SW NW (DIAGS[k] lies between SIDES[k], SIDES[k+1])


def load(path):
    rows = [line.split() for line in open(path) if line.strip()]
    return np.array(rows)


def norm(t):
    """W counts as M."""
    t = np.array(t, dtype="<U1")
    t[t == "W"] = "M"
    return t


def shifted(t, dr, dc, fill="#"):
    out = np.full(t.shape, fill, dtype="<U1")
    R, C = t.shape
    out[max(dr, 0):R + min(dr, 0), max(dc, 0):C + min(dc, 0)] = t[max(-dr, 0):R + min(-dr, 0), max(-dc, 0):C + min(-dc, 0)]
    return out


def pair_key(a, b):
    return "-".join(sorted((a, b), key=TIERS.index))


def budgets(tiers):
    """Dict with tier counts, per-pair edges / corners / anomalies, junctions and longest run."""
    t = norm(tiers)
    R, C = t.shape
    side = [shifted(t, *o) for o in SIDES]
    diag = [shifted(t, *o) for o in DIAGS]
    out = {"count": {k: int((t == k).sum()) for k in TIERS}}
    out["count"]["W"] = int((np.asarray(tiers) == "W").sum())
    for a, b in PAIRS:
        key = pair_key(a, b)
        edges = int(((t[:, :-1] == a) & (t[:, 1:] == b)).sum() + ((t[:, :-1] == b) & (t[:, 1:] == a)).sum()
                    + ((t[:-1] == a) & (t[1:] == b)).sum() + ((t[:-1] == b) & (t[1:] == a)).sum())
        res = {"edges": edges, "corners": 0, "convex": 0, "concave": 0, "cap": 0, "strip": 0, "dot": 0, "pinch": 0}
        for own, oth in ((a, b), (b, a)):
            s = np.stack([x == oth for x in side])     # 4 x R x C
            d = np.stack([x == oth for x in diag])
            mine = t == own
            ns = s.sum(0)
            adj2 = np.zeros_like(mine)
            for k in range(4):
                adj2 |= s[k] & s[(k + 1) % 4]
            convex = mine & (ns == 2) & adj2
            strip = mine & (ns == 2) & ~adj2
            concave = mine & (ns == 0) & d.any(0) & ~((d[0] & d[2]) | (d[1] & d[3]))
            pinch = mine & (ns == 0) & ((d[0] & d[2]) | (d[1] & d[3]))
            res["convex"] += int(convex.sum())
            res["concave"] += int(concave.sum())
            res["strip"] += int(strip.sum())
            res["cap"] += int((mine & (ns == 3)).sum())
            res["dot"] += int((mine & (ns == 4)).sum())
            res["pinch"] += int(pinch.sum())
        res["corners"] = res["convex"] + res["concave"]
        out[key] = res
    # junctions: cells whose 8-neighbourhood holds two or more tiers it needs a transition against
    junction = 0
    for r in range(R):
        for c in range(C):
            others = set()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    if (dr or dc) and 0 <= rr < R and 0 <= cc < C and t[rr, cc] != t[r, c] \
                            and frozenset((t[r, c], t[rr, cc])) not in FREE:
                        others.add(t[rr, cc])
            junction += len(others) >= 2
    out["junction"] = junction
    am = anomaly_map(tiers)
    out["anomaly"] = {k: int((am == k).sum()) for k in ("cap", "strip", "dot", "pinch")}
    out["run"] = longest_run(t)
    return out


def longest_run(t):
    """Longest straight boundary (between budget-pair tiers) along one grid line, in edges."""
    best = 0
    def is_b(x, y):
        return x != y and frozenset((x, y)) not in FREE
    R, C = t.shape
    for r in range(R - 1):            # horizontal grid lines between rows r and r+1
        run = 0
        for c in range(C):
            run = run + 1 if is_b(t[r, c], t[r + 1, c]) else 0
            best = max(best, run)
    for c in range(C - 1):
        run = 0
        for r in range(R):
            run = run + 1 if is_b(t[r, c], t[r, c + 1]) else 0
            best = max(best, run)
    return best


def table(named):
    """Text table: one column per picture, rows per pair metric, plus spread."""
    names = list(named)
    bs = [named[n] for n in names]
    lines = [f"{'':22s}" + "".join(f"{n:>9s}" for n in names) + "   spread"]
    def row(label, vals):
        lines.append(f"{label:22s}" + "".join(f"{v:9d}" for v in vals) + f"{max(vals) - min(vals):9d}")
    for k in "DMLSW":
        row(f"cells {k}", [b["count"][k] for b in bs])
    for a, b2 in PAIRS:
        key = pair_key(a, b2)
        row(f"{key} edges", [b[key]["edges"] for b in bs])
        row(f"{key} corners", [b[key]["corners"] for b in bs])
        lines.append(f"{'  convex/concave':22s}" + "".join(f"{str(b[key]['convex']) + '/' + str(b[key]['concave']):>9s}" for b in bs))
    for k in ("cap", "strip", "dot", "pinch"):
        row(f"anomaly {k}", [b["anomaly"][k] for b in bs])
    row("junction cells", [b["junction"] for b in bs])
    row("longest straight run", [b["run"] for b in bs])
    return "\n".join(lines)


if __name__ == "__main__":
    named = {p.rsplit("/", 1)[-1].replace(".txt", ""): budgets(load(p)) for p in sys.argv[1:]}
    print(table(named))


def anomaly_map(tiers):
    """Per cell: '' or the anomaly kind. A neighbour is foreign when its tier differs and the pair
    needs a transition (anything but S-L). cap: foreign on three sides (a 1-cell tip or notch);
    strip: foreign on two opposite sides (1 cell wide); dot: foreign on all sides; pinch: foreign on
    two opposite diagonals and no side (two regions meeting at a corner)."""
    t = norm(tiers)
    R, C = t.shape
    out = np.full((R, C), "", dtype=object)

    def foreign(r, c, rr, cc):
        return 0 <= rr < R and 0 <= cc < C and t[rr, cc] != t[r, c] \
            and frozenset((t[r, c], t[rr, cc])) not in FREE

    for r in range(R):
        for c in range(C):
            s = [foreign(r, c, r + dr, c + dc) for dr, dc in SIDES]
            d = [foreign(r, c, r + dr, c + dc) for dr, dc in DIAGS]
            n = sum(s)
            if n == 4:
                out[r, c] = "dot"
            elif n == 3:
                out[r, c] = "cap"
            elif n == 2 and ((s[0] and s[2]) or (s[1] and s[3])):
                out[r, c] = "strip"
            elif n == 0 and ((d[0] and d[2]) or (d[1] and d[3])):
                out[r, c] = "pinch"
    return out


def diagonal_runs(tiers, min_steps=2):
    """45-degree staircase boundaries, per budget pair: (number of runs, cells in runs).
    A run is a chain of convex corner cells of one tier with the same orientation (other tier on
    the same two adjacent sides) placed diagonally one after another, e.g. (r, c), (r-1, c-1), ...;
    runs of at least `min_steps` cells count. A future 45-degree diagonal tile would replace each."""
    t = norm(tiers)
    R, C = t.shape
    res = {pair_key(*p): [0, 0] for p in PAIRS}
    for own in TIERS:
        for oth in TIERS:
            if own == oth or frozenset((own, oth)) in FREE or pair_key(own, oth) not in res:
                continue
            for k in range(4):                       # other tier on SIDES[k] and SIDES[k+1]
                a, b = SIDES[k], SIDES[(k + 1) % 4]
                def corner(r, c):
                    if not (0 <= r < R and 0 <= c < C) or t[r, c] != own:
                        return False
                    ok = []
                    for dr, dc in (a, b):
                        rr, cc = r + dr, c + dc
                        ok.append(0 <= rr < R and 0 <= cc < C and t[rr, cc] == oth)
                    return all(ok)
                # the staircase advances along (a - b) or (b - a); walk along one of them
                step = (a[0] - b[0], a[1] - b[1])
                seen = set()
                for r in range(R):
                    for c in range(C):
                        if (r, c) in seen or not corner(r, c) or corner(r - step[0], c - step[1]):
                            continue
                        n, rr, cc = 0, r, c
                        while corner(rr, cc):
                            seen.add((rr, cc)); n += 1
                            rr, cc = rr + step[0], cc + step[1]
                        if n >= min_steps:
                            res[pair_key(own, oth)][0] += 1
                            res[pair_key(own, oth)][1] += n
    return res
