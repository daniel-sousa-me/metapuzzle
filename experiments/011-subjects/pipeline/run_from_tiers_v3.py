#!/usr/bin/env python3
"""v3 of run_from_tiers_v2.py: per-class-pair placement of surplus transition pieces (FINDINGS 14, 20, 23).

Same stages and same histogram target as v2. Only the roles stage differs: surplus S-L pieces go to S cells
next to an S-L boundary (oriented to extend the ragged edge), surplus D-L and D-M pieces to D interior cells
at distance >= 2 from any transition (free rotation), M-L pieces to M interior (lower part first), and W pairs
to W cells (MW falls back to M when the fixed target keeps W plain). Fallbacks are logged per image and pair.
Intermediates go to pipeline/v3/, renders to 27x38/run-ink-v3/ and 27x38/run-full-v3/.

Same stages as v1 (run_from_tiers.py, kept unchanged). Differences in v2:
  - ORDER D < S < M < W < L (S mid-dark). S cells are classified like any tier with the 8-neighbourhood
    rule, so S-L contacts become transitions (classes SLs/LSs/SLc/... from classes-v9.json). S-D, S-M and
    S-W contacts (8-neighbourhood) are forbidden: counted at classify, and never created by equalize.
  - equalize may move cells between S and L (cost 1 each); no other S move is legal.
  - roles treat S as a plain tier too (s_near/s_far/s_slot/...); the S count is part of the plain targets.
  - intermediates go to pipeline/v2/ (v1 files in pipeline/ are not overwritten); renders go to
    27x38/run-ink-v2/ and 27x38/run-full-v2/.

Experiment 011 (Field, Wood and Water): tier files -> transition classes -> roles -> scenes -> renders.

Reads 27x38/tiers-{A,B,C}.txt directly (tokens D M W L S; A hare, B owl, C swan). Adapted from
experiment 013 (quantize_v5.py, make_roles_v5.py, build_scenes_v5.py) and 005 (classes-v4/ink specs,
equalize_budgets_v5b.py). Nothing in src/ or in 005/013 is modified.

Stages (each reads the files of the previous one, so a stage can be re-run alone):
  classify  tiers -> merged transition classes (darker tier hosts; ties to the lighter tier;
            frame cells plain; S plain and never a transition; W a tier, order D < M < W < L)
  budgets   per-class max over images, surplus, pair edges, S contacts, verify_edges
  roles     roles.txt and roles-spec.json (surplus into 8-isolated far slots, near fallback)
  scenes    three class maps, common whole-board histogram, one skeleton per map, validate_scenes
  metrics   metapuzzle scene-metrics
  render    metapuzzle prototype with classes-ink.json and classes-v4.json

Differences from 013/005 that the data forced:
  - Frame composition differs between images (edge and corner pools), so the `standard` border
    cannot hold (validate_scenes compares them). The renders use the `tray` border, which the
    README anticipates. `--border standard` is still accepted and fails validation (see report).
  - Tier totals differ slightly between images. The roles planner works per image (F_k per tier)
    with common plain targets, instead of refusing unequal totals.
  - S cells are fixed plain roles (s_frame, s_fix); W is a transition tier like M, L, D.

Usage: run_from_tiers.py [--stages classify,budgets,roles,scenes,metrics,render] [--border tray]
                         [--iters N] [--seed N] [--restarts N] [--cell N]
                         [--in-dir 27x38] [--out-dir D --render-tag ""]   (D: pipeline-out/, run-ink/, run-full/)
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import subprocess
import sys
import time
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent              # experiments/011-subjects/pipeline
EXP = HERE.parent                                   # experiments/011-subjects
REPO = HERE.parents[2]                              # /home/user/metapuzzle
CLS_DIR = REPO / "experiments" / "005-hybrid-tones"  # class specs (read only)
SIZE_DIR = EXP / "27x38"                             # input tiers (--in-dir)
OUT_DIR = SIZE_DIR                                   # renders (--out-dir; default: the input folder)
RENDER_TAG = "-v3"                                   # render folder suffix (--render-tag)
IMAGES =["A", "B", "C"]                            # hare, owl, swan
IMAGE_NAME = {"A": "hare", "B": "owl", "C": "swan"}
TILES = "DMWLS"
ORDER = "DSMWL"                                      # darker first: D < S < M < W < L (v2: S mid-dark)
RANK = {t: i for i, t in enumerate(ORDER)}
PAIRS = ["DM", "DW", "DL", "MW", "ML", "WL", "SL"]
FORBIDDEN_S = frozenset("DMW")                       # S may touch L only (8-neighbourhood)
V9_CLASSES, V9_INK = "classes-v9.json", "classes-ink-v9.json"   # in pipeline/, from gen_classes_v9.py
WORK = HERE / "v3"                                   # this run's intermediates (v1 and v2 files are kept)
SIDE_OFF = [(0, -1), (1, 0), (0, 1), (-1, 0)]        # T, R, B, L as (dx, dy)
CORNER_OFF = [(-1, -1), (1, -1), (1, 1), (-1, 1)]    # TL, TR, BR, BL
CANON = {"s": (0,), "c": (0, 1), "p": (0, 1, 3)}
OPPOSITE = [frozenset({0, 2}), frozenset({1, 3})]
APPROX_ORDER = ["strip", "s+diag", "c+diag", "i+multi"]
# Half-edge profiles of the canonical pieces (from v5 quantize): sides T, R, B, L, two halves each.
HALVES = {
    "s": [("m", "m"), ("m", "b"), ("b", "b"), ("b", "m")],
    "p": [("m", "m"), ("m", "b"), ("b", "b"), ("b", "m")],
    "c": [("m", "m"), ("m", "m"), ("m", "b"), ("b", "m")],
    "d": [("b", "b")] * 4,
}
SURPLUS_W, NSLOT_W = 0.5, 0.2
N_RESTARTS = 3000
SEED = 0
def log(msg: str = "") -> None:
    print(msg, flush=True)


# ------------------------------------------------------------------ input and classification


def read_tiers(path: Path) -> list[list[str]]:
    rows = [ln.split() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not rows or len({len(r) for r in rows}) != 1:
        raise SystemExit(f"{path}: rows are empty or ragged")
    bad = {t for r in rows for t in r} - set(TILES)
    if bad:
        raise SystemExit(f"{path}: unknown tokens {sorted(bad)}")
    return rows


def is_frame(r: int, c: int, R: int, C: int) -> bool:
    return r in (0, R - 1) or c in (0, C - 1)


@dataclass(frozen=True)
class Cell:
    code: str    # v4-style code: own tier, neighbour tier, pattern (or nbr+own+'d' for dots)
    token: str   # with rotation suffix
    pattern: str  # plain / s / c / i / p / d
    approx: str | None
    mixed: bool  # two different lighter tiers among the 8 neighbours (three-tier junction)


def rot_of(pattern: str, sides: frozenset) -> int:
    for r in range(4):
        if {(k + r) % 4 for k in CANON[pattern]} == set(sides):
            return r
    raise AssertionError((pattern, sides))


def classify(tok: list[list[str]], r: int, c: int) -> Cell:
    R, C = len(tok), len(tok[0])
    t = tok[r][c]
    if is_frame(r, c, R, C):
        return Cell(t, t, "plain", None, False)
    own = RANK[t]

    def at(dx: int, dy: int) -> int:
        rr, cc = r + dy, c + dx
        return RANK[tok[rr][cc]] if (0 <= rr < R and 0 <= cc < C) else own  # outside counts as own

    sides = [at(dx, dy) for dx, dy in SIDE_OFF]
    corners = [at(dx, dy) for dx, dy in CORNER_OFF]
    differing = [x for x in sides + corners if x > own]  # host rule: only lighter neighbours count
    if not differing:
        return Cell(t, t, "plain", None, False)
    count = Counter(differing)
    n = max(count, key=lambda x: (count[x], x))  # ties go to the lighter tier (higher rank)
    mixed = len(count) > 1
    S = frozenset(k for k in range(4) if sides[k] == n)
    Q = [k for k in range(4) if corners[k] == n and k not in S and (k + 3) % 4 not in S]
    nbr = ORDER[n]
    approx = None
    if len(S) == 4:
        return Cell(nbr + t + "d", nbr + t + "d", "d", None, mixed)
    if len(S) == 3:
        pattern, rot = "p", rot_of("p", S)
    elif len(S) == 2 and S in OPPOSITE:
        approx = "strip"
        pattern, rot = "s", min(S)
    elif len(S) == 2:
        pattern, rot = "c", rot_of("c", S)
        if Q:
            approx = "c+diag"
    elif len(S) == 1:
        pattern, rot = "s", rot_of("s", S)
        if Q:
            approx = "s+diag"
    else:  # convex corner: no side has the neighbour tier
        assert Q, "a lighter neighbour must be a side or a corner"
        pattern, rot = "i", Q[0]
        if len(Q) > 1:
            approx = "i+multi"
    code = t + nbr + pattern
    token = code if rot == 0 else f"{code}@{90 * rot}"
    return Cell(code, token, pattern, approx, mixed)


def merged(cell: Cell) -> tuple[str, int] | None:
    """(merged class, rotation in degrees) of a classified cell; None for a plain cell.

    Straights: darker tier first (PQs). A straight whose own tier is the lighter one is turned by 180
    so that its base faces the darker neighbour (FLIP_LIGHT_STRAIGHTS of v5, always on here).
    """
    deg = int(cell.token.partition("@")[2] or 0)
    if cell.pattern == "plain":
        return None
    if cell.pattern == "d":
        return cell.code, 0
    own, nbr = cell.code[0], cell.code[1]
    if cell.pattern == "s":
        P, Q = sorted((own, nbr), key=ORDER.index)
        turn = own == Q
        return P + Q + "s", ((deg + 180) % 360) if turn else deg
    if cell.pattern == "c":
        return own + nbr + "c", deg
    if cell.pattern == "i":
        return nbr + own + "c", ((deg // 90 - 3) % 4) * 90
    if cell.pattern == "p":
        return own + nbr + "p", deg
    raise AssertionError(cell)


def pair_of(cls: str) -> str:
    return "".join(sorted(cls[:2], key=ORDER.index))


def classify_image(tok: list[list[str]]) -> dict:
    R, C = len(tok), len(tok[0])
    grid = [[classify(tok, r, c) for c in range(C)] for r in range(R)]
    st = {"grid": grid, "tokens": [], "hist": Counter(), "approx": Counter(), "pair_approx": Counter(),
          "own_tr": Counter(), "mixed": 0, "plain": Counter()}
    for r in range(R):
        row = []
        for c in range(C):
            cell = grid[r][c]
            m = merged(cell)
            if m is None:
                row.append(tok[r][c])
                st["plain"][tok[r][c]] += 1
                continue
            cls, deg = m
            st["hist"][cls] += 1
            st["own_tr"][tok[r][c]] += 1
            if cell.mixed:
                st["mixed"] += 1
            if cell.approx:
                st["approx"][cell.approx] += 1
                st["pair_approx"][(pair_of(cls), cell.approx)] += 1
            row.append(cls if deg == 0 else f"{cls}@{deg}")
        st["tokens"].append(row)
    return st


def side_profile(token: str):
    """Per-side tiers (T, R, B, L; each a pair of halves) of a token: a plain tier or a rotated piece."""
    code, _, deg = token.partition("@")
    if len(code) == 1:
        return [(code, code)] * 4
    r = (int(deg or 0) // 90) % 4
    out = [None] * 4
    for k, halves in enumerate(HALVES[code[2]]):
        out[(k + r) % 4] = tuple(code[0] if h == "b" else code[1] for h in halves)
    return out


def edge_check(tok: list[list[str]], st: dict) -> tuple[int, Counter]:
    """Every shared edge: half j of one side must carry the tier of half 1 - j of the other.

    Categories of a mismatch (first match): frame (cut on a frame cell, coded plain); S-L (must be 0 in
    v2: S-L is a transition pair); S-other (S against D, M or W: must be 0); approx (a v4
    approximation); junction (three-tier corner); cap; other (must be 0).
    """
    R, C = len(tok), len(tok[0])
    grid, tokens = st["grid"], st["tokens"]
    n_edges, bad = 0, Counter()
    for r in range(R):
        for c in range(C):
            for k, (dx, dy) in ((1, SIDE_OFF[1]), (2, SIDE_OFF[2])):
                rr, cc = r + dy, c + dx
                if not (0 <= rr < R and 0 <= cc < C):
                    continue
                n_edges += 1
                a = side_profile(tokens[r][c])[k]
                b = side_profile(tokens[rr][cc])[(k + 2) % 4]
                if a[0] == b[1] and a[1] == b[0]:
                    continue
                x, y = grid[r][c], grid[rr][cc]
                pair = {tok[r][c], tok[rr][cc]}
                if is_frame(r, c, R, C) or is_frame(rr, cc, R, C):
                    bad["frame"] += 1
                elif "S" in pair:
                    bad["S-L" if pair == {"S", "L"} else "S-other"] += 1
                elif x.approx or y.approx:
                    bad["approx"] += 1
                elif x.mixed or y.mixed:
                    bad["junction"] += 1
                elif x.pattern == "p" or y.pattern == "p":
                    bad["cap"] += 1
                else:
                    bad["other"] += 1
    return n_edges, bad


def pair_edges(tok: list[list[str]]) -> Counter:
    """Shared 4-neighbour edges between different tiers, by unordered pair (frame included)."""
    R, C = len(tok), len(tok[0])
    out = Counter()
    for r in range(R):
        for c in range(C):
            for dx, dy in ((1, 0), (0, 1)):
                rr, cc = r + dy, c + dx
                if rr < R and cc < C and tok[rr][cc] != tok[r][c]:
                    a, b = tok[r][c], tok[rr][cc]
                    out["".join(sorted((a, b), key=ORDER.index))] += 1
    return out


# ------------------------------------------------------------------ stage: classify and budgets


def load_specs() -> tuple[dict, dict]:
    specs = {}
    for name in ("classes-v4.json", "classes-ink.json"):
        specs[name] = json.loads((CLS_DIR / name).read_text(encoding="utf-8"))["classes"]
    return specs["classes-v4.json"], specs["classes-ink.json"]


def stage_classify(tiles: dict[str, list[list[str]]]) -> dict[str, dict]:
    t0 = time.time()
    for n in IMAGES:
        bad = s_contacts(tiles[n])
        if bad:
            raise SystemExit(f"{n}: S touches D, M or W (interior, 8-neighbourhood): {dict(bad)}")
    st = {n: classify_image(tiles[n]) for n in IMAGES}
    log("1. tiers per image (input) and transition cells")
    for n in IMAGES:
        cnt = Counter(t for row in tiles[n] for t in row)
        log(f"   {n} {IMAGE_NAME[n]:6s} tiles D {cnt['D']:3d} M {cnt['M']:3d} W {cnt['W']:3d} "
            f"L {cnt['L']:3d} S {cnt['S']:3d}   transitions {sum(st[n]['hist'].values()):3d} "
            f"(own D/S/M/W/L {st[n]['own_tr']['D']}/{st[n]['own_tr']['S']}/{st[n]['own_tr']['M']}/"
            f"{st[n]['own_tr']['W']}/{st[n]['own_tr']['L']})")
    log(f"   classify {time.time() - t0:.1f} s")
    # Write the class maps (text, scene-file layout).
    out = WORK / "quantized-codes.txt"
    lines = ["# Merged class maps, experiment 011 (A hare, B owl, C swan). Transition cells: class plus @deg.", ""]
    for n in IMAGES:
        lines += [f"# {n}"] + [" ".join(row) for row in st[n]["tokens"]] + [""]
    out.write_text("\n".join(lines), encoding="utf-8")
    log(f"   wrote {out}")
    return st


def s_contacts(tok, interior_only: bool = True) -> Counter:
    """8-neighbour contacts between S and D, M or W, each unordered pair once (forbidden in v2)."""
    R, C = len(tok), len(tok[0])
    out = Counter()
    for r in range(R):
        for c in range(C):
            for rr, cc in nb8(R, C, r, c):
                a, b = tok[r][c], tok[rr][cc]
                other = b if a == "S" else a if b == "S" else None
                if other is None or other not in FORBIDDEN_S:
                    continue
                if interior_only and (is_frame(r, c, R, C) or is_frame(rr, cc, R, C)):
                    continue
                out[tuple(sorted((a, b), key=ORDER.index))] += 1
    return Counter({k: v // 2 for k, v in out.items() if v // 2})


def stage_budgets(tiles, st) -> dict:
    log("2. budgets (per class: max over images, own counts, surplus = max - own)")
    classes = sorted({c for n in IMAGES for c in st[n]["hist"]}, key=lambda c: (ORDER.index(c[0]), ORDER.index(c[1]) if len(c) == 3 else 0, c[2:]))
    T = {c: max(st[n]["hist"][c] for n in IMAGES) for c in classes}
    sur = {n: {c: T[c] - st[n]["hist"][c] for c in classes} for n in IMAGES}
    lines = ["# Boundary budgets, experiment 011 (A hare, B owl, C swan). max = per-class max over images;",
             "# surplus = max - own (cells that must be added in near roles). W is a tier of its own here.", ""]
    hdr = f"{'class':7s}{'pair':>5s} " + "".join(f"{n + ' ' + IMAGE_NAME[n]:>11s}" for n in IMAGES) + f"{'max':>6s}" + "".join(
        f"{'sur_' + n:>8s}" for n in IMAGES)
    lines.append(hdr)
    log("   " + hdr)
    for pair in PAIRS:
        block = [c for c in classes if pair_of(c) == pair]
        if not block:
            continue
        tot = [0, 0, 0]
        for c in block:
            own = [st[n]["hist"][c] for n in IMAGES]
            row = f"{c:7s}{pair:>5s} " + "".join(f"{x:11d}" for x in own) + f"{T[c]:6d}" + "".join(
                f"{sur[n][c]:8d}" for n in IMAGES)
            lines.append(row)
            log("   " + row)
        pmax = sum(T[c] for c in block)
        for k, n in enumerate(IMAGES):
            tot[k] = sum(st[n]["hist"][c] for c in block)
        row = f"{'total':7s}{pair:>5s} " + "".join(f"{x:11d}" for x in tot) + f"{pmax:6d}" + "".join(
            f"{pmax - x:8d}" for x in tot)
        lines.append(row)
        log("   " + row)
    total_sur = {n: sum(sur[n].values()) for n in IMAGES}
    own_all = {n: sum(st[n]["hist"].values()) for n in IMAGES}
    line = (f"Transition cells per image: " + ", ".join(f"{n} {own_all[n]}" for n in IMAGES) +
            "; surplus (max minus own, all classes): " + ", ".join(f"{n} {total_sur[n]}" for n in IMAGES))
    log("   " + line)
    lines.append(line)
    approx = {n: dict(st[n]["approx"]) for n in IMAGES}
    log("   approximations: " + "; ".join(f"{n} {approx[n]}" for n in IMAGES))
    log("   cells with a three-tier junction (two lighter tiers among 8 neighbours): " +
        ", ".join(f"{n} {st[n]['mixed']}" for n in IMAGES))
    # Pair edges (4-neighbour), with W reported separately and as M (budget convention).
    log("   shared 4-neighbour edges (different tiers, frame included):")
    pe = {n: pair_edges(tiles[n]) for n in IMAGES}
    keys = sorted({k for n in IMAGES for k in pe[n]})
    for k in keys:
        log(f"     {k:6s} " + "  ".join(f"{n} {pe[n][k]:3d}" for n in IMAGES))
    wm = {n: pe[n]["MW"] for n in IMAGES}
    log(f"   W-M contacts (MW edges): " + ", ".join(f"{n} {wm[n]}" for n in IMAGES))
    sc = {n: s_contacts(tiles[n], interior_only=False) for n in IMAGES}
    log("   S contacts: S-L edges (transitions) " + ", ".join(f"{n} {pe[n]['SL']}" for n in IMAGES) +
        "; S-D/S-M/S-W 8-neighbour contacts (must be 0) " + ", ".join(f"{n} {sum(sc[n].values())}" for n in IMAGES))
    # verify_edges
    log("   verify_edges (shared edges whose halves disagree, from the rotated pieces' profiles):")
    totals = Counter()
    for n in IMAGES:
        n_edges, bad = edge_check(tiles[n], st[n])
        totals.update(bad)
        log(f"     {n} {IMAGE_NAME[n]:6s} shared edges {n_edges}  " + "  ".join(f"{k} {v}" for k, v in sorted(bad.items())))
    log("     total: " + "  ".join(f"{k} {v}" for k, v in sorted(totals.items())))
    (WORK / "boundary-budgets.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"T": T, "sur": sur, "classes": classes, "pe": pe, "approx": approx}


# ------------------------------------------------------------------ stage: equalize (005 v5b logic)
# Simulated annealing over tier cells, ported from equalize_budgets_v5b.py to five tiers (D S M W L).
# Moves are reverse pairs (X->Y with Y->X), so tier totals stay per image. Rules: only cells within
# one cell (8-neighbourhood) of the original boundary, never the frame; the only S move is S-L, and
# eq_s_legal refuses any move that puts S next to D, M or W (8-neighbourhood); a changed cell has at
# least two orthogonal neighbours of its new tier; no new rare cell (at most one same-tier orthogonal
# neighbour); no new bite (an M or W cell with three D neighbours). Cost: 1 per cell for a pair
# with L (S-L included), 2 otherwise (005: D-L and M-L cost 1, D-M cost 2).

EQ_MAX_FLIPS = 40
EQ_LAM = 2.0
EQ_TARGET = 10
EQ_TARGET_W = 5.0
EQ_T_HI, EQ_T_LO = 0.6, 0.01
TIER_PAIRS = [(a, b) for i, a in enumerate(ORDER) for b in ORDER[i + 1:]
              if "S" not in (a, b) or (a, b) == ("S", "L")]


def nb4(R: int, C: int, r: int, c: int):
    for dx, dy in SIDE_OFF:
        rr, cc = r + dy, c + dx
        if 0 <= rr < R and 0 <= cc < C:
            yield rr, cc


def nb8(R: int, C: int, r: int, c: int):
    for dx, dy in SIDE_OFF + CORNER_OFF:
        rr, cc = r + dy, c + dx
        if 0 <= rr < R and 0 <= cc < C:
            yield rr, cc


def eq_band(tok0: list[list[str]]) -> list[list[bool]]:
    """Cells that may change: interior cells within one cell (8-neighbourhood) of a tier change. S is a
    tier in v2, so S-L boundary cells are in the band; eq_s_legal rejects any move that makes an S-D,
    S-M or S-W contact."""
    R, C = len(tok0), len(tok0[0])
    band = [[False] * C for _ in range(R)]
    for r in range(R):
        for c in range(C):
            if is_frame(r, c, R, C):
                continue
            if any(tok0[rr][cc] != tok0[r][c] for rr, cc in nb8(R, C, r, c)):
                band[r][c] = True
    out = [row[:] for row in band]
    for r in range(R):
        for c in range(C):
            if band[r][c]:
                for rr, cc in nb8(R, C, r, c):
                    if not is_frame(rr, cc, R, C):
                        out[rr][cc] = True
    return out


def eq_masks(tok, band):
    R, C = len(tok), len(tok[0])
    has = {t: [[False] * C for _ in range(R)] for t in TILES}
    for r in range(R):
        for c in range(C):
            for rr, cc in nb4(R, C, r, c):
                has[tok[rr][cc]][r][c] = True
    masks = {}
    for a, b in TIER_PAIRS:
        for old, new in ((a, b), (b, a)):
            cost2 = "L" not in (a, b)
            m = []
            for r in range(R):
                for c in range(C):
                    if band[r][c] and tok[r][c] == old and has[new][r][c] and (not cost2 or has[old][r][c]):
                        m.append((r, c))
            masks[(old, new)] = m
    return masks


def eq_propose(rnd: random.Random, tok, band):
    masks = eq_masks(tok, band)
    kinds = [k for k in masks if masks[k] and masks[(k[1], k[0])]]
    if not kinds:
        return None
    old, new = kinds[rnd.randrange(len(kinds))]
    a = masks[(old, new)][rnd.randrange(len(masks[(old, new)]))]
    back = masks[(new, old)]
    near = [p for p in back if max(abs(p[0] - a[0]), abs(p[1] - a[1])) <= 4]
    pool = near if (near and rnd.random() < 0.7) else back
    b = pool[rnd.randrange(len(pool))]
    return [(a[0], a[1], new), (b[0], b[1], old)]


def eq_rare(tok) -> set:
    R, C = len(tok), len(tok[0])
    out = set()
    for r in range(R):
        for c in range(C):
            if is_frame(r, c, R, C) or tok[r][c] == "S":
                continue
            same = sum(1 for rr, cc in nb4(R, C, r, c) if tok[rr][cc] == tok[r][c])
            if same <= 1:
                out.add((r, c))
    return out


def eq_bite(tok) -> set:
    R, C = len(tok), len(tok[0])
    out = set()
    for r in range(R):
        for c in range(C):
            if is_frame(r, c, R, C) or tok[r][c] not in ("M", "W"):
                continue
            if sum(1 for rr, cc in nb4(R, C, r, c) if tok[rr][cc] == "D") >= 3:
                out.add((r, c))
    return out


def eq_s_legal(tok, cells) -> bool:
    """No S cell may touch D, M or W (8-neighbourhood) after the move on these cells."""
    R, C = len(tok), len(tok[0])
    for r, c in cells:
        a = tok[r][c]
        for rr, cc in nb8(R, C, r, c):
            b = tok[rr][cc]
            if (a == "S" and b in FORBIDDEN_S) or (b == "S" and a in FORBIDDEN_S):
                return False
    return True


def eq_cost(tok, tok0) -> int:
    R, C = len(tok), len(tok[0])
    total = 0
    for r in range(R):
        for c in range(C):
            if tok[r][c] != tok0[r][c]:
                total += 1 if "L" in (tok[r][c], tok0[r][c]) else 2
    return total


def eq_changed(tok, tok0) -> int:
    return sum(1 for row, row0 in zip(tok, tok0) for a, b in zip(row, row0) if a != b)


def eq_score(hists: list, costs: list) -> float:
    classes = set().union(*hists)
    mx = {c: max(h.get(c, 0) for h in hists) for c in classes}
    spread = sum(mx[c] - min(h.get(c, 0) for h in hists) for c in classes)
    per = [sum(mx[c] - h.get(c, 0) for c in classes) for h in hists]
    over = sum(max(0, p - EQ_TARGET) for p in per)
    return spread + EQ_LAM * sum(costs) + EQ_TARGET_W * over


def eq_surplus(hists: list) -> list:
    classes = set().union(*hists)
    mx = {c: max(h.get(c, 0) for h in hists) for c in classes}
    return [sum(mx[c] - h.get(c, 0) for c in classes) for h in hists]


def eq_anneal(seed: int, iters: int, tok0: list, bands: list, log) -> tuple[float, list]:
    rnd = random.Random(seed)
    toks = [[row[:] for row in t] for t in tok0]
    hists = [classify_image(t)["hist"] for t in toks]
    rares = [eq_rare(t) for t in toks]
    bites = [eq_bite(t) for t in toks]
    costs = [0, 0, 0]
    cur = eq_score(hists, costs)
    best = (cur, [[row[:] for row in t] for t in toks])
    accepted = 0
    for it in range(iters):
        temp = EQ_T_HI * (EQ_T_LO / EQ_T_HI) ** (it / max(1, iters - 1))
        k = rnd.randrange(3)
        mv = eq_propose(rnd, toks[k], bands[k])
        if mv is None:
            continue
        t = toks[k]
        saved = [(r, c, t[r][c]) for r, c, _ in mv]
        for r, c, new in mv:
            t[r][c] = new
        ok = all(sum(1 for rr, cc in nb4(len(t), len(t[0]), r, c) if t[rr][cc] == new) >= 2 for r, c, new in mv)
        ok = ok and eq_s_legal(t, [(r, c) for r, c, _ in mv])
        rare_a = bite_a = None
        if ok:
            rare_a = eq_rare(t)
            ok = not (rare_a - rares[k])
        if ok:
            bite_a = eq_bite(t)
            ok = not (bite_a - bites[k])
        if ok and eq_changed(t, tok0[k]) > EQ_MAX_FLIPS:
            ok = False
        if not ok:
            for r, c, old in saved:
                t[r][c] = old
            continue
        hs = hists.copy()
        hs[k] = classify_image(t)["hist"]
        cs = costs.copy()
        cs[k] = eq_cost(t, tok0[k])
        new_score = eq_score(hs, cs)
        if new_score <= cur or rnd.random() < math.exp(-(new_score - cur) / temp):
            hists, costs, cur = hs, cs, new_score
            rares[k], bites[k] = rare_a, bite_a
            accepted += 1
            if cur < best[0]:
                best = (cur, [[row[:] for row in x] for x in toks])
        else:
            for r, c, old in saved:
                t[r][c] = old
        if (it + 1) % max(1, iters // 4) == 0:
            log(f"    seed {seed} it {it + 1:6d} accepted {accepted:5d} surplus {eq_surplus(hists)} "
                f"cost {costs} score {cur:.2f} best {best[0]:.2f}")
    return best


def stage_equalize(src: dict, iters: int, seeds: list[int]) -> dict:
    C, R = len(src["A"][0]), len(src["A"])
    tok0 = [src[n] for n in IMAGES]
    bands = [eq_band(t) for t in tok0]
    st0 = {n: classify_image(src[n]) for n in IMAGES}
    before = eq_surplus([st0[n]["hist"] for n in IMAGES])
    log("0. equalize (005 v5b logic; v2: five tiers, S-L moves only, S-D/S-M/S-W never created)")
    log(f"   cells allowed to change per image: {[sum(map(sum, b)) for b in bands]}")
    log(f"   surplus before: " + ", ".join(f"{n} {before[k]}" for k, n in enumerate(IMAGES)) + f"   total {sum(before)}")
    results = []
    for seed in seeds:
        t0 = time.time()
        sc, tb = eq_anneal(seed, iters, tok0, bands, log)
        results.append((sc, seed, tb))
        log(f"   seed {seed}: best score {sc:.2f} ({time.time() - t0:.0f} s)")
    sc, seed, tb = min(results, key=lambda x: x[0])
    out = {n: tb[k] for k, n in enumerate(IMAGES)}
    # checks
    for k, n in enumerate(IMAGES):
        h0 = Counter(x for row in tok0[k] for x in row)
        h1 = Counter(x for row in out[n] for x in row)
        assert h0 == h1, f"{n}: tier totals changed {h0} -> {h1}"
        for r in range(R):
            for c in range(C):
                if out[n][r][c] != tok0[k][r][c]:
                    assert bands[k][r][c], f"{n}: change outside the band at {(r, c)}"
                    assert not is_frame(r, c, R, C), f"{n}: frame cell changed"
    after_st = {n: classify_image(out[n]) for n in IMAGES}
    after = eq_surplus([after_st[n]["hist"] for n in IMAGES])
    changed = {n: [(r, c, src[n][r][c], out[n][r][c]) for r in range(R) for c in range(C) if out[n][r][c] != src[n][r][c]]
               for n in IMAGES}
    log(f"   chosen seed {seed}, score {sc:.2f}")
    log(f"   surplus after:  " + ", ".join(f"{n} {after[k]}" for k, n in enumerate(IMAGES)) + f"   total {sum(after)}")
    log("   changed cells per image: " + ", ".join(f"{n} {len(changed[n])}" for n in IMAGES) +
        " (tier totals unchanged, frame unchanged, changes inside the band)")
    for n in IMAGES:
        assert not s_contacts(out[n], interior_only=False), f"{n}: forbidden S contact after equalize"
    lines = ["# Equalized tiers, experiment 011 (A hare, B owl, C swan). Changed cells vs tiers-*.txt: (row, col) old->new.", ""]
    for n in IMAGES:
        (WORK / f"tiers-eq-{n}.txt").write_text("\n".join(" ".join(row) for row in out[n]) + "\n", encoding="utf-8")
        ch = ", ".join(f"({r},{c}) {a}->{b}" for r, c, a, b in changed[n]) or "-"
        lines += [f"# {n} ({len(changed[n])} changed): {ch}"]
    lines += ["", f"surplus before {before} after {after} (A, B, C)"]
    (WORK / "equalize-report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"   wrote tiers-eq-A/B/C.txt and equalize-report.txt")
    return out




def ring8(x: int, y: int, C: int, R: int):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if (dx, dy) != (0, 0) and 0 <= x + dx < C and 0 <= y + dy < R:
                yield x + dx, y + dy


def image_roles(tok, st, C: int, R: int) -> dict:
    """Cells of one image by role: frame plain, transition cells (S-L included), near/far plain."""
    boundary = {(x, y) for y in range(R) for x in range(C)
                if not is_frame(y, x, R, C) and len(st["tokens"][y][x].partition("@")[0]) == 3}
    out = {"frame": Counter(), "near": [], "far": [], "edges": Counter(), "boundary": boundary}
    for y in range(R):
        for x in range(C):
            t = tok[y][x]
            if is_frame(y, x, R, C):
                if (x, y) in boundary:
                    raise SystemExit(f"frame cell ({x},{y}) is a transition")
                out["frame"][t] += 1
            elif (x, y) in boundary:
                out["edges"][st["tokens"][y][x].partition("@")[0]] += 1
            elif any(p in boundary for p in ring8(x, y, C, R)):
                out["near"].append((x, y))
            else:
                out["far"].append((x, y))
    out["near_n"] = Counter(tok[y][x] for x, y in out["near"])
    out["far_n"] = Counter(tok[y][x] for x, y in out["far"])
    return out


def tier_caps(far, X, rnd, C, R):
    caps = Counter()
    for _ in range(N_RESTARTS):
        order = far[:]
        rnd.shuffle(order)
        chosen, blocked = [], set()
        for p in order:
            if p in blocked:
                continue
            chosen.append(p)
            blocked.add(p)
            blocked.update(ring8(*p, C, R))
        cnt = Counter(X(*p) for p in chosen)
        for t in ORDER:
            caps[t] = max(caps[t], cnt[t])
    return caps


def max_flow(cap: dict, s: str, t: str) -> int:
    flow = 0
    while True:
        parent = {s: None}
        q = deque([s])
        while q and t not in parent:
            u = q.popleft()
            for v, c in cap.get(u, {}).items():
                if c > 0 and v not in parent:
                    parent[v] = u
                    q.append(v)
        if t not in parent:
            return flow
        f, v = float("inf"), t
        while parent[v] is not None:
            f = min(f, cap[parent[v]][v])
            v = parent[v]
        v = t
        while parent[v] is not None:
            u = parent[v]
            cap[u][v] -= f
            cap.setdefault(v, {}).setdefault(u, 0)
            cap[v][u] += f
            v = u
        flow += f


def pair_flow_ok(P: dict, s: dict) -> bool:
    """Can every pair's surplus P[pair] be split between its two tiers so tier t gets s[t]?"""
    if sum(P.values()) != sum(s.values()) or any(v < 0 for v in s.values()):
        return False
    cap: dict = {"src": {}}
    for pair, v in P.items():
        cap["src"][("p", pair)] = v
        cap[("p", pair)] = {("t", t): 10**9 for t in pair}
    for t, v in s.items():
        cap[("t", t)] = {"snk": v}
    flow = max_flow(cap, "src", "snk")
    return flow == sum(P.values())


