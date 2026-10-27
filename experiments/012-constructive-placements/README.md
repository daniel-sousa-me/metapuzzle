# 012 constructive placements

Question: can three placements be built algebraically so that every mating class is minimal (K(3,3) for tab/blank, K4 for andro), and can such placements respect three class maps? Design write-up: `docs/design/09-constructive-placements.md`.

Requirements: the repo's package (editable install), numpy and Pillow (PNG only). The SAT scripts (`oned.py` when run as a script, `satschemes.py`, `sat_classes.py`, `k4.py`, `k4_periodic.py`) also need `pip install python-sat`. `construct.py`, `compat.py`, `perturb.py`, `artwork.py` and `k4_families.py` run in under a minute without it.

| script | what it does | output |
|---|---|---|
| `oned.py` | 1D frame-side problem (rotation none): three orderings of n pieces with fixed ends whose E/W contacts are K(3,3) blocks; stored solutions and `sequence(n)` for every n = 1 mod 3, n >= 7 | stdout |
| `construct.py` | constructions as `Solution` objects, checked with `connectors.class_summary`, shared adjacency, `validate_solution` | `construct-out.txt`, two solution JSONs |
| `satschemes.py` | SAT model of exact minimal classes on small boards (placement variables; tray, standard or torus; K(3,3) or K4) | stdout |
| `sat_classes.py` | the same with three class maps imposed | stdout |
| `k4.py` | K4 search on a torus (side involutions + vertex condition + connectivity cuts), cut to trays, checked with connectors | `k4-out.txt` |
| `k4_families.py`, `k4_periodic.py` | negative searches: linear / homogeneous K4 families, SAT with translation symmetry | stdout |
| `compat.py` | class-map compatibility of the families on 005 scenes-v3; repaint ("linked canvas") | `compat-out.txt`, `linked-canvas-*.png` |
| `perturb.py` | false-fit ratio when a fraction of pieces leaves the construction | `perturb-out.txt` |
| `artwork.py` | share of false fits ruled out by tone classes alone (005 run-quarter-v3b) | `artwork-out.txt` |

## 1. Rotation none: exact K(3,3) exists iff cols, rows = 1 (mod 3), both >= 7

**Necessity.** Each side in a complete K(3,3) has three partners, so a side used once is used in all three placements. A side facing the wall once therefore faces it always: on a tray the outer ring is invariant (its wall sides are dead and could be cut flat), so an exact tray is a standard frame, and without rotation every piece stays on its frame side and corners are fixed. Along the top row the E/W contacts involve only top-row pieces: a 1D problem on n = cols pieces with fixed ends, needing 3 | n - 1. n = 4 is impossible (the corner would meet the opposite corner in one placement). SAT (`oned.search`): n = 7 only with shared adjacencies and a fixed piece; n = 10, 13, 16 have solutions with zero shared adjacencies (13, 16 also with no fixed piece).

**Construction.** 1D, n = 9j + 1: position i < n - 1 holds piece mu_k i mod (n - 1) with mu_k = 1 + k (n - 1)/3, the last position holds piece n - 1 (the cyclic group construction cut at its fixed point 0). Joining two solutions at a shared end piece gives n1 + n2 - 1, so 10, 13, 16 generate every n >= 10. 2D: P_k(i, j) = (alpha_k(i), beta_k(j)) with alpha, beta 1D solutions for cols and rows.

`construct-out.txt` (all classes checked by `metapuzzle.connectors`):

| construction | valid | sides | classes | class sizes | complete minimal classes | false fits | ratio | shared AB/AC/BC | fixed pieces |
|---|---|---|---|---|---|---|---|---|---|
| product 7x7 standard none | yes | 168 | 28 | [6] | 28 | 0 | 0.000 | 28/28/28 | 16 |
| product 10x10 standard none | yes | 360 | 60 | [6] | 60 | 0 | 0.000 | 0/0/0 | 16 |
| product 13x13 standard none | yes | 624 | 104 | [6] | 104 | 0 | 0.000 | 0/0/0 | 4 |
| product 19x25 standard none | yes | 1812 | 302 | [6] | 302 | 0 | 0.000 | 0/0/0 | 35 |
| product 22x22 standard none | yes | 1848 | 308 | [6] | 308 | 0 | 0.000 | 0/0/0 | 25 |
| product 16x31 standard none | yes | 1890 | 315 | [6] | 315 | 0 | 0.000 | 0/0/0 | 16 |
| group 6x6 tray none (22 parameter sets) | yes | 140 | 24 | [5, 6] | 12 | 24 | 0.133 | 0/0/0 | 4 |
| group 9x9 tray none (64 parameter sets) | yes | 300 | 51 | [5, 6] | 42 | 9 | 0.021 | 0/0/0 | 27 |
| group 21x24 tray none (22 parameter sets) | yes | 2001 | 336 | [5, 6] | 291 | 90 | 0.031 | 0/0/0 | 56 |
| group 21x21 tray none (22 parameter sets) | yes | 1750 | 294 | [5, 6] | 252 | 84 | 0.033 | 0/0/0 | 49 |
| checkerboard 13x13 standard none | yes | 624 | 104 | [6] | 104 | 0 | 0.000 | 0/0/0 | 85 |
| checkerboard 19x25 standard none | yes | 1812 | 302 | [6] | 302 | 0 | 0.000 | 0/0/0 | 238 |

