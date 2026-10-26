"""Procedural tone targets for experiment 005 (hybrid tones).

Each target is a (25 rows x 20 cols) float array in [0, 1]; 0 = dark, 1 = light.
Shapes are drawn on an 8x supersampled grid and box-downsampled (anti-aliasing).
Coordinates are in cell units: x runs 0..20 (columns), y runs 0..25 (rows).

Tiers (fixed thresholds, used by quantize.py as well):
    dark  tone < 0.35
    mid   0.35 <= tone <= 0.65
    light tone > 0.65

Matched tonal areas: each subject has free shape sizes (its dark mass and its mid band).
fit_all() searches the sizes of all three subjects in code and keeps the combination whose
dark-tier and mid-tier counts agree across images (spread at most 3 cells; the search finds 0).
Among those, it prefers the sizes closest to the targets DARK_T / MID_T and to the sketch.

Versions (optional argument, the output suffix):
    ""     v1, the geometry behind scenes.txt (small cat head and ears; light sail on light sky).
    "-v2"  subject fixes: the cat has a larger head and taller ears; the sail is a mid tone, so
           it shows against the light sky; the horizon search range allows a lower horizon to
           keep the mid count matched.
Outputs: targets/<name><suffix>.npy and .png.
"""
import sys
from functools import partial
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "targets"
ROWS, COLS, SS = 25, 20, 8
UP = 16  # preview upscale (nearest)
DARK_MAX, LIGHT_MIN = 0.35, 0.65  # tier thresholds
DARK_T, MID_T = 76, 120  # target tier counts (cells per image)
SUFFIXES = ("", "-v2")

# Flat tone levels. Dark and light mix into mid along anti-aliased edges.
DARK, MID = 0.10, 0.50
LIGHT, LIGHT_SAIL = 0.90, 0.97


def sample_grid():
    ys = (np.arange(ROWS * SS) + 0.5) / SS
    xs = (np.arange(COLS * SS) + 0.5) / SS
    return np.meshgrid(xs, ys)  # X, Y: shape (ROWS*SS, COLS*SS)


def ellipse(X, Y, cx, cy, rx, ry):
    return ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1.0


def disc(X, Y, cx, cy, r):
    return (X - cx) ** 2 + (Y - cy) ** 2 <= r * r


def rect(X, Y, x0, x1, y0, y1):
    return (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1)


def polygon(X, Y, pts):
    """Even-odd point-in-polygon test, vectorized over the sample grid."""
    inside = np.zeros(X.shape, bool)
    n = len(pts)
    for i in range(n):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
        if y1 == y2:
            continue
        crosses = (y1 > Y) != (y2 > Y)
        xint = x1 + (Y - y1) * (x2 - x1) / (y2 - y1)
        inside ^= crosses & (X < xint)
    return inside


def stroke(X, Y, pts, r):
    """Thick polyline (round caps): union of capsules along consecutive points."""
    mask = np.zeros(X.shape, bool)
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        dx, dy = x2 - x1, y2 - y1
        t = np.clip(((X - x1) * dx + (Y - y1) * dy) / (dx * dx + dy * dy), 0.0, 1.0)
        d2 = (X - (x1 + t * dx)) ** 2 + (Y - (y1 + t * dy)) ** 2
        mask |= d2 <= r * r
    return mask


def paint(ground, layers):
    """layers: list of (mask, tone), painted in order over the ground tone."""
    img = np.full((ROWS * SS, COLS * SS), ground, dtype=float)
    for mask, tone in layers:
        img[mask] = tone
    return img


def downsample(img):
    return img.reshape(ROWS, SS, COLS, SS).mean(axis=(1, 3))


HEAD_BIG = 3.4  # v2 head radius in cells (v1: 2.5 times the body scale)

# Ear corners relative to the head centre, in head radii: (base, apex, base) for each ear.
EARS = {
    False: ([(-1.0, -0.4), (-0.8, -1.9), (-0.1, -0.9)], [(0.1, -0.9), (0.6, -1.9), (0.95, -0.4)]),
    True: ([(-1.1, -0.4), (-0.9, -2.6), (-0.05, -0.9)], [(-0.05, -0.9), (0.95, -0.5), (0.6, -2.5)]),
}


