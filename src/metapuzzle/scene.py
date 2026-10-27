"""Per-solution class maps: parsing, validation, and inventory derivation.

Tokens: ``cls`` (a class label), ``cls@R`` (R in 0, 90, 180, 270: the piece at that cell must
sit at rotation R), and ``cls@*`` (any rotation: the escape for a forced class).

Orientation rule, applied across the three maps by ``load_scenes`` and ``parse_text``: if ANY
token of a class in any map carries an explicit ``@R`` suffix (``@0`` counts), every token of
that class is orientation-forced. Bare and ``@0`` tokens force rotation 0, ``@R`` forces R, and
``@*`` leaves that one cell free. A class with no explicit suffix anywhere stays unconstrained,
so its pieces may rotate in quarter mode.
"""
from __future__ import annotations

import json
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .board import CORNERS, ROTATION_DEGREES, SIDE_DELTA, SIDES, Board
from .pieces import _CORNER_FLATS, Piece, SeamPlanner, SeamSpace, build_valid_layout, default_sides


class SceneError(ValueError):
    """Raised when class maps are malformed or inconsistent."""


class _ForcedZero(int):
    """Rotation 0 that is forced, as opposed to the plain 0 that means unconstrained.

    The solver reads cells as ``rot or None``, so this int is truthy. It still equals 0 everywhere else.
    """

    def __bool__(self) -> bool:
        return True


FORCED_ZERO = _ForcedZero(0)
ANY_ROTATION = "*"


@dataclass
class ClassMap:
    """Grid of class labels (rows x cols) plus per-cell rotations.

    ``rot`` cell values: plain 0 = unconstrained (any rotation); ``FORCED_ZERO`` = rotation 0 is
    forced; 90, 180, 270 = forced. ``forced`` lists the classes orientation-forced across the
    whole scene set (module docstring); it decides how unconstrained cells of such classes are
    written back as ``cls@*``.
    """

    cls: list[list[str]]
    rot: list[list[int]]
    forced: frozenset = frozenset()

    @property
    def rows(self) -> int:
        return len(self.cls)

    @property
    def cols(self) -> int:
        return len(self.cls[0]) if self.cls else 0

    def histogram(self) -> Counter:
        return Counter(c for row in self.cls for c in row)

    def tokens(self) -> list[list[str]]:
        """Token rows that ``from_tokens`` reads back to the same map."""
        forced = self.forced | {c for cr, rr in zip(self.cls, self.rot) for c, r in zip(cr, rr) if r}
        out = []
        for cr, rr in zip(self.cls, self.rot):
            row = []
            for c, r in zip(cr, rr):
                if isinstance(r, _ForcedZero):
                    row.append(f"{c}@0")
                elif r:
                    row.append(f"{c}@{r}")
                else:
                    row.append(f"{c}@{ANY_ROTATION}" if c in forced else c)
            out.append(row)
        return out

    @classmethod
    def from_tokens(cls, rows: Sequence[Sequence[str]]) -> "ClassMap":
        """One map from token rows. The orientation rule sees only this map; use ``load_scenes`` for the set."""
        return _maps_from_rows([rows])[0]


def _split_token(tok: str) -> tuple[str, int | None, bool]:
    """(label, rotation, explicit). Rotation is None for ``@*``; explicit is False for a bare label."""
    label, sep, rot = tok.partition("@")
    if not label or "@" in rot:
        raise SceneError(f"bad token {tok!r}")
    if not sep:
        return label, 0, False
    if rot == ANY_ROTATION:
        return label, None, True
    try:
        r = int(rot)
    except ValueError:
        raise SceneError(f"bad rotation in token {tok!r}") from None
    if r not in ROTATION_DEGREES:
        raise SceneError(f"rotation in {tok!r} must be one of {ROTATION_DEGREES}")
    return label, r, True


