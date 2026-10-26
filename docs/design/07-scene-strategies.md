# 07 — Scene strategies: three structures from one inventory

Direction A failed because all three scenes put the same class in the same place (66–71 % same-position overlap). Experiment 003 looks for strategies that make three images structurally different with identical class histograms. Files are in `experiments/003-scene-strategies/<name>/` (`scenes.txt`, `intent.txt`, `scenes.png`, `scene-metrics.txt`).

## Rules the experiment uncovered

1. **Field ownership.** Uniform blocks dominate 2x2 reuse and the transferable blob: one 2x2 SK block anywhere in B makes every sky window of A count as reused. A bulk class may therefore form blocks (2x2, or regions of 8+ cells) in **one scene only**. Elsewhere it must appear as lines, strips or scatter, in another role. Experiment 004 had three different subjects and still failed 2x2 reuse (0.44–0.80) for this reason.
2. **Skyline rule (no rotation).** Every transition has sky on its upper side. So the light region touches the top edge, every column holds exactly one transition piece, and neighbouring columns differ by at most one row. A fixed light count then fixes the average horizon height.
3. **Frame rule (no rotation).** Frames 8, 12 and 16 wide need 8, 12 and 16 transitions, so a shared histogram forces the wider frames to hide 4 and 8 columns under full-height dark masses.
4. **Rotation frees the light region.** With quarter turns, a transition piece can face down or sideways, so the light region can sit at the bottom (a lake under a night sky) or in a corner (sea seen from the air).
5. **Seam floor.** Only SK–SN, ME–FO and FO–DP may meet at a cut, so field boundaries produce the same few windows in every scene (DP|FO corners, FO|ME edges). Fields are rotation-invariant, so **rotated** 2x2 reuse stays at about 0.4–0.5 whatever the layout. Rotated 3x3 reuse is 0–0.02: no larger cluster survives.

## Strategies tested

Context re-reading, value inversion (dark sky over a pale lake), viewpoint change (frontal vs aerial), skyline variation (flat / V / peak) and frame variation (8x12 / 16x6 / 12x8). Grids come from `experiments/003-scene-strategies/fill.py`. An intent grid fixes the silhouette, transitions and features, and leaves field cells as alternatives (e.g. `ME|FO`). The tool fills them to the shared histogram and anneals swaps against forbidden seams and the gate metrics, as 03 proposed.

## Candidate 1 — "inversion" (rotation, 8x10 ×3, tray) — passes

| Scene | Structure | What to recognize |
|---|---|---|
| A **Valley River** (day, frontal) | Light top, horizontal | Big sky, cumulus, sun. Wooded hills with a lake between them, a river winding toward the viewer between wooded banks, meadows, a red mill tower. |
| B **Moonlit Lake** (night, frontal, inverted) | Dark top, light bottom | Indigo night sky, moon, tree tips. A forest band, a moonlit meadow and a boathouse above a pale, glittering lake with a zigzag far shore. |
| C **Coast from the Air** (aerial) | Diagonal | Pale shallows top-left with surf lines parallel to the coast. A diagonal wooded coastline, a two-mouthed river delta, strip fields, a farmstead. |

Class re-readings:

| Class | A | B | C |
|---|---|---|---|
| SK | sky | lake water | shallow sea |
| SN, S/ | cloud body, shoulders | moon glitter | surf, wave crests |
| SU | sun | moon reflection | sun glare on the sea |
| DP | river | **night sky** (owner) | delta channels |
| MO (new) | glint on the river | **moon** | glint in the delta |
| FO | hills, river banks | **forest** (owner) | coastal woods, hedges |
| ME | meadows | moonlit meadow | strip fields |
| F/ | hilltops @0/@90 | forest foot over the lake @180/@270 | coastline @0 |
| HD | lake under the hills | dark water under the boathouse @180 | river mouths |
| RU, PH | mill tower | boathouse | farmstead |

Ownership: A owns SK, B owns DP and FO, and C is built from diagonal stripes. In B and C, SN on every third diagonal breaks up SK. New class **MO**: SU's gold disc on a deep_field host.

Inventory (80): SK 14, SN 6, S/ 3, SU 1, F/ 6, HD 2, DP 10, MO 1, FO 26, ME 8, RU 2, PH 1. Forbidden seams 0/0/0. `metapuzzle solve --rotation quarter --border tray` gives 2/1/0 shared piece adjacencies. Only B turns pieces upside down (8 shore transitions at 180°/270°); A uses 0° and 90°, C only 0°.

