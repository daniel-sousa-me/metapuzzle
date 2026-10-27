"""Piece inventory: side profiles, shape types, classes, allowed rotations."""
from __future__ import annotations

import functools
import itertools
import math
import random
from dataclasses import dataclass
from typing import Sequence

from .board import CORNERS, ROTATION_DEGREES, SIDE_DELTA, SIDES, Board

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


# ---- seams: flat-sided pieces sitting inside a picture ------------------------------------
# A flat side is legal inside the picture only against another flat side. A *group* is a set of
# flat-sided pieces on interior cells whose flat sides all face each other: a domino (edge + edge),
# an L-tromino (a two-flat corner piece + two edge pieces), a 2x2 block of two corners and two edges
# (C C over E E) or four corners. The scene prescribes the class of every cell, so the pieces of a
# group need not share a class: each piece only has to match the class (and forced rotation) of the
# cell it sits on. Every other side of a group piece meets an ordinary connector.


def flat_dirs(sides: Sequence[str], rotation: int) -> frozenset:
    """Board directions (N=0..W=3) whose facing profile is flat when rotated by `rotation` degrees."""
    q = rotation // 90
    return frozenset(d for d in range(4) if sides[(d - q) % 4] == "flat")


def exact_rotations(piece: Piece, flats: frozenset, cls_at: str | None = None, forced: int | None = None) -> tuple[int, ...]:
    """Rotations at which `piece` shows exactly the flat directions `flats`; class and forced rotation respected."""
    if cls_at is not None and piece.cls != cls_at:
        return ()
    return tuple(
        r for r in sorted(piece.allowed_rotations)
        if (forced is None or r == forced) and flat_dirs(piece.sides, r) == flats
    )


def _sig(p: Piece) -> tuple:
    return (p.sides, p.allowed_rotations, p.cls)


def _shape(cells, links) -> tuple:
    """((dx, dy, flat directions), ...) of a group: cells with `links` (index pairs) as flat-flat contacts."""
    flats = [set() for _ in cells]
    for i, j in links:
        d = SIDE_DELTA.index((cells[j][0] - cells[i][0], cells[j][1] - cells[i][1]))
        flats[i].add(d)
        flats[j].add((d + 2) % 4)
    return tuple((x, y, frozenset(f)) for (x, y), f in zip(cells, flats))


def _group_shapes() -> list[tuple]:
    out = [_shape([(0, 0), (1, 0)], [(0, 1)]), _shape([(0, 0), (0, 1)], [(0, 1)])]  # dominoes
    for a in range(4):  # L: a corner piece (flats a, a+1) with an edge piece across each flat
        out.append(_shape([(0, 0), SIDE_DELTA[a], SIDE_DELTA[(a + 1) % 4]], [(0, 1), (0, 2)]))
    ring = [(0, 0), (1, 0), (1, 1), (0, 1)]
    out.append(_shape(ring, [(0, 1), (1, 2), (2, 3), (3, 0)]))  # four corners
    for skip in range(4):  # two corners and two edges: the ring with one contact left out
        out.append(_shape(ring, [(i, (i + 1) % 4) for i in range(4) if i != skip]))
    return out


GROUP_SHAPES = _group_shapes()


def _kind(flat_counts) -> tuple[int, int]:
    return (sum(n == 1 for n in flat_counts), sum(n == 2 for n in flat_counts))


@functools.lru_cache(maxsize=32)
def _geometry(cols: int, rows: int) -> dict:
    """Every placement of each group shape on interior cells: kind (edges, corners) -> [(slots, flats)]."""
    out: dict = {}
    for shape in GROUP_SHAPES:
        kind = _kind([len(f) for _, _, f in shape])
        lst = out.setdefault(kind, [])
        for y in range(1, rows - 1):
            for x in range(1, cols - 1):
                cells = [(x + dx, y + dy) for dx, dy, _ in shape]
                if all(1 <= cx < cols - 1 and 1 <= cy < rows - 1 for cx, cy in cells):
                    lst.append((tuple(cy * cols + cx for cx, cy in cells), tuple(f for _, _, f in shape)))
    return out


