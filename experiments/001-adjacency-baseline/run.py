"""Experiment 001: baseline shared-adjacency counts. Run from the repo root:
python3 experiments/001-adjacency-baseline/run.py"""
import time
from pathlib import Path

from metapuzzle.board import square_board
from metapuzzle.optimize import solve, validate_solution
from metapuzzle.pieces import make_inventory

OUT = Path(__file__).parent
SEEDS = range(5)
CONFIGS = [
    ("10x8", [(10, 8)] * 3), ("25x20", [(25, 20)] * 3),
    ("mixed 96: 8x12,12x8,16x6", [(8, 12), (12, 8), (16, 6)]),
]
rows = []
for name, sizes in CONFIGS:
    for border in ("standard", "tray"):
        for rotation in ("none", "quarter"):
            if name.startswith("mixed") and border == "tray":
                continue
            boards = [square_board(c, r, border, rotation) for c, r in sizes]
            pieces = make_inventory(boards)
            res = []
            for seed in SEEDS:
                t = time.perf_counter()
                sol = solve(boards, pieces, seed=seed)
                res.append((sol, time.perf_counter() - t))
                assert validate_solution(sol) == []
            sol, secs = res[0]
            tag = name.split(":")[0].replace(" ", "")
            sol.save(OUT / f"{tag}-{border}-{rotation}.json")
            m = sol.meta["shared"]
            worst = max(sum(s.meta["shared"].values()) for s, _ in res)
            rows.append(
                f"| {name} | {border} | {rotation} | {m['AB']}/{m['AC']}/{m['BC']} | {sol.meta['iters_used']} | "
                f"{secs:.2f} | {worst} | {sum(s.meta['iters_used'] for s, _ in res) / len(res):.0f} | "
                f"{sum(t for _, t in res) / len(res):.2f} |"
            )
            print(rows[-1], flush=True)
print("\n".join(rows))
