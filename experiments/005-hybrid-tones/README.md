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


## Step 2

**Solve.** `make_roles.py` turns `scenes.txt` into `roles.txt` and `roles-spec.json`. Frame cells take their plain tier. Interior plain cells may take their tier's transition classes (texture). Interior transitions keep their orientation as `@deg`. No target counts. `roles-to-scenes --rotation quarter --restarts 8` finds a common histogram in about 1 s; `validate_scenes` passes.

**Histogram (all three images):** D 21, DM 24, DL 31; M 69, MD 26, ML 29; L 227, LD 36, LM 37.

**Frame.** The quarter border rule needs common edge and corner pools, so `quantize.py` step 2b equalizes their tiers (edge 1/30/55, corners 0/2/2). It shifted 8, 8 and 4 cells (`quantize-report.txt`).

**Interior transitions** (cat / sailboat / tree): 134 / 123 / 128 on edge roles; 49 / 60 / 55 texture.

**Boundaries on cuts.** Interior: 0. Frame: 28 (10 / 8 / 10), coded plain. Limitation: `validate_scenes` rejects suffixes on frame cells; fix in the engine later.

**Scene metrics** (`scene-metrics.txt`, gates fail). Same position A-B / A-C / B-C: 45.8 / 44.4 / 43.2%, or 34.1 / 30.7 / 33.0% excluding the dominant light class. 2x2 reuse plain/rotated: 0.71/0.81, 0.75/0.85, 0.73/0.89.

Light cells (45% of each map) dominate same-position overlap. Proposal: count matches only over cells whose class is not the most common class of either map, dividing by that count.
