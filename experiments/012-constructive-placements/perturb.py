"""How fast do minimal classes dissolve when the designer departs from the construction?

Run: python3 experiments/012-constructive-placements/perturb.py
Start from an exact construction and displace a fraction f of the pieces in B and in C (a random
permutation among the displaced pieces of the same shape type, so frames stay valid): this models
repairing a construction towards class maps that are not orbit-compatible (each unsatisfied piece
must move). Reports mean over seeds of: largest class (share of sides), share of sides still in a
complete minimal class, false-fit ratio (metapuzzle.connectors), shared adjacencies.
"""
from __future__ import annotations

import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import construct  # noqa: E402
from construct import Solution, class_summary, PAIR_INDEX, shared_adjacencies  # noqa: E402

FRACTIONS = (0.0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 0.76, 1.0)


def displace(sol, f, rng):
    groups = defaultdict(list)
    for p in sol.pieces:
        groups[(p.shape_type, p.home)].append(p.piece_id)
    placements = [dict(sol.placements[0])]
    for k in (1, 2):
        pl = dict(sol.placements[k])
        for ids in groups.values():
            chosen = [p for p in ids if rng.random() < f]
            cells = [pl[p] for p in chosen]
            rng.shuffle(cells)
            for p, c in zip(chosen, cells):
                pl[p] = c
        placements.append(pl)
    return Solution(sol.boards, sol.pieces, placements)


def measure(sol, m=6):
    s = class_summary(sol)
    complete = sum(r["size"] for r in s["per_class"] if r["size"] == m and r["false"] == 0)
    shared = sum(shared_adjacencies(sol.placements[i], sol.placements[j], sol.boards[i], sol.boards[j])[0] for i, j in PAIR_INDEX)
    return s["size"]["max"] / s["sides"], complete / s["sides"], s["false_ratio"], shared


def main(seeds=3):
    cases = [("product 19x25 standard none", construct.product_standard(19, 25)),
             ("group 21x24 tray none", construct.group_tray(21, 24))]
    print("| construction | displaced f | largest class | sides in complete K(3,3) | false-fit ratio | shared adjacencies (sum of pairs) |")
    print("|---|---|---|---|---|---|")
    for name, base in cases:
        for f in FRACTIONS:
            rows = [measure(displace(base, f, random.Random(seed))) for seed in range(seeds)]
            mean = [sum(r[i] for r in rows) / len(rows) for i in range(4)]
            print(f"| {name} | {f:.2f} | {100 * mean[0]:.1f}% | {100 * mean[1]:.0f}% | {mean[2]:.2f} | {mean[3]:.0f} |", flush=True)


if __name__ == "__main__":
    main()