def cat(s=1.0, floor_top=20.0, big=False):
    """Cat sitting in profile, facing left. s scales the dark mass; floor_top sets the mid floor.
    big=True (v2): head radius HEAD_BIG (fixed, not scaled by s; was 2.5 s) set higher on the body,
    and taller ears."""
    X, Y = sample_grid()
    rx, ry = 2.9 * s, 5.2 * s
    cx, cy = 9.5, floor_top - ry + 0.8  # body base sits just into the floor
    hr = HEAD_BIG if big else 2.5 * s
    hx, hy = cx - 0.8 * s, cy - ry + (0.3 if big else 0.7) * hr  # head on top of the body, a little to the left
    left, right = EARS[big]
    ear_l = [(hx + dx * hr, hy + dy * hr) for dx, dy in left]
    ear_r = [(hx + dx * hr, hy + dy * hr) for dx, dy in right]
    tail = [(cx + 0.5 * rx, floor_top - 0.6 * s), (cx + rx + 2.5 * s, floor_top - 0.6 * s),
            (cx + rx + 2.8 * s, floor_top - 4.5 * s), (cx + rx + 1.2 * s, floor_top - 6.0 * s)]
    layers = [
        (rect(X, Y, 0, COLS, floor_top, ROWS), MID),             # floor band (mid)
        (ellipse(X, Y, cx, cy, rx, ry), DARK),                   # body
        (disc(X, Y, hx, hy, hr), DARK),                          # head
        (polygon(X, Y, ear_l), DARK),                            # left ear
        (polygon(X, Y, ear_r), DARK),                            # right ear
        (stroke(X, Y, tail, 0.75 * s), DARK),                    # curled tail
    ]
    return downsample(paint(LIGHT, layers))


def sailboat(h=18.0, hw=8.5, hh=2.6, mw=1.0, mid_sail=False):
    """Sailboat: light sky, mid sea below horizon h, dark hull (half-width hw, height hh), sail.
    mid_sail=True (v2): the sail is a mid tone, so it stands out against the light sky."""
    X, Y = sample_grid()
    ht = h - 1.0  # hull top
    hull = [(10 - hw, ht), (10 + hw, ht), (10 + hw - 1.6, ht + hh), (10 - hw + 1.6, ht + hh)]
    sail = [(10.7, 4.0), (10.7, ht - 0.6), (16.8, ht - 0.6)]
    img = paint(LIGHT, [
        (rect(X, Y, 0, COLS, h, ROWS), MID),          # sea (lower part)
        (polygon(X, Y, hull), DARK),                  # hull
        (rect(X, Y, 10 - mw / 2, 10 + mw / 2, 3.5, ht), DARK),  # mast
        (polygon(X, Y, sail), MID if mid_sail else LIGHT_SAIL),  # sail
    ])
    return downsample(img)


def tree(r=4.0, g=19.0, tw=2.0):
    """Tree: dark round canopy (radius r) and trunk (width tw), mid ground band from row g, light sky."""
    X, Y = sample_grid()
    cy = 9.0
    img = paint(LIGHT, [
        (rect(X, Y, 0, COLS, g, ROWS), MID),          # ground band
        (rect(X, Y, 10 - tw / 2, 10 + tw / 2, cy, ROWS), DARK),  # trunk, standing in the ground
        (disc(X, Y, 10.0, cy, r), DARK),              # canopy
    ])
    return downsample(img)


def search_space(suffix: str) -> dict:
    """Shape-size search space per subject for one version: (builder, parameter grid, defaults)."""
    if suffix not in SUFFIXES:
        raise SystemExit(f"unknown suffix {suffix!r}; use one of {SUFFIXES}")
    v2 = suffix == "-v2"
    horizon = np.arange(16.5, 20.51, 0.1) if v2 else np.arange(16.5, 18.81, 0.1)
    return {
        "cat": (partial(cat, big=v2), {"s": np.arange(0.70, 1.41, 0.02), "floor_top": np.arange(17.0, 21.01, 0.1)},
                {"s": 1.0, "floor_top": 20.0}),
        "sailboat": (partial(sailboat, mid_sail=v2), {"h": horizon, "hw": np.arange(6.0, 9.51, 0.25),
                                                      "hh": np.arange(2.2, 3.61, 0.1),
                                                      "mw": np.array([0.8, 1.0, 1.2, 1.4])},
                     {"h": 18.0, "hw": 8.5, "hh": 2.6, "mw": 1.0}),
        # v2 keeps the v1 tree (r 4.4, g 19.0, tw 2.4): cat and sailboat are fitted to it.
        "tree": (tree, {"r": np.array([4.4]), "g": np.array([19.0]), "tw": np.array([2.4])},
                 {"r": 4.0, "g": 19.0, "tw": 2.0}) if v2 else
                (tree, {"r": np.arange(3.0, 6.01, 0.05), "g": np.arange(17.0, 21.01, 0.1),
                        "tw": np.array([1.6, 2.0, 2.4])}, {"r": 4.0, "g": 19.0, "tw": 2.0}),
    }


