"""Contact sheet and pairs sheet for the Direction B class spec (Garden Terrazzo).

Pieces are drawn at the spec's ref_size (100 units, the unit the counts are written
in) and scaled into 64 px cells by the drawer, so the density matches the lexicon.
Run: PYTHONPATH=src python3 experiments/006-direction-b/render_sheets.py
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
    # ranked pairs from the run-quarter window review (8th place: DK|GD kept over DT|TE)
    ("GT", "TE"), ("BL", "GB"), ("NT", "TE"), ("BL", "CB"),
    ("GB", "GD"), ("OC", "OG"), ("GR", "NT"), ("DK", "GD"),
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
