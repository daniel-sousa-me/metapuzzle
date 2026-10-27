"""Merged transition classes for experiment 005 (v5, scenes only).

Reuses quantize_v4 (8-neighbour classification, approximations, tiers from quantize.equalize_tiers).
A transition piece between tiers P (darker) and Q (lighter) is one physical piece, rotated by the
side it sits on. v4 codes that differ only by which tier is own are merged:

  straight  v4 s (own X, neighbour Y)            -> PQs@deg   (Q half on the boundary side, deg = v4 rotation)
  corner    v4 c (own X quarter, Y on two sides) -> XYc@deg   (quarter tier first; canonical quarter at BL)
  corner    v4 i (Y quarter at corner k)         -> YXc@(k-3)  (quarter tier first; BL canonical, so TL = @90)
  cap       v4 p (own X tongue on 3 sides of Y)  -> XYp@deg
  dot       v4 d (own X dot in Y base)           -> YXd       (rotation-free; v4 naming, base first)

Class codes start with the tier that holds the quarter / tongue (for straights: the darker tier,
always). Dots keep v4 naming (base tier first, dot tier second), so classes-v4.json applies as is.
Per unordered pair this gives up to 7 classes: PQs, PQc, QPc, PQp, QPp, YXd, XYd.

Light-own straights: the spec rule keeps the v4 rotation number (B-half on the boundary side for
both cells). v4's neighbour-half convention would need +180 for those cells. FLIP_LIGHT_STRAIGHTS
switches that; it is False (spec) and the difference is a single constant.

Input: quantize-v2 targets via quantize (same as v4). Outputs:
  quantized-codes-v5.txt   three merged class maps (tokens), read by make_roles_v5.py
  boundary-budgets-v5.txt  per pair: classes, per-class max, surplus per image, approximations
  stdout is saved as quantize-report-v5.txt.
"""
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import quantize as q  # noqa: E402
import quantize_v4 as v4  # noqa: E402

TIER = v4.TIER
NAMES = q.NAMES
ROWS, COLS = q.ROWS, q.COLS
FLIP_LIGHT_STRAIGHTS = False  # True: add 180 to straights whose own tier is the lighter one
PAIRS = [("D", "M"), ("D", "L"), ("M", "L")]  # darker first
# Per pair: class, role in the pair (what the class holds), label for the budget table.
PAIR_CLASSES = ["s", "c-P", "c-Q", "p-P", "p-Q", "d-P", "d-Q"]
APPROX_ORDER = ["strip", "s+diag", "c+diag", "i+multi"]
ORDER = {t: i for i, t in enumerate(TIER)}


