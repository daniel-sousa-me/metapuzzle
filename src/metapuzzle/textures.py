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
  of cell area, scaled by ``(size / 100) ** 2``. The class-spec drawer always
  passes its reference size (100 by default) here, so the artwork does not
  depend on the size a piece is displayed at.
* Marks are scattered over a padded area that extends past every edge by at
  least one mark extent. Marks cut by the edge therefore occur at the same
  density as in the interior, which keeps adjacent independent cells free of
  a visible band or seam.
* Every primitive draws its own full background unless ``background=False``.
  Fragments paint in order, so later fragments cover earlier ones.
* ``blotch_mask`` is not a painter. It returns a ``<clipPath>`` element and its
  id, so a caller can clip another fragment to the blotch shape.

Public API
----------
stipple, dabs, mosaic, hatch_multi, scatter_shapes, blotch, blotch_mask, motif,
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
    "blotch_mask",
    "motif",
    "MOTIF_KINDS",
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


def _clip_id(name: str, seed: int, size: float, palette: Sequence[str], params: dict) -> str:
    """Id for a clip path. It hashes name, seed and all parameters, so fragments can
    share one SVG document without id collisions."""
    key = repr((name, seed, float(size), tuple(palette), tuple(sorted(params.items()))))
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
    return f"clip-{name}-{seed}-{digest}"


def _wrap(name: str, seed: int, size: float, palette: Sequence[str],
          params: dict, body: str) -> str:
    """Clip ``body`` to the cell, with the id from ``_clip_id``."""
    cid = _clip_id(name, seed, size, palette, params)
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


_HALO_SCALE = 1.18   # blotch() paints a halo out to this multiple of the blob radius


def _check_blotch_args(coverage: float, side: str | None, inset: float = 0.0,
                       roughness: float = 0.0, spread: float = 1.0) -> None:
    if not 0.0 <= coverage <= 1.0:
        raise ValueError("coverage must be in [0, 1]")
    if side not in _SIDES:
        raise ValueError(f"side must be one of {_SIDES}")
    if not 0.0 <= inset < 0.5:
        raise ValueError("inset must be in [0, 0.5)")
    if not 0.0 <= roughness <= 1.0:
        raise ValueError("roughness must be in [0, 1]")
    if not 0.0 <= spread <= 1.0:
        raise ValueError("spread must be in [0, 1]")
    if spread != 1.0 and (side is None or roughness == 0.0):
        raise ValueError("spread applies only with a side and roughness > 0")


def _inset_blotch(cx: float, cy: float, offs: list[tuple[float, float]], size: float,
                  side: str | None, inset: float):
    """Move one blotch so it lies inside the cell, ``inset * size`` from each edge.

    The edge named by ``side`` is not inset: the blotch must still reach it. The
    reach counts blotch()'s halo, so the halo stays inside as well. If a blotch is
    too large to fit, its outline is scaled down to fit. Returns (cx, cy, offs)."""
    reach = _HALO_SCALE * max(math.hypot(dx, dy) for dx, dy in offs)
    half = size * (0.5 - inset)                 # largest reach that fits in the cell
    if reach > half:
        f = half / reach
        offs = [(dx * f, dy * f) for dx, dy in offs]
        reach = half
    lo, hi = size * inset + reach, size * (1.0 - inset) - reach
    x_lo = -math.inf if side == "left" else lo
    x_hi = math.inf if side == "right" else hi
    y_lo = -math.inf if side == "top" else lo
    y_hi = math.inf if side == "bottom" else hi
    return min(max(cx, x_lo), x_hi), min(max(cy, y_lo), y_hi), offs


def _rough_vertex_count(roughness: float) -> int:
    """Polygon vertices for a rough outline: 16 at roughness 0.0, 28 at 1.0."""
    return round(16 + 12 * roughness)


