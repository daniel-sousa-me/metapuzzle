"""Class specs v12 for experiment 011 (motif layer v6): per-piece variation and a lighter ink motif layer.

Writes pipeline/classes-v12.json (colour) and pipeline/classes-ink-v12.json (ink), validates both, and writes
check sheets to 27x38-v2/pipeline-out-v6/. Built on classes-v10.json (the plain, transition and chip classes),
as v11 was. Changes from v11 (evaluation-v5.md):

  kinds      the motif primitive's new kinds (curl, streak, seed_head, snowflake, chevron, pebbles, cloud_puff,
             sparkle) are used where textures.MOTIF_KINDS lists them; otherwise the v11 substitute is kept
             (a multi-layer composition, or the v11 kind). Which kind each class used is printed and written to
             the spec's _note. cloud_puff keeps rotation none; streak, seed_head and snowflake are drawn at
             scale 0.7 (they are faint at 21 px).
  variation  each regular motif is three classes, <base>_a, _b, _c, at scale factors 0.8, 1.0 and 1.2 (offsets
             scaled too). metapuzzle.classes does not seed a layer's scale (scale is a fixed parameter), so
             scale variation is made by distributing the pieces equally over the three variants. The motif
             primitive does seed the per-layer centre (jitter: uniform +-jitter per axis, from the piece seed
             and the layer index) and the rotation (rotation "any"). Offset per piece is therefore the seeded
             jitter, capped at 0.12 and at the 10% margin (scale/2 + offset + jitter <= 0.40, the v11 rule).
             A single-layer motif takes jitter and rotation; a multi-layer fallback takes neither (its layers
             would scatter apart).
  heroes     the six hero classes are unchanged from v11 (one-off pieces; they keep their look).
  ink        --ink-motifs none|light|full (default light). light: each regular motif is a thin light-grey outline
             (a grey rim of width STROKE, a white body). full: v11's black rim and black details. none: regular
             motifs are plain tier pieces in ink. Ink copies share no seed, so ink motifs have no jitter and no
             rotation (rim and body must line up). Heroes keep v11's full ink.

Run: python3 experiments/011-subjects/pipeline/gen_classes_v12.py [--ink-motifs none|light|full]
"""
from __future__ import annotations

import argparse
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
OUT = HERE / "classes-v12.json"
OUT_INK = HERE / "classes-ink-v12.json"
PREVIEW_DIR = HERE.parents[0] / "27x38-v2" / "pipeline-out-v6"   # check sheets only

ROTS = [0, 90, 180, 270]
MARGIN = 0.10                                  # every mark stays this far from the cell edge (v11 rule)
REACH = 0.5 - MARGIN                           # 0.40: |offset| + scale / 2 + jitter must not exceed it
MAX_JITTER = 0.12                              # per-piece seeded offset, per axis
VARIANTS = (("a", 0.8), ("b", 1.0), ("c", 1.2))  # scale factors, one class per factor
INK_STROKE = ink.STROKE
LIGHT_GREY = "#b3b3b3"
INK_PALETTE = {"white": "#ffffff", "black": "#000000", "grey": LIGHT_GREY}
PEBBLE_XY = [(-0.14, -0.05), (0.13, -0.09), (0.02, 0.12)]          # v11 fallback: three discs, scale 0.22
FAINT = {"streak", "seed_head", "snowflake"}                       # drawn at scale 0.7 (faint at 21 px)
NO_ROTATE = {"cloud_puff"}                                         # rotation none
INK_MOTIFS = ("none", "light", "full")


def part(kind: str, fill: str, ground: str, scale: float, dx: float = 0.0, dy: float = 0.0) -> dict:
    """One motif part: kind, fill colour, ground colour (palette[0], used for details), scale, offset."""
    return {"kind": kind, "fill": fill, "ground": ground, "scale": scale, "offset": [dx, dy]}


def _six_arms() -> list:
    arms = [part("disc", "pale_blue", "cream", 0.16, 0.2 * math.cos(math.radians(a)), 0.2 * math.sin(math.radians(a)))
            for a in range(0, 360, 60)]
    return arms + [part("disc", "pale_blue", "cream", 0.20)]


