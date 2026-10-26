"""Per-solution class maps: parsing, validation, and inventory derivation."""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .board import CORNERS, ROTATION_DEGREES, SIDES, Board
from .pieces import Piece, default_sides


class SceneError(ValueError):
    """Raised when class maps are malformed or inconsistent."""


@dataclass
class ClassMap:
    """Grid of class labels (rows x cols) plus forced rotations (0 = unconstrained)."""

    cls: list[list[str]]
    rot: list[list[int]]

    @property
    def rows(self) -> int:
        return len(self.cls)

    @property
    def cols(self) -> int:
        return len(self.cls[0]) if self.cls else 0

    def histogram(self) -> Counter:
        return Counter(c for row in self.cls for c in row)

    def tokens(self) -> list[list[str]]:
        return [[c if r == 0 else f"{c}@{r}" for c, r in zip(cr, rr)] for cr, rr in zip(self.cls, self.rot)]

    @classmethod
    def from_tokens(cls, rows: Sequence[Sequence[str]]) -> "ClassMap":
        if not rows or not rows[0]:
            raise SceneError("empty class map")
        if len({len(r) for r in rows}) != 1:
            raise SceneError("class map rows have different lengths")
        parsed = [[parse_token(t) for t in r] for r in rows]
        return cls([[c for c, _ in r] for r in parsed], [[o for _, o in r] for r in parsed])


def parse_token(tok: str) -> tuple[str, int]:
    """'sky@90' -> ('sky', 90); 'sky@0' == 'sky'."""
    label, sep, rot = tok.partition("@")
    if not label or "@" in rot:
        raise SceneError(f"bad token {tok!r}")
    if not sep:
        return label, 0
    try:
        r = int(rot)
    except ValueError:
        raise SceneError(f"bad rotation in token {tok!r}") from None
    if r not in ROTATION_DEGREES:
        raise SceneError(f"rotation in {tok!r} must be one of {ROTATION_DEGREES}")
    return label, r


def parse_text(text: str) -> list[ClassMap]:
    """Parse text: rows of whitespace-separated tokens; blank lines separate maps; '#' comments."""
    blocks: list[list[list[str]]] = [[]]
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            if blocks[-1]:
                blocks.append([])
            continue
        blocks[-1].append(line.split())
    return [ClassMap.from_tokens(b) for b in blocks if b]


def _maps_from_json(data) -> list[ClassMap]:
    grids = data["maps"] if isinstance(data, dict) else data
    out = []
    for g in grids:
        rows = [r.split() if isinstance(r, str) else list(r) for r in g]
        out.append(ClassMap.from_tokens(rows))
    return out


def load_scenes(paths: str | Path | Sequence[str | Path]) -> list[ClassMap]:
    """Load 3 maps: three files (one map each), or one text/JSON file holding all three."""
    plist = [paths] if isinstance(paths, (str, Path)) else list(paths)
    maps: list[ClassMap] = []
    for p in plist:
        text = Path(p).read_text()
        if Path(p).suffix.lower() == ".json":
            try:
                maps += _maps_from_json(json.loads(text))
            except (KeyError, TypeError, json.JSONDecodeError) as e:
                raise SceneError(f"bad scene JSON {p}: {e}") from e
        else:
            maps += parse_text(text)
    if len(maps) != 3:
        raise SceneError(f"expected 3 class maps, found {len(maps)}")
    return maps


def _boards3(boards) -> list[Board]:
    bl = [boards] * 3 if isinstance(boards, Board) else list(boards)
    if len(bl) != 3:
        raise SceneError("need one board or three boards")
    return bl


