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

## 2026-10-26 — Square lattice is the base (owner clarification)

The base tiling is a square lattice; hexagonal or triangular tilings are not pursued. "Unconventional shapes" means individual piece cuts that deviate from a square (e.g. curving toward a triangle) while still occupying one lattice cell. For now the prototypes use plain squares; shape deviation within the lattice is a later-stage experiment to revisit once the visual grammar is validated.

## 2026-10-26 — Solutions may have different aspect ratios (owner)

The three images need not share an aspect ratio; only the piece count is fixed. Consequences:
- The engine takes one board per solution (equal slot counts, possibly different cols×rows) instead of one shared board.
- Different frames have different perimeter lengths, so border inventories only match if edge pieces can rotate or if flat-sided pieces may sit in the interior (see docs/IDEAS.md). These ideas are now linked.
- Piece counts with several factorizations become attractive: 96 = 8×12 = 12×8 = 16×6 for prototypes; 480 = 20×24 = 30×16 = 40×12 or 504 = 21×24 = 28×18 = 36×14 near the 500 target. Final count is open; "500" is a target, not a contract.
- Plan: prototype 1 uses identical frames (simplest, isolates the visual-grammar question); prototype 2 varies frames (portrait / landscape / panorama) and compares distinctiveness and border cost.

## 2026-10-26 — Image-generation models as an occasional reference channel (owner)

Image models are not used by the toolkit. Once style, elements and scenes are settled, the owner can run a small number of prompts manually and return the images as creative reference for the design. This is a slow channel: use it rarely (a batch of two or three prompts at a milestone), never block work on it, and record the prompts sent in docs/IDEAS.md or the experiment log.
