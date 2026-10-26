"""Metrics on solutions: shared adjacencies, clusters, familiarity, reports.

Adjacency is a property of piece pairs: two pieces are neighbors in a solution when
their slots are lattice neighbors on that solution's board (any contact, including
flat-flat seams). Comparisons across solutions are therefore board-independent.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Mapping

from .board import Board

Placement = Mapping[int, tuple[int, int]]
PAIR_NAMES = ("AB", "AC", "BC")
PAIR_INDEX = ((0, 1), (0, 2), (1, 2))

# Piece-level pass/fail gates, checked per pair. A gate passes when its value is strictly below
# the limit. "shared_fraction_below" is the shared fraction of adjacencies; "largest_cluster_below"
# is the piece count of the largest connected group of shared adjacencies.
PIECE_GATES = {"shared_fraction_below": 0.05, "largest_cluster_below": 4}


def gate_line(name: str, failures: list[str]) -> str:
    """Final gate line of a text report: 'piece gates: PASS' or 'piece gates: FAIL (item; item)'."""
    if not failures:
        return f"{name} gates: PASS"
    return f"{name} gates: FAIL ({'; '.join(failures)})"


def _piece_failures(pairs: Mapping[str, dict]) -> list[str]:
    frac_lim = PIECE_GATES["shared_fraction_below"]
    clus_lim = PIECE_GATES["largest_cluster_below"]
    out = []
    for name, v in pairs.items():
        if v["fraction"] >= frac_lim:
            out.append(f"{name} shared {100 * v['fraction']:.1f}% ≥ {100 * frac_lim:g}%")
        if v["largest_component"] >= clus_lim:
            out.append(f"{name} largest shared cluster {v['largest_component']} pieces ≥ {clus_lim}")
    return out


def piece_gates(solution) -> tuple[bool, list[str]]:
    """(ok, failures) of the piece gates for a solution; failures name the pair and the value."""
    failures = _piece_failures(report(solution)["pairs"])
    return not failures, failures


def piece_edges(placement: Placement, board: Board) -> set[tuple[int, int]]:
    """Unordered neighbor pairs (p<q) of pieces in one solution."""
    at = {slot: p for p, (slot, _) in placement.items()}
    out = set()
    for a, b in board.adjacencies:
        p, q = at[a], at[b]
        out.add((p, q) if p < q else (q, p))
    return out


def shared_adjacencies(pa: Placement, pb: Placement, board_a: Board, board_b: Board | None = None) -> tuple[int, list[tuple[int, int]]]:
    """(count, sorted pairs) of piece pairs adjacent in both placements."""
    shared = sorted(piece_edges(pa, board_a) & piece_edges(pb, board_b or board_a))
    return len(shared), shared


def shared_fraction(pa: Placement, pb: Placement, board_a: Board, board_b: Board | None = None) -> float:
    """Shared count divided by the smaller board's adjacency total."""
    bb = board_b or board_a
    return shared_adjacencies(pa, pb, board_a, bb)[0] / min(board_a.n_adjacencies, bb.n_adjacencies)


def components(edges) -> list[list[int]]:
    """Connected components (sorted node lists, largest first) of an edge list."""
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        parent.setdefault(a, a)
        parent.setdefault(b, b)
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    groups: dict[int, list[int]] = defaultdict(list)
    for x in parent:
        groups[find(x)].append(x)
    return sorted((sorted(g) for g in groups.values()), key=lambda g: (-len(g), g))


def transferable_clusters(pairs, min_size: int = 3) -> list[list[int]]:
    """Components of the shared-adjacency graph with at least `min_size` pieces."""
    return [c for c in components(pairs) if len(c) >= min_size]


def cluster_penalty(pairs) -> int:
    """Sum of sizes of shared components with 3+ pieces."""
    return sum(len(c) for c in components(pairs) if len(c) >= 3)


def familiarity(pa: Placement, pb: Placement, board_a: Board, board_b: Board | None = None) -> dict[int, int]:
    """Per piece: how many of its neighbors in B it also had as neighbors in A."""
    count, pairs = shared_adjacencies(pa, pb, board_a, board_b)
    fam = {p: 0 for p in pa}
    for p, q in pairs:
        fam[p] += 1
        fam[q] += 1
    return fam


