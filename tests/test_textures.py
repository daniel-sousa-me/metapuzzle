import hashlib
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
    (tx.blotch, {"roughness": 0.6}),
    (tx.blotch, {"side": "left", "roughness": 0.6}),
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


# ------------------------------------------------------------------ dabs angle

_ROTATE = re.compile(r"rotate\((-?[\d.]+)\)")
_TRANSLATE = re.compile(r"translate\(([-\d.]+) ([-\d.]+)\) rotate")


def test_dabs_angle_keeps_every_rotation_within_the_jitter_range():
    for seed in range(5):
        frag = tx.dabs(seed, 100.0, PALETTE, count=120, shape="ellipse",
                       angle=0.0, angle_jitter=8.0)
        rots = [float(v) for v in _ROTATE.findall(frag)]
        assert len(rots) > 100
        assert all(abs(r) <= 8.0 + 1e-3 for r in rots), seed
        assert min(rots) < -4.0 and max(rots) > 4.0, seed   # the jitter is used, not zeroed


def test_dabs_angle_without_jitter_sets_every_rotation_exactly():
    frag = tx.dabs(3, 100.0, PALETTE, count=40, angle=90.0)
    assert {float(v) for v in _ROTATE.findall(frag)} == {90.0}


def test_dabs_angle_changes_only_the_orientation():
    # Positions, sizes and colours come from the same draws whatever the angle.
    random_angle = tx.dabs(4, 100.0, PALETTE, count=50, shape="ellipse")
    fixed = tx.dabs(4, 100.0, PALETTE, count=50, shape="ellipse", angle=0.0, angle_jitter=8.0)
    assert _TRANSLATE.findall(random_angle) == _TRANSLATE.findall(fixed)
    sizes = re.compile(r'(rx|ry|fill)="([^"]+)"')
    assert sizes.findall(random_angle) == sizes.findall(fixed)


def test_dabs_default_angle_is_still_random():
    rots = [float(v) for v in _ROTATE.findall(tx.dabs(5, 100.0, PALETTE, count=200))]
    assert min(rots) < 45.0 and max(rots) > 315.0


def test_dabs_angle_arguments_are_checked():
    with pytest.raises(ValueError):
        tx.dabs(1, 100.0, PALETTE, angle=0.0, angle_jitter=-1.0)
    with pytest.raises(ValueError):
        tx.dabs(1, 100.0, PALETTE, angle_jitter=5.0)


# ------------------------------------------------------------------ flower and moon

def _is_color(rgb, color: str, tol: int = 2) -> bool:
    return max(abs(a - b) for a, b in zip(rgb, tx._hex_to_rgb(color))) <= tol


def _unit_px(px, u: float, v: float, size: int = 100, radius_px: float = 25.0):
    """Pixel at unit coordinates (u, v) from the centre, for a motif at scale 0.5 and jitter 0."""
    return px[int(size / 2 + u * radius_px), int(size / 2 + v * radius_px)]


def test_flower_has_a_base_coloured_centre_and_gaps_between_petals():
    frag = tx.motif(1, 100.0, PALETTE, kind="flower", scale=0.5, jitter=0.0)
    px = _render_cell(frag, 100).load()
    assert _is_color(_unit_px(px, 0.0, 0.0), PALETTE[0])            # centre disc
    assert _is_color(_unit_px(px, 0.0, -0.56), PALETTE[1])          # top petal
    # Radius 0.7, midway between the top and upper-right petals: a gap.
    assert _is_color(_unit_px(px, 0.7 * math.cos(math.radians(-54)),
                              0.7 * math.sin(math.radians(-54))), PALETTE[0])


def test_moon_is_a_crescent_with_its_hollow_toward_the_upper_right():
    frag = tx.motif(1, 100.0, PALETTE, kind="moon", scale=0.5, jitter=0.0)
    px = _render_cell(frag, 100).load()
    assert _is_color(_unit_px(px, -0.566, 0.566), PALETTE[1])       # thick lower-left arm
    assert _is_color(_unit_px(px, 0.424, -0.424), PALETTE[0])       # inside the cut-out disc
    marks = sum(1 for x in range(100) for y in range(100) if _is_color(px[x, y], PALETTE[1]))
    assert 0.15 < marks / (math.pi * 25.0 ** 2) < 0.30               # about 22% of the disc


