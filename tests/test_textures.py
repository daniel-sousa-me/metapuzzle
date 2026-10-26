import io
import math
import re
import xml.etree.ElementTree as ET

import cairosvg
import pytest
from PIL import Image

from metapuzzle import classes
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


# ------------------------------------------------------------------ motif

MOTIF_PALETTE = ["#ffffff", "#000000", "#777777"]   # base, mark, halo


def _render_cell(frag: str, size: int) -> Image.Image:
    svg = tx.cell_svg(frag, float(size))
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=size, output_height=size)
    return Image.open(io.BytesIO(png)).convert("RGB")


@pytest.mark.parametrize("kind", tx.MOTIF_KINDS)
def test_every_motif_kind_renders_deterministically(kind):
    a = tx.motif(4, 100.0, MOTIF_PALETTE, kind=kind)
    root = ET.fromstring(tx.cell_svg(a, 100.0))
    assert root.tag.endswith("svg")
    assert tx.motif(4, 100.0, MOTIF_PALETTE, kind=kind) == a
    assert tx.motif(5, 100.0, MOTIF_PALETTE, kind=kind) != a


@pytest.mark.parametrize("kind", tx.MOTIF_KINDS)
@pytest.mark.parametrize("rotation", ["none", "any", "flip"])
@pytest.mark.parametrize("scale", [0.5, 0.68])   # 0.68 is the largest scale that fits at jitter 0.08
def test_motif_stays_inside_the_margin(kind, rotation, scale):
    size = 100
    margin = int(0.08 * size) - 1    # strip width whose pixels must all be background
    for seed in (1, 2):
        frag = tx.motif(seed, float(size), MOTIF_PALETTE, kind=kind, scale=scale,
                        rotation=rotation)
        img = _render_cell(frag, size)
        px = img.load()
        for x in range(size):
            for y in range(size):
                if x < margin or x >= size - margin or y < margin or y >= size - margin:
                    assert max(abs(c - 255) for c in px[x, y]) <= 2, (kind, seed, x, y)
        # the shape is actually drawn somewhere inside the cell
        ink = sum(1 for x in range(size) for y in range(size) if px[x, y][0] < 128)
        assert ink > 20, (kind, seed)


def test_motif_rejects_bad_arguments():
    with pytest.raises(ValueError):
        tx.motif(1, 100.0, MOTIF_PALETTE, kind="cloud")
    with pytest.raises(ValueError):
        tx.motif(1, 100.0, MOTIF_PALETTE, rotation="spin")
    with pytest.raises(ValueError):
        tx.motif(1, 100.0, MOTIF_PALETTE, scale=0.7)          # 0.35 + 0.08 > 0.42
    with pytest.raises(ValueError):
        tx.motif(1, 100.0, MOTIF_PALETTE, color_index=3)
    with pytest.raises(ValueError):
        tx.motif(1, 100.0, MOTIF_PALETTE, halo=0.3, halo_color_index=9)


def test_motif_halo_draws_translucent_circles_behind_the_shape():
    plain = tx.motif(2, 100.0, MOTIF_PALETTE, kind="star")
    halo = tx.motif(2, 100.0, MOTIF_PALETTE, kind="star", halo=0.5)
    assert "fill-opacity" not in plain
    root = ET.fromstring(tx.cell_svg(halo, 100.0))
    circles = [e for e in root.iter("{http://www.w3.org/2000/svg}circle")
               if e.get("fill-opacity") is not None]
    assert 2 <= len(circles) <= 3
    opacities = [float(e.get("fill-opacity")) for e in circles]
    radii = [float(e.get("r")) for e in circles]
    assert radii == sorted(radii, reverse=True)           # outermost first
    assert opacities == sorted(opacities)                 # opacity rises inward


def test_motif_flip_mirrors_about_half_the_seeds():
    flips = 0
    for seed in range(40):
        frag = tx.motif(seed, 100.0, MOTIF_PALETTE, kind="fish", rotation="flip")
        flips += "scale(-" in frag
    assert 10 < flips < 30


def test_motif_is_registered_for_class_specs():
    assert classes.PRIMITIVES["motif"] is tx.motif
