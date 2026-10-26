"""Data-driven piece drawer: a JSON class spec maps each piece class to a stack of texture layers.

Spec format (see ``data/sample_classes.json``)::

    {
      "palette": {"paper": "#e8dcc4", "moss": "#5b7f5b", ...},
      "classes": {
        "canopy": {
          "layers": [
            {"primitive": "stipple", "palette": ["moss", "pine", "paper"],
             "params": {"density": 180}},
            {"primitive": "scatter_shapes", "palette": ["paper", "moss"],
             "params": {"kinds": ["leaf"], "count": 20}, "background": false}
          ],
          "directional": false,
          "allowed_rotations": [0, 90, 180, 270]
        }
      }
    }

* ``primitive`` is one of the functions in ``textures`` (stipple, dabs, mosaic,
  hatch_multi, scatter_shapes, blotch).
* ``palette`` entries are names from the top-level palette or raw ``#rgb``/``#rrggbb``.
* ``background`` defaults to true for the first layer and false for the others.
* Layers are drawn in order. Layer ``i`` of a piece with seed ``s`` uses a seed derived
  from ``(s, i)`` through SHA-256, so layers are independent and the output does not
  depend on ``PYTHONHASHSEED``.
* ``directional`` defaults to false. ``allowed_rotations`` defaults to all four
  rotations, or to ``[0]`` for a directional class.
* Keys starting with ``_`` are ignored everywhere, so a spec can carry comments.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from xml.sax.saxutils import escape

import cairosvg

from . import textures as tx
from .render import PieceDrawer

__all__ = [
    "ClassSpec",
    "ClassSpecError",
    "Layer",
    "PieceClass",
    "PRIMITIVES",
    "ROTATIONS",
    "SAMPLE_SPEC_PATH",
    "load_class_spec",
]

PRIMITIVES = {
    "stipple": tx.stipple,
    "dabs": tx.dabs,
    "mosaic": tx.mosaic,
    "hatch_multi": tx.hatch_multi,
    "scatter_shapes": tx.scatter_shapes,
    "blotch": tx.blotch,
}
ROTATIONS = (0, 90, 180, 270)
SAMPLE_SPEC_PATH = Path(__file__).resolve().parent / "data" / "sample_classes.json"

_RESERVED_PARAMS = frozenset({"seed", "size", "palette", "background"})
_HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_TEST_SEED = 1
_TEST_SIZE = 64.0


class ClassSpecError(ValueError):
    """A class spec is malformed. The message names the class and layer at fault."""


@dataclass(frozen=True)
class Layer:
    primitive: str
    palette: tuple[str, ...]
    params: dict
    background: bool


@dataclass(frozen=True)
class PieceClass:
    layers: tuple[Layer, ...]
    directional: bool
    allowed_rotations: tuple[int, ...]


_NEUTRAL_LAYERS = (
    Layer("stipple", ("#e6e6e6", "#8a8a8a", "#5c5c5c"), {"density": 150.0}, True),
)


# ------------------------------------------------------------------ parsing

def _check_keys(d: Mapping, allowed: set[str], where: str, required: Sequence[str] = ()) -> None:
    for key in d:
        if not str(key).startswith("_") and key not in allowed:
            raise ClassSpecError(f"{where}: unknown key {key!r}")
    for key in required:
        if key not in d:
            raise ClassSpecError(f"{where}: missing required key {key!r}")


def _parse_layer(where: str, index: int, raw: Any) -> Layer:
    if not isinstance(raw, Mapping):
        raise ClassSpecError(f"{where} layer {index}: must be an object")
    w = f"{where} layer {index}"
    _check_keys(raw, {"primitive", "palette", "params", "background"}, w, ("primitive", "palette"))
    prim = raw["primitive"]
    if not isinstance(prim, str):
        raise ClassSpecError(f"{w}: primitive must be a string")
    names = raw["palette"]
    if not isinstance(names, list) or not names or not all(isinstance(n, str) for n in names):
        raise ClassSpecError(f"{w}: palette must be a non-empty list of color names or hex strings")
    params = raw.get("params", {})
    if not isinstance(params, Mapping):
        raise ClassSpecError(f"{w}: params must be an object")
    background = raw.get("background", index == 0)
    if not isinstance(background, bool):
        raise ClassSpecError(f"{w}: background must be true or false")
    return Layer(prim, tuple(names), dict(params), background)


def _parse_class(name: str, raw: Any) -> PieceClass:
    where = f"class {name!r}"
    if not isinstance(raw, Mapping):
        raise ClassSpecError(f"{where}: must be an object")
    _check_keys(raw, {"layers", "directional", "allowed_rotations"}, where, ("layers",))
    layers_raw = raw["layers"]
    if not isinstance(layers_raw, list) or not layers_raw:
        raise ClassSpecError(f"{where}: layers must be a non-empty list")
    layers = tuple(_parse_layer(where, i, lr) for i, lr in enumerate(layers_raw))
    directional = raw.get("directional", False)
    if not isinstance(directional, bool):
        raise ClassSpecError(f"{where}: directional must be true or false")
    default_rot = [0] if directional else list(ROTATIONS)
    rots = raw.get("allowed_rotations", default_rot)
    if not isinstance(rots, list):
        raise ClassSpecError(f"{where}: allowed_rotations must be a list")
    return PieceClass(layers, directional, tuple(rots))


def _layer_seed(piece_seed: int, index: int) -> int:
    digest = hashlib.sha256(f"{int(piece_seed)}:{index}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


# ------------------------------------------------------------------ spec

@dataclass
class ClassSpec:
    """A parsed class spec. Build with ``load_class_spec`` or ``ClassSpec.from_dict``."""

    palette: dict[str, str]
    classes: dict[str, PieceClass]

    @classmethod
    def from_dict(cls, data: Any) -> "ClassSpec":
        """Parse the JSON structure. Checks shape and keys; ``validate`` checks the rest."""
        if not isinstance(data, Mapping):
            raise ClassSpecError("spec must be a JSON object")
        _check_keys(data, {"palette", "classes"}, "spec", ("classes",))
        palette = data.get("palette", {})
        if not isinstance(palette, Mapping) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in palette.items()
        ):
            raise ClassSpecError("palette must map names to color strings")
        classes_raw = data["classes"]
        if not isinstance(classes_raw, Mapping) or not classes_raw:
            raise ClassSpecError("classes must be a non-empty object")
        parsed = {
            name: _parse_class(name, raw)
            for name, raw in classes_raw.items()
            if not str(name).startswith("_")
        }
        if not parsed:
            raise ClassSpecError("classes must be a non-empty object")
        return cls(palette=dict(palette), classes=parsed)

    def _resolve(self, names: Sequence[str]) -> list[str]:
        out = []
        for n in names:
            if n.startswith("#"):
                if not _HEX.match(n):
                    raise ClassSpecError(f"bad hex color {n!r}; use #rgb or #rrggbb")
                out.append(n)
            elif n in self.palette:
                out.append(self.palette[n])
            else:
                raise ClassSpecError(f"unknown palette name {n!r}")
        return out

    def _check_layer(self, layer: Layer) -> None:
        fn = PRIMITIVES.get(layer.primitive)
        if fn is None:
            raise ClassSpecError(f"unknown primitive {layer.primitive!r}; use one of {sorted(PRIMITIVES)}")
        palette = self._resolve(layer.palette)
        reserved = _RESERVED_PARAMS & set(layer.params)
        if reserved:
            raise ClassSpecError(f"params may not set {sorted(reserved)}; 'background' is a layer key")
        accepted = set(inspect.signature(fn).parameters) - _RESERVED_PARAMS
        unknown = set(layer.params) - accepted
        if unknown:
            raise ClassSpecError(f"{layer.primitive} has no parameter(s) {sorted(unknown)}; "
                                 f"accepts {sorted(accepted)}")
        try:
            frag = fn(_TEST_SEED, _TEST_SIZE, palette, background=layer.background, **layer.params)
        except Exception as e:  # the primitive's own message is the useful part
            raise ClassSpecError(f"{type(e).__name__}: {e}") from e
        if not frag.strip():
            raise ClassSpecError("primitive produced an empty fragment")

    def validate(self) -> None:
        """Check every class: primitives, palette names, parameters, rotations.

        Each layer is called once with a fixed test seed. Raises ``ClassSpecError``
        listing every problem found.
        """
        errors: list[str] = []
        for key, value in self.palette.items():
            if not _HEX.match(value):
                errors.append(f"palette {key!r}: {value!r} is not #rgb or #rrggbb")
        for name, pc in self.classes.items():
            where = f"class {name!r}"
            rots = pc.allowed_rotations
            if not rots or len(set(rots)) != len(rots) or any(r not in ROTATIONS for r in rots):
                errors.append(f"{where}: allowed_rotations must be distinct values from "
                              f"{list(ROTATIONS)}, got {list(rots)}")
            for i, layer in enumerate(pc.layers):
                try:
                    self._check_layer(layer)
                except ClassSpecError as e:
                    errors.append(f"{where} layer {i} ({layer.primitive}): {e}")
        if errors:
            raise ClassSpecError("invalid class spec:\n  " + "\n  ".join(errors))

    def allowed_rotations(self, cls: str) -> tuple[int, ...]:
        """Rotations (degrees) allowed for a class. Unknown classes get all four."""
        pc = self.classes.get(cls)
        return ROTATIONS if pc is None else pc.allowed_rotations

    def _layer_fragment(self, layer: Layer, index: int, piece_seed: int, size: float) -> str:
        palette = self._resolve(layer.palette)
        return PRIMITIVES[layer.primitive](
            _layer_seed(piece_seed, index), size, palette,
            background=layer.background, **layer.params,
        )

    def drawer(self) -> PieceDrawer:
        """A ``PieceDrawer`` that draws each piece from its class's layers.

        Unknown classes draw a neutral grey stipple and emit one warning per class.
        The drawer is a pure function of (cls, rng_seed, size).
        """
        self.validate()
        warned: set[str] = set()

        def draw(piece_id: str, cls: str, rng_seed: int, size: float) -> str:
            pc = self.classes.get(cls)
            if pc is None:
                if cls not in warned:
                    warned.add(cls)
                    warnings.warn(f"class {cls!r} not in spec; drawing neutral stipple",
                                  UserWarning, stacklevel=2)
                layers = _NEUTRAL_LAYERS
            else:
                layers = pc.layers
            return tx.compose(*(
                self._layer_fragment(layer, i, rng_seed, float(size))
                for i, layer in enumerate(layers)
            ))

        return draw

    # ---------------------------------------------------------- inspection

    def _cell_fragments(self, cells: Sequence[tuple[str, int]], cell: float) -> list[str]:
        draw = self.drawer()
        return [draw(f"{cls}#{seed}", cls, seed, cell) for cls, seed in cells]

    def contact_sheet(self, out_png: str | Path, cell: float = 64, per_class: int = 4) -> Path:
        """PNG with one labelled row per class: ``per_class`` adjacent cells with different seeds.

        Adjacent cells show seams between same-class neighbors.
        """
        rows = []
        seed = 1
        for name, pc in self.classes.items():
            info = f"{name}  rotations {list(pc.allowed_rotations)}"
            if pc.directional:
                info += "  directional"
            cells = []
            for _ in range(per_class):
                cells.append((name, seed))
                seed += 1
            rows.append((info, self._cell_fragments(cells, cell)))
        return _write_sheet(rows, cell, out_png)

    def pairs_sheet(self, out_png: str | Path, pairs: Sequence[tuple[str, str]],
                    cell: float = 64) -> Path:
        """PNG with one row per class pair: an A cell and a B cell side by side.

        The shared edge is the cross-class boundary to inspect.
        """
        rows = []
        seed = 1
        for a, b in pairs:
            for name in (a, b):
                if name not in self.classes:
                    raise ClassSpecError(f"pairs_sheet: unknown class {name!r}")
            cells = [(a, seed), (b, seed + 1)]
            seed += 2
            rows.append((f"{a} | {b}", self._cell_fragments(cells, cell)))
        return _write_sheet(rows, cell, out_png)


_SHEET_PAD = 12
_SHEET_LABEL_H = 20
_SHEET_ROW_GAP = 12


def _write_sheet(rows: Sequence[tuple[str, Sequence[str]]], cell: float, out_png: str | Path) -> Path:
    """Lay out labelled rows of adjacent cell fragments and rasterise to PNG."""
    ncells = max((len(frags) for _, frags in rows), default=0)
    label_w = max((0.6 * 12 * len(label) for label, _ in rows), default=0)
    width = 2 * _SHEET_PAD + max(ncells * cell, label_w)
    row_h = _SHEET_LABEL_H + cell + _SHEET_ROW_GAP
    height = 2 * _SHEET_PAD + len(rows) * row_h
    w, h = f"{width:g}", f"{height:g}"
    parts = [f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>']
    for r, (label, frags) in enumerate(rows):
        y0 = _SHEET_PAD + r * row_h
        parts.append(
            f'<text x="{_SHEET_PAD}" y="{y0 + 14:g}" font-family="sans-serif" font-size="12" '
            f'fill="#222">{escape(label)}</text>'
        )
        for i, frag in enumerate(frags):
            x = _SHEET_PAD + i * cell
            parts.append(f'<g transform="translate({x:g} {y0 + _SHEET_LABEL_H:g})">{frag}</g>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}">' + "".join(parts) + "</svg>"
    )
    out = Path(out_png)
    out.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(out))
    return out


def load_class_spec(path: str | Path, *, validate: bool = True) -> ClassSpec:
    """Read a JSON class spec. With ``validate`` (default) the spec is fully checked."""
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ClassSpecError(f"{p}: invalid JSON: {e}") from e
    try:
        spec = ClassSpec.from_dict(data)
        if validate:
            spec.validate()
    except ClassSpecError as e:
        raise ClassSpecError(f"{p}: {e}") from e
    return spec