@pytest.mark.parametrize("kind", ["flower", "moon"])
def test_flower_and_moon_render_deterministically_inside_the_margin(kind):
    for seed in (1, 2, 3):
        frag = tx.motif(seed, 100.0, PALETTE, kind=kind, scale=0.68, rotation="any")
        assert tx.motif(seed, 100.0, PALETTE, kind=kind, scale=0.68, rotation="any") == frag
        ET.fromstring(tx.cell_svg(frag, 100.0))
        assert _dirty_pixels(frag, 100, EDGES) == [], (kind, seed)


# ------------------------------------------------------------------ blotch inset

INSET = 0.08
EDGES = ("top", "bottom", "left", "right")


def _dirty_pixels(frag: str, size: int, edges) -> list[tuple[int, int]]:
    """Pixels inside the inset margin of the given edges that are not background."""
    px = _render_cell(frag, size).load()
    m = int(INSET * size) - 1
    base = tx._hex_to_rgb(PALETTE[0])
    bad = []
    for x in range(size):
        for y in range(size):
            in_margin = (("left" in edges and x < m) or ("right" in edges and x >= size - m)
                         or ("top" in edges and y < m) or ("bottom" in edges and y >= size - m))
            if in_margin and max(abs(a - b) for a, b in zip(px[x, y], base)) > 2:
                bad.append((x, y))
    return bad


@pytest.mark.parametrize("coverage", [0.30, 0.45, 1.0])
def test_blotch_inset_keeps_blotches_and_halo_inside_the_margin(coverage):
    # coverage 1.0 makes blotches too large to fit, so they are scaled down to the margin.
    for seed in range(4):
        frag = tx.blotch(seed, 100.0, PALETTE, coverage=coverage, inset=INSET)
        assert _dirty_pixels(frag, 100, EDGES) == [], (coverage, seed)


def test_without_inset_blotches_meet_the_edges():
    # the margin check above is not vacuous: without inset the same seeds reach the edge
    assert any(_dirty_pixels(tx.blotch(seed, 100.0, PALETTE, coverage=0.45), 100, EDGES)
               for seed in range(4))


@pytest.mark.parametrize("side", ["top", "bottom", "left", "right"])
def test_blotch_inset_with_side_insets_only_the_other_edges(side):
    other = tuple(e for e in EDGES if e != side)
    for seed in range(4):
        frag = tx.blotch(seed, 100.0, PALETTE, coverage=0.45, side=side, inset=INSET)
        assert _dirty_pixels(frag, 100, other) == [], (side, seed)
    # the biased edge is still reached, so the transition keeps its cut
    assert any(_dirty_pixels(tx.blotch(seed, 100.0, PALETTE, coverage=0.45, side=side,
                                       inset=INSET), 100, (side,))
               for seed in range(6))


def _mask_margin_hits(clip: str, cid: str, edges, size: int = 100) -> int:
    grid = _mask_coverage(clip, cid, size)
    m = int(INSET * size) - 1
    hits = 0
    for y in range(size):
        for x in range(size):
            in_margin = (("left" in edges and x < m) or ("right" in edges and x >= size - m)
                         or ("top" in edges and y < m) or ("bottom" in edges and y >= size - m))
            hits += in_margin and grid[y][x]
    return hits


@pytest.mark.parametrize("side", [None, "top", "bottom", "left", "right"])
def test_blotch_mask_inset_keeps_the_region_inside_the_margin(side):
    edges = EDGES if side is None else tuple(e for e in EDGES if e != side)
    for seed in range(4):
        clip, cid = tx.blotch_mask(seed, 100.0, PALETTE, coverage=0.45, side=side,
                                   count=3, inset=INSET)
        assert clip.count("<path") == 3                    # inset does not change the count
        assert _mask_margin_hits(clip, cid, edges) == 0, (side, seed)


