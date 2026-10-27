"""Automatic boundary-budget equalization (v5eq), experiment 005.

Nudges the three tier maps (D/M/L, 20x25, loaded as quantize_v5 does) before quantization, so that the
merged transition classes need fewer surplus pieces. Simulated annealing over the tiers.

Moves (one image per move; tier totals of that image are kept, so the frame and threshold equalization
still hold):
  single  a boundary cell takes the tier of one of its neighbours; a partner cell of that tier takes
          the tier the first cell had (a pair of flips, so the totals stay equal).
  domino  two orthogonally adjacent cells of one tier take a neighbour's tier, and a partner domino
          of that tier takes the old tier back.
Every changed cell must have a neighbour of its new tier after the move (the rule of quantize_v5).
Frame cells never change. A cell may change only if it lies within one cell (8-neighbourhood) of the
original boundary, so the figures stay as they are.

Objective (lower is better):
  sum over merged classes of (max over images - min over images)     [class balance]
  + LAM_FLIP * (cells changed, all images)
  + LAM_RARE * (increase over the original of cells with at most one same-tier 4-neighbour)
    (1-cell protrusions, isolated cells and diagonal-only contacts; they need rare tiles)
Hard cap: at most MAX_FLIPS changed cells per image.

After annealing the script writes, with the -v5eq suffix:
  quantized-v5eq/*.npy, tiers-v5eq.txt        tier maps (npy as quantized-v2; text with changed cells)
  quantized-codes-v5eq.txt, boundary-budgets-v5eq.txt, quantize-report-v5eq.txt
                                              quantize_v5.main() run on the equalized tiers
  roles-v5eq.txt, roles-spec-v5eq.json        make_roles_v5.main() run on the equalized tiers
  scenes-v5eq.txt                             build_scenes_v5.main() run on the equalized roles
  scene-metrics-v5eq.txt                      metapuzzle scene-metrics
  run-full-v5eq/, run-ink-v5eq/               metapuzzle prototype with classes-v4.json / classes-ink.json
The existing v5 scripts are used unchanged: their HERE and the quantizer's equalize_tiers are redirected
to a staging folder (removed at the end), so no existing file is modified.

Usage: equalize_budgets_v5.py [--iters N] [--seeds 0,1,2] [--no-pipeline] [--no-render]
"""
import argparse
import contextlib
import io
import math
import random
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import quantize as q  # noqa: E402
import quantize_v5 as v5  # noqa: E402
import make_roles_v5 as mr  # noqa: E402
import build_scenes_v5 as bs  # noqa: E402

NAMES = q.NAMES
ROWS, COLS = q.ROWS, q.COLS
FRAME = q.FRAME
INNER = ~FRAME
SUFFIX = "v5eq"
STAGE = HERE / "_stage-v5eq"  # scratch folder for the unchanged v5 scripts; removed at the end
ORTH = list(q.OFFSETS)  # (dx, dy): N, E, S, W
DIAGS = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
NEIGH8 = ORTH + DIAGS
MAX_FLIPS = 24
LAM_FLIP = 0.1
LAM_RARE = 1.0
DOMINO_PROB = 0.4
LOCAL_RADIUS = 4
LOCAL_PROB = 0.7
T_HI, T_LO = 0.6, 0.01
ADJACENT_TIERS_ONLY = True  # a flip moves a cell one tier (D<->M or M<->L), never D<->L: a large tonal jump


def shifted(T: np.ndarray, dx: int, dy: int, fill: int = -1) -> np.ndarray:
    """Value of the neighbour at offset (dx, dy) for every cell; fill outside the board."""
    P = np.full((ROWS + 2, COLS + 2), fill, dtype=T.dtype)
    P[1:-1, 1:-1] = T
    return P[1 + dy:1 + dy + ROWS, 1 + dx:1 + dx + COLS]


def neighbours(r: int, c: int, offsets=NEIGH8):
    for dx, dy in offsets:
        rr, cc = r + dy, c + dx
        if 0 <= rr < ROWS and 0 <= cc < COLS:
            yield rr, cc


