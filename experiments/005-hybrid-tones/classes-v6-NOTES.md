# 005 classes v6: chip-signature sub-classes

`gen_classes_v6.py` writes `classes-v6.json` (68 classes, validated with `load_class_spec`), `contact-sheet-v6.png` and `chip-field-v6.png`. v4 files are unchanged.

## Counts

| Group | Classes | Count |
|---|---|---|
| Plain | D, M, L, S, W | 5 |
| Light sub-classes (cream ground) | Lr, Lb, Lo, Lx | 4 |
| Mid sub-classes (olive ground) | Mr, Mb, Mc | 3 |
| Transitions (plain tiers only) | 4 patterns x ordered pairs of D, M, L, W | 48 |
| Dots (D/L pair) | DLd, LDd | 2 |
| Motifs on L | SUN, FLO, FLB, CLD, LEF, MOON | 6 |

Transitions are the same 48 + 2 as v4. No sub-class has transitions.

## Sub-class chips

Each chip is a `motif` layer, kind `fleck` (small irregular blob), with:
- `scale` 0.125: the enclosing diameter is about 1/8 of the piece side. This is my reading of "about 1/8 of the piece".
- `rotation` "any": each chip gets its own seeded angle.
- `offset` from one of four fixed sites, plus `jitter` 0.08 per axis.

| Class | Ground | Chips |
|---|---|---|
| L | cream | 1 sand (very sparse, neutral) |
| Lr | cream | 3 rust |
| Lb | cream | 4 pale blue |
| Lo | cream | 2 olive |
| Lx | cream | 1 rust, 1 pale blue, 1 olive |
| M | olive | 1 sand (very sparse, neutral) |
| Mr | olive | 3 rust |
| Mb | olive | 3 pale blue |
| Mc | olive | 2 cream |

Chip counts are fixed per class, not random within the 2 to 4 range. Chip positions vary by about 8% of the side around each site.

## How the chips stay inside

`scatter_shapes` and `dabs` have no inset parameter, and their marks run past the cell edge. `motif` is the only existing primitive that places one shape at a chosen position. The src primitive set is fixed, so I did not add a new one.

Each chip lies inside the 10% inset if |offset| + jitter <= 0.5 - 0.10 - 0.125/2 = 0.3375. The largest offset is 0.20 and the jitter is 0.08, so the bound holds with margin. `_check_sites` enforces it at build time. `motif`'s own 8% clamp never acts.

Rendered check, 4 seeds per class at 400 px: the smallest clearance from any chip to a piece edge is 0.177 to 0.195 of the side. The requirement is at least 0.10.

## Changes beyond the request

- **L and M recipes are replaced.** v4 used busy dab textures. Sub-classes need a calm ground to read at 64 px, and they must read as the same ground when adjacent, so I made L and M flat grounds with one sand chip each. The request asked for this change to L. The change to M was my call, to keep Mr, Mb and Mc on the same footing as L.
- **Transitions, W and the six motifs use the new L and M recipes.** 59 of the 61 v4 classes have different layers in v6. D and S are unchanged.
- **W** is still M plus horizontal cream lenses. Its lenses are `dabs` and are not inset. They are not chips in the sub-class sense, so I left them alone.
- **Mid chip colours.** The request said "Mr, Mb, Mc (cream chips)". I read the letter as the chip colour: r rust, b pale blue, c cream.

## Validation

- `load_class_spec` validates every layer, mask and rotation.
- Chip pixel fractions per class (mean of 4 seeds, from the run): Lr rust 1.6%, Lb pale blue 2.2%, Lo olive 1.0%, Lx about 0.5% each of rust, pale blue and olive, L sand 0.5%, Mr rust 1.6%, Mb pale blue 1.6%, Mc cream 1.0%. Each sub-class has only its own chip colours on its ground.
- Contact sheet at 64 px, 4 seeds per class (L, Lr, Lb, Lo, Lx, M, Mr, Mb, Mc): the chip colours are distinct on each ground.
- Mixed field: 3x3 cells at 96 px, each a random pick of L, Lr, Lb or Lo, rotated randomly, no borders. It reads as one cream surface with scattered chips.

## Limitations

- Pale blue on cream is the weakest signature at 64 px. Lb uses four chips to compensate.
- Chips sit at four fixed sites. Pieces within a class share a chip layout that varies only slightly, so chip position is not a per-piece cue.
- Chip sizes are set in the spec, not by the scene. Scene arrangement of the sub-classes is outside this file.
