"""Square-lattice board model: slots, 4-neighborhood, border constraints, side profiles."""
from __future__ import annotations

from dataclasses import dataclass

ROTATION_DEGREES = (0, 90, 180, 270)
SIDES = ("N", "E", "S", "W")
CORNERS = ("NW", "NE", "SE", "SW")
# (dx, dy) of the neighbor across side N, E, S, W
SIDE_DELTA = ((0, -1), (1, 0), (0, 1), (-1, 0))

# Edge profiles. "flat" mates only with "flat" (or the board boundary); tab~blank;
# "andro" mates with "andro"; "wild" is a placeholder connector that mates with any
# non-flat profile (extension point for keyed/custom connectors).
PROFILES = ("tab", "blank", "flat", "andro", "wild")


def mates(a: str, b: str) -> bool:
    """True if two touching side profiles are compatible."""
    if a == "flat" or b == "flat":
        return a == b
    if a == "wild" or b == "wild":
        return True
    return (a, b) in (("tab", "blank"), ("blank", "tab"), ("andro", "andro"))


@dataclass(frozen=True)
class Slot:
    """One lattice cell."""

    id: int
    x: int
    y: int
    kind: str  # "corner" | "edge" | "interior"
    home: str | None  # corner: NW..SW; edge: N/E/S/W; interior: None
    type: str  # "interior" | "edge_N" | "corner_NW" ...
    neighbors: tuple[int, ...]
    boundary_sides: tuple[int, ...] = ()  # side indices (N=0..W=3) on the board boundary


@dataclass
class Board:
    """A rectangular board of slots."""

    cols: int
    rows: int
    border: str  # "standard" | "tray"
    rotation: str  # "none" | "quarter"
    slots: list[Slot]

    @property
    def n_slots(self) -> int:
        return len(self.slots)

    @property
    def rotations(self) -> tuple[int, ...]:
        return (0,) if self.rotation == "none" else ROTATION_DEGREES

    @property
    def adjacencies(self) -> list[tuple[int, int]]:
        return [(s.id, n) for s in self.slots for n in s.neighbors if s.id < n]

    @property
    def n_adjacencies(self) -> int:
        return self.cols * (self.rows - 1) + self.rows * (self.cols - 1)

    def slot_at(self, x: int, y: int) -> int:
        return y * self.cols + x

    def kind_counts(self) -> dict[str, int]:
        out = {"corner": 0, "edge": 0, "interior": 0}
        for s in self.slots:
            out[s.kind] += 1
        return out

    def params(self) -> dict:
        return {"cols": self.cols, "rows": self.rows, "border": self.border, "rotation": self.rotation}

    def rotations_for(
        self,
        sides: tuple[str, ...],
        allowed,
        slot_id: int,
        forced: int | None = None,
    ) -> tuple[int, ...]:
        """Rotations (degrees) under which a piece with upright `sides` fits the slot.

        Slot-level test only: on a standard board every boundary side of the slot must
        present "flat". Contacts between neighboring pieces are checked pairwise by the
        solver, not here. A tray board constrains nothing at the boundary.
        """
        slot = self.slots[slot_id]
        out = []
        for r in sorted(allowed):
            if forced is not None and r != forced:
                continue
            q = r // 90
            if self.border == "standard" and any(sides[(d - q) % 4] != "flat" for d in slot.boundary_sides):
                continue
            out.append(r)
        return tuple(out)


def square_board(cols: int, rows: int, border: str = "standard", rotation: str = "none") -> Board:
    """Build a cols x rows square board. border: standard|tray; rotation: none|quarter."""
    if border not in ("standard", "tray"):
        raise ValueError(f"unknown border mode {border!r}")
    if rotation not in ("none", "quarter"):
        raise ValueError(f"unknown rotation mode {rotation!r}")
    if border == "standard" and (cols < 2 or rows < 2):
        raise ValueError("standard border needs cols >= 2 and rows >= 2")
    if cols < 1 or rows < 1:
        raise ValueError("board must be at least 1x1")
    slots: list[Slot] = []
    for y in range(rows):
        for x in range(cols):
            nbrs = tuple(
                (y + dy) * cols + (x + dx)
                for dx, dy in SIDE_DELTA
                if 0 <= x + dx < cols and 0 <= y + dy < rows
            )
            bsides = tuple(
                d for d, (dx, dy) in enumerate(SIDE_DELTA) if not (0 <= x + dx < cols and 0 <= y + dy < rows)
            )
            kind, home = "interior", None
            if border == "standard":
                top, bottom, left, right = y == 0, y == rows - 1, x == 0, x == cols - 1
                if (top or bottom) and (left or right):
                    kind = "corner"
                    home = ("N" if top else "S") + ("W" if left else "E")
                    home = {"NW": "NW", "NE": "NE", "SE": "SE", "SW": "SW"}[home]
                elif top or bottom or left or right:
                    kind = "edge"
                    home = "N" if top else "S" if bottom else "W" if left else "E"
            stype = "interior" if kind == "interior" else f"{kind}_{home}"
            slots.append(Slot(y * cols + x, x, y, kind, home, stype, nbrs, bsides))
    return Board(cols, rows, border, rotation, slots)
