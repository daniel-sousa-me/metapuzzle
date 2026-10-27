# 09 — Constructive placements: minimal mating classes and what they cost the pictures

Experiment 012 (`experiments/012-constructive-placements/`, numbers in its README) builds three placements algebraically so that every mating class is minimal: K(3,3) for tab/blank sides or K4 for andro sides, with the three placements as the class's three perfect matchings (zero false fits). It then tests whether such placements can carry three independent class maps. All constructions are verified with `metapuzzle.connectors`.

## Summary

1. **Rotation none:** exact K(3,3) everywhere exists **iff cols ≡ rows ≡ 1 (mod 3) and both ≥ 7**, on a standard frame (an exact tray is a standard frame). There is an explicit product construction with zero shared adjacencies. 19x25, 22x22 and 16x31 work; **20x25 cannot**.
2. **Quarter rotation:** the frame ring is bipartite, so its minimum is K(3,3) (tab/blank ring sides). No translation-type (group) K4 exists. K4 does exist without symmetry: SAT finds a 4x4 torus scheme whose classes are all complete K4s. Searches on 6x6 and 8x8 did not finish in 50 minutes; same-shape K4 at 500 pieces is open.
3. **Class maps:** a construction fixes every piece's three cells, so B and C are A pushed through fixed cell maps. Those maps destroy every adjacency, and in the algebraic families they jump by thirds of the board, so B and C come out scrambled. On scenes-v3 the best constructions satisfy 20–24% of pieces (random: 11%). Even an idealized cyclic scheme is capped at 53%.
4. **Compromise:** minimal classes survive only about 2% of pieces leaving the construction (ratio 1.1); 5% gives 22, and the 76% scenes-v3 needs gives 124. Free pictures have no middle ground.

## 1. Two lemmas

Placement k maps piece p to (cell, rotation); the trajectory of p is (c_A, c_B, c_C).

**L1 (frame invariance).** In a complete minimal class every side has degree 3, so a side used once is used in all three placements, and a side that faces the wall once always faces it. On a tray the outer ring is invariant and its wall sides are dead, so an exact tray *is* a standard frame. Without rotation, each frame piece stays on its side and the corners are fixed.

**L2 (frame sides are one-dimensional).** Without rotation, the E/W contacts of the top row join top-row pieces only. They form three orderings of n = cols pieces with fixed ends, whose successor relation must split into K(3,3) blocks: n − 1 tab sides in blocks of 3 gives **3 | n − 1**. **n = 4 is impossible**: the start piece needs three different right neighbours, and one of them would be the end piece. SAT (`oned.py`) finds n = 7 only with shared adjacencies and a fixed piece; n = 10, 13 and 16 have clean solutions.

## 2. Rotation none (Q1)

**1D sequences.** For n = 9j + 1, cut the cyclic group construction at its fixed point:

  P_k(i) = μ_k · i mod (n−1) for i < n−1, P_k(n−1) = n−1, with μ_k = 1 + k(n−1)/3.

E side g meets W side g + μ_k, and {μ_k} is a coset of the order-3 subgroup ⟨(n−1)/3⟩, so blocks are cosets. Cutting at piece 0 replaces W(0) by the end piece's W side inside one block. Joining two solutions at a shared, fixed end piece gives n₁ + n₂ − 1. The bases 10 (formula), 13 and 16 (SAT, stored in `oned.SEQ`) therefore generate **every n ≡ 1 (mod 3), n ≥ 10**, with zero shared adjacencies (checked up to 49).

**2D product.** Use P_k(i, j) = (α_k(i), β_k(j)) with α, β the 1D solutions for cols and rows. Horizontal contacts are 1D contacts row by row, and vertical contacts are column by column, so every class is a K(3,3). No pair touches both horizontally and vertically. Verified on 19x25, 22x22 and 16x31 standard boards: 302, 308 and 315 classes, all complete K(3,3), 0 false fits, 0 shared adjacencies, 35, 25 and 16 fixed pieces (products of 1D fixed points). `product-19x25-standard-none.json` passes `metapuzzle connectors` and `metapuzzle report`.

**Tray with live wall sides.** Exactness is impossible (L1). Experiment 010's group construction (piece g ∈ Z_c × Z_r at φ_k⁻¹(g), φ_k = [e₁ + k·h | e₂ + k·v], h and v of order 3) gives classes of 5–6 sides, ratio 0.03 at 21x24; 20x24 has no working parameters.

**Checkerboard family** (cols, rows ≡ 1 mod 6). Cells with x + y even never move, and the other cells form arbitrary triples (t₀, t₁, t₂) with P_k(t_j) = t_{j+k}. The family is exact for *any* grouping, but half the pieces are fixed.

## 3. Quarter rotation and K4 (Q2)

