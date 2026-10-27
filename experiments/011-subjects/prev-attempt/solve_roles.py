"""roles-to-scenes for a tray board (experiment 011).

`metapuzzle roles-to-scenes` builds a standard board inside `roles.assign_classes`, so it pools
and equalizes the frame, which value inversion cannot satisfy (each picture's frame has a
different tier mix). This script runs the same solver with a tray board by rebinding the
module's `square_board` name for the call (no change to src/), then validates the result with
tray boards and writes scenes.txt. Engine follow-up: give roles-to-scenes a --border option.

Usage (repo root): python3 experiments/011-subjects/solve_roles.py [--restarts 8] [--seed 0]
"""
import argparse
from pathlib import Path

from metapuzzle import roles, scene_metrics
from metapuzzle.board import square_board
from metapuzzle.scene import load_scenes, validate_scenes

HERE = Path(__file__).resolve().parent


def tray_board(cols, rows, border="standard", rotation="none"):
    return square_board(cols, rows, "tray", rotation)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--iters", type=int, default=20000)
    ap.add_argument("--restarts", type=int, default=8)
    a = ap.parse_args()
    roles.square_board = tray_board
    maps = roles.assign_classes(roles.load_role_maps(HERE / "roles.txt"), roles.load_roles_spec(HERE / "roles-spec.json"),
                                rotation="quarter", seed=a.seed, iters=a.iters, restarts=a.restarts)
    hist = maps[0].histogram()
    print("histogram: " + " ".join(f"{c}={n}" for c, n in sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))))
    for i, j in ((0, 1), (0, 2), (1, 2)):
        cnt, frac = scene_metrics.same_position_overlap(maps[i], maps[j])
        print(f"same-position {roles.NAMES[i]}-{roles.NAMES[j]}: {cnt} cells ({100 * frac:.1f}%)")
    out = HERE / "scenes.txt"
    roles.write_scene_file(maps, out)
    m = load_scenes(out)
    validate_scenes([square_board(m[0].cols, m[0].rows, "tray", "quarter")] * 3, m)
    print(f"wrote {out}: validate_scenes (tray, quarter) OK")


if __name__ == "__main__":
    main()
