import dataclasses
import json
import os
import re
import subprocess
import sys
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PIL import Image

from metapuzzle import textures as tx
from metapuzzle.board import square_board
from metapuzzle.classes import (
    SAMPLE_SPEC_PATH,
    ClassSpec,
    ClassSpecError,
    _layer_seed,
    load_class_spec,
)
from metapuzzle.cli import main
from metapuzzle.optimize import solve
from metapuzzle.pieces import make_inventory
from metapuzzle.render import render_solution_svg

SRC = Path(__file__).resolve().parents[1] / "src"
SAMPLE_CLASSES = ["canopy", "sea", "shore", "sun"]
PALETTE = {"paper": "#e8dcc4", "moss": "#5b7f5b", "pine": "#2f4f4f", "sand": "#c9a66b"}


def _spec_dict(classes, palette=PALETTE):
    return {"palette": dict(palette), "classes": classes}


def _layer(primitive="stipple", palette=("moss", "pine"), params=None, **extra):
    d = {"primitive": primitive, "palette": list(palette), "params": params or {}}
    d.update(extra)
    return d


def _one_class(*layers, **cls_extra):
    cls = {"layers": list(layers), **cls_extra}
    return _spec_dict({"c": cls})


def _load(d):
    return ClassSpec.from_dict(d)


@pytest.fixture(scope="module")
def sample():
    return load_class_spec(SAMPLE_SPEC_PATH)


# ------------------------------------------------------------ loading

def test_sample_spec_loads_with_expected_classes(sample):
    assert list(sample.classes) == SAMPLE_CLASSES
    assert sample.allowed_rotations("canopy") == (0, 90, 180, 270)
    assert sample.allowed_rotations("shore") == (0,)
    assert sample.classes["shore"].directional is True
    assert sample.classes["canopy"].directional is False


def test_sample_spec_is_packaged_data():
    # pyproject lists data/*.json as package data; the file must sit inside the package.
    assert SAMPLE_SPEC_PATH.is_file()
    assert SAMPLE_SPEC_PATH.parent.name == "data"
    assert "data/*.json" in (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()


def test_background_defaults_first_layer_only():
    spec = _load(_one_class(_layer(), _layer(), _layer(background=True)))
    flags = [layer.background for layer in spec.classes["c"].layers]
    assert flags == [True, False, True]


def test_rotation_defaults():
    free = _load(_one_class(_layer())).classes["c"]
    assert free.directional is False and free.allowed_rotations == (0, 90, 180, 270)
    edge = _load(_one_class(_layer(), directional=True)).classes["c"]
    assert edge.allowed_rotations == (0,)


def test_comment_keys_are_ignored():
    d = _one_class(_layer(_note="hi"), _note="class note")
    d["_note"] = "spec note"
    spec = _load(d)
    spec.validate()
    assert list(spec.classes) == ["c"]


def test_load_from_file_and_bad_json(tmp_path):
    good = tmp_path / "good.json"
    good.write_text(json.dumps(_one_class(_layer())))
    assert list(load_class_spec(good).classes) == ["c"]
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(ClassSpecError, match="invalid JSON"):
        load_class_spec(bad)


# ------------------------------------------------------------ validation

BAD_SPECS = {
    "unknown primitive": (_one_class(_layer("sparkle")), "unknown primitive 'sparkle'"),
    "unknown palette name": (_one_class(_layer(palette=("moss", "teal"))), "unknown palette name 'teal'"),
    "bad raw hex": (_one_class(_layer(palette=("moss", "#12345"))), "bad hex color '#12345'"),
    "unknown param": (_one_class(_layer(params={"densty": 10})), "no parameter(s) ['densty']"),
    "reserved param": (_one_class(_layer(params={"background": False})), "may not set"),
    "primitive rejects value": (
        _one_class(_layer("blotch", params={"side": "middle"})), "side must be one of"),
    "palette index out of range": (
        _one_class(_layer("blotch", palette=("moss",), params={"color_index": 3})), "out of range"),
    "bad rotation": (_one_class(_layer(), allowed_rotations=[45]), "allowed_rotations must be distinct"),
    "duplicate rotation": (_one_class(_layer(), allowed_rotations=[0, 0]), "allowed_rotations must be distinct"),
    "bad top-level hex": (_spec_dict({"c": {"layers": [_layer()]}}, {"moss": "green"}), "'green' is not"),
}


@pytest.mark.parametrize("name", list(BAD_SPECS))
def test_validation_errors_name_the_problem(name):
    data, fragment = BAD_SPECS[name]
    with pytest.raises(ClassSpecError, match=re.escape(fragment)):
        _load(data).validate()


@pytest.mark.parametrize("data, fragment", [
    (_spec_dict({}), "classes must be a non-empty object"),
    (_spec_dict({"c": {"layers": []}}), "layers must be a non-empty list"),
    (_spec_dict({"c": {"layers": [_layer()], "layer": []}}), "unknown key 'layer'"),
    (_spec_dict({"c": {"layers": [{"palette": ["moss"]}]}}), "missing required key 'primitive'"),
    (_spec_dict({"c": {"layers": [_layer(background="yes")]}}), "background must be true or false"),
    (_spec_dict({"c": {"layers": [_layer()], "directional": "no"}}), "directional must be true or false"),
    (_spec_dict({"c": {"layers": [_layer(palette=[])]}}), "palette must be a non-empty list"),
])
def test_structural_errors_raise_on_parse(data, fragment):
    with pytest.raises(ClassSpecError, match=fragment):
        _load(data)


def test_validate_reports_every_problem_at_once():
    d = _spec_dict({"a": {"layers": [_layer("sparkle")]}, "b": {"layers": [_layer(palette=("nope",))]}})
    with pytest.raises(ClassSpecError) as info:
        _load(d).validate()
    msg = str(info.value)
    assert "class 'a' layer 0" in msg and "class 'b' layer 0" in msg


def test_load_class_spec_error_names_file(tmp_path):
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(_one_class(_layer("sparkle"))))
    with pytest.raises(ClassSpecError, match=f"{p}: "):
        load_class_spec(p)
    assert list(load_class_spec(p, validate=False).classes) == ["c"]


