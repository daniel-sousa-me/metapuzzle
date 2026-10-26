"""Stochastic, non-directional procedural textures as SVG fragments.

Each primitive returns SVG *elements* (no ``<svg>`` root) that fill the square
(0, 0)-(size, size) and are clipped to it, so fragments can be placed inside a
larger SVG with a transform. Output is deterministic for a given integer seed.

Conventions
-----------
* ``palette[0]`` is the base/background color; ``palette[1:]`` are mark colors.
  With a one-color palette the marks reuse the base color.
* Geometric parameters (radii, lengths, widths, pitch, scale) are fractions of
  ``size``, so the look does not depend on the unit used for ``size``.
* Count-like parameters (``density``, ``count``) are marks per 100 x 100 units
  of cell area, scaled by ``(size / 100) ** 2``.
* Marks are scattered over a padded area that extends past every edge by at
  least one mark extent. Marks cut by the edge therefore occur at the same
  density as in the interior, which keeps adjacent independent cells free of
  a visible band or seam.
* Every primitive draws its own full background unless ``background=False``.
  Fragments paint in order, so later fragments cover earlier ones.

Public API
----------
stipple, dabs, mosaic, hatch_multi, scatter_shapes, blotch,
compose, cell_svg
"""

from __future__ import annotations

import hashlib
import math
import random
from typing import Sequence

__all__ = [
    "stipple",
    "dabs",
    "mosaic",
    "hatch_multi",
    "scatter_shapes",
    "blotch",
    "compose",
    "cell_svg",
]

_SHAPE_KINDS = ("leaf", "disc", "triangle", "blob")
_HATCH_ANGLES = {3: (0.0, 60.0, 120.0), 4: (0.0, 45.0, 95.0, 140.0)}
_SIDES = (None, "top", "bottom", "left", "right")


# ---------------------------------------------------------------- helpers

def _f(x: float) -> str:
    """Compact, locale-free number formatting for SVG attributes."""
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _split(palette: Sequence[str]) -> tuple[str, list[str]]:
    if not palette:
        raise ValueError("palette needs at least one color (the base)")
    return palette[0], list(palette[1:]) or [palette[0]]


def _count(per_100: float, size: float) -> int:
    return max(0, round(per_100 * (size / 100.0) ** 2))


def _key_args(local_vars: dict) -> dict:
    """Parameters that affect output, for the clip id. Call first in a primitive."""
    return {k: v for k, v in local_vars.items() if k not in ("seed", "size", "palette")}


def _ground(base: str, size: float, background: bool) -> str:
    if not background:
        return ""
    s = _f(size)
    return f'<rect x="0" y="0" width="{s}" height="{s}" fill="{base}"/>'


def _wrap(name: str, seed: int, size: float, palette: Sequence[str],
          params: dict, body: str) -> str:
    """Clip ``body`` to the cell. The clip id hashes name, seed and all parameters,
    so fragments can share one SVG document without id collisions."""
    key = repr((name, seed, float(size), tuple(palette), tuple(sorted(params.items()))))
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
    cid = f"clip-{name}-{seed}-{digest}"
    s = _f(size)
    return (
        f'<defs><clipPath id="{cid}"><rect x="0" y="0" width="{s}" height="{s}"/>'
        f"</clipPath></defs>"
        f'<g clip-path="url(#{cid})">{body}</g>'
    )


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    h = color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"unsupported color {color!r}; use #rgb or #rrggbb")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _shade(color: str, amount: float) -> str:
    """Mix toward white (amount > 0) or black (amount < 0) by |amount|."""
    r, g, b = _hex_to_rgb(color)
    target = 255 if amount > 0 else 0
    t = min(abs(amount), 1.0)
    return "#{:02x}{:02x}{:02x}".format(*(round(c + (target - c) * t) for c in (r, g, b)))


def _points(pts: Sequence[tuple[float, float]]) -> str:
    return " ".join(f"{_f(x)},{_f(y)}" for x, y in pts)


