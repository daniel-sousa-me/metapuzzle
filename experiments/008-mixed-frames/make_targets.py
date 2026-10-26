"""Procedural tone targets for the mixed-frame experiment (008).

Three targets with different shapes, all 480 cells: a portrait tree (20 cols x 24 rows),
a landscape sailboat (30 x 16) and a panorama skyline (40 x 12). Each is a float array in
[0, 1]; 0 = dark, 1 = light. Shapes are drawn on an SS x supersampled grid and box-downsampled,
so boundary cells get fractional tones. Coordinates are in cell units: x runs 0..cols,
y runs 0..rows.
"""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "targets"
SS = 8
UP = 16  # preview upscale (nearest)
SHAPES = {"tree": (20, 24), "sailboat": (30, 16), "panorama": (40, 12)}  # (cols, rows)


def sample_grid(cols, rows):
    ys = (np.arange(rows * SS) + 0.5) / SS
    xs = (np.arange(cols * SS) + 0.5) / SS
    return np.meshgrid(xs, ys)  # X, Y: shape (rows*SS, cols*SS)


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


def paint(shape, ground, layers):
    """layers: list of (mask, tone), painted in order over the ground tone."""
    cols, rows = shape
    img = np.full((rows * SS, cols * SS), ground, dtype=float)
    for mask, tone in layers:
        img[mask] = tone
    return img


def downsample(img, shape):
    cols, rows = shape
    return img.reshape(rows, SS, cols, SS).mean(axis=(1, 3))


def tree():
    """Tall tree: dark round canopy and trunk, light sky, mid ground band."""
    shape = SHAPES["tree"]
    X, Y = sample_grid(*shape)
    layers = [
        (rect(X, Y, 0, 20, 21.5, 24), 0.50),        # ground band (mid)
        (rect(X, Y, 9.0, 11.0, 13.5, 21.8), 0.10),  # trunk (dark)
        (disc(X, Y, 10.0, 8.5, 6.5), 0.12),         # round canopy (dark)
    ]
    return downsample(paint(shape, 0.92, layers), shape)  # light sky


def sailboat():
    """Landscape sailboat: dark hull and mast, light sail, mid sea, light sky."""
    shape = SHAPES["sailboat"]
    X, Y = sample_grid(*shape)
    layers = [
        (rect(X, Y, 0, 30, 9.0, 16), 0.45),                                              # sea (mid)
        (polygon(X, Y, [(8.5, 9.6), (21.5, 9.6), (19.6, 11.6), (10.4, 11.6)]), 0.08),   # hull (dark)
        (rect(X, Y, 14.6, 15.4, 2.5, 9.6), 0.08),                                        # mast (dark)
        (polygon(X, Y, [(15.9, 3.0), (15.9, 9.2), (23.0, 9.2)]), 1.00),                  # sail (light)
    ]
    return downsample(paint(shape, 0.80, layers), shape)  # light sky above the horizon at y = 9


def panorama():
    """Mountain skyline: dark jagged range in the lower half, light sky, small light sun disc."""
    shape = SHAPES["panorama"]
    X, Y = sample_grid(*shape)
    ridge = [(0, 8.0), (3, 6.2), (5, 7.4), (8, 4.6), (11, 7.0), (14, 5.0), (17, 7.6), (20, 5.4),
             (23, 4.3), (26, 6.8), (29, 5.6), (32, 7.4), (35, 5.0), (38, 6.8), (40, 6.2)]
    layers = [
        (polygon(X, Y, ridge + [(40, 12), (0, 12)]), 0.10),  # mountains (dark)
        (disc(X, Y, 33.0, 2.5, 1.6), 1.00),                  # sun (light)
    ]
    return downsample(paint(shape, 0.80, layers), shape)  # light sky


def save_preview(name, tone):
    g = np.round(tone * 255).astype(np.uint8)
    rows, cols = tone.shape
    Image.fromarray(g, mode="L").resize((cols * UP, rows * UP), Image.NEAREST).save(OUT / f"{name}.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in [("tree", tree), ("sailboat", sailboat), ("panorama", panorama)]:
        tone = fn()
        cols, rows = SHAPES[name]
        assert tone.shape == (rows, cols), (name, tone.shape)
        np.save(OUT / f"{name}.npy", tone)
        save_preview(name, tone)
        print(f"{name} {cols}x{rows}: min {tone.min():.3f} max {tone.max():.3f} mean {tone.mean():.3f}")


if __name__ == "__main__":
    main()
