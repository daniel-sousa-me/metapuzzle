"""Class spec v7 for experiment 005: the v4 set plus diag, tip, bump and notch transitions.

Extends gen_classes_v4.build (the v4 class set, unchanged) with four new march_mask patterns for every
ordered pair of tiers D, M, L, W (12 pairs):
  <own><nbr>g   pattern "diag"   the boundary runs corner to corner (45 degrees)
  <own><nbr>t   pattern "tip"    the base rises to a peak at the middle (height 0.75)
  <own><nbr>b   pattern "bump"   the path bulges up into the mass (amplitude 0.18)
  <own><nbr>n   pattern "notch"  the path dips down into the base (amplitude 0.18)
The construction matches v4: the own tier is the base, the neighbour tier is the mass under a mask
named "edge", and rotation 0 puts the neighbour on top (the mass sides are top, or the rotated sides).
Diag tiles have T and R fully mass and L and B fully base (quantize_v6 uses them with the rotation
that matches the mass sides, as for c).

Writes classes-v7.json, validates it with load_class_spec, and renders contact-sheet-v7.png (the new
classes, each pattern in both tier orders of D/M/L) next to this file.

Run: python3 experiments/005-hybrid-tones/gen_classes_v7.py
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))

from metapuzzle.classes import ClassSpec, load_class_spec  # noqa: E402

import gen_classes_v4 as v4  # noqa: E402

SRC = HERE / "classes.json"
OUT = HERE / "classes-v7.json"
SHEET_PNG = HERE / "contact-sheet-v7.png"

TIERS = "DMLW"
NEW = {  # letter: (march pattern, extra params)
    "g": ("diag", {}),
    "t": ("tip", {"height": 0.75}),
    "b": ("bump", {"amplitude": 0.18}),
    "n": ("notch", {"amplitude": 0.18}),
}


def _march(pattern: str, extra: dict) -> dict:
    params = {"pattern": pattern, "roughness": 0.5, "wobble": 0.12}
    params.update(extra)
    return {"primitive": "march_mask", "params": params}


def build_v7(src: dict) -> dict:
    data = v4.build(src)                  # the v4 class set, unchanged
    classes = data["classes"]
    tiers = {t: classes[t]["layers"] for t in "DML"}
    tiers["W"] = classes["W"]["layers"]
    for own in TIERS:
        for nbr in TIERS:
            if own == nbr:
                continue
            for letter, (pattern, extra) in NEW.items():
                nbr_layers = copy.deepcopy(tiers[nbr])
                for layer in nbr_layers:
                    layer["mask"] = "edge"
                classes[f"{own}{nbr}{letter}"] = {
                    "layers": copy.deepcopy(tiers[own]) + nbr_layers,
                    "directional": False,
                    "allowed_rotations": [0, 90, 180, 270],
                    "masks": {"edge": _march(pattern, extra)},
                }
    data["_note"] = ("v7 (005). The v4 class set plus <own><nbr>g (diag), t (tip), b (bump), n (notch) for "
                     "every ordered pair of D, M, L, W. Transitions: own tier base, neighbour tier mass under "
                     "a march_mask named 'edge'; rotation as in v4. Diag: T and R mass, L and B base.")
    return data


def write_sheet(spec: ClassSpec, out_png: Path) -> Path:
    """One row per pattern letter, the six ordered pairs of D, M, L (both orders), one seed each."""
    names = [f"{own}{nbr}{letter}" for letter in NEW for own, nbr in
             (("D", "M"), ("M", "D"), ("D", "L"), ("L", "D"), ("M", "L"), ("L", "M"))]
    sub = ClassSpec(palette=spec.palette, classes={k: spec.classes[k] for k in names},
                    ref_size=spec.ref_size)
    return sub.contact_sheet(out_png, cell=72, per_class=1)


def main() -> None:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    data = build_v7(src)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    spec = load_class_spec(OUT)           # validates every layer, mask and rotation
    names = list(spec.classes)
    new = [n for n in names if len(n) == 3 and n[2] in NEW]
    print(f"{OUT.name}: {len(names)} classes valid (v4 set 60, new {len(new)}: "
          f"{len(NEW)} patterns x {len(TIERS) * (len(TIERS) - 1)} ordered pairs)")
    print(write_sheet(spec, SHEET_PNG))


if __name__ == "__main__":
    main()
