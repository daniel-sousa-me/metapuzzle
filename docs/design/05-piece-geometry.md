# 05 — Piece geometry and rotation

Status: decided direction, 2026-10-26.
Scope (from the owner): the base tiling is a **square lattice of plain square pieces**. Rotation is the experiment variable (DECISIONS #4). Pieces whose cut deviates from a square while still occupying one cell are a later-stage idea. Hexagons and triangles were considered and rejected.

## 0. Headline findings

1. **The combinatorics are easy, so the art decides.** Two random arrangements of a 25×20 grid already share only about 7 of 955 neighbor pairs. A plain swap-based local search reached **0/0/0 shared adjacencies** (A–B, A–C, B–C) within a few thousand swaps in every square configuration below, with and without rotation. Section 2.3 of HANDOFF ("zero shared adjacencies") is not the binding constraint. Visual quality is.
2. **The border is the only real combinatorial limit.** It is also an artistic one: the same border fragments frame all three images.
3. **Rotation buys two things:** border freedom, and a small number of deliberate double readings of marks. It costs legibility and multiplies false fits. It should be a per-piece privilege set by the art, not a global switch.

Shared adjacency here means an unordered piece pair that is adjacent in two solutions, regardless of which sides touch. Zero pairwise sharing automatically means no shared clusters of any size.

## 1. Square lattice, no rotation (implement first)

### Counts

| Size | Pieces | Corners | Other border | Interior | Internal adjacencies | Random overlap per pair |
|---|---|---|---|---|---|---|
| 25×20 | 500 | 4 | 82 | 414 | 955 | ≈7.3 |
| 10×8 (prototype) | 80 | 4 | 28 | 48 | 142 | ≈6.4 |
| 9×9 | 81 | 4 | 28 | 49 | 144 | ≈6.4 |

Each interior piece has degree 4, each edge piece degree 3, and each corner degree 2. Random overlap is ≈ E²/C(N,2).

### Connectors

Give every interior piece **one identical asymmetric shape**: blanks on N and W, tabs on S and E. Every interior piece then fits every interior slot. The shape also physically rejects the three wrong orientations, so the player never tests rotations and an upside-down piece cannot sit in place.

- Top-edge pieces share one shape (flat N), and likewise for each side.
- The 4 corners are 4 distinct shapes.
- The alternative, a checkerboard of 4-tab and 4-blank pieces, splits the set into two parity classes. That does not hurt the adjacency target, but it gives no benefit in this mode.

### Border constraints

Without rotation:

- Each **corner piece occupies the same corner slot in all three images.**
- Each side's pieces only permute along that side.
- The 82 + 4 border fragments (17% of 500, and 40% at 10×8) frame every image. A "sky along the top" in image A forces image B's top strip to be built from the same 23 sky-ish fragments.

**Side-length bound.** A side with *n* non-corner pieces is a path from corner to corner. Zero sharing needs three such orderings with no edge in common.

- Each inner piece needs 6 distinct partners across the three paths, so n + 1 ≥ 6.
- Exhaustive search confirms that **n = 3, 4 and 5 are infeasible and n ≥ 6 is feasible.**
- So every side needs at least 8 pieces including corners. 25×20 and 10×8 pass. A 12×7 grid fails: the best found was 1/1/2 shared pairs, and that floor comes from the 7-piece sides.

### Interior

**Construction:** A is the identity. B and C are random permutations within each class (interior, each side), then greedy swaps within a class whenever they reduce shared pairs. Results:

| Size | Shared pairs at start (A–B, A–C, B–C) | After swaps | Swaps needed |
|---|---|---|---|
| 10×8 | 8 / 10 / 11 | 0 / 0 / 0 | ~7k |
| 9×9 | 11 / 13 / 14 | 0 / 0 / 0 | ~2k |
| 25×20 | 16 / 16 / 12 | 0 / 0 / 0 | ~2k |

Why it is easy: each solution uses under 1% of the possible pairs at 500 pieces (4.5% at 80), and the space of permutations is enormous. The real optimizer will therefore spend its effort on visual objectives, with shared adjacency as a cheap hard constraint, or as a soft one when the art justifies a few repeats.

### Artwork implications

Gravity is preserved, so recognizable scenes (DECISIONS #3), horizons and upright figures all work. Directional marks stay valid as long as each mark is direction-neutral *across positions*, not across rotations.

The cost is the straight row-and-column cut network, which is the most "grid-like" option for the piece-boundary problem (HANDOFF §5). Section 3 addresses that later.

### Solving experience

Mechanics carry zero information, so the art does all the placement work. HANDOFF §7 explicitly allows this. Trial and error scales with the number of compatible slots (414 interior candidates), with exactly one orientation each. Border-first still works as an opening, but in the second and third solves the border set is already known, which is a mild giveaway.

### Manufacturing

This is the simplest possible die. 500 pieces at about 1.9 cm cells give roughly 48×38 cm, a standard format. Identical shapes have uniform knob strength and are durable.

## 2. Square lattice with 90° rotation (second experiment)

### Counts

The counts are identical to section 1. Rotation changes compatibility, not the graph.

### Connectors

Interior shapes must survive a quarter turn.

| Option | Cut | Fit | Verdict |
|---|---|---|---|
| (a) Checkerboard | All-tab and all-blank pieces | Any rotation; each piece keeps its parity class of about 250 | Standard and robust. **Default for the physical version.** |
| (b) Ribbon cut | Tabs N/S on one class, tabs E/W on the other | Any slot, but slot parity dictates {0°, 180°} or {90°, 270°} | Couples art orientation to position. Rejected. |
| (c) Androgynous S-edge | Half knob and half socket, point-symmetric | Any slot, any rotation | Maximum freedom, but weaker hold. Needs a physical test. |

### Border

Rotation pools all 82 edge pieces across the four sides, and corners can move between corners (within parity under option (a)). A top-edge piece becomes a left-edge piece. The side-length bound disappears: **12×7 now reaches 0/0/0**, as do 10×8 and 25×20, under both (a) and (c), each in about 1k swaps or fewer.

What rotation does *not* fix: the **set** of 86 border fragments is still shared by all three images.

### Rearrangement freedom

There is nothing new to gain for interior adjacency, because it was already zero. The genuine new freedom is **reinterpretation** (HANDOFF §6.2). For example:

- A vertical bar is a trunk; at 90° it is a log or a shoreline.
- A crescent is a hull; at 180° it is a bowl or a smile.
- A cluster of dashes is rain; turned, it is reeds.

### Artwork implications

Most scene marks carry gravity: figures, trees, cast shadows, ground, water surfaces. Rotation helps only two kinds of piece:

- **Isotropic** pieces (speckle, foliage clumps, pebbles, stars). These were already flexible, so they gain little.
- Pieces drawn on purpose to be **bi-readable**.

The strongly oriented pieces, which are the ones that need help, cannot use rotation at all.

Therefore rotation is a **per-piece privilege**. The art vocabulary tags each piece *upright* {0°}, *flip* {0°, 180°}, *quarter* {0°, 90°}, or *isotropic* (all four). The optimizer rotates a piece only within its tag. "No rotation" mode is then simply every piece tagged upright.

Report how many pieces actually appear rotated in each solution. If that number stays near zero, rotation bought nothing.

### Solving experience

Every candidate slot now has up to 4 physical fits, so false positives quadruple. The player must infer "up" from the art. That is easy for oriented pieces, and harmless for isotropic ones, since they look fine either way. Bi-readable pieces are the intended source of delightful confusion.

### Manufacturing

Option (a) is standard. Option (c) should be laser-cut and tested for hold before it is relied upon.

## 3. Later stage: shape deviation within the square lattice

**Idea.** A piece still occupies one lattice cell, but its outline deviates from a square: bowed edges, an outline curving toward a triangle, deep wavy cuts. A neighbor must fill whatever the piece does not, so a deviation is really a property of a **lattice edge profile** shared by two slots.

**Key consequence.** Slot outlines are the same in all three solutions, so every deviation partitions the slots into **shape classes**. A piece only ever moves among slots of its class. Everything below follows from that.

**What it could buy:**

- **Hiding the grid.** Varied or wavy profiles break the straight row and column lines, which is the main geometric lever on HANDOFF §5. If all edges share *one* identical wavy profile, freedom is fully preserved.
- **Mechanically encoded orientation.** An outline with 180° symmetry admits only {0°, 180°}. A 4-fold symmetric outline admits all four rotations, and an asymmetric one admits only 0°. The art tags from section 2 become physical, which cuts false fits. The square cell cannot add rotations beyond the four quarter turns; it can only select among them.
- **A difficulty dial.** Use *k* profile "dialects" scattered over the board. Each piece then fits N/k slots, and players regain mechanical guidance. With k ≤ 4 and well-spread classes, zero sharing should remain easy.
- **Border relief.** The related, non-shape fix is a **frame tray**: all 500 pieces are interior-shaped and the outer profile is a separate frame. This removes corner and edge classes entirely, along with the shared border inventory.

**Costs:**

- Every new class shrinks freedom, and pins a class's *slot positions* identically across all three images.
- A distinctive outline becomes a remembered landmark between solves.
- Deep curves and narrow necks weaken pieces.
- The frame tray loses the classic edge-first opening.

**Gate.** Revisit once the plain-square prototype shows which constraint actually hurts: the border, the visibility of the grid, or ambiguity.

## 4. Rejected alternatives

- **Hexagons.** Six neighbors and a honeycomb cut network are attractive. But a rectangular outline needs at least 4 border shapes, 60° and 120° rotations only tilt scene marks, the knobs are cramped (about 1.2 cm sides at equal area), and the combinatorics gain nothing. Rejected per the owner.
- **Triangles and mixed tilings.** Sharp tips are fragile and hold no marks, up and down triangles form split classes, 120° rotations are tilts, and the look is kaleidoscopic rather than scenic. Rejected.
- **Circular outline (polar grid).** A ring-*k* piece only fits ring *k*, which locks each piece's radius in all three images. Rejected.
- **Unique irregular per-piece cuts.** Each piece then fits one slot, which defeats the concept. Rejected.

## 5. Data model for the engine

Write the model once. Modes 1 and 2 are configurations, and section 3 only adds new profile ids.

```text
Rot     = 0..3 quarter turns (clockwise); side indices N=0, E=1, S=2, W=3
Profile = "flat" | "frame" | ("tab", d) | ("blank", d) | ("andro", d)   # d = dialect id, 0 for now
mates(a, b): flat~flat (board edge), frame~frame, tab(d)~blank(d), andro(d)~andro(d)

Board:
  width, height
  slots[i]:      pos (x, y); req[4]: Profile         # what the occupant's side s must present
  neighbors[i]:  [(j, side)]                         # derived from the lattice
  rotation_group: subset of Rot                      # {0} or {0,1,2,3}

Piece:
  id
  sides[4]: Profile             # in the piece's own upright frame
  art_rots: subset of Rot       # tag: upright {0}, flip {0,2}, quarter {0,1}, iso {0..3}
  art: reference into the visual vocabulary (docs/design/01–04)

valid(p, slot, r) iff r in board.rotation_group ∩ p.art_rots
                   and for every side s: p.sides[(s - r) mod 4] equals slot.req[s]
Compat[p] = { (slot, r) : valid }        # precomputed; identical Compat sets form classes

Solution k in {A, B, C}:
  place[p] = (slot, r)                   # bijection onto slots, each entry in Compat
  board reference                        # the same board for now; HANDOFF §11.6 leaves room for per-solution boards

Derived:
  E_k   = { {p, q} : place[p].slot and place[q].slot are lattice neighbors }
  shared(k, l)       = |E_k ∩ E_l|       # hard target 0, or soft with a weight
  clusters(k, l)     = components of size ≥ 2 in (E_k ∩ E_l)
  rotated_frac(k)    = share of pieces with r ≠ 0
  branching          = mean |Compat[p]|  # mechanical trial-and-error proxy
  border_locked_frac = share of pieces whose Compat touches only outline slots

Optimizer moves: swap two pieces of one class (choosing rotations from Compat), re-rotate one piece, 3-cycles.
```

### Configurations

**Mode 1 (no rotation):**

- Interior requirement: N = blank, E = tab, S = tab, W = blank.
- Outline sides use `flat`.
- `rotation_group = {0}`.

**Mode 2 (rotation):**

- Checkerboard requirements: all-tab and all-blank by parity.
- Or option (c): `andro` on every side.
- `rotation_group = {0, 1, 2, 3}`.
- Each piece's `art_rots` comes from its art tag.

**Hooks for section 3:**

- Shape deviation means new `d` values or new profile ids on chosen lattice edges.
- The frame tray means outline sides use `frame`.
- Compat and the optimizer need no other change.

`slot.req[s]` is the profile the occupant must present on side *s*; the board generator builds `req` so that neighboring requirements mate.
