"""Render a texture demo sheet for seam inspection.

Each row shows four horizontally adjacent cells of one primitive with the same
parameters and different seeds. Seams between independent cells should be
invisible. Output goes to ``gallery/textures-demo.svg`` and ``.png``.

Run with ``python3 -m metapuzzle.texture_demo``.
"""

from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape

import cairosvg

from . import textures as tx

SAMPLE_PALETTE = ["#e8dcc4", "#5b7f5b", "#2f4f4f", "#c9a66b"]

CELL = 110            # integer, so adjacent cells land on whole pixels at 1x
CELLS_PER_ROW = 4
PAD = 12
COL_GAP = 24
TITLE_H = 34
LABEL_H = 20
ROW_GAP = 12
SHEET_COLS = 2

_REPO_GALLERY = Path(__file__).resolve().parents[2] / "gallery"

# (function, params) per row; each primitive gets three settings.
ROWS: list[tuple[object, dict]] = [
    (tx.stipple, {"density": 150, "radius": (0.012, 0.03)}),
    (tx.stipple, {"density": 400, "radius": (0.008, 0.02)}),
    (tx.stipple, {"density": 900, "radius": (0.004, 0.012)}),
    (tx.dabs, {"count": 40, "length": 0.12, "width": 0.04, "shape": "rect"}),
    (tx.dabs, {"count": 90, "length": 0.07, "width": 0.025}),
    (tx.dabs, {"count": 160, "length": 0.04, "width": 0.02, "shape": "ellipse"}),
    (tx.mosaic, {"tess": 0.10}),
    (tx.mosaic, {"tess": 0.06}),
    (tx.mosaic, {"tess": 0.035, "gap": 0.2}),
    (tx.hatch_multi, {"count": 60, "length": 0.14}),
    (tx.hatch_multi, {"count": 150, "length": 0.08}),
    (tx.hatch_multi, {"count": 300, "length": 0.05, "families": 3}),
    (tx.scatter_shapes, {"kinds": ("leaf", "disc"), "count": 20, "scale": 0.07}),
    (tx.scatter_shapes, {"kinds": ("triangle", "blob"), "count": 40, "scale": 0.045}),
    (tx.scatter_shapes, {"kinds": ("leaf", "disc", "triangle", "blob"), "count": 90, "scale": 0.03}),
    (tx.blotch, {"coverage": 0.2}),
    (tx.blotch, {"coverage": 0.6}),
    (tx.blotch, {"coverage": 0.4, "side": "bottom"}),
]


def _label(fn, params: dict) -> str:
    args = ", ".join(f"{k}={v}" for k, v in params.items())
    return f"{fn.__name__}  {args}"


def build_sheet(palette: list[str] = SAMPLE_PALETTE) -> str:
    """Return the demo sheet as an SVG document string."""
    per_col = math.ceil(len(ROWS) / SHEET_COLS)
    col_w = CELLS_PER_ROW * CELL
    width = 2 * PAD + SHEET_COLS * col_w + (SHEET_COLS - 1) * COL_GAP
    row_h = LABEL_H + CELL + ROW_GAP
    height = TITLE_H + PAD + per_col * row_h

    parts = [
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{PAD}" y="22" font-family="sans-serif" font-size="14" fill="#111">'
        f"Texture demo: {CELLS_PER_ROW} adjacent cells per row, same parameters, "
        f"different seeds</text>",
    ]
    for idx, (fn, params) in enumerate(ROWS):
        col, r = divmod(idx, per_col)
        x0 = PAD + col * (col_w + COL_GAP)
        y0 = TITLE_H + r * row_h
        parts.append(
            f'<text x="{x0}" y="{y0 + 14}" font-family="sans-serif" font-size="12" '
            f'fill="#222">{escape(_label(fn, params))}</text>'
        )
        for i in range(CELLS_PER_ROW):
            seed = 1000 * (idx + 1) + i
            frag = fn(seed, CELL, palette, **params)
            parts.append(
                f'<g transform="translate({x0 + i * CELL} {y0 + LABEL_H})">{frag}</g>'
            )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">' + "".join(parts) + "</svg>"
    )


def main(out_dir: str | Path | None = None) -> tuple[Path, Path]:
    """Render the sheet to textures-demo.svg and textures-demo.png; return both paths."""
    out = Path(out_dir) if out_dir is not None else _REPO_GALLERY
    out.mkdir(parents=True, exist_ok=True)
    svg = build_sheet()
    svg_path = out / "textures-demo.svg"
    png_path = out / "textures-demo.png"
    svg_path.write_text(svg, encoding="utf-8")
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path))
    print(svg_path)
    print(png_path)
    return svg_path, png_path


if __name__ == "__main__":
    main()