def test_validate_passes_for_sample(sample):
    sample.validate()


# ------------------------------------------------------------ drawing

def test_palette_names_and_raw_hex_both_resolve():
    spec = _load(_one_class(_layer("stipple", palette=("#123456", "moss"), params={"density": 300})))
    frag = spec.drawer()("7", "c", 7, 80.0)
    assert 'fill="#5b7f5b"' in frag


def test_layers_draw_in_order_with_independent_seeds():
    # Two identical stipple layers must not produce identical marks.
    spec = _load(_one_class(_layer(params={"density": 200}), _layer(params={"density": 200})))
    draw = spec.drawer()
    frag = draw("1", "c", 1, 100.0)
    clip_ids = [part.split('"')[1] for part in frag.split("clipPath id=")[1:]]
    assert len(clip_ids) == 2 and clip_ids[0] != clip_ids[1]
    assert frag.count("<circle") == 2 * 200


def test_drawer_is_deterministic_for_same_piece(sample):
    draw = sample.drawer()
    for cls in SAMPLE_CLASSES:
        for seed in (0, 17, 4096):
            assert draw(str(seed), cls, seed, 90.0) == draw(str(seed), cls, seed, 90.0)


def test_drawer_identical_across_instances(sample):
    other = load_class_spec(SAMPLE_SPEC_PATH).drawer()
    draw = sample.drawer()
    for cls in SAMPLE_CLASSES:
        assert draw("3", cls, 3, 64.0) == other("3", cls, 3, 64.0)


def test_different_pieces_differ(sample):
    draw = sample.drawer()
    assert draw("1", "canopy", 1, 64.0) != draw("2", "canopy", 2, 64.0)


