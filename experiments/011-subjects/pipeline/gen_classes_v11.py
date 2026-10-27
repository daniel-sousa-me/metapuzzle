"""Class specs v11 for experiment 011: the v10 set plus motif classes and hero classes.

Writes pipeline/classes-v11.json (colour) and pipeline/classes-ink-v11.json (ink), validates both, checks
every motif against the 10% margin, and writes check sheets to 27x38-v2/pipeline-out-v5/.

v11 keeps every v10 class (the chip sub-classes Lr Lb Lo Lx, Mr Mb Mc stay: they take the plain cells that carry
no motif, as docs/design/10-motif-vocabulary.md suggests). A motif class is the tier's plain recipe (the v10 D,
M or L layers) plus one or more motif layers, each a single ``motif`` primitive with jitter 0 and rotation none:

  regular (plain D, M, L; 12 classes, named <tier>_<code>):
    D_s star (cream)        star, 4-point sparkle drawn with the 5-point star kind
    D_p pebbles (pale blue) three discs
    D_k streak (cream)      drop: teardrop, head at the bottom
    D_v chevron (cream)     silhouette_bird: the two arches of a V
    M_s star (cream)
    M_c curl (cream)        ring: the nearest kind to a spiral
    M_l leaf (rust)         leaf with midrib
    M_d seed head (cream)   flower: radial burst, centre in the ground colour
    L_p pebbles (navy)      three discs
    L_v chevron (navy)      silhouette_bird
    L_u cloud puff (pale)   three overlapping discs
    L_f snowflake (pale)    six arm discs and a centre disc

  heroes (6 classes, named H_<code>; the piece class is the one the motif map gives):
    H_I amber wedge  on plain L: hull (ochre)
    H_O crater ring  on plain L: ring (olive)
    H_N beak or nose on plain M: drop (navy)
    H_G catchlight   on the D-L convex corner DLc: star (navy) on the cream L part (the D corner is too small)
    H_E amber eye    on the D-in-M dot MDd: disc (ochre) on the dot
    H_Y eye glint    on the D-in-L dot LDd: disc (cream) on the dot

Every mark has |offset| + scale / 2 <= 0.40 (a 10% margin on every side, the rule of doc 10). Pebbles and
the snowflake are the only classes with several motif layers.

The ink set gives each motif or hero a black outline: a black rim (scale + 2 STROKE) under a white body with
black details (gen_classes_ink.motif), per layer, with no jitter and no rotation so the two copies line up.
Heroes on transition pieces keep the transition's ink lines and mask.

Run: python3 experiments/011-subjects/pipeline/gen_classes_v11.py
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP005 = HERE.parents[1] / "005-hybrid-tones"
sys.path.insert(0, str(EXP005))
sys.path.insert(0, str(HERE.parents[2] / "src"))

from metapuzzle.classes import ClassSpec, load_class_spec  # noqa: E402

import gen_classes_v6 as v6  # noqa: E402
import gen_classes_ink as ink  # noqa: E402

V10 = HERE / "classes-v10.json"
V10_INK = HERE / "classes-ink-v10.json"
OUT = HERE / "classes-v11.json"
OUT_INK = HERE / "classes-ink-v11.json"
PREVIEW_DIR = HERE.parents[0] / "27x38-v2" / "pipeline-out-v5"   # check sheets only

ROTS = [0, 90, 180, 270]
MARGIN = 0.10                                  # every mark stays this far from the cell edge
INK_STROKE = ink.STROKE
PEBBLE_XY = [(-0.14, -0.05), (0.13, -0.09), (0.02, 0.12)]          # three dots, scale 0.22


def part(kind: str, fill: str, ground: str, scale: float, dx: float = 0.0, dy: float = 0.0) -> dict:
    """One motif layer: kind, fill colour, ground colour (palette[0], used for details), scale, offset."""
    return {"kind": kind, "fill": fill, "ground": ground, "scale": scale, "offset": [dx, dy]}


def _six_arms() -> list:
    arms = [part("disc", "pale_blue", "cream", 0.16, 0.2 * math.cos(math.radians(a)), 0.2 * math.sin(math.radians(a)))
            for a in range(0, 360, 60)]
    return arms + [part("disc", "pale_blue", "cream", 0.20)]


# name -> (base layers taken from: "D", "M", "L" or a transition code, motif layers)
REGULAR = {
    "D_s": ("D", [part("star", "cream", "indigo", 0.46)]),
    "D_p": ("D", [part("disc", "pale_blue", "indigo", 0.22, *xy) for xy in PEBBLE_XY]),
    "D_k": ("D", [part("drop", "cream", "indigo", 0.56)]),
    "D_v": ("D", [part("silhouette_bird", "cream", "indigo", 0.66)]),
    "M_s": ("M", [part("star", "cream", "olive", 0.44)]),
    "M_c": ("M", [part("ring", "cream", "olive", 0.50)]),
    "M_l": ("M", [part("leaf", "rust", "olive", 0.56)]),
    "M_d": ("M", [part("flower", "cream", "olive", 0.56)]),
    "L_p": ("L", [part("disc", "indigo", "cream", 0.22, *xy) for xy in PEBBLE_XY]),
    "L_v": ("L", [part("silhouette_bird", "indigo", "cream", 0.66)]),
    "L_u": ("L", [part("disc", "pale_blue", "cream", 0.36, -0.12, 0.04),
                  part("disc", "pale_blue", "cream", 0.36, 0.08, -0.06),
                  part("disc", "pale_blue", "cream", 0.26, 0.13, 0.10)]),
    "L_f": ("L", _six_arms()),
}
HEROES = {
    "H_I": ("L", [part("hull", "ochre", "cream", 0.60, 0.0, 0.08)]),
    "H_O": ("L", [part("ring", "olive", "cream", 0.50)]),
    "H_N": ("M", [part("drop", "indigo", "olive", 0.34)]),
    "H_G": ("DLc", [part("star", "indigo", "cream", 0.30, 0.10, -0.10)]),
    "H_E": ("MDd", [part("disc", "ochre", "indigo", 0.22)]),
    "H_Y": ("LDd", [part("disc", "cream", "indigo", 0.20)]),
}
MOTIF_NAMES = list(REGULAR) + list(HEROES)


def motif_layer(p: dict) -> dict:
    """Colour motif layer. palette = [ground, fill, ground]; jitter 0, rotation none: the glyph is exact."""
    return {"primitive": "motif", "palette": [p["ground"], p["fill"], p["ground"]], "background": False,
            "params": {"kind": p["kind"], "scale": p["scale"], "jitter": 0.0, "rotation": "none",
                       "offset": list(p["offset"])}}


def ink_layers(parts: list) -> list:
    """Ink motif layers: per part a black rim (fill black) and a white body with black details."""
    out = []
    for p in parts:
        shape = {"kind": p["kind"], "jitter": 0.0, "rotation": "none", "offset": list(p["offset"])}
        out.append({"primitive": "motif", "palette": ["white", "black", "white"], "background": False,
                    "params": {**shape, "scale": round(p["scale"] + 2 * INK_STROKE, 4)}})
        out.append({"primitive": "motif", "palette": ["black", "white", "black"], "background": False,
                    "params": {**shape, "scale": p["scale"]}})
    return out


def build_colour(v10: dict) -> dict:
    data = copy.deepcopy(v10)
    classes = data["classes"]
    for name, (base, parts) in {**REGULAR, **HEROES}.items():
        src = classes[base]
        cls = {"layers": copy.deepcopy(src["layers"]) + [motif_layer(p) for p in parts],
               "directional": False, "allowed_rotations": list(ROTS)}
        if "masks" in src:                              # heroes on transition pieces keep the mask
            cls["masks"] = copy.deepcopy(src["masks"])
        classes[name] = cls
    data["_note"] = ("v11 (011). The v10 set plus 12 motif classes D_s D_p D_k D_v M_s M_c M_l M_d L_p L_v L_u L_f "
                     "(plain tier recipe + motif layers) and 6 hero classes H_I H_O H_N H_G H_E H_Y (amber wedge, "
                     "crater ring, beak, catchlight on DLc, amber eye on MDd, eye glint on LDd). Built by "
                     "gen_classes_v11.py from classes-v10.json.")
    return data


def build_ink(v10_ink: dict) -> dict:
    classes = copy.deepcopy(v10_ink["classes"])
    for name, (base, parts) in {**REGULAR, **HEROES}.items():
        src = classes[base]
        if base in ("D", "M", "L"):
            layers = [dict(ink.PLAIN_BG)]
        else:
            layers = copy.deepcopy(src["layers"])
        cls = {"layers": layers + ink_layers(parts), "directional": False, "allowed_rotations": list(ROTS)}
        if "masks" in src:
            cls["masks"] = copy.deepcopy(src["masks"])
        classes[name] = cls
    return {
        "_note": ("Ink version of classes-v11.json, generated by gen_classes_v11.py; do not edit by hand. The v10 ink "
                  "classes plus the motif and hero classes: each motif a black outline (rim) round a white body with "
                  "black details, at its colour site with no jitter and no rotation. Heroes on transition pieces keep "
                  "the transition's ink line and mask."),
        "ref_size": v10_ink.get("ref_size", 100),
        "palette": ink.PALETTE,
        "classes": classes,
    }


def check_margins(data: dict) -> list:
    """Analytic check: every motif layer's enclosing circle, offset included, stays inside the 10% margin."""
    bad = []
    for name, (_, parts) in {**REGULAR, **HEROES}.items():
        for p in parts:
            reach = math.hypot(*p["offset"]) + p["scale"] / 2.0
            if reach > 0.5 - MARGIN + 1e-9:
                bad.append((name, p["kind"], round(reach, 3)))
    return bad


