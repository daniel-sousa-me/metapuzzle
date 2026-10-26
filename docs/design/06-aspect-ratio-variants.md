# 06 — Aspect-ratio variants (input to the second experiment)

The owner has allowed the three images to differ in frame as long as the piece count is the same. This is the strongest available fix for the main weakness of the 8×10 set: about 55 of 80 cells keep the same class at the same position (03, 04). Different frames move every band to a different place, so sky and meadow blocks can no longer be carried over.

## Proposed frames for 96 pieces

| Scene | Frame | Why it gains |
|---|---|---|
| A — The Lone Tree | **8 × 12 portrait** | A tree is vertical. The crown can grow to about 6 wide × 4 tall with a proper underside, the trunk can be 3–4 cells and the horizon can sit low, around r8, with a short meadow. |
| B — Isle and Sail | **16 × 6 panorama** | A seascape is horizontal. The horizon row gets 16 cells, which removes the "horizon capacity" bottleneck (03, coupling 2). The island can sit at one end and the sail near a third of the width, with open sea between. B stops looking like A. |
| C — Snow Peak | **12 × 8 landscape** | A broad massif with symmetric flanks (more S\ and F\), a row of firs and a lake that spans the width. |

## Implications

- **Histogram.** Still identical (one inventory). With 96 cells, the extra 16 cells should go mostly to transitions and features rather than to sky and meadow. A suggested budget is SK about 22, ME about 18, DP about 16, FO about 14, transitions about 18 and features about 8. The panorama needs proportionally more DP and HD; the portrait needs more ME and FO. Balance comes from giving each scene a secondary use of the other scenes' bulk materials (e.g. B's foreground grass bank absorbs ME).
- **Borders: this breaks flat-edge pieces.** The perimeters differ. 8×12 and 12×8 have 36 edge pieces, but 16×6 has 40. Side lengths differ too (top side 6 vs 10 vs 14 non-corner pieces). Flat-edged border pieces therefore cannot be consistent. The second experiment needs **frameless cutting**: every piece interlocks on all four sides, and the assembled image sits in a tray or is simply left with a knobbed outline. The outer border of each scene then becomes ordinary interior pieces whose art must tolerate being at the image edge. Fields do; features near the edge are fine.
- **Orientation.** 8×12 vs 12×8 is a 90° frame turn. In no-rotation mode pieces keep their orientation, so "up" is the same in all frames, which fits upright landscapes. Rotation mode would allow a scene to use the transposed frame, but it is not needed here.
- **Skyline coupling.** The skyline-tile multiset must still match across scenes, but the horizon rows now have 8, 16 and 12 cells, so the per-scene budgets fit far more easily.
