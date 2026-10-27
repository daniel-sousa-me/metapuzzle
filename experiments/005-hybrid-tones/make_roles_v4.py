"""Step 5 roles: marching-tiles role maps and roles spec (experiment 005, v4).

Reads quantized-codes-v4.txt (quantize_v4.py: class code plus @rotation per interior boundary cell)
and writes roles-v4.txt and roles-spec-v4.json, built the way make_roles_v3.py builds v3:

- target_counts[code] for a transition code = max over the three images of its boundary cells.
  Plain tiers take the rest of their tier totals (tier total = cells whose own tier is X, counting
  the transition cells' own tier; equal in all images).
- Frame cells: plain tier roles (x_frame). Edge roles: interior transition cells, one role per code,
  with the code's rotation as the suffix (edge_<code>@<deg>).
- Interior plain cells: x_near when 4-adjacent to a transition cell of own tier x, else x_far.
  x_near may take x's transition codes whose pattern is in NEAR_PATTERNS (surplus only, weight 3);
  x_far takes the plain class only. Default NEAR_PATTERNS = "s" (surplus s extends a boundary).

Usage: make_roles_v4.py [NEAR_PATTERNS]   e.g. "s", "sc", "scipd"
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))

from metapuzzle.scene import load_scenes  # noqa: E402
from quantize_v4 import own_tier_of  # noqa: E402

ROWS, COLS = 25, 20
TIER_ORDER = "DML"
NEAR_WEIGHT = 3


def is_frame(x: int, y: int) -> bool:
    return y in (0, ROWS - 1) or x in (0, COLS - 1)


def neighbours(x: int, y: int):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS:
            yield nx, ny


def pattern_of(code: str) -> str:
    return code[-1]  # s, c, i, p or d


def near_boundary(cls, x: int, y: int, tier: str) -> bool:
    return any(len(cls[ny][nx]) > 1 and own_tier_of(cls[ny][nx]) == tier for nx, ny in neighbours(x, y))


def main(near_patterns: str) -> None:
    maps = load_scenes(HERE / "quantized-codes-v4.txt")
    grids = [(m.cls, m.rot) for m in maps]

    def is_trans(code: str) -> bool:
        return len(code) > 1

    # Tier totals (own tier of every cell, plain or transition) must agree across maps.
    tier_tot = [Counter(own_tier_of(c) for row in g for c in row) for g, _ in grids]
    for t in TIER_ORDER:
        if len({tt[t] for tt in tier_tot}) != 1:
            raise SystemExit(f"tier {t} totals differ across images: {[tt[t] for tt in tier_tot]}")

    needs = [Counter(g[y][x] for y in range(ROWS) for x in range(COLS)
                     if not is_frame(x, y) and is_trans(g[y][x])) for g, _ in grids]
    codes = sorted({c for n in needs for c in n})
    target = {c: max(n[c] for n in needs) for c in codes}
    for t in TIER_ORDER:
        target[t] = tier_tot[0][t] - sum(v for c, v in target.items() if is_trans(c) and own_tier_of(c) == t)
    if sum(target.values()) != ROWS * COLS:
        raise SystemExit("target counts do not sum to the cell count")

    near_codes = {t: [c for c in codes if is_trans(c) and own_tier_of(c) == t and pattern_of(c) in near_patterns
                      and target[c] > 0] for t in TIER_ORDER}

    roles = {}
    for t in TIER_ORDER:
        low = t.lower()
        classes = [t] + near_codes[t]
        roles[f"{low}_frame"] = {"classes": [t]}
        roles[f"{low}_near"] = {"classes": classes, "weights": [1] + [NEAR_WEIGHT] * len(near_codes[t])}
        roles[f"{low}_far"] = {"classes": [t]}
    for c in codes:
        if is_trans(c):
            roles[f"edge_{c.lower()}"] = {"classes": [c]}

    counts = {c: target[c] for c in codes if is_trans(c)}
    counts.update({t: target[t] for t in TIER_ORDER})
    counts = {k: counts[k] for k in sorted(counts)}
    spec = {
        "_note": "Step 5 (v4, marching tiles): target_counts per transition code = max over maps of its "
                 "boundary cells; plain tiers take the rest of their totals. Edge roles fix one code per "
                 "cell (rotation suffix from quantize_v4). *_near (interior, next to a transition of the "
                 f"same own tier) may take that tier's codes with patterns '{near_patterns}' as surplus; "
                 "*_far take the plain class only. Frame cells plain.",
        "roles": roles,
        "target_counts": counts,
    }
    suffix = "" if near_patterns == "s" else "-" + near_patterns
    (HERE / f"roles-spec-v4{suffix}.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    lines = ["# Step 5 role maps (marching tiles), experiment 005 (v4). A = cat, B = sailboat, C = tree.",
             "# Roles: x_frame frame cells (plain tier); x_near / x_far interior plain cells (near a transition",
             "# of the same own tier or not); edge_<code>@deg interior transition cells, deg = orientation.", ""]
    for k, (g, rots) in enumerate(grids):
        name = "ABC"[k]
        lines.append(f"# {name}")
        near_ct, far_ct = Counter(), Counter()
        for y in range(ROWS):
            row = []
            for x in range(COLS):
                cls, deg = g[y][x], rots[y][x]
                if is_frame(x, y):
                    if is_trans(cls):
                        raise SystemExit(f"frame cell ({x},{y}) of map {name} is a transition: {cls}")
                    row.append(f"{cls.lower()}_frame")
                elif is_trans(cls):
                    row.append(f"edge_{cls.lower()}@{deg}")
                else:
                    kind = "near" if near_boundary(g, x, y, cls) else "far"
                    (near_ct if kind == "near" else far_ct)[cls] += 1
                    row.append(f"{cls.lower()}_{kind}")
            lines.append(" ".join(row))
        lines.append("")
        surplus = {c: target[c] - needs[k][c] for c in codes if is_trans(c)}
        print(f"map {name}: boundary need {sum(needs[k].values())} cells; surplus total "
              f"{sum(surplus.values())}; surplus by code {{{', '.join(f'{c}:{v}' for c, v in surplus.items() if v)}}}")
        print(f"   interior plain cells near {dict(near_ct)} far {dict(far_ct)}")
    out = HERE / f"roles-v4{suffix}.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"target_counts {counts}")
    print(f"near classes {near_codes}")
    print(f"wrote {out} and roles-spec-v4{suffix}.json")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "s")
