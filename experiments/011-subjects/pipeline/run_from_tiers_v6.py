#!/usr/bin/env python3
"""v6 of run_from_tiers_v5.py (experiment 011, motif layer v6; copy of v5 with these changes):

  motifs   motif maps from motifs/make_motif_maps_v2.py (coverage 14%, organic clusters, per-class spacing, carrier
           halo). Each regular motif class is three variant classes (<base>_a/_b/_c, scale 0.8/1.0/1.2), dealt out
           per picture by a seeded shuffle, so the counts per variant are identical in A, B and C.
  halo     a displaced motif (moved off a host cell) must keep HALO from every tier boundary cell.
  specs    classes-v12.json and classes-ink-v12.json (gen_classes_v12.py); renders run-full-v6 and run-ink-v6;
           intermediates pipeline-out-v6/. v5 files are not touched.

Everything else is v5. The v4 notes follow.

v4 of run_from_tiers_v3.py: chip-signature sub-classes on the plain L and M tiers (experiment 011).

Everything up to roles is the v3 pipeline (classify, budgets, equalize, surplus placement), unchanged. Two changes:

  roles    plain L and M cells, frame included, that are not transitions or surplus hosts take a chip sub-class:
           Lr Lb Lo Lx (cream ground) and Mr Mb Mc (olive ground), from classes-v10.json. Each picture has its own
           low-frequency pattern (CHIP_FEATURES): a sub-class claims its equal share of the tier's plain cells
           nearest its feature (a point, a horizon line or a ring), and the plain class keeps the rest. Each
           chip role lists the whole family with a preference weight (1.0 for its own class, CHIP_OTHER_W for
           the others), so the roles solver puts the sub-classes where the pattern asks. target_counts gives
           each sub-class the same count in all three pictures (share = Pt / family size) and the plain class
           Pt minus those, so the histograms match.
  scenes   tray border only: the border rule constrains nothing, so the whole board is one container and the
           solver may put chips on the frame too. Frame D, S and W cells keep their fixed roles.

Outputs: pipeline-out-v4/ (intermediates) inside the input folder 27x38-v2/, renders run-ink-v4/ and
run-full-v4/ there. Chip classes come from pipeline/classes-v10.json and classes-ink-v10.json, written by
gen_classes_v10.py. pipeline/v3/ and the v3 renders are not touched.

Same stages as v3: equalize,classify,budgets,roles,scenes,metrics,render (see main). Stage roles also writes
chip-report.txt (own-class share and the centroid of each sub-class per picture).

Run: python3 experiments/011-subjects/pipeline/run_from_tiers_v4.py [--stages ...] [--pref-weight 0.25]
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
SIZE_DIR = EXP / "27x38-v2"                             # input tiers (--in-dir)
OUT_DIR = SIZE_DIR                                   # renders (--out-dir; default: the input folder)
RENDER_TAG = "-v6"                                   # render folder suffix (--render-tag)
IMAGES =["A", "B", "C"]                            # hare, owl, swan
IMAGE_NAME = {"A": "hare", "B": "owl", "C": "swan"}
TILES = "DMWLS"
ORDER = "DSMWL"                                      # darker first: D < S < M < W < L (v2: S mid-dark)
RANK = {t: i for i, t in enumerate(ORDER)}
PAIRS = ["DM", "DW", "DL", "MW", "ML", "WL", "SL"]
FORBIDDEN_S = frozenset("DMW")                       # S may touch L only (8-neighbourhood)
V12_CLASSES, V12_INK = "classes-v12.json", "classes-ink-v12.json"   # in pipeline/, from gen_classes_v12.py
WORK = EXP / "27x38-v2" / "pipeline-out-v6"                                   # this run's intermediates (v1 to v5 files are kept)
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


def fmt(d: dict) -> str:
    return "/".join(str(d.get(t, 0)) for t in ORDER)


# ------------------------------------------------------------------ motifs (v6)
# The motif maps are made by motifs/make_motif_maps.py, rerun here on the equalized tiles. Its functions are
# called (load, build, main); its own folder is not written: the maps go to pipeline-out-v6/.
MOTIF_PY = EXP / "motifs" / "make_motif_maps_v2.py"
VARIANT_TAGS = ("a", "b", "c")                             # scale variants of each regular motif class (gen_classes_v12)
REG_CLASS = {("s", "D"): "D_s", ("p", "D"): "D_p", ("k", "D"): "D_k", ("v", "D"): "D_v",
             ("s", "M"): "M_s", ("c", "M"): "M_c", ("l", "M"): "M_l", ("d", "M"): "M_d",
             ("u", "L"): "L_u", ("v", "L"): "L_v", ("p", "L"): "L_p", ("f", "L"): "L_f"}
HERO_CLASS = {"I": "H_I", "O": "H_O", "N": "H_N", "G": "H_G", "E": "H_E", "Y": "H_Y"}
HERO_TRANS = {"G": "DLc", "E": "MDd", "Y": "LDd"}          # hero on a transition piece: its piece class
HERO_PLAIN_TIER = {"I": "L", "O": "L", "N": "M"}           # hero on a plain cell: its tier


def mo_role(cls: str) -> str:
    """Role name of a motif or hero class (one role per class, fixed to that class)."""
    return "mo_" + cls.lower()


_MM = {}


def motif_module(tiles: dict):
    """make_motif_maps_v2.py, loaded once, reading the equalized tiles of this run (mm.load)."""
    import importlib.util
    if "mm" not in _MM:
        spec = importlib.util.spec_from_file_location("make_motif_maps_v2", MOTIF_PY)
        mm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mm)
        _MM["mm"] = mm
    mm = _MM["mm"]
    mm.HERE = WORK                                           # outputs go to pipeline-out-v6/
    mm.load = lambda p: [list(row) for row in tiles[p]]      # the equalized tiles, not 27x38-v2/tiers-*.txt
    return mm


def run_motif_maps(tiles: dict) -> dict:
    """make_motif_maps_v2.py on these tiles: {picture: {(x, y): motif code}} for every non-'.' cell."""
    mm = motif_module(tiles)
    mm.main()                                                # checks heroes; writes motif-maps-v6.txt, motif-counts-v6.txt
    out = {}
    for p in IMAGES:
        _, m, _ = mm.build(p)
        out[p] = {(x, y): m[y][x] for y in range(len(m)) for x in range(len(m[0])) if m[y][x] != "."}
    log("0b. motif maps: make_motif_maps_v2.py rerun on the equalized tiles; written to " + WORK.name + "/motif-maps-v6.txt")
    return out


def variant_labels(base: str, n: int) -> list:
    """Balanced variant labels 0, 1, 2 for n cells of one base class, shuffled with a seed fixed by the class name,
    so every picture with n cells of this class gets the same number of each variant."""
    labels = [i % len(VARIANT_TAGS) for i in range(n)]
    random.Random(f"variant:{base}").shuffle(labels)
    return labels


def special_cells(n: str, codes: dict, tok: list, st: dict, R: int, C: int) -> dict:
    """{(x, y): (class, kind)} for the motif and hero cells of one picture. kind: 'motif' (regular motif on a plain
    cell), 'plain' (hero on a plain cell), 'trans' (hero on its transition piece, class replaced, same mask)."""
    out = {}
    by_base = {}                                           # v6: regular motif cells per base class, in cell order
    for (x, y), code in sorted(codes.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if not code.isupper() and len(st["tokens"][y][x].partition("@")[0]) == 1:
            t = tok[y][x]
            cls = REG_CLASS.get((code, t))
            if cls is not None:
                by_base.setdefault(cls, []).append((x, y))
    variant_of = {}
    for cls, cells in by_base.items():
        for (x, y), lab in zip(cells, variant_labels(cls, len(cells))):
            variant_of[(x, y)] = f"{cls}_{VARIANT_TAGS[lab]}"
    for (x, y), code in sorted(codes.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        t = tok[y][x]
        base = st["tokens"][y][x].partition("@")[0]
        if code.isupper():
            if code in HERO_TRANS:
                if base != HERO_TRANS[code]:
                    raise SystemExit(f"{IMAGE_NAME[n]}: hero {code} at {(x, y)} sits on {base}, expected {HERO_TRANS[code]}")
                out[(x, y)] = (HERO_CLASS[code], "trans")
            else:
                if len(base) != 1 or t != HERO_PLAIN_TIER[code]:
                    raise SystemExit(f"{IMAGE_NAME[n]}: hero {code} at {(x, y)} is {base}, expected plain {HERO_PLAIN_TIER[code]}")
                out[(x, y)] = (HERO_CLASS[code], "plain")
        else:
            if len(base) != 1:
                raise SystemExit(f"{IMAGE_NAME[n]}: motif {code} at {(x, y)} is a transition cell ({base})")
            cls = variant_of.get((x, y))
            if cls is None:
                raise SystemExit(f"{IMAGE_NAME[n]}: no class for motif {code} on tier {t}")
            out[(x, y)] = (cls, "motif")
    return out


def displace_specials(n: str, spec_n: dict, cell_info_n: dict, tok: list, trans: set, C: int, R: int,
                      dist: list) -> list:
    """A motif or plain hero whose cell became a surplus host moves to the nearest plain cell of its tier that is
    not a host, transition, frame or motif cell. v6: a regular motif first looks for a cell that keeps HALO from
    every tier boundary cell (dist = boundary_distance of the tiles) and is one cell clear of other motifs; if none
    is left, it takes the nearest plain cell as in v5, and the move is logged as a halo breach. Mutates spec_n.
    Returns [(from, to, class, tier, halo_ok)]."""
    mm = _MM["mm"]
    moves = []
    for p in sorted(spec_n, key=lambda q: (q[1], q[0])):
        cls, kind = spec_n[p]
        if kind == "trans" or p not in cell_info_n:
            continue
        t = tok[p[1]][p[0]]
        best = {}
        for y in range(R):
            for x in range(C):
                q = (x, y)
                if q in spec_n or q in cell_info_n or q in trans or is_frame(y, x, R, C) or tok[y][x] != t:
                    continue
                near = [spec_n[a, b][0] for a, b in ((x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1))
                        if (a, b) in spec_n]
                clear = not any(max(abs(x - a), abs(y - b)) <= 1 for a, b in spec_n)
                ok = kind != "motif" or (dist[y][x] is not None and dist[y][x] >= mm.HALO and clear)
                same = kind == "motif" and cls in near           # a same-class neighbour is the last resort
                key = (max(abs(x - p[0]), abs(y - p[1])), (x - p[0]) ** 2 + (y - p[1]) ** 2, y, x)
                slot = (ok, not same)
                if best.get(slot) is None or key < best[slot][0]:
                    best[slot] = (key, q)
        choice = next((best[k] for k in ((True, True), (True, False), (False, True), (False, False))
                       if best.get(k) is not None), None)
        halo_ok = choice is not None and any(best.get(k) is choice for k in ((True, True), (True, False)))
        if choice is None:
            raise SystemExit(f"{IMAGE_NAME[n]}: no free plain {t} cell to move {cls} from {p}")
        q = choice[1]
        spec_n[q] = spec_n.pop(p)
        moves.append((p, q, cls, t, halo_ok))
    return moves


# ------------------------------------------------------------------ stage: roles (v3 placement policy)
# Histogram target: v2's (transition counts T per class, max over images; plain targets Pt common to the
# three images). Surplus transition pieces are hosted by plain cells along a fallback chain per pair.
# A chain stage is (host tile, zone):
#   far     interior cell at Chebyshev distance >= FUR_MIN_DIST from every transition cell and >= FRAME_MIN
#           from the picture edge; free rotation ("fur" mark)
#   near    any other interior non-transition cell (next to a transition or to the edge ring)
#   edge    S cell that touches an S-L boundary (8-neighbourhood) for some class; interior = the rest
# Transition cells and frame cells are never hosts. The capacity check (min-cost allocation over the chain
# stages) and the picker (place_image) both read the pools of host_zones, so a plan that passes the check
# always finds cells. The tile counts of a plan are exact: host tile t of image n = F[n][t] - Pt[t].

CHAIN = {                                             # stages per pair, in order; cost = position
    "DL": [("D", "far"), ("D", "near"), ("M", "far"), ("M", "near"), ("L", "far")],
    "DM": [("D", "far"), ("D", "near"), ("M", "far"), ("M", "near"), ("L", "far")],
    "DW": [("D", "far"), ("D", "near"), ("M", "far"), ("M", "near"), ("L", "far")],   # pairs with D: D chain
    "ML": [("M", "far"), ("M", "near"), ("L", "far")],
    "MW": [("W", "far"), ("W", "near"), ("M", "far")],
    "WL": [("W", "far"), ("W", "near"), ("M", "far")],
    "SL": [("S", "edge"), ("S", "interior")],
}
STAGE_ORDER = [("D", "far"), ("D", "near"), ("M", "far"), ("M", "near"), ("L", "far"),
               ("W", "far"), ("W", "near"), ("S", "edge"), ("S", "interior")]
FUR_MIN_DIST = 2                       # Chebyshev distance from every transition cell for interior marks
FRAME_MIN = 2                          # ... and from the picture edge (frame cells), in cells
SE_ROLE = {"SLs": "se_sls", "SLc": "se_slc", "LSc": "se_lsc"}   # S-edge roles, one class each
SE_CLASS = {v: k for k, v in SE_ROLE.items()}


def stage_name(stage: tuple) -> str:
    return f"{stage[0]}-{stage[1]}"


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


def s_geometry(p, trans: set):
    """Sides k (0 T, 1 R, 2 B, 3 L) and corners q (0 TL .. 3 BL) of cell p whose neighbour is a transition."""
    B = {k for k, (dx, dy) in enumerate(SIDE_OFF) if (p[0] + dx, p[1] + dy) in trans}
    Q = [q for q, (dx, dy) in enumerate(CORNER_OFF) if (p[0] + dx, p[1] + dy) in trans]
    return B, Q


def s_options(B: set, Q: list) -> dict:
    """Best (score, rotation in degrees) per SL class for a plain S cell.

    B: sides k whose neighbour is a transition; Q: corners q whose diagonal neighbour is a transition.
    Score 2 = every L side meets a boundary, 0 = partly, < 0 = none.
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