def test_blotch_mask_inset_shares_geometry_with_blotch():
    clip, _ = tx.blotch_mask(4, 100.0, PALETTE, coverage=0.45, side="left", inset=INSET)
    frag = tx.blotch(4, 100.0, PALETTE, coverage=0.45, side="left", inset=INSET, background=False)
    paths = re.findall(r'<path d="([^"]+)"', clip)
    assert paths
    for d in paths:
        assert f'<path d="{d}" fill="#5b7f5b"/>' in frag


def test_inset_zero_keeps_the_original_output():
    # Golden hashes from before inset existed: the default output must not change.
    def h(s):
        return hashlib.sha256(s.encode()).hexdigest()[:16]
    assert h(tx.blotch(1, 100.0, PALETTE, coverage=0.45)) == "4653e6b097f9a715"
    assert h(tx.blotch_mask(1, 100.0, PALETTE, coverage=0.45)[0]) == "567f7468fb550c82"
    assert tx.blotch(1, 100.0, PALETTE, inset=0.0) == tx.blotch(1, 100.0, PALETTE)
    assert tx.blotch_mask(1, 100.0, PALETTE, inset=0) == tx.blotch_mask(1, 100.0, PALETTE)


@pytest.mark.parametrize("bad", [-0.1, 0.5, 0.9, float("nan")])
def test_inset_must_be_a_fraction_below_one_half(bad):
    with pytest.raises(ValueError, match="inset must be in"):
        tx.blotch(1, 100.0, PALETTE, inset=bad)
    with pytest.raises(ValueError, match="inset must be in"):
        tx.blotch_mask(1, 100.0, PALETTE, inset=bad)



# ------------------------------------------------------------------ roughness and spread

def _vertex_count(d: str) -> int:
    """Vertices in a blotch outline: Q commands for the smooth lobe, L commands plus one
    for the straight-edged polygon."""
    return max(d.count("Q"), d.count("L") + 1)


def test_roughness_zero_keeps_the_golden_outputs():
    # The same hashes as test_inset_zero_keeps_the_original_output, with the new
    # parameters given explicitly at their defaults, plus side-biased outputs.
    def h(s):
        return hashlib.sha256(s.encode()).hexdigest()[:16]
    assert h(tx.blotch(1, 100.0, PALETTE, coverage=0.45, roughness=0.0, spread=1.0)) == "4653e6b097f9a715"
    assert h(tx.blotch_mask(1, 100.0, PALETTE, coverage=0.45, roughness=0.0)[0]) == "567f7468fb550c82"
    assert h(tx.blotch(2, 100.0, PALETTE, coverage=0.45, side="top", inset=0.08)) == "ad02087200495085"
    assert h(tx.blotch_mask(3, 100.0, PALETTE, coverage=0.45, side="right", count=3,
                            inset=0.08)[0]) == "f4d83e4c0bb449c7"
    assert h(tx.blotch(5, 100.0, PALETTE, coverage=0.3, side="bottom")) == "49375d542ebec6a4"
    assert h(tx.blotch(9, 100.0, PALETTE)) == "86bd0e0ae36e244a"
    assert h(tx.blotch_mask(9, 100.0, PALETTE, count=2)[0]) == "7e86f7bbb2f5fb61"


def test_roughness_is_deterministic_and_seed_dependent():
    a = tx.blotch(4, 100.0, PALETTE, roughness=0.6)
    assert tx.blotch(4, 100.0, PALETTE, roughness=0.6) == a
    assert tx.blotch(5, 100.0, PALETTE, roughness=0.6) != a
    b = tx.blotch_mask(4, 100.0, PALETTE, side="top", roughness=0.6, count=3)
    assert tx.blotch_mask(4, 100.0, PALETTE, side="top", roughness=0.6, count=3) == b
    assert tx.blotch_mask(5, 100.0, PALETTE, side="top", roughness=0.6, count=3) != b


