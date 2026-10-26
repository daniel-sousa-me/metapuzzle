"""Scene-level metrics on class maps: class carry-over between solutions.

Pieces of one class are visually interchangeable, so a region can stay assembled across
two solutions even when no piece pair is shared, as long as the class layout matches.
These metrics compare class maps directly (piece identities play no role).

Conventions: a window is h x w = rows x cols. Map sizes are reported as ``cols x rows``
to match the board and scene file names.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterator, Mapping, Sequence

from .scene import ClassMap

Grid = Sequence[Sequence[str]]
Cell = tuple[int, int]
Pattern = tuple[tuple[str, ...], ...]

WINDOW_SIZES = ((1, 2), (2, 1), (2, 2), (3, 3))
DEFAULT_NAMES = ("A", "B", "C")


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


def same_position_overlap(map_a: ClassMap | Grid, map_b: ClassMap | Grid) -> tuple[int, float] | None:
    """(count, fraction) of cells with the same class at the same (row, col); None if shapes differ."""
    a, b = _grid(map_a), _grid(map_b)
    if _shape(a) != _shape(b):
        return None
    rows, cols = _shape(a)
    n = sum(x == y for ra, rb in zip(a, b) for x, y in zip(ra, rb))
    return n, n / (rows * cols)


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
    return {
        "names": names,
        "same_position": same,
        "window_reuse": win,
        "transferable_blob": tb,
        "transferable_fraction": tb / (rows_a * cols_a),
    }


def _sorted_counts(c: Mapping[str, int]) -> dict[str, int]:
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def report(maps: Sequence[ClassMap | Grid], names: Sequence[str] = DEFAULT_NAMES) -> dict:
    """Pairwise carry-over metrics, class histograms and largest blobs; key 'text' is a summary."""
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
    rep["text"] = format_scene_report(rep)
    return rep


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.2f}"


def format_scene_report(rep: dict) -> str:
    """Readable summary of a report() dict."""
    lines = ["maps (cols x rows): " + ", ".join(f"{n} {c}x{r}" for n, (c, r) in rep["shapes"].items())]
    lines.append("class histograms:")
    for n, h in rep["histograms"].items():
        lines.append(f"  {n}: " + " ".join(f"{k}={v}" for k, v in h.items()))
    lines.append("largest same-class blob per class:")
    for n, h in rep["largest_blobs"].items():
        lines.append(f"  {n}: " + " ".join(f"{k}={v}" for k, v in h.items()))
    lines.append("pairs (window reuse shown as plain/rotated, window = rows x cols):")
    for key, p in rep["pairs"].items():
        if p["same_position"] is None:
            same = "same position n/a (shapes differ)"
        else:
            cnt, frac = p["same_position"]
            same = f"same position {cnt} ({100 * frac:.1f}%)"
        lines.append(f"  {key}: {same}")
        wins = "  ".join(
            f"{k} {_pct(v['plain'])}/{_pct(v['rot'])}" if v else f"{k} n/a" for k, v in p["window_reuse"].items()
        )
        lines.append(f"    window reuse: {wins}")
        first = p["names"][0]
        lines.append(
            f"    transferable blob: {p['transferable_blob']} cells "
            f"({100 * p['transferable_fraction']:.1f}% of {first})"
        )
    return "\n".join(lines)