def _to_xy(side: str, u: float, v: float, size: float) -> tuple[float, float]:
    """Band coordinates: ``u`` runs along the edge named by ``side``, ``v`` is the depth
    inward from that edge. Returns the point in the cell."""
    if side == "top":
        return u, v
    if side == "bottom":
        return u, size - v
    if side == "left":
        return v, u
    return size - v, u                          # right


def _band_polys(rng: random.Random, size: float, coverage: float, side: str,
                count: int | None, inset: float, roughness: float, spread: float,
                ) -> list[tuple[float, float, list[tuple[float, float]]]]:
    """One band of mass along the ``side`` edge, cut into ``count`` overlapping pieces so
    neighbouring pieces join. The band covers ``spread`` of the edge width, centred; at
    spread 1 it reaches both corners. Its depth follows ``coverage`` plus or minus 0.15
    across the width, and two frequencies of seeded radial noise make the edge ragged.
    ``inset`` keeps the far edge clear. The side edges are not inset: the band must reach
    the corners to join its neighbours. Pieces extend past the cell, so the cell clips them."""
    n_pieces = rng.randint(1, 3) if count is None else count
    phase = [rng.uniform(0.0, 2.0 * math.pi) for _ in range(3)]
    u0 = size * (1.0 - spread) / 2.0
    u1 = size - u0
    if u1 <= u0:
        return []
    seg = (u1 - u0) / n_pieces
    overlap = min(seg / 2.0, 0.05 * size)
    nv = _rough_vertex_count(roughness)
    taper = 0.15 * size if spread < 1.0 else 0.0   # spread < 1: band ends fade to nothing
    far = size * (1.0 - inset)
    ext = 0.1 * size                               # how far pieces run past the cell
    polys = []
    for i in range(n_pieces):
        a = max(u0, u0 + i * seg - overlap)
        b = min(u1, u0 + (i + 1) * seg + overlap)
        edge = []
        for k in range(nv):
            u = a + (b - a) * k / (nv - 1)
            t = (u - u0) / (u1 - u0)
            cov = coverage + 0.15 * (0.6 * math.sin(2.0 * math.pi * t + phase[0])
                                     + 0.4 * math.sin(2.0 * math.pi * 2.3 * t + phase[1]))
            depth = size * (0.12 + 0.5 * cov)
            low = math.sin(2.0 * math.pi * 3.0 * t + phase[2])   # slow noise across the width
            high = rng.uniform(-1.0, 1.0)                        # fast noise per vertex
            depth *= 1.0 + roughness * (0.25 * low + 0.3 * high)
            if taper:
                depth *= max(0.0, min(1.0, (u - u0) / taper, (u1 - u) / taper))
            edge.append((u, min(max(depth, 0.0), far)))
        if a <= u0:                                 # run out past the corner
            head = [(a - ext, -ext), (a - ext, edge[0][1])]
        else:
            head = [(a, -ext)]
        if b >= u1:
            tail = [(b + ext, edge[-1][1]), (b + ext, -ext)]
        else:
            tail = [(b, -ext)]
        uv = head + edge + tail
        pts = [_to_xy(side, u, v, size) for u, v in uv]
        cx, cy = _to_xy(side, (a + b) / 2.0, 0.0, size)
        polys.append((cx, cy, pts))
    return polys


