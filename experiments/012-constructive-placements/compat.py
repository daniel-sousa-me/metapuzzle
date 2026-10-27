"""Class-map compatibility of the constructive families (experiment 005 scenes-v3, 20x25).

Run: python3 experiments/012-constructive-placements/compat.py [--png]

A construction fixes each piece's trajectory (c_A, c_B, c_C). A piece can carry one class only, so it is
"satisfied" when A(c_A) = B(c_B) = C(c_C). Counts reported:
- reference: cells with A = B = C at the same position (what "all pieces fixed" would satisfy);
- random: expected count for random trajectories, sum_X n_X^3 / N^2;
- cyclic bound: any scheme in which pieces cycle through cell triples (c, s(c), s^2(c)) (checkerboard,
  speed and H1 = H2 group schemes) needs v(s(c)) = rot v(c) for v(c) = (A(c), B(c), C(c)); the best
  geometry-free count is sum_X n(X,X,X) + sum over rotation orbits 3 min(n(v), n(rot v), n(rot^2 v));
- checkerboard bound: fixed cells need constant v, moving cells the cyclic matching above;
- group family (tray 21x24): exhaustive over the 22 parameter sets and all 504^2 translations of B and C;
- product family (standard 19x25): the construction itself (6 role assignments) and an upper bound
  from hill-climbing over arbitrary row and column permutations with fixed ends (relaxation).
Then the best scheme's pictures are "repainted" by majority vote along trajectories (the strict linked
canvas) and the fraction of cells that change is reported; --png renders the before/after panels.
"""
from __future__ import annotations

import argparse
import itertools
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from metapuzzle.scene import load_scenes  # noqa: E402

import construct  # noqa: E402

SCENES = ROOT / "experiments/005-hybrid-tones/scenes-v3.txt"


def load(tier=False):
    maps = load_scenes(SCENES)
    grids = [np.array([[c[0] if tier else c for c in row] for row in m.cls], dtype=object) for m in maps]
    return grids  # each rows x cols


def crop(grids, cols, rows):
    out = []
    for g in grids:
        h, w = g.shape
        g = g[:rows, :min(cols, w)]
        while g.shape[1] < cols:  # pad by repeating the last column
            g = np.concatenate([g, g[:, -1:]], axis=1)
        out.append(g)
    return out


def rot(v):
    return (v[2], v[0], v[1])


def vector_stats(grids, mask=None):
    A, B, C = grids
    vecs = Counter()
    for y in range(A.shape[0]):
        for x in range(A.shape[1]):
            if mask is None or mask[y, x]:
                vecs[(A[y, x], B[y, x], C[y, x])] += 1
    const = sum(n for v, n in vecs.items() if len(set(v)) == 1)
    cyc, seen = 0, set()
    for v in vecs:
        if len(set(v)) == 1 or v in seen:
            continue
        orbit = [v, rot(v), rot(rot(v))]
        seen.update(orbit)
        cyc += 3 * min(vecs.get(o, 0) for o in orbit)
    return const, cyc


def random_expect(grids):
    n = grids[0].size
    hs = [Counter(g.ravel()) for g in grids]
    return sum(hs[0][x] * hs[1].get(x, 0) * hs[2].get(x, 0) for x in hs[0]) / n ** 2


