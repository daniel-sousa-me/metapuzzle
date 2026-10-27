# 005 classes v4: notes

`gen_classes_v4.py` writes `classes-v4.json`: 60 classes, validated with `load_class_spec`.

**Counts**: 5 plain (D, M, L from v3; new S, W); 48 transitions (ordered pairs of D, M, L, W times s, c, i, p); 2 dots (DLd, LDd, the D/L pair only); 5 motifs (SUN, FLO, FLB, CLD, LEF, on the L recipe).

**Tuning**: S is leaf/blob chips, scale 0.06, count 200, measured 55% cover. W is M plus cream ellipse lenses, length 0.25, width 0.06, count 34, measured 15% cover.

**Transitions**: own tier is the base; the neighbour tier is the mass under a named `edge` march_mask (roughness 0.5, wobble 0.12). Rotation 0 puts the neighbour on top.

**Limitations**
- `dabs` and `scatter_shapes` take no orientation, so W's lenses are random-angle. They read as a flecked mid-tone, not horizontal waves. Fixing this needs an angle option in `dabs`, a src change not made here.
- No motif is a flower; FLO and FLB use the five-point `star`.
- CLD uses the `fleck` kind, not a blob.
- Chips do not cross cell cuts; only the boundary joins.
