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

from metapuzzle.classes import (
    SAMPLE_SPEC_PATH,
    ClassSpec,
    ClassSpecError,
    load_class_spec,
)
from metapuzzle.cli import main

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
