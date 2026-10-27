# Diagnostic (scratch): class-pair domino compatibility on each board (interior placements),
# over all classes with any single-flat piece, for N=20. Prints compatible pairs only.
import itertools
from collections import Counter
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
single = [i for i in range(len(pieces)) if sum(s == "flat" for s in pieces[i].sides) == 1]
classes = sorted({pieces[i].cls for i in single})
for k in (1, 2):
    b, m = boards[k], maps[k]
    cls_at = [m.cls[s.y][s.x] for s in b.slots]
    forced_at = [m.rot[s.y][s.x] or None for s in b.slots]
    rep = {c: [i for i in single if pieces[i].cls == c][:3] for c in classes}
    pairs = []
    for x, y in itertools.combinations_with_replacement(classes, 2):
        ok = any(a != bb and pc.group_placements(b, [pieces[min(a, bb)], pieces[max(a, bb)]], cls_at, forced_at)
                 for a in rep[x] for bb in rep[y])
        if ok:
            pairs.append(x + y)
    print(f"board {'ABC'[k]}: compatible edge-class pairs {pairs}")
