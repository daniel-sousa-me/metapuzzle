# Blind recognition test 1 — direction A baseline (run-none)

Evaluator: a fresh agent shown only solution-A/B/C.png, not told the subjects.
Intended subjects: A "The Lone Tree", B "Isle and Sail", C "Snow Peak".

## What the evaluator saw

- **A**: "A stylized landscape with a tall green tree and a rust-colored trunk containing a small door, under a sky with a sun and cloud." Tree canopy 5/5, trunk 4/5, grass 5/5, sky 5/5, sun 4/5. The knothole read as a door. The navy "deep" band behind the canopy looked like an unexplained rectangle. Tile-grid score 1/5 (reads as one image).
- **B**: "The same landscape as A, but many shapes are broken into hard-edged rectangles." No island, no sail, no boat recognized. Rectangular cells of about one piece dominate. Tile-grid score 4/5.
- **C**: "A wide, low landscape with a navy hill band, a rust structure with a door at the bottom center, and blocky green bushes." No mountain, no snow, no hut recognized. The white fleck "has no clear role". Tile-grid score 3/5.

## Comparison

"These are variations of one picture." Shared: speckled sky, sun, cloud, navy band, green strip, grass, rust structure, door. Mutual distinctiveness 3/5.

## Conclusions

1. Only scene A is recognized as intended. B and C are read as rearrangements of A, which is exactly the failure mode the handoff warns about (section 9: "three finished images that look insufficiently different").
2. Hard class boundaries landing on piece edges (deep/meadow, rust/anything, foliage blocks in B and C) make the grid visible. The lexicon allows only close-valued pairs at cuts, but dark-navy "deep" against light-green "meadow" is not close-valued, and several such cuts occur.
3. The intended hero structures (island, sail, summit, hut) are 3–4 cells across and built from the same transition pieces as scene A's tree crown, so they are not distinguishable at this scale.
4. The class-level carry-over metrics (66–71% same-position overlap) predicted this outcome. Those metrics should be a gate on scene designs before rendering.