def _blotch_polys(rng: random.Random, size: float, coverage: float, side: str | None,
                  count: int | None = None, inset: float = 0.0,
                  roughness: float = 0.0, spread: float = 1.0,
                  ) -> list[tuple[float, float, list[tuple[float, float]]]]:
    """Wobbly blotches as ``(center_x, center_y, outline)``, 1-3 of them unless
    ``count`` is given. Draws from ``rng`` in a fixed order, so ``blotch`` output is stable.
    ``inset > 0`` moves blotches inside the cell (see ``_inset_blotch``); the draws are
    the same, so the blotches keep their random shapes. ``roughness > 0`` with a ``side``
    gives one band instead (see ``_band_polys``); without a side it gives lobes with more
    vertices and radial noise."""
    if roughness > 0.0 and side is not None:
        return _band_polys(rng, size, coverage, side, count, inset, roughness, spread)
    r_base = size * (0.12 + 0.5 * coverage)
    polys = []
    for _ in range(rng.randint(1, 3) if count is None else count):
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
        if roughness > 0.0:
            m = _rough_vertex_count(roughness)
            phase = rng.uniform(0.0, 2.0 * math.pi)
        else:
            m = rng.randint(10, 14)
        offs = []
        for k in range(m):
            a = (k + rng.uniform(-0.15, 0.15)) * 2.0 * math.pi / m
            rr = r * rng.uniform(0.7, 1.15)
            if roughness > 0.0:
                low = math.sin(2.0 * math.pi * 2.0 * k / m + phase)   # two lobes around the blob
                high = rng.uniform(-1.0, 1.0)                         # per-vertex jag
                rr *= 1.0 + roughness * (0.3 * low + 0.35 * high)
            offs.append((rr * math.cos(a), rr * math.sin(a)))
        if inset > 0.0:
            cx, cy, offs = _inset_blotch(cx, cy, offs, size, side, inset)
        polys.append((cx, cy, [(cx + dx, cy + dy) for dx, dy in offs]))
    return polys


def _outline(pts: Sequence[tuple[float, float]], roughness: float) -> str:
    """Path data for a blotch outline: a smooth lobe at roughness 0, and a straight-edged
    polygon above it, so the edge reads as torn rather than round."""
    if roughness > 0.0:
        return "M" + " L".join(f"{_f(x)} {_f(y)}" for x, y in pts) + " Z"
    return _smooth_closed(pts)


def _drop_blotch_defaults(params: dict, inset: float, roughness: float, spread: float) -> None:
    """Remove parameters at their default from the clip-id key, so the ids, and so the
    output, of existing calls do not change."""
    if inset == 0:
        del params["inset"]
    if roughness == 0:
        del params["roughness"]
    if spread == 1.0:
        del params["spread"]


def blotch(seed: int, size: float, palette: Sequence[str], *,
           coverage: float = 0.45, side: str | None = None, color_index: int = 1,
           background: bool = True, inset: float = 0.0, roughness: float = 0.0,
           spread: float = 1.0) -> str:
    """1-3 large soft, wobbly blotches over the background.

    coverage: 0-1, scales blotch radius (about 0.12 to 0.62 of size).
    side: None, or "top"/"bottom"/"left"/"right" to bias the blotch centers
        toward that edge. The cut through the cell is the piece's transition.
    color_index: palette index of the blotch color (default: palette[1]).
    inset: 0 (default) lets blotches meet the cell edges, so they are clipped
        there. Above 0, each blotch, halo included, stays inside the cell by
        ``inset * size``. Blotches that cannot fit are scaled down. With a
        ``side``, the three edges other than that side are inset; the biased
        side is not, so the blotch still reaches it. Use 0.08 to keep a
        same-class neighbour from showing a hard cut.
    roughness: 0-1. 0 (default) gives the smooth lobes. Above 0 the outline is a
        straight-edged polygon of 16 to 28 vertices with seeded radial noise at
        two frequencies, so it reads as torn paper. With a ``side``, the mass is
        one band along that edge instead of separate lobes. Its depth follows
        ``coverage`` plus or minus 0.15 across the width, and the band reaches
        both corners of the edge, so neighbouring pieces join. In band mode the
        side edges are not inset, and ``inset`` only keeps the far edge clear.
    spread: 0-1, the share of the biased edge's width the band covers, centred.
        1 (default) covers the full width. Needs a ``side`` and roughness > 0.
    Blotches are not padded, so with ``inset=0`` they intentionally meet the
    edges as a visible boundary. Neighboring cells will differ there unless
    deliberately matched. To clip another texture to the same shape, use
    ``blotch_mask``.
    """
    params = _key_args(locals())
    _check_blotch_args(coverage, side, inset, roughness, spread)
    _drop_blotch_defaults(params, inset, roughness, spread)
    if not 0 <= color_index < len(palette):
        raise ValueError("color_index is out of range for palette")
    base = palette[0]
    color = palette[color_index]
    rng = random.Random(seed)
    parts = [_ground(base, size, background)]
    for cx, cy, pts in _blotch_polys(rng, size, coverage, side, inset=inset,
                                     roughness=roughness, spread=spread):
        halo = [(cx + (px - cx) * _HALO_SCALE, cy + (py - cy) * _HALO_SCALE) for px, py in pts]
        parts.append(f'<path d="{_outline(halo, roughness)}" fill="{color}" fill-opacity="0.3"/>')
        parts.append(f'<path d="{_outline(pts, roughness)}" fill="{color}"/>')
    return _wrap("blotch", seed, size, palette, params, "".join(parts))


