# Diagnostic (scratch): why extra-flat runs (N>0) stay invalid. Runs the N=20 derivation and solve
# with the seam-aware builder wrapped, and prints the validity problems.
import sys
from collections import Counter
from pathlib import Path
import metapuzzle.optimize as opt
from metapuzzle.board import square_board
from metapuzzle.classes import load_class_spec
from metapuzzle.optimize import validate_solution
from metapuzzle.prototype import _allowed_rotations
from metapuzzle.scene import load_scenes, pieces_from_scenes

BASE = Path("/home/user/metapuzzle/experiments/011-subjects")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
calls = []
real_build = opt.build_valid_layout
def spy(*a, **k):
    r = real_build(*a, **k)
    calls.append(r is not None)
    return r
opt.build_valid_layout = spy

maps = load_scenes(str(BASE / "pipeline/v3/scenes.txt"))
boards = [square_board(m.cols, m.rows, "standard", "quarter") for m in maps]
spec = load_class_spec(str(BASE / "pipeline/classes-v9.json"))
rots = {c: _allowed_rotations(spec, c, "quarter") for c in maps[0].histogram()}
pieces = pieces_from_scenes(boards, maps, extra_flat_pieces=N, allowed_rotations=rots)
sol = opt.solve(boards, pieces, maps, seed=0)
errs = validate_solution(sol)
print(f"N={N} build_valid_layout calls={len(calls)} results={calls[:5]}")
print(f"violations={len(errs)}")
for e in errs:
    print("  ", e)