def parse_token(tok: str) -> tuple[str, int]:
    """'sky@90' -> ('sky', 90); 'sky@0' and 'sky' -> ('sky', 0); 'sky@*' -> ('sky', 0), unconstrained."""
    label, rot, _ = _split_token(tok)
    return label, rot or 0


def _text_grids(text: str) -> list[list[list[str]]]:
    """Token rows per map in text: blank lines separate maps; '#' starts a comment."""
    blocks: list[list[list[str]]] = [[]]
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            if blocks[-1]:
                blocks.append([])
            continue
        blocks[-1].append(line.split())
    return [b for b in blocks if b]


def _json_grids(data) -> list[list[list[str]]]:
    grids = data["maps"] if isinstance(data, dict) else data
    return [[r.split() if isinstance(r, str) else list(r) for r in g] for g in grids]


def _maps_from_rows(grids: Sequence[Sequence[Sequence[str]]]) -> list[ClassMap]:
    """Parse token grids into maps, applying the orientation rule across all of them."""
    parsed = []
    for rows in grids:
        if not rows or not rows[0]:
            raise SceneError("empty class map")
        if len({len(r) for r in rows}) != 1:
            raise SceneError("class map rows have different lengths")
        parsed.append([[_split_token(t) for t in r] for r in rows])
    forced = frozenset(
        lbl for g in parsed for row in g for lbl, rot, explicit in row if explicit and rot is not None
    )

    def cell(lbl: str, rot: int | None) -> int:
        if rot is None:
            return 0
        return FORCED_ZERO if rot == 0 and lbl in forced else rot

    return [
        ClassMap(
            [[lbl for lbl, _, _ in row] for row in g],
            [[cell(lbl, rot) for lbl, rot, _ in row] for row in g],
            forced,
        )
        for g in parsed
    ]


def parse_text(text: str) -> list[ClassMap]:
    """Parse text: rows of whitespace-separated tokens; blank lines separate maps; '#' comments."""
    return _maps_from_rows(_text_grids(text))


def load_scenes(paths: str | Path | Sequence[str | Path]) -> list[ClassMap]:
    """Load 3 maps: three files (one map each), or one text/JSON file holding all three.

    The orientation rule (module docstring) is applied across all three maps together.
    """
    plist = [paths] if isinstance(paths, (str, Path)) else list(paths)
    grids: list[list[list[str]]] = []
    for p in plist:
        text = Path(p).read_text()
        if Path(p).suffix.lower() == ".json":
            try:
                grids += _json_grids(json.loads(text))
            except (KeyError, TypeError, json.JSONDecodeError) as e:
                raise SceneError(f"bad scene JSON {p}: {e}") from e
        else:
            grids += _text_grids(text)
    if len(grids) != 3:
        raise SceneError(f"expected 3 class maps, found {len(grids)}")
    return _maps_from_rows(grids)


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
                if m.rot[y][x] != 0:  # explicit nonzero suffix; forced 0 (inferred or @0) is always allowed
                    # Frame cells may carry one too: their piece's flat side is then fixed by the rotation.
                    if b.rotation != "quarter":
                        raise SceneError(f"map {'ABC'[k]} cell ({x},{y}): orientation suffix needs rotation 'quarter'")
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


