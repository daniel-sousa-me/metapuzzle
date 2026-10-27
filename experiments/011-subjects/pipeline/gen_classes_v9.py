"""Class specs v9 for experiment 011: the 005 v8 sets plus S-L transitions (chips against L).

Writes pipeline/classes-v9.json (colour) and pipeline/classes-ink-v9.json (ink), and validates both.

The generators are those of experiment 005, imported read-only from there (nothing in 005 is
written): gen_classes_v8.build_v8 gives the v8 colour set (v4 + v7 + tee junctions), and
gen_classes_ink_v8.junction_ink / gen_classes_ink.convert give the ink versions of them.

New in v9: the pair (L, S) in both orders, for the patterns below. S is the chip tier of classes-v4
(scatter_shapes, cream with indigo chips, background True); its layers are copied from classes-v4.json
so the recipe is the same one. Each class follows the v4 convention <own><nbr><p>: own layers are the
base (background included), nbr layers are the mass under a march_mask named 'edge' (dots: 'dot').

  <own><nbr>s  straight      <own><nbr>c  corner       <own><nbr>p  cap
  <own><nbr>d  dot (nbr base, own dot, as <nbr><own>d in v4)
  <own><nbr>g  diag          <own><nbr>t  tip (height 0.75)

Darker first: S sits between D and M in the quantizer's order (run_from_tiers_v2.py), so the
canonical pair is S then L. Both orders are generated, so every quantizer code exists in either
spelling. The i (convex corner) pattern is not generated: the quantizer writes it as a c class with
the tiers swapped, as for the other pairs.

Run: python3 experiments/011-subjects/pipeline/gen_classes_v9.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP005 = HERE.parents[1] / "005-hybrid-tones"
sys.path.insert(0, str(EXP005))
sys.path.insert(0, str(HERE.parents[2] / "src"))

from metapuzzle.classes import ClassSpec, load_class_spec  # noqa: E402

import gen_classes_v8 as v8  # noqa: E402
import gen_classes_ink as ink  # noqa: E402
import gen_classes_ink_v8 as ink8  # noqa: E402

CLASSES_JSON = EXP005 / "classes.json"
V4_JSON = EXP005 / "classes-v4.json"
OUT = HERE / "classes-v9.json"
OUT_INK = HERE / "classes-ink-v9.json"

ROTS = [0, 90, 180, 270]
# letter -> (march pattern, extra params), as in gen_classes_v4 (s c p d) and v7 (g t)
PATTERNS = {
    "s": ("straight", {}),
    "c": ("corner", {}),
    "p": ("cap", {}),
    "d": ("dot", {}),
    "g": ("diag", {}),
    "t": ("tip", {"height": 0.75}),
}
DOT_LETTER = "d"


def _march(pattern: str, extra: dict) -> dict:
    params = {"pattern": pattern, "roughness": 0.5, "wobble": 0.12}
    params.update(extra)
    return {"primitive": "march_mask", "params": params}


def _s_and_l_layers() -> tuple[list, list]:
    """The S and L layers exactly as classes-v4.json defines them."""
    v4 = json.loads(V4_JSON.read_text(encoding="utf-8"))["classes"]
    return copy.deepcopy(v4["S"]["layers"]), copy.deepcopy(v4["L"]["layers"])


def add_sl_pairs(data: dict) -> dict:
    """Adds <own><nbr><letter> for (own, nbr) in (S, L) and (L, S), for every letter above."""
    classes = data["classes"]
    s_layers, l_layers = _s_and_l_layers()
    tiers = {"S": s_layers, "L": l_layers}
    for own, nbr in (("S", "L"), ("L", "S")):                       # darker first (S before L)
        for letter, (pattern, extra) in PATTERNS.items():
            if letter == DOT_LETTER:
                # <nbr><own>d: nbr is the base, own a dot (as v4's LDd / DLd).
                dot_layers = copy.deepcopy(tiers[own])
                for layer in dot_layers:
                    layer["mask"] = "dot"
                classes[f"{nbr}{own}d"] = {
                    "layers": copy.deepcopy(tiers[nbr]) + dot_layers,
                    "directional": False,
                    "allowed_rotations": list(ROTS),
                    "masks": {"dot": _march("dot", {})},
                }
                continue
            nbr_layers = copy.deepcopy(tiers[nbr])
            for layer in nbr_layers:
                layer["mask"] = "edge"
            classes[f"{own}{nbr}{letter}"] = {
                "layers": copy.deepcopy(tiers[own]) + nbr_layers,
                "directional": False,
                "allowed_rotations": list(ROTS),
                "masks": {"edge": _march(pattern, extra)},
            }
    data["_note"] = ("v9 (011). The 005 v8 class set plus S-L transitions: <S><L><s|c|p|d|g|t> and "
                     "<L><S><s|c|p|d|g|t>. S is the chip tier of classes-v4 (scatter_shapes, cream with "
                     "indigo chips); own layers are the base, nbr layers the mass under 'edge' (dots: "
                     "'dot', nbr base). Built by gen_classes_v9.py from the 005 v8 generators.")
    return data


def build_v9(src: dict) -> dict:
    return add_sl_pairs(v8.build_v8(src))


def build_ink_v9(spec: dict) -> dict:
    """The ink version: a junction is gen_classes_ink_v8.junction_ink, everything else ink.convert."""
    classes = {}
    for name, src in spec["classes"].items():
        is_junction = "p1" in src.get("masks", {})
        classes[name] = ink8.junction_ink(src) if is_junction else ink.convert(src)
    return {
        "_note": ("Ink version of classes-v9.json, generated by gen_classes_v9.py; do not edit by hand. "
                  "The v8 ink classes (gen_classes_ink_v8.py) plus the S-L transitions as march_line "
                  "outlines of their masks."),
        "ref_size": spec.get("ref_size", 100),
        "palette": ink.PALETTE,
        "classes": classes,
    }


def main() -> None:
    src = json.loads(CLASSES_JSON.read_text(encoding="utf-8"))
    data = build_v9(src)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    spec = load_class_spec(OUT)                         # validates every layer, mask and rotation
    ink_data = build_ink_v9(data)
    ClassSpec.from_dict(ink_data).validate()            # raises before anything is written
    OUT_INK.write_text(json.dumps(ink_data, indent=2) + "\n", encoding="utf-8")
    new = sorted(n for n in spec.classes if len(n) == 3 and set(n[:2]) == {"S", "L"})
    v8_n = len(spec.classes) - len(new)
    print(f"{OUT.name}: {len(spec.classes)} classes valid (v8 set {v8_n}, new S-L {len(new)}: {' '.join(new)})")
    print(f"{OUT_INK.name}: {len(ink_data['classes'])} classes valid")


if __name__ == "__main__":
    main()
