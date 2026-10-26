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
