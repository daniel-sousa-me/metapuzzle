"""Piece inventory: side profiles, shape types, classes, allowed rotations."""
from __future__ import annotations

import itertools
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
# A flat side is legal inside the picture only against another flat side. A *group* is a root
# piece plus leaf pieces, each leaf showing a flat side to one of the root's flat sides: a domino
# (edge + edge) or an L-tromino (a two-flat corner piece + two edge pieces). Groups sit on interior
# slots, so every other side of their pieces meets an ordinary connector.


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


def group_placements(board: Board, parts: Sequence[Piece], cls_at=None, forced_at=None) -> list[tuple]:
    """Every way to place a group on interior slots of `board`.

    parts[0] is the root, the rest are leaves; the root shows exactly len(leaves) flat sides, each
    facing a leaf that shows a flat side back (and no other). Returns tuples of (slot, rotation degrees)
    in `parts` order. cls_at / forced_at are per-slot class labels and forced rotations (or None).
    """
    root, leaves = parts[0], parts[1:]
    out: list[tuple] = []
    for u in board.slots:
        if u.boundary_sides:
            continue
        for r in sorted(root.allowed_rotations):
            if (forced_at and forced_at[u.id] not in (None, r)) or (cls_at and cls_at[u.id] != root.cls):
                continue
            fl = flat_dirs(root.sides, r)
            if len(fl) != len(leaves):
                continue
            for assign in set(itertools.permutations(sorted(fl))):
                placed = [(u.id, r)]
                for leaf, d in zip(leaves, assign):
                    dx, dy = SIDE_DELTA[d]
                    x, y = u.x + dx, u.y + dy
                    if not (0 <= x < board.cols and 0 <= y < board.rows):
                        break
                    v = board.slot_at(x, y)
                    if board.slots[v].boundary_sides:
                        break
                    rs = exact_rotations(leaf, frozenset({(d + 2) % 4}), cls_at[v] if cls_at else None,
                                         forced_at[v] if forced_at else None)
                    if not rs:
                        break
                    placed.append((v, rs[0]))
                else:
                    if len({s for s, _ in placed}) == len(placed):
                        out.append(tuple(placed))
    return out


SEARCH_STEPS = 4000