def is_far_cell(p, dist: dict, C: int, R: int) -> bool:
    return (dist.get(p, 99) >= FUR_MIN_DIST and FRAME_MIN <= p[0] <= C - 1 - FRAME_MIN
            and FRAME_MIN <= p[1] <= R - 1 - FRAME_MIN)


def host_zones(tok, st, C: int, R: int) -> dict:
    """Candidate host cells of one image by chain stage, with the S options. Capacity and picker both use this."""
    trans = transition_cells(st, R, C)
    dist = cheb_dist(trans, C, R)
    pools: dict = {(t, z): [] for t in "DMWL" for z in ("far", "near")}
    pools[("S", "edge")], pools[("S", "interior")] = [], []
    s_opts: dict = {}
    for y in range(R):
        for x in range(C):
            p = (x, y)
            if is_frame(y, x, R, C) or p in trans:
                continue
            t = tok[y][x]
            if t == "S":
                s_opts[p] = s_options(*s_geometry(p, trans))
                zone = "edge" if max(v[0] for v in s_opts[p].values()) >= 0 else "interior"
                pools[("S", zone)].append(p)
            else:
                pools[(t, "far" if is_far_cell(p, dist, C, R) else "near")].append(p)
    return {"pools": pools, "s_opts": s_opts, "trans": trans}