def fmt(d: dict) -> str:
    return "/".join(str(d.get(t, 0)) for t in ORDER)


# ------------------------------------------------------------------ stage: roles (v3 placement policy)
# Histogram target: v2's, unchanged (transition counts T per class, max over images; plain targets Pt from
# the same search, with the same tier-flow test; the search now also needs the host split below to exist).
# v3 changes only where surplus transition pieces may sit, by class pair (FINDINGS 14, 20, 23):
#   SL      S cells on the S side of an S-L boundary. A plain S cell with a transition on side k takes the
#           piece whose L side is k (classify's rule for a boundary S cell: rot = k). Corners use the sides
#           {k, k+1}; the convex LSc piece uses its diagonal L corner. The ragged edge thickens outward.
#   DL, DM  D cells at Chebyshev distance >= FUR_MIN_DIST from every transition and FRAME_MIN from the edge
#           ("fur" marks), free rotation
#           (@*). Fallback: M cells at the same distance, then L.
#   ML      M cells at the same distance, lower part of the picture preferred, free rotation. L only when the
#           fixed target leaves no other host; then an L cell next to the M-L boundary (flagged in the log).
#   MW, WL  W cells, far first, then ring. MW falls back to M when the fixed target keeps every W cell plain.

FUR_MIN_DIST = 2                       # Chebyshev distance from every transition cell for interior marks
FRAME_MIN = 2                          # ... and from the picture edge (frame cells), in cells
HOST_COST = {                          # tiers that may host a surplus pair, with a cost (0 = the policy)
    "SL": {"S": 0, "L": 4},
    "DL": {"D": 0, "M": 1, "L": 4},
    "DM": {"D": 0, "M": 1, "L": 4},
    "ML": {"M": 0, "L": 3},
    "MW": {"W": 0, "M": 2},
    "WL": {"W": 0, "L": 3},
    "DW": {"D": 0, "W": 1},
}
SE_ROLE = {"SLs": "se_sls", "SLc": "se_slc", "LSc": "se_lsc"}   # S-edge roles, one class each
SE_CLASS = {v: k for k, v in SE_ROLE.items()}