def build_valid_layout(board: Board, pieces: Sequence[Piece], cls_at=None, forced_at=None, rng=None, tries: int = 25):
    """Construct one valid placement of `pieces` on a standard board, seams included.

    Border slots take pieces whose flat sides are exactly the slot's boundary sides (a maximum
    matching); the flat-sided pieces left over form seam groups on interior slots (each corner piece
    with two edge pieces, then edge pieces in pairs); plain pieces fill the rest by class.
    Returns (slot_of, rotation_of, groups) indexed by position in `pieces`, groups being lists of
    piece indices (root first), or None when no layout was found. Validity assumes every non-flat
    profile mates with every other non-flat profile the pieces can present.
    """
    n = board.n_slots
    if board.border != "standard" or len(pieces) != n:
        return None
    rng = rng or random.Random(0)
    nflat = [sum(s == "flat" for s in p.sides) for p in pieces]
    if max(nflat) > 2:
        return None
    memo: dict = {}
    grp_memo: dict = {}

    def rots(i: int, slot: int, flats: frozenset) -> tuple[int, ...]:
        key = (_sig(pieces[i]), slot, flats)
        if key not in memo:
            memo[key] = exact_rotations(pieces[i], flats, cls_at[slot] if cls_at else None,
                                        forced_at[slot] if forced_at else None)
        return memo[key]

    interior_all = [s for s in board.slots if not s.boundary_sides]
    border = [s for s in board.slots if s.boundary_sides]
    flat_idx = [i for i in range(n) if nflat[i]]
    plain_idx = [i for i in range(n) if not nflat[i]]
    if len(flat_idx) < len(border):
        return None
    bflats = {s.id: frozenset(s.boundary_sides) for s in border}
    cand0 = {s.id: [i for i in flat_idx if nflat[i] == len(bflats[s.id]) and rots(i, s.id, bflats[s.id])] for s in border}
    if any(not c for c in cand0.values()):
        return None
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
            return None
        slot_of: dict[int, int] = {}
        rot_of: dict[int, int] = {}
        at: dict[int, int] = {}
        for i, s in owner.items():
            slot_of[i], at[s] = s, i
            rot_of[i] = rng.choice(rots(i, s, bflats[s]))
        # 2. seam groups from the leftover flat-sided pieces. Each leftover corner takes two edge
        # pieces (the pair with the most placements) and forms an L; the other edge pieces are paired
        # up (any two with a common placement). A min-conflicts search then picks one placement per
        # group, and may swap partners between two dominoes.
        left = [i for i in flat_idx if i not in owner]
        rng.shuffle(left)
        taken: set[int] = set()
        members: list[list[int]] = []  # corner groups: [corner, leaf, leaf]; dominoes: [lower id, higher id]

        def group_options(ids) -> list:
            key = tuple(_sig(pieces[i]) for i in ids)
            if key not in grp_memo:
                grp_memo[key] = group_placements(board, [pieces[i] for i in ids], cls_at, forced_at)
            return grp_memo[key]

        ok = True
        for root in [i for i in left if nflat[i] == 2]:
            taken.add(root)
            by_sig: dict = {}
            for j in left:
                if j not in taken and nflat[j] == 1:
                    by_sig.setdefault(_sig(pieces[j]), []).append(j)
            sigs = list(by_sig)
            scored = []
            for x, sa in enumerate(sigs):
                for sb in sigs[x:]:
                    if sa == sb and len(by_sig[sa]) < 2:
                        continue
                    ia, ib = by_sig[sa][0], by_sig[sb][-1 if sa == sb else 0]
                    n_opt = len(group_options([root, ia, ib]))
                    if n_opt:
                        scored.append(((len(by_sig[sa]) + len(by_sig[sb])) * (0.5 + rng.random()), ia, ib))
            if not scored:
                ok = False
                break
            _, ia, ib = max(scored)
            taken.update((ia, ib))
            members.append([root, ia, ib])
        if not ok:
            continue
        n_corner_groups = len(members)
        rest = [i for i in left if i not in taken and nflat[i] == 1]
        busy = set(at)
        partner: dict[int, int] = {}
        compat = {a: [] for a in rest}
        for x, a in enumerate(rest):
            for b in rest[x + 1:]:
                n_opt = len(group_options([a, b] if a < b else [b, a]))
                if n_opt:
                    w = n_opt * (0.5 + rng.random())
                    compat[a].append((w, b))
                    compat[b].append((w, a))
        for a in compat:
            compat[a] = [b for _, b in sorted(compat[a], reverse=True)]

        def augment_pair(a: int, depth: int, seen: set) -> bool:
            for b in compat[a]:
                if b in seen:
                    continue
                seen.add(b)
                if b not in partner:
                    partner[a], partner[b] = b, a
                    return True
                if depth:
                    c = partner[b]
                    del partner[b], partner[c]
                    seen.add(c)
                    if augment_pair(c, depth - 1, seen):
                        partner[a], partner[b] = b, a
                        return True
                    partner[b], partner[c] = c, b
            return False

        order = list(rest)
        rng.shuffle(order)
        order.sort(key=lambda a: len(compat[a]))
        for a in order:
            if a not in partner and not augment_pair(a, 60, {a}):
                ok = False
                break
        if not ok:
            continue
        members += [[a, b] for a, b in partner.items() if a < b]
        opt_cache: dict = {}

        def cands(ids) -> list:
            key = tuple(ids)
            if key not in opt_cache:
                opt_cache[key] = group_options(ids)
            return opt_cache[key]

        cand = [cands(m) for m in members]
        if any(not c for c in cand):
            continue
        choice = [rng.randrange(len(c)) for c in cand]
        cover: dict[int, int] = {}

        def put(g: int, sign: int) -> None:
            for slot, _ in cand[g][choice[g]]:
                cover[slot] = cover.get(slot, 0) + sign

        def overlap(g: int) -> int:
            return sum(cover[sl] - 1 for sl, _ in cand[g][choice[g]])

        def best_choice(g: int) -> int:
            pool = rng.sample(range(len(cand[g])), min(40, len(cand[g])))
            return min(pool, key=lambda t: (sum(cover.get(sl, 0) for sl, _ in cand[g][t]), rng.random()))

        for g in range(len(members)):
            put(g, 1)
        for _step in range(SEARCH_STEPS):
            bad = [g for g in range(len(members)) if overlap(g) > 0]
            if not bad:
                break
            g = rng.choice(bad)
            others = [x for x in range(n_corner_groups, len(members)) if x != g]
            if g < n_corner_groups or rng.random() < 0.7 or not others:  # move a group to its least crowded placement
                put(g, -1)
                choice[g] = best_choice(g)
                put(g, 1)
                continue
            h = rng.choice(others)  # or swap partners with another domino
            (a, b), (c, d) = members[g], members[h]
            new = rng.choice([((a, c), (b, d)), ((a, d), (b, c))])
            new = [sorted(new[0]), sorted(new[1])]
            oc = [cands(new[0]), cands(new[1])]
            if not oc[0] or not oc[1]:
                continue
            old = (members[g], members[h], cand[g], cand[h], choice[g], choice[h])
            before = sum(overlap(x) > 0 for x in (g, h))
            put(g, -1)
            put(h, -1)
            members[g], members[h] = new
            cand[g], cand[h] = oc
            choice[g] = best_choice(g)
            put(g, 1)
            choice[h] = best_choice(h)
            put(h, 1)
            if sum(overlap(x) > 0 for x in (g, h)) > before:
                put(g, -1)
                put(h, -1)
                members[g], members[h], cand[g], cand[h], choice[g], choice[h] = old
                put(g, 1)
                put(h, 1)
        else:
            continue
        groups: list[list[int]] = [list(m) for m in members]
        for g, mem in enumerate(members):
            for i, (slot, rot) in zip(mem, cand[g][choice[g]]):
                slot_of[i], rot_of[i], at[slot] = slot, rot, i
        # 3. plain pieces fill the remaining slots by class
        by_cls: dict = {}
        for i in plain_idx:
            by_cls.setdefault(pieces[i].cls if cls_at else None, []).append(i)
        for lst in by_cls.values():
            rng.shuffle(lst)
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
            return [slot_of[i] for i in range(n)], [rot_of[i] for i in range(n)], groups
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
