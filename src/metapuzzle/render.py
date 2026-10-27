"""SVG and PNG rendering of solutions: three placements, one piece artwork per piece id."""
from __future__ import annotations

import colorsys
import hashlib
import math
import random
from pathlib import Path
from typing import Mapping, Protocol
from xml.sax.saxutils import escape

import cairosvg

from .optimize import Solution

GRID_STYLES = {
    "faint": 'stroke="#000" stroke-opacity="0.22" stroke-width="0.6"',
    "strong": 'stroke="#000" stroke-opacity="0.9" stroke-width="1.2"',
}
N_DOTS = 12
DARKEN = 0.8  # dot shade relative to the piece colour
CUT_OPACITY = 0.35  # outline opacity of the cut overlay
CUT_BUMP = 0.15  # radius of a tab/blank bump, as a fraction of the cell size

FragmentCache = dict  # (piece_id: int, size: float) -> SVG fragment


class PieceDrawer(Protocol):
    """Draws one piece in a local frame whose square is (0,0)-(size,size).

    Must be a pure function of its arguments so the same piece always gets the same artwork.
    """

    def __call__(self, piece_id: str, cls: str, rng_seed: int, size: float) -> str: ...


def _num(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _attr(s: str) -> str:
    return escape(str(s), {'"': "&quot;"})


def _hex_to_rgb(color: str) -> tuple[float, float, float]:
    h = color.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"palette colour must be #rrggbb, got {color!r}")
    try:
        return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        raise ValueError(f"palette colour must be #rrggbb, got {color!r}") from None


def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{round(min(max(c, 0.0), 1.0) * 255):02x}" for c in rgb)


def _hash_rgb(cls: str) -> tuple[float, float, float]:
    """Stable (process-independent) pastel colour for a class label."""
    digest = hashlib.sha256(cls.encode("utf-8")).digest()
    hue = int.from_bytes(digest[:4], "big") / 2**32
    return colorsys.hls_to_rgb(hue, 0.66, 0.55)


def flat_class_drawer(palette: Mapping[str, str] | None = None) -> PieceDrawer:
    """Default drawer: a flat square coloured by class, with 12 darker dots placed by the seed.

    `palette` maps class labels to "#rrggbb"; other classes get a hash-derived hue.
    The piece id is not used, so pieces of the same class differ only by their seed.
    """
    fixed = {k: _hex_to_rgb(v) for k, v in (palette or {}).items()}

    def draw(piece_id: str, cls: str, rng_seed: int, size: float) -> str:
        base = fixed[cls] if cls in fixed else _hash_rgb(cls)
        dot = _rgb_to_hex(tuple(c * DARKEN for c in base))
        s = _num(size)
        rng = random.Random(rng_seed)
        parts = [f'<rect x="0" y="0" width="{s}" height="{s}" fill="{_rgb_to_hex(base)}"/>']
        for _ in range(N_DOTS):
            cx = size * rng.uniform(0.12, 0.88)
            cy = size * rng.uniform(0.12, 0.88)
            r = size * rng.uniform(0.04, 0.08)
            parts.append(f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(r)}" fill="{dot}"/>')
        return "".join(parts)

    return draw


def _fragment(piece, drawer: PieceDrawer, size: float, cache: FragmentCache) -> str:
    key = (piece.piece_id, float(size))
    frag = cache.get(key)
    if frag is None:
        frag = drawer(str(piece.piece_id), piece.cls, piece.piece_id, float(size))
        cache[key] = frag
    return frag


def _check_grid(grid: str) -> None:
    if grid != "none" and grid not in GRID_STYLES:
        raise ValueError(f"grid must be none, faint or strong; got {grid!r}")