def transition_cells(st, R: int, C: int) -> set:
    return {(x, y) for y in range(R) for x in range(C)
            if not is_frame(y, x, R, C) and len(st["tokens"][y][x].partition("@")[0]) == 3}


def cheb_dist(trans: set, C: int, R: int) -> dict:
    """Chebyshev distance to the nearest transition cell, for every cell (8-neighbour BFS)."""
    dist = {p: 0 for p in trans}
    q = deque(trans)
    while q:
        p = q.popleft()
        for n8 in ring8(p[0], p[1], C, R):
            if n8 not in dist:
                dist[n8] = dist[p] + 1
                q.append(n8)
    return dist


def s_options(B: set, Q: list) -> dict:
    """Best (score, rotation in degrees) per SL class for a plain S cell.

    B: sides k (0 T, 1 R, 2 B, 3 L) whose neighbour is a transition; Q: corners q (0 TL .. 3 BL) whose
    diagonal neighbour is a transition. Score 2 = every L side meets a boundary, 0 = partly, < 0 = none.
    """
    out = {}
    ks = sorted(B)
    out["SLs"] = (2, 90 * ks[0]) if ks else (-1, 0)
    best = None
    for k in range(4):
        m = (k in B) + (((k + 1) % 4) in B)
        score = {2: 4, 1: 1, 0: -2}[m]
        if best is None or score > best[0]:
            best = (score, 90 * k)
    out["SLc"] = best
    bestL = (-2, 0)
    for q in Q:                                   # classify's i-rule: rot = q, merged to LSc at (q-3) % 4
        hits = (q in B) + (((q + 3) % 4) in B)
        score = 2 - 2 * hits
        if score > bestL[0]:
            bestL = (score, 90 * ((q - 3) % 4))
    out["LSc"] = bestL
    return out