def differ_mask(T: np.ndarray) -> np.ndarray:
    """Cells with an 8-neighbour of a different tier."""
    m = np.zeros((ROWS, COLS), bool)
    for dx, dy in NEIGH8:
        s = shifted(T, dx, dy)
        m |= (s >= 0) & (s != T)
    return m


def has_neighbour(T: np.ndarray, value: int) -> np.ndarray:
    m = np.zeros((ROWS, COLS), bool)
    for dx, dy in NEIGH8:
        m |= shifted(T, dx, dy) == value
    return m


def dilate(m: np.ndarray) -> np.ndarray:
    P = np.zeros((ROWS + 2, COLS + 2), bool)
    P[1:-1, 1:-1] = m
    out = m.copy()
    for dx, dy in NEIGH8:
        out |= P[1 + dy:1 + dy + ROWS, 1 + dx:1 + dx + COLS]
    return out


def rare_total(T: np.ndarray) -> int:
    """Interior cells with at most one 4-neighbour of their own tier."""
    same4 = sum((shifted(T, dx, dy) == T).astype(int) for dx, dy in ORTH)
    return int(((same4 <= 1) & INNER).sum())


def surplus(hists: list) -> tuple[list, int]:
    """Budget surplus per image (per-class max minus own, summed) and the sum of (max - min) per class."""
    classes = set().union(*hists)
    mx = {c: max(h[c] for h in hists) for c in classes}
    per_image = [sum(mx[c] - h[c] for c in classes) for h in hists]
    spread = sum(mx[c] - min(h[c] for h in hists) for c in classes)
    return per_image, spread


def score(hists: list, rares: list, flips: list, rare0: list) -> float:
    _, spread = surplus(hists)
    rare_up = sum(max(0, rares[k] - rare0[k]) for k in range(3))
    return spread + LAM_FLIP * sum(flips) + LAM_RARE * rare_up


def propose(rnd: random.Random, T: list, allow: list):
    """Random move: (image index, [(row, col, new tier), ...]) or None."""
    k = rnd.randrange(3)
    t = T[k]
    cand = np.flatnonzero(differ_mask(t) & allow[k])
    if cand.size == 0:
        return None
    ar, ac = divmod(int(cand[rnd.randrange(cand.size)]), COLS)
    told = int(t[ar, ac])
    nbr_tiers = sorted({int(t[rr, cc]) for rr, cc in neighbours(ar, ac) if t[rr, cc] != told})
    if ADJACENT_TIERS_ONLY:
        nbr_tiers = [x for x in nbr_tiers if abs(x - told) == 1]
    if not nbr_tiers:
        return None

    def partner_mask(tnew: int, exclude: set) -> np.ndarray:
        m = allow[k] & (t == tnew) & has_neighbour(t, told)
        for cell in exclude:
            m[cell] = False
        return m

    def pick_local(cells: list, centre) -> tuple:
        near = [p for p in cells if max(abs(p[0] - centre[0]), abs(p[1] - centre[1])) <= LOCAL_RADIUS]
        pool = near if (near and rnd.random() < LOCAL_PROB) else cells
        return pool[rnd.randrange(len(pool))]

    if rnd.random() >= DOMINO_PROB:  # single pair
        tnew = nbr_tiers[rnd.randrange(len(nbr_tiers))]
        m = partner_mask(tnew, {(ar, ac)})
        cells = [(int(r), int(c)) for r, c in zip(*np.nonzero(m))]
        if not cells:
            return None
        br, bc = pick_local(cells, (ar, ac))
        return k, [(ar, ac, tnew), (br, bc, told)]

    # domino: a and an orthogonal neighbour a2 of the same tier take tnew
    same = [(rr, cc) for rr, cc in neighbours(ar, ac, ORTH)
            if t[rr, cc] == told and allow[k][rr, cc]]
    if not same:
        return None
    a2r, a2c = same[rnd.randrange(len(same))]
    tiers_a = sorted({int(t[rr, cc]) for rr, cc in list(neighbours(ar, ac)) + list(neighbours(a2r, a2c))
                      if t[rr, cc] != told})
    if ADJACENT_TIERS_ONLY:
        tiers_a = [x for x in tiers_a if abs(x - told) == 1]
    if not tiers_a:
        return None
    tnew = tiers_a[rnd.randrange(len(tiers_a))]
    m = partner_mask(tnew, {(ar, ac), (a2r, a2c)})
    pairs = []
    for r, c in zip(*np.nonzero(m)):
        for rr, cc in neighbours(int(r), int(c), ORTH):
            if m[rr, cc] and (rr, cc) != (ar, ac):
                pairs.append(((int(r), int(c)), (rr, cc)))
    if not pairs:
        return None
    near = [p for p in pairs if max(abs(p[0][0] - ar), abs(p[0][1] - ac)) <= LOCAL_RADIUS]
    pool = near if (near and rnd.random() < LOCAL_PROB) else pairs
    (br, bc), (b2r, b2c) = pool[rnd.randrange(len(pool))]
    return k, [(ar, ac, tnew), (a2r, a2c, tnew), (br, bc, told), (b2r, b2c, told)]