# Motif code -> (new kind, scale, fill, ground) if the kind exists; else the v11 substitute parts below.
# Each motif: (base tier, preferred kind, scale, fill, ground, v11 substitute parts).
REGULAR = {
    "D_s": ("D", "sparkle", 0.46, "cream", "indigo", [part("star", "cream", "indigo", 0.46)]),
    "D_p": ("D", "pebbles", 0.56, "pale_blue", "indigo", [part("disc", "pale_blue", "indigo", 0.22, *xy) for xy in PEBBLE_XY]),
    "D_k": ("D", "streak", 0.70, "cream", "indigo", [part("drop", "cream", "indigo", 0.56)]),
    "D_v": ("D", "chevron", 0.66, "cream", "indigo", [part("silhouette_bird", "cream", "indigo", 0.66)]),
    "M_s": ("M", "sparkle", 0.44, "cream", "olive", [part("star", "cream", "olive", 0.44)]),
    "M_c": ("M", "curl", 0.56, "cream", "olive", [part("ring", "cream", "olive", 0.50)]),
    "M_l": ("M", "leaf", 0.56, "rust", "olive", [part("leaf", "rust", "olive", 0.56)]),
    "M_d": ("M", "seed_head", 0.70, "cream", "olive", [part("flower", "cream", "olive", 0.56)]),
    "L_p": ("L", "pebbles", 0.56, "indigo", "cream", [part("disc", "indigo", "cream", 0.22, *xy) for xy in PEBBLE_XY]),
    "L_v": ("L", "chevron", 0.66, "indigo", "cream", [part("silhouette_bird", "indigo", "cream", 0.66)]),
    "L_u": ("L", "cloud_puff", 0.60, "pale_blue", "cream",
            [part("disc", "pale_blue", "cream", 0.36, -0.12, 0.04), part("disc", "pale_blue", "cream", 0.36, 0.08, -0.06),
             part("disc", "pale_blue", "cream", 0.26, 0.13, 0.10)]),
    "L_f": ("L", "snowflake", 0.70, "pale_blue", "cream", _six_arms()),
}
# Heroes: unchanged from v11 (base layers, parts). The piece class is the one the motif map gives.
HEROES = {
    "H_I": ("L", [part("hull", "ochre", "cream", 0.60, 0.0, 0.08)]),
    "H_O": ("L", [part("ring", "olive", "cream", 0.50)]),
    "H_N": ("M", [part("drop", "indigo", "olive", 0.34)]),
    "H_G": ("DLc", [part("star", "indigo", "cream", 0.30, 0.10, -0.10)]),
    "H_E": ("MDd", [part("disc", "ochre", "indigo", 0.22)]),
    "H_Y": ("LDd", [part("disc", "cream", "indigo", 0.20)]),
}


def available_kinds() -> set:
    """Motif kinds the installed metapuzzle provides (read at generation time)."""
    try:
        from metapuzzle import textures
        return set(textures.MOTIF_KINDS)
    except Exception:                       # keep the v11 substitutes if the module cannot be read
        return set()


def regular_parts(name: str, kinds: set) -> tuple[list, str]:
    """Parts of a regular motif class and the kind it used ('v11' for the substitute)."""
    _, kind, scale, fill, ground, fallback = REGULAR[name]
    if kind in kinds:
        return [part(kind, fill, ground, scale)], kind
    return copy.deepcopy(fallback), "v11"


def variant_factor(name: str, tag: str) -> float:
    """Scale factor of a variant: 0.8, 1.0 or 1.2, capped so the largest variant's colour motif and its ink rim
    (scale + 2 STROKE) both stay within the 10% margin (scale <= 2 * REACH - 2 STROKE)."""
    f = dict(VARIANTS)[tag]
    return min(f, (2 * REACH - 2 * INK_STROKE) / REGULAR[name][2])


def variant_parts(parts: list, f: float) -> list:
    """Scale every part by f and move its offset by f (composition kept for multi-part motifs)."""
    return [part(p["kind"], p["fill"], p["ground"], round(p["scale"] * f, 4),
                 round(p["offset"][0] * f, 4), round(p["offset"][1] * f, 4)) for p in parts]


def jitter_for(parts: list) -> float:
    """Seeded per-piece offset for a single-part motif: as large as the margin allows, at most MAX_JITTER."""
    if len(parts) != 1:
        return 0.0
    p = parts[0]
    room = REACH - (math.hypot(*p["offset"]) + p["scale"] / 2.0)
    return round(max(0.0, min(MAX_JITTER, room - 1e-6)), 4)


def motif_layer(p: dict, jitter: float, rotation: str) -> dict:
    """Colour motif layer. palette = [ground, fill, ground]; the layer's seed gives its own jitter and rotation."""
    return {"primitive": "motif", "palette": [p["ground"], p["fill"], p["ground"]], "background": False,
            "params": {"kind": p["kind"], "scale": p["scale"], "jitter": jitter, "rotation": rotation,
                       "offset": list(p["offset"])}}


