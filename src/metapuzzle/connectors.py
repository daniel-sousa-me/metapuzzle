"""Physical connector analysis: the side-mating graph, mating classes and false fits.

A node is a non-flat piece side (piece_id, upright side index N=0, E=1, S=2, W=3). Every
contact between two touching non-flat sides, in any of the three solutions, is an edge.
Connected components are mating classes: sides forced to share one connector shape.
Flat sides never become nodes. A contact with a flat side is a flat contact (a seam).

False fits: within one class every tab can physically mate with every blank (generally,
every pair of sides whose profiles `mates`, on different pieces). The pairs that are not
actual contacts in any solution are the physically possible but unintended connections.

`MatingPenalty` is the incremental form used by the solver: it keeps the side-mating graph as
adjacency counts and a penalty that is zero exactly when every side sits in a block of at most
`m` sides (6 for tab/blank, 4 for andro), updated per move on the touched sides only.
"""
from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass

from .board import SIDE_DELTA, mates
from .metrics import components

Node = tuple[int, int]  # (piece_id, upright side index)
FLAT = "flat"


@dataclass
class Contacts:
    """Side-mating graph of one solution set: edges keep multiplicity (one per solution contact)."""

    nodes: list[Node]
    profile: dict[Node, str]
    edges: list[tuple[Node, Node]]
    flat_contacts: int  # contacts where at least one facing side is flat
    intended: int  # internal adjacencies summed over the three boards (3 x n for equal boards)
    mismatched: int  # non-flat contacts whose profiles do not mate (zero in a valid solution)


