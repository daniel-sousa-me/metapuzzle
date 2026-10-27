# Diagnostic (scratch): class-level check of the seam domino step for board A with N extra flats.
# Leftover single-flat edge pieces per class (after border demand), class-pair compatibility on the
# interior of board A, and the maximum domino matching at class level.
import itertools, sys
from collections import Counter
from pathlib import Path
import metapuzzle.pieces as pc
from metapuzzle.board import square_board
from metapuzzle.classes import load_class_spec
from metapuzzle.prototype import _allowed_rotations
from metapuzzle.scene import load_scenes, pieces_from_scenes

BASE = Path("/home/user/metapuzzle/experiments/011-subjects")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
maps = load_scenes(str(BASE / "pipeline/v3/scenes.txt"))
boards = [square_board(m.cols, m.rows, "standard", "quarter") for m in maps]
spec = load_class_spec(str(BASE / "pipeline/classes-v9.json"))
rots = {c: _allowed_rotations(spec, c, "quarter") for c in maps[0].histogram()}
pieces = pieces_from_scenes(boards, maps, extra_flat_pieces=N, allowed_rotations=rots)
b, m = boards[0], maps[0]
cls_at = [m.cls[s.y][s.x] for s in b.slots]
forced_at = [m.rot[s.y][s.x] or None for s in b.slots]
nflat = [sum(s == "flat" for s in p.sides) for p in pieces]
single = [i for i in range(len(pieces)) if nflat[i] == 1]
demand = Counter(m.cls[s.y][s.x] for s in b.slots if len(s.boundary_sides) == 1)
supply = Counter(pieces[i].cls for i in single)
left = {c: supply[c] - demand[c] for c in set(supply) | set(demand)}
print("N", N, "single-flat supply", dict(supply))
print("border demand (1-side cells)", dict(demand))
print("leftover for dominoes/corner L (supply - demand)", dict(left), "total", sum(left.values()))
classes = sorted(c for c in left if left[c] > 0)
rep = {c: [i for i in single if pieces[i].cls == c][:3] for c in classes}
compat = {}
for x, y in itertools.combinations_with_replacement(classes, 2):
    ok = False
    for a in rep[x]:
        for bb in rep[y]:
            if a != bb and pc.group_placements(b, [pieces[min(a, bb)], pieces[max(a, bb)]], cls_at, forced_at):
                ok = True; break
        if ok: break
    compat[(x, y)] = compat[(y, x)] = ok
print("class-pair domino compat (True = some interior placement):")
for x in classes:
    print("  ", x, "->", [y for y in classes if compat[(x, y)]])
# Hall-type necessary condition for a perfect domino matching: each class X needs its leftover
# pieces to partner with leftover pieces of classes compatible with X.
for x in classes:
    nb = sum(left[y] for y in classes if compat[(x, y)])
    flag = "" if left[x] <= nb else "  <-- HALL FAILS"
    print(f"  class {x}: leftover {left[x]}, compatible leftover {nb}{flag}")
print("total leftover", sum(left.values()), "(even needed for dominoes)")
# Corner L-tromino check: which class pairs of edges can join each leftover corner piece?
corners = [i for i in range(len(pieces)) if nflat[i] == 2]
print("corner classes (all 7 double-flat pieces):", dict(Counter(pieces[i].cls for i in corners)))
ccls = Counter(pieces[i].cls for i in corners)
for cc in sorted(ccls):
    root = next(i for i in corners if pieces[i].cls == cc)
    pairs = []
    for x, y in itertools.combinations_with_replacement(classes, 2):
        ok = any(pc.group_placements(b, [pieces[root], pieces[a], pieces[bb]], cls_at, forced_at)
                 for a in [i for i in single if pieces[i].cls == x][:2]
                 for bb in [i for i in single if pieces[i].cls == y][:2] if a != bb)
        if ok:
            pairs.append(x + y)
    print(f"  corner class {cc}: L-tromino edge-class pairs {pairs}")