def ink_motif_layers(parts: list, mode: str) -> list:
    """Ink layers for a regular motif (mode light or full), or none. Jitter and rotation are 0 and none, so
    the rim and body (which draw from different layer seeds) line up."""
    if mode == "none":
        return []
    out = []
    for p in parts:
        shape = {"kind": p["kind"], "jitter": 0.0, "rotation": "none", "offset": list(p["offset"])}
        rim_scale = round(p["scale"] + 2 * INK_STROKE, 4)
        if mode == "light":
            out.append({"primitive": "motif", "palette": ["white", "grey", "white"], "background": False,
                        "params": {**shape, "scale": rim_scale}})
            out.append({"primitive": "motif", "palette": ["white", "white", "white"], "background": False,
                        "params": {**shape, "scale": p["scale"]}})
        else:
            out.append({"primitive": "motif", "palette": ["white", "black", "white"], "background": False,
                        "params": {**shape, "scale": rim_scale}})
            out.append({"primitive": "motif", "palette": ["black", "white", "black"], "background": False,
                        "params": {**shape, "scale": p["scale"]}})
    return out


def hero_ink_layers(parts: list) -> list:
    """v11's full ink for heroes: black rim, white body with black details."""
    return ink_motif_layers(parts, "full")


def variant_names():
    for name in REGULAR:
        for tag, _ in VARIANTS:
            yield name, f"{name}_{tag}", dict(VARIANTS)[tag]


def build_colour(v10: dict, kinds: set, used: dict) -> dict:
    data = copy.deepcopy(v10)
    classes = data["classes"]
    for name, cls_name, _ in variant_names():
        base = REGULAR[name][0]
        parts, kind = regular_parts(name, kinds)
        used.setdefault(name, kind)
        vparts = variant_parts(parts, variant_factor(name, cls_name[-1]))
        j = jitter_for(vparts)
        rot = "none" if (len(vparts) != 1 or kind in NO_ROTATE) else "any"
        layers = [motif_layer(p, j, rot) for p in vparts]
        classes[cls_name] = {"layers": copy.deepcopy(classes[base]["layers"]) + layers,
                             "directional": False, "allowed_rotations": list(ROTS)}
    for name, (base, parts) in HEROES.items():
        src = classes[base]
        cls = {"layers": copy.deepcopy(src["layers"]) + [motif_layer(p, 0.0, "none") for p in parts],
               "directional": False, "allowed_rotations": list(ROTS)}
        if "masks" in src:                         # heroes on transition pieces keep the mask
            cls["masks"] = copy.deepcopy(src["masks"])
        classes[name] = cls
    data["_note"] = ("v12 (011, motif layer v6). The v10 set, plus three variant classes per regular motif "
                     "(<base>_a/_b/_c at scale 0.8, 1.0, 1.2: scale is not seeded in metapuzzle, so the pieces are "
                     "split equally over the variants), each with a seeded per-piece jitter (<= 0.12, capped by the "
                     "10% margin) and seeded rotation (any; none for cloud_puff). Motif kinds: "
                     + ", ".join(f"{k} {v}" for k, v in sorted(used.items())) + ". Six hero classes H_I H_O H_N H_G "
                     "H_E H_Y as in v11. Built by gen_classes_v12.py from classes-v10.json.")
    return data


def build_ink(v10_ink: dict, mode: str, kinds: set) -> dict:
    classes = copy.deepcopy(v10_ink["classes"])
    for name, cls_name, _ in variant_names():
        parts, _ = regular_parts(name, kinds)
        vparts = variant_parts(parts, variant_factor(name, cls_name[-1]))
        layers = [dict(ink.PLAIN_BG)] + ink_motif_layers(vparts, mode)
        classes[cls_name] = {"layers": layers, "directional": False, "allowed_rotations": list(ROTS)}
    for name, (base, parts) in HEROES.items():
        src = classes[base]
        layers = [dict(ink.PLAIN_BG)] + hero_ink_layers(parts)
        if base in ("DLc", "MDd", "LDd"):           # heroes on transition pieces keep the transition's ink line
            layers = copy.deepcopy(src["layers"]) + hero_ink_layers(parts)
        cls = {"layers": layers, "directional": False, "allowed_rotations": list(ROTS)}
        if "masks" in src:
            cls["masks"] = copy.deepcopy(src["masks"])
        classes[name] = cls
    return {
        "_note": (f"Ink version of classes-v12.json, generated by gen_classes_v12.py (--ink-motifs {mode}); do not "
                  "edit by hand. Regular motifs: " + {"none": "omitted (plain tier pieces).",
                                                     "light": "thin light-grey outlines (grey rim, white body).",
                                                     "full": "black outline and black details."}[mode]
                  + " Heroes: black rim and black details as in v11, on transitions with the transition ink line."),
        "ref_size": v10_ink.get("ref_size", 100),
        "palette": INK_PALETTE,
        "classes": classes,
    }


