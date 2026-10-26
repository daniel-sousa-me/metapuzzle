# Decision log

Decisions made with the project owner. Later entries may refine earlier ones.

## 2026-10-26 — Initial framing (owner-confirmed)

1. **Deliverable**: a software toolkit plus digital prototypes. Code generates piece arrangements, procedural artwork, rendered images of all three solutions, and metrics. Start at roughly 60–100 pieces, scale toward 500. Design notes live alongside the code.
2. **Art method**: procedural, code-drawn artwork (SVG and/or raster) built from a designed visual vocabulary. No AI image generation.
3. **Subjects**: the three images should be recognizable scenes (nameable subjects), emerging from a shared vocabulary of marks.
4. **Rotation**: whether pieces may rotate between solutions is an experiment variable. Build both the no-rotation and 90-degree-rotation modes and compare.

## 2026-10-26 — Piece geometry is an open experiment (owner note)

The owner asked that unconventional piece shapes (which permit more rotations, e.g. hexagons or triangles) be explored rather than ruled out at the start. Consequence: the arrangement engine is built geometry-agnostic (slots + adjacency graph + slot/piece type compatibility + orientation group), so square-no-rotation, square-with-rotation, hexagonal and other tilings can be compared on identical metrics. A narrowing decision on geometry will be made after the first round of prototype results, not before. See docs/design/05-piece-geometry.md.

## Working method

Think broadly during experiments, then make explicit narrowing decisions and record them here, so scope converges on a workable result.