def count(grids, maps, cols):
    A, B, C = grids
    s = 0
    for c, (cb, _) in maps[1].items():
        cc = maps[2][c][0]
        a = A[c // cols, c % cols]
        s += a == B[cb // cols, cb % cols] == C[cc // cols, cc % cols]
    return int(s)


def group_family(grids, cols, rows):
    A, B, C = (g.ravel() for g in grids)
    n = cols * rows
    best = (-1, None)
    shifts = [(tx, ty) for ty in range(rows) for tx in range(cols)]
    tmat = np.array([[((c % cols + tx) % cols) + ((c // cols + ty) % rows) * cols for c in range(n)] for tx, ty in shifts])
    for hh, hv in construct.group_params(cols, rows):
        maps = construct.group_maps(cols, rows, hh, hv)
        psi1 = np.array([maps[1][c][0] for c in range(n)])
        psi2 = np.array([maps[2][c][0] for c in range(n)])
        M1 = (A[None, :] == B[tmat[:, psi1]]).astype(np.float32)  # [t1, c]
        M2 = (A[None, :] == C[tmat[:, psi2]]).astype(np.float32)
        cnt = M1 @ M2.T
        i, j = np.unravel_index(int(np.argmax(cnt)), cnt.shape)
        if cnt[i, j] > best[0]:
            best = (int(cnt[i, j]), (hh, hv, shifts[i], shifts[j]))
    hh, hv, t1, t2 = best[1]
    return best[0], construct.group_maps(cols, rows, hh, hv, ((0, 0), t1, t2)), best[1]


def product_family(grids, cols, rows):
    base = construct.product_maps(cols, rows)
    best = (-1, None)
    for perm in itertools.permutations(range(3)):
        # use ordering perm[0] as A: trajectories c_perm0 -> c_perm1 -> c_perm2
        inv = {base[perm[0]][p][0]: p for p in base[0]}
        maps = [{c: base[perm[k]][inv[c]] for c in inv} for k in range(3)]
        n = count(grids, maps, cols)
        if n > best[0]:
            best = (n, maps)
    return best


def permutation_bound(grids, cols, rows, iters=200_000, restarts=4, seed=0):
    """Max over row/column permutations (ends fixed) of #cells with A(x,y) = B(a1 x, b1 y) = C(a2 x, b2 y)."""
    A, B, C = grids
    rng = random.Random(seed)
    best_all = 0
    for _ in range(restarts):
        perms = []
        for n in (cols, rows, cols, rows):
            mid = list(range(1, n - 1))
            rng.shuffle(mid)
            perms.append([0] + mid + [n - 1])
        a1, b1, a2, b2 = perms

        def sat_cell(x, y):
            return A[y, x] == B[b1[y], a1[x]] == C[b2[y], a2[x]]

        cur = sum(sat_cell(x, y) for y in range(rows) for x in range(cols))
        T = 2.0
        for it in range(iters):
            which = rng.randrange(4)
            p = perms[which]
            n = len(p)
            i, j = rng.sample(range(1, n - 1), 2)
            if which in (0, 2):
                cells = [(x, y) for x in (i, j) for y in range(rows)]
            else:
                cells = [(x, y) for y in (i, j) for x in range(cols)]
            before = sum(sat_cell(x, y) for x, y in cells)
            p[i], p[j] = p[j], p[i]
            after = sum(sat_cell(x, y) for x, y in cells)
            d = after - before
            temp = T * (1 - it / iters) + 0.05
            if d >= 0 or rng.random() < np.exp(d / temp):
                cur += d
            else:
                p[i], p[j] = p[j], p[i]
            best_all = max(best_all, cur)
    return best_all


def repaint(grids, maps, cols):
    """Majority class along each trajectory; returns repainted grids and per-picture changed fraction."""
    A, B, C = grids
    out = [g.copy() for g in grids]
    for c in maps[0]:
        cells = [maps[k][c][0] for k in range(3)]
        vals = [grids[k][cc // cols, cc % cols] for k, cc in enumerate(cells)]
        top = Counter(vals).most_common()
        x = top[0][0] if top[0][1] > 1 else vals[0]
        for k, cc in enumerate(cells):
            out[k][cc // cols, cc % cols] = x
    changed = [float((out[k] != grids[k]).mean()) for k in range(3)]
    return out, changed


TONE = {"L": 225, "M": 140, "D": 40}


def render(panels, path, scale=10):
    from PIL import Image, ImageDraw
    h, w = panels[0][0].shape
    rows_, cols_ = len(panels), len(panels[0])
    img = Image.new("RGB", (cols_ * (w * scale + 10) + 10, rows_ * (h * scale + 10) + 10), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    for r, rowp in enumerate(panels):
        for c, g in enumerate(rowp):
            ox, oy = 10 + c * (w * scale + 10), 10 + r * (h * scale + 10)
            for y in range(h):
                for x in range(w):
                    cls = g[y, x]
                    t = sum(TONE[ch] for ch in cls) // len(cls)
                    dr.rectangle([ox + x * scale, oy + y * scale, ox + (x + 1) * scale - 1, oy + (y + 1) * scale - 1], fill=(t, t, t))
    img.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--iters", type=int, default=200_000)
    a = ap.parse_args()
    for tier in (False, True):
        label = "tiers L/M/D" if tier else "full classes (9)"
        full = load(tier)
        n = full[0].size
        const, cyc = vector_stats(full)
        checker = []
        for par in (0, 1):
            mask = np.fromfunction(lambda y, x: (x + y) % 2 == par, full[0].shape)
            cb, _ = vector_stats(full, mask)
            cw_const, cw_cyc = vector_stats(full, ~mask)
            checker.append(cb + cw_cyc + cw_const - cw_const % 3)
        print(f"## {label}, 20x25 ({n} cells)")
        print(f"same class at the same cell in A, B, C: {const} ({100 * const / n:.1f}%)")
        print(f"random trajectories (expected): {random_expect(full):.1f} ({100 * random_expect(full) / n:.1f}%)")
        print(f"cyclic-scheme bound: {const + cyc} ({100 * (const + cyc) / n:.1f}%)  [constant {const} + rotation orbits {cyc}]")
        print(f"checkerboard bound (best parity): {max(checker)} ({100 * max(checker) / n:.1f}%)")
        g = crop(full, 21, 24)
        gb, gmaps, gpar = group_family(g, 21, 24)
        print(f"group family, tray 21x24 (crop + pad), best of 22 x 504^2 schemes: {gb} / 504 ({100 * gb / 504:.1f}%); "
              f"random {100 * random_expect(g) / 504:.1f}%; params {gpar}")
        p = crop(full, 19, 25)
        pb, pmaps = product_family(p, 19, 25)
        bound = permutation_bound(p, 19, 25, a.iters)
        print(f"product family, standard 19x25 (crop): construction {pb} / 475 ({100 * pb / 475:.1f}%); "
              f"any row/column permutations (upper bound, annealed): {bound} ({100 * bound / 475:.1f}%); random {100 * random_expect(p) / 475:.1f}%")
        for name, grids, maps, cols in (("group 21x24", g, gmaps, 21), ("product 19x25", p, pmaps, 19)):
            rep, changed = repaint(grids, maps, cols)
            print(f"repaint {name} by majority vote: cells changed A/B/C = " + "/".join(f"{100 * c:.0f}%" for c in changed))
            if a.png and not tier:
                derived = [grids[0].copy(), grids[0].copy(), grids[0].copy()]
                for c in maps[0]:
                    for k in (1, 2):
                        cc = maps[k][c][0]
                        derived[k][cc // cols, cc % cols] = grids[0][c // cols, c % cols]
                tag = name.split()[0]
                render([grids, derived, rep], HERE / f"linked-canvas-{tag}.png")
        print()


if __name__ == "__main__":
    main()