class SeamSpace:
    """Seam groups on the interior of one board, for the class map `cls_at` and forced rotations `forced_at`.

    Both are per-slot lists (or None). `placements` lists the ways to put a group on the board; `plan`
    searches for a set of disjoint groups that absorbs given flat-sided pieces.
    """

    def __init__(self, board: Board, cls_at=None, forced_at=None):
        self.board, self.cls_at, self.forced_at = board, cls_at, forced_at
        self.geom = _geometry(board.cols, board.rows)
        self._rots: dict = {}
        self._index: dict | None = None
        self.instances: list = []
        self.inst_kind: list = []
        self._opts: dict = {}

    def rots(self, piece: Piece, slot: int, flats: frozenset, sig=None) -> tuple[int, ...]:
        """Rotations at which `piece` sits on interior `slot` showing exactly `flats`."""
        c = self.cls_at[slot] if self.cls_at else None
        f = self.forced_at[slot] if self.forced_at else None
        key = (sig or _sig(piece), c, f, flats)
        r = self._rots.get(key)
        if r is None:
            r = self._rots[key] = exact_rotations(piece, flats, c, f)
        return r

    def index(self) -> dict:
        """(cell class, flat count, group kind) -> [(instance id, position)] over every group placement."""
        if self._index is None:
            idx: dict = {}
            for kind, lst in self.geom.items():
                for inst in lst:
                    iid = len(self.instances)
                    self.instances.append(inst)
                    self.inst_kind.append(kind)
                    for pos, (slot, f) in enumerate(zip(*inst)):
                        idx.setdefault((self.cls_at[slot] if self.cls_at else None, len(f), kind), []).append((iid, pos))
            self._index = idx
        return self._index

    def options(self, piece: Piece, sig, kinds) -> list:
        """(instance id, position) pairs where `piece` fits a group of one of the given kinds."""
        key = (sig, tuple(kinds))
        if key not in self._opts:
            idx = self.index()
            n = sum(s == "flat" for s in piece.sides)
            ck = piece.cls if self.cls_at else None
            self._opts[key] = [
                (iid, pos) for kind in kinds for iid, pos in idx.get((ck, n, kind), ())
                if self.rots(piece, self.instances[iid][0][pos], self.instances[iid][1][pos], sig)
            ]
        return self._opts[key]

    def placements(self, parts: Sequence[Piece]) -> list[tuple]:
        """Every way to place the group `parts` (a tuple of (slot, rotation degrees) per part, in order)."""
        kind = _kind([sum(s == "flat" for s in p.sides) for p in parts])
        if kind not in self.geom:
            return []
        out: list[tuple] = []
        for slots, flats in self.geom[kind]:
            by_n: dict = {1: [], 2: []}
            for pos, f in enumerate(flats):
                by_n[len(f)].append(pos)
            pbn: dict = {1: [], 2: []}
            for j, p in enumerate(parts):
                pbn[sum(s == "flat" for s in p.sides)].append(j)
            for perm1 in set(itertools.permutations(pbn[1])):
                for perm2 in set(itertools.permutations(pbn[2])):
                    placed = [None] * len(parts)
                    ok = True
                    for js, ps in ((perm1, by_n[1]), (perm2, by_n[2])):
                        for j, pos in zip(js, ps):
                            rs = self.rots(parts[j], slots[pos], flats[pos])
                            if not rs:
                                ok = False
                                break
                            placed[j] = (slots[pos], rs[0])
                        if not ok:
                            break
                    if ok:
                        out.append(tuple(placed))
        return out

    def plan(self, pieces: Sequence[Piece], left: Sequence[int], rng: random.Random, steps: int = 0):
        """Place the flat-sided pieces `left` (indices into `pieces`) as disjoint seam groups.

        Returns (groups, unplaced): on success `groups` holds (piece indices by position, ((slot, rotation
        degrees), ...)) and `unplaced` is empty; otherwise `groups` is empty and `unplaced` lists the
        pieces left over in the best state found (a piece with no placement at all comes alone).
        """
        left = list(left)
        planner = SeamPlanner(self, rng)
        for i in left:
            planner.add(pieces[i])
        planner.search(steps)
        if planner.unplaced:
            return [], sorted(left[j] for j in planner.best)
        return [([left[j] for j in mem], placed) for mem, placed in planner.groups_out()], []


