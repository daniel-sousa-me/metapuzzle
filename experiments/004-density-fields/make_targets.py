"""Procedural tone targets for the density-field mosaic experiment.

Each target is a (25 rows x 20 cols) float array in [0, 1]; 0 = dark, 1 = light.
Shapes are drawn on an 8x supersampled grid and box-downsampled, so boundary
cells get fractional tones (anti-aliasing). Coordinates are in cell units:
x runs 0..20 (columns), y runs 0..25 (rows).
"""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "targets"
ROWS, COLS, SS = 25, 20, 8
UP = 16  # preview upscale (nearest)


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
    img = np.full(ground_shape(), ground, dtype=float)
    for mask, tone in layers:
        img[mask] = tone
    return img


def ground_shape():
    return (ROWS * SS, COLS * SS)


def downsample(img):
    return img.reshape(ROWS, SS, COLS, SS).mean(axis=(1, 3))


def cat():
    X, Y = sample_grid()
    dark = 0.06
    tail = [(13.0, 21.0), (15.6, 21.8), (17.8, 20.6), (18.6, 18.0), (17.9, 15.9), (15.9, 15.0), (14.7, 16.0)]
    layers = [
        (ellipse(X, Y, 10.0, 15.6, 4.6, 6.2), dark),          # body
        (disc(X, Y, 10.0, 8.0, 3.1), dark),                   # head
        (polygon(X, Y, [(7.4, 6.4), (7.7, 1.9), (9.6, 5.0)]), dark),    # left ear
        (polygon(X, Y, [(12.6, 6.4), (12.3, 1.9), (10.4, 5.0)]), dark),  # right ear
        (stroke(X, Y, tail, 0.7), dark),                      # curled tail
    ]
    return downsample(paint(0.90, layers))


def sailboat():
    X, Y = sample_grid()
    layers = [
        (rect(X, Y, 0, COLS, 12.0, ROWS), 0.45),                          # sea (mid)
        (polygon(X, Y, [(4.5, 15.5), (15.5, 15.5), (13.8, 18.2), (6.2, 18.2)]), 0.08),  # hull (dark)
        (rect(X, Y, 9.6, 10.4, 3.5, 15.8), 0.08),                         # mast
        (polygon(X, Y, [(10.6, 4.0), (10.6, 14.8), (16.8, 14.8)]), 1.00),  # sail (light)
    ]
    return downsample(paint(0.78, layers))  # sky (light) above the horizon at y = 12


def tree():
    X, Y = sample_grid()
    layers = [
        (rect(X, Y, 0, COLS, 20.5, ROWS), 0.50),              # ground band (mid)
        (rect(X, Y, 9.0, 11.0, 11.0, 21.0), 0.10),            # trunk (dark)
        (disc(X, Y, 10.0, 8.0, 7.0), 0.12),                   # canopy (dark, large, round)
    ]
    return downsample(paint(0.92, layers))


def save_preview(name, tone):
    g = np.round(tone * 255).astype(np.uint8)
    Image.fromarray(g, mode="L").resize((COLS * UP, ROWS * UP), Image.NEAREST).save(OUT / f"{name}.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in [("cat", cat), ("sailboat", sailboat), ("tree", tree)]:
        tone = fn()
        assert tone.shape == (ROWS, COLS)
        np.save(OUT / f"{name}.npy", tone)
        save_preview(name, tone)
        print(f"{name}: min {tone.min():.3f} max {tone.max():.3f} mean {tone.mean():.3f}")


if __name__ == "__main__":
    main()