def test_roughness_gives_more_vertices():
    smooth = tx.blotch_mask(2, 100.0, PALETTE, coverage=0.45, count=3)[0]
    rough = tx.blotch_mask(2, 100.0, PALETTE, coverage=0.45, count=3, roughness=0.6)[0]
    smooth_d = re.findall(r'<path d="([^"]+)"', smooth)
    rough_d = re.findall(r'<path d="([^"]+)"', rough)
    assert len(smooth_d) == len(rough_d) == 3
    assert all(10 <= _vertex_count(d) <= 14 for d in smooth_d)
    assert all(16 <= _vertex_count(d) <= 28 for d in rough_d)
    assert "Q" not in "".join(rough_d)               # straight edges, not smoothed lobes


def test_band_mask_reaches_both_corners_and_the_whole_top_edge():
    # spread 1 with a side: the band covers the full width of the biased edge, so the
    # top row is covered at every x (both corners included) for every seed.
    for seed in range(6):
        clip, cid = tx.blotch_mask(seed, 100.0, PALETTE, coverage=0.45, side="top",
                                   count=3, roughness=0.6, spread=1.0)
        grid = _mask_coverage(clip, cid)
        assert grid[0][0] and grid[0][99], seed
        assert all(grid[0][x] for x in range(100)), seed


def test_band_spread_covers_only_the_centre():
    for seed in range(6):
        clip, cid = tx.blotch_mask(seed, 100.0, PALETTE, coverage=0.45, side="top",
                                   count=3, roughness=0.6, spread=0.5)
        grid = _mask_coverage(clip, cid)
        assert not grid[0][0] and not grid[0][99], seed
        assert grid[0][50], seed


def test_band_inset_keeps_the_far_edge_clear():
    # coverage 1.0 pushes the depth past the far margin, so the clamp must hold it back.
    for seed in range(4):
        clip, cid = tx.blotch_mask(seed, 100.0, PALETTE, coverage=1.0, side="top",
                                   count=3, inset=INSET, roughness=0.6)
        assert _mask_margin_hits(clip, cid, ("bottom",)) == 0, seed


def test_band_mode_pieces_are_drawn_from_the_side_given():
    # The band lies along the named edge: for "right" the mask covers the right columns.
    clip, cid = tx.blotch_mask(3, 100.0, PALETTE, coverage=0.45, side="right", count=3,
                               roughness=0.6)
    grid = _mask_coverage(clip, cid)
    right = sum(row[x] for row in grid for x in range(67, 100))
    left = sum(row[x] for row in grid for x in range(0, 33))
    assert right > 4 * max(left, 1)


def test_roughness_and_spread_reject_bad_arguments():
    with pytest.raises(ValueError, match="roughness must be in"):
        tx.blotch(1, 100.0, PALETTE, roughness=1.5)
    with pytest.raises(ValueError, match="roughness must be in"):
        tx.blotch_mask(1, 100.0, PALETTE, roughness=-0.1)
    with pytest.raises(ValueError, match="spread must be in"):
        tx.blotch_mask(1, 100.0, PALETTE, side="top", roughness=0.6, spread=1.2)
    with pytest.raises(ValueError, match="spread applies only"):
        tx.blotch(1, 100.0, PALETTE, side="top", spread=0.5)           # roughness 0
    with pytest.raises(ValueError, match="spread applies only"):
        tx.blotch(1, 100.0, PALETTE, roughness=0.6, spread=0.5)        # no side


# ------------------------------------------------------------------ march_mask

MARCH_EDGE = ("straight", "corner", "corner_in", "cap")
MARCH_ENDS = {                       # pinned path endpoints (size 100)
    "straight": ((0.0, 50.0), (100.0, 50.0)),
    "cap": ((0.0, 50.0), (100.0, 50.0)),
    "corner": ((0.0, 50.0), (50.0, 100.0)),
    "corner_in": ((0.0, 50.0), (50.0, 0.0)),
}
MARCH_TAIL = {                       # mass-polygon corners after the path
    "straight": [(100.0, 0.0), (0.0, 0.0)],
    "cap": [(100.0, 0.0), (0.0, 0.0)],
    "corner": [(100.0, 100.0), (100.0, 0.0), (0.0, 0.0)],
    "corner_in": [(0.0, 0.0)],
}