def s_cat(score: int) -> str:
    return "S-edge" if score >= 2 else ("S-edge partial" if score >= 0 else "S-off-edge")


def split_pairs(P: dict, s: dict):
    """Split each pair's surplus over its allowed host tiers so that tier t receives exactly s[t] pieces,
    at the least total HOST_COST. Returns (cost, {pair: {tier: n}}) or None."""
    pairs = [p for p in PAIRS if P.get(p, 0)]
    best = {"cost": None, "alloc": None}

    def splits(n: int, k: int):
        if k == 1:
            yield (n,)
            return
        for i in range(n + 1):
            for rest in splits(n - i, k - 1):
                yield (i,) + rest

    def rec(i: int, used: dict, cost: int, alloc: dict) -> None:
        if best["cost"] is not None and cost >= best["cost"]:
            return
        if i == len(pairs):
            if all(used.get(t, 0) == s.get(t, 0) for t in ORDER):
                best["cost"], best["alloc"] = cost, {p: dict(v) for p, v in alloc.items()}
            return
        p = pairs[i]
        hosts = list(HOST_COST[p])
        for split in splits(P[p], len(hosts)):
            u = dict(used)
            ok = True
            for t, k in zip(hosts, split):
                u[t] = u.get(t, 0) + k
                if u[t] > s.get(t, 0):
                    ok = False
                    break
            if not ok:
                continue
            alloc[p] = dict(zip(hosts, split))
            rec(i + 1, u, cost + sum(HOST_COST[p][t] * k for t, k in zip(hosts, split)), alloc)
            del alloc[p]

    rec(0, {}, 0, {})
    return None if best["alloc"] is None else (best["cost"], best["alloc"])


