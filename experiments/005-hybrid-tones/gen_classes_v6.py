"""Generate the v6 class spec for experiment 005: chip-signature sub-classes.

Copied from gen_classes_v4.py, with the light and mid tiers rebuilt.

Plain tiers. L and M are now calm grounds (one flat cream or olive colour) with very
sparse neutral chips (one sand fleck). The v4 dab textures were too busy for the chips
to read at 64 px. D and S are unchanged from v4. W is M plus cream lenses, as in v4.

Sub-classes (chip signature only, same ground as the plain tier):
  light, cream ground:  Lr 3 rust, Lb 4 pale blue, Lo 2 olive, Lx one rust + one blue + one olive
  mid, olive ground:    Mr 3 rust, Mb 3 pale blue, Mc 2 cream

Chips are ``motif`` layers with kind ``fleck``, ``scale`` 0.125 (enclosing diameter
about 1/8 of the piece side), ``rotation`` "any", and a per-chip ``offset`` plus a
small ``jitter``. The offsets are chosen so that every chip, jitter included, lies
inside a 10% inset: |offset| + jitter <= 0.5 - INSET - CHIP_SCALE / 2. ``motif``'s own
8% clamp then never acts. ``check_inset`` renders the pieces and confirms it.
``scatter_shapes`` and ``dabs`` have no inset, so they are not used for chips.

Transitions are unchanged in form. Every ordered pair of D/M/L/W gets four march_mask
transitions (s, c, i, p), built from the plain tiers. Sub-classes get no transitions,
so the transition count is the same as in v4. The D/L pair gets two dots. Six motif
classes sit on L.

Writes classes-v6.json, validates it, checks the inset, and renders contact-sheet-v6.png
(cell 64, 4 seeds per class) and chip-field-v6.png (3x3 mix of L, Lr, Lb, Lo).
Notes are in classes-v6-NOTES.md.

Run: python3 experiments/005-hybrid-tones/gen_classes_v6.py
"""
from __future__ import annotations

import copy
import io
import json
import random
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image

from metapuzzle.classes import ClassSpec, load_class_spec

HERE = Path(__file__).resolve().parent
SRC = HERE / "classes.json"
OUT = HERE / "classes-v6.json"
CONTACT_PNG = HERE / "contact-sheet-v6.png"
FIELD_PNG = HERE / "chip-field-v6.png"

ROTS = [0, 90, 180, 270]
PATTERNS = {"s": "straight", "c": "corner", "i": "corner_in", "p": "cap"}

# Chips (motif fleck). A chip's enclosing circle must stay inside the 10% inset.
INSET = 0.10
CHIP_SCALE = 0.125          # enclosing diameter, fraction of the piece side (about 1/8)
CHIP_JITTER = 0.08          # per-axis jitter, fraction of the piece side
# Chip sites, as offsets from the piece centre (fractions of the side).
SITES = [(-0.20, -0.20), (0.20, -0.08), (-0.08, 0.20), (0.20, 0.20)]

# (ground colour, [(chip colour, site index), ...]) for each chip-coded class.
LIGHT_PLAIN = ("cream", [("sand", 3)])                      # L: very sparse neutral
MID_PLAIN = ("olive", [("sand", 3)])                        # M: very sparse neutral
SUB = {
    "Lr": ("cream", [("rust", 0), ("rust", 1), ("rust", 2)]),
    "Lb": ("cream", [("pale_blue", 0), ("pale_blue", 1), ("pale_blue", 2), ("pale_blue", 3)]),
    "Lo": ("cream", [("olive", 0), ("olive", 2)]),
    "Lx": ("cream", [("rust", 0), ("pale_blue", 1), ("olive", 2)]),
    "Mr": ("olive", [("rust", 0), ("rust", 1), ("rust", 2)]),
    "Mb": ("olive", [("pale_blue", 0), ("pale_blue", 1), ("pale_blue", 2)]),
    "Mc": ("olive", [("cream", 0), ("cream", 2)]),
}

# v4 tier S and W, unchanged.
S_CHIPS = {"kinds": ["leaf", "blob"], "count": 200, "scale": 0.06}
W_LENSES = {"shape": "ellipse", "count": 34, "length": 0.25, "width": 0.06,
            "angle": 0.0, "angle_jitter": 8.0}

# kind, scale, colour for each motif class on L (as v4).
MOTIFS = {
    "SUN": ("disc", 0.6, "rust"),
    "FLO": ("flower", 0.45, "rust"),
    "FLB": ("flower", 0.45, "slate"),
    "CLD": ("fleck", 0.5, "pale_blue"),
    "LEF": ("leaf", 0.45, "olive"),
    "MOON": ("moon", 0.6, "cream"),
}
OUTLINED = {"MOON": ("indigo", 0.08)}


def _cls(layers: list, masks: dict | None = None) -> dict:
    out = {"layers": layers, "directional": False, "allowed_rotations": list(ROTS)}
    if masks:
        out["masks"] = masks
    return out


def _march(pattern: str) -> dict:
    return {"primitive": "march_mask",
            "params": {"pattern": pattern, "roughness": 0.5, "wobble": 0.12}}


