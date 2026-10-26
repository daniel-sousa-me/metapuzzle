"""Piece inventory: side profiles, shape types, classes, allowed rotations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .board import CORNERS, ROTATION_DEGREES, SIDES, Board

_ASYM = ("blank", "tab", "tab", "blank")  # N, E, S, W for an interior piece (rotation none)
_CORNER_FLATS = {"NW": (0, 3), "NE": (0, 1), "SE": (1, 2), "SW": (2, 3)}
_EDGE_ORDER = ("N", "S", "W", "E")


def flat_side_indices(shape_type: str, home: str | None) -> tuple[int, ...]:
    """Upright-frame side indices that are flat for a shape type and home."""
    if shape_type == "interior":
        return ()
    if shape_type == "corner":
        return _CORNER_FLATS[home or "NW"]
    if shape_type == "edge":
        return (SIDES.index(home or "N"),)
    raise ValueError(f"unknown shape_type {shape_type!r}")


def default_sides(shape_type: str, home: str | None, connectors: str = "asym", inner: str | None = None) -> tuple[str, ...]:
    """Side profiles (N, E, S, W) of a standard piece.

    connectors "asym": blank N/W, tab S/E (rotation none); "andro": all andro (rotation safe).
    `inner` overrides every non-flat side (e.g. "wild" for freely rotating corners).
    """
    base = list(_ASYM if connectors == "asym" else ("andro",) * 4)
    if inner is not None:
        base = [inner] * 4
    for d in flat_side_indices(shape_type, home):
        base[d] = "flat"
    return tuple(base)


@dataclass(frozen=True)
class Piece:
    """One physical piece. `sides` are profiles N, E, S, W in the piece's upright frame."""

    piece_id: int
    shape_type: str  # "corner" | "edge" | "interior" (label; `sides` is authoritative)
    cls: str = "any"
    allowed_rotations: frozenset = frozenset({0})
    home: str | None = None  # upright side/corner of the flat sides
    sides: tuple | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_rotations", frozenset(self.allowed_rotations))
        if not self.allowed_rotations <= set(ROTATION_DEGREES) or not self.allowed_rotations:
            raise ValueError(f"bad allowed_rotations {set(self.allowed_rotations)}")
        if self.sides is None:
            conn = "asym" if self.allowed_rotations == {0} else "andro"
            object.__setattr__(self, "sides", default_sides(self.shape_type, self.home, conn))
        else:
            object.__setattr__(self, "sides", tuple(self.sides))


def rotations_for_piece(board: Board, piece: Piece, slot_id: int, forced: int | None = None) -> tuple[int, ...]:
    """Rotations (degrees) at which `piece` fits `slot_id` at slot level."""
    return board.rotations_for(piece.sides, piece.allowed_rotations, slot_id, forced)


def _as_boards(boards) -> list[Board]:
    bl = [boards] if isinstance(boards, Board) else list(boards)
    if not bl:
        raise ValueError("need at least one board")
    if len({b.n_slots for b in bl}) != 1:
        raise ValueError("all boards must have the same number of slots")
    if len({(b.border, b.rotation) for b in bl}) != 1:
        raise ValueError("all boards must share border and rotation modes")
    return bl


def inventory_layout(
    boards: Board | Sequence[Board], extra_flat_pieces: int = 0, free_corners: bool = False
) -> list[tuple[str, str | None]]:
    """(shape_type, home) per piece for an inventory able to fill every given board.

    Border pieces number the maximum any board needs (per side without rotation, pooled
    with rotation) plus `extra_flat_pieces` flat-sided pieces that sit inside the picture
    in some solutions. Without rotation extras cycle N, S, W, E so that they can pair up
    into seams; use an even count.
    """
    bl = _as_boards(boards)
    n, b0 = bl[0].n_slots, bl[0]
    quarter = b0.rotation == "quarter"
    layout: list[tuple[str, str | None]] = []
    if b0.border == "standard":
        if quarter or free_corners:
            layout += [("corner", "NW")] * 4
        else:
            layout += [("corner", c) for c in CORNERS]
        if quarter:
            layout += [("edge", "N")] * max(b.kind_counts()["edge"] for b in bl)
        else:
            for side in _EDGE_ORDER:
                span = max((b.cols if side in "NS" else b.rows) - 2 for b in bl)
                layout += [("edge", side)] * span
    for i in range(extra_flat_pieces):
        layout.append(("edge", "N" if quarter else _EDGE_ORDER[i % 4]))
    if len(layout) > n:
        raise ValueError(f"inventory needs {len(layout)} border pieces but boards have only {n} slots")
    layout += [("interior", None)] * (n - len(layout))
    return layout


def make_inventory(
    boards: Board | Sequence[Board],
    cls: str = "any",
    extra_flat_pieces: int = 0,
    free_corners: bool = False,
) -> list[Piece]:
    """Piece inventory matching one board, or three boards with equal slot counts.

    extra_flat_pieces: flat-sided pieces beyond the perimeter (replacing interior pieces).
    free_corners: corner pieces may rotate (all four) even without rotation mode; their
    inner sides are "wild" connectors.
    """
    bl = _as_boards(boards)
    quarter = bl[0].rotation == "quarter"
    conn = "andro" if quarter else "asym"
    all_rots = frozenset(ROTATION_DEGREES)
    out = []
    for i, (shape, home) in enumerate(inventory_layout(bl, extra_flat_pieces, free_corners)):
        if shape == "corner" and free_corners:
            out.append(Piece(i, shape, cls, all_rots, home, default_sides(shape, home, conn, "wild")))
        else:
            allowed = all_rots if quarter else frozenset({0})
            out.append(Piece(i, shape, cls, allowed, home, default_sides(shape, home, conn)))
    return out


def piece_to_dict(p: Piece) -> dict:
    return {
        "piece_id": p.piece_id,
        "shape_type": p.shape_type,
        "home": p.home,
        "cls": p.cls,
        "allowed_rotations": sorted(p.allowed_rotations),
        "sides": list(p.sides),
    }


def piece_from_dict(d: dict) -> Piece:
    return Piece(
        d["piece_id"],
        d["shape_type"],
        d.get("cls", "any"),
        frozenset(d.get("allowed_rotations", [0])),
        d.get("home"),
        tuple(d["sides"]) if d.get("sides") else None,
    )
