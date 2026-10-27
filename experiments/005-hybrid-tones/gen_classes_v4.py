"""Generate the v4 class spec for experiment 005 (hybrid tones).

Tiers D, M, L are copied from classes.json. New: S (navy chips on cream), W (M with
cream lenses). Every ordered pair of D/M/L/W gets four march_mask transitions
(s, c, i, p); the D/L pair gets two dots. Six motif classes sit on L.

The transition convention matches gallery/march-demo.py: the own tier is the base
(background included), the neighbour tier is the mass, clipped by a named march_mask.
In canonical orientation (rotation 0) the neighbour lies on top of the boundary.

Writes classes-v4.json, validates it, and renders contact-sheet-v4.png and
pairs-sheet-v4.png next to this file.

Run: python3 experiments/005-hybrid-tones/gen_classes_v4.py
"""
from __future__ import annotations

import copy
import io
import json
from pathlib import Path
from xml.sax.saxutils import escape

import cairosvg
import numpy as np
from PIL import Image

from metapuzzle.classes import ClassSpec, load_class_spec
from metapuzzle import textures as tx

HERE = Path(__file__).resolve().parent
SRC = HERE / "classes.json"
OUT = HERE / "classes-v4.json"
CONTACT_PNG = HERE / "contact-sheet-v4.png"
PAIRS_PNG = HERE / "pairs-sheet-v4.png"

ROTS = [0, 90, 180, 270]
PATTERNS = {"s": "straight", "c": "corner", "i": "corner_in", "p": "cap"}

# Tuned by measured alpha coverage over 8 seeds (see measure_coverage).
S_CHIPS = {"kinds": ["leaf", "blob"], "count": 200, "scale": 0.06}        # ~55%
# Lenses lie horizontal: angle 0, each within 8 degrees.
W_LENSES = {"shape": "ellipse", "count": 34, "length": 0.25, "width": 0.06,
            "angle": 0.0, "angle_jitter": 8.0}                                # ~15%

# kind, scale, colour for each motif class on L.
MOTIFS = {
    "SUN": ("disc", 0.6, "rust"),
    "FLO": ("flower", 0.45, "rust"),
    "FLB": ("flower", 0.45, "slate"),
    "CLD": ("fleck", 0.5, "pale_blue"),
    "LEF": ("leaf", 0.45, "olive"),
    "MOON": ("moon", 0.6, "cream"),
}
# Motifs drawn with a thin outline: a same-shape layer in this colour, a little larger,
# goes under the fill. Both layers use jitter 0, so their centres match.
OUTLINED = {"MOON": ("indigo", 0.08)}


def _cls(layers: list, masks: dict | None = None) -> dict:
    out = {"layers": layers, "directional": False, "allowed_rotations": list(ROTS)}
    if masks:
        out["masks"] = masks
    return out


def _march(pattern: str) -> dict:
    return {"primitive": "march_mask",
            "params": {"pattern": pattern, "roughness": 0.5, "wobble": 0.12}}


def build(src: dict) -> dict:
    classes: dict[str, dict] = {}
    tiers: dict[str, list] = {}

    for t in "DML":
        classes[t] = copy.deepcopy(src["classes"][t])
        tiers[t] = copy.deepcopy(src["classes"][t]["layers"])

    classes["S"] = _cls([{"primitive": "scatter_shapes", "palette": ["cream", "indigo"],
                          "background": True, "params": dict(S_CHIPS)}])

    w_layers = copy.deepcopy(tiers["M"]) + [
        {"primitive": "dabs", "palette": ["cream"], "background": False,
         "params": dict(W_LENSES)}]
    tiers["W"] = w_layers
    classes["W"] = _cls(copy.deepcopy(w_layers))

    # <own><nbr><p>: own layers as base, nbr layers (background included) under a mask.
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

    def motif_layer(kind: str, scale: float, color: str, jitter: float | None = None) -> dict:
        # palette[2] is the halo colour; the motif checks it exists even with no halo.
        params = {"kind": kind, "scale": scale}
        if jitter is not None:
            params["jitter"] = jitter
        return {"primitive": "motif", "palette": ["cream", color, "cream"],
                "background": False, "params": params}

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
        "_note": ("v4 (005). Plain D/M/L from v3; S = navy chips on cream; W = M plus "
                  "cream lenses. Transitions <own><nbr><s|c|i|p>: own base, nbr mass under "
                  "a march_mask named 'edge'; canonical orientation puts nbr on top. Dots "
                  "<nbr><own>d for the D/L pair. Motifs SUN FLO FLB CLD LEF MOON sit on L; "
                  "MOON has an indigo outline."),
        "ref_size": src["ref_size"],
        "palette": copy.deepcopy(src["palette"]),
        "classes": classes,
    }