## Candidate 2 — "skyline" (no rotation, 8x10 ×3, tray) — control, fails

Three scenes: A **Bay between Hills**, B **Wooded Gorge** (a V of sky between forested walls) and C **Mountain Peak** (a blue rock pyramid). Seams, 2x2 reuse and blob pass. Same-position stays at 27.5–30 % because the top row is light everywhere and horizon heights are tied. Six fills never got the worst pair below 28.7 %. Standard borders are rejected because the side multisets differ. This is the measured ceiling of "same frame, no rotation".

## Candidate 3 — "frames" (no rotation, 96 pieces, tray) — fails

A **Lone Tree on the Hillside** (8x12), B **Cove and Sail** (16x6, a shadowed cliff hides 8 sky columns) and C **Snow Peak above the Alp** (12x8, a sunlit alp hides 4). New class **HF** (horizon_foliage): the HD recipe with foliage as the mass. The transition multiset is identical in all three. Same-position no longer applies, but the frame rule leaves only 15 light cells (16 %). The 73 dark cells cannot stay thin, so ME and DP blocks recur: 2x2 reuse is 0.34–0.43 and the blob 9–12.5 %. With three SN cells the snow peak does not read.

## Metrics

Window reuse is plain/rotated; blob is the transferable blob. Gates: same-position < 25 %, plain 2x2 < 30 %, blob < 10 %.

| Candidate | Pair | Same position | 2x2 | 3x3 | Blob | Gates |
|---|---|---|---|---|---|---|
| direction A | A-B / A-C / B-C | 66 / 71 / 69 % | 0.44 / 0.57 / 0.51 | ≤0.29 | 27–30 % | fail |
| **inversion** | A-B | **3.8 %** | **0.10** / 0.51 | 0.00 / 0.02 | 7.5 % | **pass** |
| | A-C | 21.2 % | 0.17 / 0.54 | 0.00 / 0.00 | 5.0 % | |
| | B-C | 11.2 % | 0.16 / 0.38 | 0.00 / 0.00 | 6.2 % | |
| skyline | A-B | 28.7 % | 0.27 / 0.63 | 0.00 | 6.2 % | fail |
| | A-C | 30.0 % | 0.22 / 0.46 | 0.00 | 7.5 % | |
| | B-C | 27.5 % | 0.24 / 0.49 | 0.00 | 7.5 % | |
| frames | A-B | n/a | 0.43 / 0.74 | 0.00 / 0.03 | 9.4 % | fail |
| | A-C | n/a | 0.34 / 0.53 | 0.02 | 10.4 % | |
| | B-C | n/a | 0.43 / 0.55 | 0.02 | 12.5 % | |

## Trade-offs

- **Rotation is required**, with a tray or frameless cut; F/ and F\ become one rotated family. Separate "inverted" transition classes would avoid rotation, but the shared histogram would make every scene use both kinds and force all three into the same sky–ground–sky sandwich. Rotation adds false-positive fits (HANDOFF §7); the skyline control shows what avoiding it costs.
- **Ownership pushes the other classes into thin forms.** Left free, the annealer makes checkerboards (an early B draft did), which expose the grid. Intents must draw lines explicitly: rivers with banks, hedgerows, surf lines.
- **Rotated 2x2 reuse stays at about 0.4–0.5** (the seam floor). It is harmless at 3x3, but players will recognize water and forest corners.
- **C needs crisp diagonals.** In the dapple render with the current blotch-mask transitions (`inversion/triptych-dapple.png`), A and B read but C's coast dissolves. It needs the masked transitions now under way in 002.
- **A and C share a motif** (a river between wooded banks). Next iteration: give C's DP another role, such as a tidal lagoon or channels.
- **Recognition is unproven** until a blind test.

## Recommendation

Carry forward **value and viewpoint inversion with field ownership**: rotation mode, one shared frame, a tray. It is the only strategy that passed every gate, with large margins on A-B and B-C. The same pieces change meaning (sky → lake → sea, river → night sky → delta) instead of shifting position. Without rotation, frames should not be the main lever; later they can sit on top of inversion (e.g. C as a 10x8 aerial).

Next steps:

1. Render inversion with real diagonal transitions and run blind test T1.
2. Fill a second triple from the **same inventory** to show that the strategy, not one lucky layout, carries the result.
3. At 500 pieces, keep one owner per bulk class and budget transitions as interface length per scene.