def validate_scenes(boards, maps: Sequence[ClassMap], free_corners: bool = False, strict_border: bool | None = None) -> None:
    """Raise SceneError unless the three maps fit the boards and are mutually consistent.

    Border-side class counts are compared only when all boards have the same shape
    (strict_border=None) or strict_border=True; pass False when flat-sided extras make
    the border inventory larger than the perimeter.
    """
    bl = _boards3(boards)
    if len(maps) != 3:
        raise SceneError(f"expected 3 class maps, got {len(maps)}")
    for k, (m, b) in enumerate(zip(maps, bl)):
        if (m.cols, m.rows) != (b.cols, b.rows):
            raise SceneError(f"map {'ABC'[k]} is {m.cols}x{m.rows} but board is {b.cols}x{b.rows}")
        for row in m.cls:
            for c in row:
                if re.search(r"\s|@", c):
                    raise SceneError(f"bad class label {c!r}")
        for y in range(m.rows):
            for x in range(m.cols):
                if m.rot[y][x]:
                    if b.rotation != "quarter":
                        raise SceneError(f"map {'ABC'[k]} cell ({x},{y}): orientation suffix needs rotation 'quarter'")
                    if b.slots[b.slot_at(x, y)].kind != "interior":
                        raise SceneError(f"map {'ABC'[k]} cell ({x},{y}): orientation suffix not allowed on border cells")
    h0 = maps[0].histogram()
    for k in (1, 2):
        if maps[k].histogram() != h0:
            diff = (maps[k].histogram() - h0) + (h0 - maps[k].histogram())
            raise SceneError(f"class histograms of maps A and {'ABC'[k]} differ: {dict(diff)}")
    same_shape = len({(b.cols, b.rows) for b in bl}) == 1
    if strict_border is None:
        strict_border = same_shape
    if not strict_border or bl[0].border != "standard":
        return
    per_side = bl[0].rotation == "none"

    def border_hist(m: ClassMap, b: Board) -> dict:
        out: dict = {}
        for s in b.slots:
            if s.kind == "interior":
                continue
            key = (s.kind, s.home) if (per_side and not (s.kind == "corner" and free_corners)) else (s.kind, None)
            out.setdefault(key, Counter())[m.cls[s.y][s.x]] += 1
        return out

    ref = border_hist(maps[0], bl[0])
    for k in (1, 2):
        cur = border_hist(maps[k], bl[k])
        for key in set(ref) | set(cur):
            if ref.get(key, Counter()) != cur.get(key, Counter()):
                where = f"{key[0]} {key[1]}" if key[1] else key[0]
                raise SceneError(f"border class counts differ between maps A and {'ABC'[k]} at {where}")


ALL_ROTATIONS = frozenset(ROTATION_DEGREES)
_EXTRA_HOMES = (0, 2, 3, 1)  # N, S, W, E: extra flat pieces cycle so their flats pair up in seams
_RANK = {"corner": 0, "edge": 1, "interior": 2}


