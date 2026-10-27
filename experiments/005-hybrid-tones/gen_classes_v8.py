"""Class spec v8 for experiment 005: the v7 set plus three-tier junction classes (tee).

Adds <A><B><C>j for every ordered triple of distinct tiers A, B, C from D, M, L: six classes.
The base A fills the cell. Mass B is clipped by the named mask p1 (march_mask pattern "tee",
part 1), and mass C by p2 (part 2). Both masks take one geometry per class (the crc32 of the
class name): a class spec gives each named mask its own seed, so without a shared geometry
the two parts would not meet. The parts of one tee therefore always share their boundary, but
every cell of one class has the same junction outline.

Rotation rule (the allowed rotations are clockwise quarter turns). At rotation 0:
  top side:    B on its left half, C on its right half (the junction side J)
  left side:   B above, A below
  right side:  C above, A below
  bottom side: A
To encode a cell whose junction is on side J (the side whose two halves carry two different
foreign tiers): pick the rotation r that turns J to the top (J top: 0, right: 90, bottom: 180,
left: 270). Then B is the tier on the side counter-clockwise from J, and C the tier on the side
clockwise from J, each on the half next to J. A is the tier on the side opposite J.

Not generated: tee_side is tee turned a quarter turn clockwise, so <A><B><C>k at rotation r is
exactly <A><B><C>j at rotation r + 90, and a second set would only add ties for a quantizer. quad
(rare) is in textures.py, but no classes are made for it: its four regions need a fourth tier or
a repeated mass tier, and this spec covers triples of D, M, L only.

Writes classes-v8.json, validates it with load_class_spec, and renders junction-demo.png next to
this file: a 3 x 3 patch of a D region and an M region on an L background, with one tee in the
centre cell.

Run: python3 experiments/005-hybrid-tones/gen_classes_v8.py
"""
from __future__ import annotations

import copy
import itertools
import json
import sys
import zlib
from pathlib import Path

import cairosvg

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))

from metapuzzle.classes import ClassSpec, load_class_spec  # noqa: E402

import gen_classes_v7 as v7  # noqa: E402

SRC = HERE / "classes-v7.json"
OUT = HERE / "classes-v8.json"
DEMO_PNG = HERE / "junction-demo.png"

TIERS = "DML"
ROTATIONS = [0, 90, 180, 270]
CELL = 96.0          # demo cell size, in SVG units
DEMO_SCALE = 2       # PNG pixels per SVG unit

# (row, col) -> (class, clockwise rotation). The centre cell is the tee: base L, D in the
# top-left quadrant, M in the top-right one. Its neighbours share its edge midpoints: D runs up
# the column above it (a vertical boundary, a straight turned a quarter turn), M runs right, and
# the row through its middle is the L boundary of the two straights beside it.
DEMO = {
    (0, 0): ("D", 0),     (0, 1): ("DMs", 90),  (0, 2): ("M", 0),
    (1, 0): ("LDs", 0),   (1, 1): ("LDMj", 0),  (1, 2): ("LMs", 0),
    (2, 0): ("L", 0),     (2, 1): ("L", 0),     (2, 2): ("L", 0),
}


def _junction_mask(part: int, geometry: int) -> dict:
    return {"primitive": "march_mask",
            "params": {"pattern": "tee", "part": part, "roughness": 0.5, "wobble": 0.12,
                       "geometry": geometry}}


def build_v8(src: dict) -> dict:
    data = v7.build_v7(src)               # the v7 class set, unchanged
    classes = data["classes"]
    tiers = {t: classes[t]["layers"] for t in TIERS}
    for a, b, c in itertools.permutations(TIERS):
        name = f"{a}{b}{c}j"
        geometry = zlib.crc32(name.encode("ascii"))
        layers = copy.deepcopy(tiers[a])
        for part, tier in ((1, b), (2, c)):
            for layer in copy.deepcopy(tiers[tier]):
                layer["mask"] = f"p{part}"
                layers.append(layer)
        classes[name] = {
            "layers": layers,
            "directional": False,
            "allowed_rotations": list(ROTATIONS),
            "masks": {"p1": _junction_mask(1, geometry), "p2": _junction_mask(2, geometry)},
        }
    data["_note"] = ("v8 (005). The v7 class set plus <A><B><C>j tee junctions for every ordered "
                     "triple of D, M, L. Base A fills the cell; mass B under mask p1 (tee part 1), "
                     "mass C under p2 (tee part 2), both with one geometry per class. Rotation 0: "
                     "B on the left half of the top side, C on the right half, A on the bottom. "
                     "See gen_classes_v8.py for the rotation rule.")
    return data


def render_demo(spec: ClassSpec, out_png: Path) -> Path:
    """The 3 x 3 patch in DEMO, each cell drawn by the spec with its own seed."""
    draw = spec.drawer()
    parts = []
    for k, ((row, col), (cls, turn)) in enumerate(sorted(DEMO.items())):
        x, y = col * CELL, row * CELL
        frag = draw(f"demo{row}{col}", cls, 101 + 17 * k, CELL)
        parts.append(f'<g transform="translate({x:g} {y:g})">'
                     f'<g transform="rotate({turn} {CELL / 2:g} {CELL / 2:g})">{frag}</g></g>')
    side = 3 * CELL
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{side:g}" height="{side:g}" '
           f'viewBox="0 0 {side:g} {side:g}"><rect width="{side:g}" height="{side:g}" '
           f'fill="#ffffff"/>{"".join(parts)}</svg>')
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(out_png), scale=DEMO_SCALE)
    return out_png


def main() -> None:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    data = build_v8(src)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    spec = load_class_spec(OUT)           # validates every layer, mask and rotation
    junctions = [n for n, pc in spec.classes.items() if "p1" in pc.masks]
    print(f"{OUT.name}: {len(spec.classes)} classes valid (v7 set {len(spec.classes) - len(junctions)}, "
          f"new junction classes {len(junctions)}: {' '.join(junctions)})")
    print(render_demo(spec, DEMO_PNG))


if __name__ == "__main__":
    main()
