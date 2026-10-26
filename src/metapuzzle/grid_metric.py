"""Automatic grid visibility: straight colour steps along piece edges in a solution PNG.

Human reviewers rate grid visibility by looking for straight colour steps on piece edges. This
module measures the same thing on a rendered solution (`solution-X.png`, without the grid overlay):

- Every interior grid line segment is the edge shared by two adjacent cells. Its *across-edge
  contrast* is the CIE76 colour difference between the `band`-pixel strip just inside one cell and
  the strip just inside the other, computed row by row along the edge and averaged.
- The *within-cell contrast* is the same statistic on a line of the same orientation through the
  middle of a cell, where no piece edge exists. The median over the board is the reference.
- A segment is *visible* when its across-edge contrast exceeds `VISIBLE_RATIO` (2) times that
  reference. A full grid line (every segment of one interior row or column boundary) is visible
  when more than half of its segments are visible.

Geometry follows render.py: cell (c, r) spans x in [margin + c*cell, margin + (c+1)*cell) and the
same for y. An image rendered at an integer scale k has cell and margin multiplied by k. The margin
is not recorded in run folders, so `run_grid_metric` uses render.py's default.

`grid_score` maps the visible fraction onto the 1-5 human scale (5 = the grid is strongly visible).
"""
from __future__ import annotations

import inspect
import json
import re
from collections.abc import Mapping
from pathlib import Path

import numpy as np
from PIL import Image

BAND = 3  # pixels of strip on each side of an edge
VISIBLE_RATIO = 2.0  # visible when across-edge contrast > VISIBLE_RATIO * within-cell median
SOLUTION_NAMES = ("A", "B", "C")

# Visible fraction -> human-scale score. Upper bounds are inclusive: <=0.15 scores 1, (0.15, 0.30]
# scores 2, (0.30, 0.50] scores 3, (0.50, 0.70] scores 4, and above 0.70 scores 5.
GRID_SCORE_BANDS = ((0.15, 1), (0.30, 2), (0.50, 3), (0.70, 4))

# CIE D65 white point and sRGB -> XYZ matrix (D65).
_D65 = np.array([0.95047, 1.0, 1.08883])
_RGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ]
)


