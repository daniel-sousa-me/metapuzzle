# Evaluations — pipeline v6 (sparse organic motif layer) on 27x38-v2 tiers

## Blind, full render
- A hare: "top-down overworld-style map: an olive landmass with two peaks on cream ground" (hare not named). Stars, leaves, snowflakes, spirals named 3–4/5. About 18–20 cream rectangles on the green (surplus). Grid 2/5.
- B owl: "a navy structure shaped like a face or skull, with two large cream eye-shaped openings" (3–4/5 as face). Grid 3/5.
- C swan: "a winding cream path or river over olive ground, with a navy lake" (swan not named). Grid 4/5 (most surplus blocks).
- Distinctiveness 4/5. The evaluator reads all three as maps.

## Blind, ink render
- A "tall abstract figure with upright lobes" (2/5); B "face or mask" (3/5); C "blocky animal-like or hooded form" (2/5). Contours 70 / 85 / 55% continuous. The faint symbols are neutral.

## Conclusions
1. Sparser motifs restore the silhouettes' dominance but recognition is no better than v2 and worse in ink: the limiting factor is the figures themselves (blobby pixel-art silhouettes without internal detail) and missing scene cues (horizon, water under the swan, moon behind the owl), plus the surplus rectangles that make the pictures read as patchwork maps.
2. The design pass in progress (owl cues, hare background, swan water and wing) and the class-level matcher (surplus) are the right next steps; motif density is a secondary dial (14–20%).
3. The ink view remains the stricter test; the owl's internal features are what makes it the most readable, so internal lines (wing, ear, tail) should be added to the hare and swan too.

## T9 solvability (v6)
- Score 3/5 (up from 2/5): motifs sort into 8 groups and cluster by region; 60–70% of pieces still have a look-alike at contact-sheet scale (plain cream/navy fields, about half the picture).
- Same-motif pieces differ only slightly; exact matching against the box image works where motifs are dense (olive centre), not for isolated motifs.
- Busy zones: navy edges and the top cream band ("confetti"); surplus cream rectangles inside the olive mislead matching.
- Suggested next lever: no plain interior piece without some marker; i.e. raise coverage toward 20–25% in the plain fields specifically (not near figures), keep the halo.