def place_image(n: str, tok: list, st: dict, sur_n: dict, alloc_n: dict, C: int, R: int, rnd: random.Random) -> dict:
    """Host cells of one image: {(x, y): (role token, category, pair)}. Plain and edge cells are not listed."""
    trans = transition_cells(st, R, C)
    dist = cheb_dist(trans, C, R)
    out: dict = {}

    def inside(p) -> bool:
        return 0 <= p[0] < C and 0 <= p[1] < R

    def tr(p) -> bool:
        return inside(p) and p in trans

    def far(p) -> bool:                                  # interior: away from transitions and from the edge
        return (dist.get(p, 99) >= FUR_MIN_DIST and FRAME_MIN <= p[0] <= C - 1 - FRAME_MIN
                and FRAME_MIN <= p[1] <= R - 1 - FRAME_MIN)

    # S hosts (SL pair): every surplus SL piece, most constrained class first.
    s_cells = [(x, y) for y in range(R) for x in range(C)
               if not is_frame(y, x, R, C) and tok[y][x] == "S" and (x, y) not in trans]
    opts = {}
    for p in s_cells:
        B = {k for k, (dx, dy) in enumerate(SIDE_OFF) if tr((p[0] + dx, p[1] + dy))}
        Q = [q for q, (dx, dy) in enumerate(CORNER_OFF) if tr((p[0] + dx, p[1] + dy))]
        opts[p] = s_options(B, Q)
    tie = {p: rnd.random() for p in s_cells}
    chosen_s: set = set()
    rem = {c: sur_n.get(c, 0) for c in ("LSc", "SLc", "SLs")}
    while sum(rem.values()):                       # best (cell, class) first: score, then fewest chosen neighbours
        best_key, best_pick = None, None
        for p in s_cells:
            if p in out:
                continue
            pen = sum(1 for dx, dy in SIDE_OFF if (p[0] + dx, p[1] + dy) in chosen_s)
            for cls, k in rem.items():
                if k:
                    key = (-opts[p][cls][0], pen, tie[p], cls)
                    if best_key is None or key < best_key:
                        best_key, best_pick = key, (p, cls)
        if best_pick is None:
            raise SystemExit(f"{IMAGE_NAME[n]}: no plain S cell left for the S-edge pieces")
        p, cls = best_pick
        score, deg = opts[p][cls]
        out[p] = (f"{SE_ROLE[cls]}@{deg}", s_cat(score), "SL")
        chosen_s.add(p)
        rem[cls] -= 1
    if len(chosen_s) != alloc_n.get("SL", {}).get("S", 0):
        raise SystemExit(f"{IMAGE_NAME[n]}: S hosts {len(chosen_s)} != SL pieces hosted at S")

    # Other hosts (D, M, W, L): interior marks with free rotation, spaced by one cell.
    blocked: set = set()

    def pick(pool: list, k: int, tier: str) -> list:
        """k cells in pool order; one-cell spacing from other marks first, relaxed only if the pool runs out."""
        got: list = []
        for relaxed in (False, True):
            for p in pool:
                if len(got) == k:
                    break
                if p in got or p in out or (not relaxed and p in blocked):
                    continue
                got.append(p)
                blocked.add(p)
                blocked.update(ring8(p[0], p[1], C, R))
            if len(got) == k:
                break
        if len(got) < k:
            raise SystemExit(f"{IMAGE_NAME[n]}: only {len(got)} of {k} {tier} hosts available")
        if relaxed:
            log(f"   {n} {IMAGE_NAME[n]:6s} {tier}: spacing relaxed for {k} hosts (pool too small)")
        return got

    by_tile: dict = {t: [] for t in TILES}
    for y in range(R):
        for x in range(C):
            if not is_frame(y, x, R, C) and (x, y) not in trans:
                by_tile[tok[y][x]].append((x, y))
    m_key = {p: rnd.random() ** (1.0 / (1.0 + 2.0 * p[1] / max(1, R - 1))) for p in by_tile["M"]}
    d_pool = [p for p in by_tile["D"] if far(p)]
    rnd.shuffle(d_pool)
    pools = {
        "D": d_pool,
        "M": sorted((p for p in by_tile["M"] if far(p)), key=lambda p: -m_key[p]),
        "W": sorted(by_tile["W"], key=lambda p: (not far(p), rnd.random())),
    }
    def l_pool(pair: str) -> list:                 # L cells next to the pair's other tile, if any
        other = next(t for t in pair if t != "L")
        ot = {p for p in trans if tok[p[1]][p[0]] == other}
        return sorted((p for p in by_tile["L"] if dist.get(p, 99) == 1),
                      key=lambda p: (not any((p[0] + dx, p[1] + dy) in ot for dx, dy in SIDE_OFF), rnd.random()))

    for tier in ("D", "M", "W", "L"):
        labels = [pair for pair, split in alloc_n.items() for _ in range(split.get(tier, 0))]
        if not labels:
            continue
        rnd.shuffle(labels)
        if tier == "L":
            picked = []
            for pair in dict.fromkeys(labels):
                k = labels.count(pair)
                picked += [(p, pair) for p in pick(l_pool(pair), k, tier)]
            pairs_of = dict(picked)
        else:
            pairs_of = dict(zip(pick(pools[tier], len(labels), tier), labels))
        for p, pair in pairs_of.items():
            if tier == "D":
                cat = "D-interior"
            elif tier == "M":
                cat = "M-interior" if pair == "ML" else "M-fallback"
            elif tier == "W":
                cat = "W-far" if far(p) else "W-ring"
            else:
                cat = "L-edge (forced)"
            out[p] = (f"{tier.lower()}_fur_{pair.lower()}@*", cat, pair)
    return out