def contacts(solution) -> Contacts:
    """Build the side-mating graph of a solution (anything with boards, pieces, placements)."""
    sides_of = {p.piece_id: tuple(p.sides) for p in solution.pieces}
    profile: dict[Node, str] = {}
    edges: list[tuple[Node, Node]] = []
    flat = mismatched = intended = 0
    for board, placement in zip(solution.boards, solution.placements):
        intended += board.n_adjacencies
        at = {slot: (pid, rot // 90) for pid, (slot, rot) in placement.items()}
        for slot in board.slots:
            for d, (dx, dy) in enumerate(SIDE_DELTA):
                x, y = slot.x + dx, slot.y + dy
                if not (0 <= x < board.cols and 0 <= y < board.rows):
                    continue
                other = y * board.cols + x
                if other < slot.id:
                    continue  # each adjacency once
                pa, qa = at[slot.id]
                pb, qb = at[other]
                u: Node = (pa, (d - qa) % 4)
                v: Node = (pb, ((d + 2) % 4 - qb) % 4)
                prof_u, prof_v = sides_of[pa][u[1]], sides_of[pb][v[1]]
                if prof_u == FLAT or prof_v == FLAT:
                    flat += 1
                    continue
                profile[u], profile[v] = prof_u, prof_v
                if not mates(prof_u, prof_v):
                    mismatched += 1
                edges.append((u, v))
    nodes = sorted(profile)
    return Contacts(nodes, profile, edges, flat, intended, mismatched)


def mating_classes(solution) -> list[list[Node]]:
    """Connected components of the side-mating graph, largest first; each a sorted node list."""
    return components(contacts(solution).edges)


def _rows(solution) -> tuple[Contacts, list[dict]]:
    """Per-class rows: sizes, profile counts, possible and actual false-fit pairs."""
    c = contacts(solution)
    classes = components(c.edges)
    index = {n: i for i, comp in enumerate(classes) for n in comp}
    # distinct contacting pairs (one physical connection even if two solutions produce it)
    actual: Counter = Counter()
    for u, v in {(min(a, b), max(a, b)) for a, b in c.edges}:
        if mates(c.profile[u], c.profile[v]) and u[0] != v[0]:
            actual[index[u]] += 1
    rows = []
    for i, comp in enumerate(classes):
        prof = Counter(c.profile[n] for n in comp)
        possible = 0
        names = sorted(prof)
        for a_i, pa in enumerate(names):
            for pb in names[a_i:]:
                if not mates(pa, pb):
                    continue
                na, nb = prof[pa], prof[pb]
                possible += na * (na - 1) // 2 if pa == pb else na * nb
        by_piece: dict[int, list[str]] = defaultdict(list)
        for n in comp:
            by_piece[n[0]].append(c.profile[n])
        for sides in by_piece.values():  # a piece cannot mate with itself
            for x in range(len(sides)):
                for y in range(x + 1, len(sides)):
                    if mates(sides[x], sides[y]):
                        possible -= 1
        rows.append({
            "size": len(comp),
            "tabs": prof.get("tab", 0),
            "blanks": prof.get("blank", 0),
            "other": len(comp) - prof.get("tab", 0) - prof.get("blank", 0),
            "possible": possible,
            "actual": actual.get(i, 0),
            "false": possible - actual.get(i, 0),
        })
    rows.sort(key=lambda r: (-r["size"], -r["false"]))
    return c, rows


def false_fit_count(solution) -> dict:
    """Physically possible but unintended connections, per class and in total.

    total = sum over classes of (possible mating pairs - distinct actual contacts).
    ratio = total / intended contacts (3 x internal adjacencies).
    """
    c, rows = _rows(solution)
    total = sum(r["false"] for r in rows)
    return {
        "total": total,
        "intended": c.intended,
        "ratio": total / c.intended if c.intended else 0.0,
        "classes": rows,
    }


def _spread(values: list[int]) -> dict:
    if not values:
        return {"min": None, "median": None, "max": None}
    return {"min": min(values), "median": statistics.median(values), "max": max(values)}


def class_summary(solution) -> dict:
    """Headline numbers for the mating classes and the false-fit count of one solution set."""
    c, rows = _rows(solution)
    sizes = [r["size"] for r in rows]
    total_false = sum(r["false"] for r in rows)
    largest = rows[0] if rows else None
    n_sides = len(c.nodes)
    profiles = Counter(c.profile.values())
    edges = len(c.edges)
    return {
        "classes": len(rows),
        "sides": n_sides,
        "profiles": dict(profiles),
        "size": _spread(sizes),
        "tabs": _spread([r["tabs"] for r in rows]),
        "blanks": _spread([r["blanks"] for r in rows]),
        "largest": None if largest is None else {**largest, "fraction": largest["size"] / n_sides},
        "false_fits": total_false,
        "intended": c.intended,
        "false_ratio": total_false / c.intended if c.intended else 0.0,
        "edges": edges,
        "flat_contacts": c.flat_contacts,
        "mismatched": c.mismatched,
        "edge_identity_ok": edges == c.intended - c.flat_contacts,
        "per_class": rows,
    }


def format_summary(s: dict) -> str:
    """Readable text summary of class_summary()."""
    def fmt(sp: dict) -> str:
        if sp["min"] is None:
            return "-"
        return f"{sp['min']} / {sp['median']:g} / {sp['max']}"

    lg = s["largest"]
    lines = [
        f"non-flat sides: {s['sides']}  profiles: " + ", ".join(f"{k}={v}" for k, v in sorted(s["profiles"].items())),
        f"mating classes: {s['classes']}",
        f"class size min / median / max: {fmt(s['size'])}",
        f"tabs per class min / median / max: {fmt(s['tabs'])}",
        f"blanks per class min / median / max: {fmt(s['blanks'])}",
    ]
    if lg:
        lines.append(
            f"largest class: {lg['size']} sides ({100 * lg['fraction']:.1f}% of sides), "
            f"{lg['tabs']} tabs, {lg['blanks']} blanks, {lg['other']} other"
        )
    lines.append(
        f"false fits: {s['false_fits']} of {s['intended']} intended contacts "
        f"(ratio {s['false_ratio']:.3f})"
    )
    lines.append(
        f"contacts: {s['edges']} edges, {s['flat_contacts']} flat contacts, {s['mismatched']} mismatched"
    )
    lines.append("edge identity (edges = intended - flat): " + ("OK" if s["edge_identity_ok"] else "FAILED"))
    return "\n".join(lines)


# ---- incremental mating penalty (solver energy) -----------------------------------------------

SYMMETRIC_PROFILES = frozenset({"andro", "flat"})
DEFAULT_MATING_HOPS = 3


def target_block_size(profiles) -> int:
    """Smallest possible class: 4 (K4) when every non-flat side is andro, else 6 (K(3,3))."""
    return 4 if set(profiles) <= SYMMETRIC_PROFILES else 6


class MatingPenalty:
    """Penalty sum over sides of max(0, |B(s)| - m), with B(s) the `hops`-hop ball of s.

    Nodes are ints (the solver uses piece_index * 4 + upright side). The graph keeps one count per
    contact, so a pair touching in two solutions is one partner with multiplicity two. B(s) is the
    set of sides within `hops` steps of s (s, its partners, their partners, ...): an approximation
    of the whole class (the connected component), which would need dynamic connectivity.

    - It is exact for the target structures: a side with three distinct partners has a 2-hop ball
      of at most 6 only if all its partners share the same other two sides, i.e. its class is
      K(3,3); for andro, a 2-hop ball of 4 means K4.
    - Sides with fewer partners (borders, shared adjacencies) can sit in long chains or cycles of
      degree-2 sides, whose 2-hop ball stays at 5 whatever the length. The default 3 hops sees 7 on
      such a chain and penalizes it (a K(3,3) minus edges still passes); `hops=2` does not.
    - The ball is always a lower bound on the class, so a zero penalty with three hops does not
      prove the classes are small: check with `class_summary`.

    A move is `propose(old_contacts, new_contacts)` (the contacts incident to the touched slots
    before and after; the graph is changed in place), then `commit()` or `rollback()`. Only the sides
    within `hops - 1` of a changed side are re-evaluated; `f` holds the nonzero per-side values.
    """

    def __init__(self, m: int, hops: int = DEFAULT_MATING_HOPS):
        if hops < 2:
            raise ValueError("hops must be at least 2")
        self.m = m
        self.hops = hops
        self.adj: dict[int, dict[int, int]] = {}
        self.f: dict[int, int] = {}
        self.total = 0
        self.bad: list[int] = []  # sides with f > 0 (for focused moves)
        self._bad_pos: dict[int, int] = {}
        self._pend = None

    # graph edits
    def _add(self, u: int, v: int) -> None:
        adj = self.adj
        d = adj.get(u)
        if d is None:
            d = adj[u] = {}
        d[v] = d.get(v, 0) + 1
        d = adj.get(v)
        if d is None:
            d = adj[v] = {}
        d[u] = d.get(u, 0) + 1

    def _remove(self, u: int, v: int) -> None:
        adj = self.adj
        d, e = adj[u], adj[v]
        c = d[v] - 1
        if c:
            d[v] = e[u] = c
        else:
            del d[v]
            del e[u]

    def ball_size(self, u: int) -> int:
        adj = self.adj
        a = adj.get(u)
        if not a:
            return 1
        seen = {u}
        seen.update(a)
        if self.hops == 2:
            for y in a:
                seen.update(adj[y])
            return len(seen)
        frontier = list(a)
        for _ in range(self.hops - 1):
            nxt = []
            for x in frontier:
                for y in adj[x]:
                    if y not in seen:
                        seen.add(y)
                        nxt.append(y)
            frontier = nxt
        return len(seen)

    def _value(self, u: int) -> int:
        v = self.ball_size(u) - self.m
        return v if v > 0 else 0

    def _near(self, nodes) -> set[int]:
        """Nodes within hops - 1 of `nodes` in the current graph (including them)."""
        adj = self.adj
        seen = set(nodes)
        frontier = list(seen)
        for _ in range(self.hops - 1):
            nxt = []
            for x in frontier:
                for y in adj.get(x, ()):
                    if y not in seen:
                        seen.add(y)
                        nxt.append(y)
            frontier = nxt
        return seen

    def _set_f(self, u: int, val: int) -> None:
        f, pos, bad = self.f, self._bad_pos, self.bad
        if val:
            if u not in f:
                pos[u] = len(bad)
                bad.append(u)
            f[u] = val
        elif u in f:
            del f[u]
            i = pos.pop(u)
            last = bad.pop()
            if last != u:
                bad[i] = last
                pos[last] = i

    def build(self, edges) -> int:
        """Load a full contact list; returns the total penalty."""
        for u, v in edges:
            self._add(u, v)
        self.f.clear()
        self.bad.clear()
        self._bad_pos.clear()
        self.total = 0
        for u in self.adj:
            val = self._value(u)
            if val:
                self._set_f(u, val)
                self.total += val
        return self.total

    def propose(self, old, new) -> int:
        """Replace the contacts `old` by `new`; return the change of the penalty (pending)."""
        touched = set()
        for u, v in old:
            touched.add(u)
            touched.add(v)
        for u, v in new:
            touched.add(u)
            touched.add(v)
        region = self._near(touched)
        for u, v in old:
            self._remove(u, v)
        for u, v in new:
            self._add(u, v)
        region |= self._near(touched)
        f = self.f
        newf = {}
        delta = 0
        for u in region:
            val = self._value(u)
            newf[u] = val
            delta += val - f.get(u, 0)
        self._pend = (old, new, newf, delta)
        return delta

    def commit(self) -> None:
        _old, _new, newf, delta = self._pend
        for u, val in newf.items():
            self._set_f(u, val)
        self.total += delta
        self._pend = None

    def rollback(self) -> None:
        old, new, _newf, _delta = self._pend
        for u, v in new:
            self._remove(u, v)
        for u, v in old:
            self._add(u, v)
        self._pend = None


def mating_penalty(solution, m: int | None = None, hops: int = DEFAULT_MATING_HOPS) -> int:
    """The solver's mating penalty of a finished solution set (0 when every block has <= m sides)."""
    c = contacts(solution)
    if m is None:
        m = target_block_size(c.profile.values())
    index = {n: i for i, n in enumerate(c.nodes)}
    mp = MatingPenalty(m, hops)
    return mp.build([(index[u], index[v]) for u, v in c.edges])
