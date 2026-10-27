"""Automatic boundary-budget equalization, figure-aware (v5b, -v5eq2 outputs), experiment 005.

Revises equalize_budgets_v5.py. The v5eq run reached surplus 0/1/0 but put olive (M) bites into the
dark (D) figures, because it only allowed D-M and M-L flips. Here the moves are ranked by cost:

  (a) figure vs light: a D cell with an L 4-neighbour becomes L (erode), or an L cell with a D
      4-neighbour becomes D (dilate).                                            cost 1 per cell
  (b) mid band vs light: an M cell with an L 4-neighbour becomes L, or an L cell with an M
      4-neighbour becomes M.                                                     cost 1 per cell
  (c) figure/ground junction: a D<->M flip only where the cell already touches both D and M
      (4-neighbours).                                                            cost 2 per cell

Hard rules (checked after each move, for the whole image):
  - every changed cell has at least 2 orthogonal neighbours of its new tier (no isolated cells,
    no 1-cell protrusions, no diagonal-only contacts);
  - no changed cell becomes M with all four orthogonal neighbours D (no olive islands in figures),
    and none with three or more D neighbours (no olive bites);
  - no cell becomes newly "rare" (at most one orthogonal neighbour of its own tier, interior cells);
  - changed cells lie within one cell (8-neighbourhood) of the original boundary, frame excluded;
  - at most MAX_FLIPS changed cells per image.
Tier totals are kept per image: every move is a reverse pair (X->Y with Y->X), single or domino.

Objective (lower is better):
  sum over merged classes of (max over images - min over images)          [class balance, as v5]
  + LAM_FLIP * (move cost, all images; cost of a changed cell from its original tier, see above)
  + TARGET_W * sum over images of max(0, surplus - TARGET_SURPLUS)        [target surplus <= 10]

After annealing the script writes, with the -v5eq2 suffix:
  quantized-v5eq2/*.npy, tiers-v5eq2.txt      tier maps (npy as quantized-v2; text with changed cells)
  quantized-codes-v5eq2.txt, boundary-budgets-v5eq2.txt, quantize-report-v5eq2.txt
                                              quantize_v5.main() run on the revised tiers
  roles-v5eq2.txt, roles-spec-v5eq2.json      make_roles_v5.main() run on the revised tiers
  scenes-v5eq2.txt                            build_scenes_v5.main() run on the roles
  scene-metrics-v5eq2.txt                     metapuzzle scene-metrics
  run-full-v5eq2/, run-ink-v5eq2/             metapuzzle prototype with classes-v4.json / classes-ink.json
The v5 scripts are used unchanged: their HERE and the quantizer's equalize_tiers are redirected to a
staging folder (removed at the end), so no existing file is modified.

Usage: equalize_budgets_v5b.py [--iters N] [--seeds 0,1,2] [--lam X] [--no-pipeline] [--no-render]
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
SUFFIX = "v5eq2"
STAGE = HERE / "_stage-v5eq2"  # scratch folder for the unchanged v5 scripts; removed at the end
ORTH = list(q.OFFSETS)  # (dx, dy): N, E, S, W
DIAGS = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
NEIGH8 = ORTH + DIAGS
D, M, L = 0, 1, 2  # tier indices, as quantize.tier_of (0 dark, 1 mid, 2 light)
MOVE_COST = {frozenset((D, L)): 1, frozenset((M, L)): 1, frozenset((D, M)): 2}
MOVE_NAME = {frozenset((D, L)): "a", frozenset((M, L)): "b", frozenset((D, M)): "c"}
MAX_FLIPS = 30
LAM_FLIP = 2.0  # chosen by sweep (0.1 to 3.0): largest weight that keeps every image at surplus <= 10
TARGET_SURPLUS = 10
TARGET_W = 5.0
DOMINO_PROB = 0.4
LOCAL_RADIUS = 4
LOCAL_PROB = 0.7
T_HI, T_LO = 0.6, 0.01


def shifted(T: np.ndarray, dx: int, dy: int, fill: int = -1) -> np.ndarray:
    """Value of the neighbour at offset (dx, dy) for every cell; fill outside the board."""
    P = np.full((ROWS + 2, COLS + 2), fill, dtype=T.dtype)
    P[1:-1, 1:-1] = T
    return P[1 + dy:1 + dy + ROWS, 1 + dx:1 + dx + COLS]


def orth_nb(r: int, c: int):
    for dx, dy in ORTH:
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


def dilate(m: np.ndarray) -> np.ndarray:
    P = np.zeros((ROWS + 2, COLS + 2), bool)
    P[1:-1, 1:-1] = m
    out = m.copy()
    for dx, dy in NEIGH8:
        out |= P[1 + dy:1 + dy + ROWS, 1 + dx:1 + dx + COLS]
    return out


def has4(T: np.ndarray, value: int) -> np.ndarray:
    m = np.zeros((ROWS, COLS), bool)
    for dx, dy in ORTH:
        m |= shifted(T, dx, dy) == value
    return m


def same4(T: np.ndarray) -> np.ndarray:
    return sum((shifted(T, dx, dy) == T).astype(int) for dx, dy in ORTH)


def rare_mask(T: np.ndarray) -> np.ndarray:
    """Interior cells with at most one orthogonal neighbour of their own tier."""
    return (same4(T) <= 1) & INNER


def surplus(hists: list) -> tuple[list, int]:
    """Budget surplus per image (per-class max minus own, summed) and the sum of (max - min) per class."""
    classes = set().union(*hists)
    mx = {c: max(h[c] for h in hists) for c in classes}
    per_image = [sum(mx[c] - h[c] for c in classes) for h in hists]
    spread = sum(mx[c] - min(h[c] for h in hists) for c in classes)
    return per_image, spread


def cost_of(t: np.ndarray, t0: np.ndarray) -> int:
    """Move cost of an image: each changed cell costs by its (original, new) tier pair."""
    return sum(MOVE_COST[frozenset((int(t0[r, c]), int(t[r, c])))] for r, c in zip(*np.nonzero(t != t0)))


def type_counts(t: np.ndarray, t0: np.ndarray) -> dict:
    out = {"a": 0, "b": 0, "c": 0}
    for r, c in zip(*np.nonzero(t != t0)):
        out[MOVE_NAME[frozenset((int(t0[r, c]), int(t[r, c])))]] += 1
    return out


def score(hists: list, costs: list) -> float:
    per, spread = surplus(hists)
    over = sum(max(0, p - TARGET_SURPLUS) for p in per)
    return spread + LAM_FLIP * sum(costs) + TARGET_W * over


def flip_masks(t: np.ndarray, allow: np.ndarray) -> dict:
    """Cells that may flip (old, new) on the current state, under the move rules (a), (b), (c)."""
    hD, hM, hL = has4(t, D), has4(t, M), has4(t, L)
    return {
        (D, L): (t == D) & hL & allow,               # (a) erode the figure against light
        (L, D): (t == L) & hD & allow,               # (a) dilate the figure into light
        (M, L): (t == M) & hL & allow,               # (b) erode the mid band against light
        (L, M): (t == L) & hM & allow,               # (b) dilate the mid band into light
        (D, M): (t == D) & hD & hM & allow,          # (c) junction: cell touches both D and M
        (M, D): (t == M) & hD & hM & allow,          # (c) junction
    }


def cells_of(m: np.ndarray) -> list:
    return [(int(r), int(c)) for r, c in zip(*np.nonzero(m))]


def pick_local(rnd: random.Random, items: list, centre, key=lambda x: x):
    near = [p for p in items if max(abs(key(p)[0] - centre[0]), abs(key(p)[1] - centre[1])) <= LOCAL_RADIUS]
    pool = near if (near and rnd.random() < LOCAL_PROB) else items
    return pool[rnd.randrange(len(pool))]


def propose(rnd: random.Random, T: list, allow: list):
    """Random reverse-pair move: (image index, [(row, col, new tier), ...]) or None."""
    k = rnd.randrange(3)
    t = T[k]
    masks = flip_masks(t, allow[k])
    kinds = [key for key in masks if masks[key].any() and masks[(key[1], key[0])].any()]
    if not kinds:
        return None
    old, new = kinds[rnd.randrange(len(kinds))]
    m_out, m_back = masks[(old, new)], masks[(new, old)]
    out_cells = cells_of(m_out)
    a = out_cells[rnd.randrange(len(out_cells))]
    if rnd.random() >= DOMINO_PROB:  # single pair
        back = cells_of(m_back)
        b = pick_local(rnd, back, a)
        return k, [(a[0], a[1], new), (b[0], b[1], old)]
    # domino: a and an orthogonal neighbour a2 (both old -> new), and a partner domino (new -> old)
    nb = [p for p in orth_nb(*a) if m_out[p]]
    if not nb:
        return None
    a2 = nb[rnd.randrange(len(nb))]
    pairs = [(b, b2) for b in cells_of(m_back) for b2 in orth_nb(*b) if m_back[b2]]
    if not pairs:
        return None
    (br, bc), (b2r, b2c) = pick_local(rnd, pairs, a, key=lambda p: p[0])
    return k, [(a[0], a[1], new), (a2[0], a2[1], new), (br, bc, old), (b2r, b2c, old)]


def bite_mask(T: np.ndarray) -> np.ndarray:
    """Interior M cells with three or more D orthogonal neighbours (olive bites into a figure)."""
    nD = sum((shifted(T, dx, dy) == D).astype(int) for dx, dy in ORTH)
    return (T == M) & (nD >= 3) & INNER


def legal(t: np.ndarray, changes: list, rare_before: np.ndarray, bite_before: np.ndarray):
    """Hard rules on the image after the move. Returns (ok, rare mask after, bite mask after)."""
    for r, c, new in changes:
        nb = [int(t[rr, cc]) for rr, cc in orth_nb(r, c)]
        if sum(1 for v in nb if v == new) < 2:  # isolated cell, 1-cell protrusion or diagonal-only contact
            return False, None, None
        if new == M and all(v == D for v in nb):  # olive island inside a figure
            return False, None, None
    rare_after = rare_mask(t)
    if (rare_after & ~rare_before).any():  # a cell became rare: the move created a protrusion
        return False, None, None
    bite_after = bite_mask(t)
    if (bite_after & ~bite_before).any():  # a new olive bite (M cell with three D sides), anywhere
        return False, None, None
    return True, rare_after, bite_after


def anneal(seed: int, iters: int, T0: list, tone: list, allow: list, log) -> tuple:
    rnd = random.Random(seed)
    T = [t.copy() for t in T0]
    hists = [v5.analyse(T[k], tone[k])["hist"] for k in range(3)]
    rares = [rare_mask(T[k]) for k in range(3)]
    bites = [bite_mask(T[k]) for k in range(3)]
    costs = [cost_of(T[k], T0[k]) for k in range(3)]
    cur = score(hists, costs)
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
        nflip = int(np.count_nonzero(t != T0[k]))
        ok, rare_after, bite_after = (False, None, None)
        if nflip <= MAX_FLIPS:
            ok, rare_after, bite_after = legal(t, changes, rares[k], bites[k])
        if not ok:
            for r, c, old in saved:
                t[r, c] = old
            continue
        hs, cs = hists.copy(), costs.copy()
        hs[k] = v5.analyse(t, tone[k])["hist"]
        cs[k] = cost_of(t, T0[k])
        new_score = score(hs, cs)
        if new_score <= cur or rnd.random() < math.exp(-(new_score - cur) / temp):
            hists, costs, cur = hs, cs, new_score
            rares[k] = rare_after
            bites[k] = bite_after
            accepted += 1
            if cur < best[0]:
                best = (cur, [x.copy() for x in T])
        else:
            for r, c, old in saved:
                t[r, c] = old
        if (it + 1) % max(1, iters // 5) == 0:
            per, spread = surplus(hists)
            log(f"    seed {seed} it {it + 1:6d} T {temp:.3f} accepted {accepted:6d} "
                f"surplus {per} spread {spread} cost {costs} score {cur:.2f} best {best[0]:.2f}")
    return best


def shape(t: np.ndarray) -> dict:
    """Figure-shape counts: olive bites (M cells with >= 3 D neighbours), isolated or 1-cell
    protrusions (rare cells), and D cells lost to light (D cells with >= 3 L neighbours)."""
    bites = sum(int(((t[r, c] == M) and sum(1 for rr, cc in orth_nb(r, c) if t[rr, cc] == D) >= 3))
                for r in range(ROWS) for c in range(COLS) if INNER[r, c])
    lost = sum(int(((t[r, c] == D) and sum(1 for rr, cc in orth_nb(r, c) if t[rr, cc] == L) >= 3))
               for r in range(ROWS) for c in range(COLS) if INNER[r, c])
    return {"olive_bites": bites, "D_eroded": lost, "rare": int(rare_mask(t).sum())}


def report_state(label: str, T: list, T0: list, tone: list, rare0: list, target) -> dict:
    hists = [v5.analyse(T[k], tone[k])["hist"] for k in range(3)]
    per, spread = surplus(hists)
    rares = [int(rare_mask(T[k]).sum()) for k in range(3)]
    totals = [np.bincount(T[k].ravel(), minlength=3).tolist() for k in range(3)]
    types = [type_counts(T[k], T0[k]) for k in range(3)]
    costs = [cost_of(T[k], T0[k]) for k in range(3)]
    print(label)
    print(f"   surplus per image (cat / sailboat / tree): {per[0]} / {per[1]} / {per[2]}   total {sum(per)}")
    print(f"   sum over classes of (max - min): {spread}")
    print(f"   cells changed per image: {[sum(x.values()) for x in types]}   "
          f"by type a/b/c: {[f'{x['a']}/{x['b']}/{x['c']}' for x in types]}   move cost {costs}")
    print(f"   tier totals D/M/L per image: {totals}   (target {list(target)})")
    print(f"   rare interior cells per image: {rares} (original {rare0})")
    shp = [shape(T[k]) for k in range(3)]
    print(f"   shape per image (olive bites / D lost to light / rare): "
          f"{[f'{s['olive_bites']}/{s['D_eroded']}/{s['rare']}' for s in shp]}")
    return {"per": per, "spread": spread, "types": types, "costs": costs, "shape": shp}


def main() -> None:
    global LAM_FLIP
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=30000)
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--no-pipeline", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--lam", type=float, default=LAM_FLIP, help="weight per unit of move cost")
    args = ap.parse_args()
    LAM_FLIP = args.lam
    t_start = time.time()

    v2 = {n: np.load(q.TARGETS / f"{n}-v2.npy") for n in NAMES}
    orig_equalize = q.equalize_tiers
    tiers, _, target, _ = orig_equalize(v2)
    T0 = [tiers[n].astype(np.int64) for n in NAMES]
    tone = [v2[n] for n in NAMES]

    # Only cells within one cell (8-neighbourhood) of the original boundary may change; frame never.
    allow = [dilate(differ_mask(t)) & INNER for t in T0]
    rare0 = [int(rare_mask(t).sum()) for t in T0]
    print("1. original tiers (equalized): D/M/L per image", [np.bincount(t.ravel(), minlength=3).tolist() for t in T0])
    print(f"   cells allowed to change per image: {[int(a.sum()) for a in allow]}")
    base = report_state("2. before annealing", T0, T0, tone, rare0, target)

    def log(msg: str) -> None:
        print(msg, flush=True)

    print("3. simulated annealing (one run per seed; the best final score is kept)")
    results = []
    for seed in [int(s) for s in args.seeds.split(",")]:
        t0 = time.time()
        sc, Tb = anneal(seed, args.iters, T0, tone, allow, log)
        results.append((sc, seed, Tb))
        print(f"   seed {seed}: best score {sc:.2f} ({time.time() - t0:.0f} s)", flush=True)
    sc, seed, T = min(results, key=lambda x: x[0])
    print(f"   chosen seed {seed}, score {sc:.2f}")

    # Checks: totals kept, changes within the band, frame untouched, surplus target met.
    for k in range(3):
        assert (np.bincount(T[k].ravel(), minlength=3) == target).all(), "tier totals changed"
        assert not (T[k] != T0[k])[~allow[k] & (T[k] != T0[k])].any(), "change outside the band"
        assert not (T[k] != T0[k])[FRAME].any(), "frame cell changed"
    after = report_state("4. after annealing", T, T0, tone, rare0, target)
    if max(after["per"]) > TARGET_SURPLUS:
        print(f"   WARNING: surplus above the target {TARGET_SURPLUS} in at least one image")
    print("   changed cells (row, col) old -> new:")
    for k, n in enumerate(NAMES):
        ch = [(int(r), int(c), int(T0[k][r, c]), int(T[k][r, c])) for r, c in zip(*np.nonzero(T[k] != T0[k]))]
        print(f"   {n:9s} " + ", ".join(f"({r},{c}) {q.TIER_SYM[a]}->{q.TIER_SYM[b]}" for r, c, a, b in ch))

    # Write the tier maps and the -v5eq2 outputs.
    out_tiers = HERE / f"quantized-{SUFFIX}"
    out_tiers.mkdir(exist_ok=True)
    text = [f"# Equalized tier maps ({SUFFIX}), experiment 005. D / M / L per cell; A = cat, B = sailboat, C = tree.",
            "# Changed cells (vs quantized-v2): (row, col) old -> new. Move costs: a 1 (D-L), b 1 (M-L), c 2 (D-M).",
            ""]
    for k, n in enumerate(NAMES):
        np.save(out_tiers / f"{n}.npy", T[k].astype(np.int64))
        text.append(f"# {n}")
        text += [" ".join(q.TIER_SYM[x] for x in row) for row in T[k]]
        ch = [f"({int(r)},{int(c)}) {q.TIER_SYM[int(T0[k][r, c])]}->{q.TIER_SYM[int(T[k][r, c])]}"
              for r, c in zip(*np.nonzero(T[k] != T0[k]))]
        tc = after["types"][k]
        text.append(f"changed ({tc['a']} a, {tc['b']} b, {tc['c']} c): " + (", ".join(ch) or "-"))
        text.append("")
    (HERE / f"tiers-{SUFFIX}.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(f"wrote {out_tiers} and tiers-{SUFFIX}.txt")

    if args.no_pipeline:
        return

    # Rest of the v5 pipeline on the revised tiers, through the unchanged scripts.
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
    print("quantize_v5.main on revised tiers: report, codes and budgets written")

    mr.HERE = STAGE
    try:
        with contextlib.redirect_stdout(io.StringIO()) as mb:
            mr.main()
    finally:
        mr.HERE = HERE
    shutil.copy(STAGE / "roles-v5.txt", HERE / f"roles-{SUFFIX}.txt")
    shutil.copy(STAGE / "roles-spec-v5.json", HERE / f"roles-spec-{SUFFIX}.json")
    print("make_roles_v5 on revised tiers:")
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
    print("build_scenes_v5 on revised roles: " + bb.getvalue().strip().splitlines()[-1])

    metrics = subprocess.run(["metapuzzle", "scene-metrics", str(HERE / f"scenes-{SUFFIX}.txt")],
                             capture_output=True, text=True)
    (HERE / f"scene-metrics-{SUFFIX}.txt").write_text(metrics.stdout + metrics.stderr, encoding="utf-8")
    print(f"scene-metrics exit status {metrics.returncode} (3 = a scene gate fails)")
    shutil.rmtree(STAGE)

    if args.no_render:
        return
    for classes, out in [("classes-v4.json", f"run-full-{SUFFIX}"), ("classes-ink.json", f"run-ink-{SUFFIX}")]:
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
