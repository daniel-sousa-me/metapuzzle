"""Scene-level metrics on class maps: class carry-over between solutions.

Pieces of one class are visually interchangeable, so a region can stay assembled across
two solutions even when no piece pair is shared, as long as the class layout matches.
These metrics compare class maps directly (piece identities play no role).

Conventions: a window is h x w = rows x cols. Map sizes are reported as ``cols x rows``
to match the board and scene file names.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Collection, Iterator, Mapping, Sequence

from .metrics import gate_line
from .scene import ClassMap

Grid = Sequence[Sequence[str]]
Cell = tuple[int, int]
Pattern = tuple[tuple[str, ...], ...]

WINDOW_SIZES = ((1, 2), (2, 1), (2, 2), (3, 3))
DEFAULT_NAMES = ("A", "B", "C")

# A pair's dominant class (most cells across both maps) is excluded from the same-position gate
# when it covers more than this share of the cells. Strictly more: exactly 40% does not trigger.
DOMINANT_SHARE = 0.40

# Scene-level pass/fail gates, checked per pair (A-B, A-C, B-C). A gate passes when its value is
# strictly below the limit. A value that cannot be evaluated (a 2x2 window in a map narrower than
# 2 cells, or an overlap of maps with different shapes or with no cells left) is not a failure.
#   same_position_below:      same-class cells at the same (row, col), fraction of A's cells.
#                             Where the pair's dominant class covers more than DOMINANT_SHARE of
#                             the cells, the value is same_position_overlap excluding that class.
#   weighted_overlap_below:   weighted_overlap, i.e. the mean over A's classes of the fraction of
#                             each class's cells that stay in place
#   window_2x2_plain_below:   fraction of A's 2x2 windows (no rotation) found anywhere in B
#   transferable_below:       transferable blob (cells) as a fraction of A's cells
SCENE_GATES = {
    "same_position_below": 0.25,
    "weighted_overlap_below": 0.25,
    "window_2x2_plain_below": 0.30,
    "transferable_below": 0.10,
}


def _grid(m: ClassMap | Grid) -> list[list[str]]:
    return m.cls if isinstance(m, ClassMap) else [list(r) for r in m]


def _shape(g: Grid) -> tuple[int, int]:
    """(rows, cols)."""
    return len(g), (len(g[0]) if g else 0)


def _windows(g: Grid, h: int, w: int) -> Iterator[Pattern]:
    rows, cols = _shape(g)
    for r in range(rows - h + 1):
        for c in range(cols - w + 1):
            yield tuple(tuple(g[r + i][c : c + w]) for i in range(h))


def _rot90(p: Pattern) -> Pattern:
    """Clockwise quarter turn of a class pattern."""
    return tuple(zip(*p[::-1]))


def same_position_overlap(
    map_a: ClassMap | Grid, map_b: ClassMap | Grid, exclude: Collection[str] | None = None
) -> tuple[int, float] | None:
    """(count, fraction) of cells with the same class at the same (row, col).

    None if the shapes differ, or if no cells remain after ``exclude``. Cells whose class is in
    ``exclude`` in either map are skipped; the fraction is over the cells that remain.
    """
    a, b = _grid(map_a), _grid(map_b)
    if _shape(a) != _shape(b):
        return None
    skip = set(exclude or ())
    kept = [(x, y) for ra, rb in zip(a, b) for x, y in zip(ra, rb) if x not in skip and y not in skip]
    if not kept:
        return None
    n = sum(x == y for x, y in kept)
    return n, n / len(kept)


def weighted_overlap(map_a: ClassMap | Grid, map_b: ClassMap | Grid) -> float | None:
    """Same-position overlap where a matching cell of class c weighs 1 / share_A(c).

    Normalised by the total weight of A's cells, so a map compared with itself gives 1.0. Every
    class carries the same total weight (its cells times 1 / share), so the value equals the mean
    over A's classes of the fraction of that class's cells that stay in place. A common class
    therefore counts no more than a rare one. None if the shapes differ.
    """
    a, b = _grid(map_a), _grid(map_b)
    if _shape(a) != _shape(b):
        return None
    total = Counter(x for ra in a for x in ra)
    matched = Counter(x for ra, rb in zip(a, b) for x, y in zip(ra, rb) if x == y)
    # The weighted ratio with each class's weight cancelled out: the mean over classes of
    # matching cells / cells. Written this way, identical maps give exactly 1.0.
    return sum(matched[c] / n for c, n in total.items()) / len(total)


def dominant_class(map_a: ClassMap | Grid, map_b: ClassMap | Grid) -> tuple[str, float]:
    """(class, share): the most frequent class over the cells of both maps, ties broken by name."""
    a, b = _grid(map_a), _grid(map_b)
    counts = Counter(x for g in (a, b) for row in g for x in row)
    cls, n = min(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return cls, n / sum(counts.values())


def window_reuse(map_a: ClassMap | Grid, map_b: ClassMap | Grid, h: int, w: int, allow_rotation: bool = False) -> float:
    """Fraction of h x w windows of A whose class pattern occurs at any position in B.

    With ``allow_rotation`` a window also counts when one of its 4 rotations occurs in B.
    Raises ValueError when the window does not fit inside A.
    """
    a, b = _grid(map_a), _grid(map_b)
    if h < 1 or w < 1:
        raise ValueError("window must be at least 1x1")
    ra, ca = _shape(a)
    if h > ra or w > ca:
        raise ValueError(f"{h}x{w} window does not fit in map A ({ca}x{ra} cols x rows)")
    index: dict[tuple[int, int], set[Pattern]] = {}

    def in_b(p: Pattern) -> bool:
        key = (len(p), len(p[0]))
        if key not in index:
            index[key] = set(_windows(b, *key))
        return p in index[key]

    wins = list(_windows(a, h, w))
    hits = 0
    for p in wins:
        variants = [p]
        if allow_rotation:
            for _ in range(3):
                variants.append(_rot90(variants[-1]))
        if any(in_b(q) for q in variants):
            hits += 1
    return hits / len(wins)


def _components(g: Grid) -> list[tuple[str, frozenset[Cell]]]:
    """4-connected same-class components as (class, cells)."""
    rows, cols = _shape(g)
    seen: set[Cell] = set()
    out: list[tuple[str, frozenset[Cell]]] = []
    for r0 in range(rows):
        for c0 in range(cols):
            if (r0, c0) in seen:
                continue
            cls = g[r0][c0]
            comp: set[Cell] = set()
            stack = [(r0, c0)]
            seen.add((r0, c0))
            while stack:
                r, c = stack.pop()
                comp.add((r, c))
                for n in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if 0 <= n[0] < rows and 0 <= n[1] < cols and n not in seen and g[n[0]][n[1]] == cls:
                        seen.add(n)
                        stack.append(n)
            out.append((cls, frozenset(comp)))
    return out


def _largest_piece(cells: set[Cell]) -> int:
    """Size of the largest 4-connected part of a cell set."""
    best = 0
    left = set(cells)
    while left:
        stack = [left.pop()]
        size = 1
        while stack:
            r, c = stack.pop()
            for n in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if n in left:
                    left.remove(n)
                    stack.append(n)
                    size += 1
        best = max(best, size)
    return best


def largest_blob(map_: ClassMap | Grid) -> dict[str, int]:
    """Largest 4-connected same-class component size, per class."""
    out: dict[str, int] = {}
    for cls, cells in _components(_grid(map_)):
        out[cls] = max(out.get(cls, 0), len(cells))
    return out


def transferable_blob(map_a: ClassMap | Grid, map_b: ClassMap | Grid) -> int:
    """Size of the largest single-class connected region of A that fits in B by translation.

    Exact among single-class regions, translation only (no rotation). Multi-class regions
    are not considered, so this is a lower bound on the general problem.

    Method: for each same-class component C of A and each same-class component D of B,
    count for every shift t how many cells p of C have p+t in D (the overlap). Any
    connected region fitting at shift t lies inside one such overlap, and every
    connected part of an overlap fits. The result is the largest connected part of any
    overlap, so it is achieved by an actual shape. Shifts are tried in decreasing overlap
    order and skipped once the overlap cannot beat the best found.
    """
    ga, gb = _grid(map_a), _grid(map_b)
    comps_b: dict[str, list[frozenset[Cell]]] = defaultdict(list)
    for cls, cells in _components(gb):
        comps_b[cls].append(cells)
    best = 0
    for cls, cells_a in _components(ga):
        if len(cells_a) <= best:
            continue
        for cells_b in comps_b.get(cls, ()):
            shifts = Counter((rb - ra, cb - ca) for ra, ca in cells_a for rb, cb in cells_b)
            for (dr, dc), n in shifts.most_common():
                if n <= best:
                    break
                overlap = {(r, c) for r, c in cells_a if (r + dr, c + dc) in cells_b}
                best = max(best, _largest_piece(overlap))
    return best


def _pair_metrics(ga: Grid, gb: Grid, names: tuple[str, str]) -> dict:
    rows_a, cols_a = _shape(ga)
    same = same_position_overlap(ga, gb)
    win = {}
    for h, w in WINDOW_SIZES:
        if h <= rows_a and w <= cols_a:
            win[f"{h}x{w}"] = {"plain": window_reuse(ga, gb, h, w), "rot": window_reuse(ga, gb, h, w, True)}
        else:
            win[f"{h}x{w}"] = None
    tb = transferable_blob(ga, gb)
    dom_cls, dom_share = dominant_class(ga, gb)
    return {
        "names": names,
        "same_position": same,
        "dominant": {"class": dom_cls, "share": dom_share},
        "same_position_excl_dominant": same_position_overlap(ga, gb, exclude={dom_cls}),
        "weighted_overlap": weighted_overlap(ga, gb),
        "window_reuse": win,
        "transferable_blob": tb,
        "transferable_fraction": tb / (rows_a * cols_a),
    }


def _sorted_counts(c: Mapping[str, int]) -> dict[str, int]:
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def _analyse(maps: Sequence[ClassMap | Grid], names: Sequence[str]) -> dict:
    """Histograms, blobs and pairwise metrics (no gates, no text)."""
    if len(names) != len(maps):
        raise ValueError(f"{len(maps)} maps but {len(names)} names")
    if len(maps) < 2:
        raise ValueError("need at least two maps")
    grids = [_grid(m) for m in maps]
    names = list(names)
    rep = {
        "names": names,
        "shapes": {n: (_shape(g)[1], _shape(g)[0]) for n, g in zip(names, grids)},
        "histograms": {n: _sorted_counts(Counter(c for row in g for c in row)) for n, g in zip(names, grids)},
        "largest_blobs": {n: _sorted_counts(largest_blob(g)) for n, g in zip(names, grids)},
        "pairs": {},
    }
    for i in range(len(grids)):
        for j in range(i + 1, len(grids)):
            key = f"{names[i]}-{names[j]}"
            rep["pairs"][key] = _pair_metrics(grids[i], grids[j], (names[i], names[j]))
    return rep


def _limit(x: float) -> str:
    return f"{100 * x:g}%"


def _gated_same_position(p: dict) -> tuple[str | None, tuple[int, float] | None]:
    """(excluded class or None, value) of the same-position gate for one pair.

    The dominant class is excluded when it covers more than DOMINANT_SHARE of the pair's cells.
    """
    if p["dominant"]["share"] > DOMINANT_SHARE:
        return p["dominant"]["class"], p["same_position_excl_dominant"]
    return None, p["same_position"]


def _gate_failures(pairs: Mapping[str, dict]) -> list[str]:
    """One string per failing gate item, e.g. 'A-B same-position 66.2% ≥ 25%'."""
    g = SCENE_GATES
    out = []
    for key, p in pairs.items():
        dom, same = _gated_same_position(p)
        if same is not None and same[1] >= g["same_position_below"]:
            label = "same-position" if dom is None else f"same-position excl. {dom}"
            out.append(f"{key} {label} {100 * same[1]:.1f}% ≥ {_limit(g['same_position_below'])}")
        ws = p["weighted_overlap"]
        if ws is not None and ws >= g["weighted_overlap_below"]:
            out.append(f"{key} weighted overlap {100 * ws:.1f}% ≥ {_limit(g['weighted_overlap_below'])}")
        w = p["window_reuse"]["2x2"]
        if w is not None and w["plain"] >= g["window_2x2_plain_below"]:
            out.append(f"{key} 2x2 window reuse {100 * w['plain']:.1f}% ≥ {_limit(g['window_2x2_plain_below'])}")
        if p["transferable_fraction"] >= g["transferable_below"]:
            out.append(
                f"{key} transferable blob {100 * p['transferable_fraction']:.1f}% ≥ "
                f"{_limit(g['transferable_below'])} of cells"
            )
    return out


def scene_gates(maps: Sequence[ClassMap | Grid], names: Sequence[str] = DEFAULT_NAMES) -> tuple[bool, list[str]]:
    """(ok, failures) of the scene gates; failures are the items listed in the report's gate line.

    Same-position gate rule: per pair, the pair's dominant class (most cells across both maps) is
    excluded when it covers more than DOMINANT_SHARE (40%) of the cells, and the gate reads the
    excluded value; otherwise it reads the plain same-position overlap.
    """
    failures = _gate_failures(_analyse(maps, names)["pairs"])
    return not failures, failures


def report(maps: Sequence[ClassMap | Grid], names: Sequence[str] = DEFAULT_NAMES) -> dict:
    """Pairwise carry-over metrics, class histograms, largest blobs and scene gates.

    Keys: 'pairs', 'histograms', 'largest_blobs', 'shapes', 'names', 'gates' ({'ok', 'failures'})
    and 'text', a readable summary whose last line is the scene gate line.
    """
    rep = _analyse(maps, names)
    failures = _gate_failures(rep["pairs"])
    rep["gates"] = {"ok": not failures, "failures": failures}
    rep["text"] = format_scene_report(rep)
    return rep


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.2f}"


def format_scene_report(rep: dict) -> str:
    """Readable summary of a report() dict, ending with the scene gate line.

    Per pair: plain same-position, same-position excluding the pair's dominant class (marked
    as gated when the dominant class covers more than 40% of cells, in which case the gate reads
    that line), and the weighted overlap.
    """
    lines = ["maps (cols x rows): " + ", ".join(f"{n} {c}x{r}" for n, (c, r) in rep["shapes"].items())]
    lines.append("class histograms:")
    for n, h in rep["histograms"].items():
        lines.append(f"  {n}: " + " ".join(f"{k}={v}" for k, v in h.items()))
    lines.append("largest same-class blob per class:")
    for n, h in rep["largest_blobs"].items():
        lines.append(f"  {n}: " + " ".join(f"{k}={v}" for k, v in h.items()))
    lines.append(
        f"same-position gate: where the pair's dominant class covers more than {100 * DOMINANT_SHARE:g}% "
        "of the cells, the gate reads same position excl. that class; otherwise the plain line"
    )
    lines.append("pairs (window reuse shown as plain/rotated, window = rows x cols):")
    for key, p in rep["pairs"].items():
        if p["same_position"] is None:
            same = "same position n/a (shapes differ)"
        else:
            cnt, frac = p["same_position"]
            same = f"same position {cnt} ({100 * frac:.1f}%)"
        lines.append(f"  {key}: {same}")
        dom = p["dominant"]
        gated = "gated" if dom["share"] > DOMINANT_SHARE else "not gated"
        excl = p["same_position_excl_dominant"]
        if p["same_position"] is None:
            excl_txt = "n/a (shapes differ)"
        elif excl is None:
            excl_txt = "n/a (no cells left)"
        else:
            excl_txt = f"{excl[0]} ({100 * excl[1]:.1f}%)"
        lines.append(
            f"    same position excl. dominant {dom['class']} "
            f"(covers {100 * dom['share']:.1f}% of cells, {gated}): {excl_txt}"
        )
        ws = p["weighted_overlap"]
        lines.append("    weighted overlap: " + ("n/a (shapes differ)" if ws is None else f"{100 * ws:.1f}%"))
        wins = "  ".join(
            f"{k} {_pct(v['plain'])}/{_pct(v['rot'])}" if v else f"{k} n/a" for k, v in p["window_reuse"].items()
        )
        lines.append(f"    window reuse: {wins}")
        first = p["names"][0]
        lines.append(
            f"    transferable blob: {p['transferable_blob']} cells "
            f"({100 * p['transferable_fraction']:.1f}% of {first})"
        )
    lines.append(gate_line("scene", _gate_failures(rep["pairs"])))
    return "\n".join(lines)