def _march_pts(clip: str) -> list[tuple[float, float]]:
    m = re.search(r'<polygon points="([^"]+)"', clip)
    assert m, clip[:200]
    return [tuple(map(float, p.split(","))) for p in m.group(1).split()]


@pytest.mark.parametrize("roughness", [0.0, 0.5, 1.0])
@pytest.mark.parametrize("pattern", MARCH_EDGE)
def test_march_path_is_pinned_at_mid_edges(pattern, roughness):
    # The boundary enters and leaves at the exact edge midpoints, and nowhere else touches
    # an edge: that is what lets neighbouring transition cells join.
    for seed in range(10):
        clip, _ = tx.march_mask(seed, 100.0, None, pattern=pattern, roughness=roughness)
        pts = _march_pts(clip)
        k = len(MARCH_TAIL[pattern])
        path = pts[:-k]
        assert pts[-k:] == MARCH_TAIL[pattern], (pattern, seed)
        assert (path[0], path[-1]) == MARCH_ENDS[pattern], (pattern, seed)
        assert 12 <= len(path) <= 20, (pattern, seed)
        for x, y in path[1:-1]:
            assert 0.0 < x < 100.0 and 0.0 < y < 100.0, (pattern, seed, x, y)


def test_march_wobble_is_capped_so_paths_stay_inside():
    for pattern in MARCH_EDGE:
        for seed in range(20):
            clip, _ = tx.march_mask(seed, 100.0, None, pattern=pattern, roughness=1.0,
                                    wobble=0.2)
            for x, y in _march_pts(clip)[1:-4]:
                assert 0.0 < x < 100.0 and 0.0 < y < 100.0, (pattern, seed)
    with pytest.raises(ValueError, match="wobble must be in"):
        tx.march_mask(1, 100.0, None, wobble=0.3)


def test_march_roughness_zero_is_straight_between_the_pinned_points():
    clip, _ = tx.march_mask(4, 100.0, None, pattern="straight", roughness=0.0)
    assert all(y == 50.0 for _, y in _march_pts(clip)[:-2])
    clip, _ = tx.march_mask(4, 100.0, None, pattern="corner", roughness=0.0)
    path = _march_pts(clip)[:-3]
    # collinear with (0, 50) and (50, 100): the cross product of each point's offset is zero
    for x, y in path:
        assert abs((x - 0.0) * 50.0 - (y - 50.0) * 50.0) < 1e-6


def test_march_mass_is_on_the_documented_side():
    for seed in range(6):
        grid = _mask_coverage(*tx.march_mask(seed, 100.0, None, pattern="straight"))
        assert all(grid[0][x] for x in range(100))              # whole top edge is mass
        assert not any(grid[99][x] for x in range(100))         # bottom edge is base
        assert grid[10][50] and not grid[90][50]

        grid = _mask_coverage(*tx.march_mask(seed, 100.0, None, pattern="corner"))
        assert grid[0][0] and grid[0][99] and grid[99][99]      # top and right are mass
        assert not grid[99][0]                                   # bottom-left is base

        grid = _mask_coverage(*tx.march_mask(seed, 100.0, None, pattern="corner_in"))
        assert grid[0][0] and not grid[0][99] and not grid[99][0] and not grid[99][99]

        grid = _mask_coverage(*tx.march_mask(seed, 100.0, None, pattern="cap"))
        assert all(grid[0][x] for x in range(100))              # still touches the top
        assert grid[60][50] and not grid[90][50]                # the tongue reaches down
        assert not grid[95][1] and not grid[95][98]             # sides are base low down

        grid = _mask_coverage(*tx.march_mask(seed, 100.0, None, pattern="dot"))
        assert grid[50][50] and not grid[0][0] and not grid[99][99]


