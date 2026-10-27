# 010 connector classes

Mating classes of a solution set (`metapuzzle connectors SOLUTION.json`, `connectors.py`). Nodes are non-flat sides; each contact in any solution is an edge; components are classes. False fits are possible tab-blank pairs inside a class that never touch. Ratio = false fits / intended contacts (3 x internal adjacencies).

| run | sides | classes | size min / median / max | largest | false fits | ratio | all pairs | ratio |
|---|---|---|---|---|---|---|---|---|
| 005 run-quarter 20x25 | 1910 andro | 2 | 172 / 955 / 1738 | 91.0% | 1,518,724 | 530.1 | 1,817,496 | 634.4 |
| 006 run-quarter 8x10 | 284 andro | 2 | 64 / 142 / 220 | 77.5% | 25,360 | 59.5 | 39,384 | 92.5 |
| 001 25x20 none | 1910 (955 tab, 955 blank) | 6 | 38 / 48 / 874 | 45.8% | 375,692 | 131.1 | - | - |
| 001 25x20 quarter | 1910 andro | 2 | 172 / 955 / 1738 | 91.0% | 1,518,724 | 530.1 | 1,817,496 | 634.4 |

"All pairs" bounds false fits when every andro side is one shape.

## Why the minimum is 6

On a standard board each non-flat side has one contact per solution. With no shared adjacency, no piece pair touches twice, so the contact graph is simple and 3-regular. With asym connectors it is also tab-blank bipartite, which needs at least three nodes per side. The smallest class is therefore K(3,3): 3 tabs and 3 blanks, each tab touching each blank once, with zero false fits. Andro is not bipartite, so its floor is K4.

## What the sizes imply

- **001 none:** six classes mean at most six connector shapes, with 131 false fits per intended contact.
- **Quarter:** all sides are andro, so classes are not distinct shapes. The 172-side class holds two sides of each of the 86 frame pieces (the ring-facing pair), a geometric split rather than a solver result.
- **Headroom:** asym classes of at least 6 sides allow up to about 318 distinct shapes.

## Recommendation

Target K(3,3) classes. Each solution then supplies one perfect matching of the block, so the three solutions form a 1-factorisation. Add sum of m(m-3) over classes (m = tabs per class) to the energy, and propose swaps between partner sets of one class.


## Round 2: mating penalty in the solver

Code: `MatingPenalty` in `connectors.py`, `solve(..., mating_weight, max_shared_fraction, mating_hops)` in `optimize.py`, CLI `--mating-weight W --max-shared-fraction F` on `solve` and `prototype`. Experiment: `python3 experiments/010-connector-classes/round2.py` (tables below, seed 0, 300,000 iterations, 3 runs in parallel so wall times are indicative).

**Penalty.** Nodes are sides; contacts of all three solutions are edges (a pair touching twice is one partner). For each non-flat side s, B(s) is every side within 3 steps of s; the penalty is the sum over sides of max(0, |B(s)| - m), m = 6 for tab/blank and 4 when every side is andro. Components would need dynamic connectivity, so the ball is an approximation and a lower bound on the class. Two hops are exact for the target (a side with three partners and a 2-hop ball of at most 6 sits in a K(3,3); 4 for K4 with andro) but blind to long chains of degree-2 sides, which shared adjacencies create: the annealer found them (6x6, penalty near 10, classes of 40+ sides). Three hops see 7 on such a chain, so it is the default. Updates are incremental: a move re-reads only the contacts around the touched slots and the sides within two steps of them, and rolls back on rejection. Extra moves with mating on: more rotation moves (quarter mode), and a targeted "merge" swap that takes an oversized side x, a side y two steps away, a partner c of x that y lacks and a partner d of y that x lacks, and swaps their pieces so that y meets c (rotated so the right side faces y). `max_shared_fraction` (default 0.10 when mating is on) rejects any move that raises a pair's shared adjacencies above that fraction of the smaller board's adjacency count.

**Results.** m = 6 (none) or 4 (quarter). "Sides in classes <= m" is the share of non-flat sides that already sit in a class of the target size or smaller.

Solver, 300000 iterations, seed 0.

| case | mating | classes | largest class | sides in classes <= m | false-fit ratio | shared AB/AC/BC (max %) | wall s | valid |
|---|---|---|---|---|---|---|---|---|
| 10x8 tray none | off | 2 | 160 | 0% | 28.5 | 0/0/0 (0.0) | 0 | yes |
| 10x8 tray none | on, max shared 0.05 | 5 | 160 | 4% | 25.3 | 7/7/7 (4.9) | 47 | yes |
| 10x8 tray none | on, max shared 0.10 | 8 | 144 | 4% | 18.7 | 14/14/13 (9.9) | 52 | yes |
| 10x8 tray quarter | off | 2 | 316 | 1% | 114.7 | 0/0/0 (0.0) | 0 | yes |
| 10x8 tray quarter | on, max shared 0.05 | 6 | 291 | 1% | 97.3 | 7/6/7 (4.9) | 43 | yes |
| 10x8 tray quarter | on, max shared 0.10 | 3 | 304 | 1% | 106.3 | 12/14/12 (9.9) | 48 | yes |
| 25x20 standard none | off | 6 | 874 | 0% | 131.1 | 0/0/0 (0.0) | 0 | yes |
| 25x20 standard none | on, max shared 0.05 | 22 | 856 | 5% | 125.5 | 46/47/46 (4.9) | 95 | yes |
| 25x20 standard none | on, max shared 0.10 | 27 | 864 | 4% | 128.9 | 95/94/94 (9.9) | 115 | yes |
| 25x20 standard quarter | off | 2 | 1738 | 0% | 530.1 | 0/0/0 (0.0) | 0 | yes |
| 25x20 standard quarter | on, max shared 0.05 | 25 | 1676 | 1% | 490.1 | 42/47/40 (4.9) | 89 | yes |
| 25x20 standard quarter | on, max shared 0.10 | 23 | 1686 | 1% | 496.1 | 43/54/43 (5.7) | 88 | yes |
| 005 scenes-v3 20x25 quarter | off | 2 | 1738 | 0% | 530.1 | 0/0/0 (0.0) | 0 | yes |
| 005 scenes-v3 20x25 quarter | on, max shared 0.05 | 14 | 1720 | 1% | 517.1 | 47/47/47 (4.9) | 59 | yes |
| 005 scenes-v3 20x25 quarter | on, max shared 0.10 | 12 | 1728 | 1% | 521.9 | 86/94/95 (9.9) | 74 | yes |

