# 04 — Risks and prototype tests

## Risks, ranked

1. **Class-level "free" blocks (the biggest risk, already measured).** Same-class pieces are interchangeable by design, so players solve at the class level. In the 8×10 set, 53–57 of 80 cells have the same class at the same position across scene pairs: the sky band and the meadow block. A player can leave the top row and the bottom three rows assembled. Piece-level adjacency optimization does not help, because the player cannot see the difference.
   *Mitigations:* different frame per scene (06), rotation mode, field sub-variants with different dab statistics, a smaller share of sky and meadow, and a border tray (risk 6).
2. **Congruent clusters.** B's sail is the same 3-tile cluster as C's summit, and B's island is the same 6-tile cluster as A's crown. This is good for context reading, but the player can lift the cluster as a unit. Watch whether testers do it.
3. **Texture soup / scenes too similar.** All three are upright landscapes with sky on top, a horizon at r3–r4 and meadow below. At thumbnail size they may look like one image with blobs moved around. The distinctiveness rests on three small heroes of about 4×3 cells.
4. **Unrecognizable heroes at 80 cells.** A 4×2 crown on a 3-cell trunk may read as a lollipop or a bush, and a 2×2 sail may read as a cloud. The peak may read as a tent.
5. **Grid shows through.** Soft-pair seams (foliage|deep, meadow|foliage) run along cuts and may reveal knob profiles. Long same-material regions may show a faint lattice if dab density drops near edges, which is a renderer bug to test for.
6. **Border/physics.** Identical side sequences are forced in no-rotation mode. If frames differ per scene (06), flat-edged pieces become impossible, and a tray or frameless cut is needed.
7. **Features too conspicuous or too weak.** The gold sun may pop out as the only saturated warm spot (fine as an anchor). HB and HL may be too small to read as boat, hut or sail at viewing distance.
8. **Low solvability in large fields.** 21 sky and 24 meadow pieces are near-identical. The class mix is fine, but within a field the player has nothing to go on except edge shape.
9. **Palette drift in print.** Soft pairs depend on close values. CMYK printing can push foliage|deep or sky|snow into either a hard seam or no edge at all.

## Tests for the first prototype

Run these on renders first (cheap), then on a printed, cut 80-piece set.

| # | Test | Method | Pass criterion |
|---|---|---|---|
| T1 | **Blind recognition** | Show each full render (on screen at about 30 cm per 10 cells, then printed) to 8+ people who have not been told the subjects. Ask "Describe this picture in one sentence", then "What is the large shape in the middle?" Record verbatim. | ≥ 6/8 name the subject class (tree, boat or sailing, mountain) unprompted; ≥ 7/8 say the three images are different pictures. |
| T2 | **Feature reading** | Same participants: point at SU, HB, HL and PH in each scene and ask "What is this?" | Each feature gets the intended reading in ≥ 2 of its 3 contexts for most people. Log the readings that collide. |
| T3 | **Grid visibility** | Render each scene with piece outlines hidden, at 1 m and 2 m viewing distance. Ask "Do you see a grid or tiles?" Do an A/B comparison against the same scene with randomized seeds per piece. Also compute the edge-energy spectrum (FFT peak at the cell period). | No unprompted "grid" or "tiles". FFT peak at the cell frequency < 2× the background. |
| T4 | **Seam audit** | Automated: zero forbidden pairs (already true). Visual: crop 3×3-cell windows around every soft seam and show them mixed with crops of same-class seams. | Observers cannot pick soft-pair seams above chance on 60 % of the crops. |
| T5 | **Shuffle test** | Re-render each scene 20 times with a different random permutation of same-class pieces. | All renders judged "the same picture". This confirms class-level interchangeability. |
| T6 | **Thumbnail distinctness** | Downscale all three scenes to 40 px wide. Ask people to match the thumbnails to the full images. Also compute the pairwise SSIM of blurred images. | 100 % correct matching. Blurred SSIM between scenes < 0.6. |
| T7 | **Carry-over solve** | Physical. Testers solve A, then are told "the same pieces make a boat picture" and solve B. Log the time, the clusters kept intact (photograph them) and their comments. Counterbalance the order across testers. | The second and third solves take ≥ 60 % of the first. Kept clusters are < 15 % of pieces. **Expect failure on the sky/meadow blocks**; quantify it. |
| T8 | **Rotation variant** | Repeat T1, T3 and T7 with a rotation-mode class set: one flank class per material pair, rotated. | Compare class count, recognizability and kept clusters against no-rotation. |
| T9 | **Print check** | Proof-print the 15 class swatches and soft-pair seams on the intended board stock. | Each soft pair stays distinguishable but not harsh: ΔE00 between grounds is 8–20. |

Instrument everything: the renderer should emit per-scene metrics (histogram, border multisets, seam counts, same-class-same-position count, class-level shared adjacencies) so every edit is scored.
