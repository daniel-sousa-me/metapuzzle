# B-04 — Risks and prototype tests (direction B)

## Failure modes, ranked

1. **C does not read as koi.** The pond is the most abstract scene, and round gold blobs on teal may read as "autumn leaves on water" or as noise. The pale border cells on C's sides, forced by the border counts, add clutter. *Fixes, in order:* an elongated blotch mask for gold mixes; cluster koi into 3–4-piece groups; move C's border `BL` toward the top corners (this costs about 2 cells of carry-over with A).
2. **A and B share the "gold above, dark below" value plan.** Both have a bright upper-middle mass over a dark lower half, so the blurred thumbnails may look alike even though the subjects differ.
3. **Hard seams show the grid** in C (14 edges), mainly stones against water and sky against teal.
4. **Family-level carry-over.** The top row is pale and the bottom row green in all three scenes. Players may keep the border loosely sorted between solves. This is a border-rule artefact, not a class one.
5. **Too few distinguishable pieces.** 14 classes over 80 pieces means some classes have 9–12 identical-looking members (BL, TE, NT, OC). Solving within a class is pure trial and error.
6. **Mixes all look alike.** Five mixes share the same blotch grammar, so players may not sort them quickly.

## Tests for the first prototype

Render all three scenes with the class spec in B-02, at 800 px tall and as a 100 px thumbnail, plus a contact sheet of all 80 pieces.

| # | Test | Method | Pass |
|---|---|---|---|
| T1 | **Blind recognition** | Show each full image, in random order, to 5 or more evaluators (people or a vision model) who are not told the subjects. Ask: "What is this a picture of? Name it in 3 words." No hints, no multiple choice. Then show all three side by side and ask whether they are the same picture rearranged. | Each scene is named correctly (sunflower / sunset over sea / fish or koi pond) by at least 4 of 5. No evaluator calls two scenes "the same". |
| T2 | **Thumbnail distinctness** | Blur each image (Gaussian, σ = ½ piece) and compute pairwise colour-histogram distance per 2×2-piece block. Ask evaluators to match blurred to unblurred. | Matching is correct ≥ 90%. A–B block distance is above the median across pairs. |
| T3 | **Grid visibility** | Ask evaluators at normal viewing distance: "Do you see a grid?" Separately, compute edge energy along cut lines against cell centres. | At most 1 in 5 reports a grid. Cut-line energy is ≤ 1.3× interior energy. |
| T4 | **Feature reinterpretation** | Crop `SU`, `DK` and `DT` with one ring of neighbours from each scene and ask "what is this?" | Answers differ by scene for `DK` and `DT` in at least 2 of 3 scenes. |
| T5 | **Piece sortability** | Shuffle the contact sheet and have evaluators sort it into piles. | At least 10 piles found. Mixes are not confused with each other more than 20% of the time. |
| T6 | **Carry-over regression** | The script in B-03 runs in CI: histograms, border counts, class carry-over ≤ 20% per pair, largest carried patch ≤ 3, hard seams ≤ 10% of edges per scene. | All green. |
| T7 | **Rotation mode** | Re-run with `rotation="quarter"` and let the optimizer rotate mixes and fields. | T1 and T3 do not get worse, which confirms that "non-directional" holds. |

**Decision rule.** If T1 fails only for C, try fix 1 above before changing the trio. If A and B are confused (T2), change B's value plan first: put the glow band lower and use more `CR`, rather than touching A.