def test_output_is_independent_of_python_hash_seed():
    code = (
        "import hashlib;from metapuzzle.classes import load_class_spec,SAMPLE_SPEC_PATH;"
        "d=load_class_spec(SAMPLE_SPEC_PATH).drawer();"
        "print(hashlib.sha256(''.join(d(str(s),c,s,64.0) for s in range(5) for c in "
        "['canopy','sea','shore','sun']).encode()).hexdigest())"
    )
    digests = set()
    for hash_seed in ("0", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONPATH=str(SRC))
        out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                             text=True, check=True).stdout.strip()
        digests.add(out)
    assert len(digests) == 1


def test_unknown_class_draws_neutral_and_warns_once(sample):
    draw = sample.drawer()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        a = draw("9", "mystery", 9, 64.0)
        b = draw("10", "mystery", 10, 64.0)
        draw("11", "other", 11, 64.0)
    assert a and b and a != b
    messages = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
    assert len(messages) == 2
    assert "'mystery'" in messages[0] and "'other'" in messages[1]


def test_allowed_rotations(sample):
    assert sample.allowed_rotations("sea") == (0, 90, 180, 270)
    assert sample.allowed_rotations("never_defined") == (0, 90, 180, 270)


def test_fragments_are_well_formed_svg(sample):
    draw = sample.drawer()
    for cls in SAMPLE_CLASSES:
        frag = draw("1", cls, 1, 64.0)
        root = ET.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg">{frag}</svg>')
        assert root is not None


# ------------------------------------------------------------ sheets

def test_contact_sheet_is_produced(sample, tmp_path):
    out = tmp_path / "sheet.png"
    assert sample.contact_sheet(out, cell=40, per_class=3) == out
    img = Image.open(out)
    assert img.size[0] >= 3 * 40
    assert img.size[1] >= len(SAMPLE_CLASSES) * 40


def test_pairs_sheet_is_produced_and_checks_names(sample, tmp_path):
    out = tmp_path / "pairs.png"
    sample.pairs_sheet(out, [("sea", "shore"), ("shore", "canopy")], cell=40)
    assert Image.open(out).size[0] >= 2 * 40
    with pytest.raises(ClassSpecError, match="unknown class 'nope'"):
        sample.pairs_sheet(tmp_path / "x.png", [("sea", "nope")])


def test_contact_sheet_creates_parent_directory(sample, tmp_path):
    out = tmp_path / "nested" / "dir" / "sheet.png"
    sample.contact_sheet(out, cell=24, per_class=2)
    assert out.is_file()


# ------------------------------------------------------------ CLI

def test_render_cli_uses_class_spec(tmp_path, capsys):
    sol_path = tmp_path / "sol.json"
    assert main(["solve", "--cols", "6", "--rows", "4", "--seed", "2", "--out", str(sol_path)]) == 0
    data = json.loads(sol_path.read_text())
    for i, piece in enumerate(data["pieces"]):
        piece["cls"] = SAMPLE_CLASSES[i % len(SAMPLE_CLASSES)]
    sol_path.write_text(json.dumps(data))
    out_dir = tmp_path / "out"
    capsys.readouterr()
    assert main(["render", str(sol_path), "--out", str(out_dir), "--cell", "24",
                 "--classes", str(SAMPLE_SPEC_PATH)]) == 0
    assert (out_dir / "sol-A.svg").is_file()
    assert (out_dir / "sol-pieces.png").is_file()
    svg = (out_dir / "sol-A.svg").read_text()
    # Layer clip ids come from the texture primitives, so the spec drawer was used.
    assert "clip-stipple-" in svg and "clip-hatch_multi-" in svg


def test_render_cli_bad_spec_is_error(tmp_path, capsys):
    sol_path = tmp_path / "sol.json"
    assert main(["solve", "--cols", "4", "--rows", "3", "--out", str(sol_path)]) == 0
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(_one_class(_layer("sparkle"))))
    capsys.readouterr()
    assert main(["render", str(sol_path), "--out", str(tmp_path / "o"), "--classes", str(bad)]) == 1
    assert "unknown primitive" in capsys.readouterr().err


# ------------------------------------------------------------ render size and reference size

MARK_TAG = re.compile(r"<(circle|ellipse|path)[ >]")