class SeamPlanner:
    """A stateful seam search on one `SeamSpace`: pieces can be added and the search resumed.

    An ejection-chain search: an unplaced piece takes a group placement whose other positions are filled
    from unplaced pieces or from the groups it displaces (a piece of any group may be taken, which displaces
    that group too); displaced pieces become unplaced. A worsening move is accepted with probability
    exp(-cost/0.7). `best` keeps the unplaced pieces of the best state seen (local indices, in the order
    pieces were added).
    """

    def __init__(self, space: SeamSpace, rng: random.Random):
        self.space, self.rng = space, rng
        self.pieces: list[Piece] = []
        self.sig: list = []
        self.nfl: list = []
        self.ck: list = []
        self.unplaced: set = set()
        self.where: dict = {}  # piece -> group id
        self.groups: dict = {}  # group id -> (members by position, instance id)
        self.occ: dict = {}  # slot -> group id
        self.all_key: dict = {}  # (class, flat count) -> every piece of that kind
        self.nxt = 0
        self.best: list = []

    def copy(self) -> "SeamPlanner":
        c = SeamPlanner(self.space, self.rng)
        c.pieces, c.sig, c.nfl, c.ck = list(self.pieces), list(self.sig), list(self.nfl), list(self.ck)
        c.unplaced, c.where = set(self.unplaced), dict(self.where)
        c.groups, c.occ, c.nxt = dict(self.groups), dict(self.occ), self.nxt
        c.all_key = {k: list(v) for k, v in self.all_key.items()}
        c.best = list(self.best)
        return c

    def add(self, piece: Piece) -> int:
        i = len(self.pieces)
        n = sum(s == "flat" for s in piece.sides)
        self.pieces.append(piece)
        self.sig.append(_sig(piece))
        self.nfl.append(n)
        self.ck.append(piece.cls if self.space.cls_at else None)
        self.unplaced.add(i)
        self.all_key.setdefault((self.ck[i], n), []).append(i)
        self.best = sorted(self.unplaced)
        return i

    def _kinds(self) -> list:
        n_corner = sum(n == 2 for n in self.nfl)
        return [k for k in self.space.geom if k[1] <= n_corner and k[0] <= sum(n == 1 for n in self.nfl)]

    def search(self, steps: int = 0) -> int:
        """Run up to `steps` moves (0: a default growing with the piece count); returns the unplaced count."""
        sp, rng = self.space, self.rng
        sp.index()
        insts = sp.instances
        kinds = self._kinds()
        opts: dict = {}
        for i in range(len(self.pieces)):
            if self.sig[i] not in opts:
                opts[self.sig[i]] = sp.options(self.pieces[i], self.sig[i], kinds)
        dead = [i for i in self.unplaced if not opts[self.sig[i]]]
        if dead:
            self.best = sorted(dead)
            return len(self.unplaced)
        pieces, sig, nfl, ck = self.pieces, self.sig, self.nfl, self.ck
        unplaced, where, groups, occ, all_key = self.unplaced, self.where, self.groups, self.occ, self.all_key
        cls_at = sp.cls_at
        steps = steps or 3000 + 100 * len(pieces)

        def fill(iid: int, pos: int, p: int, blk: set):
            """Pieces for the other positions of instance `iid` (p sits at `pos`), or None."""
            slots, flats = insts[iid]
            order = [j for j in range(len(slots)) if j != pos]
            used = {p}
            res = {pos: p}

            def rec(t: int) -> bool:
                if t == len(order):
                    return True
                j = order[t]
                key = (cls_at[slots[j]] if cls_at else None, len(flats[j]))
                near, far = [], []
                for q in all_key.get(key, ()):
                    if q not in used:
                        (near if q in unplaced or where[q] in blk else far).append(q)
                rng.shuffle(near)
                rng.shuffle(far)
                for q in near + far[:6]:
                    if not sp.rots(pieces[q], slots[j], flats[j], sig[q]):
                        continue
                    used.add(q)
                    res[j] = q
                    if rec(t + 1):
                        return True
                    used.discard(q)
                return False

            return res if rec(0) else None

        for _ in range(steps):
            if not unplaced:
                break
            p = rng.choice(sorted(unplaced))
            op = opts[sig[p]]
            sample = op if len(op) <= 24 else rng.sample(op, 24)
            scored = []
            for iid, pos in sample:
                slots = insts[iid][0]
                blk = {occ[sl] for sl in slots if sl in occ}
                res = fill(iid, pos, p, blk)
                if res is not None:
                    gone = blk | {where[q] for q in res.values() if q in where}
                    scored.append((sum(len(groups[g][0]) for g in gone) - len(slots), rng.random(), iid, gone, res))
            if not scored:
                continue
            cost, _, iid, gone, res = min(scored) if rng.random() < 0.85 else rng.choice(scored)
            if cost > 0 and rng.random() > math.exp(-cost / 0.7):
                continue
            slots = insts[iid][0]
            for g in gone:
                members, _i = groups.pop(g)
                for m in members:
                    unplaced.add(m)
                    del where[m]
                for sl in insts[_i][0]:
                    del occ[sl]
            mem = [res[j] for j in range(len(slots))]
            for m in mem:
                unplaced.discard(m)
                where[m] = self.nxt
            groups[self.nxt] = (mem, iid)
            for sl in slots:
                occ[sl] = self.nxt
            self.nxt += 1
            if len(unplaced) < len(self.best) or not self.best:
                self.best = sorted(unplaced)
        return len(unplaced)

    def groups_out(self) -> list:
        """Placed groups as (members by position, ((slot, rotation degrees), ...))."""
        sp, rng = self.space, self.rng
        out = []
        for mem, iid in self.groups.values():
            slots, flats = sp.instances[iid]
            out.append((mem, tuple((sl, rng.choice(sp.rots(self.pieces[m], sl, f, self.sig[m])))
                                   for m, sl, f in zip(mem, slots, flats))))
        return out


