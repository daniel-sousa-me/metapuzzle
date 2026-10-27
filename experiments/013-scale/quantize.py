"""Tier quantization with transition codes for experiment 005 (hybrid tones).

Steps (see README.md for the results):

1. Tiers by fixed thresholds: D (tone < 0.35), M (0.35 <= tone <= 0.65), L (tone > 0.65).
2. Exact tier counts: target per tier = largest-remainder rounding of the mean of the three
   images' counts (sum 500). Cells are moved only across a threshold, and only the cells whose
   tone is closest to that threshold: D->M takes the D cells with the highest tone, M->D the M
   cells with the lowest tone (both next to 0.35); M->L takes the M cells with the highest tone,
   L->M the L cells with the lowest tone (both next to 0.65). D/L are fixed first, so M absorbs
   the rest and ends at its target.
2b. Frame (board edge and corner cells). The strict border rule compares the class histograms of
   the edge pool and of the corner pool across the three maps, so their tier composition must be
   common. Each pool gets the rounded mean composition of the three images; cells cross one tier
   threshold at a time, the one closest to it first. The interior takes the rest, so the global
   tier counts stay exact.
3. Codes: a plain cell (no 4-neighbour in another tier) keeps its tier code D, M or L. Frame cells
   are always plain: a scene cannot carry an orientation suffix on the frame, so a frame transition
   is coded as its tier and the cut is counted. A transition cell is coded <own><neighbour>@<side>, side = direction of the neighbour with the
   different tier (T = N, R = E, B = S, L = W). If two or more sides differ, the side with the
   largest tone difference wins (ties: N, E, S, W order); the count of such cells is reported.
4. Equalization of the transition codes. The histogram is taken on rotation-equivalent classes
   (D, M, L, DM, DL, MD, ML, LD, LM: the side is dropped, because a class spec rotates pieces).
   Target: largest-remainder rounding of the mean class histogram per own-tier group.
   (i) Side swap: a transition cell with two or more different-tier sides may move to another
       of them if that side's tone difference is at least 0.1 and the swap brings the class
       histogram closer to the target (greedy).
   Plain cells cannot be swapped to a transition code: a plain cell has no neighbour in another
   tier, so it has no side to take. Changing a plain cell would change its tier, which
   step 2 forbids.
   (ii) Rotation: the scene file writes each cell as <class>@<rotation>, clockwise, with the
   canonical class (mid neighbour at T) at 0: T 0, R 90, B 180, L 270. The directional
   histogram (class + side) is reported for information; it is not forced equal.
5. Output: scenes.txt (3 maps, 20 cols x 25 rows), quantized/*.npy (tier arrays),
   quantized-preview.png.

Optional argument: the output suffix (for example "-v2"). It selects targets/<name><suffix>.npy as
input and writes scenes<suffix>.txt, quantized<suffix>/, quantized-preview<suffix>.png. Without it,
the files are the v1 names above.
"""
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from gridcfg import COLS, ROWS, WORK  # grid size: GRID env var

HERE = Path(__file__).resolve().parent
TARGETS = WORK / "targets"
NAMES = ["cat", "sailboat", "tree"]
CELLS = ROWS * COLS
DARK_MAX, LIGHT_MIN = 0.35, 0.65
FRAME = np.zeros((ROWS, COLS), bool)
FRAME[0, :] = FRAME[-1, :] = FRAME[:, 0] = FRAME[:, -1] = True
CORNER = np.zeros((ROWS, COLS), bool)
CORNER[0, 0] = CORNER[0, -1] = CORNER[-1, 0] = CORNER[-1, -1] = True
EDGE = FRAME & ~CORNER
INNER = ~FRAME
TIER_SYM = "DML"
CLASSES = ["D", "M", "L", "DM", "DL", "MD", "ML", "LD", "LM"]
OWN_GROUPS = {0: [0, 3, 4], 1: [1, 5, 6], 2: [2, 7, 8]}  # class indices by own tier
OFFSETS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # N, E, S, W as (dx, dy)
SIDE_NAMES = ["T", "R", "B", "L"]
MIN_SWAP_DIFF = 0.1
UP = 16