def _check_sites() -> None:
    """Every chip, jitter included, must lie inside the inset (see module docstring)."""
    limit = 0.5 - INSET - CHIP_SCALE / 2.0
    for ox, oy in SITES:
        if max(abs(ox), abs(oy)) + CHIP_JITTER > limit + 1e-9:
            raise ValueError(f"site {(ox, oy)} with jitter {CHIP_JITTER} leaves the inset")


def chip_layers(ground: str, chips: list[tuple[str, int]]) -> list[dict]:
    """Flat ground plus one fleck motif per chip. The first layer paints the ground."""
    layers = []
    for i, (color, site) in enumerate(chips):
        ox, oy = SITES[site]
        layers.append({
            "primitive": "motif",
            "palette": [ground, color, ground],     # palette[0] ground, [1] chip, [2] halo
            "background": i == 0,
            "params": {"kind": "fleck", "scale": CHIP_SCALE, "jitter": CHIP_JITTER,
                       "rotation": "any", "offset": [ox, oy]},
        })
    return layers


def motif_layer(kind: str, scale: float, color: str, jitter: float | None = None) -> dict:
    # palette[2] is the halo colour; the motif checks it exists even with no halo.
    params = {"kind": kind, "scale": scale}
    if jitter is not None:
        params["jitter"] = jitter
    return {"primitive": "motif", "palette": ["cream", color, "cream"],
            "background": False, "params": params}


def build(src: dict) -> dict:
    _check_sites()
    classes: dict[str, dict] = {}
    tiers: dict[str, list] = {}

    # D is v4's dab texture, unchanged. L and M are the calm chip grounds.
    classes["D"] = copy.deepcopy(src["classes"]["D"])
    tiers["D"] = copy.deepcopy(src["classes"]["D"]["layers"])
    tiers["L"] = chip_layers(*LIGHT_PLAIN)
    tiers["M"] = chip_layers(*MID_PLAIN)
    classes["L"] = _cls(copy.deepcopy(tiers["L"]))
    classes["M"] = _cls(copy.deepcopy(tiers["M"]))

    classes["S"] = _cls([{"primitive": "scatter_shapes", "palette": ["cream", "indigo"],
                          "background": True, "params": dict(S_CHIPS)}])

    w_layers = copy.deepcopy(tiers["M"]) + [
        {"primitive": "dabs", "palette": ["cream"], "background": False,
         "params": dict(W_LENSES)}]
    tiers["W"] = w_layers
    classes["W"] = _cls(copy.deepcopy(w_layers))

    # Sub-classes: the chip signature only, on the same ground as their plain tier.
    for name, (ground, chips) in SUB.items():
        classes[name] = _cls(chip_layers(ground, chips))

    # <own><nbr><p>: own plain layers as base, nbr plain layers (background included)
    # under a mask. Sub-classes are never used here.
    for own in "DMLW":
        for nbr in "DMLW":
            if own == nbr:
                continue
            for letter, pattern in PATTERNS.items():
                nbr_layers = copy.deepcopy(tiers[nbr])
                for layer in nbr_layers:
                    layer["mask"] = "edge"
                classes[f"{own}{nbr}{letter}"] = _cls(
                    copy.deepcopy(tiers[own]) + nbr_layers,
                    masks={"edge": _march(pattern)})

    # <nbr><own>d: base nbr, with an isolated dot of own. Only for the D/L pair.
    for own, nbr in (("L", "D"), ("D", "L")):
        dot_layers = copy.deepcopy(tiers[own])
        for layer in dot_layers:
            layer["mask"] = "dot"
        classes[f"{nbr}{own}d"] = _cls(copy.deepcopy(tiers[nbr]) + dot_layers,
                                       masks={"dot": _march("dot")})

    for name, (kind, scale, color) in MOTIFS.items():
        layers = copy.deepcopy(tiers["L"])
        if name in OUTLINED:
            outline, grow = OUTLINED[name]
            layers.append(motif_layer(kind, round(scale + grow, 3), outline, jitter=0.0))
            layers.append(motif_layer(kind, scale, color, jitter=0.0))
        else:
            layers.append(motif_layer(kind, scale, color))
        classes[name] = _cls(layers)

    return {
        "_note": ("v6 (005). Calm L (cream + one sand fleck) and M (olive + one sand fleck). "
                  "Chip sub-classes Lr Lb Lo Lx (cream) and Mr Mb Mc (olive): fleck motif "
                  "chips, scale 0.125, inset 10%. D, S, W as v4. Transitions "
                  "<own><nbr><s|c|i|p> use plain tiers only; dots <nbr><own>d for D/L. "
                  "Motifs SUN FLO FLB CLD LEF MOON sit on L; MOON has an indigo outline."),
        "ref_size": src["ref_size"],
        "palette": copy.deepcopy(src["palette"]),
        "classes": classes,
    }


