"""Step 2: role maps and roles spec from the quantized codes in scenes.txt (written by quantize.py).

Each cell becomes a role:
- frame cell (board edge or corner), plain tier code -> role d_frame / m_frame / l_frame, which
  takes only that tier's plain class. Frame cells are always plain (a scene cannot carry an
  orientation suffix on the frame), so the frame transitions are not in the roles;
- interior plain tier code D / M / L -> d_int / m_int / l_int (may take its tier's transition
  classes too, as texture);
- interior transition code XY (own X, neighbour Y) -> x_edge_y, which must take class XY, with
  the orientation suffix of the cell (d_edge_m@90), passed to the scene token.

Writes roles.txt (three grids, scene layout) and roles-spec.json (no target_counts: the solver
finds a common histogram).
"""
import json
from pathlib import Path

from metapuzzle.scene import load_scenes

HERE = Path(__file__).resolve().parent
TIERS = {"D": "d", "M": "m", "L": "l"}
ROWS, COLS = 25, 20
WEIGHTS = {"D": 6, "DM": 1, "DL": 1, "M": 6, "MD": 1, "ML": 1, "L": 6, "LD": 1, "LM": 1}


def role_of(cls: str) -> str:
    own = cls[0]
    if len(cls) == 1:
        return f"{TIERS[own]}_int"
    return f"{TIERS[own]}_edge_{TIERS[cls[1]]}"


def spec_roles() -> dict:
    roles = {}
    for own, low in TIERS.items():
        int_cls = [own] + [own + nb for nb in "DML" if nb != own]
        roles[f"{low}_int"] = {"classes": int_cls, "weights": [WEIGHTS[c] for c in int_cls]}
        roles[f"{low}_frame"] = {"classes": [own]}
        for nb in "DML":
            if nb != own:
                roles[f"{low}_edge_{TIERS[nb]}"] = {"classes": [own + nb]}
    return roles


def main() -> None:
    maps = load_scenes(HERE / "scenes.txt")
    roles = spec_roles()
    spec = {
        "_note": "Step 2: frame cells take their plain tier only (scene rule: no suffix on the frame). "
                 "Interior tier cells may take their tier's transition classes (texture); "
                 "interior edge roles take only their transition class.",
        "roles": roles,
    }
    (HERE / "roles-spec.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    lines = ["# Step 2 role maps, experiment 005. A = cat, B = sailboat, C = tree.",
             "# Roles: x_frame frame cells (plain tier); x_int interior plain tier cells; x_edge_y interior",
             "# transition cells (own x, neighbour y), with @deg = orientation carried into the scene token.", ""]
    interior_tr = {}
    for k, m in enumerate(maps):
        name = "ABC"[k]
        lines.append(f"# {name}")
        interior_tr[name] = 0
        for y in range(ROWS):
            row = []
            for x in range(COLS):
                cls, rot = m.cls[y][x], m.rot[y][x]
                frame = y in (0, ROWS - 1) or x in (0, COLS - 1)
                if frame:
                    if len(cls) != 1:
                        raise SystemExit(f"frame cell ({x},{y}) of map {name} is a transition: {cls}")
                    row.append(f"{TIERS[cls]}_frame")
                elif len(cls) == 1:
                    row.append(role_of(cls))
                else:
                    interior_tr[name] += 1
                    row.append(f"{role_of(cls)}@{rot}")
            lines.append(" ".join(row))
        lines.append("")
    (HERE / "roles.txt").write_text("\n".join(lines), encoding="utf-8")

    for name in "ABC":
        print(f"map {name}: interior transition cells {interior_tr[name]}")
    print(f"wrote {HERE / 'roles.txt'} and {HERE / 'roles-spec.json'} ({len(roles)} roles)")


if __name__ == "__main__":
    main()
