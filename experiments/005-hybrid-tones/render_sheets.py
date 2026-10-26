"""Contact sheet and pairs sheet for the 005 hybrid-tones class spec.

Pieces are drawn at the spec's ref_size and scaled into 64 px cells by the drawer.
Run: PYTHONPATH=src python3 experiments/005-hybrid-tones/render_sheets.py

pairs-sheet.png has two kinds of row:
  * plain pairs (D|M, M|L, D|L): an A cell and a B cell side by side;
  * transitions: the neighbour's plain cell above and the transition cell below, the
    arrangement the class is drawn for (base below, neighbour above at @0).
"""
from pathlib import Path

import cairosvg

from metapuzzle.classes import _SHEET_LABEL_H, _SHEET_PAD, _SHEET_ROW_GAP, load_class_spec
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
CELL = 64.0   # displayed cell size in px
GAP = 24.0    # horizontal gap between instances in a row

spec = load_class_spec(HERE / "classes.json")
draw = spec.drawer()


def frag(cls: str, seed: int) -> str:
    return draw(f"{cls}#{seed}", cls, seed, CELL)


PLAIN_PAIRS = [("D", "M"), ("M", "L"), ("D", "L")]
# transition code -> (base tier, neighbour tier placed above)
TRANSITIONS = {"DM": "M", "DL": "L", "MD": "D", "ML": "L", "LD": "D", "LM": "M"}


def pairs_rows():
    """Rows of (label, items, width, height); items are (x, y, svg) in px."""
    rows, seed = [], 1
    for a, b in PLAIN_PAIRS:
        items, w = [], 0.0
        for k in range(2):
            x0 = k * (2 * CELL + GAP)
            items.append((x0, 0.0, frag(a, seed)))
            items.append((x0 + CELL, 0.0, frag(b, seed + 1)))
            seed += 2
        w = 2 * (2 * CELL + GAP) - GAP
        rows.append((f"{a} | {b}", items, w, CELL))
    for code, above in TRANSITIONS.items():
        items = []
        for k in range(2):
            x0 = k * (CELL + GAP)
            items.append((x0, 0.0, frag(above, seed)))          # neighbour, above
            items.append((x0, CELL, frag(code, seed + 1)))      # transition, below
            seed += 2
        w = 2 * CELL + GAP
        rows.append((f"{code} over {above}  (base {code[0]} below, neighbour {above} above)",
                     items, w, 2 * CELL))
    return rows


def write_pairs(out_png: Path) -> Path:
    rows = pairs_rows()
    width = 2 * _SHEET_PAD + max(max(w for _, _, w, _ in rows),
                                 max(0.6 * 12 * len(label) for label, *_ in rows))
    parts = []
    y = _SHEET_PAD
    for label, items, _, h in rows:
        parts.append(f'<text x="{_SHEET_PAD}" y="{y + 14:g}" font-family="sans-serif" '
                     f'font-size="12" fill="#222">{escape(label)}</text>')
        for x, dy, svg in items:
            parts.append(f'<g transform="translate({_SHEET_PAD + x:g} '
                         f'{y + _SHEET_LABEL_H + dy:g})">{svg}</g>')
        y += _SHEET_LABEL_H + h + _SHEET_ROW_GAP
    height = y + _SHEET_PAD - _SHEET_ROW_GAP
    w, hh = f"{width:g}", f"{height:g}"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{hh}" '
           f'viewBox="0 0 {w} {hh}"><rect x="0" y="0" width="{w}" height="{hh}" '
           f'fill="#ffffff"/>' + "".join(parts) + "</svg>")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(out_png))
    return out_png


if __name__ == "__main__":
    print(spec.contact_sheet(HERE / "contact-sheet.png", cell=CELL, per_class=4))
    print(write_pairs(HERE / "pairs-sheet.png"))