def min_cost_flow(arcs: list, src, snk) -> tuple[int, int, list]:
    """Successive shortest paths (Bellman-Ford). arcs: (u, v, cap, cost). Returns (flow, cost, flow per arc)."""
    g: dict = {}
    fwd: list = []

    def add(u, v, cap: int, cost: int) -> None:
        f = {"to": v, "cap": cap, "cost": cost, "rev": None}
        b = {"to": u, "cap": 0, "cost": -cost, "rev": f}
        f["rev"] = b
        g.setdefault(u, []).append(f)
        g.setdefault(v, []).append(b)
        fwd.append((f, cap))

    for u, v, cap, cost in arcs:
        add(u, v, cap, cost)
    flow = total = 0
    while True:
        dist = {src: 0}
        prev: dict = {}
        for _ in range(len(g)):
            moved = False
            for u in list(dist):
                for e in g.get(u, []):
                    if e["cap"] > 0 and (e["to"] not in dist or dist[u] + e["cost"] < dist[e["to"]]):
                        dist[e["to"]] = dist[u] + e["cost"]
                        prev[e["to"]] = e
                        moved = True
            if not moved:
                break
        if snk not in dist:
            break
        push, v = None, snk
        while v != src:
            e = prev[v]
            push = e["cap"] if push is None else min(push, e["cap"])
            v = e["rev"]["to"]
        v = snk
        while v != src:
            e = prev[v]
            e["cap"] -= push
            e["rev"]["cap"] += push
            v = e["rev"]["to"]
        flow += push
        total += push * dist[snk]
    return flow, total, [cap - f["cap"] for f, cap in fwd]


