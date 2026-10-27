"""Step 6 roles (v5): merged transition classes, surplus pieces in far slots, near cells as fallback.

Reads quantized-codes-v5.txt (quantize_v5.py: merged class plus @degrees per transition cell) and
quantized-v2/*.npy (tiers). Writes roles-v5.txt and roles-spec-v5.json.

Cells (interior unless noted; frame cells are plain):
- x_frame: frame cell, plain class only.
- edge_<class>@deg: interior transition cell, class and rotation fixed.
- x_near: plain interior cell within 1 (8-neighbourhood) of a transition cell. Plain only.
- x_far: plain interior cell at distance >= 2 from every transition cell. Plain only, unless a slot.
- x_slot: far cell in an 8-independent set (no two surplus pieces touch, even diagonally). Plain, or a
  surplus class of a pair that contains x. Surplus weight 0.5 (low preference).
- x_nslot: FALLBACK near cell of tier x, used only for surplus that the far slots of tier x cannot hold.
  Plain, or a surplus class of a pair containing x. Surplus weight 0.2.

Surplus: per transition class c, target T[c] = max over the images; surplus in an image = T[c] - own count.
Tier accounting: plain targets P_x are common to the images. In an image, the non-frame, non-edge tier-x
cells are near_x + far_x; s_x = frame_x + near_x + far_x - P_x of them carry surplus. Each pair's surplus
can go to either tier of the pair (flow y_DM, y_DL, y_ML, solved exactly). The plain targets are chosen to
minimise the near fallback summed over the images; the far-slot capacity per tier is estimated from
randomised greedy independent sets, then the chosen placement is built and its counts printed.

Usage: make_roles_v5.py
"""
import json
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))

from metapuzzle.scene import load_scenes  # noqa: E402

NAMES = ["cat", "sailboat", "tree"]
ROWS, COLS = 25, 20
TIERS = "DML"
PAIRS = ("DM", "DL", "ML")
N_RESTARTS = 3000
SLOT_WEIGHT = 0.5
NSLOT_WEIGHT = 0.2
SEED = 0


def is_frame(x: int, y: int) -> bool:
    return y in (0, ROWS - 1) or x in (0, COLS - 1)


def is_trans(code: str) -> bool:
    return len(code) == 3  # merged classes: two tier letters and a pattern letter (dots too)


def pair_key(code: str) -> str:
    return "".join(sorted(code[:2], key=TIERS.index))


def ring8(x: int, y: int):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if (dx, dy) != (0, 0) and 0 <= x + dx < COLS and 0 <= y + dy < ROWS:
                yield x + dx, y + dy


def analyse(grid, tier):
    """Cells of one image by role class. Returns dict with counts and cell lists."""
    boundary = {(x, y) for y in range(ROWS) for x in range(COLS)
                if not is_frame(x, y) and is_trans(grid[y][x])}
    X = lambda x, y: TIERS[int(tier[y, x])]  # noqa: E731
    out = {"frame": Counter(), "near": [], "far": [], "edges": Counter(), "boundary": boundary}
    for y in range(ROWS):
        for x in range(COLS):
            if is_frame(x, y):
                out["frame"][X(x, y)] += 1
            elif (x, y) in boundary:
                out["edges"][grid[y][x]] += 1
            elif any(p in boundary for p in ring8(x, y)):
                out["near"].append((x, y))
            else:
                out["far"].append((x, y))
    out["near_n"] = Counter(X(x, y) for x, y in out["near"])
    out["far_n"] = Counter(X(x, y) for x, y in out["far"])
    out["X"] = X
    return out


def independent_far(far, X, need, rnd):
    """Best randomised greedy 8-independent subset of far cells: reaches need[t] per tier if it can."""
    best, best_score = [], -1
    for _ in range(N_RESTARTS):
        order = far[:]
        rnd.shuffle(order)
        chosen, blocked = [], set()
        for p in order:
            if p in blocked:
                continue
            chosen.append(p)
            blocked.add(p)
            blocked.update(ring8(*p))
        cnt = Counter(X(*p) for p in chosen)
        score = sum(min(cnt[t], need[t]) for t in TIERS)
        if score > best_score:
            best, best_score = chosen, score
        if all(cnt[t] >= need[t] for t in TIERS):
            break
    return best


def tier_caps(far, X, rnd):
    """Largest 8-independent far count per tier over the restarts (an estimate; placement confirms it)."""
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
            blocked.update(ring8(*p))
        cnt = Counter(X(*p) for p in chosen)
        for t in TIERS:
            caps[t] = max(caps[t], cnt[t])
    return caps


def pair_flow(P, s):
    """Split pair surplus P (dict over PAIRS) so tier t receives s[t]. Returns (yDM, yDL, yML) or None.

    yDM = DM pieces that go to D (rest to M); yDL = DL pieces to D; yML = ML pieces to M.
    """
    for yDM in range(P["DM"] + 1):
        yDL = s["D"] - yDM
        yML = s["M"] - P["DM"] + yDM
        if 0 <= yDL <= P["DL"] and 0 <= yML <= P["ML"] and \
                (P["DL"] - yDL) + (P["ML"] - yML) == s["L"]:
            return yDM, yDL, yML
    return None


