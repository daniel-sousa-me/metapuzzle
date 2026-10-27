"""Per-solution class maps: parsing, validation, and inventory derivation."""
from __future__ import annotations

import json
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .board import CORNERS, ROTATION_DEGREES, SIDE_DELTA, SIDES, Board
from .pieces import _CORNER_FLATS, Piece, build_valid_layout, default_sides


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
_RANK = {"corner": 0, "edge": 1, "interior": 2}


def _covers(home: int, rots) -> set[int]:
    """Frame positions (side or corner index, clockwise from N or NW) a piece covers at `rots`."""
    return {(home + r // 90) % 4 for r in rots}


def _add_seam_pieces(bl, maps, pools, used, total, rots_for, quarter, free_corners, extra, cap_share) -> None:
    """Append flat edge pieces to `pools` so each map's leftover flat pieces can form seams."""
    classes = list(pools)
    fixed = not free_corners and all(len(rots_for(c, "edge")) == 1 for c in classes)
    free = quarter and not free_corners and all(len(rots_for(c, "edge")) == 4 for c in classes)

    def room(c):
        return total[c] - len(pools[c])

    def pick_class(score=None):
        opts = [c for c in classes if room(c) > 0 and (fixed or len(rots_for(c, "edge")) == 4)]
        if not opts:
            raise SceneError("no class has room for the flat-sided pieces the smaller frames need")
        return max(opts, key=lambda c: ((score(c) if score else 0), room(c)))

    def add(c, side):
        pools[c].append(("edge", (side - min(x // 90 for x in rots_for(c, "edge"))) % 4))

    def eff(c, shape, home):  # side or corner a piece shows its flat at, without turning it further
        return (home + (next(iter(rots_for(c, shape))) // 90 if fixed else 0)) % 4

    def leftovers(k):
        return {c: [(sh, eff(c, sh, h)) for i, (sh, h) in enumerate(pools[c]) if i not in used[k][c]] for c in classes}

    c = None
    for j in range(extra):  # pairs of one class: the second piece takes the class of the first
        if j % 2 == 0 or room(c) <= 0:
            c = pick_class()
        add(c, (0, 2, 1, 3)[j % 4] if fixed else 0)
    if not (fixed or free):
        return
    if fixed:
        _pad_for_seams(bl, maps, pools, used, total, classes, leftovers, add, room, cap_share)
        return
    for _ in range(sum(total.values())):
        edges = [sum(sh == "edge" for lst in leftovers(k).values() for sh, _ in lst) for k in range(3)]
        corners = sum(sh == "corner" for lst in leftovers(0).values() for sh, _ in lst)
        if (edges[0] - 2 * corners) % 2 == 0 and min(edges) >= 2 * corners:
            return
        add(pick_class(), 0)


def _max_flow(supply: dict, demand: dict, cap: dict) -> int:
    """Largest number of units sent from supply classes to demand classes over capacitated class pairs."""
    res: dict = {}
    for a, n in supply.items():
        res[("s", ("a", a))] = n
    for b, n in demand.items():
        res[(("b", b), "t")] = n
    for (a, b), cp in cap.items():
        if a in supply and b in demand:
            res[(("a", a), ("b", b))] = cp
    adj: dict = {}
    for (u, v) in list(res):
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)
        res.setdefault((v, u), 0)
    total = 0
    while True:
        parent = {"s": None}
        queue = ["s"]
        for u in queue:
            for v in adj.get(u, ()):
                if v not in parent and res[(u, v)] > 0:
                    parent[v] = u
                    queue.append(v)
        if "t" not in parent:
            return total
        push, v = None, "t"
        while parent[v] is not None:
            push = res[(parent[v], v)] if push is None else min(push, res[(parent[v], v)])
            v = parent[v]
        v = "t"
        while parent[v] is not None:
            res[(parent[v], v)] -= push
            res[(v, parent[v])] += push
            v = parent[v]
        total += push


def _pad_for_seams(bl, maps, pools, used, total, classes, leftovers, add, room, cap_share) -> None:
    """Without rotation, add flat edge pieces until every map's leftovers can pair into seams.

    A seam pairs a d-flat piece at one interior cell with a (d+2)-flat piece at the neighbour in
    direction d, so the classes of the two pieces must be adjacent in that map. For each map the
    leftovers (corner partners taken off) are matched as a flow over class pairs, with a capacity of
    a share of the adjacent interior cell pairs. Padding goes on while a single piece or an opposite
    pair keeps reducing (or, on a plateau, not raising) the unmatched count summed over the maps; the
    inventory only grows, and the best state seen is kept.
    """
    cap = []  # per map, per d in (0, 1): class pair -> capacity
    for k in range(3):
        b, m = bl[k], maps[k]
        per_d = []
        for d in (0, 1):
            cnt: dict = {}
            for s in b.slots:
                if s.boundary_sides:
                    continue
                dx, dy = SIDE_DELTA[d]
                v = b.slot_at(s.x + dx, s.y + dy)
                if b.slots[v].boundary_sides:
                    continue
                key = (m.cls[s.y][s.x], m.cls[b.slots[v].y][b.slots[v].x])
                cnt[key] = cnt.get(key, 0) + 1
            per_d.append({key: int(n * cap_share) for key, n in cnt.items() if int(n * cap_share)})
        cap.append(per_d)
    cnt = [[{c: 0 for c in classes} for _ in range(4)] for _ in range(3)]  # per map, side: edges by class
    dem = [[0] * 4 for _ in range(3)]  # per map, side: partners the leftover corners need
    for k in range(3):
        for c, lst in leftovers(k).items():
            for sh, e in lst:
                if sh == "edge":
                    cnt[k][e][c] += 1
                else:
                    for f in _CORNER_FLATS[CORNERS[e]]:
                        dem[k][(f + 2) % 4] += 1
    memo: dict = {}

    def adjusted(k: int, side: int):
        """Leftover edges of `side` once corners have taken their partners from the fullest classes."""
        a, short = dict(cnt[k][side]), 0
        for _ in range(dem[k][side]):
            c = max(classes, key=a.get)
            if a[c] > 0:
                a[c] -= 1
            else:
                short += 1
        return a, short

    def val(k: int, d: int) -> int:
        key = (k, d, tuple(cnt[k][d].values()), tuple(cnt[k][d + 2].values()))
        if key not in memo:
            (a, sa), (b, sb) = adjusted(k, d), adjusted(k, d + 2)
            memo[key] = sum(a.values()) + sum(b.values()) - 2 * _max_flow(a, b, cap[k][d]) + sa + sb
        return memo[key]

    def pair_total(d: int) -> int:
        return sum(val(k, d) for k in range(3))

    def put(side, c, sign=1):
        for k in range(3):
            cnt[k][side][c] += sign

    cur = pair_total(0) + pair_total(1)
    pads: list = []
    best = (cur, 0)
    rnd = random.Random(0)
    stall = 0
    for _ in range(PAD_STEPS):
        if not cur or stall > PAD_STALL:
            break
        other = {0: pair_total(1), 1: pair_total(0)}
        options = [((s, c),) for s in range(4) for c in classes if room(c) > 0]
        options += [((d, a), ((d + 2) % 4, b)) for d in (0, 1) for a in classes for b in classes
                    if room(a) > 0 and room(b) > 0 and (a != b or room(a) > 1)]
        scored = []
        for opt in options:
            for s, c in opt:
                put(s, c)
            dd = opt[0][0] % 2
            scored.append((pair_total(dd) + other[dd], len(opt), rnd.random(), opt))
            for s, c in opt:
                put(s, c, -1)
        score, _, _, opt = min(scored, key=lambda x: x[:3])
        for s, c in opt:
            put(s, c)
            pads.append((c, s))
        cur = score
        stall += 1
        if cur < best[0]:
            best = (cur, len(pads))
            stall = 0
    for c, s in pads[: best[1]]:
        add(c, s)


PAD_STEPS = 300
PAD_STALL = 40
SEAM_CAP_SHARES = (0.75, 0.6, 0.45)  # share of adjacent cell pairs the padding search may count on


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
    class.

    Flat-sided pieces that frame one map sit inside a smaller frame, where they must form seams
    (two flat sides touching: a domino of two edge pieces, or a two-flat corner piece with two edge
    pieces in an L). The border inventory therefore covers the largest need of the three maps, and
    flat edge pieces are added, with classes chosen to suit all three maps, until each map's
    leftover flat pieces can pair up (opposite flat sides without rotation, an even number with
    rotation). `extra_flat_pieces` adds that many more flat edge pieces on top, spread over the
    classes (without rotation, in N/S then W/E pairs; an odd count gets one more partner). The
    automatic padding needs every class to be rotation-free or every class fully rotatable.

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

    # Greedy per class: pools[c] lists the physical frame pieces of class c as (shape, home).
    # used[k][c] holds the pool indices that fill map k's own border; the rest sit inside map k.
    pools: dict[str, list[tuple[str, int]]] = {c: [] for c in classes}
    a_pick: dict[int, tuple[str, int]] = {}  # map A slot -> (class, pool index)
    used: list[dict[str, set[int]]] = [{c: set() for c in classes} for _ in range(3)]
    for k in range(3):
        for c in classes:
            for slot_id, shape, key in need[k].get(c, []):
                rots = rots_for(c, shape)
                idx = next(
                    (i for i, (sh, h) in enumerate(pools[c]) if i not in used[k][c] and sh == shape and key in _covers(h, rots)),
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
                    idx = len(pools[c]) - 1
                used[k][c].add(idx)
                if k == 0:
                    a_pick[slot_id] = (c, idx)

    def assemble(pools):
        """One piece per cell of A: its border piece, else a spare flat piece, else a plain one."""
        spare: dict[str, list[tuple[str, int | None]]] = {}
        for c in classes:
            if len(pools[c]) > total[c]:
                raise SceneError(f"class {c!r} has {total[c]} cells, too few for its {len(pools[c])} flat-sided pieces")
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

    if a_board.border != "standard":
        return assemble(pools)
    base = {c: list(v) for c, v in pools.items()}
    shares = SEAM_CAP_SHARES if all(len(rots_for(c, "edge")) == 1 for c in classes) and not free_corners else (1.0,)
    for share in shares:
        pools = {c: list(v) for c, v in base.items()}
        _add_seam_pieces(bl, maps, pools, used, total, rots_for, quarter, free_corners, extra_flat_pieces, share)
        out = assemble(pools)
        if all(len(pools[c]) == len(used[k][c]) for k in range(3) for c in classes):
            break  # no flat piece sits inside any picture
        if _layouts_exist(bl, maps, out):
            break
    return out


def _layouts_exist(bl, maps, pieces) -> bool:
    """True when every map admits a valid placement of `pieces` (seams included)."""
    for b, m in zip(bl, maps):
        cls_at = [m.cls[s.y][s.x] for s in b.slots]
        forced = [m.rot[s.y][s.x] or None for s in b.slots]
        if build_valid_layout(b, pieces, cls_at, forced, random.Random(0), tries=4) is None:
            return False
    return True
