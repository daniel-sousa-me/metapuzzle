"""Contact sheet and pairs sheet for the Direction A class spec.

Pieces are drawn at the spec's ref_size (100 units, the unit the counts are written
in) and scaled into 64 px cells by the drawer, so the density matches the lexicon.
Run: PYTHONPATH=src python3 experiments/002-direction-a/render_sheets.py
"""
import json
from pathlib import Path

from metapuzzle.classes import _write_sheet, load_class_spec

HERE = Path(__file__).resolve().parent
CELL = 64.0   # displayed cell size in px

spec = load_class_spec(HERE / "classes.json")
CIDS = {k: v["_id"] for k, v in json.loads((HERE / "classes.json").read_text())["classes"].items()}
draw = spec.drawer()


def frag(cls: str, seed: int) -> str:
    # The drawer builds the piece at the spec's ref_size and scales it to CELL itself.
    return draw(f"{cls}#{seed}", cls, seed, CELL)


def contact_rows():
    rows, seed = [], 1
    for code, pc in spec.classes.items():
        label = f"{code}  {CIDS[code]}  rot {list(pc.allowed_rotations)}"
        if pc.directional:
            label += "  dir"
        cells = []
        for _ in range(4):
            cells.append(frag(code, seed))
            seed += 1
        rows.append((label, cells))
    return rows


PAIRS = [
    # soft pairs the seam rule allows at a cut
    ("SK", "SN"), ("ME", "FO"), ("FO", "DP"),
    # rust may touch anything as a short object edge
    ("RU", "ME"), ("RU", "SK"),
    # each transition next to both of its materials
    ("S/", "SK"), ("S/", "SN"), ("S\\", "SK"), ("S\\", "SN"),
    ("F/", "SK"), ("F/", "FO"), ("F\\", "SK"), ("F\\", "FO"),
    ("HD", "SK"), ("HD", "DP"),
]


def pair_rows():
    rows, seed = [], 1
    for a, b in PAIRS:
        cells = [frag(a, seed), frag(b, seed + 1)]
        seed += 2
        rows.append((f"{a} {CIDS[a]} | {b} {CIDS[b]}", cells))
    return rows


if __name__ == "__main__":
    print(_write_sheet(contact_rows(), CELL, HERE / "contact-sheet.png"))
    print(_write_sheet(pair_rows(), CELL, HERE / "pairs-sheet.png"))