def tier_counts(tone: np.ndarray) -> tuple[int, int, int]:
    dark = int((tone < DARK_MAX).sum())
    light = int((tone > LIGHT_MIN).sum())
    return dark, tone.size - dark - light, light


def candidates(space: dict, name: str) -> dict:
    """All grid sizes of one subject, keyed by its (dark, mid) tier counts.

    Each key keeps the sizes closest to the sketch (smallest drift from the defaults).
    """
    build, grid, default = space[name]
    keys = list(grid)
    out: dict = {}
    for combo in np.array(np.meshgrid(*[grid[k] for k in keys])).reshape(len(keys), -1).T:
        params = dict(zip(keys, (float(v) for v in combo)))
        tone = build(**params)
        dark, mid, _ = tier_counts(tone)
        drift = sum(abs(params[k] - default[k]) / (np.ptp(grid[k]) or 1) for k in keys)
        if (dark, mid) not in out or drift < out[(dark, mid)][0]:
            out[(dark, mid)] = (drift, params, tone)
    return out


def fit_all(suffix: str = "") -> dict:
    """Pick one size per subject so the dark and mid counts agree across the three images.

    Searches every combination of achievable (dark, mid) pairs, keeping the combination with the
    smallest spread (max - min) in each tier, then the smallest total distance to the targets
    DARK_T and MID_T, then the smallest drift from the sketch sizes.
    """
    names = ["cat", "sailboat", "tree"]
    space = search_space(suffix)
    cands = {n: {k: v for k, v in candidates(space, n).items()
                 if abs(k[0] - DARK_T) <= 8 and abs(k[1] - MID_T) <= 12} for n in names}
    best = None
    for a in cands["cat"]:
        for b in cands["sailboat"]:
            for c in cands["tree"]:
                trio = (a, b, c)
                darks = [t[0] for t in trio]
                mids = [t[1] for t in trio]
                spread = (max(darks) - min(darks)) + (max(mids) - min(mids))
                if max(darks) - min(darks) > 3 or max(mids) - min(mids) > 3:
                    continue
                err = sum(abs(d - DARK_T) + abs(m - MID_T) for d, m in trio)
                drift = sum(cands[n][t][0] for n, t in zip(names, trio))
                score = (spread, err, drift)
                if best is None or score < best[0]:
                    best = (score, dict(zip(names, trio)))
    if best is None:
        raise SystemExit("no size combination matches the tier counts within +-3")
    return {n: cands[n][t] for n, t in best[1].items()}


def save_preview(name, tone, suffix):
    g = np.round(tone * 255).astype(np.uint8)
    Image.fromarray(g, mode="L").resize((COLS * UP, ROWS * UP), Image.NEAREST).save(OUT / f"{name}{suffix}.png")


def main(suffix: str = "") -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fits = fit_all(suffix)
    counts = {}
    for name in ["cat", "sailboat", "tree"]:
        _, params, tone = fits[name]
        assert tone.shape == (ROWS, COLS)
        np.save(OUT / f"{name}{suffix}.npy", tone)
        save_preview(name, tone, suffix)
        counts[name] = tier_counts(tone)
        p = ", ".join(f"{k}={v:.2f}" for k, v in params.items())
        print(f"{name} ({p}): dark {counts[name][0]}  mid {counts[name][1]}  light {counts[name][2]}")
    darks = [c[0] for c in counts.values()]
    mids = [c[1] for c in counts.values()]
    print(f"dark spread {max(darks) - min(darks)}, mid spread {max(mids) - min(mids)} (limit 3)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