def anneal(seed: int, iters: int, T0: list, tone: list, allow: list, rare0: list, log) -> tuple:
    rnd = random.Random(seed)
    T = [t.copy() for t in T0]
    hists = [v5.analyse(T[k], tone[k])["hist"] for k in range(3)]
    rares = [rare_total(T[k]) for k in range(3)]
    flips = [0, 0, 0]
    cur = score(hists, rares, flips, rare0)
    best = (cur, [t.copy() for t in T])
    accepted = 0
    for it in range(iters):
        temp = T_HI * (T_LO / T_HI) ** (it / max(1, iters - 1))
        mv = propose(rnd, T, allow)
        if mv is None:
            continue
        k, changes = mv
        t = T[k]
        saved = [(r, c, int(t[r, c])) for r, c, _ in changes]
        for r, c, new in changes:
            t[r, c] = new
        valid = all(any(t[rr, cc] == new for rr, cc in neighbours(r, c)) for r, c, new in changes)
        if ADJACENT_TIERS_ONLY:  # never more than one tier away from the original, however many moves
            valid = valid and all(abs(new - int(T0[k][r, c])) <= 1 for r, c, new in changes)
        nf = int(np.count_nonzero(t != T0[k]))
        if not valid or nf > MAX_FLIPS:
            for r, c, old in saved:
                t[r, c] = old
            continue
        hs, rs, fl = hists.copy(), rares.copy(), flips.copy()
        hs[k] = v5.analyse(t, tone[k])["hist"]
        rs[k] = rare_total(t)
        fl[k] = nf
        new_score = score(hs, rs, fl, rare0)
        if new_score <= cur or rnd.random() < math.exp(-(new_score - cur) / temp):
            hists, rares, flips, cur = hs, rs, fl, new_score
            accepted += 1
            if cur < best[0]:
                best = (cur, [x.copy() for x in T])
        else:
            for r, c, old in saved:
                t[r, c] = old
        if (it + 1) % max(1, iters // 5) == 0:
            per, spread = surplus(hists)
            log(f"    seed {seed} it {it + 1:6d} T {temp:.3f} accepted {accepted:6d} "
                f"surplus {per} spread {spread} flips {flips} score {cur:.2f} best {best[0]:.2f}")
    return best


def report_state(label: str, T: list, tone: list, rare0: list, target) -> dict:
    hists = [v5.analyse(T[k], tone[k])["hist"] for k in range(3)]
    per, spread = surplus(hists)
    flips = [int(np.count_nonzero(T[k] != T0_GLOBAL[k])) for k in range(3)]
    rares = [rare_total(T[k]) for k in range(3)]
    totals = [np.bincount(T[k].ravel(), minlength=3).tolist() for k in range(3)]
    print(f"{label}")
    print(f"   surplus per image (cat / sailboat / tree): {per[0]} / {per[1]} / {per[2]}   total {sum(per)}")
    print(f"   sum over classes of (max - min): {spread}")
    print(f"   cells changed per image: {flips[0]} / {flips[1]} / {flips[2]}")
    print(f"   tier totals D/M/L per image: {totals}   (target {list(target)})")
    print(f"   rare interior cells per image: {rares} (original {rare0})")
    return {"per": per, "spread": spread, "flips": flips, "hists": hists}


T0_GLOBAL: list = []


def main() -> None:
    global T0_GLOBAL
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=30000)
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--no-pipeline", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args()
    t_start = time.time()

    v2 = {n: np.load(q.TARGETS / f"{n}-v2.npy") for n in NAMES}
    orig_equalize = q.equalize_tiers
    tiers, _, target, _ = orig_equalize(v2)
    T0 = [tiers[n].astype(np.int64) for n in NAMES]
    T0_GLOBAL = [t.copy() for t in T0]
    tone = [v2[n] for n in NAMES]

    # Boundary of the original maps, dilated by one cell: the only cells that may change.
    allow = [dilate(differ_mask(t)) & INNER for t in T0]
    rare0 = [rare_total(t) for t in T0]
    print("1. original tiers (equalized): D/M/L per image", [np.bincount(t.ravel(), minlength=3).tolist() for t in T0])
    print(f"   cells allowed to change per image: {[int(a.sum()) for a in allow]} "
          f"(interior cells within one cell of the boundary)")
    base = report_state("2. before annealing", T0, tone, rare0, target)

    def log(msg: str) -> None:
        print(msg, flush=True)

    print("3. simulated annealing (one run per seed; the best final score is kept)")
    results = []
    for seed in [int(s) for s in args.seeds.split(",")]:
        t0 = time.time()
        sc, Tb = anneal(seed, args.iters, T0, tone, allow, rare0, log)
        results.append((sc, seed, Tb))
        print(f"   seed {seed}: best score {sc:.2f} ({time.time() - t0:.0f} s)", flush=True)
    sc, seed, T = min(results, key=lambda x: x[0])
    print(f"   chosen seed {seed}, score {sc:.2f}")

    # Checks: totals kept, changes within the allowed band, frame untouched.
    for k in range(3):
        assert (np.bincount(T[k].ravel(), minlength=3) == target).all(), "tier totals changed"
        assert not (T[k] != T0[k])[~allow[k] & (T[k] != T0[k])].any(), "change outside the band"
        assert not (T[k] != T0[k])[FRAME].any(), "frame cell changed"
    after = report_state("4. after annealing", T, tone, rare0, target)
    print("   changed cells (row, col) old -> new:")
    for k, n in enumerate(NAMES):
        ch = [(int(r), int(c), int(T0[k][r, c]), int(T[k][r, c])) for r, c in zip(*np.nonzero(T[k] != T0[k]))]
        print(f"   {n:9s} " + ", ".join(f"({r},{c}) {q.TIER_SYM[a]}->{q.TIER_SYM[b]}" for r, c, a, b in ch))

    # Write the tier maps and the -v5eq outputs.
    out_tiers = HERE / f"quantized-{SUFFIX}"
    out_tiers.mkdir(exist_ok=True)
    text = ["# Equalized tier maps (v5eq), experiment 005. D / M / L per cell; A = cat, B = sailboat, C = tree.",
            "# Changed cells (vs quantized-v2): (row, col) old -> new.", ""]
    for k, n in enumerate(NAMES):
        np.save(out_tiers / f"{n}.npy", T[k].astype(np.int64))
        text.append(f"# {n}")
        text += [" ".join(q.TIER_SYM[x] for x in row) for row in T[k]]
        ch = [f"({int(r)},{int(c)}) {q.TIER_SYM[int(T0[k][r, c])]}->{q.TIER_SYM[int(T[k][r, c])]}"
              for r, c in zip(*np.nonzero(T[k] != T0[k]))]
        text.append("changed: " + (", ".join(ch) or "-"))
        text.append("")
    (HERE / f"tiers-{SUFFIX}.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(f"wrote {out_tiers} and tiers-{SUFFIX}.txt")

    if args.no_pipeline:
        return

    # Rest of the v5 pipeline on the equalized tiers, through the unchanged scripts.
    if STAGE.exists():
        shutil.rmtree(STAGE)
    (STAGE / "quantized-v2").mkdir(parents=True)
    for k, n in enumerate(NAMES):
        np.save(STAGE / "quantized-v2" / f"{n}.npy", T[k])

    buf = io.StringIO()
    q_orig = q.HERE
    q.HERE = STAGE
    v5.HERE = STAGE
    q.equalize_tiers = lambda _tones: (dict(zip(NAMES, T)), None, target, None)
    try:
        with contextlib.redirect_stdout(buf):
            v5.main()
    finally:
        q.equalize_tiers = orig_equalize
        q.HERE = q_orig
        v5.HERE = HERE
    (HERE / f"quantize-report-{SUFFIX}.txt").write_text(buf.getvalue(), encoding="utf-8")
    shutil.copy(STAGE / "quantized-codes-v5.txt", HERE / f"quantized-codes-{SUFFIX}.txt")
    shutil.copy(STAGE / "boundary-budgets-v5.txt", HERE / f"boundary-budgets-{SUFFIX}.txt")
    print("quantize_v5.main on equalized tiers: report, codes and budgets written")

    mr.HERE = STAGE
    try:
        with contextlib.redirect_stdout(io.StringIO()) as mb:
            mr.main()
    finally:
        mr.HERE = HERE
    shutil.copy(STAGE / "roles-v5.txt", HERE / f"roles-{SUFFIX}.txt")
    shutil.copy(STAGE / "roles-spec-v5.json", HERE / f"roles-spec-{SUFFIX}.json")
    print("make_roles_v5 on equalized tiers:")
    print("   " + "\n   ".join(mb.getvalue().strip().splitlines()[:6]))

    bs.HERE = STAGE
    saved_argv = sys.argv
    sys.argv = ["build_scenes_v5.py"]
    try:
        with contextlib.redirect_stdout(io.StringIO()) as bb:
            bs.main()
    finally:
        bs.HERE = HERE
        sys.argv = saved_argv
    shutil.copy(STAGE / "scenes-v5.txt", HERE / f"scenes-{SUFFIX}.txt")
    print("build_scenes_v5 on equalized roles: " + bb.getvalue().strip().splitlines()[-1])

    import subprocess as sp
    metrics = sp.run(["metapuzzle", "scene-metrics", str(HERE / f"scenes-{SUFFIX}.txt")],
                     capture_output=True, text=True)
    (HERE / f"scene-metrics-{SUFFIX}.txt").write_text(metrics.stdout + metrics.stderr, encoding="utf-8")
    print(f"scene-metrics exit status {metrics.returncode} (3 = a scene gate fails)")
    shutil.rmtree(STAGE)

    if args.no_render:
        return
    for classes, out in [("classes-v4.json", "run-full-v5eq"), ("classes-ink.json", "run-ink-v5eq")]:
        cmd = ["metapuzzle", "prototype", "--scenes", str(HERE / f"scenes-{SUFFIX}.txt"),
               "--classes", str(HERE / classes), "--out", str(HERE / out),
               "--sizes", "20x25,20x25,20x25", "--border", "standard", "--rotation", "quarter",
               "--seed", "0", "--iters", "300000", "--cell", "32"]
        print("render:", " ".join(cmd[1:4]), out, flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(f"   exit {r.returncode}; {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:]}")
    print(f"done in {time.time() - t_start:.0f} s")


if __name__ == "__main__":
    main()
