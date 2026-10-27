"""Do exact K(3,3) placements exist that respect three independent class maps? (small boards, SAT)

Run: python3 experiments/012-constructive-placements/sat_classes.py   (needs python-sat; minutes)
Board 7x7 or 10x10 standard border, rotation none. Synthetic three-tone maps (frame all L, a dark
subject and a mid halo placed differently in each map, identical histograms). For each case the
SAT model of satschemes.py is run with the extra constraint that a piece (named by its A cell) may sit
only on cells of its class. Also run on maps derived from a construction (orbit-compatible) as control.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from satschemes import search  # noqa: E402


def synth(cols, rows, n_dark, n_mid, seed):
    """Three maps with identical histograms: L frame, interior blobs at different centres."""
    rng = random.Random(seed)
    maps = []
    interior = [(x, y) for y in range(1, rows - 1) for x in range(1, cols - 1)]
    for k in range(3):
        cx, cy = rng.uniform(1, cols - 2), rng.uniform(1, rows - 2)
        order = sorted(interior, key=lambda c: (c[0] - cx) ** 2 + (c[1] - cy) ** 2 + rng.random() * 0.1)
        m = ["L"] * (cols * rows)
        for i, (x, y) in enumerate(order):
            if i < n_dark:
                m[y * cols + x] = "D"
            elif i < n_dark + n_mid:
                m[y * cols + x] = "M"
        maps.append(m)
    return maps


def show(maps, cols):
    rows = [" ".join("".join(m[y * cols:(y + 1) * cols]) for m in maps) for y in range(len(maps[0]) // cols)]
    return "\n".join("    " + r for r in rows)


def main():
    import os
    limit = float(os.environ.get("SAT_TIMEOUT", "1200"))
    cases = [(7, 7, 4, 8, s) for s in range(3)] + [(7, 7, 3, 0, s) for s in range(3)] + [(10, 10, 9, 15, 0)]
    for cols, rows, nd, nm, seed in cases:
        maps = synth(cols, rows, nd, nm, seed)
        res, dt = search(cols, rows, "standard", "none", maps=maps, timeout=limit)
        verdict = "timeout" if res == "timeout" else ("SAT" if res else "UNSAT")
        print(f"{cols}x{rows} dark {nd} mid {nm} seed {seed}: {verdict} ({dt:.0f}s)", flush=True)
        print(show(maps, cols), flush=True)


if __name__ == "__main__" and "--single" not in sys.argv:
    main()


def single_piece_tests(cols=10, rows=10, trials=8, seed=0, limit=600):
    """One dark interior piece whose three cells are drawn at random: how many trajectories are feasible?"""
    rng = random.Random(seed)
    out = []
    for _ in range(trials):
        cells = [(rng.randrange(1, cols - 1), rng.randrange(1, rows - 1)) for _ in range(3)]
        maps = []
        for x, y in cells:
            m = ["L"] * (cols * rows)
            m[y * cols + x] = "D"
            maps.append(m)
        res, dt = search(cols, rows, "standard", "none", maps=maps, timeout=limit)
        verdict = "timeout" if res == "timeout" else ("SAT" if res else "UNSAT")
        out.append(verdict)
        print(f"  single D piece {cols}x{rows} cells {cells}: {verdict} ({dt:.0f}s)", flush=True)
    return out


if __name__ == "__main__" and "--single" in sys.argv:
    single_piece_tests()
