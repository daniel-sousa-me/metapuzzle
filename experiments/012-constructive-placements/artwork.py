"""How many mechanical false fits does the artwork rule out? (experiment 005 run-quarter-v3b, 20x25)

Run: python3 experiments/012-constructive-placements/artwork.py
All non-flat sides of a quarter-rotation run are andro; false fits come from metapuzzle.connectors.
A false fit between pieces of classes X and Y is "class-plausible" when X and Y are neighbours
(any direction) somewhere in one of the three class maps, i.e. a player who only reads tone classes
could try it. Distinguishing marks inside a class (T9) would cut further; not modelled.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from metapuzzle.connectors import class_summary, contacts, mating_classes  # noqa: E402
from metapuzzle.optimize import Solution  # noqa: E402
from metapuzzle.board import mates  # noqa: E402

RUN = ROOT / "experiments/005-hybrid-tones/run-quarter-v3b/solution.json"


def main():
    sol = Solution.load(RUN)
    s = class_summary(sol)
    cls = {p.piece_id: p.cls for p in sol.pieces}
    plausible = set()
    for m in sol.class_maps:
        g = [[t.split("@")[0] for t in row] for row in (m.cls if hasattr(m, "cls") else m)]
        for y in range(len(g)):
            for x in range(len(g[0])):
                for dx, dy in ((1, 0), (0, 1)):
                    if x + dx < len(g[0]) and y + dy < len(g):
                        plausible.add(frozenset((g[y][x], g[y + dy][x + dx])))
    c = contacts(sol)
    actual = {frozenset((u, v)) for u, v in c.edges}
    total = plaus = same = 0
    by_pair = Counter()
    for comp in mating_classes(sol):
        for i, u in enumerate(comp):
            for v in comp[i + 1:]:
                if u[0] == v[0] or not mates(c.profile[u], c.profile[v]) or frozenset((u, v)) in actual:
                    continue
                total += 1
                key = frozenset((cls[u[0]], cls[v[0]]))
                if key in plausible:
                    plaus += 1
                    by_pair[tuple(sorted(key))] += 1
    print(f"false fits {total} (connectors.py: {s['false_fits']}), intended {s['intended']}, ratio {total / s['intended']:.1f}")
    print(f"class-plausible false fits {plaus}, ratio {plaus / s['intended']:.1f} ({100 * plaus / total:.0f}% of false fits)")
    print("largest contributors:", ", ".join(f"{'|'.join(k if len(k) == 2 else k * 2)} {v / s['intended']:.1f}" for k, v in by_pair.most_common(5)))
    print(f"class pairs that are neighbours somewhere: {len(plausible)} of {len({frozenset((a, b)) for a in set(cls.values()) for b in set(cls.values())})}")


if __name__ == "__main__":
    main()