def test_mark_count_is_the_same_at_every_render_size(sample):
    draw = sample.drawer()
    for cls in SAMPLE_CLASSES:
        small = draw("5", cls, 5, 40.0)
        large = draw("5", cls, 5, 256.0)
        assert len(MARK_TAG.findall(small)) == len(MARK_TAG.findall(large)), cls
    # canopy and sun are built from circles and paths, so the check is not vacuous
    assert MARK_TAG.findall(draw("5", "canopy", 5, 256.0))
    assert MARK_TAG.findall(draw("5", "sun", 5, 256.0))


def test_artwork_is_identical_at_every_size_up_to_the_scale_wrapper(sample):
    draw = sample.drawer()
    for cls in SAMPLE_CLASSES:
        ref = draw("5", cls, 5, 100.0)
        prefix = '<g transform="scale(1)">'
        assert ref.startswith(prefix) and ref.endswith("</g>"), cls
        body = ref[len(prefix):-len("</g>")]
        assert draw("5", cls, 5, 256.0) == f'<g transform="scale(2.56)">{body}</g>'
        assert draw("5", cls, 5, 40.0) == f'<g transform="scale(0.4)">{body}</g>'


def test_solution_marks_do_not_depend_on_cell_size(sample):
    boards = [square_board(6, 4), square_board(4, 6), square_board(8, 3)]
    sol = solve(boards, make_inventory(boards), seed=1, iters=300)
    sol.pieces = [dataclasses.replace(p, cls=SAMPLE_CLASSES[p.piece_id % len(SAMPLE_CLASSES)])
                  for p in sol.pieces]
    draw = sample.drawer()
    small = render_solution_svg(sol, 0, draw, cell_size=40)
    large = render_solution_svg(sol, 0, draw, cell_size=256)
    assert len(MARK_TAG.findall(small)) == len(MARK_TAG.findall(large)) > 0


def test_clip_ids_are_unique_within_a_piece_and_across_pieces(sample):
    draw = sample.drawer()
    seen: list[str] = []
    for seed, cls in enumerate(SAMPLE_CLASSES * 3, start=1):
        ids = re.findall(r'clipPath id="([^"]+)"', draw(str(seed), cls, seed, 64.0))
        assert len(ids) == len(set(ids)), cls
        seen += ids
    assert len(seen) == len(set(seen))


def test_ref_size_is_the_drawing_unit():
    d = _one_class(_layer("stipple", params={"density": 40}))
    d["ref_size"] = 50
    spec = _load(d)
    assert spec.ref_size == 50
    frag = spec.drawer()("1", "c", 1, 100.0)
    assert frag.startswith('<g transform="scale(2)">')
    assert _load(_one_class(_layer())).ref_size == 100


@pytest.mark.parametrize("bad", [0, -5, "100", True, None])
def test_ref_size_must_be_a_positive_number(bad):
    d = _one_class(_layer())
    d["ref_size"] = bad
    with pytest.raises(ClassSpecError, match="ref_size must be a positive number"):
        _load(d)


def test_sample_transition_uses_a_mask(sample):
    assert "clip-blotch_mask-" in sample.drawer()("2", "shore", 2, 64.0)


# ------------------------------------------------------------ masks

MASK = {"primitive": "blotch_mask", "params": {"coverage": 0.35, "side": "right", "count": 3}}


def _masked(mask, **layer_extra):
    return _one_class(_layer("stipple", params={"density": 50}, mask=mask, background=True,
                             **layer_extra))


MASK_BAD = {
    "unknown mask primitive": ({"primitive": "sparkle"}, "unknown mask primitive 'sparkle'"),
    "unknown mask param": ({"primitive": "blotch_mask", "params": {"densty": 2}},
                           "mask blotch_mask has no parameter(s) ['densty']"),
    "bad mask side": ({"primitive": "blotch_mask", "params": {"side": "middle"}},
                      "side must be one of"),
    "bad mask count": ({"primitive": "blotch_mask", "params": {"count": 0}}, "count must be"),
    "mask palette not allowed": ({"primitive": "blotch_mask", "palette": ["moss"]},
                                 "unknown key 'palette'"),
}


