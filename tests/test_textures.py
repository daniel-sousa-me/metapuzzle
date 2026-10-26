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


# ------------------------------------------------------------------ blotch_mask

def _mask_coverage(clip: str, cid: str, size: int = 100) -> list[list[bool]]:
    """Rasterise a mask at the cell's own size: True where the clip path covers the cell."""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
           f'viewBox="0 0 {size} {size}">'
           f'<defs>{clip}</defs><rect width="{size}" height="{size}" fill="#fff"/>'
           f'<rect width="{size}" height="{size}" fill="#000" clip-path="url(#{cid})"/></svg>')
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=size, output_height=size)
    px = Image.open(io.BytesIO(png)).convert("L").load()
    return [[px[x, y] < 128 for x in range(size)] for y in range(size)]


def test_blotch_mask_returns_a_clip_path_with_its_id():
    clip, cid = tx.blotch_mask(3, 100.0, PALETTE, coverage=0.35, side="right")
    assert cid.startswith("clip-blotch_mask-3-")
    assert clip.startswith(f'<clipPath id="{cid}">') and clip.endswith("</clipPath>")
    assert "<rect" not in clip and "fill" not in clip      # outlines only, no paint
    root = ET.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg">{clip}</svg>')
    assert root.find("{http://www.w3.org/2000/svg}clipPath") is not None


def test_blotch_mask_is_deterministic_and_seed_dependent():
    a = tx.blotch_mask(7, 100.0, PALETTE, coverage=0.35, side="bottom")
    assert tx.blotch_mask(7, 100.0, PALETTE, coverage=0.35, side="bottom") == a
    assert tx.blotch_mask(8, 100.0, PALETTE, coverage=0.35, side="bottom") != a


def test_blotch_mask_count_sets_the_number_of_blotches():
    for n in (1, 2, 3, 6):
        clip, _ = tx.blotch_mask(5, 100.0, PALETTE, count=n)
        assert clip.count("<path") == n
    clip, _ = tx.blotch_mask(5, 100.0, PALETTE)          # default: 1 to 3
    assert 1 <= clip.count("<path") <= 3


def test_blotch_mask_side_biases_the_covered_area():
    right = left = 0
    for seed in range(12):
        clip, cid = tx.blotch_mask(seed, 100.0, PALETTE, coverage=0.35, side="right", count=3)
        grid = _mask_coverage(clip, cid)
        right += sum(row[x] for row in grid for x in range(67, 100))
        left += sum(row[x] for row in grid for x in range(0, 33))
    assert right > 2 * left


def test_blotch_mask_edge_is_ragged():
    # Different seeds give different boundaries, so the mask is not a fixed shape.
    shapes = set()
    for seed in range(6):
        clip, cid = tx.blotch_mask(seed, 100.0, PALETTE, coverage=0.35, side="bottom", count=3)
        shapes.add(tuple(map(tuple, _mask_coverage(clip, cid))))
    assert len(shapes) == 6


def test_blotch_mask_rejects_bad_arguments():
    with pytest.raises(ValueError):
        tx.blotch_mask(1, 100.0, PALETTE, side="diagonal")
    with pytest.raises(ValueError):
        tx.blotch_mask(1, 100.0, PALETTE, coverage=1.5)
    for bad in (0, 7, 2.5):
        with pytest.raises(ValueError):
            tx.blotch_mask(1, 100.0, PALETTE, count=bad)


def test_blotch_mask_shares_geometry_with_blotch():
    # Same seed and parameters: the mask's outlines are exactly blotch's outlines.
    clip, _ = tx.blotch_mask(4, 100.0, PALETTE, coverage=0.35, side="left")
    frag = tx.blotch(4, 100.0, PALETTE, coverage=0.35, side="left", background=False)
    paths = re.findall(r'<path d="([^"]+)"', clip)
    assert paths
    for d in paths:
        assert f'<path d="{d}" fill="#5b7f5b"/>' in frag


# ------------------------------------------------------------------ motif offset and new kinds

def _center(frag: str) -> tuple[float, float]:
    m = re.search(r'<g transform="translate\(([-\d.]+) ([-\d.]+)\)', frag)
    assert m, frag[:200]
    return float(m.group(1)), float(m.group(2))


def test_motif_offset_shifts_the_center():
    base = tx.motif(2, 100.0, MOTIF_PALETTE, kind="disc", jitter=0.0)
    moved = tx.motif(2, 100.0, MOTIF_PALETTE, kind="disc", jitter=0.0, offset=(0.1, -0.1))
    assert _center(base) == (50.0, 50.0)
    assert _center(moved) == (60.0, 40.0)


def test_motif_default_offset_is_a_no_op():
    a = tx.motif(9, 100.0, MOTIF_PALETTE, kind="fish", jitter=0.12)
    assert a == tx.motif(9, 100.0, MOTIF_PALETTE, kind="fish", jitter=0.12, offset=(0.0, 0.0))
    assert _center(a) == _center(tx.motif(9, 100.0, MOTIF_PALETTE, kind="fish", jitter=0.12))


def test_motif_offset_is_clamped_to_the_margin():
    # scale 0.5: radius 25, so the center stays in [8 + 25, 100 - 8 - 25] = [33, 67].
    right = tx.motif(1, 100.0, MOTIF_PALETTE, kind="disc", scale=0.5, jitter=0.0, offset=(0.6, 0.0))
    left = tx.motif(1, 100.0, MOTIF_PALETTE, kind="disc", scale=0.5, jitter=0.0, offset=(-0.6, 0.0))
    assert _center(right) == (67.0, 50.0)
    assert _center(left) == (33.0, 50.0)


@pytest.mark.parametrize("kind", tx.MOTIF_KINDS)
@pytest.mark.parametrize("offset", [(0.5, 0.5), (-0.5, 0.2), (0.3, -0.45)])
def test_motif_with_offset_stays_inside_the_margin(kind, offset):
    size = 100
    margin = int(0.08 * size) - 1
    frag = tx.motif(3, float(size), MOTIF_PALETTE, kind=kind, scale=0.5, jitter=0.0, offset=offset)
    px = _render_cell(frag, size).load()
    for x in range(size):
        for y in range(size):
            if x < margin or x >= size - margin or y < margin or y >= size - margin:
                assert max(abs(c - 255) for c in px[x, y]) <= 2, (kind, offset, x, y)


def test_motif_rejects_bad_offsets():
    with pytest.raises(ValueError):
        tx.motif(1, 100.0, MOTIF_PALETTE, offset=(0.1,))
    with pytest.raises(ValueError):
        tx.motif(1, 100.0, MOTIF_PALETTE, offset=(float("nan"), 0.0))


def test_hull_is_a_hull_without_mast_or_sail():
    frag = tx.motif(1, 100.0, MOTIF_PALETTE, kind="hull", jitter=0.0)
    assert frag.count("<path") == 1
    assert "<line" not in frag and "<polygon" not in frag


def test_fleck_is_a_soft_blob():
    frag = tx.motif(1, 100.0, MOTIF_PALETTE, kind="fleck", jitter=0.0)
    assert 'fill-opacity="0.92"' in frag and frag.count("<path") == 1
