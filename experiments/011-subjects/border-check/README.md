# Border check: standard border with seams (011, 27x38)

**Scenes:** no `27x38-v2/pipeline-out/` exists yet, and `27x38/pipeline/v3/` does not either. Used `../pipeline/v3/scenes.txt` with `../pipeline/classes-v9.json`. Command: `metapuzzle prototype --border standard --rotation quarter --cell 21 --extra-flat N`.

**Results (all runs fail):**

| N | exit | outcome |
|---|---|---|
| 0 | 1 | SceneError: border class counts differ between maps A and B at edge |
| 20 | 2 | invalid: 10 mismatched contacts (energy 0), shared 0/0/0 |
| 40 | 2 | invalid: 10 mismatched contacts |
| 80 | 2 | invalid: 10 mismatched contacts |

No valid run, so no shared-adjacency, seam or triptych record. `run_prototype` has no `strict_border` option; `extra_flat > 0` already skips the count check, so the failure is validity.

**Cause (diagnostics in this folder):** `build_valid_layout` returns None on all three boards (25 tries), so the solver starts random and cannot remove the mismatches. Seam partners are same-class only (sampled placements on A, B, C). Each class's leftover flat edges must then be even on every board. Extra pieces add the same count to all three boards, so the parity differences are fixed for any N. Leftover parity differs across boards for every class (A-B: D, L, S, W; A-C: M).

**Recommendation:** keep `--border tray` for this set. Standard needs either matched 1-side border class counts (or at least matched parity) across the three maps, or seams that can pair across classes. Neither is a flag change.