@pytest.mark.parametrize("name", list(MASK_BAD))
def test_bad_masks_are_reported(name):
    mask, fragment = MASK_BAD[name]
    with pytest.raises(ClassSpecError, match=re.escape(fragment)):
        _load(_masked(mask)).validate()


@pytest.mark.parametrize("mask, fragment", [
    (["blotch_mask"], "mask must be an object"),
    ({"params": {}}, "missing required key 'primitive'"),
    ({"primitive": "blotch_mask", "params": []}, "mask params must be an object"),
    ({"primitive": 3}, "mask primitive must be a string"),
])
def test_structural_mask_errors_raise_on_parse(mask, fragment):
    with pytest.raises(ClassSpecError, match=fragment):
        _load(_masked(mask))


def test_masked_layer_is_clipped_to_its_mask():
    frag = _load(_masked(MASK)).drawer()("4", "c", 4, 64.0)
    mid = re.search(r'<g clip-path="url\(#(clip-blotch_mask-[^)]+)\)"', frag)
    assert mid, frag[:300]
    assert f'clipPath id="{mid.group(1)}"' in frag
    # the mask's <defs> comes before the group that uses it
    assert frag.index(f'clipPath id="{mid.group(1)}"') < mid.start()


def test_mask_is_derived_from_the_piece_seed():
    draw = _load(_masked(MASK)).drawer()
    a = draw("4", "c", 4, 100.0)
    assert a == draw("4", "c", 4, 100.0)
    assert a != draw("5", "c", 5, 100.0)
    # the mask uses seed (piece seed, "0:mask") and the layer's resolved palette
    _, expected_id = tx.blotch_mask(_layer_seed(4, "0:mask"), 100.0, [PALETTE["moss"], PALETTE["pine"]],
                                    coverage=0.35, side="right", count=3)
    assert expected_id in a


def test_mask_applies_only_to_its_own_class():
    spec = _load(_masked(MASK))
    with pytest.warns(UserWarning, match="not in spec"):
        frag = spec.drawer()("9", "other", 9, 64.0)
    assert "clip-blotch_mask-" not in frag


# ------------------------------------------------------------ named masks

SHARED_MASK = {"primitive": "blotch_mask",
               "params": {"coverage": 0.35, "side": None, "count": 3, "inset": 0.08}}


def _shared_spec(name="m1", masks=None):
    """A mosaic-like fill and its chips, both clipped by the one named mask ``name``."""
    masks = {name: SHARED_MASK} if masks is None else masks
    return _spec_dict({"c": {
        "masks": masks,
        "layers": [
            _layer("dabs", ("moss", "pine", "paper"), {"count": 60}, background=True, mask=name),
            _layer("scatter_shapes", ("paper", "moss"),
                   {"kinds": ["disc"], "count": 10, "scale": 0.05}, background=False, mask=name),
            _layer("stipple", ("paper", "pine"), {"density": 40}, background=False),
        ],
    }})


def test_named_mask_is_one_clip_shared_by_its_layers():
    frag = _load(_shared_spec()).drawer()("4", "c", 4, 64.0)
    # primitives also clip to their own cell, so keep only the mask's references
    refs = [r for r in re.findall(r'clip-path="url\(#([^)]+)\)"', frag) if "blotch_mask" in r]
    defined = [d for d in re.findall(r'<clipPath id="([^"]+)"', frag) if "blotch_mask" in d]
    assert len(refs) == 2 and len(set(refs)) == 1
    assert defined == refs[:1]                       # defined once, before the first use
    assert frag.index(f'<clipPath id="{refs[0]}"') < frag.index(f'url(#{refs[0]})')


def test_named_mask_id_comes_from_piece_seed_and_name():
    draw = _load(_shared_spec()).drawer()
    frag = draw("4", "c", 4, 64.0)
    _, cid = tx.blotch_mask(_layer_seed(4, "mask:m1"), 100.0, (),
                            coverage=0.35, side=None, count=3, inset=0.08)
    assert f'<clipPath id="{cid}">' in frag
    assert f'<clipPath id="{cid}">' not in draw("5", "c", 5, 64.0)
    renamed = _load(_shared_spec(name="m2")).drawer()("4", "c", 4, 64.0)
    assert f'<clipPath id="{cid}">' not in renamed


