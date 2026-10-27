# Diagnostic (scratch): leftover single-flat edge pieces per class for each of the three boards.
from collections import Counter
from pathlib import Path
from metapuzzle.board import square_board
from metapuzzle.classes import load_class_spec
from metapuzzle.prototype import _allowed_rotations
from metapuzzle.scene import load_scenes, pieces_from_scenes
BASE = Path("/home/user/metapuzzle/experiments/011-subjects")
maps = load_scenes(str(BASE / "pipeline/v3/scenes.txt"))
boards = [square_board(m.cols, m.rows, "standard", "quarter") for m in maps]
spec = load_class_spec(str(BASE / "pipeline/classes-v9.json"))
rots = {c: _allowed_rotations(spec, c, "quarter") for c in maps[0].histogram()}
for N in (0, 20, 40, 80):
    try:
        pieces = pieces_from_scenes(boards, maps, extra_flat_pieces=N, allowed_rotations=rots)
    except Exception as e:
        print(f"N={N}: {type(e).__name__}: {e}"); continue
    supply = Counter(p.cls for p in pieces if sum(s == "flat" for s in p.sides) == 1)
    for k, (m, b) in enumerate(zip(maps, boards)):
        demand = Counter(m.cls[s.y][s.x] for s in b.slots if len(s.boundary_sides) == 1)
        left = {c: supply[c] - demand[c] for c in sorted(set(supply) | set(demand))}
        odd = {c: v for c, v in left.items() if v % 2}
        print(f"N={N} board {'ABC'[k]}: leftover edges {left} odd classes {odd}")
