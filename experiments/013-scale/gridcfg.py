"""Grid size for experiment 013 (scale study).

Set with the GRID environment variable, COLSxROWS (default 20x25, the 005 grid):
    GRID=25x30 python make_targets.py -v2
Outputs go to g<COLS>x<ROWS>/ next to this file.

Shape geometry is defined once, in 005's 20x25 reference units (REF_COLS x REF_ROWS), and the
sampling grid maps each cell onto that reference frame. A figure therefore keeps its place and
proportions on the board at every size, and only the resolution changes.
"""
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLS, ROWS = (int(v) for v in os.environ.get("GRID", "20x25").lower().split("x"))
CELLS = COLS * ROWS
WORK = HERE / f"g{COLS}x{ROWS}"
REF_COLS, REF_ROWS = 20, 25