def stage_roles(tiles, st, bud) -> None:
    rnd = random.Random(SEED)
    C, R = len(tiles["A"][0]), len(tiles["A"])
    CELLS = R * C
    T, sur_k = bud["T"], bud["sur"]
    codes = bud["classes"]
    info = {n: image_roles(tiles[n], st[n], C, R) for n in IMAGES}
    X = {n: (lambda n: (lambda x, y: tiles[n][y][x]))(n) for n in IMAGES}
    total_trans = sum(T.values())
    plain_total = CELLS - total_trans
    frame_k = {n: {t: info[n]["frame"][t] for t in ORDER} for n in IMAGES}
    F = {n: {t: info[n]["frame"][t] + info[n]["near_n"][t] + info[n]["far_n"][t] for t in ORDER} for n in IMAGES}
    P_pair = {n: {p: sum(sur_k[n][c] for c in codes if pair_of(c) == p) for p in PAIRS} for n in IMAGES}
    caps = {n: tier_caps(info[n]["far"], X[n], rnd, C, R) for n in IMAGES}
    log(f"3. roles: total transitions {total_trans}, plain target total {plain_total}, tiers {ORDER}")
    for n in IMAGES:
        log(f"   {n} F (plain-capable, frame incl.) {fmt(F[n])}; frame {fmt(frame_k[n])}; "
            f"far-slot estimate {fmt(caps[n])}")
    # Plain targets: v2's search (same bounds, same tier-flow test) plus the v3 host split, which must exist.
    lo = {t: max(frame_k[n][t] for n in IMAGES) for t in ORDER}
    hi = {t: min(F[n][t] for n in IMAGES) for t in ORDER}
    last = ORDER[-1]
    feas = []
    for vals in itertools.product(*(range(lo[t], hi[t] + 1) for t in ORDER[:-1])):
        Pt = dict(zip(ORDER[:-1], vals))
        Pt[last] = plain_total - sum(vals)
        if not (lo[last] <= Pt[last] <= hi[last]):
            continue
        short = near_use = 0
        ok = True
        for n in IMAGES:
            s = {t: F[n][t] - Pt[t] for t in ORDER}
            if any(s[t] < 0 or s[t] > info[n]["near_n"][t] + info[n]["far_n"][t] for t in ORDER):
                ok = False
                break
            if not pair_flow_ok(P_pair[n], s):
                ok = False
                break
            short += sum(max(0, s[t] - caps[n][t] - info[n]["near_n"][t]) for t in ORDER)
            near_use += sum(max(0, s[t] - caps[n][t]) for t in ORDER)
        if ok:
            feas.append(((short, near_use), Pt))
    if not feas:
        raise SystemExit("no plain-target split is flow-feasible")
    feas.sort(key=lambda f: f[0])
    Pt = short_est = near_est = None
    for (short, near_use), cand in feas:
        if all(split_pairs(P_pair[n], {t: F[n][t] - cand[t] for t in ORDER}) for n in IMAGES):
            Pt, short_est, near_est = cand, short, near_use
            break
    if Pt is None:
        raise SystemExit("no plain-target split matches the host policy")
    log(f"   plain targets {fmt(Pt)}; far-slot estimate short {short_est}, near use {near_est}")

    s_n = {n: {t: F[n][t] - Pt[t] for t in ORDER} for n in IMAGES}
    alloc = {}
    for n in IMAGES:
        cost, alloc[n] = split_pairs(P_pair[n], s_n[n])
        log(f"   {n} {IMAGE_NAME[n]:6s} host tiers needed D/S/M/W/L {fmt(s_n[n])}; policy split cost {cost}")

    cell_info = {n: place_image(n, tiles[n], st[n], sur_k[n], alloc[n], C, R, rnd) for n in IMAGES}
    log("   surplus placement (pair: host category, cells):")
    place_lines = []
    for n in IMAGES:
        tally = Counter((pair, cat) for _, cat, pair in cell_info[n].values())
        for pair in PAIRS:
            parts = [f"{cat} {k}" for (pp, cat), k in sorted(tally.items()) if pp == pair]
            if parts:
                log(f"     {n} {IMAGE_NAME[n]:6s} {pair}: " + ", ".join(parts))
        for (x, y), (role_tok, cat, pair) in sorted(cell_info[n].items(), key=lambda kv: (kv[0][1], kv[0][0])):
            place_lines.append(f"{n} x={x} y={y} tile={tiles[n][y][x]} pair={pair} {cat} {role_tok}")
    (WORK / "placement.txt").write_text("\n".join(place_lines) + "\n", encoding="utf-8")

    used = {r.partition("@")[0] for n in IMAGES for r, _, _ in cell_info[n].values()}
    roles = {}
    for t in ORDER:
        low = t.lower()
        roles[f"{low}_frame"] = {"classes": [t]}
        roles[f"{low}_near"] = {"classes": [t]}
        roles[f"{low}_far"] = {"classes": [t]}
    for name in sorted(used):
        if name in SE_CLASS:
            roles[name] = {"classes": [SE_CLASS[name]]}
        else:                                       # d_fur_dl, m_fur_ml, w_fur_wl, l_fur_ml ...
            pair = name.split("_")[-1].upper()
            roles[name] = {"classes": [c for c in codes if pair_of(c) == pair and T[c] > 0]}
    for c in codes:
        roles[f"edge_{c.lower()}"] = {"classes": [c]}
    target = {c: T[c] for c in codes}
    target.update(Pt)
    assert sum(target.values()) == CELLS, (sum(target.values()), CELLS)
    spec = {"_note": "Experiment 011 v3 roles: surplus transition pieces placed by class pair (S-edge oriented, "
                     "D/M/W interior free rotation); target_counts = v2's (per-class max over images for "
                     "transitions, common plain targets). Frame and edge roles fixed.",
            "roles": roles, "target_counts": {k: target[k] for k in sorted(target)}}
    (WORK / "roles-spec.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    lines = ["# Role maps, experiment 011 v3. A hare, B owl, C swan. x_frame: frame cell; x_near / x_far: plain cell",
             "# near / away from transitions; se_<class>@deg: S-edge piece (oriented); <tier>_fur_<pair>@*: interior",
             "# piece with free rotation; edge_<class>@deg: transition (S-L included).", ""]
    for n in IMAGES:
        lines.append(f"# {n}")
        far_set = set(info[n]["far"])
        for y in range(R):
            row = []
            for x in range(C):
                cls = st[n]["tokens"][y][x]
                base = cls.partition("@")[0]
                if is_frame(y, x, R, C):
                    row.append(f"{tiles[n][y][x].lower()}_frame")
                elif len(base) == 3:
                    row.append(f"edge_{base.lower()}@{cls.partition('@')[2] or 0}")
                elif (x, y) in cell_info[n]:
                    row.append(cell_info[n][(x, y)][0])
                else:
                    default = "far" if (x, y) in far_set else "near"
                    row.append(f"{tiles[n][y][x].lower()}_{default}")
            lines.append(" ".join(row))
        lines.append("")
    (WORK / "roles.txt").write_text("\n".join(lines), encoding="utf-8")
    log(f"   wrote roles.txt, roles-spec.json, placement.txt ({len(used)} role names)")