def corner_order(placement: Placement, board: Board) -> tuple[int, ...]:
    """Cyclic order of the four corner slots' pieces, clockwise from NW, rotated so the smallest id leads.

    Two orders that differ only by rotating the whole board are equal; there are 6 classes.
    """
    at = {slot: p for p, (slot, _) in placement.items()}
    c, r = board.cols, board.rows
    seq = [at[0], at[c - 1], at[r * c - 1], at[(r - 1) * c]]
    i = seq.index(min(seq))
    return tuple(seq[i:] + seq[:i])


def _boards(solution) -> list[Board]:
    return list(solution.boards)


def report(solution) -> dict:
    """Metrics dict for a solution (has key 'text' with a readable summary)."""
    boards = _boards(solution)
    pl = solution.placements
    pairs_rep = {}
    all_edges = []
    for name, (i, j) in zip(PAIR_NAMES, PAIR_INDEX):
        count, shared = shared_adjacencies(pl[i], pl[j], boards[i], boards[j])
        fam = familiarity(pl[i], pl[j], boards[i], boards[j])
        comps = components(shared)
        vals = list(fam.values())
        pairs_rep[name] = {
            "shared": count,
            "fraction": count / min(boards[i].n_adjacencies, boards[j].n_adjacencies),
            "clusters": [len(c) for c in comps if len(c) >= 3],
            "largest_component": len(comps[0]) if comps else 0,
            "familiar_pieces": sum(1 for v in vals if v),
            "max_familiarity": max(vals) if vals else 0,
            "mean_familiarity": sum(vals) / len(vals) if vals else 0.0,
        }
        all_edges.append(shared)
    rotated = [sum(1 for _, r in p.values() if r) for p in pl]
    rep = {
        "boards": [b.params() for b in boards],
        "n_pieces": len(solution.pieces),
        "n_adjacencies": [b.n_adjacencies for b in boards],
        "pairs": pairs_rep,
        "total_shared": sum(v["shared"] for v in pairs_rep.values()),
        "cluster_penalty": sum(cluster_penalty(e) for e in all_edges),
        "rotated_pieces": rotated,
        "meta": dict(solution.meta),
    }
    try:
        rep["corner_orders"] = [list(corner_order(p, b)) for p, b in zip(pl, boards)]
    except KeyError:
        rep["corner_orders"] = None
    failures = _piece_failures(pairs_rep)
    rep["gates"] = {"ok": not failures, "failures": failures}
    rep["text"] = format_report(rep)
    return rep


def format_report(rep: dict) -> str:
    """Readable multi-line summary of a report dict."""
    lines = []
    for name, b in zip("ABC", rep["boards"]):
        lines.append(f"board {name}: {b['cols']}x{b['rows']} {b['border']} rotation={b['rotation']}")
    lines.append(f"pieces: {rep['n_pieces']}  adjacencies per board: {rep['n_adjacencies']}")
    for name, v in rep["pairs"].items():
        lines.append(
            f"{name}: shared={v['shared']} ({100 * v['fraction']:.2f}%)  clusters(3+)={v['clusters']}  "
            f"largest={v['largest_component']}  familiar pieces={v['familiar_pieces']}  "
            f"max fam={v['max_familiarity']}  mean fam={v['mean_familiarity']:.3f}"
        )
    lines.append(f"total shared={rep['total_shared']}  cluster penalty={rep['cluster_penalty']}")
    lines.append(f"rotated pieces per solution: {rep['rotated_pieces']}")
    if rep.get("corner_orders"):
        lines.append(f"corner orders: {rep['corner_orders']}")
    m = rep.get("meta", {})
    if m:
        lines.append("meta: " + ", ".join(f"{k}={v}" for k, v in m.items() if k != "shared"))
    lines.append(gate_line("piece", _piece_failures(rep["pairs"])))
    return "\n".join(lines)
