# 02 — Piece classes (lexicon)

There are 15 classes: 6 fields, 5 skyline transitions and 4 features. Each class has a two-character **grid code** (used in 03-three-scenes.md) and a snake_case **ID**. Counts are per scene for the 80-piece prototype, identical in A, B and C.

Conventions: the cell spans [0,1]², with y pointing down. "Dab", "speck", "sprig" and the palette tokens are defined in 01-visual-grammar.md. **Edges** gives the material on the top, right, bottom and left edges (S sky, N snow, M meadow, F foliage, D deep, R rust). The seam checker uses this column.

Every piece is drawn as `ground fill → dabs (back to front) → sprigs/specks → boundary clip (transitions) → feature (features)`, with a per-piece RNG seeded from the piece ID. Draw onto cell + 0.25 bleed and clip to the physical outline.

## Field classes (non-directional)

| Code | ID | Count | Edges | Description |
|---|---|---|---|---|
| SK | `sky_field` | 21 | SSSS | Pale blue dappled field |
| SN | `snow_field` | 1 | NNNN | Cream-white dappled field |
| ME | `meadow_field` | 24 | MMMM | Yellow-green grass with tufts and flower specks |
| FO | `foliage_field` | 9 | FFFF | Dark green leaf dabs with small sprigs |
| DP | `deep_field` | 10 | DDDD | Indigo dabs with a teal undertone and sparse pale glints |
| RU | `rust_block` | 2 | RRRR | Red-brown, slightly coarser dabs |

Recipes (all dab angles uniform in [0, π), positions uniform over cell + bleed):

- **sky_field.** Ground `#A9CBE3`. 30–38 dabs, diameter 0.18–0.30. Tone weights: `#8DB8DA` 0.35, `#C9DEEC` 0.45, `#D3DFEA` 0.10 (spill toward snow), `#A9CBE3` 0.10. No specks.
  Readings: sky in A, B and C. In C the row under the snow also reads as thin mountain air or mist.
- **snow_field.** Ground `#F2EDE1`. 30–38 dabs, diameter 0.18–0.30. Tones: `#FFFFFF` 0.40, `#DED6C4` 0.35, `#D3DFEA` 0.25.
  Readings: cloud body (A), sail cloth (B), snowfield (C).
- **meadow_field.** Ground `#A9BF63`. 34–44 dabs, diameter 0.16–0.26. Tones: `#8EAD4B` 0.40, `#C7CF7C` 0.40, `#6B904D` 0.10 (spill toward foliage), ground 0.10. Then 2–4 sprigs in `#7E9E40` (3–5 strokes, length 0.06–0.12, width 0.015–0.025) and 0–4 specks in `#E2C35A`.
  Readings: field/hillside in A, coastal grass in B, alpine pasture in C.
- **foliage_field.** Ground `#4F7B44`. 34–44 dabs, diameter 0.16–0.28. Tones: `#3B6537` 0.40, `#6B904D` 0.30, `#2F5A50` 0.20 (spill toward deep), `#8EAD4B` 0.10 (spill toward meadow). Then 1–3 sprigs in `#2E4F2B` and 0–3 specks in `#9CC07A`.
  Readings: tree crown and hedgerow (A), island and shore woods (B), mountain forest (C).
- **deep_field.** Ground `#34477A`. 32–40 dabs, diameter 0.18–0.30. Tones: `#26355F` 0.40, `#4A5F95` 0.35, `#2F5A6E` 0.20 (spill toward foliage), `#2F5A50` 0.05. Then 0–5 specks in `#DCE6EE` at 70 % opacity.
  Readings: the specks read as sparkle on the sea (A, B) and as snow flecks or scree on the mountain body (C). The field itself is sea (A, B) or mountain lake and mountain body (C).
- **rust_block.** Ground `#A65233`. 26–32 dabs, diameter 0.20–0.32. Tones: `#8A3F28` 0.45, `#C26A43` 0.40, `#6E3322` 0.15.
  Readings: tree trunk (A), boathouse wall (B), cabin wall (C).

## Skyline transitions (directional; no-rotation mode)

All transitions share one boundary generator. The boundary is a polyline between two corner pins, with 12–20 interior points and perpendicular jitter ±0.06 (smoothed with a 3-point moving average). Flanks also get a convex bulge sampled from U(0, 0.12) toward the sky side, which gives a rounded shoulder. The upper side is drawn with the **sky_field** recipe and the lower side with the mass recipe, each clipped to its side. Within 0.10 of the line, 15 % of each side's dabs use the other side's tones.