def _render_piece(draw, name: str, seed: int, size: float) -> np.ndarray:
    frag = draw(f"{name}#{seed}", name, seed, size)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size:g}" height="{size:g}" '
           f'viewBox="0 0 {size:g} {size:g}">{frag}</svg>')
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"))
    return np.array(Image.open(io.BytesIO(png)).convert("RGB")).astype(int)


def check_inset(spec: ClassSpec, names: list[str], seeds=range(1, 5), size: float = 400.0):
    """For each class, render pieces and return (name, worst clearance in units of the side,
    chip pixel fraction). Clearance is the smallest distance from any chip pixel to a piece
    edge. The chips pass when this is at least INSET (up to 1 px of antialiasing)."""
    draw = spec.drawer()
    rows = []
    for name in names:
        worst = 1.0
        frac = []
        for s in seeds:
            img = _render_piece(draw, name, s, size)
            ground = img[0, 0]                      # corner is always ground
            # The ground is flat, so any real chip differs from it. Sand on cream differs by
            # at most 44 per channel and is drawn at 0.92 opacity, so the threshold is low.
            chip = np.abs(img - ground).max(axis=2) > 12
            ys, xs = np.nonzero(chip)
            if xs.size == 0:
                worst = min(worst, 0.0)
                continue
            clear = min(xs.min(), ys.min(), size - 1 - xs.max(), size - 1 - ys.max())
            worst = min(worst, (clear - 1.0) / size)
            frac.append(chip.mean())
        rows.append((name, worst, float(np.mean(frac)) if frac else 0.0))
    return rows


def chip_colour_fractions(spec: ClassSpec, names: list[str], palette: dict[str, str],
                          seeds=range(1, 5), size: float = 400.0):
    """Mean pixel fraction of each chip colour in each class (distinguishability check)."""
    draw = spec.drawer()
    chip_rgb = {c: np.array(_hex(palette[c])) for c in ("rust", "pale_blue", "olive", "sand", "cream")}
    out = {}
    for name in names:
        acc = {c: [] for c in chip_rgb}
        for s in seeds:
            img = _render_piece(draw, name, s, size)
            for c, rgb in chip_rgb.items():
                acc[c].append((np.abs(img - rgb).max(axis=2) <= 20).mean())
        out[name] = {c: round(float(np.mean(v)), 4) for c, v in acc.items()}
    return out


def _hex(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def write_chip_field(spec: ClassSpec, out_png: Path, cell: float = 96.0, n: int = 3,
                     seed: int = 6) -> Path:
    """3x3 patch of L, Lr, Lb, Lo chosen at random, each piece randomly rotated.

    Cells carry no borders, so any seam must come from the artwork itself."""
    rng = random.Random(seed)
    names = ["L", "Lr", "Lb", "Lo"]
    draw = spec.drawer()
    half = cell / 2.0
    parts = []
    picks = []
    for r in range(n):
        for c in range(n):
            name = rng.choice(names)
            sd = 1000 + r * n + c
            angle = rng.choice(ROTS)
            picks.append(name)
            body = draw(f"{name}#{sd}", name, sd, cell)
            if angle:
                body = f'<g transform="rotate({angle} {half:g} {half:g})">{body}</g>'
            parts.append(f'<g transform="translate({c * cell:g} {r * cell:g})">{body}</g>')
    w = n * cell
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{w:g}" '
           f'viewBox="0 0 {w:g} {w:g}"><rect width="{w:g}" height="{w:g}" fill="#ffffff"/>'
           + "".join(parts) + "</svg>")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(out_png))
    print("chip-field picks:", ", ".join(picks))
    return out_png


def main() -> None:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    data = build(src)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    spec = load_class_spec(OUT)   # validates every layer, mask and rotation
    names = list(spec.classes)
    n_trans = sum(1 for n in names if len(n) == 3 and n[-1] in "scip")
    n_dots = sum(1 for n in names if n.endswith("d") and len(n) == 3)
    n_sub = len(SUB)
    print(f"{OUT.name}: {len(names)} classes valid (plain 5 + sub {n_sub}, "
          f"transitions {n_trans}, dots {n_dots}, motifs {len(MOTIFS)})")

    shown = ["L", "Lr", "Lb", "Lo", "Lx", "M", "Mr", "Mb", "Mc"]
    print("inset check (clearance as fraction of side; must be >= 0.10):")
    for name, worst, frac in check_inset(spec, shown):
        flag = "ok" if worst >= INSET - 1e-9 else "FAIL"
        print(f"  {name:3s} worst clearance {worst:.3f}  chip pixels {frac:.3f}  {flag}")

    fracs = chip_colour_fractions(spec, shown, spec.palette)
    print("chip colour pixel fractions (mean of 4 seeds):")
    for name, d in fracs.items():
        kept = {c: v for c, v in d.items() if v > 0.0005}
        print(f"  {name:3s} {kept}")

    sub = ClassSpec(palette=spec.palette, classes={k: spec.classes[k] for k in shown},
                    ref_size=spec.ref_size)
    print(sub.contact_sheet(CONTACT_PNG, cell=64, per_class=4))
    print(write_chip_field(spec, FIELD_PNG))


if __name__ == "__main__":
    main()