def blotch_mask(seed: int, size: float, palette: Sequence[str], *,
                coverage: float = 0.45, side: str | None = None,
                count: int | None = None, inset: float = 0.0,
                roughness: float = 0.0, spread: float = 1.0) -> tuple[str, str]:
    """Clip path for a blotch-shaped region: ``(clip_svg, clip_id)``.

    ``clip_svg`` is a ``<clipPath id="clip_id">`` element holding only the blotch
    outlines (no fill, no halo). Put it in a ``<defs>`` and reference it with
    ``clip-path="url(#clip_id)"``. Parameters have the same meaning as in
    ``blotch``, including ``inset``, ``roughness`` and ``spread``. ``count`` sets the
    number of blotches, or band pieces in band mode (1-6); by default it is random,
    1 to 3, as in ``blotch``. With ``inset``, the outlines keep the halo margin that
    ``blotch`` uses, so the two share geometry.

    ``palette`` is accepted for parity with the painting primitives. A mask has
    no colour, so the palette is not read.
    """
    params = _key_args(locals())
    _check_blotch_args(coverage, side, inset, roughness, spread)
    _drop_blotch_defaults(params, inset, roughness, spread)
    if count is not None and not (isinstance(count, int) and 1 <= count <= 6):
        raise ValueError("count must be an integer in [1, 6], or None")
    rng = random.Random(seed)
    cid = _clip_id("blotch_mask", seed, size, palette, params)
    paths = "".join(
        f'<path d="{_outline(pts, roughness)}"/>'
        for _, _, pts in _blotch_polys(rng, size, coverage, side, count, inset,
                                       roughness, spread))
    return f'<clipPath id="{cid}">{paths}</clipPath>', cid


MOTIF_KINDS = ("disc", "ring", "silhouette_bird", "leaf", "fish", "boat",
               "window", "star", "drop", "hull", "fleck")
_MOTIF_ROTATIONS = ("none", "any", "flip")
_MOTIF_MARGIN = 0.08   # minimum gap between a motif and any cell edge, as a fraction of size


