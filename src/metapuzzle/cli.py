"""Command line interface: `metapuzzle solve` and `metapuzzle report`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .board import square_board
from .metrics import report
from .optimize import Solution, solve, validate_solution
from .pieces import make_inventory
from .scene import SceneError, load_scenes, pieces_from_scenes


def _parse_sizes(text: str) -> list[tuple[int, int]]:
    out = []
    for part in text.split(","):
        try:
            c, r = part.lower().split("x")
            out.append((int(c), int(r)))
        except ValueError:
            raise SystemExit(f"bad --sizes entry {part!r}; expected COLSxROWS") from None
    if len(out) == 1:
        out = out * 3
    if len(out) != 3:
        raise SystemExit("--sizes needs one or three COLSxROWS entries")
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="metapuzzle", description="Multi-solution jigsaw arrangement engine.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("solve", help="find three low-overlap placements")
    s.add_argument("--cols", type=int)
    s.add_argument("--rows", type=int)
    s.add_argument("--sizes", help="per-solution sizes COLSxROWS,COLSxROWS,COLSxROWS (equal piece counts)")
    s.add_argument("--border", choices=["standard", "tray"], default="standard")
    s.add_argument("--rotation", choices=["none", "quarter"], default="none")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--iters", type=int, default=None)
    s.add_argument("--scenes", nargs="+", metavar="PATH", help="class maps: three files, or one file with three maps")
    s.add_argument("--extra-flat", type=int, default=0, help="flat-sided pieces beyond the perimeter")
    s.add_argument("--free-corners", action="store_true", help="corner pieces may rotate even without rotation mode")
    s.add_argument("--distinct-corner-orders", action="store_true", help="three different cyclic corner orders")
    s.add_argument("--out", help="write solution JSON here")
    r = sub.add_parser("report", help="print metrics for a solution JSON")
    r.add_argument("path")
    r.add_argument("--json", action="store_true", help="print the metrics dict as JSON")
    g = sub.add_parser("render", help="draw the three placements and a piece sheet as SVG/PNG")
    g.add_argument("path")
    g.add_argument("--out", required=True, help="output directory")
    g.add_argument("--cell", type=int, default=40, help="cell size in pixels")
    g.add_argument("--grid", choices=["none", "faint", "strong"], default="none", help="cell outlines")
    g.add_argument("--labels", action="store_true", help="print piece ids in the cells")
    return ap


def _cmd_solve(a: argparse.Namespace) -> int:
    maps = None
    if a.scenes:
        maps = load_scenes(a.scenes)
        sizes = [(m.cols, m.rows) for m in maps]
        explicit = _parse_sizes(a.sizes) if a.sizes else ([(a.cols, a.rows)] * 3 if a.cols and a.rows else None)
        if explicit and explicit != sizes:
            raise SystemExit(f"requested sizes {explicit} differ from the class map sizes {sizes}")
    elif a.sizes:
        sizes = _parse_sizes(a.sizes)
    else:
        sizes = [(a.cols or 10, a.rows or 8)] * 3
    boards = [square_board(c, r, a.border, a.rotation) for c, r in sizes]
    if maps:
        pieces = pieces_from_scenes(boards, maps, a.extra_flat, a.free_corners)
    else:
        pieces = make_inventory(boards, "any", a.extra_flat, a.free_corners)
    sol = solve(boards, pieces, maps, seed=a.seed, iters=a.iters, distinct_corner_orders=a.distinct_corner_orders)
    m = sol.meta
    print(
        f"sizes={sizes} shared AB/AC/BC={m['shared']['AB']}/{m['shared']['AC']}/{m['shared']['BC']} "
        f"valid={m['valid']} iters={m['iters_used']} time={m['elapsed_s']}s"
    )
    if a.out:
        sol.save(a.out)
        print(f"wrote {a.out}")
    return 0 if m["valid"] else 2


def _cmd_report(a: argparse.Namespace) -> int:
    sol = Solution.load(a.path)
    rep = report(sol)
    errs = validate_solution(sol)
    if a.json:
        print(json.dumps({k: v for k, v in rep.items() if k != "text"}, indent=2))
    else:
        print(rep["text"])
        print("validity: OK" if not errs else f"validity: {len(errs)} problem(s), first: {errs[0]}")
    return 0 if not errs else 2


def _cmd_render(a: argparse.Namespace) -> int:
    from .render import flat_class_drawer, render_all  # lazy: cairosvg is only needed here

    sol = Solution.load(a.path)
    written = render_all(
        sol, flat_class_drawer(), a.out, Path(a.path).stem,
        cell_size=a.cell, grid=a.grid, labels=a.labels,
    )
    for path in written.values():
        print(path)
    return 0


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    handlers = {"solve": _cmd_solve, "report": _cmd_report, "render": _cmd_render}
    try:
        return handlers[a.cmd](a)
    except (SceneError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