def alloc_hosts(P: dict, s: dict, size: dict):
    """Split each pair's surplus over its chain stages so that host tile t gets exactly s[t] pieces, at the least
    total chain cost. size: pool size per stage (the cells the picker draws from). Returns (cost, {pair: {stage: n}})
    or None when no split exists."""
    pieces = {p: P[p] for p in PAIRS if P.get(p, 0)}
    if sum(pieces.values()) != sum(s.values()) or any(v < 0 for v in s.values()):
        return None
    arcs, idx = [], []
    for p, n in pieces.items():
        arcs.append(("src", ("p", p), n, 0))
        for k, stage in enumerate(CHAIN[p]):
            if size.get(stage, 0):
                idx.append((len(arcs), p, stage))
                arcs.append((("p", p), ("st", stage), n, k))
    for stage, cap in size.items():
        if cap:
            arcs.append((("st", stage), ("t", stage[0]), cap, 0))
    for t in ORDER:
        arcs.append((("t", t), "snk", s.get(t, 0), 0))
    flow, cost, got = min_cost_flow(arcs, "src", "snk")
    if flow != sum(pieces.values()):
        return None
    out: dict = {}
    for i, p, stage in idx:
        if got[i]:
            out.setdefault(p, {})[stage] = got[i]
    return cost, out


def place_image(n: str, tok: list, host: dict, sur_n: dict, alloc_n: dict, C: int, R: int,
                rnd: random.Random, avoid: frozenset = frozenset()) -> dict:
    """Host cells of one image: {(x, y): (role token, stage, pair, chain rank)}. Plain cells are not listed."""
    pools, s_opts, trans = host["pools"], host["s_opts"], host["trans"]
    out: dict = {}
    m_key = {p: rnd.random() ** (1.0 / (1.0 + 2.0 * p[1] / max(1, R - 1)))
             for z in ("far", "near") for p in pools[("M", z)]}

    # SL pieces: S-edge cells first, then S-interior; within a zone the best (cell, class) by score.
    rem = {c: sur_n.get(c, 0) for c in ("LSc", "SLc", "SLs")}
    tie = {p: rnd.random() for p in s_opts}
    chosen_s: set = set()
    for stage in (("S", "edge"), ("S", "interior")):
        for _ in range(alloc_n.get("SL", {}).get(stage, 0)):
            best = None
            for p in pools[stage]:
                if p in out:
                    continue
                pen = sum(1 for dx, dy in SIDE_OFF if (p[0] + dx, p[1] + dy) in chosen_s)
                for cls, k in rem.items():
                    if k:
                        key = (-s_opts[p][cls][0], pen, tie[p], cls)
                        if best is None or key < best[0]:
                            best = (key, p, cls)
            if best is None:
                raise SystemExit(f"{IMAGE_NAME[n]}: no free {stage_name(stage)} cell for an SL piece (left {rem})")
            _, p, cls = best
            score, deg = s_opts[p][cls]
            out[p] = (f"{SE_ROLE[cls]}@{deg}", stage_name(stage), "SL", CHAIN["SL"].index(stage))
            chosen_s.add(p)
            rem[cls] -= 1
    if any(rem.values()):
        raise SystemExit(f"{IMAGE_NAME[n]}: SL classes not placed: {rem}")

    # Other hosts: interior marks with free rotation, one cell apart from other marks where the pool allows.
    blocked: set = set()

    def pick(pool: list, k: int, stage: tuple) -> list:
        got: list = []
        relaxed_picks = 0
        for relaxed in (False, True):
            for p in pool:
                if len(got) == k:
                    break
                if p in got or p in out or (not relaxed and p in blocked):
                    continue
                if p in trans or is_frame(p[1], p[0], R, C):
                    raise SystemExit(f"{IMAGE_NAME[n]}: {stage_name(stage)} pool holds a transition or frame cell {p}")
                got.append(p)
                blocked.add(p)
                blocked.update(ring8(p[0], p[1], C, R))
                if relaxed:
                    relaxed_picks += 1
            if len(got) == k:
                break
        if len(got) < k:
            raise SystemExit(f"{IMAGE_NAME[n]}: {stage_name(stage)} pool gives {len(got)} of {k} hosts")
        if relaxed_picks:
            log(f"   {n} {IMAGE_NAME[n]:6s} {stage_name(stage)}: spacing relaxed for {relaxed_picks} of {k} hosts")
        return got

    for stage in STAGE_ORDER:
        if stage[0] == "S":
            continue
        labels = [pair for pair, split in alloc_n.items() if pair != "SL" for _ in range(split.get(stage, 0))]
        if not labels:
            continue
        rnd.shuffle(labels)
        pool = list(pools[stage])
        if stage[0] == "M":
            pool.sort(key=lambda p: -m_key[p])            # lower part of the picture first
        else:
            rnd.shuffle(pool)
        pool.sort(key=lambda q: q in avoid)              # v5: motif and hero cells last (stable)
        for p, pair in zip(pick(pool, len(labels), stage), labels):
            out[p] = (f"{stage[0].lower()}_fur_{pair.lower()}@*", stage_name(stage), pair, CHAIN[pair].index(stage))
    return out