# ------------------------------------------------------------------ stage: scenes


def stage_scenes(border: str, restarts: int, iters: int, seed: int) -> None:
    import metapuzzle.roles as R_
    from metapuzzle.board import square_board
    from metapuzzle.scene import ClassMap, SceneError, validate_scenes
    Cn = Counter

    spec = R_.parse_roles_spec(json.loads((WORK / "roles-spec.json").read_text(encoding="utf-8")))
    role_maps = R_.load_role_maps(WORK / "roles.txt")
    grids, rot_grids = R_._grids(role_maps)
    rows, cols = len(grids[0]), len(grids[0][0])
    board = square_board(cols, rows, border, "quarter")
    flat = [[r for row in g for r in row] for g in grids]
    allowed, weights = spec.allowed, spec.weights
    containers = R_._containers(board, "quarter")
    target = Cn(spec.target_counts)
    # Skeleton per map: frame containers hold that map's own frame classes; the interior holds the
    # common target minus the map's frame, so every map reaches the same whole-board histogram.
    Mk = [[Cn() for _ in containers] for _ in range(3)]
    for k in range(3):
        frame_total = Cn()
        interior = None
        for g, (name, cells) in enumerate(containers):
            if name == "interior":
                interior = g
                continue
            m = Cn(allowed[flat[k][p]][0] for p in cells)
            Mk[k][g] = m
            frame_total.update(m)
        neg = {c: target[c] - frame_total.get(c, 0) for c in target}
        if min(neg.values()) < 0:
            raise SystemExit(f"map {k}: frame holds more of a class than the target: {neg}")
        Mk[k][interior] = Cn({c: v for c, v in neg.items() if v})
        if sum(Mk[k][interior].values()) + sum(frame_total.values()) != sum(target.values()):
            raise SystemExit("skeleton does not add up")
    log(f"4. scenes: border {border}, rotation quarter, containers {[n for n, _ in containers]}")
    rnd_seed = seed
    results = []
    for r in range(max(1, restarts)):
        rng = random.Random(rnd_seed + r)
        cls0 = []
        for k in range(3):
            cls = [None] * len(flat[k])
            for g, (name, cells) in enumerate(containers):
                supply = Cn(flat[k][p] for p in cells)
                flow = R_._transport(supply, Mk[k][g], allowed)
                if flow is None:
                    raise SystemExit(f"skeleton of {name!r} does not fit map {'ABC'[k]}")
                pools = {x: [] for x in supply}
                for (x, c), f in flow.items():
                    pools[x].extend([c] * f)
                for p in cells:
                    cls[p] = pools[flat[k][p]].pop()
            cls0.append(cls)
        cls, value = R_._arrange(cls0, flat, containers, allowed, weights, board, rng, iters, 0.25, None, 1.0)
        results.append((value, r, cls))
        log(f"   restart {r}: objective {value:.2f}")
    value, r, cls = min(results, key=lambda t: t[0])
    flat_rot = [[x for line in g for x in line] for g in rot_grids]
    maps = [ClassMap([row[y * cols:(y + 1) * cols] for y in range(rows)],
                     [rot[y * cols:(y + 1) * cols] for y in range(rows)])
            for row, rot in zip(cls, flat_rot)]
    try:
        validate_scenes([board] * 3, maps)
        log(f"   validate_scenes passed (border {border})")
    except SceneError as e:
        log(f"   validate_scenes FAILED (border {border}): {e}")
        if border == "standard":
            (WORK / "scenes-standard-rejected.txt").write_text(str(e) + "\n", encoding="utf-8")
            raise SystemExit(2)
        raise
    out = WORK / "scenes.txt"
    R_.write_scene_file(maps, out)
    for k, m in enumerate(maps):
        h = m.histogram()
        assert all(h[c] == target[c] for c in target), f"map {'ABC'[k]} histogram differs"
    log(f"   best restart {r} (objective {value:.2f}); wrote {out}; all maps match target_counts")