Joint construction (no search; see `construct_tray_none`).

| case | mating | classes | largest class | sides in classes <= m | false-fit ratio | shared AB/AC/BC (max %) | wall s | valid |
|---|---|---|---|---|---|---|---|---|
| 6x6 tray none | joint construction | 24 | 6 | 100% | 0.1 | 0/0/0 (0.0) | 0 | yes |
| 9x9 tray none | joint construction | 51 | 6 | 100% | 0.0 | 0/0/0 (0.0) | 0 | yes |
| 10x9 tray none | joint construction | 57 | 6 | 100% | 0.0 | 0/0/0 (0.0) | 0 | yes |
| 12x9 tray none | joint construction | 69 | 6 | 100% | 0.0 | 0/0/0 (0.0) | 0 | yes |
| 21x24 tray none | joint construction | 336 | 6 | 100% | 0.0 | 0/0/0 (0.0) | 0 | yes |

### How close to K(3,3) / K4

- **Tray boards at toy size.** On 6x6 (unit test, 40,000 iterations) the largest class falls from 72 to 36-61 (none) and from 144 to 30-125 (quarter), across seeds and false fits fall by half or more. Classes of exactly 6 appear but most sides stay in one or two big classes.
- **At 80 and 500 pieces the annealer barely moves the classes.** Largest class 144-160 of 160 sides at 10x8 none, 856-864 of 1910 at 25x20, 1676-1738 for quarter. False-fit ratio drops by a third at 10x8 none (28.5 to 18.7), 15% at 10x8 quarter and under 5% at 25x20. Only 0 to 5% of sides end in a class of 6 (4 for andro). The local penalty falls sharply (10x8 none, 2-hop units: about 800 to about 170) but a few leaks per block still join blocks into one giant component, and the number of shared adjacencies it spends (the whole 5% or 10% budget, 5.7% at 25x20 quarter) buys degree-2 sides rather than closed blocks.
- **Longer runs do not help.** With the 2-hop penalty, 10x8 none at 1,000,000 iterations reached the same penalty (171 vs 173 at 200,000) and the same largest class, so the limit is the search landscape, not the budget.
- **What limits it.** (1) The target is a global design: every side's three partners must also be partners of two other sides, in all three solutions at once. A swap changes about eight contacts in one solution and breaks blocks elsewhere. (2) The class maps of the scene runs restrict swaps to pieces of one class and the L background class holds most pieces, so there is room, but the border and the rare transition classes get no say in blocks. (3) The border: standard boards have flat sides, so about 17% of pieces (the frame) have fewer than four contacts and blocks around the frame are partial. (4) Shared adjacencies are a cheat for the penalty (they lower degrees), which the guard bounds but cannot make useful.

### What would work: construct the three solutions jointly

The last table is not search. For a tray in rotation none, give the pieces the elements of G = Z_cols x Z_rows and place piece M_k(x, y) at cell (x, y) in solution k, where M_k is a 2x2 integer matrix that is bijective on G. A piece then touches u + h_k on its east side and u + v_k on its south side. If {h_k} and {v_k} are cosets of order-3 subgroups, every N side meets the S sides of exactly one coset of three pieces and vice versa: each class is K(3,3) and the three solutions are the three perfect matchings of it, a 1-factorization. `construct_tray_none` finds such matrices in milliseconds whenever 3 divides cols x rows and gives largest class 6 (all sides in classes of 6 or 5), zero shared adjacencies and false-fit ratio 0.00 to 0.13. It does not cover 10x8 or 25x20 (80 and 500 are not multiples of 3; 480 = 24x20 and 30x16 were not found with this family; 504 = 21x24 is), standard borders (flat sides need frame pieces), class maps or the quarter-mode K4 (a translation-only design cannot generate K4 because the grid graph would split into cosets; rotations must supply the odd cycles). A production version would (a) choose the block structure first (triples of pieces for each side direction, or quadruples for andro), (b) tile each solution against it as an edge-matching problem with three candidates per neighbour, using the algebraic tiling above as the seed on trays, and (c) hand the result to the annealer, which then only trades a few shared adjacencies for class-map and frame constraints.
