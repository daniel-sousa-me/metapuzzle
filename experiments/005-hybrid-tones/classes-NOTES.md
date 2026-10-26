# 005 classes: notes

**Palette** (8 colours; CIE L* in brackets): indigo base D (23) with slate and rust chips; olive base M (57) with ochre, sand and slate chips; cream base L (90) with sand and pale-blue chips. Tiers are evenly spaced in L*.

**Plain tiers**: `dabs`, count 60, length 0.2 (14 to 24 units at ref_size 100), mixed shapes. Slate is shared by D and M, sand by M and L, so their steps are crossed by shared chips.

**Transitions**: base tier texture, then the neighbour's full dabs texture (background on) under `blotch_mask` with `side: top`, coverage 0.45, count 3, inset 0.08. The mass reaches the top edge and stays off the other edges.

**Issues**
- D|L shares no chip, so it stays a hard step.
- Dabs are clipped at cell edges, so cut marks can still show seams between same-class neighbours.
- Transition boundaries read as rounded lobes more than ragged edges.
- `pairs-sheet.png` comes from `render_sheets.py`, not `pairs_sheet` (horizontal pairs only), so it stacks transitions over their neighbour. It uses the private `_SHEET_*` constants.
- Three passes: lightness and inset; count 3; more shared chips.