def test_named_mask_output_is_deterministic():
    draw = _load(_shared_spec()).drawer()
    assert draw("7", "c", 7, 80.0) == draw("7", "c", 7, 80.0)


def test_inline_and_named_masks_can_mix_in_one_class():
    d = _spec_dict({"c": {
        "masks": {"m1": SHARED_MASK},
        "layers": [_layer("stipple", ("moss", "pine"), {"density": 50}, mask="m1"),
                   _layer("stipple", ("paper", "pine"), {"density": 50}, background=True,
                          mask=dict(MASK))],
    }})
    frag = _load(d).drawer()("3", "c", 3, 64.0)
    assert frag.count('<clipPath id="clip-blotch_mask-') == 2
    assert frag.count('clip-path="url(#clip-blotch_mask-') == 2


def test_named_masks_are_local_to_their_class():
    d = _spec_dict({
        "c": {"masks": {"m1": SHARED_MASK}, "layers": [_layer(mask="m1")]},
        "e": {"layers": [_layer(mask="m1")]},
    })
    with pytest.raises(ClassSpecError, match="class 'e' layer 0: unknown mask 'm1'"):
        _load(d)


def _with_mask(mask_ref, masks):
    return _spec_dict({"c": {"masks": masks, "layers": [_layer(mask=mask_ref)]}})


NAMED_BAD = {
    "unknown name": (_with_mask("nope", {"m1": SHARED_MASK}), "unknown mask 'nope'"),
    "unused name": (_with_mask(None, {"m1": SHARED_MASK}), "mask(s) ['m1'] defined but not used"),
    "masks not an object": (_spec_dict({"c": {"layers": [_layer()], "masks": ["m1"]}}),
                            "masks must be an object"),
    "named mask missing primitive": (_with_mask("m1", {"m1": {"params": {}}}),
                                     "missing required key 'primitive'"),
    "named mask palette key": (_with_mask("m1", {"m1": {"primitive": "blotch_mask", "palette": []}}),
                               "unknown key 'palette'"),
    "named mask unknown primitive": (_with_mask("m1", {"m1": {"primitive": "sparkle"}}),
                                     "unknown mask primitive 'sparkle'"),
    "named mask unknown param": (_with_mask("m1", {"m1": {"primitive": "blotch_mask",
                                                          "params": {"densty": 2}}}),
                                 "mask blotch_mask has no parameter(s) ['densty']"),
    "inset too large": (_with_mask("m1", {"m1": {"primitive": "blotch_mask",
                                                 "params": {"inset": 0.5}}}),
                        "inset must be in [0, 0.5)"),
}


@pytest.mark.parametrize("name", list(NAMED_BAD))
def test_named_mask_errors_are_reported(name):
    data, fragment = NAMED_BAD[name]
    with pytest.raises(ClassSpecError, match=re.escape(fragment)):
        _load(data).validate()


def test_named_mask_accepts_comment_keys():
    d = _with_mask("m1", {"_note": "shared edge", "m1": SHARED_MASK})
    _load(d).validate()
    assert list(_load(d).classes["c"].masks) == ["m1"]


def test_sample_transition_is_a_named_mask(sample):
    shore = sample.classes["shore"]
    assert list(shore.masks) == ["edge"]
    assert [layer.mask for layer in shore.layers] == [None, "edge"]
    frag = sample.drawer()("2", "shore", 2, 64.0)
    assert frag.count('<clipPath id="clip-blotch_mask-') == 1
    assert frag.count('clip-path="url(#clip-blotch_mask-') == 1



# ------------------------------------------------------------ seed groups

def _polygon(clip_svg):
    """The vertices of a march_mask clip polygon, as floats."""
    pts = re.search(r'<polygon points="([^"]+)"', clip_svg).group(1)
    return [tuple(map(float, p.split(","))) for p in pts.split()]


def _polygon_piece(spec, seed):
    return spec.drawer()(str(seed), "c", seed, 64.0)


