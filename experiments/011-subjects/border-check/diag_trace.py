# Diagnostic (scratch): find which exit of build_valid_layout fires for the N=20 pieces (board A).
import inspect, re, textwrap, random
from pathlib import Path
import metapuzzle.pieces as pc
from metapuzzle.board import square_board
from metapuzzle.classes import load_class_spec
from metapuzzle.prototype import _allowed_rotations
from metapuzzle.scene import load_scenes, pieces_from_scenes

BASE = Path("/home/user/metapuzzle/experiments/011-subjects")
maps = load_scenes(str(BASE / "pipeline/v3/scenes.txt"))
boards = [square_board(m.cols, m.rows, "standard", "quarter") for m in maps]
spec = load_class_spec(str(BASE / "pipeline/classes-v9.json"))
rots = {c: _allowed_rotations(spec, c, "quarter") for c in maps[0].histogram()}
pieces = pieces_from_scenes(boards, maps, extra_flat_pieces=20, allowed_rotations=rots)
src = textwrap.dedent(inspect.getsource(pc.build_valid_layout))
lines = src.splitlines()
out = []
for i, ln in enumerate(lines):
    s = ln.strip()
    ind = ln[: len(ln) - len(ln.lstrip())]
    if s.startswith("continue") or s == "return None" or s.startswith("return None") or s == "break":
        out.append(f"{ind}print('EXIT line {i}: {s}')")
    out.append(ln)
ns = dict(vars(pc))
exec(compile("\n".join(out), "trace", "exec"), ns)
b = boards[0]; m = maps[0]
cls_at = [m.cls[s.y][s.x] for s in b.slots]
forced_at = [m.rot[s.y][s.x] or None for s in b.slots]
for seed in (0, 1):
    res = ns["build_valid_layout"](b, pieces, cls_at, forced_at, random.Random(seed))
    print("seed", seed, "result is None:", res is None)
