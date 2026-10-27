"""End-to-end prototype run: class maps and a class spec in, a solved and rendered set out.

`run_prototype` loads the three class maps, derives the piece inventory from them, restricts
each piece's rotations by its class in the spec, solves, and writes solution, metrics, renders,
triptychs and a summary into one output directory. `metapuzzle prototype` wraps it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PIL import Image

from .board import ROTATION_DEGREES, square_board
from .classes import ClassSpec, load_class_spec
from .connectors import class_summary, format_summary
from . import scene_metrics
from .metrics import PAIR_NAMES, gate_line, report
from .optimize import solve, validate_solution
from .pieces import Piece, rotations_for_piece
from .render import render_all, render_solution_png, render_solution_svg
from .scene import SceneError, load_scenes, pieces_from_scenes

TRIPTYCH_MAX_HEIGHT = 600
TRIPTYCH_GAP = 24
NAMES = ("A", "B", "C")


def parse_sizes(sizes) -> list[tuple[int, int]]:
    """'8x10,8x10,8x10' or a sequence of (cols, rows) -> three (cols, rows); one entry is repeated."""
    if isinstance(sizes, str):
        entries = []
        for part in (p.strip().lower() for p in sizes.split(",") if p.strip()):
            bits = part.split("x")
            if len(bits) != 2 or not all(b.isdigit() for b in bits):
                raise ValueError(f"bad sizes entry {part!r}; expected COLSxROWS")
            entries.append((int(bits[0]), int(bits[1])))
    else:
        entries = [(int(c), int(r)) for c, r in sizes]
    if len(entries) == 1:
        entries *= 3
    if len(entries) != 3:
        raise ValueError("sizes needs one or three COLSxROWS entries")
    return entries


def _allowed_rotations(spec: ClassSpec, cls: str, rotation: str) -> frozenset[int]:
    """Rotations a piece of class `cls` may use.

    Rotation "none" pins every piece to 0 (the spec's rotations only apply in "quarter" mode).
    Rotation "quarter" uses the spec's allowed rotations for the class.
    """
    if rotation == "none":
        return frozenset({0})
    return frozenset(spec.allowed_rotations(cls)) & frozenset(ROTATION_DEGREES)


def _check_cells_fit(maps, boards, pieces: list[Piece]) -> None:
    """Each cell of each map needs at least one piece of its class that fits it.

    Necessary, not sufficient, for a solution; it turns an opaque solver failure into a
    message that names the cell (e.g. a directional class on a frame side that needs rotation).
    """
    by_cls: dict[str, list[Piece]] = {}
    for p in pieces:
        by_cls.setdefault(p.cls, []).append(p)
    for k, (m, b) in enumerate(zip(maps, boards)):
        for s in b.slots:
            cls = m.cls[s.y][s.x]
            forced = m.rot[s.y][s.x] or None
            if not any(rotations_for_piece(b, p, s.id, forced) for p in by_cls.get(cls, [])):
                raise SceneError(
                    f"map {NAMES[k]} cell ({s.x},{s.y}) class {cls!r}: no piece of that class fits "
                    f"the cell at its allowed rotations"
                )


def seam_counts(sol) -> list[dict]:
    """Per board: flat-flat contacts (seams) inside the picture and flat-sided pieces off the frame."""
    by_id = {p.piece_id: p for p in sol.pieces}
    out = []
    for pl, b in zip(sol.placements, sol.boards):
        at = {s: pid for pid, (s, _) in pl.items()}
        seams = 0
        for sl in b.slots:
            for face, (x, y) in ((1, (sl.x + 1, sl.y)), (2, (sl.x, sl.y + 1))):  # E and S: each contact once
                if x >= b.cols or y >= b.rows:
                    continue
                a, c = at[sl.id], at[b.slot_at(x, y)]
                if (by_id[a].sides[(face - pl[a][1] // 90) % 4] == "flat"
                        and by_id[c].sides[(face + 2 - pl[c][1] // 90) % 4] == "flat"):
                    seams += 1
        inside = sum(1 for pid, (s, _) in pl.items() if "flat" in by_id[pid].sides and not b.slots[s].boundary_sides)
        out.append({"seams": seams, "flat_pieces_inside": inside})
    return out


def _triptych(paths: Sequence[Path], dest: Path) -> Path:
    """Side by side, each image at most TRIPTYCH_MAX_HEIGHT tall, TRIPTYCH_GAP apart, white."""
    images = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        if im.height > TRIPTYCH_MAX_HEIGHT:
            w = round(im.width * TRIPTYCH_MAX_HEIGHT / im.height)
            im = im.resize((w, TRIPTYCH_MAX_HEIGHT), Image.LANCZOS)
        images.append(im)
    height = max(im.height for im in images)
    width = sum(im.width for im in images) + TRIPTYCH_GAP * (len(images) - 1)
    canvas = Image.new("RGB", (width, height), "white")
    x = 0
    for im in images:
        canvas.paste(im, (x, (height - im.height) // 2))
        x += im.width + TRIPTYCH_GAP
    canvas.save(dest)
    return dest


def _summary_md(
    *, params: dict, rep: dict, errs: list[str], scene_text: str,
    gate_lines: list[str], missing_classes: list[str], files: list[str], connectors_text: str = "",
) -> str:
    rows = dict(params)
    rows["valid"] = "yes" if not errs else f"no ({len(errs)} violation(s))"
    if missing_classes:
        rows["classes not in spec (drawn as neutral stipple)"] = ", ".join(missing_classes)
    lines = ["# Prototype summary", "", "## Parameters", ""]
    lines += [f"- {key}: {value}" for key, value in rows.items()]
    lines += [f"  - violation: {e}" for e in errs[:5]]
    lines += [
        "",
        "## Piece-level shared adjacencies",
        "",
        "Adjacency = two pieces touching in a solution (flat seams included). Shared = touching in both solutions of the pair.",
        "",
        "| pair | shared | fraction | clusters (3+) | largest component | familiar pieces | max familiarity | mean familiarity |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name in PAIR_NAMES:
        v = rep["pairs"][name]
        lines.append(
            f"| {name} | {v['shared']} | {100 * v['fraction']:.2f}% | {v['clusters'] or '-'} | "
            f"{v['largest_component']} | {v['familiar_pieces']} | {v['max_familiarity']} | {v['mean_familiarity']:.3f} |"
        )
    lines += ["", f"Total shared: {rep['total_shared']}; cluster penalty: {rep['cluster_penalty']}; "
              f"rotated pieces per solution: {rep['rotated_pieces']}", "", "## Scene-level metrics", ""]
    lines += ["```text", scene_text, "```"]
    lines += ["", "## Gates", ""]
    lines += [f"- {g}" for g in gate_lines]
    if connectors_text:
        lines += [
            "", "## Connectors", "",
            "Mating classes: sides forced to share one connector shape (a contact in any solution is an edge). "
            "The smallest possible class is K(3,3), 6 sides, for tab/blank (K4, 4 sides, for andro). "
            "False fits are tab-blank pairs inside a class that touch in no solution; ratio = false fits / intended contacts.",
            "", "```text", connectors_text, "```",
        ]
    lines += ["", "## Files", ""]
    lines += [f"- `{f}`" for f in files]
    lines.append("- `summary.md` (this file)")
    return "\n".join(lines) + "\n"


def run_prototype(
    scenes_path,
    classes_path,
    out_dir,
    *,
    sizes=None,
    border: str = "standard",
    rotation: str = "none",
    seed: int = 0,
    iters: int | None = None,
    cell: int = 48,
    grid: str = "none",
    labels: bool = False,
    extra_flat: int = 0,
    mating_weight: float = 0.0,
    max_shared_fraction: float | None = None,
) -> dict:
    """Solve the three class maps and write the prototype outputs into `out_dir`.

    The class maps set each solution's board size. `sizes` (COLSxROWS,COLSxROWS,COLSxROWS or
    a sequence of pairs) is optional and must equal the map sizes. Piece rotations come from
    the class spec: pinned to 0 in "none" mode, the spec's allowed rotations in "quarter" mode.

    Boards of different shapes have different frames, so the border inventory covers the largest
    frame and the surplus flat-sided pieces sit inside the smaller pictures as seams (two flat
    sides touching). `extra_flat` adds that many more flat-sided pieces beyond the automatic ones.

    Returns a dict with `valid`, `violations`, `shared` (per pair), `files` (name -> path) and
    `out_dir`. Invalid solutions still write their outputs and return `valid: False`.
    `gates` is {"piece": ok, "scene": ok, "failures": [...]} (failures prefixed "piece: " or
    "scene: "); `gate_lines` are the two printed gate lines. Gate failures do not change `valid`.
    """
    maps = load_scenes(scenes_path)
    map_sizes = [(m.cols, m.rows) for m in maps]
    if sizes is not None:
        wanted = parse_sizes(sizes)
        if wanted != map_sizes:
            raise SceneError(f"requested sizes {wanted} differ from the class map sizes {map_sizes}")
    boards = [square_board(c, r, border, rotation) for c, r in map_sizes]
    spec = load_class_spec(classes_path)

    class_rotations = {cls: _allowed_rotations(spec, cls, rotation) for cls in maps[0].histogram()}
    pieces = pieces_from_scenes(boards, maps, extra_flat_pieces=extra_flat, allowed_rotations=class_rotations)
    _check_cells_fit(maps, boards, pieces)
    missing_classes = sorted(set(maps[0].histogram()) - set(spec.classes))

    sol = solve(boards, pieces, maps, seed=seed, iters=iters,
                mating_weight=mating_weight, max_shared_fraction=max_shared_fraction)
    errs = validate_solution(sol)
    connector_summary = class_summary(sol)
    seams = seam_counts(sol)
    rep = report(sol)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files: dict[str, Path] = {}

    files["solution.json"] = out / "solution.json"
    sol.save(files["solution.json"])

    validity = "validity: OK" if not errs else f"validity: {len(errs)} problem(s), first: {errs[0]}"
    files["metrics.txt"] = out / "metrics.txt"
    files["metrics.txt"].write_text(rep["text"] + "\n" + validity + "\n", encoding="utf-8")

    scene_rep = scene_metrics.report(maps)
    scene_text = scene_rep["text"]
    files["scene-metrics.txt"] = out / "scene-metrics.txt"
    files["scene-metrics.txt"].write_text(scene_text + "\n", encoding="utf-8")

    drawer = spec.drawer()
    rendered = render_all(sol, drawer, out, "solution", cell_size=cell, grid=grid, labels=labels)
    for path in rendered.values():
        files[path.name] = path
    files["triptych.png"] = _triptych([rendered[f"{n}.png"] for n in NAMES], out / "triptych.png")

    faint_dir = out / "grid-faint"
    faint_dir.mkdir(exist_ok=True)
    cache: dict = {}
    faint_pngs = []
    for k, n in enumerate(NAMES):
        svg = render_solution_svg(sol, k, drawer, cell_size=cell, grid="faint", labels=labels, cache=cache)
        faint_pngs.append(render_solution_png(svg, faint_dir / f"solution-{n}.png"))
        files[f"grid-faint/solution-{n}.png"] = faint_pngs[-1]
    files["triptych-grid.png"] = _triptych(faint_pngs, out / "triptych-grid.png")

    params = {
        "scenes": str(scenes_path),
        "classes": str(classes_path),
        "sizes": ", ".join(f"{c}x{r}" for c, r in map_sizes),
        "border": border,
        "rotation": rotation,
        "extra_flat": extra_flat,
        "mating_weight": mating_weight,
        "max_shared_fraction": sol.meta.get("max_shared_fraction"),
        "seed": seed,
        "iters": sol.meta.get("iters"),
        "iters_used": sol.meta.get("iters_used"),
        "cell": cell,
        "grid": grid,
        "labels": labels,
        "interior seams (A / B / C)": " / ".join(str(x["seams"]) for x in seams),
    }
    piece_failures, scene_failures = rep["gates"]["failures"], scene_rep["gates"]["failures"]
    gate_lines = [gate_line("piece", piece_failures), gate_line("scene", scene_failures)]
    gates = {
        "piece": rep["gates"]["ok"],
        "scene": scene_rep["gates"]["ok"],
        "failures": [f"piece: {f}" for f in piece_failures] + [f"scene: {f}" for f in scene_failures],
    }
    listed = [str(p.relative_to(out)) for p in files.values()]
    files["summary.md"] = out / "summary.md"
    files["summary.md"].write_text(
        _summary_md(params=params, rep=rep, errs=errs, scene_text=scene_text, gate_lines=gate_lines,
                    missing_classes=missing_classes, files=sorted(listed),
                    connectors_text=format_summary(connector_summary)),
        encoding="utf-8",
    )

    return {
        "seams": seams,
        "out_dir": str(out),
        "params": params,
        "valid": not errs,
        "violations": errs,
        "shared": {n: rep["pairs"][n]["shared"] for n in PAIR_NAMES},
        "files": {name: str(p) for name, p in files.items()},
        "gates": gates,
        "gate_lines": gate_lines,
    }