def srgb_to_lab(rgb) -> np.ndarray:
    """sRGB values in 0..255 (any shape ending in 3) -> CIE L*a*b* (D65)."""
    c = np.asarray(rgb, dtype=float) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = (lin @ _RGB_TO_XYZ.T) / _D65
    eps, kappa = 216 / 24389, 24389 / 27
    f = np.where(xyz > eps, np.cbrt(xyz), (kappa * xyz + 16) / 116)
    return np.stack(
        [116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1
    )


def _vertical_contrast(lab: np.ndarray, x: int, y0: int, y1: int, band: int) -> float:
    """Contrast along the vertical line at column boundary x, rows [y0, y1)."""
    left = lab[y0:y1, x - band : x].mean(axis=1)
    right = lab[y0:y1, x : x + band].mean(axis=1)
    return float(np.linalg.norm(left - right, axis=1).mean())


def _horizontal_contrast(lab: np.ndarray, y: int, x0: int, x1: int, band: int) -> float:
    """Contrast along the horizontal line at row boundary y, columns [x0, x1)."""
    top = lab[y - band : y, x0:x1].mean(axis=0)
    bottom = lab[y : y + band, x0:x1].mean(axis=0)
    return float(np.linalg.norm(top - bottom, axis=1).mean())


def _geometry(size: tuple[int, int], cols: int, rows: int, cell: int, margin: int) -> tuple[int, int]:
    """Cell and margin in pixels for an image of `size` (w, h), allowing an integer render scale."""
    w, h = size
    ew, eh = 2 * margin + cols * cell, 2 * margin + rows * cell
    k = w // ew if ew > 0 else 0
    if k < 1 or w != k * ew or h != k * eh:
        raise ValueError(
            f"image is {w}x{h}px; expected {ew}x{eh}px (or an integer multiple) for {cols}x{rows} cells "
            f"of {cell}px with a {margin}px margin"
        )
    return cell * k, margin * k


def edge_contrast(png_path, cols: int, rows: int, cell: int, margin: int, band: int = BAND) -> dict:
    """Across-edge contrast of every interior grid segment of a solution PNG.

    Vertical grid lines are the boundaries between columns: `across["v"]` has shape (rows, cols-1)
    and `across["h"]` (horizontal lines, between rows) has shape (rows-1, cols). Within-cell
    references are per orientation: `within_median["v"]` is the median of the middle-line contrasts
    of vertical lines through every cell, and `within_median["h"]` the same for horizontal lines.

    Returns a dict with: `across`, `within_median`, `visible` (boolean arrays, same shapes as
    `across`), `visible_fraction` (visible segments / all segments), `line_fraction` (full grid
    lines with more than half their segments visible / all interior lines), `n_segments`,
    `n_lines`, `lines_visible`. With no interior segments both fractions are 0.0.
    """
    if cols < 1 or rows < 1:
        raise ValueError("cols and rows must be at least 1")
    if cell < 2 * band:
        raise ValueError(f"cell must be at least {2 * band}px for a {band}px band")
    with Image.open(png_path) as im:
        rgb = np.asarray(im.convert("RGB"), dtype=float)
    cell_px, m = _geometry((rgb.shape[1], rgb.shape[0]), cols, rows, cell, margin)
    lab = srgb_to_lab(rgb)
    half = cell_px // 2

    across_v = np.zeros((rows, cols - 1))
    across_h = np.zeros((rows - 1, cols))
    within_v = np.zeros((rows, cols))
    within_h = np.zeros((rows, cols))
    for r in range(rows):
        y0 = m + r * cell_px
        for c in range(cols):
            x0 = m + c * cell_px
            within_v[r, c] = _vertical_contrast(lab, x0 + half, y0, y0 + cell_px, band)
            within_h[r, c] = _horizontal_contrast(lab, y0 + half, x0, x0 + cell_px, band)
            if c < cols - 1:
                across_v[r, c] = _vertical_contrast(lab, x0 + cell_px, y0, y0 + cell_px, band)
            if r < rows - 1:
                across_h[r, c] = _horizontal_contrast(lab, y0 + cell_px, x0, x0 + cell_px, band)

    ref = {"v": float(np.median(within_v)), "h": float(np.median(within_h))}
    visible = {"v": across_v > VISIBLE_RATIO * ref["v"], "h": across_h > VISIBLE_RATIO * ref["h"]}
    n_seg = visible["v"].size + visible["h"].size
    n_vis = int(visible["v"].sum() + visible["h"].sum())
    # A vertical line has `rows` segments (one per row); a horizontal line has `cols` segments.
    lines_visible = int((visible["v"].sum(axis=0) > rows / 2).sum()) + int(
        (visible["h"].sum(axis=1) > cols / 2).sum()
    )
    n_lines = (cols - 1) + (rows - 1)
    return {
        "across": {"v": across_v, "h": across_h},
        "within_median": ref,
        "visible": visible,
        "visible_fraction": n_vis / n_seg if n_seg else 0.0,
        "line_fraction": lines_visible / n_lines if n_lines else 0.0,
        "n_segments": n_seg,
        "n_lines": n_lines,
        "lines_visible": lines_visible,
    }


def grid_score(metrics) -> float:
    """Human-scale grid visibility, 1 (invisible) to 5 (strong), from `edge_contrast` output.

    Accepts the dict returned by `edge_contrast` or a visible fraction directly. Bands on the
    visible fraction: <=0.15 -> 1, <=0.30 -> 2, <=0.50 -> 3, <=0.70 -> 4, above -> 5 (see GRID_SCORE_BANDS).
    The bands are a rough calibration against the recorded human verdicts in experiments/009.
    """
    f = float(metrics["visible_fraction"]) if isinstance(metrics, Mapping) else float(metrics)
    for upper, score in GRID_SCORE_BANDS:
        if f <= upper:
            return float(score)
    return 5.0


def run_geometry(run_dir) -> dict:
    """Board sizes from solution.json and the cell size from summary.md of a prototype run folder.

    The margin is not recorded, so render.py's default `margin` for `render_all` is used.
    """
    from .render import render_all  # lazy: cairosvg is only needed here

    run = Path(run_dir)
    summary, sol_json = run / "summary.md", run / "solution.json"
    if not summary.is_file() or not sol_json.is_file():
        raise ValueError(f"{run} is not a prototype run folder (needs summary.md and solution.json)")
    match = re.search(r"^- cell: (\d+)\s*$", summary.read_text(encoding="utf-8"), re.M)
    if not match:
        raise ValueError(f"{summary} records no cell size")
    boards = json.loads(sol_json.read_text(encoding="utf-8"))["boards"]
    margin = inspect.signature(render_all).parameters["margin"].default
    return {
        "cell": int(match.group(1)),
        "margin": int(margin),
        "sizes": [(int(b["cols"]), int(b["rows"])) for b in boards],
    }


def run_grid_metric(run_dir) -> dict:
    """Grid metric for each of the three solution PNGs in a prototype run folder."""
    run = Path(run_dir)
    geo = run_geometry(run)
    solutions = []
    for k, name in enumerate(SOLUTION_NAMES):
        png = run / f"solution-{name}.png"
        if not png.is_file():
            raise ValueError(f"{png} is missing")
        cols, rows = geo["sizes"][k]
        m = edge_contrast(png, cols, rows, geo["cell"], geo["margin"])
        solutions.append(
            {
                "solution": name,
                "png": str(png),
                "visible_fraction": m["visible_fraction"],
                "line_fraction": m["line_fraction"],
                "score": grid_score(m),
                "within_median": m["within_median"],
            }
        )
    return {"run_dir": str(run), "geometry": geo, "solutions": solutions}