- **Ring.** A frame piece keeps its flat side outwards, so its clockwise ring side always meets a counter-clockwise one. The ring contact graph is bipartite and K4 is impossible there. Use tab/blank ring sides (K(3,3)). Counting K(3,3) on the ring and K4 inside requires 2(c + r) − 4 ≡ 0 (mod 12), i.e. **c + r ≡ 2 (mod 6)**: 20x24 and 19x25 qualify, 20x25 does not.
- **No group K4.** Sides correspond to elements of Γ = Z²/Λ ⋊ C₄. Placement A glues x to x·t, where t is the half-turn about an edge midpoint, and any placement that treats all pieces alike glues by another half-turn. K4 needs t_A·t_B = t_C (a Klein group), but (a, 2)(b, 2) = (a − b, 0) is a translation, not a half-turn. Rotations must vary from piece to piece. Linear cell maps with period-2 rotation patterns, a homogeneous side family up to 12x12, and period-2-symmetric SAT on 4x4 and 6x6 all find nothing (`k4_families.py`, `k4_periodic.py`).
- **K4 by search.** `k4.py` encodes K4 directly (π_B commutes with π_A, π_C = π_A·π_B, r∘π_k has only 4-cycles, connectivity cuts). On the 4x4 torus every class is a complete K4, but B lands on a sheared torus. Cut to 4x4, 8x2 and 4x4 trays (the engine allows differing shapes), connectors.py reports a valid solution: 16 classes of 3–4 sides, ratio 0.29 (cut wall contacts only), shared adjacencies 5/10/6 (the torus is tiny).
- **Practical answer.** Asymmetric connectors with the rotation-none constructions also give zero false fits; pieces then turn only with the whole board.

## 4. Compatibility with class maps (Q3)

**Formulation.** A piece shows one class, so a scheme respects the maps iff A(c_A) = B(c_B) = C(c_C) for every piece, i.e. **B = A ∘ ψ_B⁻¹, C = A ∘ ψ_C⁻¹** for the scheme's cell maps ψ. Interchanging same-class pieces changes nothing; the only freedom is the choice of scheme (parameters, translations, 1D sequences).

**Orbit compatibility.** In a cyclic scheme pieces cycle through cell triples (c, s·c, s²·c); this covers the checkerboard, speed-coloring and H₁ = H₂ group schemes. Write v(c) = (A(c), B(c), C(c)); the scheme needs **v(s·c) = rot v(c)**, so the cells must split into rotation orbits {v, rot v, rot² v}. The best geometry-free count is Σ n(X,X,X) + Σ_orbits 3·min(n(v), n(rot v), n(rot² v)).

**scenes-v3 (20x25, 9 classes; tiers L/M/D in brackets):**

| | satisfied pieces |
|---|---|
| random trajectories | 10.8% (23.5%) |
| group family, 21x24 tray, best of 22 × 504² schemes | 20.2% (34.7%) |
| product construction, 19x25 standard | 23.6% (40.4%) |
| any cyclic scheme, geometry-free bound | 52.6% (87.0%) |
| any row/column permutation (product relaxation) | 56.0% (77.1%) |
| same class at the same cell (pieces never move; invalid) | 43.6% (68.4%) |

**Structural reason.** ψ must break every adjacency, and in the algebraic families it moves pieces by order-3 elements (a third of the board). The derived B is three shifted copies of A interleaved on residue classes (`linked-canvas-*.png`, middle row); a majority repaint changes 49–57% of B's and C's cells. SAT agrees: three independently placed blobs on 7x7 and 10x10 are UNSAT within a second, while maps derived from a construction are SAT. **Exact minimal classes and three independently designed subjects are incompatible in every family found.** The only flexible family is the checkerboard: fixed cells need one class in all three maps and moving cells need the orbit balance. Its bound on scenes-v3 is 47%.

## 5. Compromises, quantified at about 500 pieces (Q4)

False-fit ratio = unintended mating pairs per intended contact.

| option | pictures | false-fit ratio |
|---|---|---|
| annealer, quarter / none (exp. 010) | free | 530 / 131 |
| same, counting only pairs whose tone classes are neighbours somewhere | free | 412 (L\|L alone: 104) |
| strict linked canvas (draw A, B and C follow) | B, C scrambled | 0 |
| construction + repair, f = fraction of pieces moved off the scheme | f = 1% / 2% / 5% / 10% | 0.28 / 1.1 / 22 / 58 |
| construction repaired to scenes-v3 (f ≈ 76%) | free | 124 |
| checkerboard family | half the pieces identical in all three | 0 |
| classes of t tabs + t blanks: (t − 3)/3; m andro: (m − 4)/3 | — | 12 sides: 1.0 / 2.7 |
| F equal shape families (theory ≈ 318/F) | needs closed families | F = 6: 53 |

Classes percolate: beyond about 3% displaced pieces one class per axis absorbs nearly every side, so "classes of 6–12" exist only as a 1–2% tolerance around a construction. The checkerboard has zero false fits but defeats the puzzle: after solving A, half of B is already in place, and each hole's four sides accept only a few pieces. Shape families must be unions of mating classes, so with free pictures F stays at the annealer's 2–6.

## 6. Recommendation

1. **Do not pursue minimal interior classes for three free subjects.** Exactness forces B and C to be fixed shuffles of A, and the tolerance (about 2% of pieces) is far below what three different subjects need. Record this as a structural result next to finding 16.
2. **Take the cheap mechanical wins that leave the pictures free.**
   - Prefer rotation none: one shape per axis cuts the ratio 530 → 131.
   - Choose a board with cols, rows ≡ 1 (mod 3), such as 19x25 or 22x22. The frame can then use the exact 1D sequences, a ring of K(3,3) with zero false fits that the interior never touches.
   - The price is a border that is tone-uniform per side (a mat or frame band), because the 1D shuffle scrambles any border pattern.
3. **Make uniqueness an artwork property.** Tone classes rule out only 22% of false fits (L|L background alone: 104 per contact). Distinguishing marks inside each class (T9 chip signatures, sparse non-repeating motifs) must carry it. Evaluate false fits that survive both shape and marks; connector false fits alone will stay in the hundreds.
4. **Keep the linked canvas as an art experiment only.** With the 19x25 product construction the designer paints A and B, C follow: textures or interleaves, not three nameable subjects.