def _smooth_closed(pts: Sequence[tuple[float, float]]) -> str:
    """Closed path through the edge midpoints, with the vertices as controls.
    Turns a polygon into a soft, wobbly outline."""
    n = len(pts)
    mids = [((pts[i][0] + pts[(i + 1) % n][0]) / 2, (pts[i][1] + pts[(i + 1) % n][1]) / 2)
            for i in range(n)]
    d = [f"M{_f(mids[-1][0])} {_f(mids[-1][1])}"]
    for i in range(n):
        d.append(f"Q{_f(pts[i][0])} {_f(pts[i][1])} {_f(mids[i][0])} {_f(mids[i][1])}")
    d.append("Z")
    return " ".join(d)


# ------------------------------------------------------------- primitives

def stipple(seed: int, size: float, palette: Sequence[str], *,
            density: float = 150.0, radius: tuple[float, float] = (0.012, 0.03),
            weights: Sequence[float] | None = None, background: bool = True) -> str:
    """Background plus small circles.

    density: marks per 100x100 units of cell area.
    radius: (min, max) circle radius as fractions of size.
    weights: optional selection weights for palette[1:], in order.
    """
    params = _key_args(locals())
    base, marks = _split(palette)
    if weights is not None and len(weights) != len(marks):
        raise ValueError("weights must match palette[1:] in length")
    rng = random.Random(seed)
    rmin, rmax = radius
    pad = rmax * size
    parts = [_ground(base, size, background)]
    for _ in range(_count(density, size)):
        x = rng.uniform(-pad, size + pad)
        y = rng.uniform(-pad, size + pad)
        r = size * rng.uniform(rmin, rmax)
        color = rng.choices(marks, weights=weights)[0]
        parts.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(r)}" fill="{color}"/>')
    return _wrap("stipple", seed, size, palette, params, "".join(parts))


def dabs(seed: int, size: float, palette: Sequence[str], *,
         count: float = 60.0, length: float = 0.10, width: float = 0.035,
         shape: str = "mixed", background: bool = True) -> str:
    """Short brush-like dabs at uniformly random angles.

    count: dabs per 100x100 units of cell area.
    length, width: nominal dab size as fractions of size (each varied 0.7-1.2x).
    shape: "rect" (rounded rectangle), "ellipse", or "mixed".
    """
    params = _key_args(locals())
    if shape not in ("rect", "ellipse", "mixed"):
        raise ValueError(f"shape must be 'rect', 'ellipse' or 'mixed', not {shape!r}")
    base, marks = _split(palette)
    rng = random.Random(seed)
    pad = length * size
    parts = [_ground(base, size, background)]
    for _ in range(_count(count, size)):
        x = rng.uniform(-pad, size + pad)
        y = rng.uniform(-pad, size + pad)
        big = size * length * rng.uniform(0.7, 1.2)
        wide = min(size * width * rng.uniform(0.7, 1.2), big)
        angle = rng.uniform(0.0, 360.0)
        kind = shape if shape != "mixed" else rng.choice(("rect", "ellipse"))
        color = rng.choice(marks)
        xf = f"translate({_f(x)} {_f(y)}) rotate({_f(angle)})"
        if kind == "rect":
            parts.append(
                f'<rect x="{_f(-big / 2)}" y="{_f(-wide / 2)}" width="{_f(big)}" '
                f'height="{_f(wide)}" rx="{_f(wide * 0.35)}" transform="{xf}" fill="{color}"/>'
            )
        else:
            parts.append(
                f'<ellipse cx="0" cy="0" rx="{_f(big / 2)}" ry="{_f(wide / 2)}" '
                f'transform="{xf}" fill="{color}"/>'
            )
    return _wrap("dabs", seed, size, palette, params, "".join(parts))


