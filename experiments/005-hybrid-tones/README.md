# 005 hybrid tones

**Idea.** Each cell has a tier: D (tone < 0.35), M (0.35 to 0.65), L (> 0.65). A tier-boundary cell carries its own tier plus the neighbour's tier on one side, so the boundary falls inside a piece. One rotatable class serves all four sides.

**Targets** (`make_targets.py`): cat in profile on a mid floor, sailboat with mid sea, tree with mid ground. Shape sizes are searched in code until counts match.

**Tier counts** (D / M / L): cat 76 / 124 / 300; sailboat 76 / 124 / 300; tree 76 / 124 / 300.

**Transition cells**: cat 140 (62 multi-sided), sailboat 120 (18), tree 136 (46).

**Equalization** (`quantize.py`, log in `quantize-report.txt`)
- Tiers already exact, so no cell moved (nearest-threshold rule in code).
- Rule (i) cannot apply as written: a plain cell has no other-tier neighbour to swap to. Applied instead: a multi-sided transition may take another side if its tone difference is at least 0.1. Swaps: cat 0, sailboat 4, tree 2.
- Rule (ii): classes ignore the side; scene tokens carry it as `@rotation`.
- **Not achieved:** the nine class histograms differ. Pairwise L1: cat-sailboat 126, cat-tree 10, sailboat-tree 124. The sailboat hull covers the horizon and its mast sits on sky.

**Scene metrics** (`scene-metrics.txt`, gates fail): same-position 63.0 / 58.2 / 58.0% (A-B, A-C, B-C); 2x2 reuse plain/rotated 0.77/0.86, 0.83/0.89, 0.82/0.91. Light cells (60%) drive these.

**Class codes** (`@0` neighbour top, `@90` right, `@180` bottom, `@270` left)
- `D`, `M`, `L`: plain cell.
- `DM`: dark cell, mid neighbour at the canonical side.
- `DL`: dark cell, light neighbour.
- `MD`: mid cell, dark neighbour.
- `ML`: mid cell, light neighbour.
- `LD`: light cell, dark neighbour.
- `LM`: light cell, mid neighbour.
