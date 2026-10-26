# metapuzzle

A design toolkit for a "multi-solution jigsaw puzzle": one physical set of 500
printed pieces that can be rearranged into three distinct images. The pieces are
printed once and never change. Each solution uses every piece exactly once, and
the arrangements are chosen so that almost no pair of neighboring pieces in one
solution is still a neighboring pair in another.

The toolkit generates piece arrangements, procedurally drawn artwork (SVG and
raster), rendered images of all three solutions, and adjacency metrics. Work
starts at roughly 60 to 100 pieces and scales toward 500.

## Repository layout

- `src/metapuzzle/` - the Python package (arrangement, artwork, rendering).
- `tests/` - pytest suite.
- `docs/` - `HANDOFF.md` (concept and constraints) and `DECISIONS.md` (decision log).
- `docs/design/` - design notes that live alongside the code.
- `experiments/` - scratch experiments; `experiments/**/out/` is git-ignored.
- `gallery/` - rendered prototype images that are meant to be committed.

## Status

Early prototyping. The package is a skeleton with no puzzle logic yet.

## Further reading

- [docs/HANDOFF.md](docs/HANDOFF.md) - project goal, design principles and open questions.
- [docs/DECISIONS.md](docs/DECISIONS.md) - decisions made with the project owner.
