# 03 — Three scenes from one inventory (8 × 10 prototype)

Grid: 8 columns × 10 rows, portrait, 80 pieces, no rotation. Rows r0 (top) to r9 and columns c0 (left) to c7. Machine-readable copy: `docs/design/scenes-8x10.txt`. Class codes are defined in 02-piece-classes.md.

**Legend:** SK sky · SN snow · ME meadow · FO foliage · DP deep · RU rust · S/ S\ snow flanks · F/ F\ foliage flanks · HD horizon · HB horizon+hull · HL horizon+fleck · SU sun disc · PH rust window.

## Scene A — "The Lone Tree"

```
     c0  c1  c2  c3  c4  c5  c6  c7
r0:  SK  SK  SK  SK  SK  SK  SK  SK
r1:  SK  S/  SN  S\  SK  SK  SU  SK
r2:  SK  SK  SK  F/  F\  SK  S/  SK
r3:  SK  SK  F/  FO  FO  F\  SK  SK
r4:  HD  HB  DP  RU  DP  DP  HL  HD
r5:  DP  DP  DP  PH  DP  DP  DP  DP
r6:  FO  FO  FO  RU  FO  FO  FO  FO
r7:  ME  ME  ME  ME  ME  ME  ME  ME
r8:  ME  ME  ME  ME  ME  ME  ME  ME
r9:  ME  ME  ME  ME  ME  ME  ME  ME
```

What the player should recognize is a single round-topped tree standing on a grassy clifftop, its crown against the sky and its trunk passing in front of a band of sea. There is a cumulus at upper left and a sun at upper right with a wisp of cloud under it.

- The **crown** is F/ F\ over F/ FO FO F\: a dome four cells wide.
- The **trunk** is RU / PH / RU at c3. PH is a **knothole**.
- On the horizon, **HB** is a small red fishing boat (c1) and **HL** is a distant white sail (c6).
- The DP band is the sea and the FO row is the hedgerow at the cliff edge.

## Scene B — "Isle and Sail"

```
     c0  c1  c2  c3  c4  c5  c6  c7
r0:  SK  SK  SK  SK  SK  SK  SK  SK
r1:  SK  SK  SK  SK  S\  SK  SU  SK
r2:  SK  SK  F/  F\  SK  SK  S/  SK
r3:  SK  F/  FO  FO  F\  S/  SN  SK
r4:  HD  FO  FO  DP  DP  HL  HB  HD
r5:  DP  FO  DP  DP  DP  DP  FO  DP
r6:  FO  ME  FO  DP  DP  RU  ME  FO
r7:  ME  ME  ME  PH  RU  ME  ME  ME
r8:  ME  ME  ME  ME  ME  ME  ME  ME
r9:  ME  ME  ME  ME  ME  ME  ME  ME
```

What the player should recognize is a wooded island on the left and, to its right, a sailboat with a tall white mainsail on the horizon. The bay reaches into the foreground between grassy banks and ends at a red boathouse.

- The **sail** is S/ over S/ SN: a right-triangle mainsail whose vertical edge is the mast. It sits on **HB**, which here is the boat's hull.
- **HL** under the boom reads as the foot of the sail or a small jib.
- The **island** uses the same tile shape as A's crown, with DP (sea) under it instead of a trunk.
- The lone **S\** is a cloud wisp.
- **PH** is the boathouse window.

## Scene C — "Snow Peak"

```
     c0  c1  c2  c3  c4  c5  c6  c7
r0:  SK  SK  SK  SK  SK  SK  SK  SK
r1:  SK  SU  SK  S/  SK  SK  S\  SK
r2:  SK  SK  S/  SN  SK  SK  SK  SK
r3:  SK  F/  HB  HL  F\  F/  F\  SK
r4:  HD  FO  DP  DP  FO  FO  FO  HD
r5:  DP  DP  DP  DP  DP  DP  DP  DP
r6:  FO  FO  RU  PH  RU  FO  FO  FO
r7:  ME  ME  ME  ME  ME  ME  ME  ME
r8:  ME  ME  ME  ME  ME  ME  ME  ME
r9:  ME  ME  ME  ME  ME  ME  ME  ME
```