def cut_outline_d(solution: Solution, solution_index: int, cell_size: float = 40, margin: float = 8) -> str:
    """SVG path data outlining every cell of placement `solution_index` as it is placed.

    Each side is one subpath in board coordinates. Its profile is the one facing that board
    direction after the piece's rotation (`sides[(d - r/90) % 4]`). A flat side is a straight
    line. A tab side bulges outward, a blank side bulges inward, and andro or wild (no
    orientation) bulge outward too, so every non-flat contact shows as a bump on each piece.
    A tab-blank contact draws one bump; an andro contact draws a full circle.
    """
    if solution_index not in (0, 1, 2):
        raise ValueError("solution_index must be 0, 1 or 2")
    board = solution.boards[solution_index]
    placement = solution.placements[solution_index]
    by_id = {p.piece_id: p for p in solution.pieces}
    by_slot = {slot: (pid, rot) for pid, (slot, rot) in placement.items()}
    s = float(cell_size)
    h = s / 2
    r = CUT_BUMP * s
    parts: list[str] = []
    for slot in board.slots:
        pid, rot = by_slot[slot.id]
        sides = by_id[pid].sides
        q = rot // 90
        x0 = margin + slot.x * s
        y0 = margin + slot.y * s
        corner = {"NW": (x0, y0), "NE": (x0 + s, y0), "SE": (x0 + s, y0 + s), "SW": (x0, y0 + s)}
        # (start corner, end corner, midpoint, unit vector start->end), clockwise, for N, E, S, W
        edges = (
            (corner["NW"], corner["NE"], (x0 + h, y0), (1, 0)),
            (corner["NE"], corner["SE"], (x0 + s, y0 + h), (0, 1)),
            (corner["SE"], corner["SW"], (x0 + h, y0 + s), (-1, 0)),
            (corner["SW"], corner["NW"], (x0, y0 + h), (0, -1)),
        )
        for d, (a, b, (mx, my), (tx, ty)) in enumerate(edges):
            profile = sides[(d - q) % 4]
            if profile == "flat":
                parts.append(f"M{_num(a[0])} {_num(a[1])}L{_num(b[0])} {_num(b[1])}")
                continue
            # Clockwise traversal: sweep 1 bulges to the left of travel (outward), sweep 0 inward.
            sweep = 0 if profile == "blank" else 1
            sx, sy = mx - r * tx, my - r * ty
            ex, ey = mx + r * tx, my + r * ty
            parts.append(
                f"M{_num(a[0])} {_num(a[1])}L{_num(sx)} {_num(sy)}"
                f"A{_num(r)} {_num(r)} 0 0 {sweep} {_num(ex)} {_num(ey)}L{_num(b[0])} {_num(b[1])}"
            )
    return "".join(parts)