def _two_masks_spec(group_a, group_b, pattern="corner"):
    """One class with two named march masks of identical params, each in its own group."""
    params = {"pattern": pattern, "roughness": 1.0, "wobble": 0.2}
    masks = {"a": {"primitive": "march_mask", "params": params},
             "b": {"primitive": "march_mask", "params": dict(params)}}
    if group_a is not None:
        masks["a"]["seed_group"] = group_a
    if group_b is not None:
        masks["b"]["seed_group"] = group_b
    return _load(_spec_dict({"c": {
        "masks": masks,
        "layers": [_layer("stipple", ("moss", "pine"), {"density": 20}, mask="a"),
                   _layer("stipple", ("paper", "pine"), {"density": 20}, mask="b",
                          background=False)],
    }}))


@pytest.mark.parametrize("seed", [1, 4, 17, 4096])
def test_masks_in_one_seed_group_share_their_geometry(seed):
    cls = _two_masks_spec("g", "g").classes["c"]
    clips = _two_masks_spec("g", "g")._named_clips(cls.layers, cls.masks, seed, 100.0)
    assert _polygon(clips["a"][0]) == _polygon(clips["b"][0])
    assert clips["a"][1] == clips["b"][1]        # the same clip, so one <clipPath> in the piece
    frag = _polygon_piece(_two_masks_spec("g", "g"), seed)
    assert frag.count(f'<clipPath id="{clips["a"][1]}"') == 1


@pytest.mark.parametrize("seed", [1, 4, 17, 4096])
def test_masks_in_different_seed_groups_differ(seed):
    spec = _two_masks_spec("g", "h")
    cls = spec.classes["c"]
    clips = spec._named_clips(cls.layers, cls.masks, seed, 100.0)
    assert _polygon(clips["a"][0]) != _polygon(clips["b"][0])


def test_seed_group_is_derived_from_the_piece_seed_and_the_group_name():
    spec = _two_masks_spec("g", None)
    cls = spec.classes["c"]
    clips = spec._named_clips(cls.layers, cls.masks, 4, 100.0)
    _, cid = tx.march_mask(_layer_seed(4, "group:g"), 100.0, (), pattern="corner",
                           roughness=1.0, wobble=0.2)
    assert clips["a"][1] == cid
    # without a group, the mask keeps its own seed (name-based), so it is not the group's
    assert _polygon(clips["b"][0]) != _polygon(clips["a"][0])


def test_tee_parts_in_one_seed_group_meet_at_the_centre_for_every_piece():
    spec = _two_masks_spec(None, None)
    tee = {"primitive": "march_mask", "seed_group": "junction",
           "params": {"pattern": "tee", "roughness": 0.5, "wobble": 0.12}}
    masks = {"p1": {**tee, "params": {**tee["params"], "part": 1}},
             "p2": {**tee, "params": {**tee["params"], "part": 2}}}
    spec = _load(_spec_dict({"t": {"masks": masks, "layers": [
        _layer("stipple", ("moss", "pine"), {"density": 20}, mask="p1"),
        _layer("stipple", ("paper", "pine"), {"density": 20}, mask="p2", background=False),
    ]}}))
    pc = spec.classes["t"]
    centre = (50.0, 50.0)
    for seed in range(1, 9):
        clips = spec._named_clips(pc.layers, pc.masks, seed, 100.0)
        one, two = _polygon(clips["p1"][0]), _polygon(clips["p2"][0])
        assert centre in one and centre in two
        assert len(set(one) & set(two)) >= 12    # the shared north arm, end to end


def test_seed_group_must_be_a_non_empty_string_on_a_named_mask():
    base = {"primitive": "march_mask", "params": {"pattern": "corner"}}
    for bad in ("", 3, ["g"]):
        with pytest.raises(ClassSpecError, match="seed_group must be a non-empty string"):
            _load(_with_mask("m1", {"m1": {**base, "seed_group": bad}}))


def test_seed_group_is_refused_on_an_inline_mask():
    inline = {"primitive": "blotch_mask", "seed_group": "g"}
    with pytest.raises(ClassSpecError, match="unknown key 'seed_group'"):
        _load(_masked(inline))
