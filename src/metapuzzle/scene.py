"""Per-solution class maps: parsing, validation, and inventory derivation."""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .board import ROTATION_DEGREES, Board
from .pieces import Piece, _as_boards, inventory_layout, make_inventory, rotations_for_piece


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


def pieces_from_scenes(boards, maps: Sequence[ClassMap], extra_flat_pieces: int = 0, free_corners: bool = False) -> list[Piece]:
    """One piece per cell of map A, carrying that cell's class.

    Piece types come from the inventory layout of the boards: cells on A's frame get
    flat-sided pieces that fit them; remaining pieces (interior, plus any extra
    flat-sided ones, spread evenly) fill A's interior cells.
    """
    bl = _boards3(boards)
    validate_scenes(bl, maps, free_corners, strict_border=False if extra_flat_pieces else None)
    base = make_inventory(bl, "any", extra_flat_pieces, free_corners)
    layout = inventory_layout(bl, extra_flat_pieces, free_corners)
    a_board, a_map = bl[0], maps[0]
    unused = list(range(len(base)))
    slot_piece: dict[int, int] = {}
    border = sorted((s for s in a_board.slots if s.kind != "interior"), key=lambda s: s.kind != "corner")
    for s in border:
        best = None
        for i in unused:
            if rotations_for_piece(a_board, base[i], s.id):
                if best is None or (layout[i][0] == s.kind) > (layout[best][0] == s.kind):
                    best = i
        if best is None:
            raise SceneError(f"no piece of the inventory fits border cell ({s.x},{s.y}) of map A")
        slot_piece[s.id] = best
        unused.remove(best)
    interior = [s for s in a_board.slots if s.id not in slot_piece]
    flat_left = [i for i in unused if layout[i][0] != "interior"]
    plain_left = [i for i in unused if layout[i][0] == "interior"]
    n_int = len(interior)
    stride = n_int / max(1, len(flat_left))
    flat_slots = {int(j * stride + stride / 2) for j in range(len(flat_left))}
    fl, pl = iter(flat_left), iter(plain_left)
    for j, s in enumerate(interior):
        slot_piece[s.id] = next(fl) if j in flat_slots else next(pl)
    out = []
    for s in a_board.slots:
        p = base[slot_piece[s.id]]
        out.append(Piece(p.piece_id, p.shape_type, a_map.cls[s.y][s.x], p.allowed_rotations, p.home, p.sides))
    return sorted(out, key=lambda p: p.piece_id)
