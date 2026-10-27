# Experiment 007: solver limits (direction A, 8x10)

Question: is the residual shared adjacency a search limit or a constraint limit?

**Result:** a constraint limit. About seven times the iterations and five seeds leave the totals unchanged (37 with no rotation, 13 with quarter rotation).

Run `python3 study.py` (about 3.5 min). Details: `grid.md`, `class-bottlenecks.md`, `results.json`. Totals are AB+AC+BC of 142 adjacencies per board.

## Results (5 seeds per row)

| scene | rotation | iters | best AB/AC/BC (total) | mean total (sd) | gates, best run |
|---|---|---|---|---|---|
| A | none | 300k | 10/13/14 (37) | 37.4 (0.5) | FAIL |
| A | none | 2M | 10/13/14 (37) | 37.2 (0.4) | FAIL |
| A | quarter | 300k | 4/5/4 (13) | 13.0 (0) | PASS |
| A | quarter | 2M | 2/5/6 (13) | 13.0 (0) | PASS |
| B* | none | 300k / 2M | 7/2/4, 6/3/4 (13) | 13.0 (0) | PASS |
| B* | quarter | 300k / 2M | 1/0/0, 0/0/1 (1) | 1.0 (0) | PASS |
| A, no classes | none / quarter | 300k / 2M | 0 | 0.0 | PASS |

\*No direction-B spec exists, so B uses a stub (all classes non-directional, all rotations). Its quarter rows are optimistic.

The saved `run-none` (13/11/15) predates commit 9dad74e; current code gives 10/13/14. The quarter 2/5/6 is the 2M result.

## Bottleneck

- Counting floor (rigorous, A): AB 0, AC 2, BC 3. Random class-respecting placement expects 17.8/19.0/19.8.
- In none mode, ME (24 cells, one region, 34-37 internal edges) and SK (21 cells, 22-24) carry most of the residual: at 2M, ME/ME 2.6 and SK/SK 2.0 of AB 11.2. Quarter rotation brings both to 0.
- Internal edges are not shared adjacencies; pigeonhole is vacuous (e_A + e_B is far below C(24,2) = 276).

## Verdict

The limit is the constraint, not the search budget. About 7x the iterations and five seeds leave totals unchanged. The class-free control reaches 0 in 0.3 s, so the solver can reach zero. The 13 and 37 plateaus are not certified optimal, and the schedule (hard-coded 0.6 to 0.05) was not tested.

## Recommendation

More search is not worthwhile for none mode. Split ME and SK into several regions or thinner shapes: the random baseline scales with e_A x e_B / C(n,2), and ME alone gives 37 x 34 / 276, about 4.6. Quarter rotation is the cheaper lever and already passes gates at 300k. Recheck B with its real spec before trusting its quarter numbers.