# ------------------------------------------------------------------ chip sub-classes (v4)
CHIP_FAMILY = {"L": ["L", "Lr", "Lb", "Lo", "Lx"], "M": ["M", "Mr", "Mb", "Mc"]}   # plain tier first
SUB_CLASSES = [c for members in CHIP_FAMILY.values() for c in members[1:]]
CHIP_OWN_W, CHIP_OTHER_W = 1.0, 0.35   # role preference: the class a region is for, and the others
# Per picture and tier: the chip sub-classes in claim order, each with a feature. A sub-class claims its share
# of the tier's plain cells nearest its feature; the plain class keeps the rest. Features (fractions of the
# picture, 0,0 top left): ("pt", fx, fy) a point; ("band", fy) a horizontal line; ("ring", fx, fy, r) a circle
# of radius r cells. Picture A (hare, dawn): rust in the upper-left sky, olive along the horizon. B (owl, dusk):
# blue around the moon, olive on the snow at the bottom. C (swan, midnight): rust along the water line, blue
# at the moon. Each picture's regions differ, so one chip hints at a different place in each picture.
CHIP_FEATURES = {
    "A": {"L": [("Lr", ("pt", 0.0, 0.0)), ("Lo", ("band", 0.45)), ("Lb", ("pt", 1.0, 0.55)), ("Lx", ("pt", 0.5, 1.0))],
          "M": [("Mr", ("pt", 0.2, 0.35)), ("Mb", ("pt", 0.5, 1.0)), ("Mc", ("pt", 0.9, 0.6))]},
    "B": {"L": [("Lb", ("ring", 0.5, 0.2, 9.0)), ("Lo", ("band", 1.0)), ("Lr", ("pt", 0.0, 0.5)), ("Lx", ("pt", 1.0, 0.0))],
          "M": [("Mc", ("pt", 0.5, 1.0)), ("Mr", ("pt", 0.0, 0.0)), ("Mb", ("pt", 1.0, 0.5))]},
    "C": {"L": [("Lb", ("pt", 0.85, 0.12)), ("Lr", ("pt", 0.5, 0.3)), ("Lo", ("pt", 0.0, 0.0)), ("Lx", ("pt", 1.0, 1.0))],
          "M": [("Mr", ("band", 0.37)), ("Mb", ("pt", 0.0, 1.0)), ("Mc", ("pt", 0.6, 0.7))]},
}


def chip_role(n: str, sub: str) -> str:
    return f"chip_{n.lower()}_{sub.lower()}"


def chip_dist(feat, p, C: int, R: int) -> float:
    x, y = p
    if feat[0] == "pt":
        return math.hypot(x - feat[1] * (C - 1), y - feat[2] * (R - 1))
    if feat[0] == "band":
        return abs(y - feat[1] * (R - 1))
    if feat[0] == "ring":
        return abs(math.hypot(x - feat[1] * (C - 1), y - feat[2] * (R - 1)) - feat[3])
    raise ValueError(feat)


def chip_split(tiles, st, cell_info, special, Pmain, C: int, R: int, rnd: random.Random):
    """Chip label of every plain L or M cell (frame included) that is not a transition or a surplus host.

    Returns ({(image, (x, y)): class}, quota) with quota[tier][sub] = the common count of each sub-class. The
    plain class of a tier takes the rest, Pt[tier] minus the sub-class counts, so the label counts of every
    picture add up to the same target histogram.
    """
    quota = {t: {c: round(Pmain[t] / len(members)) for c in members[1:]} for t, members in CHIP_FAMILY.items()}
    label: dict = {}
    for n in IMAGES:
        trans = transition_cells(st[n], R, C)
        for tier, members in CHIP_FAMILY.items():
            feats = CHIP_FEATURES[n][tier]
            if sorted(c for c, _ in feats) != sorted(members[1:]):
                raise SystemExit(f"CHIP_FEATURES[{n}][{tier}] must list {members[1:]}")
            pool = [(x, y) for y in range(R) for x in range(C)
                    if tiles[n][y][x] == tier and (x, y) not in trans and (x, y) not in cell_info[n]
                    and (x, y) not in special[n]]
            if len(pool) != Pmain[tier]:
                raise SystemExit(f"{n}: {len(pool)} plain {tier} cells for the chip split, target {Pmain[tier]}")
            jit = {p: rnd.random() * 1e-3 for p in pool}
            left = set(pool)
            for sub, feat in feats:
                ranked = sorted(left, key=lambda p: (chip_dist(feat, p, C, R) + jit[p], p))
                take = ranked[:quota[tier][sub]]
                for p in take:
                    label[(n, p)] = sub
                left.difference_update(take)
            for p in left:
                label[(n, p)] = tier
    return label, quota


