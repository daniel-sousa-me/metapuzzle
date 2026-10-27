# Ideas backlog

Owner-suggested or agent-suggested ideas that are not yet decisions. Each entry says what it is, what it might buy, and what it would cost. Promote to docs/DECISIONS.md when adopted.

## Flat-sided ("frame-shaped") pieces in the interior (owner, 2026-10-26)

Some pieces with one or two flat sides sit inside the picture, with their flat sides meeting another flat side, forming an internal seam. The border inventory then exceeds the perimeter, so a piece that is on the frame in one image can be interior in another, and vice versa.

- Buys: relaxes the strongest constraint we found (border pieces locked to the frame in all three images); a well-known "false edge" trick that makes solving more interesting; the seam can be hidden by the artwork.
- Costs: slightly weaker mechanical connection along seams; the solver must pair flat sides with flat sides; artwork must not reveal seams.
- Engine requirement: edge profiles per side ("tab", "blank", "flat"), with "flat" mating only with "flat" or the board boundary; a placement is valid when all mating sides are compatible.

## Corner order keys the solution (owner stretch goal, 2026-10-26)

The four corner pieces are always corners, but their cyclic order (up to rotating the whole puzzle) differs between the three solutions. There are 6 such orders, so three solutions can each have a distinct one, and choosing a corner order could uniquely determine which image is being built.

- Buys: a memorable mechanic; a natural way to tell the player which puzzle they are solving; guaranteed that corners are not "shared structure".
- Costs: corner pieces must rotate between solutions (90-degree steps), so their artwork must read in any orientation, or be deliberately ambiguous; mechanically the corners might be keyed.
- Engine requirement: corner pieces with allowed rotations {0,90,180,270} even in otherwise no-rotation mode; an optional constraint that the three solutions use pairwise distinct corner cyclic orders.

## Frame tray instead of border pieces (geometry brief, 2026-10-26)

All pieces are interior-shaped and the puzzle sits in a tray. Removes border constraints entirely; changes the product form. Kept as a control variant in the engine ("tray" board). *Adopted 2026-10-27 as the product form (DECISIONS, product form: tray).*

## Shape deviation within the square lattice (owner, 2026-10-26)

Individual piece cuts that deviate from a square while occupying one lattice cell. Later-stage experiment; see docs/design/05-piece-geometry.md.

## Chip-signature sub-classes for solvable backgrounds (manager, 2026-10-27)

Background pieces within one tone region are visually interchangeable, so placing them is trial-and-error. Give the light (and mid) tiers sub-classes that differ only in their sparse interior chips (rust, blue, olive, none, mixed) and let each scene arrange those sub-classes in a different low-frequency pattern (e.g. rust chips gather top-left in A, along the horizon in B, around the figure in C). Chips stay inside pieces, so no adjacency constraint is added, but a player can sort by chip colour and narrow where a piece belongs, and the three images get a second, subtler layer of difference. Implemented as classes in the spec and roles in the scene files; counts match automatically via the role solver. *Implemented as pipeline v4 (011, run-full-v4): shared 0/1/0 and T9 still 2/5 (FINDINGS 25); the motif vocabulary (docs/design/10) is the follow-up.*

## Piece count vs. contour vocabulary (owner question, 2026-10-27)

At 500 pieces (20×25) silhouettes are coarse (a cat's ears are two cells). Two ways to gain resolution: (a) more pieces, e.g. 750 (25×30) or 1000 (25×40), which doubles contour resolution and removes rare tile cases at the cost of a bigger product; (b) richer transition tiles at 500 pieces: tips, bumps, notches and diagonals inside one piece, each a budget item that all three images must use equally often, so an ear tip in one picture is a sail corner or a leaf tip in another. Plan: run the 005 subjects at 750 and 1000 pieces as evidence, and add the contour vocabulary to the subject-design brief; the product target stays 500 unless the owner decides otherwise. *Superseded: the working grid is 27x38 (1026 pieces), adopted 2026-10-27 (DECISIONS).*

## Cross-class seams and frame-histogram matching (2026-10-27)

A standard rectangular border needs the three pictures' frame cells to use the same multiset of piece classes (with rotation, any side). Two ways to get there: (a) the subject designer's annealer matches the frame class histogram across pictures as one more budget term (frame cells are only about 12% of the board and mostly background, so background lines can absorb it); (b) the engine allows seam partners of different classes (a seam pair is just two flat-sided pieces at adjacent interior cells whose classes the scene prescribes), which removes the same-class restriction that currently makes seams infeasible for mixed frame mixes. (a) is cheaper and is being added to the designer; (b) is an engine improvement for later. *Status: standard-border runs at 27x38 failed on same-class seam parity (011 border-check, FINDINGS 29), so (b) is now the remaining route.*

- **Cut-overlay render mode (for the border decision).** Renders draw no piece outlines, so the
  straight interior seams of a standard-border solution are invisible in the triptych although
  they would show in the physical puzzle. A `--cut-overlay` option drawing every piece outline
  (tabs, blanks and flat seams) at low opacity would let the grid review judge seams and tab
  pattern tells before manufacturing. Needed before choosing tray vs standard at the v4 tiers.
