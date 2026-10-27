"""Class specs v10 for experiment 011: the v9 set plus chip sub-classes for L and M.

Writes pipeline/classes-v10.json (colour) and pipeline/classes-ink-v10.json (ink), validates both, and
writes check sheets (contact sheet, chip field, pixel fractions printed) to the preview folder.

Two changes to v9, both in the colour set:
  1. Plain L and M take the calm recipe of experiment 005 v6 (one flat ground, one sparse sand fleck),
     in place of the busy dab textures of v4. Every layer that carries the old L or M base is replaced in
     place (layers of transitions, junctions, motifs, W and the S-L pairs alike); masks, backgrounds and
     the rest of each class are untouched. The chip sub-classes need the same ground as the plain tier.
  2. Chip sub-classes, with the v6 recipes (gen_classes_v6.SUB, chips from gen_classes_v6.chip_layers):
       light, cream ground:  Lr 3 rust, Lb 4 pale blue, Lo 2 olive, Lx one rust + one blue + one olive
       mid, olive ground:    Mr 3 rust, Mb 3 pale blue, Mc 2 cream
     No sub-class has transitions. The ink set adds the same seven classes: a white base, and each chip as
     a black outline (a black rim with a white body, as gen_classes_ink.motif does), at the chip's site
     with no jitter and no rotation so the two copies line up.

Plain L and M (the calm variant) stay as they are in the set: one flat ground, one sand fleck.

Run: python3 experiments/011-subjects/pipeline/gen_classes_v10.py
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

import gen_classes_v6 as v6  # noqa: E402
import gen_classes_ink as ink  # noqa: E402

V9 = HERE / "classes-v9.json"
V9_INK = HERE / "classes-ink-v9.json"
OUT = HERE / "classes-v10.json"
OUT_INK = HERE / "classes-ink-v10.json"
PREVIEW_DIR = HERE.parents[0] / "27x38-v2" / "pipeline-out-v4"   # check sheets only

ROTS = [0, 90, 180, 270]
CALM_L = v6.chip_layers(*v6.LIGHT_PLAIN)[0]     # cream, one sand fleck, background
CALM_M = v6.chip_layers(*v6.MID_PLAIN)[0]       # olive, one sand fleck, background
SUB_NAMES = ["Lr", "Lb", "Lo", "Lx", "Mr", "Mb", "Mc"]
INK_STROKE = ink.STROKE                          # the same line width as the ink outlines


def _base_key(layer: dict) -> tuple:
    return layer["primitive"], tuple(layer["palette"]), json.dumps(layer["params"], sort_keys=True)


def _is_base(layer: dict, old: dict) -> bool:
    return _base_key(layer) == _base_key(old)


def _calm(layer: dict, new: dict) -> dict:
    """The calm base in place of an old base layer; mask and background flag kept."""
    out = dict(layer)
    out.update({"primitive": new["primitive"], "palette": list(new["palette"]),
                "params": copy.deepcopy(new["params"])})
    return out


def calm_base(v9: dict) -> dict:
    """Replace every old L and M base layer by the calm one. Returns the counts replaced."""
    old_L = v9["classes"]["L"]["layers"][0]
    old_M = v9["classes"]["M"]["layers"][0]
    counts = {"L": 0, "M": 0}
    for name, cls in v9["classes"].items():
        for i, layer in enumerate(cls["layers"]):
            if _is_base(layer, old_L):
                cls["layers"][i] = _calm(layer, CALM_L)
                counts["L"] += 1
            elif _is_base(layer, old_M):
                cls["layers"][i] = _calm(layer, CALM_M)
                counts["M"] += 1
    return counts


def sub_class(ground: str, chips: list) -> dict:
    return {"layers": v6.chip_layers(ground, chips), "directional": False,
            "allowed_rotations": list(ROTS)}


def build_v10(v9: dict) -> tuple[dict, dict]:
    v6._check_sites()
    data = copy.deepcopy(v9)
    counts = calm_base(data)
    for name in SUB_NAMES:
        ground, chips = v6.SUB[name]
        data["classes"][name] = sub_class(ground, chips)
    data["_note"] = ("v10 (011). The v9 set with calm plain L and M (experiment 005 v6 recipe: flat ground, one "
                     "sand fleck), used in every class that carried the old L or M base. Chip sub-classes "
                     "Lr Lb Lo Lx (cream ground) and Mr Mb Mc (olive ground) from 005 v6: fleck motif chips, "
                     "scale 0.125, inset 10%. Built by gen_classes_v10.py from classes-v9.json.")
    return data, counts


def ink_chip(ox: float, oy: float) -> list:
    """A chip as a black outline: a black rim (scale + 2 STROKE) under a white body (gen_classes_ink.motif)."""
    shared = {"kind": "fleck", "rotation": "none", "jitter": 0.0, "offset": [ox, oy]}
    rim = {"primitive": "motif", "palette": ["white", "black", "white"], "background": False,
           "params": {**shared, "scale": round(v6.CHIP_SCALE + 2 * INK_STROKE, 4)}}
    body = {"primitive": "motif", "palette": ["black", "white", "black"], "background": False,
            "params": {**shared, "scale": v6.CHIP_SCALE}}
    return [rim, body]


def ink_sub_class(chips: list) -> dict:
    layers = [dict(ink.PLAIN_BG)]
    for _, site in chips:
        layers += ink_chip(*v6.SITES[site])
    return {"layers": layers, "directional": False, "allowed_rotations": list(ROTS)}


def build_ink(v9_ink: dict) -> dict:
    classes = copy.deepcopy(v9_ink["classes"])
    for name in SUB_NAMES:
        ground, chips = v6.SUB[name]
        classes[name] = ink_sub_class(chips)
    return {
        "_note": ("Ink version of classes-v10.json, generated by gen_classes_v10.py; do not edit by hand. "
                  "The v9 ink classes (plain L and M white, as before) plus the chip sub-classes Lr Lb Lo Lx "
                  "and Mr Mb Mc: a white base and each chip as a black outline at its v6 site."),
        "ref_size": v9_ink.get("ref_size", 100),
        "palette": ink.PALETTE,
        "classes": classes,
    }


def check_inset(spec: ClassSpec) -> None:
    """Colour sub-classes: every chip stays inside the 10% inset (v6 check)."""
    rows = v6.check_inset(spec, ["L", "Lr", "Lb", "Lo", "Lx", "M", "Mr", "Mb", "Mc"])
    worst = min(w for _, w, _ in rows)
    for name, w, frac in rows:
        flag = "ok" if w >= v6.INSET - 1e-9 else "FAIL"
        print(f"  {name:3s} worst clearance {w:.3f}  chip pixels {frac:.3f}  {flag}")
    if worst < v6.INSET - 1e-9:
        raise SystemExit("a chip leaves the inset")


def main() -> None:
    v9 = json.loads(V9.read_text(encoding="utf-8"))
    v9_ink = json.loads(V9_INK.read_text(encoding="utf-8"))
    data, counts = build_v10(v9)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    spec = load_class_spec(OUT)                      # validates every layer, mask and rotation
    ink_data = build_ink(v9_ink)
    ClassSpec.from_dict(ink_data).validate()         # raises before anything is written
    OUT_INK.write_text(json.dumps(ink_data, indent=2) + "\n", encoding="utf-8")

    print(f"{OUT.name}: {len(spec.classes)} classes valid (v9 {len(v9['classes'])}, + sub-classes {len(SUB_NAMES)}); "
          f"calm base replaced in {counts['L']} L layers and {counts['M']} M layers")
    print(f"{OUT_INK.name}: {len(ink_data['classes'])} classes valid")
    print("inset check (clearance as fraction of side; must be >= 0.10):")
    check_inset(spec)
    shown = ["L", "Lr", "Lb", "Lo", "Lx", "M", "Mr", "Mb", "Mc"]
    fracs = v6.chip_colour_fractions(spec, shown, spec.palette)
    print("chip colour pixel fractions (mean of 4 seeds):")
    for name, d in fracs.items():
        print(f"  {name:3s} {({c: v for c, v in d.items() if v > 0.0005})}")
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    sub = ClassSpec(palette=spec.palette, classes={k: spec.classes[k] for k in shown}, ref_size=spec.ref_size)
    print(sub.contact_sheet(PREVIEW_DIR / "contact-sheet-v10.png", cell=64, per_class=4))
    ink_sub = ClassSpec.from_dict({**ink_data, "classes": {k: ink_data["classes"][k] for k in shown}})
    print(ink_sub.contact_sheet(PREVIEW_DIR / "contact-sheet-ink-v10.png", cell=64, per_class=4))
    print(v6.write_chip_field(spec, PREVIEW_DIR / "chip-field-v10.png"))


if __name__ == "__main__":
    main()
