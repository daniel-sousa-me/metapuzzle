"""Command line interface: `metapuzzle solve` and `metapuzzle report`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .board import square_board
from .metrics import report
from .optimize import Solution, solve, validate_solution
from . import scene_metrics
from .scene_metrics import SCENE_GATES
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
    g.add_argument("--classes", metavar="SPEC.json", help="draw pieces from a class spec instead of flat colours")
    sm = sub.add_parser(
        "scene-metrics",
        help="class carry-over metrics and scene gates between the three class maps",
        epilog=(
            "exit status: 0 when every scene gate passes, 3 when a scene gate fails, 1 on an input error. "
            f"Gates per pair: same-position overlap < {100 * SCENE_GATES['same_position_below']:g}% of cells, "
            f"2x2 window reuse (no rotation) < {100 * SCENE_GATES['window_2x2_plain_below']:g}%, "
            f"transferable blob < {100 * SCENE_GATES['transferable_below']:g}% of cells."
        ),
    )
    sm.add_argument("scenes", metavar="SCENES.txt", help="scene file with three class maps (text or JSON)")
    pt = sub.add_parser(
        "prototype",
        help="end to end: solve, metrics, renders, triptych and summary into a directory",
        epilog="prints the piece and scene gate lines; exit status 0 when valid, 2 when not (gates do not change it)",
    )
    pt.add_argument("--scenes", required=True, metavar="FILE", help="three class maps (text or JSON)")
    pt.add_argument("--classes", required=True, metavar="SPEC.json", help="class spec: drawing and per-class rotations")
    pt.add_argument("--out", required=True, metavar="DIR", help="output directory")
    pt.add_argument("--sizes", help="COLSxROWS,COLSxROWS,COLSxROWS; must match the class maps")
    pt.add_argument("--border", choices=["standard", "tray"], default="standard")
    pt.add_argument("--rotation", choices=["none", "quarter"], default="none")
    pt.add_argument("--seed", type=int, default=0)
    pt.add_argument("--iters", type=int, default=None)
    pt.add_argument("--extra-flat", type=int, default=0, metavar="N",
                    help="flat-sided pieces beyond those the frames need; the surplus sits inside as seams")
    pt.add_argument("--cell", type=int, default=48, help="cell size in pixels")
    pt.add_argument("--labels", action="store_true", help="print piece ids in the cells")
    gt = sub.add_parser(
        "gen-transitions",
        help="add transition classes (base texture + masked mass texture) for field pairs",
        epilog="writes the new spec only after it validates; exit status 1 on an input error",
    )
    gt.add_argument("spec", metavar="SPEC.json", help="class spec to extend")
    gt.add_argument("--fields", required=True, metavar="CODES", help="comma-separated field class codes, e.g. SK,ME,DP,FO")
    gt.add_argument("--out", required=True, metavar="NEW.json", help="output class spec")
    gt.add_argument("--sides", default="top,bottom,left,right", help="comma-separated mask sides")
    gt.add_argument("--coverage", type=float, default=0.45, help="blotch_mask coverage in [0, 1]")
    gt.add_argument("--rotatable", action="store_true",
                    help="one side per pair, non-directional; orient in scenes with the @90 suffix")
    gt.add_argument("--corners", action="store_true", help="also add a class per pair of adjacent sides")
    ps = sub.add_parser("prune-spec", help="keep only the classes that the scene files use")
    ps.add_argument("spec", metavar="SPEC.json", help="class spec to prune")
    ps.add_argument("--scenes", required=True, nargs="+", metavar="FILE",
                    help="scene files: three files, or one file with three maps")
    ps.add_argument("--out", required=True, metavar="NEW.json", help="output class spec")
    rs = sub.add_parser(
        "roles-to-scenes",
        help="solve a role map into three class maps with identical histograms and border counts",
        epilog="exit status 0 on success, 1 on an input error or when no common histogram is found",
    )
    rs.add_argument("roles", metavar="ROLES.txt", help="three role grids in scene-file layout")
    rs.add_argument("--spec", required=True, metavar="ROLES.json", help="allowed classes and weights per role")
    rs.add_argument("--out", required=True, metavar="SCENES.txt", help="output scene file")
    rs.add_argument("--rotation", choices=["none", "quarter"], default="none")
    rs.add_argument("--seed", type=int, default=0)
    rs.add_argument("--iters", type=int, default=20000, help="annealing iterations per phase")
    rs.add_argument("--restarts", type=int, default=1, help="runs with seeds SEED, SEED+1, ...; keep the best")
    gm = sub.add_parser(
        "grid-metric",
        help="automatic grid visibility: colour steps along piece edges in a run's solution PNGs",
        epilog="score 1 (grid invisible) to 5 (strong); bands on the visible fraction are in grid_metric.GRID_SCORE_BANDS",
    )
    gm.add_argument("run_dir", metavar="RUN_DIR", help="prototype output folder (summary.md, solution.json, solution-*.png)")
    cn = sub.add_parser(
        "connectors",
        help="mating classes (connector shapes) and false fits of a solution JSON",
        epilog="exit status 0 when every touching non-flat pair mates, 2 when some do not, 1 on an input error",
    )
    cn.add_argument("path", metavar="SOLUTION.json")
    return ap


def _cmd_connectors(a: argparse.Namespace) -> int:
    from .connectors import class_summary, format_summary  # lazy, like the other analysis commands

    s = class_summary(Solution.load(a.path))
    print(format_summary(s))
    return 0 if s["mismatched"] == 0 else 2


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

    if a.classes:
        from .classes import load_class_spec  # lazy, like render

        drawer = load_class_spec(a.classes).drawer()
    else:
        drawer = flat_class_drawer()
    sol = Solution.load(a.path)
    written = render_all(
        sol, drawer, a.out, Path(a.path).stem,
        cell_size=a.cell, grid=a.grid, labels=a.labels,
    )
    for path in written.values():
        print(path)
    return 0


def _cmd_scene_metrics(a: argparse.Namespace) -> int:
    rep = scene_metrics.report(load_scenes(a.scenes))
    print(rep["text"])
    return 0 if rep["gates"]["ok"] else 3


def _cmd_prototype(a: argparse.Namespace) -> int:
    from .prototype import run_prototype  # lazy: pulls in PIL and the texture drawer

    res = run_prototype(
        a.scenes, a.classes, a.out, sizes=a.sizes, border=a.border, rotation=a.rotation,
        seed=a.seed, iters=a.iters, cell=a.cell, labels=a.labels, extra_flat=a.extra_flat,
    )
    s = res["shared"]
    print(
        f"sizes={res['params']['sizes']} shared AB/AC/BC={s['AB']}/{s['AC']}/{s['BC']} "
        f"valid={res['valid']} wrote {len(res['files'])} files to {res['out_dir']}"
    )
    for line in res["gate_lines"]:
        print(line)
    return 0 if res["valid"] else 2


def _write_spec(data: dict, out: str) -> None:
    Path(out).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _cmd_gen_transitions(a: argparse.Namespace) -> int:
    from .classes import ClassSpec, load_class_spec  # lazy: cairosvg is only needed for validation
    from .spec_tools import generate_transitions

    load_class_spec(a.spec)  # the input must be a valid spec
    raw = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    fields = [f.strip() for f in a.fields.split(",") if f.strip()]
    sides = [s.strip() for s in a.sides.split(",") if s.strip()]
    out = generate_transitions(raw, fields, sides=sides, coverage=a.coverage,
                               rotatable=a.rotatable, corner=a.corners)
    ClassSpec.from_dict(out).validate()
    _write_spec(out, a.out)
    added = len(out["classes"]) - len(raw["classes"])
    print(f"wrote {a.out}: {len(out['classes'])} classes, {added} generated")
    return 0


def _cmd_prune_spec(a: argparse.Namespace) -> int:
    from .classes import ClassSpec, load_class_spec
    from .spec_tools import prune_unused

    load_class_spec(a.spec)
    raw = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    out = prune_unused(raw, a.scenes)
    ClassSpec.from_dict(out).validate()
    _write_spec(out, a.out)
    print(f"wrote {a.out}: kept {len(out['classes'])} of {len(raw['classes'])} classes")
    return 0


def _cmd_roles_to_scenes(a: argparse.Namespace) -> int:
    from .roles import NAMES, assign_classes, load_role_maps, load_roles_spec, write_scene_file
    from .scene import validate_scenes

    maps = assign_classes(
        load_role_maps(a.roles), load_roles_spec(a.spec), rotation=a.rotation, seed=a.seed, iters=a.iters,
        restarts=a.restarts,
    )
    hist = maps[0].histogram()
    print("histogram: " + " ".join(f"{c}={n}" for c, n in sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))))
    for i, j in ((0, 1), (0, 2), (1, 2)):
        cnt, frac = scene_metrics.same_position_overlap(maps[i], maps[j])
        print(f"same-position {NAMES[i]}-{NAMES[j]}: {cnt} cells ({100 * frac:.1f}%)")
    write_scene_file(maps, a.out)
    board = square_board(maps[0].cols, maps[0].rows, "standard", a.rotation)
    validate_scenes([board] * 3, load_scenes(a.out))  # round trip through the scene loader
    print(f"wrote {a.out}: validate_scenes OK")
    return 0


def _cmd_grid_metric(a: argparse.Namespace) -> int:
    from .grid_metric import run_grid_metric  # lazy: pulls in PIL and render

    res = run_grid_metric(a.run_dir)
    g = res["geometry"]
    print(f"cell={g['cell']}px margin={g['margin']}px (render default; not recorded) boards={g['sizes']}")
    for s in res["solutions"]:
        print(f"{s['solution']}  visible {s['visible_fraction']:.3f}  lines {s['line_fraction']:.3f}  score {s['score']:g}")
    return 0


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    handlers = {"solve": _cmd_solve, "report": _cmd_report, "render": _cmd_render, "scene-metrics": _cmd_scene_metrics, "prototype": _cmd_prototype,
                "gen-transitions": _cmd_gen_transitions, "prune-spec": _cmd_prune_spec,
                "roles-to-scenes": _cmd_roles_to_scenes,
                "grid-metric": _cmd_grid_metric, "connectors": _cmd_connectors}
    try:
        return handlers[a.cmd](a)
    except (SceneError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
