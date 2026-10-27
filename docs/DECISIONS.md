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

## 2026-10-26 — Carry-forward grammar: hybrid tone-field (experiment 005)

After three grammars were rendered and blind-tested (direction A "Dapple Mosaic", direction B "Garden Terrazzo", density fields), the hybrid tone-field grammar is the one to develop further:
- Subjects are designed as bold three-tier tone maps (dark / mid / light) with matched tier areas; one piece histogram serves all three because tiers are quantized by fixed thresholds and equalized by moving a few near-threshold cells.
- Every tier boundary lies inside a two-material transition piece (masked ragged blob), so no colour step lands on a cut; frame cells may carry transitions since 2026-10-27 (engine supports forced rotations on the frame in quarter mode).
- The role-map solver gives the histogram slack by letting interior regions absorb surplus transition pieces as texture variation.
- Quarter rotation is used; all classes are non-directional.
First render at 20×25: piece-level shared adjacencies 0/0/0; distinctiveness 4/5; the tree was recognized blind, the cat and boat were not (silhouette fixes in progress). Directions A and B are retired as scene designs; their lexicon mechanisms (masked transitions, context-dependent readings, role maps) are kept.

## 2026-10-26 — Scene-level gates are difficulty indicators, not hard gates, for the tone-field grammar

The scene-level metrics (same-position overlap, 2×2 window reuse, transferable blob) were built to catch the class-layout carry-over of direction A. For a tone-field picture they are inherently high because 40–60% of pieces are near-identical background. Whether that lets a player transfer assembled chunks between solutions depends on the physical connectors:
- With conventional distinct cuts (each tab shape fits only its mates), a chunk assembled in image A physically fits in image B only if those same pieces are neighbours in B, which the piece-level optimizer already prevents (0 shared adjacencies). Chunk transfer is then impossible by construction, and the scene-level numbers only describe how much the previous solve helps a player guess where a piece's *kind* goes (a difficulty question).
- With fully interchangeable connectors, chunk transfer becomes possible and the scene-level gates would matter again.
Decision: plan for distinct conventional cuts; keep reporting the scene-level metrics as difficulty indicators; the hard gates for the tone-field grammar are piece-level shared adjacency (< 5%, stretch 0), the blind recognition test and the grid review. Open question for the engine: three solutions force side shapes into mating classes (a side meets up to three different partners), which limits how distinct connectors can be; this is being analysed (connector mating classes).

## 2026-10-27 — Owner steers: lines first, unique solutions, relaxed adjacency target

1. **Lines first.** Explore shape and piece mapping with black lines on a white background (contours only), and add fills, textures and details afterwards. The marching-tile boundary paths become stroked lines in an "ink" class spec; every scene can be rendered in ink or in full.
2. **Each image must have a unique solution, with few wrong local solutions.** Pieces must be different enough, mechanically (connector mating classes as small as possible; see experiment 010) and visually (distinguishing marks within a region), that a player cannot assemble a plausible wrong patch. This becomes an evaluation item: false-fit ratio from `metapuzzle connectors`, plus a visual-ambiguity check.
3. **Shared adjacency: "not practically reusable" replaces "zero".** It is not required that most adjacent pairs become non-adjacent; it is enough that a finished image cannot be deduced from or worked from another in practice. Working target: no transferable cluster larger than 3 pieces and shared adjacencies below about 10% per pair; the solver may trade a few shared adjacencies for distinct connectors.

## 2026-10-27 — Piece count is free; working grid moves to about 1000 pieces (owner)

The 500-piece target was a guess that smaller would be easier; renders show the opposite (coarse silhouettes, rare tile cases, thick transition bands). The owner has freed the piece count and said computation time is not a constraint. Decision: the working grid for subject design becomes about 1000 pieces (e.g. 27×38, or per-picture frames of about 1000 cells since mixed frames are supported); 500 is kept as a comparison point; 1500–2000 may be tried if resolution still limits recognizability. Solver and render runs may take minutes without concern.
