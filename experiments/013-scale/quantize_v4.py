"""Marching-tiles boundary classes for experiment 005 (v4, scenes only).

Input: the v2 targets (targets/<name>-v2.npy), tiered and equalized by quantize.equalize_tiers
(imported, so the tiers equal quantized-v2/*.npy; checked below).

Mask model (gallery/march-demo.png): the boundary sits half a cell INTO the own-tier region. In a
cell, the mass of neighbour tier n is
  - a half strip along each side whose neighbour has tier n, and
  - a quadrant at each corner whose DIAGONAL neighbour has tier n while the two sides adjacent to
    that corner do not.
Classification uses the 8-neighbourhood. n = the most frequent differing tier among the 8
neighbours (ties: darker); other tiers count as own. Patterns, up to rotation:
  s  one side has n                      canonical: top (mass = top half)
  c  two adjacent sides have n           canonical: top and right (all but the bottom-left quadrant)
  p  three sides have n                  canonical: missing side at the bottom
  i  no side has n, one diagonal has n   canonical: top-left quadrant only (convex corner)
  d  four sides have n                   code <n><own>d (base n, dot of own)
Anything else is approximated by the nearest pattern (extra diagonals or sides dropped), and each
approximation is counted per image:
  strip   two opposite sides (1-cell strip) -> s toward the darker neighbour
  s+diag  one side plus a diagonal not adjacent to it -> s, diagonal dropped
  c+diag  two adjacent sides plus the far diagonal -> c, diagonal dropped
  i+multi two or more diagonals, no side -> i at the first corner (TL, TR, BR, BL order)

Codes: s, c, i, p are <own><n><pattern>, e.g. DMs, LDc, DMi. d is <n><own>d, e.g. MDd.
Plain cells: D, M, L. Frame cells are always plain (engine limitation, as in v2/v3).
Rotation (token suffix, clockwise): canonical side k (corner k) goes to side (k + r) mod 4
(corner k + r); the suffix is 90 * r. Rotation 0 has no suffix.

Output: quantized-codes-v4.txt (three class maps, tokens; read by make_roles_v4.py); the report on
stdout is saved as quantize-report-v4.txt.
"""
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import quantize as q  # noqa: E402  (v1 tier functions, reused)

TIER = q.TIER_SYM  # "DML"
NAMES = q.NAMES
ROWS, COLS = q.ROWS, q.COLS
FRAME = q.FRAME
SIDE_OFF = q.OFFSETS  # (dx, dy): N, E, S, W = T, R, B, L
CORNER_OFF = [(-1, -1), (1, -1), (1, 1), (-1, 1)]  # TL, TR, BR, BL (clockwise)
CANON = {"s": (0,), "c": (0, 1), "p": (0, 1, 3)}  # canonical side sets (T=0, R=1, B=2, L=3)
OPPOSITE = [frozenset({0, 2}), frozenset({1, 3})]
PATTERN_ORDER = ["plain", "s", "c", "i", "p", "d"]
APPROX_ORDER = ["strip", "s+diag", "c+diag", "i+multi"]


@dataclass(frozen=True)
class Cell:
    code: str  # class code without rotation, e.g. "DMs", "MDd", "D"
    token: str  # scene token, e.g. "DMs@90"
    pattern: str  # plain / s / c / i / p / d
    approx: str | None  # approximation type, or None when exact
    mixed: bool  # the 8 neighbours carry two different differing tiers


def own_tier_of(code: str) -> str:
    """Own tier of a class code: first letter, except d codes (<n><own>d): second letter."""
    return code[1] if len(code) == 3 and code.endswith("d") else code[0]


def _rot_sides(pattern: str, sides: frozenset) -> int:
    for r in range(4):
        if {(k + r) % 4 for k in CANON[pattern]} == set(sides):
            return r
    raise AssertionError((pattern, sides))


def classify(tiers, tone, r: int, c: int) -> Cell:
    own = int(tiers[r, c])
    plain = Cell(TIER[own], TIER[own], "plain", None, False)
    if FRAME[r, c]:
        return plain

    def at(dx: int, dy: int):
        rr, cc = r + dy, c + dx
        if 0 <= rr < ROWS and 0 <= cc < COLS:
            return int(tiers[rr, cc]), float(tone[rr, cc])
        return own, None  # outside the frame counts as own tier

    sides = [at(dx, dy) for dx, dy in SIDE_OFF]
    corners = [at(dx, dy) for dx, dy in CORNER_OFF]
    differing = [t for t, _ in sides + corners if t != own]
    if not differing:
        return plain
    count = Counter(differing)
    n = max(count, key=lambda t: (count[t], -t))  # most frequent; ties -> darker (lower index)
    mixed = len(count) > 1
    S = frozenset(k for k in range(4) if sides[k][0] == n)
    # Corner k sits between sides k and (k+3) mod 4; its quadrant is mass when the diagonal is n
    # and neither adjacent side is.
    Q = [k for k in range(4) if corners[k][0] == n and k not in S and (k + 3) % 4 not in S]
    nbr = TIER[n]
    approx = None
    if len(S) == 4:
        return Cell(nbr + TIER[own] + "d", nbr + TIER[own] + "d", "d", None, mixed)
    if len(S) == 3:
        pattern, rot, code_sides = "p", _rot_sides("p", S), None
    elif len(S) == 2 and S in OPPOSITE:
        approx = "strip"
        pick = min(S, key=lambda k: (sides[k][1] if sides[k][1] is not None else 0.0, k))
        pattern, rot = "s", pick
    elif len(S) == 2:
        pattern, rot = "c", _rot_sides("c", S)
        if Q:
            approx = "c+diag"
    elif len(S) == 1:
        pattern, rot = "s", _rot_sides("s", S)
        if Q:
            approx = "s+diag"
    else:  # no side has n: convex corner
        assert Q, "a differing neighbour must be a side or a corner"
        pattern, rot = "i", Q[0]
        if len(Q) > 1:
            approx = "i+multi"
    code = TIER[own] + nbr + pattern
    token = code if rot == 0 else f"{code}@{90 * rot}"
    return Cell(code, token, pattern, approx, mixed)