def _covers(home: int, rots) -> set[int]:
    """Frame positions (side or corner index, clockwise from N or NW) a piece covers at `rots`."""
    return {(home + r // 90) % 4 for r in rots}


def pieces_from_scenes(
    boards,
    maps: Sequence[ClassMap],
    extra_flat_pieces: int = 0,
    free_corners: bool = False,
    allowed_rotations: Mapping[str, Iterable[int]] | None = None,
) -> list[Piece]:
    """One physical piece per cell of map A, each carrying that cell's class.

    The inventory is derived class by class. Each border cell of a class, in each of the three
    maps, needs a piece of that class whose flat side(s) cover the cell at one of the class's
    allowed rotations. A directional class (rotations {0}) keeps each piece's side, so its border
    cells are matched side by side across the maps: each side gets as many pieces as the map
    needing most of them there. A rotatable class pools its border cells, since any piece covers
    any side. Pieces left over, and the plain interior pieces, fill the rest of A's cells of the
    class. `extra_flat_pieces` flat-sided pieces go to A's interior, spread evenly.

    allowed_rotations maps class -> rotations (degrees). Classes it omits get the board default:
    all four in quarter mode, {0} otherwise (corners of free_corners get all four).
    Raises SceneError naming the class and side when a class has too few cells for its border.
    """
    bl = _boards3(boards)
    validate_scenes(bl, maps, free_corners, strict_border=False if extra_flat_pieces else None)
    a_board, a_map = bl[0], maps[0]
    quarter = a_board.rotation == "quarter"
    conn = "andro" if quarter else "asym"
    given = dict(allowed_rotations or {})

    def rots_for(cls: str, shape: str) -> frozenset[int]:
        if cls in given:
            rots = frozenset(given[cls])
        elif quarter or (free_corners and shape == "corner"):
            rots = ALL_ROTATIONS
        else:
            rots = frozenset({0})
        if not rots or not rots <= ALL_ROTATIONS:
            raise SceneError(f"class {cls!r}: allowed rotations {sorted(rots)} must be a non-empty subset of {ROTATION_DEGREES}")
        return rots

    total = a_map.histogram()
    classes = sorted(total)
    # Border cells per map and class: (slot id, shape, side index or corner index); corners first.
    need: list[dict[str, list[tuple[int, str, int]]]] = [{} for _ in range(3)]
    for k in range(3):
        for s in bl[k].slots:
            if s.kind != "interior":
                key = SIDES.index(s.home) if s.kind == "edge" else CORNERS.index(s.home)
                need[k].setdefault(maps[k].cls[s.y][s.x], []).append((s.id, s.kind, key))
        for lst in need[k].values():
            lst.sort(key=lambda d: d[1] != "corner")
    interior = [s for s in a_board.slots if s.kind == "interior"]
    if extra_flat_pieces > len(interior):
        raise SceneError(f"{extra_flat_pieces} extra flat pieces do not fit the {len(interior)} interior cells of map A")
    if extra_flat_pieces:  # extras are flat-sided edge pieces in A's interior, evenly spread
        stride = len(interior) / extra_flat_pieces
        for j in range(extra_flat_pieces):
            s = interior[int(j * stride + stride / 2)]
            key = 0 if quarter else _EXTRA_HOMES[j % 4]
            need[0].setdefault(a_map.cls[s.y][s.x], []).append((s.id, "edge", key))

    # Greedy per class: pools[c] lists the physical frame pieces of class c as (shape, home).
    pools: dict[str, list[tuple[str, int]]] = {c: [] for c in classes}
    a_pick: dict[int, tuple[str, int]] = {}  # map A slot -> (class, pool index)
    for k in range(3):
        for c in classes:
            used: list[bool] = [False] * len(pools[c])
            for slot_id, shape, key in need[k].get(c, []):
                rots = rots_for(c, shape)
                idx = next(
                    (i for i, (sh, h) in enumerate(pools[c]) if not used[i] and sh == shape and key in _covers(h, rots)),
                    None,
                )
                if idx is None:
                    if len(pools[c]) == total[c]:
                        cell = bl[k].slots[slot_id]
                        where = f"{SIDES[key]} side" if shape == "edge" else f"{CORNERS[key]} corner"
                        raise SceneError(
                            f"class {c!r} (allowed rotations {sorted(rots)}) has {total[c]} cells, too few for its "
                            f"border pieces: map {'ABC'[k]} cell ({cell.x},{cell.y}) needs another piece with its "
                            f"{where} flat"
                        )
                    pools[c].append((shape, (key - min(r // 90 for r in rots)) % 4))
                    used.append(False)
                    idx = len(pools[c]) - 1
                used[idx] = True
                if k == 0:
                    a_pick[slot_id] = (c, idx)

    # Fill A's cells: picked pieces first, then leftover frame pieces, then plain interior pieces.
    spare: dict[str, list[tuple[str, int | None]]] = {}
    for c in classes:
        taken = {idx for cls_, idx in a_pick.values() if cls_ == c}
        leftover = [pools[c][i] for i in range(len(pools[c])) if i not in taken]
        spare[c] = leftover + [("interior", None)] * (total[c] - len(pools[c]))
    out: list[Piece] = []
    for pid, s in enumerate(sorted(a_board.slots, key=lambda s: _RANK[s.kind])):
        c = a_map.cls[s.y][s.x]
        if s.id in a_pick:
            shape, home = pools[c][a_pick[s.id][1]]
        else:
            shape, home = spare[c].pop(0)
        name = None if home is None else (SIDES[home] if shape == "edge" else CORNERS[home])
        inner = "wild" if shape == "corner" and free_corners else None
        out.append(Piece(pid, shape, c, rots_for(c, shape), name, default_sides(shape, name, conn, inner)))
    return out