def check_margins(data: dict) -> list:
    """Analytic check: every motif layer's enclosing circle (offset, scale and jitter) stays inside the 10% margin."""
    bad = []
    for name, cls in data["classes"].items():
        if name in HEROES:
            base = HEROES[name][0]
        elif name.rpartition("_")[0] in REGULAR:
            base = REGULAR[name.rpartition("_")[0]][0]
        else:                                  # v10 classes are not this script's to check
            continue
        n_base = len(data["classes"][base]["layers"])
        for layer in cls["layers"][n_base:]:   # only the motif layers appended here
            if layer["primitive"] != "motif":
                continue
            p = layer["params"]
            reach = math.hypot(*p.get("offset", [0.0, 0.0])) + p["scale"] / 2.0 + p.get("jitter", 0.0)
            if reach > REACH + 1e-9:
                bad.append((name, p["kind"], round(reach, 3)))
    return bad


def check_render(spec: ClassSpec, data: dict, names: list, seeds=range(1, 5), size: float = 400.0) -> list:
    """Rendered check: extent of the motif fill colours in the piece (worst clearance as a fraction of size)."""
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--ink-motifs", choices=INK_MOTIFS, default="light",
                    help="ink rendering of the regular motifs: none (omitted), light (grey outline, default), full (v11)")
    args = ap.parse_args()
    v10 = json.loads(V10.read_text(encoding="utf-8"))
    v10_ink = json.loads(V10_INK.read_text(encoding="utf-8"))
    kinds = available_kinds()
    used: dict = {}
    data = build_colour(v10, kinds, used)
    bad = check_margins(data)
    if bad:
        raise SystemExit(f"motif marks leave the 10% margin: {bad}")
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    spec = load_class_spec(OUT)                      # validates every layer, mask and rotation
    ink_data = build_ink(v10_ink, args.ink_motifs, kinds)
    ClassSpec.from_dict(ink_data).validate()         # raises before anything is written
    OUT_INK.write_text(json.dumps(ink_data, indent=2) + "\n", encoding="utf-8")

    n_reg = len(REGULAR) * len(VARIANTS)
    print(f"{OUT.name}: {len(spec.classes)} classes valid (v10 {len(v10['classes'])}, + regular {n_reg} "
          f"({len(REGULAR)} motifs x {len(VARIANTS)} variants), + heroes {len(HEROES)})")
    print(f"{OUT_INK.name}: {len(ink_data['classes'])} classes valid (--ink-motifs {args.ink_motifs})")
    print("motif kinds used:", ", ".join(f"{k} {v}" for k, v in sorted(used.items())))
    print("margin check (analytic, |offset| + scale/2 + jitter <= 0.40): ok")
    for name in REGULAR:
        js = [data["classes"][f"{name}_{tag}"]["layers"][-1]["params"]["jitter"] for tag, _ in VARIANTS]
        sc = [data["classes"][f"{name}_{tag}"]["layers"][-1]["params"]["scale"] for tag, _ in VARIANTS]
        print(f"  {name} scale a/b/c {sc} jitter a/b/c {js}")
    print("rendered extents and motif pixel fractions (worst clearance as fraction of side; need >= 0.10):")
    names = [c for _, c, _ in variant_names()]
    for name, worst, frac in check_render(spec, data, names[:: len(VARIANTS)]):
        flag = "ok" if worst >= MARGIN - 0.01 else "FAIL"
        print(f"  {name:4s} worst clearance {worst:.3f}  motif pixels {frac:.3f}  {flag}")
    print("hero fractions (motif colour pixels, transitions included in the colour count):")
    for name in HEROES:
        rows = check_render(spec, data, [name])
        print(f"  {name:4s} motif pixels {rows[0][2]:.4f}")
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    sheet_names = names + list(HEROES)
    sheet = ClassSpec(palette=spec.palette, classes={k: spec.classes[k] for k in sheet_names}, ref_size=spec.ref_size)
    print(sheet.contact_sheet(PREVIEW_DIR / "contact-sheet-v12.png", cell=96, per_class=3))
    ink_sheet = ClassSpec.from_dict({**ink_data, "classes": {k: ink_data["classes"][k] for k in sheet_names}})
    print(ink_sheet.contact_sheet(PREVIEW_DIR / "contact-sheet-ink-v12.png", cell=96, per_class=3))


if __name__ == "__main__":
    main()