def measure_coverage(seeds=range(1, 9)) -> dict[str, tuple[float, float]]:
    """Mean and spread of the painted fraction of one cell, for the tuned chip layers."""
    def cover(frag_for_seed) -> tuple[float, float]:
        vals = []
        for s in seeds:
            svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
                   f'viewBox="0 0 100 100">{frag_for_seed(s)}</svg>')
            png = cairosvg.svg2png(bytestring=svg.encode(), output_width=400, output_height=400)
            alpha = np.array(Image.open(io.BytesIO(png)).convert("RGBA"))[..., 3]
            vals.append(float((alpha > 127).mean()))
        return float(np.mean(vals)), float(np.std(vals))

    return {
        "S chips": cover(lambda s: tx.scatter_shapes(s, 100, ["cream", "indigo"],
                                                     background=False, **S_CHIPS)),
        "W lenses": cover(lambda s: tx.dabs(s, 100, ["cream"], background=False,
                                            **W_LENSES)),
    }


def write_pairs_sheet(spec: ClassSpec, out_png: Path, cell: float = 96.0) -> Path:
    """Two rows for (L own, D nbr): three straights in a row, then a 2x2 corner block.

    Rotations are applied as render.py does: a rotate(angle, half, half) group inside
    the translated cell.
    """
    draw = spec.drawer()
    half = cell / 2.0

    def frag(name: str, seed: int, angle: int = 0) -> str:
        body = draw(f"{name}#{seed}", name, seed, cell)
        if angle:
            body = f'<g transform="rotate({angle} {half:g} {half:g})">{body}</g>'
        return body

    pad, label_h, gap = 12.0, 20.0, 14.0
    rows = [
        ("LDs@0 | LDs@0 | LDs@0: one straight boundary across three cuts",
         [(0, 0, frag("LDs", 1)), (cell, 0, frag("LDs", 2)), (2 * cell, 0, frag("LDs", 3))],
         3 * cell, cell),
        ("2x2 corner: LDs@0 (top left), LDc@0 (top right), L (bottom left), LDi@90 (bottom right)",
         [(0, 0, frag("LDs", 4)), (cell, 0, frag("LDc", 5)),
          (0, cell, frag("L", 6)), (cell, cell, frag("LDi", 7, 90))],
         2 * cell, 2 * cell),
    ]
    width = 2 * pad + max(max(w for _, _, w, _ in rows),
                          max(0.6 * 12 * len(label) for label, *_ in rows))
    parts, y = [], pad
    for label, items, _, h in rows:
        parts.append(f'<text x="{pad:g}" y="{y + 14:g}" font-family="sans-serif" '
                     f'font-size="12" fill="#222">{escape(label)}</text>')
        for x, dy, svg in items:
            parts.append(f'<g transform="translate({pad + x:g} {y + label_h + dy:g})">'
                         f'{svg}</g>')
        y += label_h + h + gap
    height = y + pad - gap
    w, hh = f"{width:g}", f"{height:g}"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{hh}" '
           f'viewBox="0 0 {w} {hh}"><rect width="{w}" height="{hh}" fill="#ffffff"/>'
           + "".join(parts) + "</svg>")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(out_png))
    return out_png


def main() -> None:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    data = build(src)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    spec = load_class_spec(OUT)   # validates every layer, mask and rotation
    names = list(spec.classes)
    n_trans = sum(1 for n in names if len(n) == 3 and n[-1] in "scip")
    n_dots = sum(1 for n in names if n.endswith("d") and len(n) == 3)
    print(f"{OUT.name}: {len(names)} classes valid "
          f"(plain 5, transitions {n_trans}, dots {n_dots}, motifs {len(MOTIFS)})")

    for name, (mean, sd) in measure_coverage().items():
        print(f"  {name}: measured coverage {mean:.3f} +- {sd:.3f}")

    keep = ["D", "M", "L", "S", "W", *MOTIFS]
    sub = ClassSpec(palette=spec.palette, classes={k: spec.classes[k] for k in keep},
                    ref_size=spec.ref_size)
    print(sub.contact_sheet(CONTACT_PNG, cell=80, per_class=4))
    print(write_pairs_sheet(spec, PAIRS_PNG))


if __name__ == "__main__":
    main()
