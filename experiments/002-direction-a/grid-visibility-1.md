# Grid visibility review 1 — direction A baseline (run-none)

Evaluator: a fresh agent shown solution-A.png, its faint-grid variant, and solution-C.png.

## Findings

- Nearly every visible straight edge in A sits on an interior grid line. Of 16 interior grid lines, 7 (about 44%) show nothing; the rest are partly or fully visible.
- Causes, by frequency: (a) a color boundary landing exactly on a piece edge (trunk sides, navy block top, both full-width horizon bands); (c) a shape ending abruptly at a piece edge (navy block ends, cloud bottoms, trunk bottom). No (b) same-texture seams were seen: the stochastic textures join invisibly.
- C is worse (verdict 4/5) because more of its composition is rectangular and grid-aligned (brown block, green blocks, white block). A scored 3/5.

## Conclusion

The textures work; the class layout does not. Any boundary between two classes that falls on a cut line is visible. The lexicon only provided in-piece transitions for a few pairs (sky/foliage, sky/snow) and let other pairs (deep/meadow, meadow/foliage, rust/anything) meet at cuts. Rule for the next lexicon: every boundary between visually distinct classes must occur inside a piece (two-material pieces with a ragged boundary), or the grammar must avoid hard regions altogether (density fields of mixed pieces).
