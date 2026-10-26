#!/usr/bin/env python3
"""Experiment 007: is the residual shared adjacency a limit of the search or of the class constraints?

Grid (both scene sets, 8x10, standard border):
  scenes  A: docs/design/scenes-8x10.txt + experiments/002-direction-a/classes.json
          B: docs/design/alt-b/scenes-8x10-b.txt + experiments/006-direction-b/classes.json if present,
             else a stub spec (every class non-directional, all four rotations)
  rotation none, quarter
  iterations 300k, 2M (solver iterations; the solver has no temperature or restart parameters)
  seeds 0-4 (the only restart mechanism)
Controls: the same boards with no class maps (make_inventory pieces, cls "any"), 300k for A and B,
2M for A. Analysis: per-class internal adjacency per scene, a random-placement baseline (exact
expectation for independent class-respecting uniform placements), and a rigorous forced floor.

Run:  python3 study.py [--workers N] [--quick] [--out DIR]
Writes results.json, grid.md, class-bottlenecks.md and run.log into --out (default: this folder).
"""
from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path("/home/user/metapuzzle")
sys.path.insert(0, str(REPO / "src"))

from metapuzzle.board import ROTATION_DEGREES, square_board  # noqa: E402
from metapuzzle.classes import load_class_spec  # noqa: E402
from metapuzzle.metrics import PAIR_NAMES, piece_gates, report, shared_adjacencies  # noqa: E402
from metapuzzle.optimize import solve, validate_solution  # noqa: E402
from metapuzzle.pieces import make_inventory  # noqa: E402
from metapuzzle.prototype import _allowed_rotations, _check_cells_fit  # noqa: E402
from metapuzzle.scene import load_scenes, pieces_from_scenes  # noqa: E402

ROTATIONS = ("none", "quarter")
SCENES = {
    "A": (REPO / "docs/design/scenes-8x10.txt", REPO / "experiments/002-direction-a/classes.json"),
    "B": (REPO / "docs/design/alt-b/scenes-8x10-b.txt", REPO / "experiments/006-direction-b/classes.json"),
}


class AllRotationsSpec:
    """Stub class spec used when no class spec file exists: every class non-directional, all rotations."""

    def allowed_rotations(self, cls: str) -> tuple[int, ...]:
        return ROTATION_DEGREES


def load_spec(path: Path):
    if path.exists():
        return load_class_spec(path), path.name
    return AllRotationsSpec(), "stub (all classes non-directional, all rotations)"


def build(scene: str, rot: str, mode: str):
    """Boards, pieces and class maps for one scene set. mode 'classes' or 'free' (no class maps)."""
    scenes_path, classes_path = SCENES[scene]
    maps = load_scenes(scenes_path)
    boards = [square_board(m.cols, m.rows, "standard", rot) for m in maps]
    if mode == "free":
        return boards, make_inventory(boards), None
    spec, _ = load_spec(classes_path)
    class_rotations = {c: _allowed_rotations(spec, c, rot) for c in maps[0].histogram()}
    pieces = pieces_from_scenes(boards, maps, allowed_rotations=class_rotations)
    _check_cells_fit(maps, boards, pieces)
    return boards, pieces, maps


def pair_key(x: str, y: str) -> str:
    a, b = sorted((x, y))
    return f"{a}|{b}"


def run_job(job: tuple) -> dict:
    scene, rot, mode, iters, seed = job
    boards, pieces, maps = build(scene, rot, mode)
    t0 = time.perf_counter()
    sol = solve(boards, pieces, maps, seed=seed, iters=iters)
    wall = time.perf_counter() - t0
    errs = validate_solution(sol)
    rep = report(sol)
    gate_ok, failures = piece_gates(sol)
    cls_of = {p.piece_id: p.cls for p in pieces}
    class_pairs: dict[str, dict[str, int]] = {}
    for name, (i, j) in zip(PAIR_NAMES, ((0, 1), (0, 2), (1, 2))):
        _, prs = shared_adjacencies(sol.placements[i], sol.placements[j], boards[i], boards[j])
        tally: dict[str, int] = defaultdict(int)
        for p, q in prs:
            tally[pair_key(cls_of[p], cls_of[q])] += 1
        class_pairs[name] = dict(tally)
    return {
        "class_pairs": class_pairs,
        "scene": scene, "rotation": rot, "mode": mode, "iters": iters, "seed": seed,
        "shared": {n: rep["pairs"][n]["shared"] for n in PAIR_NAMES},
        "total": rep["total_shared"], "valid": not errs, "violations": errs[:3],
        "gates_ok": gate_ok, "gate_failures": failures,
        "iters_used": sol.meta["iters_used"], "wall_s": round(wall, 2),
    }