`product-19x25-standard-none.json` passes `metapuzzle connectors` (302 classes of 6, 0 false fits) and `metapuzzle report` (0 shared adjacencies). Near 500 pieces: 19x25 (475), 22x22 (484), 16x31 (496), 19x28 (532). 20x25 and 24x20 cannot be exact (19 and 23 are not 0 mod 3). Group trays (010's construction, generalized to all parameters) need an element of order 3 (3 | cols or rows; 20x24 has none that works) and leave partial blocks at the wall (ratio 0.03). The checkerboard family (x + y even never moves; the other cells in arbitrary triples that cycle) needs cols, rows = 1 mod 6 and fixes half the pieces.

## 2. Quarter rotation and K4

- **The frame ring cannot be K4.** A frame piece keeps its flat side outwards, so its clockwise ring side always meets a counter-clockwise ring side: the ring contact graph is bipartite and its minimal class is K(3,3) (give ring sides tab/blank). Counting K(3,3) on the ring and K4 elsewhere needs 2(c + r) - 4 = 0 mod 12, i.e. c + r = 2 mod 6 (20x24, 22x22, 19x25 qualify; 20x25 does not).
- **No translation-type (group) K4.** Identify sides with elements of the square-lattice symmetry group Z^2/L x| C4; placement A glues side x to x t with t a half-turn about an edge midpoint, and any placement that treats all pieces alike glues by another half-turn. K4 needs three gluings forming a Klein group, t_A t_B = t_C, but the product of two half-turns is a translation. Searches agree: linear cell maps with period-2 rotation patterns (4x4, 6x6), a homogeneous family (g, i) -> (g + tau(i), phi(i)) up to 12x12, and SAT with period-2 translation symmetry (4x4, 6x6: UNSAT) find nothing.
- **K4 exists without symmetry.** `k4.py` (SAT on side involutions): on the 4x4 torus every class is a complete K4 (three placements = the three perfect matchings), but one placement lands on a sheared torus, so the tray boards are 4x4, 8x2, 4x4 (allowed by the engine). Tray cut, checked with connectors: valid, 62 sides, 16 classes of 3-4 sides, 20 false fits (ratio 0.29, all from wall-cut contacts), shared adjacencies 5/10/6 (the 4x4 torus is too small to avoid them). Larger tori are inconclusive: `k4.py 6x6` (no shape constraint), `k4_periodic.py 8x8:p2,2` and `6x6:p3,3` ran 50 minutes each without an answer (CaDiCaL, one core each). Whether a same-shape K4 exists at practical sizes is open.

## 3. Class maps (005 scenes-v3, 20x25, 9 classes; `compat-out.txt`)

A construction fixes each piece's trajectory, so picture B is picture A pushed through a fixed cell map psi_B (B(psi_B c) = A(c)); same-class interchangeability adds no freedom, only the choice of scheme does. A piece is satisfied when A(c_A) = B(c_B) = C(c_C).

| quantity | full classes | tiers L/M/D |
|---|---|---|
| same class at the same cell in all three (all pieces fixed; not a valid scheme) | 43.6% | 68.4% |
| random trajectories (expected) | 10.8% | 23.5% |
| any cyclic scheme (pieces cycle through cell triples), geometry-free bound | 52.6% | 87.0% |
| checkerboard family bound | 47.2% | 77.8% |
| group family, tray 21x24, best of 22 x 504^2 schemes | 20.2% | 34.7% |
| product family, standard 19x25, construction | 23.6% | 40.4% |
| product family, any row/column permutations (relaxation, upper bound) | 56.0% | 77.1% |

Strict linked canvas (repaint each trajectory with its majority class): 12-13% of A's cells change and 49-57% of B's and C's. `linked-canvas-product.png` / `-group.png`: top row the three designed maps, middle row B and C derived from A (row/column shuffle by thirds; diagonal interleave), bottom row the majority repaint.

SAT with class maps (`sat_classes.py`, standard none): three independently placed blobs on 7x7 (6 map sets) and 10x10 (1 set) are UNSAT within a second, while maps derived from a construction are SAT in 0.4 s. On 7x7 even a single dark piece is infeasible for some cell triples.

## 4. Sensitivity and compromises (`perturb-out.txt`, `artwork-out.txt`)

Displacing a fraction f of the pieces (a designer departing from the construction):

| f | 0 | 1% | 2% | 5% | 10% | 20% | 76% (scenes-v3 needs this) |
|---|---|---|---|---|---|---|---|
| product 19x25: false-fit ratio | 0.00 | 0.28 | 1.12 | 21.7 | 58.2 | 107 | 124 |
| product 19x25: sides still in complete K(3,3) | 100% | 92% | 82% | 58% | 32% | 8% | 0% |
| group 21x24: false-fit ratio | 0.03 | 0.53 | 1.83 | 40.2 | 83.4 | 142 | 174 |

Classes percolate: past about 3% displaced pieces one class per axis swallows almost everything.

Artwork alone (run-quarter-v3b, all andro): 530 false fits per intended contact; 412 of them join pieces whose tone classes are neighbours somewhere (L|L 104, L|M 67), so tone classes rule out only 22%.