def _motif_unit(kind: str, fill: str, ink: str) -> str:
    """One motif in unit coordinates: centered on the origin, every point within
    radius 1, so any rotation or mirror stays within the scaled circumcircle.
    ``fill`` is the motif color; ``ink`` is the base color used for details."""
    if kind == "disc":
        return f'<circle cx="0" cy="0" r="1" fill="{fill}"/>'
    if kind == "ring":
        outer = "M-1 0A1 1 0 1 0 1 0A1 1 0 1 0-1 0Z"
        inner = "M-0.55 0A0.55 0.55 0 1 1 0.55 0A0.55 0.55 0 1 1-0.55 0Z"
        return f'<path d="{outer} {inner}" fill-rule="evenodd" fill="{fill}"/>'
    if kind == "silhouette_bird":
        # Two filled arches meeting at the body, with a small body ellipse.
        left = "M-0.95 0.15Q-0.5-0.7 0-0.05Q-0.5-0.05-0.95 0.15Z"
        right = "M0.95 0.15Q0.5-0.7 0-0.05Q0.5-0.05 0.95 0.15Z"
        return (f'<path d="{left} {right}" fill="{fill}"/>'
                f'<ellipse cx="0" cy="0" rx="0.24" ry="0.2" fill="{fill}"/>')
    if kind == "leaf":
        d = "M-1 0C-0.4-0.62 0.4-0.62 1 0C0.4 0.62-0.4 0.62-1 0Z"
        return (f'<g transform="rotate(-45)"><path d="{d}" fill="{fill}"/>'
                f'<line x1="-0.8" y1="0" x2="0.8" y2="0" stroke="{ink}" '
                f'stroke-width="0.09" stroke-linecap="round"/></g>')
    if kind == "fish":
        body = "M0.85 0Q0.2-0.8-0.45 0Q0.2 0.8 0.85 0Z"
        tail = "M-0.92-0.38L-0.4 0L-0.92 0.38Z"
        return (f'<path d="{body} {tail}" fill="{fill}"/>'
                f'<circle cx="0.4" cy="-0.1" r="0.09" fill="{ink}"/>')
    if kind == "boat":
        hull = "M-0.72 0.12L0.72 0.12L0.5 0.6L-0.5 0.6Z"
        sail = "M0.06-0.6L0.06 0.1L0.62 0.1Z"
        return (f'<path d="{hull} {sail}" fill="{fill}"/>'
                f'<line x1="0" y1="-0.6" x2="0" y2="0.12" stroke="{fill}" stroke-width="0.08"/>')
    if kind == "hull":
        # Boat hull only: a trapezoid with its waterline (bottom edge) at the origin.
        return f'<path d="M-0.85-0.35L0.85-0.35L0.5 0L-0.5 0Z" fill="{fill}"/>'
    if kind == "fleck":
        # Small soft irregular blob: seven fixed radii, smoothed, slightly translucent.
        radii = (0.95, 0.62, 0.82, 0.5, 0.9, 0.68, 0.78)
        pts = []
        for k, r in enumerate(radii):
            a = 0.3 + k * 2.0 * math.pi / len(radii)
            pts.append((r * math.cos(a), r * math.sin(a)))
        return f'<path d="{_smooth_closed(pts)}" fill="{fill}" fill-opacity="0.92"/>'
    if kind == "window":
        return (f'<rect x="-0.62" y="-0.78" width="1.24" height="1.56" rx="0.14" fill="{fill}"/>'
                f'<path d="M0-0.78V0.78M-0.62 0H0.62" stroke="{ink}" stroke-width="0.12"/>')
    if kind == "star":
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            r = 0.97 if k % 2 == 0 else 0.42
            pts.append((r * math.cos(a), r * math.sin(a)))
        return (f'<polygon points="{_points(pts)}" fill="{fill}" stroke="{fill}" '
                f'stroke-width="0.06" stroke-linejoin="round"/>')
    if kind == "drop":
        d = "M0-1C0.35-0.45 0.7-0.1 0.7 0.3A0.7 0.7 0 0 1-0.7 0.3C-0.7-0.1-0.35-0.45 0-1Z"
        return (f'<path d="{d}" fill="{fill}"/>'
                f'<ellipse cx="-0.3" cy="0.22" rx="0.11" ry="0.2" fill="{ink}" fill-opacity="0.8"/>')
    raise ValueError(f"kind must be one of {MOTIF_KINDS}, not {kind!r}")