def render_solution_svg(
    solution: Solution,
    solution_index: int,
    drawer: PieceDrawer,
    cell_size: float = 40,
    margin: float = 8,
    grid: str = "none",
    rotate: bool = True,
    labels: bool = False,
    cache: FragmentCache | None = None,
    cut_overlay: bool = False,
) -> str:
    """SVG of placement `solution_index` (0=A, 1=B, 2=C).

    Each slot gets one `<g data-slot data-piece>` group whose transform places and rotates the
    piece's fragment. Pass a shared `cache` to reuse fragments across solutions.
    With `cut_overlay`, every cell outline (flat, tab, blank; see `cut_outline_d`) is drawn on
    top of the artwork at low opacity, following the placed rotation.
    """
    if solution_index not in (0, 1, 2):
        raise ValueError("solution_index must be 0, 1 or 2")
    _check_grid(grid)
    cache = {} if cache is None else cache
    board = solution.boards[solution_index]
    placement = solution.placements[solution_index]
    by_id = {p.piece_id: p for p in solution.pieces}
    by_slot = {slot: (pid, rot) for pid, (slot, rot) in placement.items()}
    if set(by_slot) != set(range(board.n_slots)):
        raise ValueError("placement is not a bijection onto the board's slots")

    width = 2 * margin + board.cols * cell_size
    height = 2 * margin + board.rows * cell_size
    half = _num(cell_size / 2)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_num(width)}" height="{_num(height)}" '
        f'viewBox="0 0 {_num(width)} {_num(height)}">',
        f'<rect width="{_num(width)}" height="{_num(height)}" fill="#ffffff"/>',
    ]
    for slot in board.slots:
        pid, rot = by_slot[slot.id]
        x = margin + slot.x * cell_size
        y = margin + slot.y * cell_size
        angle = rot if rotate else 0
        frag = _fragment(by_id[pid], drawer, cell_size, cache)
        out.append(
            f'<g transform="translate({_num(x)},{_num(y)}) rotate({angle}, {half}, {half})" '
            f'data-slot="{slot.id}" data-piece="{pid}">{frag}</g>'
        )
    if grid != "none":
        out.append(f'<g fill="none" {GRID_STYLES[grid]}>')
        for slot in board.slots:
            x = margin + slot.x * cell_size
            y = margin + slot.y * cell_size
            out.append(f'<rect x="{_num(x)}" y="{_num(y)}" width="{_num(cell_size)}" height="{_num(cell_size)}"/>')
        out.append("</g>")
    if cut_overlay:
        width_px = max(0.5, 0.03 * cell_size)
        out.append(
            f'<path d="{cut_outline_d(solution, solution_index, cell_size, margin)}" fill="none" '
            f'stroke="#000" stroke-opacity="{CUT_OPACITY}" stroke-width="{_num(width_px)}"/>'
        )
    if labels:
        fs = max(6.0, cell_size * 0.22)
        for slot in board.slots:
            x = margin + slot.x * cell_size
            y = margin + slot.y * cell_size
            out.append(
                f'<text x="{_num(x + 2)}" y="{_num(y + fs)}" font-size="{_num(fs)}" '
                f'font-family="sans-serif" fill="#111">{by_slot[slot.id][0]}</text>'
            )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def render_pieces_svg(
    solution: Solution,
    drawer: PieceDrawer,
    cell_size: float = 40,
    margin: float = 8,
    cache: FragmentCache | None = None,
) -> str:
    """Contact sheet of every piece in piece-id order, upright, labelled with id and class."""
    cache = {} if cache is None else cache
    pieces = sorted(solution.pieces, key=lambda p: p.piece_id)
    n = len(pieces)
    ncols = max(1, math.ceil(math.sqrt(n)))
    nrows = math.ceil(n / ncols)
    fs = max(7.0, cell_size * 0.2)
    pad = 6
    cls_text = {p.piece_id: (p.cls if len(p.cls) <= 14 else p.cls[:13] + "~") for p in pieces}
    longest = max((max(len(f"#{p.piece_id}"), len(cls_text[p.piece_id])) for p in pieces), default=1)
    pitch_x = max(cell_size, 0.6 * fs * longest) + 2 * pad
    pitch_y = cell_size + 2.6 * fs + 2 * pad
    width = 2 * margin + ncols * pitch_x
    height = 2 * margin + nrows * pitch_y
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_num(width)}" height="{_num(height)}" '
        f'viewBox="0 0 {_num(width)} {_num(height)}">',
        f'<rect width="{_num(width)}" height="{_num(height)}" fill="#ffffff"/>',
    ]
    for i, p in enumerate(pieces):
        r, c = divmod(i, ncols)
        x0 = margin + c * pitch_x + (pitch_x - cell_size) / 2
        y0 = margin + r * pitch_y + pad
        cx = x0 + cell_size / 2
        frag = _fragment(p, drawer, cell_size, cache)
        out.append(f'<g data-piece="{p.piece_id}" data-cls="{_attr(p.cls)}">')
        out.append(f'<g transform="translate({_num(x0)},{_num(y0)})">{frag}</g>')
        out.append(
            f'<rect x="{_num(x0)}" y="{_num(y0)}" width="{_num(cell_size)}" height="{_num(cell_size)}" '
            f'fill="none" stroke="#888" stroke-width="0.6"/>'
        )
        base1 = y0 + cell_size + fs
        out.append(
            f'<text x="{_num(cx)}" y="{_num(base1)}" font-size="{_num(fs)}" font-family="sans-serif" '
            f'text-anchor="middle" fill="#111">#{p.piece_id}</text>'
        )
        out.append(
            f'<text x="{_num(cx)}" y="{_num(base1 + 1.2 * fs)}" font-size="{_num(fs)}" font-family="sans-serif" '
            f'text-anchor="middle" fill="#444">{_attr(cls_text[p.piece_id])}</text>'
        )
        out.append("</g>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


def render_solution_png(svg: str, path: str | Path, scale: float = 1.0) -> Path:
    """Rasterise an SVG string to PNG with cairosvg. Pixel size is the SVG size times `scale`."""
    path = Path(path)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(path), scale=scale)
    return path


def render_all(
    solution: Solution,
    drawer: PieceDrawer,
    out_dir: str | Path,
    basename: str,
    *,
    cell_size: float = 40,
    margin: float = 8,
    grid: str = "none",
    rotate: bool = True,
    labels: bool = False,
    scale: float = 1.0,
) -> dict[str, Path]:
    """Write `basename-A/B/C.svg` and `.png`, plus `basename-pieces.png` (contact sheet).

    All four images share one fragment cache, so each piece is drawn once and looks identical.
    Returns a mapping from file label (e.g. "A.svg", "pieces.png") to the written path.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cache: FragmentCache = {}
    written: dict[str, Path] = {}
    for k, name in enumerate("ABC"):
        svg = render_solution_svg(
            solution, k, drawer, cell_size=cell_size, margin=margin, grid=grid,
            rotate=rotate, labels=labels, cache=cache,
        )
        svg_path = out / f"{basename}-{name}.svg"
        svg_path.write_text(svg, encoding="utf-8")
        written[f"{name}.svg"] = svg_path
        written[f"{name}.png"] = render_solution_png(svg, out / f"{basename}-{name}.png", scale)
    sheet = render_pieces_svg(solution, drawer, cell_size=cell_size, margin=margin, cache=cache)
    written["pieces.png"] = render_solution_png(sheet, out / f"{basename}-pieces.png", scale)
    return written