def test_march_cap_dips_deeper_than_straight():
    for seed in range(8):
        cap = _march_pts(tx.march_mask(seed, 100.0, None, pattern="cap")[0])[:-2]
        straight = _march_pts(tx.march_mask(seed, 100.0, None, pattern="straight")[0])[:-2]
        assert max(y for _, y in cap) >= 70.0, seed          # about 70-80% of the height
        assert max(y for _, y in straight) <= 50.0 + 0.12 * 100 * 0.5 + 1e-6, seed


def test_march_dot_never_touches_the_edge():
    for seed in range(40):
        clip, cid = tx.march_mask(seed, 100.0, None, pattern="dot", roughness=1.0)
        for x, y in _march_pts(clip):
            assert 8.0 <= x <= 92.0 and 8.0 <= y <= 92.0, (seed, x, y)
    for seed in range(4):
        clip, cid = tx.march_mask(seed, 100.0, None, pattern="dot", roughness=1.0)
        assert _mask_margin_hits(clip, cid, EDGES) == 0, seed


def test_march_dot_inset_keeps_the_blob_inside_the_margin():
    for seed in range(20):
        clip, _ = tx.march_mask(seed, 100.0, None, pattern="dot", inset=0.3)
        for x, y in _march_pts(clip):
            assert 30.0 - 1e-6 <= x <= 70.0 + 1e-6 and 30.0 - 1e-6 <= y <= 70.0 + 1e-6, seed


def test_march_dot_diameter_is_about_half_the_cell():
    xs = [x for x, _ in _march_pts(tx.march_mask(3, 100.0, None, pattern="dot", roughness=0.0)[0])]
    assert 50.0 <= max(xs) - min(xs) <= 60.0


@pytest.mark.parametrize("pattern", tx._MARCH_PATTERNS)
def test_march_is_deterministic_and_seed_dependent(pattern):
    a = tx.march_mask(7, 100.0, None, pattern=pattern)
    assert tx.march_mask(7, 100.0, None, pattern=pattern) == a
    assert tx.march_mask(8, 100.0, None, pattern=pattern) != a
    # the palette is not read; it only enters the clip id
    body = lambda clip: clip[clip.index('<polygon'):]
    assert body(tx.march_mask(7, 100.0, PALETTE, pattern=pattern)[0]) == body(a[0])


def test_march_mask_is_registered_for_class_specs_and_exported():
    assert classes.MASK_PRIMITIVES["march_mask"] is tx.march_mask
    assert "march_mask" in tx.__all__


def test_march_mask_rejects_bad_arguments():
    with pytest.raises(ValueError, match="pattern must be one of"):
        tx.march_mask(1, 100.0, None, pattern="spiral")
    with pytest.raises(ValueError, match="roughness must be in"):
        tx.march_mask(1, 100.0, None, roughness=1.5)
    with pytest.raises(ValueError, match="inset must be in"):
        tx.march_mask(1, 100.0, None, inset=0.5)


def test_march_mask_extra_keywords_are_ignored_and_not_keyed():
    a = tx.march_mask(2, 100.0, None, pattern="corner")
    assert tx.march_mask(2, 100.0, None, pattern="corner", unused=1) == a


def test_march_mask_class_spec_layer_renders():
    spec = classes.ClassSpec.from_dict({
        "palette": {"paper": "#e8dcc4", "ink": "#2f4f4f"},
        "classes": {"edge": {"layers": [
            {"primitive": "stipple", "palette": ["paper", "ink"]},
            {"primitive": "stipple", "palette": ["ink", "paper"],
             "mask": {"primitive": "march_mask", "params": {"pattern": "corner"}}},
        ]}},
    })
    spec.validate()
    frag = spec.drawer()("p1", "edge", 3, 64.0)
    assert 'clipPath id="clip-march_mask-' in frag
    ET.fromstring(tx.cell_svg(frag, 64.0))