def _assign_homes(needs: Sequence[frozenset[int]], homes: Sequence[int]) -> list[int | None]:
    """Maximum matching of needs to pieces: needs[u] is the set of homes a need accepts.

    Returns, per need, the index into `homes` of its piece, or None when it has no piece.
    """
    owner: dict[int, int] = {}

    def augment(u: int, seen: set[int]) -> bool:
        for j, h in enumerate(homes):
            if j in seen or h not in needs[u]:
                continue
            seen.add(j)
            if j not in owner or augment(owner[j], seen):
                owner[j] = u
                return True
        return False

    for u in range(len(needs)):
        augment(u, set())
    out: list[int | None] = [None] * len(needs)
    for j, u in owner.items():
        out[u] = j
    return out


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
    strict_border: bool = False,
) -> list[Piece]:
    """One physical piece per cell of map A, each carrying that cell's class.

    The inventory is derived class by class. Each border cell of a class, in each of the three
    maps, needs a piece of that class whose flat side(s) cover the cell at one of the class's
    allowed rotations (a forced cell: at its forced rotation). A piece whose canonical flat side is
    h shows that flat at side (h + r/90) mod 4 when turned by r, so a cell on side `key` needs
    h = (key - r/90) mod 4; corners work the same on corner indices, with the pair of flat sides
    turned together. A directional class (rotations {0}) and a forced cell admit one home; a
    rotatable class admits all four, so its border cells pool. Each map is matched class by class
    against the same physical pool: the pool grows to the most any map needs per home, and the
    rotatable needs take what is left. Pieces left over, and the plain interior pieces, fill the
    rest of A's cells of the class.

    Flat-sided pieces that frame one map sit inside a smaller frame, where they must form seams
    (two flat sides touching: a domino of two edge pieces, or a two-flat corner piece with two edge
    pieces in an L). The border inventory therefore covers the largest need of the three maps, and
    flat edge pieces are added, with classes chosen to suit all three maps, until each map's
    leftover flat pieces can pair up (opposite flat sides without rotation, an even number with
    rotation). `extra_flat_pieces` adds that many more flat edge pieces on top, spread over the
    classes (without rotation, in N/S then W/E pairs; an odd count gets one more partner). The
    automatic padding needs every class to be rotation-free or every class fully rotatable.
    Forced frame cells (module docstring) are matched as above. The seam padding is conservative
    about forced rotations: it counts leftover flat pieces by class and ignores their rotations,
    and `_layouts_exist` then confirms that each map admits a valid layout.

    allowed_rotations maps class -> rotations (degrees). Classes it omits get the board default:
    all four in quarter mode, {0} otherwise (corners of free_corners get all four).
    Raises SceneError naming the class and side when a class has too few cells for its border.
    """
    bl = _boards3(boards)
    differ = False
    if not extra_flat_pieces:
        try:
            validate_scenes(bl, maps, free_corners, strict_border=True)
        except SceneError as e:
            if "border class counts" not in str(e):
                raise
            if strict_border:
                validate_scenes(bl, maps, free_corners)  # the classic rule: raises for boards of one shape
            differ = True  # frame class mixes differ: cross-class seams must absorb the difference
    validate_scenes(bl, maps, free_corners, strict_border=False)
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
    need: list[dict[str, list[tuple[int, str, int, int | None]]]] = [{} for _ in range(3)]
    for k in range(3):
        for s in bl[k].slots:
            if s.kind != "interior":
                key = SIDES.index(s.home) if s.kind == "edge" else CORNERS.index(s.home)
                forced = maps[k].rot[s.y][s.x] or None
                need[k].setdefault(maps[k].cls[s.y][s.x], []).append(
                    (s.id, s.kind, key, None if forced is None else int(forced)))
        for lst in need[k].values():
            lst.sort(key=lambda d: d[1] != "corner")
    interior = [s for s in a_board.slots if s.kind == "interior"]
    if extra_flat_pieces > len(interior):
        raise SceneError(f"{extra_flat_pieces} extra flat pieces do not fit the {len(interior)} interior cells of map A")

    # Frame pieces, class by class. pools[c] lists the physical frame pieces of class c as (shape, home),
    # home being the canonical flat position (side or corner index). At rotation r a piece with home h
    # shows its flat at (h + r/90) % 4, so a frame cell on side (or corner) `key` takes a piece whose
    # home is in {(key - r/90) % 4 : r allowed}: one home for a forced cell or a directional class,
    # all four for a rotatable one. Phase 1 places the one-home needs map by map (the pool grows to the
    # most any map needs per home). Phase 2 matches the other needs into the pool with augmenting paths
    # and adds a piece only where a need has no match. used[k][c] holds the pool indices that fill
    # map k's own border; the rest sit inside map k.
    pools: dict[str, list[tuple[str, int]]] = {c: [] for c in classes}
    used: list[dict[str, set[int]]] = [{c: set() for c in classes} for _ in range(3)]
    picks: list[dict[int, tuple[str, int]]] = [{} for _ in range(3)]  # map k: border slot -> (class, pool index)
    homes_of: list[dict[str, list[tuple[int, str, int, frozenset[int]]]]] = [{} for _ in range(3)]
    for k in range(3):
        for c in classes:
            for slot_id, shape, key, forced in need[k].get(c, []):
                allowed = rots_for(c, shape)
                rots = allowed
                if forced is not None:  # a forced border cell needs a piece showing its flat at that rotation
                    cell = bl[k].slots[slot_id]
                    if forced not in allowed:
                        raise SceneError(
                            f"class {c!r} (allowed rotations {sorted(allowed)}): map {'ABC'[k]} cell "
                            f"({cell.x},{cell.y}) is forced to rotation {forced}"
                        )
                    rots = frozenset({forced})
                homes = frozenset((key - r // 90) % 4 for r in rots)
                homes_of[k].setdefault(c, []).append((slot_id, shape, key, homes))

    def grow(c: str, k: int, slot_id: int, shape: str, key: int, home: int) -> int:
        """Append a piece of class c with `home` for map k's cell; raise when the class has no cell left for it."""
        if len(pools[c]) >= total[c]:
            cell = bl[k].slots[slot_id]
            where = f"{SIDES[key]} side" if shape == "edge" else f"{CORNERS[key]} corner"
            raise SceneError(
                f"class {c!r} (allowed rotations {sorted(rots_for(c, shape))}) has {total[c]} cells, too few for its "
                f"border pieces: map {'ABC'[k]} cell ({cell.x},{cell.y}) needs another piece with its "
                f"{where} flat"
            )
        pools[c].append((shape, home))
        return len(pools[c]) - 1

    for k in range(3):  # phase 1: one-home needs
        for c in classes:
            for slot_id, shape, key, homes in homes_of[k].get(c, []):
                if len(homes) > 1:
                    continue
                (home,) = homes
                idx = next((i for i, p in enumerate(pools[c]) if i not in used[k][c] and p == (shape, home)), None)
                if idx is None:
                    idx = grow(c, k, slot_id, shape, key, home)
                used[k][c].add(idx)
                picks[k][slot_id] = (c, idx)

    # phase 2: rotatable needs, per map and class, matched into the pool; a new piece takes the home
    # most often allowed by the class's rotatable needs, then the need's own side (as before).
    for k in range(3):
        for c in classes:
            for shape in ("corner", "edge"):
                todo = [(slot_id, key, homes) for slot_id, sh, key, homes in homes_of[k].get(c, [])
                        if sh == shape and len(homes) > 1]
                if not todo:
                    continue
                popular: Counter = Counter(
                    h for m in range(3) for _, sh, _, hs in homes_of[m].get(c, []) if sh == shape and len(hs) > 1 for h in hs)
                while True:
                    free = [i for i, (sh, _) in enumerate(pools[c]) if sh == shape and i not in used[k][c]]
                    match = _assign_homes([hs for _, _, hs in todo], [pools[c][i][1] for i in free])
                    if all(j is not None for j in match):
                        for (slot_id, _, _), j in zip(todo, match):
                            used[k][c].add(free[j])
                            picks[k][slot_id] = (c, free[j])
                        break
                    slot_id, key, hs = todo[match.index(None)]
                    home = min(hs, key=lambda h: (-popular[h], (h - key) % 4))
                    grow(c, k, slot_id, shape, key, home)

    a_pick = picks[0]

    def make_piece(c, shape, home, pid=0):
        name = None if home is None else (SIDES[home] if shape == "edge" else CORNERS[home])
        inner = "wild" if shape == "corner" and free_corners else None
        return Piece(pid, shape, c, rots_for(c, shape), name, default_sides(shape, name, conn, inner))

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
            out.append(make_piece(c, shape, home, pid))
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
            return out  # no flat piece sits inside any picture
        if _layouts_exist(bl, maps, out):
            return out
    # Seams could not absorb the leftover flat pieces as derived: add flat pieces of classes next to the
    # ones left unplaced (cross-class partners), as far as the class cell counts allow.
    pools, out = _repair_seams(bl, maps, pools, used, total, classes, rots_for, assemble, make_piece)
    if out is None:
        if differ:
            raise SceneError(
                "the frames of the three maps use different class mixes and the surplus flat pieces cannot "
                "all be seated as seams (cross-class seams need interior cells of the surplus classes next "
                "to each other, and spare cells in a class to hold padding pieces)")
        out = assemble(pools)
    return out


def _cls_grids(bl, maps):
    """Per map: per-slot class labels and forced rotations (None when free)."""
    return (
        [[m.cls[s.y][s.x] for s in b.slots] for b, m in zip(bl, maps)],
        [[m.rot[s.y][s.x] or None for s in b.slots] for b, m in zip(bl, maps)],
    )


def _layouts_exist(bl, maps, pieces, steps: int = 3000, tries: int = 3) -> bool:
    """True when every map admits a valid placement of `pieces` (seams included)."""
    cls_at, forced = _cls_grids(bl, maps)
    for k, b in enumerate(bl):
        if build_valid_layout(b, pieces, cls_at[k], forced[k], random.Random(0), tries=tries, steps=steps) is None:
            return False
    return True


REPAIR_TRIAL_STEPS = 400  # seam search moves per map when scoring a padding candidate
REPAIR_PADS = 40
REPAIR_PLATEAU = 5
REPAIR_DEBUG = False


def _repair_seams(bl, maps, pools, used, total, classes, rots_for, assemble, make_piece):
    """Grow the flat-piece pools until every map seats its surplus flat pieces as seams.

    Each map keeps a seam planner holding its leftover pieces (the pool entries not used on its own frame).
    A flat edge piece added to a class's pool is surplus in all three maps, so a candidate is scored by the
    pieces left unseated, summed over the maps, after a short search resumed from the current state.
    Candidates are classes that border an unseated piece in some map, singly or in pairs; the best one
    that lowers the score is kept. Returns (pools, pieces), or (pools, None) when no candidate helps.
    """
    cls_at, forced = _cls_grids(bl, maps)
    spaces = [SeamSpace(b, cls_at[k], forced[k]) for k, b in enumerate(bl)]
    forced_cls = {c for k in range(3) for c, f in zip(cls_at[k], forced[k]) if f is not None}
    planners = []
    for k in range(3):
        pl = SeamPlanner(spaces[k], random.Random(k))
        for c in classes:
            for i, (shape, home) in enumerate(pools[c]):
                if i not in used[k][c]:
                    pl.add(make_piece(c, shape, home))
        pl.search()
        planners.append(pl)

    def homes(c):
        return range(4) if (c in forced_cls or len(rots_for(c, "edge")) < 4) else (0,)

    def room(c):
        return total[c] - len(pools[c])

    def trial(extra, steps):
        pls = [pl.copy() for pl in planners]
        for pl in pls:
            for c, h in extra:
                pl.add(make_piece(c, "edge", h))
            pl.search(steps)
        return pls

    flat_steps = 0
    for _ in range(REPAIR_PADS):
        un = [len(pl.unplaced) for pl in planners]
        if not any(un):
            return pools, assemble(pools)
        for pl in planners:  # a longer search from the current state first
            if pl.unplaced:
                pl.search(2000)
        un = [len(pl.unplaced) for pl in planners]
        if not any(un):
            return pools, assemble(pools)
        reach = [Counter() for _ in range(3)]  # per map: classes next to an unseated piece (interior cells)
        for k, b in enumerate(bl):
            want = {planners[k].pieces[i].cls for i in planners[k].unplaced}
            for s in b.slots:
                if s.boundary_sides or cls_at[k][s.id] not in want:
                    continue
                reach[k][cls_at[k][s.id]] += 2
                for t in s.neighbors:
                    if not b.slots[t].boundary_sides:
                        reach[k][cls_at[k][t]] += 1
        # prefer classes that border the unseated pieces of several maps at once
        rank = sorted(classes, key=lambda c: (-sum(1 for k in range(3) if reach[k][c]), -sum(r[c] for r in reach)))
        cand_cls = [c for c in rank if any(r[c] for r in reach)][:10]
        cands = [(c, h) for c in cand_cls for h in homes(c) if room(c) > 0]
        if REPAIR_DEBUG:
            print("repair: unseated", [[(planners[k].pieces[i].cls, planners[k].pieces[i].shape_type) for i in planners[k].unplaced] for k in range(3)], "candidate classes", cand_cls, flush=True)
        trials = [[x] for x in cands] + [[x, y] for i, x in enumerate(cands[:12]) for y in cands[i:12]]
        best = None
        for extra in trials:
            if any(room(c) < sum(1 for x in extra if x[0] == c) for c, _ in extra):
                continue
            pls = trial(extra, REPAIR_TRIAL_STEPS)
            v = sum(len(pl.unplaced) for pl in pls)
            if best is None or v < best[0] or (v == best[0] and len(extra) < len(best[1])):
                best = (v, extra, pls)
        if best is None or best[0] > sum(un):
            return pools, None
        flat_steps = flat_steps + 1 if best[0] == sum(un) else 0
        if flat_steps > REPAIR_PLATEAU:  # sideways moves are allowed for a few rounds
            return pools, None
        for c, h in best[1]:
            pools[c].append(("edge", h))
        planners = best[2]
        if REPAIR_DEBUG:
            print("  added", best[1], "->", best[0], flush=True)
    return pools, None


def seam_report(boards, maps: Sequence[ClassMap], pieces: Sequence[Piece], tries: int = 8) -> list[dict]:
    """Per map: the flat-sided pieces inside the picture and the seams that hold them, from a constructed layout.

    Each entry has `flat_inside` (flat-sided pieces off the frame), `seams` (flat-flat contacts), `groups`
    (counts by size: 2 domino, 3 L-tromino, 4 block) and `cross_class` (seams whose two pieces differ in
    class). An entry is None when no layout was found.
    """
    bl = _boards3(boards)
    cls_at, forced = _cls_grids(bl, maps)
    out = []
    for k, b in enumerate(bl):
        res = build_valid_layout(b, pieces, cls_at[k], forced[k], random.Random(0), tries=tries)
        if res is None:
            out.append(None)
            continue
        slot_of, rot_of, groups = res
        at = {s: i for i, s in enumerate(slot_of)}
        seams = cross = 0
        for i, (slot, rot) in enumerate(zip(slot_of, rot_of)):
            sl = b.slots[slot]
            for face in (1, 2):  # E and S: each contact once
                x, y = sl.x + SIDE_DELTA[face][0], sl.y + SIDE_DELTA[face][1]
                if x >= b.cols or y >= b.rows:
                    continue
                j = at[b.slot_at(x, y)]
                if (pieces[i].sides[(face - rot // 90) % 4] == "flat"
                        and pieces[j].sides[(face + 2 - rot_of[j] // 90) % 4] == "flat" and not sl.boundary_sides):
                    seams += 1
                    cross += pieces[i].cls != pieces[j].cls
        sizes = Counter(len(g) for g in groups)
        out.append({"flat_inside": sum(len(g) for g in groups), "seams": seams, "cross_class": cross,
                    "groups": {"domino": sizes[2], "L": sizes[3], "block": sizes[4]}})
    return out