def merged(cell: v4.Cell):
    """(merged class, rotation in degrees) of a v4 cell, or None for a plain cell."""
    deg = int(cell.token.partition("@")[2] or 0)
    if cell.pattern == "plain":
        return None
    if cell.pattern == "d":  # v4 code <nbr><own>d (base first): kept as is
        return cell.code, 0
    own, nbr = cell.code[0], cell.code[1]
    if cell.pattern == "s":
        P, Q = sorted((own, nbr), key=ORDER.get)
        flip = FLIP_LIGHT_STRAIGHTS and own == Q
        return P + Q + "s", (deg + 180) % 360 if flip else deg
    if cell.pattern == "c":  # own tier holds the quarter
        return own + nbr + "c", deg
    if cell.pattern == "i":  # neighbour holds the quarter, at the corner v4 rotation k (TL = 0)
        return nbr + own + "c", ((deg // 90 - 3) % 4) * 90
    if cell.pattern == "p":  # own tier is the tongue (base side at the bottom in canonical)
        return own + nbr + "p", deg
    raise AssertionError(cell)


def pair_of(cls: str) -> tuple[str, str]:
    return tuple(sorted(cls[:2], key=ORDER.get))


def budget_label(cls: str, pair: tuple[str, str]) -> str:
    """Budget-table label for a merged class: straight, quarter-tier corner, tongue, dot."""
    pattern = cls[2]
    if pattern == "s":
        return "straight"
    holder = cls[1] if pattern == "d" else cls[0]  # dots: the dot tier is second
    role = "P" if holder == pair[0] else "Q"
    name = {"c": "corner", "p": "cap", "d": "dot"}[pattern]
    return f"{name}-{role} {cls}"


def analyse(tiers, tone) -> dict:
    grid = v4.classify_map(tiers, tone)
    cls_hist, approx, plain, own_tr = Counter(), Counter(), Counter(), Counter()
    tokens, pair_approx = [], Counter()
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            cell = grid[r][c]
            m = merged(cell)
            if m is None:
                plain[TIER[int(tiers[r, c])]] += 1
                row.append(TIER[int(tiers[r, c])])
                continue
            cls, deg = m
            cls_hist[cls] += 1
            own_tr[TIER[int(tiers[r, c])]] += 1
            if cell.approx:
                approx[cell.approx] += 1
                pair_approx[(pair_of(cls), cell.approx)] += 1
            row.append(cls if deg == 0 else f"{cls}@{deg}")
        tokens.append(row)
    return {"hist": cls_hist, "plain": plain, "own_tr": own_tr, "approx": approx,
            "pair_approx": pair_approx, "tokens": tokens, "grid": grid}


def main() -> None:
    v2 = {n: np.load(q.TARGETS / f"{n}-v2.npy") for n in NAMES}
    tiers, _, target, _ = q.equalize_tiers(v2)
    for n in NAMES:
        ref = np.load(q.HERE / "quantized-v2" / f"{n}.npy")
        assert (ref == tiers[n]).all(), f"tiers of {n} differ from quantized-v2"
    st = {n: analyse(tiers[n], v2[n]) for n in NAMES}
    classes = sorted({c for s in st.values() for c in s["hist"]}, key=lambda c: (ORDER[c[0]], ORDER[c[1]], c[2:]))

    print("1. tiers (equalized, identical to quantized-v2). D / M / L totals per image:")
    for n in NAMES:
        p = st[n]["plain"]
        t = st[n]["own_tr"]
        print(f"   {n:9s} plain D/M/L {p['D']:3d}/{p['M']:3d}/{p['L']:3d}   "
              f"transition cells own D/M/L {t['D']:3d}/{t['M']:3d}/{t['L']:3d}   "
              f"tier totals D/M/L {int((tiers[n]==0).sum())}/{int((tiers[n]==1).sum())}/{int((tiers[n]==2).sum())}")
    print(f"   target D/M/L {target[0]} / {target[1]} / {target[2]}; FLIP_LIGHT_STRAIGHTS = {FLIP_LIGHT_STRAIGHTS}")

    print("2. merged class histogram per image (transition classes; rotation dropped):")
    print("   class     " + "  ".join(f"{c:>4s}" for c in classes))
    for n in NAMES:
        print(f"   {n:9s} " + "  ".join(f"{st[n]['hist'][c]:4d}" for c in classes))
    hist = {n: np.array([st[n]["hist"][c] for c in classes]) for n in NAMES}
    l1 = lambda a, b: int(np.abs(hist[a] - hist[b]).sum())
    print(f"   pairwise L1 (cat-sailboat, cat-tree, sailboat-tree): {l1('cat', 'sailboat')}, {l1('cat', 'tree')}, {l1('sailboat', 'tree')}")
    print("   per-class max over images: " + "  ".join(
        f"{c}={max(st[n]['hist'][c] for n in NAMES)}" for c in classes))

    print("3. approximations per image (pattern kept, detail dropped):")
    for a in APPROX_ORDER:
        print(f"   {a:9s} " + "  ".join(f"{n}={st[n]['approx'][a]}" for n in NAMES))

    # Boundary budget table, one block per unordered pair.
    lines = ["# Boundary budgets (v5), experiment 005. Merged classes per unordered pair (darker tier first).",
             "# max = per-class max over the three images; surplus = max - own (cells that must be added",
             "# in near roles). A = cat, B = sailboat, C = tree.", ""]
    hdr = f"   {'class':18s} " + "".join(f"{n:>9s}" for n in NAMES) + f" {'max':>5s}" + "".join(
        f" {'sur_' + n[:3]:>8s}" for n in NAMES)
    for pair in PAIRS:
        block = [c for c in classes if pair_of(c) == pair]
        block_all = [c for c in block]
        title = f"Pair {pair[0]}-{pair[1]}"
        print(f"4. {title}")
        print(hdr)
        lines += [title, hdr.replace("   ", "", 1)]
        totals = {n: 0 for n in NAMES}
        tmax = 0
        for c in block_all:
            counts = [st[n]["hist"][c] for n in NAMES]
            mx = max(counts)
            tmax += mx
            surplus = [mx - x for x in counts]
            row = f"   {c:4s} {budget_label(c, pair):13s} " + "".join(f"{x:9d}" for x in counts) + f" {mx:5d}" + "".join(
                f" {s:8d}" for s in surplus)
            print(row)
            lines.append(row.replace("   ", "", 1))
            for n, x in zip(NAMES, counts):
                totals[n] += x
        pair_sur = {n: tmax - totals[n] for n in NAMES}
        row = f"   {'total':18s} " + "".join(f"{totals[n]:9d}" for n in NAMES) + f" {tmax:5d}" + "".join(
            f" {pair_sur[n]:8d}" for n in NAMES)
        print(row)
        lines.append(row.replace("   ", "", 1))
        for a in APPROX_ORDER:
            vals = [st[n]["pair_approx"][(pair, a)] for n in NAMES]
            if any(vals):
                row = f"   approx {a:9s} " + "".join(f"{v:9d}" for v in vals)
                print(row)
                lines.append(row.replace("   ", "", 1))
        print()
        lines.append("")
    total_sur = {n: sum(max(st[m]["hist"][c] for m in NAMES) - st[n]["hist"][c] for c in classes) for n in NAMES}
    line = "Transition cells per image: " + ", ".join(f"{n} {sum(st[n]['hist'].values())}" for n in NAMES) + \
        "; surplus to place (all pairs): " + ", ".join(f"{n} {total_sur[n]}" for n in NAMES)
    print(line)
    lines.append(line)
    budgets = HERE / "boundary-budgets-v5.txt"
    budgets.write_text("\n".join(lines) + "\n", encoding="utf-8")

    out = HERE / "quantized-codes-v5.txt"
    head = ["# Merged class maps (v5), experiment 005. A = cat, B = sailboat, C = tree.",
            "# Transition cells: merged class plus @degrees (clockwise); plain cells: tier only.", ""]
    body = []
    for n in NAMES:
        body += [f"# {n}"] + [" ".join(row) for row in st[n]["tokens"]] + [""]
    out.write_text("\n".join(head + body), encoding="utf-8")
    print(f"wrote {budgets} and {out}")


if __name__ == "__main__":
    main()
