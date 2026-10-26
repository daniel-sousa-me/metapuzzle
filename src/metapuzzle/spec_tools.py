"""Generate transition classes for a class spec, and prune a spec to the classes scenes use.

A transition class is the base class's layers followed by the mass class's layers, each
mass layer wrapped in a ``blotch_mask`` on one side. Where the mass shows, the cell is the
mass texture; elsewhere it is the base texture, so the boundary is a ragged line inside the
piece instead of the piece edge.

``generate_transitions`` adds, for every ordered pair (base, mass) of distinct fields and
every side, one class. With ``corner=True`` it also adds one class per pair of adjacent
sides (mass on both edges, a union of two masks). With ``rotatable=True`` it adds one side
(the first in ``sides``) per pair and marks the class non-directional with all four
rotations; the scene then orients it with the ``@90`` suffix. A rotation is clockwise, so
``top`` becomes ``right`` at ``@90``, ``bottom`` at ``@180`` and ``left`` at ``@270``.
Without ``rotatable`` each transition is directional with ``allowed_rotations`` ``[0]``.

Generated classes carry a ``_gen`` key (``base``, ``mass``, ``side``) for provenance; keys
starting with ``_`` are ignored by the class-spec parser.

Default codes avoid ``@``, which scene tokens reserve for orientation: ``SK>FO.T`` is
mass FO on the top side of base SK; ``SK>FO.TL`` is a corner; a rotatable side class is
``SK>FO``. All three are accepted by ``scene.parse_token`` and ``scene.validate_scenes``.

Coverage: ``blotch_mask`` blobs are centred up to 0.3 of the cell inward from the mass side,
so some blobs reach that edge. That is intended: the neighbour across the mass side is the
mass class, so the edge should match. Lower ``coverage`` to shrink the blobs.
"""
from __future__ import annotations

import copy
from typing import Callable, Mapping, Sequence

from .scene import load_scenes

__all__ = ["SIDE_NAMES", "generate_transitions", "prune_unused"]

SIDE_NAMES = ("top", "bottom", "left", "right")
_OPPOSITE_PAIRS = (frozenset(("top", "bottom")), frozenset(("left", "right")))
_ALL_ROTATIONS = [0, 90, 180, 270]


def _side_code(side: str) -> str:
    """'top' -> 'T'; 'top+left' -> 'TL'."""
    return "".join(part[0].upper() for part in side.split("+"))


def _default_code(base: str, mass: str, side: str, rotatable: bool = False) -> str:
    """``SK>FO.T`` (side), ``SK>FO`` (rotatable side), ``SK>FO.TL`` (corner)."""
    if rotatable and "+" not in side:
        return f"{base}>{mass}"
    return f"{base}>{mass}.{_side_code(side)}"


def _check_sides(sides: Sequence[str]) -> list[str]:
    out = list(sides)
    if not out:
        raise ValueError("sides must not be empty")
    if len(set(out)) != len(out):
        raise ValueError(f"sides has duplicates: {out}")
    bad = [s for s in out if s not in SIDE_NAMES]
    if bad:
        raise ValueError(f"unknown side(s) {bad}; use some of {list(SIDE_NAMES)}")
    return out


def _corner_sides(sides: Sequence[str]) -> list[str]:
    """Adjacent side pairs, as 'a+b' in the order the sides were given."""
    out = []
    for i, a in enumerate(sides):
        for b in sides[i + 1:]:
            if frozenset((a, b)) not in _OPPOSITE_PAIRS:
                out.append(f"{a}+{b}")
    return out


def _explicit_layers(layers: Sequence[Mapping]) -> list[dict]:
    """Copy layers with ``background`` written out, so moving a layer keeps its meaning."""
    out = []
    for i, layer in enumerate(layers):
        d = copy.deepcopy(dict(layer))
        d["background"] = bool(d.get("background", i == 0))
        out.append(d)
    return out


def _masked(layer: dict, side: str, coverage: float) -> dict:
    """A copy of a mass layer clipped to a blotch on one ``side``."""
    d = copy.deepcopy(layer)
    d["mask"] = {"primitive": "blotch_mask", "params": {"coverage": coverage, "side": side}}
    return d


def _transition_layers(base_layers: Sequence[Mapping], mass_layers: Sequence[Mapping],
                       side: str, coverage: float) -> list[dict]:
    """Base layers, then each mass layer masked on ``side``. A corner side 'a+b' masks each
    mass layer once per edge, so the mass shows along both edges."""
    layers = _explicit_layers(base_layers)
    mass = _explicit_layers(mass_layers)  # background is read at the mass layer's own index
    for edge in side.split("+"):
        layers += [_masked(m, edge, coverage) for m in mass]
    return layers