def mosaic(seed: int, size: float, palette: Sequence[str], *,
           tess: float = 0.09, gap: float = 0.14, jitter: float = 0.22,
           shade: float = 0.2, background: bool = True) -> str:
    """Jittered lattice of quads (tesserae) separated by background-colored gaps.

    tess: lattice pitch as a fraction of size.
    gap: fraction of each tessera's width removed to show the background.
    jitter: per-corner displacement as a fraction of the pitch (must be < 0.5).
    shade: max lightening/darkening of each tessera (0-1).
    The lattice phase and corner jitter come from the seed, so neighboring
    cells do not align.
    """
    params = _key_args(locals())
    if not 0.0 <= jitter < 0.5:
        raise ValueError("jitter must be in [0, 0.5)")
    base, marks = _split(palette)
    rng = random.Random(seed)
    pitch = tess * size
    n = math.ceil(size / pitch)
    fx, fy = rng.random(), rng.random()
    nodes: dict[tuple[int, int], tuple[float, float]] = {}
    for i in range(-2, n + 2):
        for j in range(-2, n + 2):
            jx = rng.uniform(-jitter, jitter)
            jy = rng.uniform(-jitter, jitter)
            nodes[(i, j)] = ((i + fx + jx) * pitch, (j + fy + jy) * pitch)
    k = 1.0 - gap
    parts = [_ground(base, size, background)]
    for i in range(-2, n + 1):
        for j in range(-2, n + 1):
            quad = [nodes[(i, j)], nodes[(i + 1, j)], nodes[(i + 1, j + 1)], nodes[(i, j + 1)]]
            cx = sum(p[0] for p in quad) / 4.0
            cy = sum(p[1] for p in quad) / 4.0
            quad = [(cx + (px - cx) * k, cy + (py - cy) * k) for px, py in quad]
            color = _shade(rng.choice(marks), rng.uniform(-shade, shade))
            parts.append(f'<polygon points="{_points(quad)}" fill="{color}"/>')
    return _wrap("mosaic", seed, size, palette, params, "".join(parts))


def hatch_multi(seed: int, size: float, palette: Sequence[str], *,
                count: float = 120.0, length: float = 0.10, width: float = 0.012,
                families: int = 4, wobble: float = 6.0, background: bool = True) -> str:
    """Short round-capped strokes in several fixed angle families, mixed evenly.

    count: strokes per 100x100 units of cell area.
    length: nominal stroke length as a fraction of size (varied 0.6-1.1x).
    width: nominal stroke width as a fraction of size (varied 0.7-1.3x).
    families: 3 (0, 60, 120 degrees) or 4 (0, 45, 95, 140 degrees).
    wobble: per-stroke angle jitter in degrees.
    """
    params = _key_args(locals())
    if families not in _HATCH_ANGLES:
        raise ValueError("families must be 3 or 4")
    angles = _HATCH_ANGLES[families]
    base, marks = _split(palette)
    rng = random.Random(seed)
    pad = length * size
    parts = [_ground(base, size, background)]
    for _ in range(_count(count, size)):
        x = rng.uniform(-pad, size + pad)
        y = rng.uniform(-pad, size + pad)
        a = math.radians(rng.choice(angles) + rng.uniform(-wobble, wobble))
        half = size * length * rng.uniform(0.6, 1.1) / 2.0
        dx, dy = math.cos(a) * half, math.sin(a) * half
        sw = size * width * rng.uniform(0.7, 1.3)
        color = rng.choice(marks)
        parts.append(
            f'<line x1="{_f(x - dx)}" y1="{_f(y - dy)}" x2="{_f(x + dx)}" y2="{_f(y + dy)}" '
            f'stroke="{color}" stroke-width="{_f(sw)}" stroke-linecap="round"/>'
        )
    return _wrap("hatch_multi", seed, size, palette, params, "".join(parts))


def _shape_svg(kind: str, rng: random.Random, x: float, y: float,
               s: float, rot: float, color: str) -> str:
    if kind == "disc":
        return f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(s)}" fill="{color}"/>'
    if kind == "leaf":
        # Pointed ellipse of half-length s, rotated and centered at (x, y).
        d = "M-1 0 C-0.4 -0.7 0.4 -0.7 1 0 C0.4 0.7 -0.4 0.7 -1 0 Z"
        xf = f"translate({_f(x)} {_f(y)}) rotate({_f(math.degrees(rot))}) scale({_f(s)})"
        return f'<path d="{d}" transform="{xf}" fill="{color}"/>'
    if kind == "triangle":
        pts = []
        for k in range(3):
            a = rot + k * 2.0 * math.pi / 3.0 + rng.uniform(-0.2, 0.2)
            r = s * rng.uniform(0.8, 1.1)
            pts.append((x + r * math.cos(a), y + r * math.sin(a)))
        return f'<polygon points="{_points(pts)}" fill="{color}"/>'
    # blob: 8 wobbly vertices, smoothed
    m = 8
    pts = []
    for k in range(m):
        a = rot + (k + rng.uniform(-0.2, 0.2)) * 2.0 * math.pi / m
        r = s * rng.uniform(0.6, 1.0)
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    return f'<path d="{_smooth_closed(pts)}" fill="{color}"/>'