def classify_map(tiers, tone) -> list[list[Cell]]:
    return [[classify(tiers, tone, r, c) for c in range(COLS)] for r in range(ROWS)]


def stats(grid: list[list[Cell]]) -> dict:
    flat = [x for row in grid for x in row]
    return {
        "pattern": Counter(x.pattern for x in flat),
        "codes": Counter(x.code for x in flat),
        "approx": Counter(x.approx for x in flat if x.approx),
        "mixed": sum(x.mixed for x in flat),
    }


def frame_cuts(tiers) -> int:
    """Frame cells with a different-tier 4-neighbour inside the frame (now plain, so the cut is not coded)."""
    n = 0
    for r in range(ROWS):
        for c in range(COLS):
            if FRAME[r, c]:
                own = int(tiers[r, c])
                for dx, dy in SIDE_OFF:
                    rr, cc = r + dy, c + dx
                    if 0 <= rr < ROWS and 0 <= cc < COLS and int(tiers[rr, cc]) != own:
                        n += 1
                        break
    return n


def code_list(stat_list: list[dict]) -> list[str]:
    """All class codes used by any image: plain tiers first, then by own tier, then transitions."""
    used = {k for s in stat_list for k in s["codes"]}
    return sorted(used, key=lambda k: (own_tier_of(k), len(k) > 1, k))


def main() -> None:
    v2 = {n: np.load(q.TARGETS / f"{n}-v2.npy") for n in NAMES}
    tiers, _, target, _ = q.equalize_tiers(v2)
    for n in NAMES:
        ref = np.load(q.WORK / "quantized-v2" / f"{n}.npy")
        assert (ref == tiers[n]).all(), f"tiers of {n} differ from quantized-v2"
    print("1. v2 tiers (equalized, identical to quantized-v2/*.npy). Target D / M / L: "
          f"{target[0]} / {target[1]} / {target[2]}")
    for n in NAMES:
        h = np.bincount(tiers[n].ravel(), minlength=3)
        print(f"   {n:9s} D / M / L {h[0]:3d} / {h[1]:3d} / {h[2]:3d}   frame cells on a tier cut: {frame_cuts(tiers[n])}")

    grids = {n: classify_map(tiers[n], v2[n]) for n in NAMES}
    st = {n: stats(grids[n]) for n in NAMES}
    print("2. pattern counts per image (all 500 cells; frame cells are plain):")
    print("   pattern   " + "  ".join(f"{n:>9s}" for n in NAMES))
    for p in PATTERN_ORDER:
        print(f"   {p:9s} " + "  ".join(f"{st[n]['pattern'][p]:9d}" for n in NAMES))
    print("   approximations (pattern kept, detail dropped):")
    for a in APPROX_ORDER:
        print(f"   {a:9s} " + "  ".join(f"{st[n]['approx'][a]:9d}" for n in NAMES))
    print("   cells with two different differing tiers among the 8 neighbours: " + ", ".join(f"{n} {st[n]['mixed']}" for n in NAMES))

    codes = code_list(list(st.values()))
    print("3. class histogram per image (rotation dropped):")
    print("   class     " + "  ".join(f"{c:>4s}" for c in codes))
    for n in NAMES:
        print(f"   {n:9s} " + "  ".join(f"{st[n]['codes'][c]:4d}" for c in codes))
    hist = {n: np.array([st[n]["codes"][c] for c in codes]) for n in NAMES}
    l1 = lambda a, b: int(np.abs(hist[a] - hist[b]).sum())
    print("   pairwise L1 (cat-sailboat, cat-tree, sailboat-tree): "
          f"{l1('cat', 'sailboat')}, {l1('cat', 'tree')}, {l1('sailboat', 'tree')}")
    print("   per-code max over images: " + "  ".join(
        f"{c}={max(st[n]['codes'][c] for n in NAMES)}" for c in codes if len(c) > 1))

    maps = {n: [[grids[n][r][c].token for c in range(COLS)] for r in range(ROWS)] for n in NAMES}
    out = q.WORK / "quantized-codes-v4.txt"
    lines = ["# Marching-tiles class maps (v4), experiment 005. A = cat, B = sailboat, C = tree.",
             "# Interior boundary cells: class code plus @rotation (clockwise). Frame and plain cells: tier only.", ""]
    for n in NAMES:
        lines += [f"# {n}"] + [" ".join(row) for row in maps[n]] + [""]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