def generate_transitions(
    spec: dict,
    fields: list[str],
    sides: Sequence[str] = ("top", "bottom", "left", "right"),
    coverage: float = 0.45,
    code_fn: Callable[[str, str, str], str] | None = None,
    rotatable: bool = False,
    corner: bool = False,
) -> dict:
    """Return a new spec dict with transition classes added for every ordered field pair.

    ``spec`` is a parsed class-spec JSON object and is not modified. ``fields`` names
    existing classes (distinct, at least two). ``sides`` picks the mask edges. ``coverage``
    is passed to ``blotch_mask``. ``code_fn(base, mass, side)`` returns the class name;
    for a corner, ``side`` is ``'top+left'``. ``rotatable`` keeps one side per pair (the
    first of ``sides``) and makes the class non-directional. ``corner`` adds one class per
    pair of adjacent sides; with ``rotatable`` it keeps only the first such pair.
    Blobs that reach the mass-side edge are intended: the neighbour on that side is the
    mass class (see the module docstring).

    Raises ``ValueError`` for an unknown field or side, a masked mass layer, or a code
    that collides with an existing class.
    """
    classes = spec.get("classes")
    if not isinstance(classes, Mapping):
        raise ValueError("spec has no 'classes' object")
    fields = list(fields)
    if len(fields) < 2:
        raise ValueError("need at least two field classes")
    if len(set(fields)) != len(fields):
        raise ValueError(f"fields has duplicates: {fields}")
    missing = [f for f in fields if f not in classes]
    if missing:
        raise ValueError(f"field class(es) not in spec: {missing}")
    sides = _check_sides(sides)
    if not 0.0 <= coverage <= 1.0:
        raise ValueError("coverage must be in [0, 1]")
    for f in fields:
        if any(layer.get("mask") is not None for layer in classes[f].get("layers", [])):
            # Fields are used as mass too; a masked mass layer would need a nested mask.
            raise ValueError(f"field {f!r} has a masked layer; cannot use it as a mass")

    side_names = list(sides[:1] if rotatable else sides)
    if corner:
        corners = _corner_sides(sides)
        if not corners:
            raise ValueError("corner=True needs two adjacent sides; sides given: " + ",".join(sides))
        side_names += corners[:1] if rotatable else corners

    code = code_fn or (lambda b, m, s: _default_code(b, m, s, rotatable))
    out = copy.deepcopy(dict(spec))
    new_classes = dict(out["classes"])
    added = 0
    for base in fields:
        for mass in fields:
            if mass == base:
                continue
            for side in side_names:
                name = code(base, mass, side)
                if not isinstance(name, str) or not name or name.startswith("_"):
                    raise ValueError(f"code_fn returned an unusable class name {name!r}")
                if name in new_classes:
                    raise ValueError(f"generated class {name!r} collides with an existing class")
                layers = _transition_layers(
                    classes[base]["layers"], classes[mass]["layers"], side, coverage,
                )
                cls = {
                    "_gen": {"base": base, "mass": mass, "side": side},
                    "layers": layers,
                }
                if rotatable:
                    cls["directional"] = False
                    cls["allowed_rotations"] = list(_ALL_ROTATIONS)
                else:
                    cls["directional"] = True
                    cls["allowed_rotations"] = [0]
                new_classes[name] = cls
                added += 1
    out["classes"] = new_classes
    return out


def prune_unused(spec: dict, scene_paths: Sequence[str]) -> dict:
    """Return a new spec dict keeping only the classes that the scene files use.

    Scenes are read with ``scene.load_scenes`` (three class maps, from one file or three).
    Raises ``ValueError`` when a scene uses a class the spec does not define, because the
    drawer would otherwise fall back to a neutral stipple without saying so.
    """
    classes = spec.get("classes")
    if not isinstance(classes, Mapping):
        raise ValueError("spec has no 'classes' object")
    used: set[str] = set()
    for m in load_scenes(list(scene_paths)):
        used.update(m.histogram())
    missing = sorted(used - set(classes))
    if missing:
        raise ValueError(f"scenes use class(es) not in spec: {missing}")
    out = copy.deepcopy(dict(spec))
    out["classes"] = {name: copy.deepcopy(c) for name, c in classes.items() if name in used}
    return out