def stage_metrics() -> None:
    out = WORK / "scene-metrics.txt"
    p = subprocess.run(["metapuzzle", "scene-metrics", str(WORK / "scenes.txt")], capture_output=True, text=True)
    out.write_text(p.stdout + p.stderr, encoding="utf-8")
    log(f"5. scene-metrics exit {p.returncode}; wrote {out}")
    log("   " + "\n   ".join((p.stdout + p.stderr).strip().splitlines()[:12]))


def check_classes_for_specs(used: set[str]) -> None:
    """Every class the roles can produce must be in the v9 specs (no local copies in v2)."""
    for name in (V9_CLASSES, V9_INK):
        spec = json.loads((HERE / name).read_text(encoding="utf-8"))
        missing = sorted(c for c in used if c not in spec["classes"])
        log(f"   {name}: used classes missing: {missing if missing else 'none'}")
        if missing:
            raise SystemExit(f"{name} lacks {missing}")


def stage_render(border: str, cell: int, iters: int, seed: int) -> None:
    for name, base in ((V9_INK, "run-ink"), (V9_CLASSES, "run-full")):
        spec_path = HERE / name
        out_name = base + RENDER_TAG
        out = OUT_DIR / out_name
        out.mkdir(parents=True, exist_ok=True)
        cmd = ["metapuzzle", "prototype", "--scenes", str(WORK / "scenes.txt"), "--classes", str(spec_path),
               "--out", str(out), "--rotation", "quarter", "--cell", str(cell), "--border", border,
               "--seed", str(seed)]
        if iters:
            cmd += ["--iters", str(iters)]
        t0 = time.time()
        p = subprocess.run(cmd, capture_output=True, text=True)
        (WORK / f"prototype-{out_name}.log").write_text(p.stdout + "\n--- stderr ---\n" + p.stderr, encoding="utf-8")
        log(f"6. prototype {out_name} ({name}): exit {p.returncode}, {time.time() - t0:.1f} s")
        for ln in (p.stdout + p.stderr).strip().splitlines()[-8:]:
            log("   " + ln)


def main() -> None:
    global EQ_LAM, SIZE_DIR, OUT_DIR, WORK, RENDER_TAG
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default="27x38", help="folder under 011-subjects holding tiers-{A,B,C}.txt")
    ap.add_argument("--out-dir", default=None,
                    help="folder for renders and pipeline-out/ (default: the input folder, intermediates in pipeline/v3/)")
    ap.add_argument("--render-tag", default="-v3", help="suffix of the render folders (run-ink<TAG>, run-full<TAG>)")
    ap.add_argument("--stages", default="equalize,classify,budgets,roles,scenes,metrics,render")
    ap.add_argument("--tiers", choices=["source", "eq"], default="eq",
                    help="tiles for the stages after equalize: source files or tiers-eq-*.txt")
    ap.add_argument("--eq-iters", type=int, default=6000)
    ap.add_argument("--eq-seeds", default="0,1,2")
    ap.add_argument("--eq-lam", type=float, default=EQ_LAM, help="weight per unit of move cost")
    ap.add_argument("--border", choices=["standard", "tray"], default="tray")
    ap.add_argument("--restarts", type=int, default=8)
    ap.add_argument("--iters", type=int, default=20000, help="scene build annealing iterations")
    ap.add_argument("--render-iters", type=int, default=300000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cell", type=int, default=21)
    args = ap.parse_args()
    EQ_LAM = args.eq_lam
    SIZE_DIR = EXP / args.in_dir
    RENDER_TAG = args.render_tag
    if args.out_dir:
        OUT_DIR = EXP / args.out_dir
        WORK = OUT_DIR / "pipeline-out"
    else:
        OUT_DIR = SIZE_DIR
    WORK.mkdir(parents=True, exist_ok=True)
    stages = args.stages.split(",")
    t_all = time.time()
    src = {n: read_tiers(SIZE_DIR / f"tiers-{n}.txt") for n in IMAGES}
    if "equalize" in stages:
        tiles = stage_equalize(src, args.eq_iters, [int(s) for s in args.eq_seeds.split(",")])
    elif args.tiers == "eq":
        tiles = {n: read_tiers(WORK / f"tiers-eq-{n}.txt") for n in IMAGES}
    else:
        tiles = src
    log(f"tiles used after equalize: {args.tiers if 'equalize' not in stages else 'eq (this run)'}")
    st = bud = None
    if any(s in stages for s in ("classify", "budgets", "roles", "render")):
        st = stage_classify(tiles)
    if any(s in stages for s in ("budgets", "roles")):
        bud = stage_budgets(tiles, st)
    if "roles" in stages:
        stage_roles(tiles, st, bud)
    if "scenes" in stages:
        stage_scenes(args.border, args.restarts, args.iters, args.seed)
    if "metrics" in stages:
        stage_metrics()
    if "render" in stages:
        # classes the scene file uses (from the roles spec: every role class that a cell can take)
        used = set(json.loads((WORK / "roles-spec.json").read_text(encoding="utf-8"))["target_counts"])
        check_classes_for_specs(used)
        stage_render(args.border, args.cell, args.render_iters, args.seed)
    log(f"done in {time.time() - t_all:.1f} s")


if __name__ == "__main__":
    main()
