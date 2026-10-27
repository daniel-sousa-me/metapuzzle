"""Outline ("ink") layers: march_line outline_of, and the ink class spec in experiments/005."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from metapuzzle import textures as tx
from metapuzzle.classes import ClassSpec, ClassSpecError, load_class_spec

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "005-hybrid-tones"
INK_SPEC = EXP / "classes-ink.json"
V4_SPEC = EXP / "classes-v4.json"
MOTIFS = {"SUN", "FLO", "FLB", "CLD", "LEF", "MOON"}
WHITE = {"#ffffff", "none"}
BLACK_AND_WHITE = {"#ffffff", "#000000", "none"}


def _mini(layers, masks=None, cls="T"):
    spec = {"palette": {"white": "#ffffff", "black": "#000000", "ink": "#2b3262"},
            "classes": {cls: {"layers": layers, **({"masks": masks} if masks else {})}}}
    return ClassSpec.from_dict(spec)


EDGE = {"edge": {"primitive": "march_mask", "params": {"pattern": "corner", "roughness": 0.5}}}
BASE = {"primitive": "stipple", "palette": ["white"], "params": {"density": 0}}
LINE = {"primitive": "march_line", "palette": ["white", "black"], "params": {"stroke": 0.03},
        "outline_of": "edge", "background": False}


def _pts(svg, element):
    body = svg.split("</clipPath>")[-1] if element == "polyline" else svg
    m = re.search(rf'<{element} points="([^"]+)"', body)
    assert m, svg[:300]
    return [tuple(map(float, p.split(","))) for p in m.group(1).split()]


def _mask_pts(svg):
    clip = re.search(r"<clipPath[^>]*>(.*?)</clipPath>", svg, re.S).group(1)
    return _pts(clip, "polygon")


# corners that close each edge pattern's mass polygon, after the path (see march_mask)
CLOSE = {"straight": 2, "cap": 2, "corner": 3, "corner_in": 1}


# ------------------------------------------------------------- outline_of

def test_outline_layer_draws_the_full_pieces_mask_boundary():
    spec = _mini([BASE, {"primitive": "stipple", "palette": ["ink"], "mask": "edge",
                         "params": {"density": 80}}, LINE], EDGE)
    draw = spec.drawer()
    for seed in range(8):
        full = draw("p", "T", seed, 100.0)
        ink = _mini([BASE, LINE], EDGE).drawer()("p", "T", seed, 100.0)
        assert _pts(ink, "polyline") == _mask_pts(full)[:-CLOSE["corner"]], seed


def test_outline_layer_is_not_clipped_to_its_mask():
    frag = _mini([BASE, LINE], EDGE).drawer()("p", "T", 3, 100.0)
    assert "clip-path=\"url(#clip-march_mask" not in frag   # no mask clip; the cell clip only
    assert "<clipPath id=\"clip-march_mask" not in frag     # the mask is not even written


def test_outline_layer_params_come_from_the_mask_and_its_own_ink():
    spec = _mini([BASE, LINE], EDGE)
    (layer,) = [layer for layer in spec.classes["T"].layers if layer.outline_of]
    assert layer.params == {"pattern": "corner", "roughness": 0.5, "stroke": 0.03}


@pytest.mark.parametrize("layer, mask, fragment", [
    ({**LINE, "outline_of": "nope"}, EDGE, "unknown mask 'nope'"),
    ({**LINE, "mask": "edge"}, EDGE, "cannot both be set"),
    ({**LINE, "params": {"stroke": 0.03, "pattern": "cap"}}, EDGE, "come from the mask"),
    ({**LINE, "primitive": "stipple", "params": {}}, EDGE, "outline_of applies only"),
    (LINE, {"edge": {"primitive": "blotch_mask"}}, "needs a march_mask"),
    ({**LINE, "outline_of": 3}, EDGE, "must be the name of a mask"),
])
def test_outline_layer_errors_are_reported(layer, mask, fragment):
    data = {"palette": {"white": "#ffffff", "black": "#000000"},
            "classes": {"T": {"layers": [BASE, layer], "masks": mask}}}
    with pytest.raises(ClassSpecError, match=fragment):
        ClassSpec.from_dict(data).validate()


def test_outline_mask_must_be_used_and_defined():
    data = {"palette": {"white": "#ffffff"}, "classes": {"T": {"layers": [BASE], "masks": EDGE}}}
    with pytest.raises(ClassSpecError, match="defined but not used"):
        ClassSpec.from_dict(data).validate()


def test_unknown_keyword_on_march_line_is_rejected_not_swallowed():
    data = {"palette": {"white": "#ffffff", "black": "#000000"},
            "classes": {"T": {"layers": [BASE, {**LINE, "params": {"stroek": 0.03}}],
                              "masks": EDGE}}}
    with pytest.raises(ClassSpecError, match="stroek"):
        ClassSpec.from_dict(data).validate()


# ------------------------------------------------------------- ink spec

@pytest.fixture(scope="module")
def ink():
    return load_class_spec(INK_SPEC)


@pytest.fixture(scope="module")
def v4():
    return load_class_spec(V4_SPEC)


def test_ink_spec_validates_and_covers_every_v4_class(ink, v4):
    assert set(v4.classes) <= set(ink.classes)
    assert {"DM", "DL", "MD", "ML", "LD", "LM"} <= set(ink.classes)


def test_ink_spec_kinds_and_rotations_match_v4(ink, v4):
    for name, pc in v4.classes.items():
        assert ink.classes[name].allowed_rotations == pc.allowed_rotations, name
    for name, pc in ink.classes.items():
        prims = [layer.primitive for layer in pc.layers]
        if pc.masks:
            assert prims == ["stipple", "march_line"] and pc.layers[1].outline_of, name
        elif name in MOTIFS:
            assert prims == ["stipple", "motif", "motif"], name
        else:
            assert prims == ["stipple"] and pc.layers[0].params == {"density": 0.0}, name


@pytest.mark.parametrize("ink_name, v4_name, element, close", [
    ("DM", "DMs", "polyline", CLOSE["straight"]),   # v3 code DM is the straight DMs
    ("DMc", "DMc", "polyline", CLOSE["corner"]),
    ("LMp", "LMp", "polyline", CLOSE["cap"]),
    ("LDi", "LDi", "polyline", CLOSE["corner_in"]),
    ("LDd", "LDd", "polygon", 0),                   # a dot: closed blob, no corners
])
def test_ink_transition_has_the_full_pieces_boundary(ink, v4, ink_name, v4_name, element, close):
    full, inked = v4.drawer(), ink.drawer()
    for seed in range(6):
        mask = _mask_pts(full(f"x{seed}", v4_name, seed, 100.0))
        line = _pts(inked(f"x{seed}", ink_name, seed, 100.0), element)
        assert line == (mask[:-close] if close else mask), (ink_name, seed)


def test_plain_and_transition_ink_pieces_are_black_lines_on_white(ink):
    draw = ink.drawer()
    for name, pc in ink.classes.items():
        if name in MOTIFS:
            continue
        for seed in range(3):
            svg = draw(f"{name}#{seed}", name, seed, 48.0)
            fills = set(re.findall(r'fill="([^"]+)"', svg))
            strokes = set(re.findall(r'stroke="([^"]+)"', svg))
            assert fills <= WHITE, (name, fills)
            assert strokes <= {"#000000"}, (name, strokes)


def test_motif_ink_pieces_use_only_black_and_white(ink):
    draw = ink.drawer()
    for name in MOTIFS:
        svg = draw(name, name, 2, 48.0)
        colours = set(re.findall(r'(?:fill|stroke)="([^"]+)"', svg))
        assert colours <= BLACK_AND_WHITE, (name, colours)
        assert "#000000" in colours and "#ffffff" in colours, name


def test_ink_render_script_writes_the_same_spec(tmp_path):
    out = subprocess.run([sys.executable, str(EXP / "gen_classes_ink.py")],
                         capture_output=True, text=True, check=True)
    assert "with 67 classes" in out.stdout
    assert json.loads(INK_SPEC.read_text())["classes"]["DMs"]["masks"]["edge"]