def tier_of(tone: np.ndarray) -> np.ndarray:
    return np.where(tone < DARK_MAX, 0, np.where(tone <= LIGHT_MIN, 1, 2)).astype(int)


def largest_remainder(frac: np.ndarray, total: int) -> np.ndarray:
    raw = np.asarray(frac, float) * total
    out = np.floor(raw).astype(int)
    for k in np.argsort(-(raw - out), kind="stable")[: total - out.sum()]:
        out[k] += 1
    return out


def _move(tiers: np.ndarray, tone: np.ndarray, src: int, dst: int, n: int, highest: bool) -> None:
    """Move n cells from tier src to dst, choosing those with tone closest to the shared threshold."""
    flat_t, flat_tone = tiers.reshape(-1), tone.reshape(-1)
    cand = np.flatnonzero(flat_t == src)
    order = cand[np.argsort(-flat_tone[cand] if highest else flat_tone[cand], kind="stable")]
    flat_t[order[:n]] = dst


def _hist(tiers: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return np.array([int(((tiers == k) & mask).sum()) for k in range(3)])


def _set_counts(tiers: np.ndarray, tone: np.ndarray, mask: np.ndarray, want: np.ndarray) -> list:
    """Move cells inside mask one tier step at a time until the mask holds the wanted counts.
    Each step takes the cell closest to the threshold it crosses. Returns (r, c, from, to) per move."""
    assert _hist(tiers, mask).sum() == want.sum(), "mask size and target differ"
    flat_t, flat_tone, flat_m = tiers.reshape(-1), tone.reshape(-1), mask.reshape(-1)
    moves = []
    while True:
        diff = _hist(tiers, mask) - want
        if not diff.any():
            return moves
        src, dst = int(np.argmax(diff)), int(np.argmin(diff))
        step = src + (1 if dst > src else -1)
        cand = np.flatnonzero(flat_m & (flat_t == src))
        order = cand[np.argsort(-flat_tone[cand] if step > src else flat_tone[cand], kind="stable")]
        p = int(order[0])
        flat_t[p] = step
        moves.append((p // COLS, p % COLS, src, step))


def equalize_tiers(tones: dict, labels: dict) -> tuple[dict, dict, np.ndarray, dict]:
    tiers = {n: labels[n].astype(int).copy() for n in NAMES}
    counts = np.array([np.bincount(tiers[n].ravel(), minlength=3) for n in NAMES])
    target = largest_remainder(counts.mean(axis=0) / CELLS, CELLS)
    moves = {}
    for n in NAMES:
        t, tone = tiers[n], tones[n]
        before = np.bincount(t.ravel(), minlength=3)
        # Dark / mid boundary (0.35): fix D first.
        d = before[0] - target[0]
        if d > 0:
            _move(t, tone, 0, 1, d, highest=True)
        elif d < 0:
            _move(t, tone, 1, 0, -d, highest=False)
        # Mid / light boundary (0.65): fix L; M then equals its target.
        cur = np.bincount(t.ravel(), minlength=3)
        l = cur[2] - target[2]
        if l > 0:
            _move(t, tone, 2, 1, l, highest=False)
        elif l < 0:
            _move(t, tone, 1, 2, -l, highest=True)
        after = np.bincount(t.ravel(), minlength=3)
        assert (after == target).all(), (n, after, target)
    # Frame and corner composition: common target (rounded mean), interior takes the rest.
    edge_t = np.array([_hist(tiers[n], EDGE) for n in NAMES])
    corner_t = np.array([_hist(tiers[n], CORNER) for n in NAMES])
    edge_target = largest_remainder(edge_t.mean(axis=0) / EDGE.sum(), int(EDGE.sum()))
    corner_target = largest_remainder(corner_t.mean(axis=0) / CORNER.sum(), int(CORNER.sum()))
    inner_target = target - edge_target - corner_target
    assert (inner_target >= 0).all(), inner_target
    shifts = {}
    for n in NAMES:
        t, tone = tiers[n], tones[n]
        shifts[n] = (_set_counts(t, tone, CORNER, corner_target)
                     + _set_counts(t, tone, EDGE, edge_target)
                     + _set_counts(t, tone, INNER, inner_target))
        assert (_hist(t, np.ones_like(INNER)) == target).all(), n
        moves[n] = int((t != labels[n]).sum())
    return tiers, moves, target, shifts


def options(tiers: np.ndarray, tone: np.ndarray, r: int, c: int) -> list:
    """Different-tier sides of cell (r, c): (side index, neighbour tier, tone difference)."""
    out = []
    for side, (dx, dy) in enumerate(OFFSETS):
        rr, cc = r + dy, c + dx
        if 0 <= rr < ROWS and 0 <= cc < COLS and tiers[rr, cc] != tiers[r, c]:
            out.append((side, int(tiers[rr, cc]), round(abs(float(tone[r, c]) - float(tone[rr, cc])), 6)))
    return out


def build_options(tiers, tone) -> list:
    """Frame cells get no options: they are always plain."""
    return [[[] if FRAME[r, c] else options(tiers, tone, r, c) for c in range(COLS)] for r in range(ROWS)]


def default_choice(opts) -> list:
    """Largest tone difference wins; ties go to the earlier side (N, E, S, W)."""
    return [[max(o, key=lambda x: (x[2], -x[0]))[0] if o else None for o in row] for row in opts]


def cell_code(tier: int, opts, side) -> tuple[str, str | None]:
    """(class label, side name) for one cell; side name is None for plain cells."""
    if not opts:
        return TIER_SYM[tier], None
    nb = [o for o in opts if o[0] == side][0][1]
    return TIER_SYM[tier] + TIER_SYM[nb], SIDE_NAMES[side]


def class_hist(tiers, opts, choice) -> np.ndarray:
    h = np.zeros(len(CLASSES), int)
    for r in range(ROWS):
        for c in range(COLS):
            label, _ = cell_code(tiers[r, c], opts[r][c], choice[r][c])
            h[CLASSES.index(label)] += 1
    return h


def full_hist(tiers, opts, choice) -> Counter:
    out = Counter()
    for r in range(ROWS):
        for c in range(COLS):
            label, side = cell_code(tiers[r, c], opts[r][c], choice[r][c])
            out[label if side is None else f"{label}@{side}"] += 1
    return out


def class_target(hists: list) -> np.ndarray:
    """Mean class histogram, rounded per own-tier group so that each group keeps its exact total."""
    mean = np.mean(hists, axis=0)
    out = np.zeros(len(CLASSES), int)
    for own, idx in OWN_GROUPS.items():
        totals = {int(h[idx].sum()) for h in hists}
        assert len(totals) == 1, (own, totals)
        out[idx] = largest_remainder(mean[idx] / mean[idx].sum(), totals.pop())
    return out


def equalize_sides(tiers, opts, choice, target) -> tuple[list, int]:
    """Greedy side swaps (rule i): keep changing the side of a multi-sided cell while the class
    histogram gets closer to the target. Only sides with tone difference >= MIN_SWAP_DIFF count."""
    choice = [row[:] for row in choice]
    cost = lambda ch: int(np.abs(class_hist(tiers, opts, ch) - target).sum())
    cur, swaps = cost(choice), 0
    while cur > 0:
        best = None
        for r in range(ROWS):
            for c in range(COLS):
                if len(opts[r][c]) < 2:
                    continue
                for side, _, diff in opts[r][c]:
                    if side == choice[r][c] or diff < MIN_SWAP_DIFF:
                        continue
                    old = choice[r][c]
                    choice[r][c] = side
                    val = cost(choice)
                    choice[r][c] = old
                    if val < cur and (best is None or val < best[0]):
                        best = (val, r, c, side)
        if best is None:
            break
        cur, r, c, side = best
        choice[r][c] = side
        swaps += 1
    return choice, swaps


def token(tier: int, opts, side) -> str:
    label, sname = cell_code(tier, opts, side)
    if sname is None:
        return label
    rot = 90 * SIDE_NAMES.index(sname)  # canonical class: mid neighbour (or other) at T, clockwise
    return label if rot == 0 else f"{label}@{rot}"


def write_scenes(maps: dict, path: Path, header: str) -> None:
    lines = [header, ""]
    for n in NAMES:
        lines += [" ".join(row) for row in maps[n]]
        lines.append("")
    path.write_text("\n".join(lines))


def preview(tones: dict, tiers: dict, choices: dict, opts: dict, path: Path) -> None:
    """Top: targets as gray tones. Bottom: tier colours; transition cells carry a stripe on their
    side in the neighbour's tier colour."""
    palette = {0: (28, 37, 54), 1: (138, 143, 152), 2: (242, 239, 230)}
    gap, label_h = 24, 26
    w, h = COLS * UP, ROWS * UP
    canvas = Image.new("RGB", (3 * w + 4 * gap, 2 * h + 3 * gap + 2 * label_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    for col, n in enumerate(NAMES):
        x = gap + col * (w + gap)
        draw.text((x, 4), f"{n} target (0 dark, 1 light)", fill=(0, 0, 0))
        t = Image.fromarray(np.round(tones[n] * 255).astype(np.uint8), "L").convert("RGB")
        canvas.paste(t.resize((w, h), Image.NEAREST), (x, label_h))
        y2 = label_h + h + gap + label_h
        draw.text((x, y2 - label_h + 4), f"{n} codes (dark navy, mid grey, light cream; stripe = neighbour side)", fill=(0, 0, 0))
        img = Image.new("RGB", (w, h), (255, 255, 255))
        cd = ImageDraw.Draw(img)
        for r in range(ROWS):
            for c in range(COLS):
                x0, y0 = c * UP, r * UP
                own = int(tiers[n][r, c])
                cd.rectangle([x0, y0, x0 + UP - 1, y0 + UP - 1], fill=palette[own])
                side = choices[n][r][c]
                if side is None:
                    continue
                nb = [o for o in opts[n][r][c] if o[0] == side][0][1]
                s = UP // 4
                box = {0: [x0, y0, x0 + UP - 1, y0 + s - 1], 1: [x0 + UP - s, y0, x0 + UP - 1, y0 + UP - 1],
                       2: [x0, y0 + UP - s, x0 + UP - 1, y0 + UP - 1], 3: [x0, y0, x0 + s - 1, y0 + UP - 1]}[side]
                cd.rectangle(box, fill=palette[nb])
        canvas.paste(img, (x, y2))
    canvas.save(path)


def main(suffix: str = "") -> None:
    tones = {n: np.load(TARGETS / f"{n}{suffix}.npy") for n in NAMES}
    labels = {n: np.load(TARGETS / f"{n}{suffix}-labels.npy") for n in NAMES}
    raw = {n: np.bincount(labels[n].ravel(), minlength=3) for n in NAMES}
    print("1. tier counts from the majority-vote tier labels (D / M / L):")
    for n in NAMES:
        print(f"   {n:9s} {raw[n][0]:3d} / {raw[n][1]:3d} / {raw[n][2]:3d}")

    tiers, moves, target, shifts = equalize_tiers(tones, labels)
    print(f"2. equalized tier target (D / M / L): {target[0]} / {target[1]} / {target[2]}")
    for n in NAMES:
        print(f"   {n:9s} cells moved across a threshold: {moves[n]}")
    print("2b. frame and corner shifts, cell (row,col) from -> to, closest to threshold first:")
    for n in NAMES:
        desc = ", ".join(f"({r},{c}) {TIER_SYM[a]}->{TIER_SYM[b]}" for r, c, a, b in shifts[n])
        print(f"   {n:9s} {len(shifts[n])} cells: {desc or '-'}")
    for n in NAMES:
        print(f"   {n:9s} frame D/M/L {_hist(tiers[n], FRAME).tolist()}  corner D/M/L {_hist(tiers[n], CORNER).tolist()}")
    frame_cuts = {n: sum(1 for r in range(ROWS) for c in range(COLS) if FRAME[r, c] and options(tiers[n], tones[n], r, c))
                  for n in NAMES}
    print("2c. frame boundaries on cuts (frame cells with a different-tier neighbour, now plain): "
          + ", ".join(f"{n} {frame_cuts[n]}" for n in NAMES))

    opts, choices, mixed, trans = {}, {}, {}, {}
    for n in NAMES:
        opts[n] = build_options(tiers[n], tones[n])
        choices[n] = default_choice(opts[n])
        trans[n] = sum(1 for row in opts[n] for o in row if o)
        mixed[n] = sum(1 for row in opts[n] for o in row if len(o) >= 2)
    print("3. transition cells (own tier differs from a neighbour) and cells with 2+ different sides:")
    for n in NAMES:
        print(f"   {n:9s} transitions {trans[n]:3d}  multi-sided {mixed[n]:3d}")

    before = {n: class_hist(tiers[n], opts[n], choices[n]) for n in NAMES}
    print("4. rotation-equivalent class histogram before equalization:")
    print("   class     " + "  ".join(f"{k:>5s}" for k in CLASSES))
    for n in NAMES:
        print(f"   {n:9s} " + "  ".join(f"{v:5d}" for v in before[n]))
    target_cls = class_target([before[n] for n in NAMES])
    print("   target    " + "  ".join(f"{v:5d}" for v in target_cls))
    l1 = lambda hs: sum(int(np.abs(hs[a] - hs[b]).sum()) for a, b in [("cat", "sailboat"), ("cat", "tree"), ("sailboat", "tree")])
    print(f"   pairwise L1 (cat-sailboat, cat-tree, sailboat-tree): "
          f"{int(np.abs(before['cat'] - before['sailboat']).sum())}, {int(np.abs(before['cat'] - before['tree']).sum())}, "
          f"{int(np.abs(before['sailboat'] - before['tree']).sum())}  (sum {l1(before)})")

    swaps = {}
    for n in NAMES:
        choices[n], swaps[n] = equalize_sides(tiers[n], opts[n], choices[n], target_cls)
    after = {n: class_hist(tiers[n], opts[n], choices[n]) for n in NAMES}
    print("5. equalization (rule i: side swaps with tone difference >= 0.1):")
    for n in NAMES:
        print(f"   {n:9s} side swaps {swaps[n]:2d}  histogram " + " ".join(f"{k}={v}" for k, v in zip(CLASSES, after[n])))
    print("   residual L1 to target per image: " + ", ".join(
        f"{n} {int(np.abs(after[n] - target_cls).sum())}" for n in NAMES))
    print(f"   pairwise L1 after: cat-sailboat {int(np.abs(after['cat'] - after['sailboat']).sum())}, "
          f"cat-tree {int(np.abs(after['cat'] - after['tree']).sum())}, "
          f"sailboat-tree {int(np.abs(after['sailboat'] - after['tree']).sum())}")

    print("6. directional histogram (class@side) after equalization, for information (rotation (ii) pools these):")
    dirs = {n: full_hist(tiers[n], opts[n], choices[n]) for n in NAMES}
    keys = sorted({k for n in NAMES for k in dirs[n]}, key=lambda k: (k.split("@")[0] not in CLASSES, k))
    for k in keys:
        print(f"   {k:8s}" + "".join(f"{dirs[n].get(k, 0):5d}" for n in NAMES))
    print("   (columns: cat, sailboat, tree)")
    print("   max directional difference: " + str(max(abs(dirs[a].get(k, 0) - dirs[b].get(k, 0))
                                                      for k in keys for a, b in [("cat", "sailboat"), ("cat", "tree"), ("sailboat", "tree")])))

    maps = {n: [[token(int(tiers[n][r, c]), opts[n][r][c], choices[n][r][c]) for c in range(COLS)] for r in range(ROWS)]
            for n in NAMES}
    (WORK / f"quantized{suffix}").mkdir(exist_ok=True)
    for n in NAMES:
        np.save(WORK / f"quantized{suffix}" / f"{n}.npy", tiers[n])
    write_scenes(maps, WORK / f"scenes{suffix}.txt",
                 f"# Hybrid tones, experiment 013 (005 method). Three {COLS}x{ROWS} class maps (cols x rows).\n"
                 "# A = cat, B = sailboat, C = tree. Classes: D dark, M mid, L light (plain);\n"
                 "# XY = own tier X with neighbour tier Y across the side set by @rotation (clockwise;\n"
                 "# canonical side = T, so @0 = neighbour at top, @90 right, @180 bottom, @270 left).")
    preview(tones, tiers, choices, opts, WORK / f"quantized-preview{suffix}.png")
    print(f"wrote scenes{suffix}.txt, quantized{suffix}/*.npy, quantized-preview{suffix}.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