def chip_report(spec, flat, cls, C: int, R: int) -> None:
    """Per picture: own-class share of the chip roles, and each sub-class's count and centroid (log, chip-report.txt)."""
    lines = ["# Chip sub-classes per picture, experiment 011 v4. Own class = the class of the role's preference.",
             "# centroid (x, y): fractions of the picture, y down.", ""]
    hist = []
    for k, n in enumerate(IMAGES):
        hit = tot = 0
        pos: dict = {}
        for p, role in enumerate(flat[k]):
            c = cls[k][p]
            if c in SUB_CLASSES:
                pos.setdefault(c, []).append(p)
            if role.startswith("chip_"):
                d = spec.roles[role]
                own = d.classes[max(range(len(d.classes)), key=lambda i: d.weights[i])]
                tot += 1
                hit += c == own
        parts = []
        for c in SUB_CLASSES:
            ps = pos.get(c, [])
            if ps:
                cx = sum(p % C for p in ps) / len(ps) / (C - 1)
                cy = sum(p // C for p in ps) / len(ps) / (R - 1)
                parts.append(f"{c} {len(ps)} ({cx:.2f},{cy:.2f})")
        lines.append(f"{n} {IMAGE_NAME[n]}: chip roles {tot}, own class {hit} ({100.0 * hit / max(tot, 1):.1f}%)")
        lines.append("   " + "; ".join(parts))
        hist.append(Counter(cls[k]))
    same = all(all(h[c] == hist[0][c] for c in SUB_CLASSES) for h in hist)
    lines.append(f"sub-class histograms identical across A, B, C: {same}")
    text = "\n".join(lines)
    (WORK / "chip-report.txt").write_text(text + "\n", encoding="utf-8")
    log("   " + text.replace("\n", "\n   "))


def stage_roles(tiles, st, bud) -> None:
    rnd = random.Random(SEED)
    C, R = len(tiles["A"][0]), len(tiles["A"])
    CELLS = R * C
    T, sur_k = bud["T"], bud["sur"]
    codes = bud["classes"]
    info = {n: image_roles(tiles[n], st[n], C, R) for n in IMAGES}
    host = {n: host_zones(tiles[n], st[n], C, R) for n in IMAGES}
    size = {n: {k: len(v) for k, v in host[n]["pools"].items()} for n in IMAGES}
    tile_pool = {n: {t: sum(v for (tt, _), v in size[n].items() if tt == t) for t in ORDER} for n in IMAGES}
    total_trans = sum(T.values())
    plain_total = CELLS - total_trans
    frame_k = {n: {t: info[n]["frame"][t] for t in ORDER} for n in IMAGES}
    F = {n: {t: info[n]["frame"][t] + info[n]["near_n"][t] + info[n]["far_n"][t] for t in ORDER} for n in IMAGES}
    P_pair = {n: {p: sum(sur_k[n][c] for c in codes if pair_of(c) == p) for p in PAIRS} for n in IMAGES}
    log(f"3. roles: total transitions {total_trans}, plain target total {plain_total}, tiers {ORDER}")
    for n in IMAGES:
        log(f"   {n} {IMAGE_NAME[n]:6s} F (plain-capable, frame incl.) {fmt(F[n])}; frame {fmt(frame_k[n])}; "
            "surplus " + " ".join(f"{p} {P_pair[n][p]}" for p in PAIRS if P_pair[n][p]))
        log(f"   {n} {IMAGE_NAME[n]:6s} host pools (cells per chain stage): "
            + " ".join(f"{stage_name(s)} {size[n][s]}" for s in STAGE_ORDER))

    # Plain targets: common to the images. Each image's host split must exist (exact tile counts, the chain
    # pools as capacity); among the feasible targets take the least total chain cost.
    lo = {t: max(frame_k[n][t] for n in IMAGES) for t in ORDER}
    hi = {t: min(F[n][t] for n in IMAGES) for t in ORDER}
    last = ORDER[-1]
    best, n_cand = None, 0
    for vals in itertools.product(*(range(lo[t], hi[t] + 1) for t in ORDER[:-1])):
        Pt = dict(zip(ORDER[:-1], vals))
        Pt[last] = plain_total - sum(vals)
        if not (lo[last] <= Pt[last] <= hi[last]):
            continue
        total, alloc = 0, {}
        for n in IMAGES:
            s = {t: F[n][t] - Pt[t] for t in ORDER}
            if any(s[t] < 0 or s[t] > tile_pool[n][t] for t in ORDER):
                break
            res = alloc_hosts(P_pair[n], s, size[n])
            if res is None:
                break
            total += res[0]
            alloc[n] = (s, res[0], res[1])
        else:
            n_cand += 1
            if best is None or total < best[0]:
                best = (total, Pt, alloc)
    if best is None:
        raise SystemExit("no plain-target split fits the chain pools")
    total_cost, Pt, alloc = best
    log(f"   plain targets {fmt(Pt)}; chain cost {total_cost} ({n_cand} feasible targets checked)")
    for n in IMAGES:
        s, c, _ = alloc[n]
        log(f"   {n} {IMAGE_NAME[n]:6s} host tiers needed D/S/M/W/L {fmt(s)}; chain cost {c}")

    # v5: motif and hero cells. Their classes come from the motif maps; hosts avoid them (picker order) and a motif
    # that is still needed as a host moves to the nearest plain cell of its tier (displace_specials).
    mot = run_motif_maps(tiles)
    special = {n: special_cells(n, mot[n], tiles[n], st[n], R, C) for n in IMAGES}
    trans_of = {n: transition_cells(st[n], R, C) for n in IMAGES}
    avoid = {n: {p for p, (_, kind) in special[n].items() if kind != "trans"} for n in IMAGES}
    cls_cnt = {n: Counter(c for c, _ in special[n].values()) for n in IMAGES}
    tr_cnt = {n: Counter(st[n]["tokens"][p[1]][p[0]].partition("@")[0] for p, (_, kind) in special[n].items()
                         if kind == "trans") for n in IMAGES}
    Msp = {n: {t: sum(1 for p, (_, kind) in special[n].items() if kind != "trans" and tiles[n][p[1]][p[0]] == t)
               for t in ORDER} for n in IMAGES}
    for n in IMAGES[1:]:
        if cls_cnt[n] != cls_cnt["A"] or tr_cnt[n] != tr_cnt["A"] or Msp[n] != Msp["A"]:
            raise SystemExit(f"motif or hero counts differ between A and {n}")
    Msp = Msp["A"]
    Pmain = {t: Pt[t] - Msp[t] for t in ORDER}              # plain remainder per tier (chips included)
    log("   motif and hero cells per picture (identical across A, B, C): "
        + ", ".join(f"{c} {k}" for c, k in sorted(cls_cnt["A"].items())))
    log(f"   plain remainder after motifs: {fmt(Pmain)} (plain targets {fmt(Pt)} minus motif cells {fmt(Msp)})")
    cell_info = {n: place_image(n, tiles[n], host[n], sur_k[n], alloc[n][2], C, R, rnd, avoid[n]) for n in IMAGES}
    dist = {n: motif_module(tiles).boundary_distance(tiles[n]) for n in IMAGES}
    moves = {n: displace_specials(n, special[n], cell_info[n], tiles[n], trans_of[n], C, R, dist[n]) for n in IMAGES}
    for n in IMAGES:
        log(f"   {n} {IMAGE_NAME[n]:6s} motifs displaced from hosts: {len(moves[n])}"
            + (" " + ", ".join(f"{c}" for _, _, c, _, _ in moves[n]) if moves[n] else ""))
    chip, quota = chip_split(tiles, st, cell_info, special, Pmain, C, R, rnd)
    chip_target = {}
    for tier, members in CHIP_FAMILY.items():
        for sub in members[1:]:
            chip_target[sub] = quota[tier][sub]
        chip_target[tier] = Pmain[tier] - sum(quota[tier].values())
    log(f"   chip split: plain targets {fmt(Pt)} -> sub-class quotas " + ", ".join(
        f"{sub} {chip_target[sub]}" for sub in SUB_CLASSES) + f"; plain L {chip_target['L']} M {chip_target['M']}")
    cols = [stage_name(s) for s in STAGE_ORDER]
    log("   placement per pair (pieces by chain stage; fallback = placed after the pair's first stage):")
    log("     " + f"{'image':10s}{'pair':>5s}{'surpl':>6s} " + "".join(f"{c:>10s}" for c in cols) + f"{'fallback':>10s}")
    place_lines = []
    for n in IMAGES:
        tally = Counter((pair, cat) for _, cat, pair, _ in cell_info[n].values())
        fb = Counter(pair for _, _, pair, rank in cell_info[n].values() if rank > 0)
        for pair in PAIRS:
            if not P_pair[n][pair]:
                continue
            placed = sum(tally[(pair, c)] for c in cols)
            if placed != P_pair[n][pair]:
                raise SystemExit(f"{IMAGE_NAME[n]} {pair}: placed {placed} of {P_pair[n][pair]}")
            log(f"     {n + ' ' + IMAGE_NAME[n]:10s}{pair:>5s}{P_pair[n][pair]:6d} "
                + "".join(f"{tally[(pair, c)]:10d}" for c in cols) + f"{fb[pair]:10d}")
        for (x, y), (role_tok, cat, pair, rank) in sorted(cell_info[n].items(), key=lambda kv: (kv[0][1], kv[0][0])):
            place_lines.append(f"{n} x={x} y={y} tile={tiles[n][y][x]} pair={pair} {cat} rank={rank} {role_tok}")
    (WORK / "placement.txt").write_text("\n".join(place_lines) + "\n", encoding="utf-8")

    used = {r.partition("@")[0] for n in IMAGES for r, _, _, _ in cell_info[n].values()}
    roles = {}
    for t in ORDER:
        if t in CHIP_FAMILY:
            continue                                # L and M: chip roles below
        low = t.lower()
        roles[f"{low}_frame"] = {"classes": [t]}
        roles[f"{low}_near"] = {"classes": [t]}
        roles[f"{low}_far"] = {"classes": [t]}
    for n in IMAGES:
        for members in CHIP_FAMILY.values():
            for own in members:
                roles[chip_role(n, own)] = {"classes": list(members),
                                            "weights": [CHIP_OWN_W if c == own else CHIP_OTHER_W for c in members]}
    for name in sorted(used):
        if name in SE_CLASS:
            roles[name] = {"classes": [SE_CLASS[name]]}
        else:                                       # d_fur_dl, m_fur_ml, w_fur_wl, l_fur_ml ...
            pair = name.split("_")[-1].upper()
            roles[name] = {"classes": [c for c in codes if pair_of(c) == pair and T[c] > 0]}
    for c in codes:
        roles[f"edge_{c.lower()}"] = {"classes": [c]}
    for cls in sorted(cls_cnt["A"]):                  # v5: one fixed role per motif and hero class
        roles[mo_role(cls)] = {"classes": [cls]}
    target = {c: T[c] - tr_cnt["A"].get(c, 0) for c in codes}     # hero transitions take their piece from the class
    target.update(Pmain)
    target.update(chip_target)
    for cls, k in cls_cnt["A"].items():                # v5: motif and hero classes (identical across pictures)
        target[cls] = k
    assert sum(target.values()) == CELLS, (sum(target.values()), CELLS)
    spec = {"_note": "Experiment 011 v5 roles (motif and hero classes fixed per cell; chip sub-classes on the plain L and M remainder): surplus transition pieces placed along the per-pair fallback chain "
                     "(D far, D near, M far, M near, L far; M far, M near, L far; W far, W near, M far; S edge, "
                     "S interior). target_counts = v2's (per-class max over images for transitions, common plain "
                     "targets). Edge roles fixed; plain L and M cells take chip roles.",
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
                if (x, y) in special[n]:                     # v5: motif or hero cell (fixed class)
                    sc, kind = special[n][(x, y)]
                    row.append(f"{mo_role(sc)}@{cls.partition('@')[2] or 0}" if kind == "trans" else mo_role(sc))
                elif len(base) == 3:
                    row.append(f"edge_{base.lower()}@{cls.partition('@')[2] or 0}")
                elif (x, y) in cell_info[n]:
                    row.append(cell_info[n][(x, y)][0])
                elif (n, (x, y)) in chip:
                    row.append(chip_role(n, chip[(n, (x, y))]))
                elif is_frame(y, x, R, C):
                    row.append(f"{tiles[n][y][x].lower()}_frame")
                else:
                    default = "far" if (x, y) in far_set else "near"
                    row.append(f"{tiles[n][y][x].lower()}_{default}")
            lines.append(" ".join(row))
        lines.append("")
    (WORK / "roles.txt").write_text("\n".join(lines), encoding="utf-8")
    rep_lines = ["# Motif and hero cells, experiment 011 v6 (A hare, B owl, C swan). moves = motif displaced from a cell",
                 "# that had to host a surplus piece, to the nearest plain cell of its tier.", ""]
    for n in IMAGES:
        rep_lines.append(f"{n} {IMAGE_NAME[n]}: " + ", ".join(f"{c} {k}" for c, k in sorted(cls_cnt[n].items())))
        rep_lines.append(f"   displaced {len(moves[n])}: " + ("; ".join(f"{p}->{q} {c} ({t}{'' if h else ', HALO BREACH'})" for p, q, c, t, h in moves[n])
                                                               or "none"))
    rep_lines.append("class counts identical across A, B, C: yes (checked)")
    rep_lines.append(f"plain motif cells per tier (identical): {fmt(Msp)}; plain remainder {fmt(Pmain)}")
    (WORK / "motif-report.txt").write_text("\n".join(rep_lines) + "\n", encoding="utf-8")
    log(f"   wrote roles.txt, roles-spec.json, placement.txt ({len(used)} role names)")


# ------------------------------------------------------------------ stage: scenes


def stage_scenes(border: str, restarts: int, iters: int, seed: int, pref_weight: float) -> None:
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
    if border != "tray":
        raise SystemExit("v4 needs --border tray: chip classes may sit on the frame, which the standard border rule forbids")
    target = Cn(spec.target_counts)
    # Tray: the border constrains nothing, so one container (the whole board) holds the common histogram.
    containers = [("all", tuple(range(rows * cols)))]
    Mk = [[Cn(target)] for _ in range(3)]
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
        cls, value = R_._arrange(cls0, flat, containers, allowed, weights, board, rng, iters, pref_weight, None, 1.0)
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
    chip_report(spec, flat, cls, cols, rows)


def stage_metrics() -> None:
    out = WORK / "scene-metrics.txt"
    p = subprocess.run(["metapuzzle", "scene-metrics", str(WORK / "scenes.txt")], capture_output=True, text=True)
    out.write_text(p.stdout + p.stderr, encoding="utf-8")
    log(f"5. scene-metrics exit {p.returncode}; wrote {out}")
    log("   " + "\n   ".join((p.stdout + p.stderr).strip().splitlines()[:12]))


def check_classes_for_specs(used: set[str]) -> None:
    """Every class the roles can produce must be in the v9 specs (no local copies in v2)."""
    for name in (V12_CLASSES, V12_INK):
        spec = json.loads((HERE / name).read_text(encoding="utf-8"))
        missing = sorted(c for c in used if c not in spec["classes"])
        log(f"   {name}: used classes missing: {missing if missing else 'none'}")
        if missing:
            raise SystemExit(f"{name} lacks {missing}")


def stage_render(border: str, cell: int, iters: int, seed: int) -> None:
    for name, base in ((V12_INK, "run-ink"), (V12_CLASSES, "run-full")):
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
    ap.add_argument("--in-dir", default="27x38-v2", help="folder under 011-subjects holding tiers-{A,B,C}.txt")
    ap.add_argument("--out-dir", default="27x38-v2",
                    help="folder for renders and pipeline-out-v6/ (intermediates)")
    ap.add_argument("--render-tag", default="-v6", help="suffix of the render folders (run-ink<TAG>, run-full<TAG>)")
    ap.add_argument("--stages", default="equalize,classify,budgets,roles,scenes,metrics,render")
    ap.add_argument("--tiers", choices=["source", "eq"], default="eq",
                    help="tiles for the stages after equalize: source files or tiers-eq-*.txt")
    ap.add_argument("--eq-iters", type=int, default=6000)
    ap.add_argument("--eq-seeds", default="0,1,2")
    ap.add_argument("--eq-lam", type=float, default=EQ_LAM, help="weight per unit of move cost")
    ap.add_argument("--border", choices=["standard", "tray"], default="tray")
    ap.add_argument("--restarts", type=int, default=8)
    ap.add_argument("--iters", type=int, default=1000000, help="scene build annealing iterations")
    ap.add_argument("--render-iters", type=int, default=300000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--pref-weight", type=float, default=1.0,
                    help="weight of the role preference (chip patterns) in the scene annealing (default 1.0)")
    ap.add_argument("--cell", type=int, default=21)
    args = ap.parse_args()
    EQ_LAM = args.eq_lam
    SIZE_DIR = EXP / args.in_dir
    RENDER_TAG = args.render_tag
    OUT_DIR = EXP / args.out_dir
    WORK = OUT_DIR / "pipeline-out-v6"
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
        stage_scenes(args.border, args.restarts, args.iters, args.seed, args.pref_weight)
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