| Code | ID | Count | Edges | Boundary | Mass recipe |
|---|---|---|---|---|---|
| S/ | `snow_flank_left` | 2 | S N N S | BL corner → TR corner | snow_field |
| S\ | `snow_flank_right` | 1 | S S N N | TL corner → BR corner | snow_field |
| F/ | `foliage_flank_left` | 2 | S F F S | BL → TR | foliage_field |
| F\ | `foliage_flank_right` | 2 | S S F F | TL → BR | foliage_field |
| HD | `horizon_deep` | 2 | S D D D | TL → TR, sagging | deep_field |

**horizon_deep boundary.** Pinned at (0,0) and (1,0). Sample k = 2–4 trough centres in (0.15, 0.85), at least 0.2 apart. Each trough is a smooth bump of depth U(0.10, 0.40) and half-width 0.10–0.20. Between troughs the line returns to y ∈ [0, 0.05]. The result reads as a sea horizon with low swells (A, B) or as the ragged snowline of a peak (C), where the troughs look like snow tongues.

Readings across scenes:

- **S/ and S\**: the left and right edges of a cumulus (A), the luff of a mainsail and its jib (B), the flank of a snow peak and a small cloud (C).
- **F/ and F\**: the shoulders of the tree crown (A), the slopes of an island (B), the forested mountain flanks and a small fir hill (C).
- **HD**: the sea horizon (A, B), the far plain or lake horizon at the frame edges (C).

## Feature classes (one self-contained motif each)

Each feature is drawn on top of a complete host recipe and is fully contained in the cell (motif ≤ 0.55, centre jitter ±0.12). It never needs a specific neighbour.

| Code | ID | Count | Edges | Host | Motif |
|---|---|---|---|---|---|
| SU | `pale_disc` | 1 | SSSS | sky_field | Gold disc |
| HB | `horizon_hull` | 1 | S D D D | horizon_deep | Rust boat/hut wedge sitting on the boundary |
| HL | `horizon_fleck` | 1 | S D D D | horizon_deep | Small white sail/fleck sitting on the boundary |
| PH | `rust_window` | 1 | RRRR | rust_block | Dark rounded window with gold rim |

- **pale_disc (SU).** Disc diameter 0.46–0.54, centre (0.5±0.12, 0.5±0.12). Ring of 14–18 dabs in `#E8A93A` (diameter 0.10–0.14) on the circumference, then 10–14 dabs in `#F2C14E`/`#F7D98A` inside. Sky dabs are not drawn inside the disc. No halo, no rays (rays would be long lines).
  Readings: sun over the meadow (A, upper right), sun over the bay (B), a low sun or moon beside the peak (C). This is a deliberately **stable** feature: it is an anchor for solvability, not an ambiguity.
- **horizon_hull (HB).** Draw horizon_deep with k = 2 and force the middle third flat at y ≈ 0.04. On it, place a trapezoid 0.40–0.55 wide and 0.14–0.20 high (wider at the top, deck at y = 0.02–0.06), made of 8–12 rust dabs clipped to the trapezoid, with a 0.02 `#6E3322` dab line at its base.
  Readings: **hull of the sailboat** under the sail (B), a **red fishing boat** on the far horizon (A), a **mountain hut** at the snowline (C).
- **horizon_fleck (HL).** Horizon_deep as above. On the flat part, place a white wedge (triangle 0.18–0.26 wide, 0.22–0.32 tall, apex up, apex offset ±0.05) made of 6–9 snow dabs.
  Readings: **a distant sail** (A), **the boom-end / second sail** of the boat under the main sail (B), **a snow tongue or glacier** under the peak (C).
- **rust_window (PH).** Rust host. Rounded rectangle 0.28–0.36 wide × 0.36–0.46 tall (corner radius 0.08), filled with `ink` plus 3–5 dark-plum dabs `#3B2E44`, rim of 12–16 small gold dabs (diameter 0.05–0.07).
  Readings: **knothole / owl hole** in the trunk (A), **boathouse window** (B), **lit cabin window** (C).

## Directionality and rotation

Fields, SU and PH are rotation-invariant, so they can be rotated freely in rotation mode. The 5 transitions, HB and HL are directional. Under 90° rotation, `/` and `\` become the same class family (one class per material pair, rotated). This is the main reason rotation mode should cut the class count; see 04-risks-and-tests.md.

## Class-count notes and extensions (for 500 pieces)

Fifteen classes cover the prototype. The first additions for 20×25 are:

1. `horizon_foliage` (sky over foliage, for treelines).
2. Mirrored S\ counts so clouds can be symmetric.
3. `sand_field` (`#D9C08A`, soft with meadow and sky). It adds a beach and a path, and gives a warm field for solvability.
4. Two or three **sub-variants per large field** that differ in dab density or speck rate (e.g. "sky, sparse" vs "sky, busy"). Same material, different statistics, which gives the solver local clues.

Do not exceed about 20 classes. Every new transition multiplies the joint-design work.