def scatter_shapes(seed: int, size: float, palette: Sequence[str], *,
                   kinds: Sequence[str] = _SHAPE_KINDS, count: float = 50.0,
                   scale: float = 0.05, background: bool = True) -> str:
    """Scattered small leaves, discs, triangles and blobs at random rotations.

    kinds: any subset of ("leaf", "disc", "triangle", "blob").
    count: shapes per 100x100 units of cell area.
    scale: nominal shape radius as a fraction of size (varied 0.6-1.25x).
    """
    params = _key_args(locals())
    kinds = tuple(kinds)
    if not kinds or set(kinds) - set(_SHAPE_KINDS):
        raise ValueError(f"kinds must be a non-empty subset of {_SHAPE_KINDS}")
    base, marks = _split(palette)
    rng = random.Random(seed)
    pad = scale * size
    parts = [_ground(base, size, background)]
    for _ in range(_count(count, size)):
        kind = rng.choice(kinds)
        x = rng.uniform(-pad, size + pad)
        y = rng.uniform(-pad, size + pad)
        s = size * scale * rng.uniform(0.6, 1.25)
        rot = rng.uniform(0.0, 2.0 * math.pi)
        color = rng.choice(marks)
        parts.append(_shape_svg(kind, rng, x, y, s, rot, color))
    return _wrap("scatter_shapes", seed, size, palette, params, "".join(parts))


def blotch(seed: int, size: float, palette: Sequence[str], *,
           coverage: float = 0.45, side: str | None = None, color_index: int = 1,
           background: bool = True) -> str:
    """1-3 large soft, wobbly blotches over the background.

    coverage: 0-1, scales blotch radius (about 0.12 to 0.62 of size).
    side: None, or "top"/"bottom"/"left"/"right" to bias the blotch centers
        toward that edge. The cut through the cell is the piece's transition.
    color_index: palette index of the blotch color (default: palette[1]).
    Blotches are not padded, so they intentionally meet the edges as a
    visible boundary. Neighboring cells will differ there unless deliberately
    matched.
    """
    params = _key_args(locals())
    if not 0.0 <= coverage <= 1.0:
        raise ValueError("coverage must be in [0, 1]")
    if side not in _SIDES:
        raise ValueError(f"side must be one of {_SIDES}")
    if not 0 <= color_index < len(palette):
        raise ValueError("color_index is out of range for palette")
    base = palette[0]
    color = palette[color_index]
    rng = random.Random(seed)
    r_base = size * (0.12 + 0.5 * coverage)
    parts = [_ground(base, size, background)]
    for _ in range(rng.randint(1, 3)):
        r = r_base * rng.uniform(0.7, 1.2)
        if side is None:
            cx, cy = rng.uniform(0.0, size), rng.uniform(0.0, size)
        else:
            t = size * rng.uniform(0.0, 0.3)   # distance inward from the chosen edge
            along = rng.uniform(0.0, size)
            cx, cy = {
                "top": (along, t),
                "bottom": (along, size - t),
                "left": (t, along),
                "right": (size - t, along),
            }[side]
        m = rng.randint(10, 14)
        pts = []
        for k in range(m):
            a = (k + rng.uniform(-0.15, 0.15)) * 2.0 * math.pi / m
            rr = r * rng.uniform(0.7, 1.15)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        halo = [(cx + (px - cx) * 1.18, cy + (py - cy) * 1.18) for px, py in pts]
        parts.append(f'<path d="{_smooth_closed(halo)}" fill="{color}" fill-opacity="0.3"/>')
        parts.append(f'<path d="{_smooth_closed(pts)}" fill="{color}"/>')
    return _wrap("blotch", seed, size, palette, params, "".join(parts))


# ---------------------------------------------------------------- helpers

def compose(*fragments: str) -> str:
    """Concatenate fragments in paint order (later ones cover earlier ones)."""
    return "\n".join(f for f in fragments if f)


def cell_svg(fragment: str, size: float) -> str:
    """Wrap a fragment in a standalone SVG document of ``size`` x ``size``."""
    s = f"{size:g}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" '
        f'viewBox="0 0 {s} {s}">{fragment}</svg>'
    )
