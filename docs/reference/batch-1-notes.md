# Reference images, batch 1 (owner-generated, 2026-10-26)

Five images were returned for the prompts in docs/image-prompts.md: two cats, two sailboats, one tree, all in a cream / olive / navy / rust / pale-blue torn-paper mosaic. The images themselves are not stored in the repository; these notes record what we take from them.

## Observations

1. **Silhouette edges are crisp and follow chip boundaries.** No haloes, no feathering; the raggedness comes from the chip shapes themselves. Our marching-tile transitions (mid-edge-pinned ragged boundaries) are the right mechanism; the boundary should be ragged at chip scale, not at piece scale.
2. **A fourth tone exists: dark chips scattered on cream.** The tree canopy is individual navy leaf chips on a cream ground, roughly 50–60% coverage, not a solid dark mass. This reads as foliage and would re-read elsewhere as a flock, gravel, blossom or a crowd. Add it as a class ("scatter" tier) between dark and light.
3. **Single-piece motifs on the background.** The rust sun disc, the five-petal flowers (rust and pale blue), the blue cloud chips and the scattered rust/blue chips are self-contained marks on cream. As piece classes they are placeable anywhere in a light region, so they cost nothing in adjacency, while giving the solver distinctive pieces and the picture charm. Counts are easily matched across the three images.
4. **Patterned mid-tone.** The sea is olive with cream wave fragments (short horizontal lenses). As a class it reads as sea under the boat and as furrows or meadow texture elsewhere: a context-dependent reuse.
5. **Chip scale.** Chips are about 1/40 of the image width in the background and larger (1/25) inside the figure; i.e. roughly 2–4 chips per piece side at 20 columns. Our dab scale (1/6–1/4 of a piece) is in range.
6. **The grass/sea band boundary** is straight but hidden by the texture change being chip-aligned; in our grammar it still needs transition pieces (or a wavy horizon).

## Consequences for the lexicon

- Tiers: D (solid navy), S (navy chips scattered on cream, new), M (olive), M-wave (olive with cream lenses, new variant), L (cream with sparse rust/blue chips).
- Motif classes on L: sun disc (rust), flower (rust or blue), cloud chip (blue), small leaf (olive). Same counts in all three images; the role solver places them in light regions.
- Keep transitions between every adjacent pair of tiers that occurs; S next to L needs no transition (it is already a mixture), which reduces the transition budget.