def choose_nslots(near_cells, X, n, rnd):
    """n[t] fallback cells per tier from the near cells, spread out (fewest chosen neighbours first)."""
    chosen = {t: [] for t in TIERS}
    picked = set()
    for t in TIERS:
        pool = [p for p in near_cells if X(*p) == t]
        if n[t] > len(pool):
            raise SystemExit(f"tier {t}: fallback needs {n[t]} near cells, only {len(pool)} exist")
        rnd.shuffle(pool)
        for _ in range(n[t]):
            p = min(pool, key=lambda q: sum(r in picked for r in ring8(*q)))
            pool.remove(p)
            chosen[t].append(p)
            picked.add(p)
    return chosen


def main() -> None:
    maps = load_scenes(HERE / "quantized-codes-v5.txt")
    grids = [(m.cls, m.rot) for m in maps]
    tones = [np.load(HERE / "quantized-v2" / f"{n}.npy") for n in NAMES]
    rnd = random.Random(SEED)

    info = [analyse(g, t) for (g, _), t in zip(grids, tones)]
    ntot = [Counter(info[k]["X"](x, y) for y in range(ROWS) for x in range(COLS)) for k in range(3)]
    if any(c != ntot[0] for c in ntot):
        raise SystemExit("tier totals differ across images")

    own = []
    for g, _ in grids:
        cnt = Counter()
        for y in range(ROWS):
            for x in range(COLS):
                if not is_frame(x, y) and is_trans(g[y][x]):
                    cnt[g[y][x]] += 1
        own.append(cnt)
    codes = sorted({c for o in own for c in o})
    T = {c: max(o[c] for o in own) for c in codes}
    total_trans = sum(T.values())
    plain_total = 500 - total_trans
    sur = [{c: T[c] - own[k][c] for c in codes} for k in range(3)]
    P = [{p: sum(sur[k][c] for c in codes if pair_key(c) == p) for p in PAIRS} for k in range(3)]

    caps = [tier_caps(info[k]["far"], info[k]["X"], rnd) for k in range(3)]
    F = [{t: info[k]["frame"][t] + info[k]["near_n"][t] + info[k]["far_n"][t] for t in TIERS} for k in range(3)]

    # Plain targets: s_t = F_t - P_t surplus pieces must sit in tier t (F_t = frame + near + far).
    # Supply per tier = isolated far slots (estimate) + near fallback. Minimise the shortfall (pieces
    # with no slot), then the near fallback used.
    best = None
    for TD in range(0, 80):
        for TM in range(0, 130):
            TL = plain_total - TD - TM
            if TL < 0:
                break
            Tp = {"D": TD, "M": TM, "L": TL}
            short, near_use, ok = 0, 0, True
            for k in range(3):
                s = {t: F[k][t] - Tp[t] for t in TIERS}
                if any(s[t] < 0 or s[t] > info[k]["near_n"][t] + info[k]["far_n"][t] for t in TIERS):
                    ok = False
                    break
                if pair_flow(P[k], s) is None:
                    ok = False
                    break
                short += sum(max(0, s[t] - caps[k][t] - info[k]["near_n"][t]) for t in TIERS)
                near_use += sum(max(0, s[t] - caps[k][t]) for t in TIERS)
            if ok and (best is None or (short, near_use) < best[0]):
                best = ((short, near_use), Tp)
    if best is None:
        raise SystemExit("no plain-target split is flow-feasible")
    (shortfall_est, near_est), Tplain = best
    print(f"plain targets {Tplain}; transition target total {total_trans}; "
          f"estimated shortfall {shortfall_est}, near fallback {near_est}")

    roles_name = lambda x, kind: f"{x.lower()}_{kind}"  # noqa: E731
    cell_role = [dict() for _ in range(3)]
    print("placement per image (surplus = pieces that must enter tier x; far slots = 8-independent far cells):")
    total_near = 0
    residue_report = []
    for k in range(3):
        I = info[k]
        X = I["X"]
        s = {t: F[k][t] - Tplain[t] for t in TIERS}
        need = {t: min(s[t], caps[k][t]) for t in TIERS}
        far_set = independent_far(I["far"], X, need, rnd)
        far_cnt = Counter(X(*p) for p in far_set)
        n_fb = {t: max(0, s[t] - far_cnt[t]) for t in TIERS}
        n_fb = {t: min(n_fb[t], info[k]["near_n"][t]) for t in TIERS}
        short_k = {t: max(0, s[t] - far_cnt[t] - n_fb[t]) for t in TIERS}
        near_set = choose_nslots(I["near"], X, n_fb, rnd)
        total_near += sum(n_fb.values())
        for p in far_set:
            cell_role[k][p] = roles_name(X(*p), "slot")
        for t in TIERS:
            for p in near_set[t]:
                cell_role[k][p] = roles_name(t, "nslot")
        # Second fallback for the residue: far cells of the same tier, not isolated (surplus may touch).
        # Only the residue, so the count stays small; each leftover piece is placed next to the fewest
        # other surplus pieces.
        taken = set(cell_role[k])
        touching = 0
        for t in TIERS:
            pool = [q for q in I["far"] if X(*q) == t and q not in taken]
            for _ in range(short_k[t]):
                if not pool:
                    raise SystemExit(f"{NAMES[k]}: no far cell left for tier {t} residue")
                q = min(pool, key=lambda z: sum(r in taken for r in ring8(*z)))
                pool.remove(q)
                if any(r in taken for r in ring8(*q)):
                    touching += 1
                taken.add(q)
                cell_role[k][q] = roles_name(t, "xslot")
        residue_report.append((short_k, touching))
        flow = pair_flow(P[k], s)
        print(f"   {NAMES[k]:9s} surplus into tier D/M/L {s['D']}/{s['M']}/{s['L']} "
              f"(pairs DM {P[k]['DM']}, DL {P[k]['DL']}, ML {P[k]['ML']}; flows DM->D {flow[0]}, DL->D {flow[1]}, ML->M {flow[2]})")
        print(f"   {'':9s} far slots (isolated) D/M/L {far_cnt['D']}/{far_cnt['M']}/{far_cnt['L']} "
              f"(estimate {caps[k]['D']}/{caps[k]['M']}/{caps[k]['L']}); near fallback D/M/L {n_fb['D']}/{n_fb['M']}/{n_fb['L']}")
    print(f"near fallback total (all images): {total_near}")
    for k in range(3):
        sh, touch = residue_report[k]
        print(f"   residue {NAMES[k]:9s}: after far slots and near fallback, {sum(sh.values())} surplus pieces "
              f"(D/M/L {sh['D']}/{sh['M']}/{sh['L']}) go to non-isolated far cells; "
              f"{touch} of them touch another surplus piece")

    roles = {}
    for t in TIERS:
        low = t.lower()
        surplus_cls = [c for c in codes if pair_key(c) and t in pair_key(c) and T[c] > 0]
        roles[f"{low}_frame"] = {"classes": [t]}
        roles[f"{low}_near"] = {"classes": [t]}
        roles[f"{low}_far"] = {"classes": [t]}
        roles[f"{low}_slot"] = {"classes": [t] + surplus_cls,
                                "weights": [1] + [SLOT_WEIGHT] * len(surplus_cls)}
        roles[f"{low}_nslot"] = {"classes": [t] + surplus_cls,
                                 "weights": [1] + [NSLOT_WEIGHT] * len(surplus_cls)}
        roles[f"{low}_xslot"] = {"classes": [t] + surplus_cls,
                                 "weights": [1] + [NSLOT_WEIGHT] * len(surplus_cls)}
    for c in codes:
        roles[f"edge_{c.lower()}"] = {"classes": [c]}

    counts = {c: T[c] for c in codes}
    counts.update(Tplain)
    counts = {k: counts[k] for k in sorted(counts)}
    assert sum(counts.values()) == 500

    spec = {
        "_note": "Step 6 (v5, merged classes; dots keep v4 naming). target_counts: transition classes = per-class "
                 "max over the three images; plain tiers chosen so every image fits. Edge roles fix class and "
                 "rotation. Frame, near and far cells are plain. Surplus transition pieces go to isolated far slots "
                 f"(x_slot, weight {SLOT_WEIGHT}); near cells (x_nslot, weight {NSLOT_WEIGHT}) only where far slots "
                 f"run out; the residue, if any, goes to non-isolated far cells (x_xslot, weight {NSLOT_WEIGHT}).",
        "roles": roles,
        "target_counts": counts,
    }
    (HERE / "roles-spec-v5.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    far_sets = [set(I["far"]) for I in info]
    lines = ["# Step 6 role maps (merged classes), experiment 005 (v5). A = cat, B = sailboat, C = tree.",
             "# x_frame: frame cell. x_near: plain cell next to a transition. x_far: plain cell away from transitions.",
             "# x_slot: far cell for surplus (isolated). x_nslot: near fallback. x_xslot: residue, non-isolated far cell.",
             "# edge_<class>@deg: transition.", ""]
    for k, (g, rots) in enumerate(grids):
        lines.append(f"# {'ABC'[k]}")
        for y in range(ROWS):
            row = []
            for x in range(COLS):
                cls, deg = g[y][x], rots[y][x]
                if is_frame(x, y):
                    if is_trans(cls):
                        raise SystemExit(f"frame cell ({x},{y}) of map {'ABC'[k]} is a transition: {cls}")
                    row.append(roles_name(cls, "frame"))
                elif is_trans(cls):
                    row.append(f"edge_{cls.lower()}@{deg}")
                else:
                    default = "far" if (x, y) in far_sets[k] else "near"
                    row.append(cell_role[k].get((x, y), roles_name(cls, default)))
            lines.append(" ".join(row))
        lines.append("")
    (HERE / "roles-v5.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"target_counts {counts}")
    print("wrote roles-v5.txt and roles-spec-v5.json")


if __name__ == "__main__":
    main()