What the player should recognize is a sharp, Matterhorn-like peak: a white summit with a vertical cliff on its right side, a blue rock body and green forested flanks. A small wooded hill stands to the right. Below are a mountain lake, a cabin on the forest edge and an alpine pasture.

- The **snow** is S/ over S/ SN. It is the same tile cluster as B's sail, now read as a summit.
- **HB** at the snowline is a **mountain hut**, and **HL** is a **glacier tongue**.
- **SU** at upper left is a low sun or moon.
- **PH** is the **lit cabin window**.

## Inventory and verification

All counts were verified with a script, not by eye (scratch checker; the logic is described in 01 §3 and §5). Identical histogram in A, B and C:

| SK | ME | DP | FO | S/ | F/ | F\ | HD | RU | SN | S\ | SU | HB | HL | PH | total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 21 | 24 | 10 | 9 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 80 |

**Borders** (no rotation, so each physical edge piece stays on its side):

| Position | Classes (identical in all three scenes) |
|---|---|
| Top (c1–c6) | 6 × SK |
| Bottom (c1–c6) | 6 × ME |
| Left and right (r1–r8, top to bottom) | SK, SK, SK, HD, DP, FO, ME, ME |
| Corners | TL and TR are SK; BL and BR are ME |

All three are checked OK.

**Seams:** none of the scenes has a forbidden material pair at a cut. Soft seams per scene (sky–snow / foliage–deep / meadow–foliage) are A 6/10/7, B 6/14/8 and C 6/15/5. Rust object edges are 8, 10 and 8.

### How the joint design was forced (read this before editing a grid)

Three couplings drove the layout. Any edit must preserve them.

1. **Skyline budget.** Sky-topped tiles (S/, S\, F/, F\, H-tiles) can only sit under sky. So every scene's skyline must be a permutation of the *same* skyline-tile multiset. Here that is 2 S/, 1 S\, 2 F/, 2 F\ and 4 horizon tiles.
2. **Horizon capacity.** With HD fixed at both side borders, the 6 interior cells of the horizon row must hold every mass base. A's crown takes 4 and its two boats take 2. B's island takes 4 and the boat takes 2. C's mountain base sits higher, at r3.
3. **Sky-region composition.** Rows r0–r3 have 32 cells in each scene and must contain the same non-sky count. This is why B's island has exactly the crown's tile shape.

### Honest weakness: positional overlap

Same class at the same position: A/B 53 of 80 cells, A/C 57, B/C 55. Shared class-level adjacencies: 74–80 %. The sky (r0) and meadow (r7–r9) blocks are visually identical in all three, so a player can leave them assembled. Piece-level adjacency can still be minimized, because the optimizer permutes interchangeable pieces. But players solve at class level. This is the price of identical frames, no rotation and upright landscapes at 80 cells. See 04 and 06 for the mitigations, of which the main one is different aspect ratios per scene.

## Scaling to 20 × 25 (500 pieces)

Keep the same grammar and roughly 18–20 classes (02 §extensions). At 500 cells:

- **Heroes grow to 6–10 rows.** A's crown becomes a true dome: about 5 rows of flanks plus a 3-row underside cut by the sea band. B gets a 6-row mainsail plus a jib, and its island moves to a far corner. C's peak fills about 60 % of the width.
- **Recycled tile budget.** The skyline budget becomes about 12 S-flanks, 12 F-flanks and 10 horizon tiles. Each scene spends them differently: A spends snow flanks on 3 clouds, B on the sail, C on the snowfield plus 1 cloud.
- **Break the sky/meadow blocks.** Horizon height varies by scene: A low (r16), B mid (r12), C high (r8 at the frame edges, with the peak to r2). Border sides then hold the same multiset in a *different order*, which a 23-cell side allows. Add `sand_field` and `horizon_foliage` so the lower halves differ: A is meadow with a path, B is beach plus water to r20, C is forest plus lake.
- **Features become 8–12 pieces.** Examples: 3 discs (sun, moon reflection, buoy), 4 hull/hut wedges and 3 windows. Each feature class gets ≥ 2 instances placed in *different* contexts within the same scene, so each one carries two meanings.
- **Tooling.** The design is now too coupled to do by hand. Engineers should build a constraint search (histogram + border multisets + seam table + per-scene intent masks such as "cells that must be skyline") and let artists edit intent masks, not cells.
