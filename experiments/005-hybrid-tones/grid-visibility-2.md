# Grid visibility review 2 — hybrid tone-field v5 full render (run-full-v5)

- About 90% of interior grid-line length is invisible in C (tree); the exceptions are the ground's top edge, which snaps to cell lines at a few places, and the edges of foreign-colour patches.
- No same-texture seams anywhere: the speckle fields join invisibly.
- Type (d) patches dominate: about 40 in C and 25 in B, hard-edged one- or two-cell blocks of olive, navy or cream inside sky, canopy, ground or hull. They read as mistakes. These are the surplus transition pieces.
- The canopy outline is ragged but its steps are cell-sized, so the rhythm partly reveals the grid; the sail's diagonal is a regular staircase (the clearest grid cue), which the new `diag` contour pattern is meant to fix.
- Verdicts: C 4/5, B 4/5, driven almost entirely by the surplus patches. Most effective change: remove the tile-sized foreign-colour blocks (match boundary budgets so there is no surplus; feather or spread any residue).
