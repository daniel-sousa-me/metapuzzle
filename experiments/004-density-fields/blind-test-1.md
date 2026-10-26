# Blind recognition test 1 — density-field mosaic (run-quarter, 20x25)

Evaluator: fresh agent, shown only the three solution PNGs. Intended: A cat, B sailboat, C tree.

- **A**: "a dark, vaguely figure-like silhouette standing in a field of olive, tan and pale-blue blocks." Figure/bell 2/5. Not recognized as a cat.
- **B**: "an abstract split scene, light top, dark band below, a vertical column rising from the middle." Column 3/5, horizon 3/5. Boat not named; mast and hull/sea structure seen.
- **C**: "a tree on a ground strip, with a dark round canopy and a trunk." Canopy 4/5, trunk 4/5, ground 3/5. Recognized.
- **Comparison**: "not the same picture; three variations on one scheme" (same palette, grid, speckle). Distinctiveness 4/5.
- **Grid**: 5/5 for all three ("cell edges and uniform colour blocks visible across the whole frame").
- **Squinting**: C clearly clearer; B somewhat; A marginally.

Conclusion: tone-map quantization gives genuinely different subjects from one histogram (first pass of the distinctiveness criterion) but fails the grid criterion completely. The cat silhouette is too subtle at 20x25 with four scattered light classes. Carry forward the structure, fix the grid with in-piece transitions and a single dominant ground class (experiment 005).
