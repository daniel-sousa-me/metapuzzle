"""Scenes for v5 from roles-v5.txt, with the common histogram given instead of searched.

`metapuzzle roles-to-scenes` searches a common histogram with roles._hall, which enumerates every subset
of the roles present in a container. The v5 interior has about 28 distinct roles per map (13 fixed edge
classes plus the slot roles), so the enumeration does not finish (killed after 15 min). Here the
histogram is the spec's target_counts, which every map must hit, so the skeleton is known: each
container holds the frame classes (plain, equal in all maps) or, for the interior, the target minus the
frame. Placement (max-flow per container) and the overlap annealing are the library's own
(roles._initial_arrangement, roles._arrange). Output: scenes-v5.txt, validated with validate_scenes.

Usage: build_scenes_v5.py [--restarts N] [--iters N]
"""
import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "src"))

from metapuzzle import roles as R  # noqa: E402
from metapuzzle.board import square_board  # noqa: E402
from metapuzzle.scene import ClassMap, validate_scenes  # noqa: E402

from gridcfg import WORK  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--restarts", type=int, default=8)
    ap.add_argument("--iters", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    spec_json = json.loads((WORK / "roles-spec.json").read_text(encoding="utf-8"))
    spec = R.parse_roles_spec(spec_json)
    role_maps = R.load_role_maps(WORK / "roles.txt")
    grids, rot_grids = R._grids(role_maps)
    rows, cols = len(grids[0]), len(grids[0][0])
    rotation = "quarter"
    board = square_board(cols, rows, "standard", rotation)
    flat = [[r for row in g for r in row] for g in grids]
    allowed, weights = spec.allowed, spec.weights
    containers = R._containers(board, rotation)
    names = [n for n, _ in containers]

    # Skeleton: frame containers hold their plain classes (same counts in every map); the interior
    # holds target_counts minus the frame.
    target = Counter(spec.target_counts)
    M: list[Counter] = []
    frame_total: Counter = Counter()
    for name, cells in containers:
        if name == "interior":
            M.append(Counter())
            continue
        m = Counter(allowed[flat[0][p]][0] for p in cells)  # frame roles are plain: one class each
        for k in (1, 2):
            if Counter(allowed[flat[k][p]][0] for p in cells) != m:
                raise SystemExit(f"frame container {name!r} differs between maps")
        M.append(m)
        frame_total.update(m)
    for g, (name, _) in enumerate(containers):
        if name == "interior":
            M[g] = Counter({c: target[c] - frame_total.get(c, 0) for c in target})
    if sum(M[g][c] for g in range(len(M)) for c in M[g]) != sum(target.values()):
        raise SystemExit("skeleton does not add up to 500 cells")
    print("containers:", names)
    print("skeleton:", {n: dict(sorted(M[g].items())) for g, n in enumerate(names)})

    results = []
    for r in range(max(1, args.restarts)):
        rng = random.Random(args.seed + r)
        try:
            cls0 = R._initial_arrangement(containers, flat, M, allowed)
        except R.SceneError as e:
            raise SystemExit(f"placement failed: {e}")
        cls, value = R._arrange(cls0, flat, containers, allowed, weights, board, rng, args.iters, 0.25, None, 1.0)
        results.append((value, r, cls))
        print(f"restart {r}: objective {value:.2f}")
    value, r, cls = min(results, key=lambda t: t[0])
    flat_rot = [[x for line in g for x in line] for g in rot_grids]
    maps = [
        ClassMap([row[y * cols:(y + 1) * cols] for y in range(rows)],
                 [rot[y * cols:(y + 1) * cols] for y in range(rows)])
        for row, rot in zip(cls, flat_rot)
    ]
    validate_scenes([board] * 3, maps)
    out = WORK / "scenes.txt"
    R.write_scene_file(maps, out)
    print(f"best restart {r} (objective {value:.2f}); wrote {out}")
    for k, m in enumerate(maps):
        h = m.histogram()
        assert all(h[c] == target[c] for c in target), f"map {'ABC'[k]} histogram differs from target"
    print("all three maps match target_counts; validate_scenes passed")


if __name__ == "__main__":
    main()
