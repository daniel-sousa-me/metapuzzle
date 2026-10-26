"""Fill scene intents into class maps with one shared histogram (experiment 003).

Intent file: the scene text format, but a cell may list alternatives, e.g. ``ME|FO``.
Fixed cells (one token, may carry @rot) never change. The tool assigns the alternative cells
so every scene reaches the inventory given with --inv, then anneals by swapping two free
cells of one scene (histogram-preserving) to minimise forbidden seams and the scene-gate
metrics (2x2 window reuse, transferable blob, same-position overlap, both directions).

  python fill.py intent.txt --inv SK=14,SN=6,... [--rot] [--iters 40000] [--seed 0] > scenes.txt
"""
from __future__ import annotations

import argparse
import math
import random
import sys
from collections import Counter

sys.path.insert(0, "/home/user/metapuzzle/src")
from metapuzzle.scene_metrics import transferable_blob, window_reuse  # noqa: E402

EDGES = {
    "SK": "SSSS", "SN": "NNNN", "ME": "MMMM", "FO": "FFFF", "DP": "DDDD", "RU": "RRRR", "PH": "RRRR",
    "SU": "SSSS", "S/": "SNNS", "S\\": "SSNN", "F/": "SFFS", "F\\": "SSFF", "HD": "SDDD", "HB": "SDDD",
    "HL": "SDDD", "HF": "SFFF", "MO": "DDDD",
}
SOFT = {frozenset("SN"), frozenset("MF"), frozenset("FD")}


def edges(c, r):
    e = EDGES[c]
    k = (r // 90) % 4
    return [e[(i - k) % 4] for i in range(4)]


def parse(path):
    scenes, cur = [], []
    for line in open(path):
        line = line.split("#", 1)[0].strip()
        if not line:
            if cur:
                scenes.append(cur)
                cur = []
            continue
        cur.append(line.split())
    if cur:
        scenes.append(cur)
    out = []
    for g in scenes:
        cells = []
        for row in g:
            r = []
            for t in row:
                if "|" in t:
                    r.append(("free", t.split("|")))
                else:
                    lab, _, rot = t.partition("@")
                    r.append(("fixed", (lab, int(rot or 0))))
            cells.append(r)
        out.append(cells)
    return out


def seam_bad(grid, rot):
    rows, cols = len(grid), len(grid[0])
    bad = 0
    for y in range(rows):
        for x in range(cols):
            e = edges(grid[y][x], rot[y][x])
            for dx, dy, i, j in ((1, 0, 1, 3), (0, 1, 2, 0)):
                X, Y = x + dx, y + dy
                if X >= cols or Y >= rows:
                    continue
                a, b = e[i], edges(grid[Y][X], rot[Y][X])[j]
                if a != b and "R" not in (a, b) and frozenset((a, b)) not in SOFT:
                    bad += 1
    return bad


def metrics(grids, use_rot):
    worst = {"w": 0.0, "b": 0.0, "s": 0.0, "wr": 0.0}
    tot = 0.0
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            a, b = grids[i], grids[j]
            n = len(a) * len(a[0])
            w = window_reuse(a, b, 2, 2)
            bl = transferable_blob(a, b) / n
            s = 0.0
            if (len(a), len(a[0])) == (len(b), len(b[0])):
                s = sum(x == y for ra, rb in zip(a, b) for x, y in zip(ra, rb)) / n
            wr = window_reuse(a, b, 2, 2, True) if use_rot else 0.0
            for k, v in (("w", w), ("b", bl), ("s", s), ("wr", wr)):
                worst[k] = max(worst[k], v)
            tot += w + bl + s + 0.5 * wr
    return worst, tot


def cost(grids, rots, use_rot):
    bad = sum(seam_bad(g, r) for g, r in zip(grids, rots))
    worst, tot = metrics(grids, use_rot)
    over = max(0, worst["w"] - 0.22) + max(0, worst["b"] - 0.075) + max(0, worst["s"] - 0.18)
    return 60 * bad + 20 * over + tot / 6, bad, worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("intent")
    ap.add_argument("--inv", required=True)
    ap.add_argument("--rot", action="store_true", help="also weigh rotated 2x2 reuse")
    ap.add_argument("--iters", type=int, default=30000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    inv = Counter({k: int(v) for k, v in (kv.split("=") for kv in a.inv.split(","))})
    rng = random.Random(a.seed)
    scenes = parse(a.intent)
    grids, rots, free = [], [], []
    for s, cells in enumerate(scenes):
        g = [[c[1][0] if c[0] == "fixed" else None for c in row] for row in cells]
        r = [[c[1][1] if c[0] == "fixed" else 0 for c in row] for row in cells]
        need = inv - Counter(x for row in g for x in row if x)
        extra = Counter(x for row in g for x in row if x) - inv
        if extra:
            sys.exit(f"scene {'ABC'[s]}: fixed cells exceed inventory: {dict(extra)}")
        fr = [(y, x, cells[y][x][1]) for y in range(len(cells)) for x in range(len(cells[0])) if cells[y][x][0] == "free"]
        if sum(need.values()) != len(fr):
            sys.exit(f"scene {'ABC'[s]}: {len(fr)} free cells but {sum(need.values())} classes left {dict(need)}")
        # greedy feasible fill: most constrained cells first
        order = sorted(fr, key=lambda t: len(t[2]))
        pool = Counter(need)
        for k, (y, x, opts) in enumerate(order):
            ch = [o for o in opts if pool[o] > 0]
            if not ch:
                sys.exit(f"scene {'ABC'[s]}: cannot fill ({y},{x}) from {opts}; left {dict(+pool)}")
            avail = Counter(o for _, _, op in order[k:] for o in op)
            o = max(ch, key=lambda o: pool[o] / avail[o] + 1e-3 * rng.random())
            g[y][x] = o
            pool[o] -= 1
        grids.append(g)
        rots.append(r)
        free.append([(y, x, set(opts)) for y, x, opts in fr])
    cur, bad, worst = cost(grids, rots, a.rot)
    best = (cur, [[row[:] for row in g] for g in grids], bad, worst)
    T0 = 0.6
    for it in range(a.iters):
        T = T0 * (1 - it / a.iters) + 1e-3
        s = rng.randrange(3)
        if len(free[s]) < 2:
            continue
        (y1, x1, o1), (y2, x2, o2) = rng.sample(free[s], 2)
        c1, c2 = grids[s][y1][x1], grids[s][y2][x2]
        if c1 == c2 or c2 not in o1 or c1 not in o2:
            continue
        grids[s][y1][x1], grids[s][y2][x2] = c2, c1
        new, nb, nw = cost(grids, rots, a.rot)
        if new <= cur or rng.random() < math.exp((cur - new) / T):
            cur = new
            if new < best[0]:
                best = (new, [[row[:] for row in g] for g in grids], nb, nw)
        else:
            grids[s][y1][x1], grids[s][y2][x2] = c1, c2
    _, gbest, bad, worst = best
    print(f"# filled by fill.py seed {a.seed}: forbidden seams {bad}; worst pair "
          + " ".join(f"{k}={v:.3f}" for k, v in worst.items()), file=sys.stderr)
    for s, (g, r) in enumerate(zip(gbest, rots)):
        print(f"# {'ABC'[s]}")
        for row, rr in zip(g, r):
            print(" ".join(c if not o else f"{c}@{o}" for c, o in zip(row, rr)))
        print()


if __name__ == "__main__":
    main()
