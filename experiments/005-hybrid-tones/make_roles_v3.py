"""Step 4: minimal, localized surplus transitions (experiment 005).

Reads roles.txt (the step 2 role maps, which hold the quantized codes: plain roles give the tier,
edge roles give the transition and its @deg) and writes roles-v3.txt and roles-spec-v3.json. Same
tier codes and boundary cells as step 2; only the role split changes. scenes.txt is not used: it
now holds the solver output (183 transitions per image, texture included), so make_roles.py run on
it would build the wrong boundary.

Minimal. A transition code XY needs, in each image, one piece per interior cell carrying XY
(its boundary cells). target_counts[XY] is the maximum over the three images, the smallest
count every image can meet with one histogram. Each image then adds (max - own) surplus pieces
of each code. A plain tier total is the tier's cell count minus its transition targets (tier
totals are equal across images), so the histogram is identical.

Localized. Interior plain tier cells split by distance to a boundary. X_near: 4-adjacent to a
transition cell of tier X (may take X's transition classes, weights 1/3/3). X_far: other interior
X cells (plain class only). Frame cells stay plain; edge roles are unchanged.
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))

from make_roles import COLS, ROWS, TIERS  # noqa: E402

REV = {v: k for k, v in TIERS.items()}  # "d" -> "D"

TIER_ORDER = "DML"
TRANS = ["DM", "DL", "MD", "ML", "LD", "LM"]
ALL_CLASSES = ["D", "DM", "DL", "M", "MD", "ML", "L", "LD", "LM"]
NEAR_WEIGHTS = [1, 3, 3]


def read_quantized(path: Path):
    """Per image: class grid and @deg grid, rebuilt from the step 2 role maps."""
    blocks, cur = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() in ("# A", "# B", "# C"):
            cur = []
            blocks.append(cur)
        elif line.strip() and not line.startswith("#") and cur is not None:
            cur.append(line.split())
    if len(blocks) != 3:
        raise SystemExit(f"{path}: expected three role grids, found {len(blocks)}")
    out = []
    for block in blocks:
        cls_grid, rot_grid = [], []
        for row in block:
            cr, rr = [], []
            for tok in row:
                role, _, deg = tok.partition("@")
                parts = role.split("_")
                if parts[1] in ("frame", "int"):
                    cls = REV[parts[0]]
                else:  # x_edge_y
                    cls = REV[parts[0]] + REV[parts[2]]
                cr.append(cls)
                rr.append(int(deg) if deg else 0)
            cls_grid.append(cr)
            rot_grid.append(rr)
        out.append((cls_grid, rot_grid))
    return out


def is_frame(x: int, y: int) -> bool:
    return y in (0, ROWS - 1) or x in (0, COLS - 1)


def neighbours(x: int, y: int):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS:
            yield nx, ny


def near_boundary(g, x: int, y: int, tier: str) -> bool:
    """True when a 4-neighbour is a transition cell whose own tier is `tier`."""
    return any(len(g[ny][nx]) == 2 and g[ny][nx][0] == tier for nx, ny in neighbours(x, y))


def spec_roles() -> dict:
    roles = {}
    for t in TIER_ORDER:
        low = TIERS[t]
        nbs = [n for n in TIER_ORDER if n != t]
        roles[f"{low}_frame"] = {"classes": [t]}
        roles[f"{low}_near"] = {"classes": [t] + [t + n for n in nbs], "weights": NEAR_WEIGHTS}
        roles[f"{low}_far"] = {"classes": [t]}
        for n in nbs:
            roles[f"{low}_edge_{TIERS[n]}"] = {"classes": [t + n]}
    return roles


def main() -> None:
    quant = read_quantized(HERE / "roles.txt")
    grids = [q[0] for q in quant]

    tier_tot = [Counter(c[0] for row in g for c in row) for g in grids]
    for t in TIER_ORDER:
        if len({tt[t] for tt in tier_tot}) != 1:
            raise SystemExit(f"tier {t} totals differ across images: {[tt[t] for tt in tier_tot]}")

    needs = []
    for g in grids:
        needs.append(Counter(g[y][x] for y in range(ROWS) for x in range(COLS)
                             if not is_frame(x, y) and len(g[y][x]) == 2))
    target = {c: max(n[c] for n in needs) for c in TRANS}
    for t in TIER_ORDER:
        target[t] = tier_tot[0][t] - sum(target[c] for c in TRANS if c[0] == t)
    counts = {c: target[c] for c in ALL_CLASSES}
    if sum(counts.values()) != ROWS * COLS:
        raise SystemExit("target counts do not sum to the cell count")

    spec = {
        "_note": "Step 4: surplus transitions only where needed. target_counts = per code the max over "
                 "maps of boundary cells; plain tiers take the rest of their totals. *_near (interior, "
                 "next to a transition of the same tier) may take the tier's transition classes; *_far "
                 "take their plain class only. Frame and edge roles as in step 2.",
        "roles": spec_roles(),
        "target_counts": counts,
    }
    (HERE / "roles-spec-v3.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    lines = ["# Step 4 role maps, experiment 005 (v3). A = cat, B = sailboat, C = tree.",
             "# Roles: x_frame frame cells (plain tier); x_near / x_far interior plain tier cells, near a",
             "# transition of the same tier or not; x_edge_y interior transition cells (own x, neighbour y),",
             "# with @deg = orientation carried into the scene token.", ""]
    stats = []
    for k, (g, rots) in enumerate(quant):
        name = "ABC"[k]
        lines.append(f"# {name}")
        near = Counter()
        far = Counter()
        for y in range(ROWS):
            row = []
            for x in range(COLS):
                cls, rot = g[y][x], rots[y][x]
                if is_frame(x, y):
                    if len(cls) != 1:
                        raise SystemExit(f"frame cell ({x},{y}) of map {name} is a transition: {cls}")
                    row.append(f"{TIERS[cls]}_frame")
                elif len(cls) == 1:
                    kind = "near" if near_boundary(g, x, y, cls) else "far"
                    (near if kind == "near" else far)[cls] += 1
                    row.append(f"{TIERS[cls]}_{kind}")
                else:
                    row.append(f"{TIERS[cls[0]]}_edge_{TIERS[cls[1]]}@{rot}")
            lines.append(" ".join(row))
        lines.append("")
        surplus = {c: target[c] - needs[k][c] for c in TRANS}
        print(f"map {name}: boundary need {dict(needs[k])}")
        print(f"  surplus {dict(surplus)} total {sum(surplus.values())}")
        print(f"  interior plain cells near {dict(near)} far {dict(far)}")
        stats.append(surplus)
    (HERE / "roles-v3.txt").write_text("\n".join(lines), encoding="utf-8")

    print(f"target_counts {counts}")
    print(f"wrote {HERE / 'roles-v3.txt'} and {HERE / 'roles-spec-v3.json'}")


if __name__ == "__main__":
    main()