def check_render(spec: ClassSpec, data: dict, names: list, seeds=range(1, 5), size: float = 400.0) -> list:
    """Rendered check for classes without transitions: extent of the motif fill colours in the piece."""
    import numpy as np
    rows = []
    draw = spec.drawer()
    for name in names:
        fills = sorted({l["palette"][1] for l in data["classes"][name]["layers"]
                        if l["primitive"] == "motif" and not l.get("background")})
        rgb = [np.array(v6._hex(spec.palette[f])) for f in fills]
        worst, frac = 1.0, []
        for s in seeds:
            img = v6._render_piece(draw, name, s, size)
            hit = np.zeros(img.shape[:2], bool)
            for c in rgb:
                hit |= np.abs(img - c).max(axis=2) <= 20
            ys, xs = np.nonzero(hit)
            if xs.size == 0:
                worst = 0.0
                continue
            clear = min(xs.min(), ys.min(), size - 1 - xs.max(), size - 1 - ys.max()) / size
            worst = min(worst, clear)
            frac.append(hit.mean())
        rows.append((name, worst, float(np.mean(frac)) if frac else 0.0))
    return rows


def main() -> None:
    v10 = json.loads(V10.read_text(encoding="utf-8"))
    v10_ink = json.loads(V10_INK.read_text(encoding="utf-8"))
    bad = check_margins(v10)
    if bad:
        raise SystemExit(f"motif marks leave the 10% margin: {bad}")
    data = build_colour(v10)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    spec = load_class_spec(OUT)                      # validates every layer, mask and rotation
    ink_data = build_ink(v10_ink)
    ClassSpec.from_dict(ink_data).validate()         # raises before anything is written
    OUT_INK.write_text(json.dumps(ink_data, indent=2) + "\n", encoding="utf-8")

    print(f"{OUT.name}: {len(spec.classes)} classes valid (v10 {len(v10['classes'])}, + motifs {len(REGULAR)}, "
          f"+ heroes {len(HEROES)})")
    print(f"{OUT_INK.name}: {len(ink_data['classes'])} classes valid")
    print("margin check (analytic, |offset| + scale/2 <= 0.40): ok")
    plain = [n for n in REGULAR]
    print("rendered extents and motif pixel fractions (worst clearance as fraction of side; need >= 0.10):")
    for name, worst, frac in check_render(spec, data, plain):
        flag = "ok" if worst >= MARGIN - 0.01 else "FAIL"
        print(f"  {name:4s} worst clearance {worst:.3f}  motif pixels {frac:.3f}  {flag}")
    print("hero fractions (motif colour pixels, transitions included in the colour count):")
    for name in HEROES:
        rows = check_render(spec, data, [name])
        print(f"  {name:4s} motif pixels {rows[0][2]:.4f}")
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    names = list(REGULAR) + list(HEROES)
    sheet = ClassSpec(palette=spec.palette, classes={k: spec.classes[k] for k in names}, ref_size=spec.ref_size)
    print(sheet.contact_sheet(PREVIEW_DIR / "contact-sheet-v11.png", cell=96, per_class=3))
    ink_sheet = ClassSpec.from_dict({**ink_data, "classes": {k: ink_data["classes"][k] for k in names}})
    print(ink_sheet.contact_sheet(PREVIEW_DIR / "contact-sheet-ink-v11.png", cell=96, per_class=3))


if __name__ == "__main__":
    main()
