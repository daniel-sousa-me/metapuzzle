import math
import re
import xml.etree.ElementTree as ET

import pytest

from metapuzzle import texture_demo
from metapuzzle import textures as tx

PALETTE = ["#e8dcc4", "#5b7f5b", "#2f4f4f", "#c9a66b"]

PRIMITIVES = [
    (tx.stipple, {}),
    (tx.dabs, {}),
    (tx.mosaic, {}),
    (tx.hatch_multi, {}),
    (tx.scatter_shapes, {}),
    (tx.blotch, {"side": "left"}),
]


@pytest.mark.parametrize("fn, params", PRIMITIVES, ids=lambda v: getattr(v, "__name__", str(v)))
def test_primitive_is_deterministic_clipped_and_seed_dependent(fn, params):
    a = fn(7, 100.0, PALETTE, **params)
    assert a.strip()
    assert "<svg" not in a
    assert 'clip-path="url(#clip-' in a
    assert fn(7, 100.0, PALETTE, **params) == a
    assert fn(8, 100.0, PALETTE, **params) != a


@pytest.mark.parametrize("fn, params", PRIMITIVES, ids=lambda v: getattr(v, "__name__", str(v)))
def test_primitive_is_well_formed_svg(fn, params):
    frag = fn(3, 110.0, PALETTE, **params)
    root = ET.fromstring(tx.cell_svg(frag, 110.0))
    assert root.tag.endswith("svg")


def test_clip_ids_are_unique_within_one_sheet():
    a = tx.stipple(1, 100.0, PALETTE)
    b = tx.stipple(2, 100.0, PALETTE)
    c = tx.dabs(1, 100.0, PALETTE)
    ids = [re.search(r'clipPath id="([^"]+)"', s).group(1) for s in (a, b, c)]
    assert len(set(ids)) == 3


def test_stipple_has_no_thinning_at_cell_edges():
    # A mark counts toward a band if its disc touches the band. Marks spawned
    # only inside the cell would thin out near the edge (their centers stop at
    # the boundary), which shows as a light band where two cells meet.
    size = 100.0
    band = 10.0
    edge = interior = 0
    for seed in range(50):
        root = ET.fromstring(tx.cell_svg(tx.stipple(seed, size, PALETTE, density=400), size))
        for c in root.iter("{http://www.w3.org/2000/svg}circle"):
            x, r = float(c.get("cx")), float(c.get("r"))
            if x - r < band and x + r > 0.0:
                edge += 1
            if x - r < 55.0 and x + r > 45.0:
                interior += 1
    assert interior > 0
    assert 0.9 < edge / interior < 1.1


def test_invalid_arguments_raise():
    with pytest.raises(ValueError):
        tx.blotch(1, 100.0, PALETTE, side="diagonal")
    with pytest.raises(ValueError):
        tx.hatch_multi(1, 100.0, PALETTE, families=5)
    with pytest.raises(ValueError):
        tx.scatter_shapes(1, 100.0, PALETTE, kinds=("star",))


def test_demo_sheet_renders_png(tmp_path):
    svg_path, png_path = texture_demo.main(out_dir=tmp_path)
    assert svg_path.read_text(encoding="utf-8").startswith("<svg")
    assert png_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
