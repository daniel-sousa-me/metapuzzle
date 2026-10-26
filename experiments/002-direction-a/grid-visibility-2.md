# Grid visibility review 2 — direction A after texture fixes (run-none-v2)

- About 44% of interior grid lines invisible in A (unchanged from review 1). Dominant cause remains (a): large color regions snapping to cell edges (navy band top/sides, trunk sides, canopy top, the two full-width horizon bands). No same-texture seams.
- The sky-to-foliage and sky-to-hill boundaries are now ragged and inside pieces (the masked transitions work). The navy/green and green/lawn bands are still straight on piece edges because the lexicon has no transition classes for those pairs.
- Verdicts: A 3/5, B 4/5. Recommended fix: every class boundary must be inside a transition piece (generate transitions for all pairs), or avoid full-width bands.
