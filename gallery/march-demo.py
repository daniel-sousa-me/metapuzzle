"""Marching-squares transition demo.

A 5 x 5 arrangement of 64-unit cells. The middle 3 x 3 block is dark, but its eight
ring cells are transition tiles, so the dark mass is a ragged blob inside that block.
Each transition tile is a dark stipple clipped by ``march_mask`` over a light stipple
base. Its boundary crosses every edge only at that edge's midpoint, so the loop is
continuous across each cut. The rotations below are chosen so that the two sides of
every shared edge have the same light and dark halves.

Two ring cells use the new patterns. The top-middle cell is a "tip" drawn with its colours
swapped, so its dark tent points up out of the blob as an ear. The right-middle cell is a
"bump", a light convex bulge pushing into the dark side. Each still meets its neighbours at
the midpoints of the shared edges, so the outline stays continuous.

Run with ``python3 gallery/march-demo.py``. Writes ``gallery/march-demo.png``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cairosvg

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from metapuzzle import textures as tx  # noqa: E402

CELL = 64.0
GRID = 5
PAD = 16.0
SCALE = 2                                   # PNG pixels per SVG unit
OUT = Path(__file__).resolve().parent / "march-demo.png"

LIGHT = ["#e8dcc4", "#c9a66b", "#b08d55"]   # base, then marks
DARK = ["#2f4f4f", "#1d3535", "#4f7070"]

# (col, row) -> (pattern, clockwise rotation in degrees) for the eight ring cells of the
# 3 x 3 block. The mass is dark and the base is light. Unrotated, "straight" puts its
# mass above the path, and "corner_in" puts its mass in the top-left corner. The block's
# convex corners need "corner_in" (a small dark corner), not "corner" (a small light one).
TRANSITIONS = {
    (2, 1): ("tip", 0),             # top side: the dark ear (colours swapped, see tile())
    (3, 2): ("bump", 270),          # right side: a light bulge into the blob
    (2, 3): ("straight", 0),        # bottom side: light below
    (1, 2): ("straight", 90),       # left side: light to the left
    (1, 1): ("corner_in", 180),     # top-left corner
    (3, 1): ("corner_in", 270),     # top-right corner
    (3, 3): ("corner_in", 0),       # bottom-right corner
    (1, 3): ("corner_in", 90),      # bottom-left corner
}
CENTER = (2, 2)
EAR = (2, 1)                        # its "tip" has the light colour as mass, so the dark tent
                                    # below the peak is the ear


def tile(col: int, row: int, seed: int) -> str:
    """SVG for the cell at (col, row), in cell-local coordinates."""
    if (col, row) == CENTER:
        return tx.stipple(seed, CELL, DARK)
    if (col, row) not in TRANSITIONS:
        return tx.stipple(seed, CELL, LIGHT)
    pattern, turn = TRANSITIONS[(col, row)]
    clip, cid = tx.march_mask(seed + 2, CELL, pattern=pattern)
    base_colours, mass_colours = (DARK, LIGHT) if (col, row) == EAR else (LIGHT, DARK)
    base = tx.stipple(seed, CELL, base_colours)
    mass = tx.stipple(seed + 1, CELL, mass_colours)
    body = tx.compose(base, f'<defs>{clip}</defs><g clip-path="url(#{cid})">{mass}</g>')
    return f'<g transform="rotate({turn} 32 32)">{body}</g>'


def build() -> str:
    """The whole arrangement as one SVG document."""
    side = 2 * PAD + GRID * CELL
    parts = [f'<rect width="{side:g}" height="{side:g}" fill="#ffffff"/>']
    for row in range(GRID):
        for col in range(GRID):
            k = row * GRID + col
            x, y = PAD + col * CELL, PAD + row * CELL
            parts.append(f'<g transform="translate({x:g} {y:g})">'
                         f'{tile(col, row, 3 * k + 1)}</g>')
    body = "".join(parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{side:g}" height="{side:g}" '
            f'viewBox="0 0 {side:g} {side:g}">{body}</svg>')


def main() -> Path:
    cairosvg.svg2png(bytestring=build().encode("utf-8"), write_to=str(OUT), scale=SCALE)
    return OUT


if __name__ == "__main__":
    print(main())