def group_placements(board: Board, parts: Sequence[Piece], cls_at=None, forced_at=None, space: SeamSpace | None = None) -> list[tuple]:
    """Every way to place a seam group on interior slots of `board`.

    `parts` are the group's pieces (a domino, an L-tromino with the corner first, or a 2x2 block); each
    piece shows exactly the flat sides that face another piece of the group. Returns tuples of
    (slot, rotation degrees) in `parts` order. cls_at / forced_at are per-slot class labels and forced
    rotations (or None); parts of different classes need cells of their own classes.
    """
    return (space or SeamSpace(board, cls_at, forced_at)).placements(parts)


def build_valid_layout(
    board: Board, pieces: Sequence[Piece], cls_at=None, forced_at=None, rng=None, tries: int = 25,
    space: SeamSpace | None = None, diag: dict | None = None, steps: int = 0,
):
    """Construct one valid placement of `pieces` on a standard board, seams included.

    Border slots take pieces whose flat sides are exactly the slot's boundary sides (a maximum
    matching); the flat-sided pieces left over form seam groups on interior slots (`SeamSpace.plan`:
    dominoes, L-trominoes, 2x2 blocks; the pieces of a group may have different classes, each matching
    the class of its cell); plain pieces fill the rest by class.
    Returns (slot_of, rotation_of, groups) indexed by position in `pieces`, groups being lists of
    piece indices, or None when no layout was found (`diag["unplaced"]` then lists the pieces the best
    attempt could not seat, `diag["frame"]` is True when the frame itself could not be matched). `steps`
    caps the seam search per try (0: a default that grows with the number of seam pieces).
    Validity assumes every non-flat profile mates with every other non-flat profile the pieces can present.
    """
    n = board.n_slots
    if diag is not None:
        diag.clear()
    if board.border != "standard" or len(pieces) != n:
        return None
    rng = rng or random.Random(0)
    nflat = [sum(s == "flat" for s in p.sides) for p in pieces]
    if max(nflat) > 2:
        return None
    space = space or SeamSpace(board, cls_at, forced_at)

    def rots(i: int, slot: int, flats: frozenset) -> tuple[int, ...]:
        return space.rots(pieces[i], slot, flats)

    border = [s for s in board.slots if s.boundary_sides]
    flat_idx = [i for i in range(n) if nflat[i]]
    plain_idx = [i for i in range(n) if not nflat[i]]
    if len(flat_idx) < len(border):
        return None
    bflats = {s.id: frozenset(s.boundary_sides) for s in border}
    cand0 = {s.id: [i for i in flat_idx if nflat[i] == len(bflats[s.id]) and rots(i, s.id, bflats[s.id])] for s in border}
    if any(not c for c in cand0.values()):
        if diag is not None:
            diag["frame"] = True
        return None
    best_unplaced = None
    for _ in range(tries):
        # 1. border matching (Kuhn), random tie-breaking
        cand = {s: rng.sample(c, len(c)) for s, c in cand0.items()}
        owner: dict[int, int] = {}  # piece -> slot

        def augment(slot: int, seen: set) -> bool:
            for i in cand[slot]:
                if i in seen:
                    continue
                seen.add(i)
                if i not in owner or augment(owner[i], seen):
                    owner[i] = slot
                    return True
            return False

        slots_order = list(cand)
        rng.shuffle(slots_order)
        if not all(augment(s, set()) for s in slots_order):
            if diag is not None:
                diag["frame"] = True
            return None
        slot_of: dict[int, int] = {}
        rot_of: dict[int, int] = {}
        at: dict[int, int] = {}
        for i, s in owner.items():
            slot_of[i], at[s] = s, i
            rot_of[i] = rng.choice(rots(i, s, bflats[s]))
        # 2. seam groups from the leftover flat-sided pieces
        left = [i for i in flat_idx if i not in owner]
        groups, unplaced = space.plan(pieces, left, rng, steps)
        if unplaced:
            if best_unplaced is None or len(unplaced) < len(best_unplaced):
                best_unplaced = unplaced
            continue
        members: list[list[int]] = []
        for mem, placed in groups:
            members.append(list(mem))
            for i, (slot, rot) in zip(mem, placed):
                slot_of[i], rot_of[i], at[slot] = slot, rot, i
        # 3. plain pieces fill the remaining slots by class
        by_cls: dict = {}
        for i in plain_idx:
            by_cls.setdefault(pieces[i].cls if cls_at else None, []).append(i)
        for lst in by_cls.values():
            rng.shuffle(lst)
        ok = True
        for s in board.slots:
            if s.id in at:
                continue
            lst = by_cls.get(cls_at[s.id] if cls_at else None)
            pick = next((i for i in (lst or []) if rots(i, s.id, frozenset())), None)
            if pick is None:
                ok = False
                break
            lst.remove(pick)
            slot_of[pick], at[s.id] = s.id, pick
            rot_of[pick] = rng.choice(rots(pick, s.id, frozenset()))
        if ok and len(at) == n:
            return [slot_of[i] for i in range(n)], [rot_of[i] for i in range(n)], members
    if diag is not None and best_unplaced is not None:
        diag["unplaced"] = best_unplaced
    return None


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