def job_list(quick: bool) -> list[tuple]:
    iters = (3_000, 20_000) if quick else (300_000, 2_000_000)
    seeds = range(2) if quick else range(5)
    jobs = []
    for it in iters[::-1]:  # longest jobs first
        for scene in "AB":
            for rot in ROTATIONS:
                for s in seeds:
                    jobs.append((scene, rot, "classes", it, s))
    for scene in "AB":
        for rot in ROTATIONS:
            for s in seeds:
                jobs.append((scene, rot, "free", iters[0], s))
    for rot in ROTATIONS:
        for s in seeds:
            jobs.append(("A", rot, "free", iters[1], s))
    return jobs


def aggregate(results: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in results:
        groups[(r["scene"], r["rotation"], r["mode"], r["iters"])].append(r)
    rows = []
    for key in sorted(groups, key=lambda k: (k[2] != "classes", k[0], k[1], k[3])):
        rs = sorted(groups[key], key=lambda r: (r["total"], r["seed"]))
        best = rs[0]
        tot = [r["total"] for r in rs]
        rows.append({
            "scene": key[0], "rotation": key[1], "mode": key[2], "iters": key[3],
            "runs": len(rs), "valid_runs": sum(r["valid"] for r in rs),
            "best_total": best["total"], "best_seed": best["seed"], "best_shared": best["shared"],
            "best_gates_ok": best["gates_ok"], "best_gate_failures": best["gate_failures"],
            "mean_total": statistics.mean(tot), "sd_total": statistics.pstdev(tot),
            "min_pair": {n: min(r["shared"][n] for r in rs) for n in PAIR_NAMES},
            "mean_pair": {n: statistics.mean(r["shared"][n] for r in rs) for n in PAIR_NAMES},
            "gates_pass_runs": sum(r["gates_ok"] for r in rs),
            "mean_wall_s": round(statistics.mean(r["wall_s"] for r in rs), 2),
            "mean_class_pair": {
                n: {k: statistics.mean(r["class_pairs"][n].get(k, 0) for r in rs)
                    for k in sorted({k for r in rs for k in r["class_pairs"][n]})}
                for n in PAIR_NAMES
            },
        })
    return rows


def grid_md(rows: list[dict]) -> str:
    head = ("| scene | rotation | mode | iters | valid | best total (seed) | best AB/AC/BC | mean total (sd) | "
            "mean AB/AC/BC | best-run piece gates | gate pass runs | mean wall s |")
    out = [head, "|" + "---|" * 12]
    for r in rows:
        b = r["best_shared"]
        out.append(
            f"| {r['scene']} | {r['rotation']} | {r['mode']} | {r['iters']:,} | {r['valid_runs']}/{r['runs']} | "
            f"{r['best_total']} ({r['best_seed']}) | {b['AB']}/{b['AC']}/{b['BC']} | "
            f"{r['mean_total']:.1f} ({r['sd_total']:.1f}) | "
            f"{r['mean_pair']['AB']:.1f}/{r['mean_pair']['AC']:.1f}/{r['mean_pair']['BC']:.1f} | "
            f"{'PASS' if r['best_gates_ok'] else 'FAIL'} | {r['gates_pass_runs']}/{r['runs']} | {r['mean_wall_s']} |"
        )
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- lower-bound analysis
def _adj(a, b) -> bool:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def _cells(m) -> dict[str, list[tuple[int, int]]]:
    out: dict[str, list] = defaultdict(list)
    for y in range(m.rows):
        for x in range(m.cols):
            out[m.cls[y][x]].append((x, y))
    return out


def _edges(m) -> dict[tuple[str, str], int]:
    """Cell-adjacency counts: key (X, X) = internal edges of class X, key (X, Y) = X-Y edges."""
    e: dict[tuple[str, str], int] = defaultdict(int)
    for y in range(m.rows):
        for x in range(m.cols):
            for nx, ny in ((x + 1, y), (x, y + 1)):
                if nx < m.cols and ny < m.rows:
                    e[tuple(sorted((m.cls[y][x], m.cls[ny][nx])))] += 1
    return e


def _components(cells: list[tuple[int, int]]) -> int:
    left, count = set(cells), 0
    while left:
        count += 1
        stack = [left.pop()]
        while stack:
            x, y = stack.pop()
            for nb in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if nb in left:
                    left.remove(nb)
                    stack.append(nb)
    return count


def _term(x: str, y: str, ek: int, el: int, n: dict[str, int]) -> float:
    """Expected shared adjacencies between class pair (x, y) under independent random placements."""
    if x == y:
        return ek * el / math.comb(n[x], 2) if n[x] >= 2 else 0.0
    return ek * el / (n[x] * n[y])


def baseline(e_k, e_l, n) -> tuple[float, dict[str, float]]:
    """Expected shared adjacencies under independent uniform class-respecting placements in k and l.

    Same class X: e_k(X,X) * e_l(X,X) / C(n,2). Cross X,Y: e_k(X,Y) * e_l(X,Y) / (n_X n_Y).
    Cross terms are split half to each class so the per-class parts sum to the total.
    """
    total, per = 0.0, defaultdict(float)
    for key in set(e_k) | set(e_l):
        x, y = key
        ek, el = e_k.get(key, 0), e_l.get(key, 0)
        if not ek or not el:
            continue
        term = _term(x, y, ek, el, n)
        if x == y:
            per[x] += term
        else:
            per[x] += term / 2
            per[y] += term / 2
        total += term
    return total, per


def forced_floor(maps, k: int, l: int) -> tuple[int, list[str]]:
    """Rigorous lower bound on shared piece pairs between maps k and l, from counts alone.

    R1: a class with 2 cells: its two pieces are adjacent in map k iff the cells are adjacent, so
        the pair is shared when the cells are adjacent in both maps.
    R2: a singleton class Y (one piece) at cell c in map k: if every cell of class X (n_X cells)
        touches c, all X pieces are adjacent to the Y piece in k. Shared when that holds in both maps.
    R3: two singleton classes whose cells are adjacent in both maps.
    Pigeonhole for larger classes is vacuous here (C(n,2) exceeds the internal edge count), so omitted.
    """
    mk, ml = maps[k], maps[l]
    ck, cl = _cells(mk), _cells(ml)
    n = {c: len(v) for c, v in ck.items()}
    total, notes = 0, []
    classes = sorted(n)
    for X in classes:
        if n[X] == 2:
            u, v = ck[X]
            pu, pv = cl[X]
            if _adj(u, v) and _adj(pu, pv):
                total += 1
                notes.append(f"R1 {X} pair adjacent in both maps")
    for Y in classes:
        if n[Y] != 1:
            continue
        cy_k, cy_l = ck[Y][0], cl[Y][0]
        for X in classes:
            if X == Y:
                continue
            if n[X] >= 2:
                fk = sum(_adj(c, cy_k) for c in ck[X]) == n[X]
                fl = sum(_adj(c, cy_l) for c in cl[X]) == n[X]
                if fk and fl:
                    total += n[X]
                    notes.append(f"R2 {Y} touches all {n[X]} {X} pieces in both maps")
            elif n[X] == 1 and X < Y and _adj(ck[X][0], cy_k) and _adj(cl[X][0], cy_l):
                total += 1
                notes.append(f"R3 singletons {X}-{Y} adjacent in both maps")
    return total, notes


def class_analysis() -> dict:
    out = {}
    for scene in "AB":
        scenes_path, _ = SCENES[scene]
        maps = load_scenes(scenes_path)
        n = dict(maps[0].histogram())
        cells = [_cells(m) for m in maps]
        edges = [_edges(m) for m in maps]
        classes = sorted(n)
        per_class = []
        for X in classes:
            comps = [_components(cells[k][X]) for k in range(3)]
            ints = [edges[k].get((X, X), 0) for k in range(3)]
            per_class.append({
                "class": X, "n": n[X], "internal": ints, "components": comps,
                "n_minus_1": n[X] - 1, "connected_all": all(c == 1 for c in comps),
            })
        pairs = {}
        class_base = {name: defaultdict(float) for name in PAIR_NAMES}
        pair_base: dict[str, dict[str, float]] = {}
        for name, (k, l) in zip(PAIR_NAMES, ((0, 1), (0, 2), (1, 2))):
            tot, per = baseline(edges[k], edges[l], n)
            floor, notes = forced_floor(maps, k, l)
            pairs[name] = {"baseline_mean": round(tot, 2), "forced_floor": floor, "forced_notes": notes}
            for X, v in per.items():
                class_base[name][X] = v
            pair_base[name] = {
                pair_key(*key): _term(key[0], key[1], edges[k][key], edges[l][key], n)
                for key in set(edges[k]) & set(edges[l]) if edges[k][key] and edges[l][key]
            }
        for row in per_class:
            X = row["class"]
            row["baseline_AB"] = round(class_base["AB"][X], 2)
            row["baseline_all"] = round(sum(class_base[p][X] for p in PAIR_NAMES), 2)
            row["pigeonhole_AB"] = max(0, row["internal"][0] + row["internal"][1] - math.comb(n[X], 2)) if n[X] >= 2 else 0
        out[scene] = {"per_class": per_class, "pairs": pairs, "pair_baseline": pair_base,
                      "cross_edges_total": sum(v for key, v in edges[0].items() if key[0] != key[1])}
    return out


def class_pair_md(analysis: dict, rows: list[dict], top: int = 12) -> str:
    """Baseline vs solver shared adjacencies (pair AB) by class pair, for the classes-mode grid."""
    lines = []
    lo = min(r["iters"] for r in rows if r["mode"] == "classes")
    hi = max(r["iters"] for r in rows if r["mode"] == "classes")
    for scene, data in analysis.items():
        cfg = [("none", lo), ("none", hi), ("quarter", hi)]
        lookup = {(r["scene"], r["rotation"], r["mode"], r["iters"]): r for r in rows}
        base = data["pair_baseline"]["AB"]
        keys = sorted(base, key=lambda k: -base[k])[:top]
        lines += [f"## Scene set {scene}: AB shared adjacencies by class pair", "",
                  f"Random baseline vs solver mean over seeds (classes mode). Columns: none {lo:,}, none {hi:,}, quarter {hi:,}.", "",
                  "| class pair | baseline AB | none " + f"{lo:,}" + " | none " + f"{hi:,}" + " | quarter " + f"{hi:,}" + " |",
                  "|---|---|---|---|---|"]
        for k in keys:
            vals = []
            for rot, it in cfg:
                r = lookup.get((scene, rot, "classes", it))
                vals.append(f"{r['mean_class_pair']['AB'].get(k, 0):.2f}" if r else "-")
            lines.append(f"| {k.replace('|', ' / ')} | {base[k]:.2f} | " + " | ".join(vals) + " |")
        lines.append("")
    return "\n".join(lines)


def class_md(analysis: dict) -> str:
    lines = ["# Per-class internal adjacency and baselines (experiment 007)", ""]
    lines += ["Internal = cell-adjacent pairs of the class within one scene map (A/B/C). n-1 is the spanning-tree",
              "minimum for a connected region; it is NOT a lower bound on shared adjacency. Baseline = expected",
              "shared adjacencies under independent uniform class-respecting placements (AB shown; 'all' = AB+AC+BC",
              "with cross terms split between the two classes). Pigeonhole = max(0, e_A + e_B - C(n,2)), which",
              "is the only counting bound on same-class pairs, and it is 0 for every class here.", ""]
    for scene, data in analysis.items():
        lines += [f"## Scene set {scene}", "",
                  "| class | n | internal A/B/C | components A/B/C | n-1 | pigeonhole AB | baseline AB (class share) | baseline all pairs (class share) |",
                  "|---|---|---|---|---|---|---|---|"]
        rows = sorted(data["per_class"], key=lambda r: -r["baseline_all"])
        for r in rows:
            i, c = r["internal"], r["components"]
            lines.append(
                f"| {r['class']} | {r['n']} | {i[0]}/{i[1]}/{i[2]} | {c[0]}/{c[1]}/{c[2]} | {r['n_minus_1']} | "
                f"{r['pigeonhole_AB']} | {r['baseline_AB']} | {r['baseline_all']} |"
            )
        lines += ["", "| pair | random-placement baseline (mean) | forced floor (rigorous) | forced notes |", "|---|---|---|---|"]
        for name, p in data["pairs"].items():
            notes = "; ".join(p["forced_notes"]) or "-"
            lines.append(f"| {name} | {p['baseline_mean']} | {p['forced_floor']} | {notes} |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--quick", action="store_true", help="tiny grid for testing the pipeline")
    ap.add_argument("--out", type=Path, default=HERE)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    log = open(args.out / "run.log", "w")

    def say(msg: str) -> None:
        print(msg, flush=True)
        log.write(msg + "\n")
        log.flush()

    specs = {s: load_spec(SCENES[s][1])[1] for s in SCENES}
    say(f"class specs: {specs}")
    jobs = job_list(args.quick)
    say(f"{len(jobs)} solver jobs on {args.workers} workers")
    t0 = time.perf_counter()
    results = []
    with mp.get_context("fork").Pool(args.workers) as pool:
        for r in pool.imap_unordered(run_job, jobs, chunksize=1):
            results.append(r)
            say(f"  {r['scene']} {r['rotation']:7s} {r['mode']:7s} {r['iters']:>9,} seed {r['seed']}: "
                f"AB/AC/BC {r['shared']['AB']}/{r['shared']['AC']}/{r['shared']['BC']} total {r['total']} "
                f"valid={r['valid']} gates={'PASS' if r['gates_ok'] else 'FAIL'} {r['wall_s']}s")
    wall = time.perf_counter() - t0
    say(f"grid wall time {wall:.1f}s")

    rows = aggregate(results)
    analysis = class_analysis()
    results_path = args.out / "results.json"
    results_path.write_text(json.dumps({
        "specs": specs, "grid_wall_s": round(wall, 1), "aggregate": rows, "analysis": analysis, "runs": results,
    }, indent=1))
    (args.out / "grid.md").write_text(grid_md(rows))
    (args.out / "class-bottlenecks.md").write_text(class_md(analysis) + "\n" + class_pair_md(analysis, rows))
    say((args.out / "grid.md").read_text())
    say(f"wrote {results_path}")


if __name__ == "__main__":
    main()