def motif(seed: int, size: float, palette: Sequence[str], background: bool = True,
          kind: str = "disc", scale: float = 0.5, jitter: float = 0.08,
          rotation: str = "none", halo: float = 0.0, color_index: int = 1,
          halo_color_index: int = 2, offset: tuple[float, float] = (0.0, 0.0)) -> str:
    """One recognizable shape, centered in the cell with a small seeded jitter.

    The shape never comes within ``_MOTIF_MARGIN`` (8%) of a cell edge.

    kind: one of MOTIF_KINDS: disc, ring, silhouette_bird, leaf, fish, boat,
        window, star, drop, hull, fleck. ``hull`` is a boat hull without mast or
        sail, with its waterline at the origin, so ``offset`` can seat it on a
        horizon line. ``fleck`` is a small soft irregular blob.
    scale: diameter of the circle enclosing the shape, as a fraction of size.
        Must satisfy scale / 2 + jitter <= 0.42, so the default fits with jitter.
    jitter: maximum center offset per axis, as a fraction of size.
    offset: (dx, dy) fractions of size added to the center, before jitter. The
        center is then clamped so the enclosing circle stays inside the 8%
        margin: an offset that would push the shape past the margin stops at
        the margin instead of leaving the cell. The default (0, 0) is a no-op.
    rotation: "none"; "any" (seeded angle); or "flip" (mirror horizontally
        with 50% chance).
    halo: 0 for none. Above 0, 2 or 3 concentric circles of decreasing opacity
        are drawn behind the shape, out to radius (1 + halo) times the shape's
        radius. The halo is not kept inside the margin and may be clipped by
        the cell edge.
    color_index: palette index of the shape color (default: palette[1]).
    halo_color_index: palette index of the halo color (default: palette[2]).
    """
    params = _key_args(locals())
    if kind not in MOTIF_KINDS:
        raise ValueError(f"kind must be one of {MOTIF_KINDS}, not {kind!r}")
    if rotation not in _MOTIF_ROTATIONS:
        raise ValueError(f"rotation must be one of {_MOTIF_ROTATIONS}, not {rotation!r}")
    if scale <= 0.0:
        raise ValueError("scale must be positive")
    if jitter < 0.0:
        raise ValueError("jitter must be non-negative")
    if scale / 2.0 + jitter > 0.5 - _MOTIF_MARGIN + 1e-9:
        raise ValueError(
            f"scale {scale} with jitter {jitter} would reach the cell edge; "
            f"need scale / 2 + jitter <= {0.5 - _MOTIF_MARGIN:g}"
        )
    if halo < 0.0:
        raise ValueError("halo must be non-negative")
    for name, idx in (("color_index", color_index), ("halo_color_index", halo_color_index)):
        if not 0 <= idx < len(palette):
            raise ValueError(f"{name} is out of range for palette")
    if len(offset) != 2 or not all(math.isfinite(v) for v in offset):
        raise ValueError("offset must be a pair of finite numbers (dx, dy)")
    base = palette[0]
    color = palette[color_index]
    halo_color = palette[halo_color_index]

    rng = random.Random(seed)
    radius = size * scale / 2.0
    # Keep the enclosing circle inside the margin: the center may only range over
    # [margin + radius, size - margin - radius]. The validation above makes this non-empty.
    lo = size * _MOTIF_MARGIN + radius
    hi = size - lo
    cx = min(max(size * (0.5 + rng.uniform(-jitter, jitter) + offset[0]), lo), hi)
    cy = min(max(size * (0.5 + rng.uniform(-jitter, jitter) + offset[1]), lo), hi)
    angle = 0.0
    mirror = False
    if rotation == "any":
        angle = rng.uniform(0.0, 360.0)
    elif rotation == "flip":
        mirror = rng.random() < 0.5

    parts = [_ground(base, size, background)]
    if halo > 0.0:
        if halo <= 0.3:
            fracs, opacities = (1.0, 0.5), (0.18, 0.34)
        else:
            fracs, opacities = (1.0, 0.6, 0.3), (0.12, 0.22, 0.34)
        for f, op in zip(fracs, opacities):
            r = radius * (1.0 + halo * f)
            parts.append(
                f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r)}" '
                f'fill="{halo_color}" fill-opacity="{op}"/>'
            )
    sx = -radius if mirror else radius
    xf = f"translate({_f(cx)} {_f(cy)}) rotate({_f(angle)}) scale({_f(sx)} {_f(radius)})"
    parts.append(f'<g transform="{xf}">{_motif_unit(kind, color, base)}</g>')
    return _wrap("motif", seed, size, palette, params, "".join(parts))


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
