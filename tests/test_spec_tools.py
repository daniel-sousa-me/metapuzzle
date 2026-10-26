import copy
import json
from pathlib import Path

import pytest

from metapuzzle.classes import ClassSpec, load_class_spec
from metapuzzle.cli import main
from metapuzzle.board import square_board
from metapuzzle.scene import load_scenes, parse_token, validate_scenes
from metapuzzle.spec_tools import generate_transitions, prune_unused

ROOT = Path(__file__).resolve().parents[1]
DIRECTION_A = ROOT / "experiments" / "002-direction-a" / "classes.json"
PALETTE = {"paper": "#e8dcc4", "moss": "#5b7f5b", "pine": "#2f4f4f", "sand": "#c9a66b"}


def _field(*, two_layers=False):
    """A field class: a background stipple, optionally a second non-background dab layer."""
    layers = [{"primitive": "stipple", "palette": ["moss", "pine"], "params": {"density": 120}}]
    if two_layers:
        layers.append({"primitive": "stipple", "palette": ["sand", "paper"],
                       "background": False, "params": {"density": 60}})
    return {"layers": layers, "directional": False, "allowed_rotations": [0, 90, 180, 270]}


@pytest.fixture
def spec():
    return {
        "palette": dict(PALETTE),
        "classes": {"A": _field(), "B": _field(two_layers=True), "C": _field()},
    }


def _new_codes(spec, out):
    return [k for k in out["classes"] if k not in spec["classes"]]


def _write(tmp_path, data, name="spec.json"):
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ------------------------------------------------------------ counts and flags

def test_count_is_pairs_times_sides(spec):
    out = generate_transitions(spec, ["A", "B", "C"])
    # 3 fields -> 6 ordered pairs, times 4 sides
    assert len(_new_codes(spec, out)) == 6 * 4
    assert "A>B.T" in out["classes"] and "C>A.R" in out["classes"]


def test_sides_subset_and_default_codes(spec):
    out = generate_transitions(spec, ["A", "B"], sides=("left", "bottom"))
    assert sorted(_new_codes(spec, out)) == sorted(["A>B.L", "A>B.B", "B>A.L", "B>A.B"])


def test_corner_adds_adjacent_pairs(spec):
    out = generate_transitions(spec, ["A", "B", "C"], corner=True)
    corners = [k for k in _new_codes(spec, out) if k.split(".")[1] in ("TL", "TR", "BL", "BR")]
    # 4 adjacent side pairs per ordered pair, opposite sides excluded
    assert len(corners) == 6 * 4
    assert len(_new_codes(spec, out)) == 6 * 4 + 6 * 4


def test_corner_with_only_opposite_sides_is_an_error(spec):
    with pytest.raises(ValueError, match="adjacent"):
        generate_transitions(spec, ["A", "B"], sides=("top", "bottom"), corner=True)


def test_rotatable_one_side_per_pair_non_directional(spec):
    out = generate_transitions(spec, ["A", "B", "C"], rotatable=True)
    new = _new_codes(spec, out)
    assert len(new) == 6
    assert sorted(new) == ["A>B", "A>C", "B>A", "B>C", "C>A", "C>B"]
    for name in new:
        assert out["classes"][name]["directional"] is False
        assert out["classes"][name]["allowed_rotations"] == [0, 90, 180, 270]


def test_rotatable_with_corner_keeps_first_corner(spec):
    out = generate_transitions(spec, ["A", "B", "C"], rotatable=True, corner=True)
    assert len(_new_codes(spec, out)) == 6 + 6
    assert sum(c.endswith(".TL") for c in _new_codes(spec, out)) == 6


def test_non_rotatable_transitions_are_directional_at_zero(spec):
    out = generate_transitions(spec, ["A", "B"])
    cls = out["classes"]["A>B.T"]
    assert cls["directional"] is True
    assert cls["allowed_rotations"] == [0]


def test_code_fn_override_and_corner_side_string(spec):
    seen = []

    def code(base, mass, side):
        seen.append(side)
        return f"{base}_{mass}_{side.replace('+', '')}"

    out = generate_transitions(spec, ["A", "B"], sides=("top", "left"), corner=True, code_fn=code)
    assert "A_B_top" in out["classes"] and "A_B_topleft" in out["classes"]
    assert "top+left" in seen


def test_code_fn_collision_is_an_error(spec):
    with pytest.raises(ValueError, match="collides"):
        generate_transitions(spec, ["A", "B"], code_fn=lambda b, m, s: "A")


def test_code_fn_bad_name_is_an_error(spec):
    with pytest.raises(ValueError, match="unusable"):
        generate_transitions(spec, ["A", "B"], code_fn=lambda b, m, s: "_hidden")


# ------------------------------------------------------------ structure

def test_layers_base_then_masked_mass_with_background_kept(spec):
    out = generate_transitions(spec, ["A", "B"], sides=("top",))
    layers = out["classes"]["A>B.T"]["layers"]
    base = spec["classes"]["A"]["layers"]
    mass = spec["classes"]["B"]["layers"]
    assert len(layers) == len(base) + len(mass)
    assert layers[0]["primitive"] == base[0]["primitive"] and "mask" not in layers[0]
    masked = layers[len(base):]
    for got, want in zip(masked, mass):
        assert got["mask"] == {"primitive": "blotch_mask", "params": {"coverage": 0.45, "side": "top"}}
        assert got["primitive"] == want["primitive"] and got["params"] == want["params"]
    # mass layer 0 had an implicit background of true; it must keep drawing it inside the mask
    assert masked[0]["background"] is True
    assert masked[1]["background"] is False


def test_default_coverage_is_0_45(spec):
    out = generate_transitions(spec, ["A", "B"], sides=("top",))
    assert out["classes"]["A>B.T"]["layers"][-1]["mask"]["params"]["coverage"] == 0.45


def test_default_codes_are_scene_safe(spec):
    out = generate_transitions(spec, ["A", "B"], corner=True)
    rot = generate_transitions(spec, ["A", "B"], rotatable=True, corner=True)
    for name in _new_codes(spec, out) + _new_codes(spec, rot):
        assert "@" not in name and not name.startswith("_")
        assert parse_token(name) == (name, 0)
    assert sorted(_new_codes(spec, rot)) == ["A>B", "A>B.TL", "B>A", "B>A.TL"]


def test_generated_code_round_trips_through_scene_file(spec, tmp_path):
    """A 2x2 three-scene file that uses a generated code loads and passes validate_scenes."""
    out = generate_transitions(spec, ["A", "B"], sides=("top",))
    code = "A>B.T"
    assert code in out["classes"]
    scene = tmp_path / "scenes.txt"
    # every map holds one transition, two A and one B, so the class histograms agree
    scene.write_text(
        f"{code} A\nA B\n\n"
        f"A {code}\nB A\n\n"
        f"A A\n{code} B\n",
        encoding="utf-8",
    )
    maps = load_scenes([scene])
    assert all(code in m.histogram() for m in maps)
    assert set().union(*(m.histogram() for m in maps)) <= set(out["classes"])
    validate_scenes(square_board(2, 2, "standard", "none"), maps, strict_border=False)


def test_coverage_is_passed_to_mask(spec):
    out = generate_transitions(spec, ["A", "B"], sides=("left",), coverage=0.3)
    m = out["classes"]["A>B.L"]["layers"][-1]["mask"]
    assert m["params"] == {"coverage": 0.3, "side": "left"}


def test_generated_spec_validates_through_loader(spec, tmp_path):
    out = generate_transitions(spec, ["A", "B", "C"], corner=True)
    loaded = load_class_spec(_write(tmp_path, out))
    assert len(loaded.classes) == 3 + 48
    loaded.validate()


def test_rotatable_spec_validates_through_loader(spec, tmp_path):
    out = generate_transitions(spec, ["A", "B", "C"], rotatable=True, corner=True)
    load_class_spec(_write(tmp_path, out))


def test_generated_transition_draws_differently_from_base(spec):
    out = generate_transitions(spec, ["A", "B"], sides=("top",))
    drawer = ClassSpec.from_dict(out).drawer()
    base = drawer("p", "A", 7, 64.0)
    trans = drawer("p", "A>B.T", 7, 64.0)
    assert base != trans
    assert "clip-blotch_mask-" in trans and "clip-blotch_mask-" not in base


def test_input_spec_not_modified(spec):
    before = copy.deepcopy(spec)
    generate_transitions(spec, ["A", "B", "C"], corner=True)
    assert spec == before


def test_fields_validation(spec):
    with pytest.raises(ValueError, match="not in spec"):
        generate_transitions(spec, ["A", "Z"])
    with pytest.raises(ValueError, match="at least two"):
        generate_transitions(spec, ["A"])
    with pytest.raises(ValueError, match="duplicates"):
        generate_transitions(spec, ["A", "A"])


def test_sides_and_coverage_validation(spec):
    with pytest.raises(ValueError, match="unknown side"):
        generate_transitions(spec, ["A", "B"], sides=("north",))
    with pytest.raises(ValueError, match="coverage"):
        generate_transitions(spec, ["A", "B"], coverage=1.5)


def test_masked_field_cannot_be_mass(spec):
    spec = copy.deepcopy(spec)
    spec["classes"]["B"]["layers"][1]["mask"] = {"primitive": "blotch_mask", "params": {"side": "top"}}
    with pytest.raises(ValueError, match="masked layer"):
        generate_transitions(spec, ["A", "B"])


# ------------------------------------------------------------ pruning

def test_prune_keeps_exactly_the_used_classes(spec, tmp_path):
    out = generate_transitions(spec, ["A", "B", "C"], corner=True)
    scene = tmp_path / "scenes.txt"
    scene.write_text("A B\nB A\n\nA A\nB B\n\nB A\nA B\n", encoding="utf-8")
    pruned = prune_unused(out, [scene])
    assert sorted(pruned["classes"]) == ["A", "B"]
    assert pruned["palette"] == out["palette"]
    load_class_spec(_write(tmp_path, pruned))


def test_prune_accepts_scenes_split_across_files(spec, tmp_path):
    out = generate_transitions(spec, ["A", "B"])
    paths = []
    for i, text in enumerate(["A\n", "B\n", "A\n"]):
        p = tmp_path / f"s{i}.txt"
        p.write_text(text, encoding="utf-8")
        paths.append(p)
    pruned = prune_unused(out, paths)
    assert sorted(pruned["classes"]) == ["A", "B"]


def test_prune_keeps_a_used_transition_and_drops_the_rest(spec, tmp_path):
    out = generate_transitions(spec, ["A", "B"], code_fn=lambda b, m, s: f"{b}{m}{s[0]}")
    scene = tmp_path / "scenes.txt"
    scene.write_text("ABt@90 A\nB B\n\nA A\nB B\n\nA B\nA B\n", encoding="utf-8")
    pruned = prune_unused(out, [scene])
    assert sorted(pruned["classes"]) == ["A", "ABt", "B"]
    assert pruned["classes"]["ABt"]["layers"] == out["classes"]["ABt"]["layers"]


def test_prune_unknown_scene_class_is_an_error(spec, tmp_path):
    scene = tmp_path / "scenes.txt"
    scene.write_text("A Q\nA A\n\nA A\nA A\n\nA A\nA A\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not in spec"):
        prune_unused(spec, [scene])


# ------------------------------------------------------------ CLI

def test_cli_gen_transitions(spec, tmp_path, capsys):
    src = _write(tmp_path, spec)
    out = tmp_path / "new.json"
    rc = main(["gen-transitions", str(src), "--fields", "A,B,C", "--out", str(out), "--corners",
               "--coverage", "0.4", "--sides", "top,left"])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["classes"]) == 3 + 6 * 2 + 6 * 1
    assert data["classes"]["A>B.TL"]["layers"][-1]["mask"]["params"]["coverage"] == 0.4
    load_class_spec(out)


def test_cli_gen_transitions_rotatable(spec, tmp_path):
    src = _write(tmp_path, spec)
    out = tmp_path / "rot.json"
    assert main(["gen-transitions", str(src), "--fields", "A,B,C", "--out", str(out), "--rotatable"]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["classes"]) == 3 + 6
    assert "A>B" in data["classes"]


def test_cli_gen_transitions_bad_field_exits_1(spec, tmp_path, capsys):
    src = _write(tmp_path, spec)
    out = tmp_path / "bad.json"
    assert main(["gen-transitions", str(src), "--fields", "A,Z", "--out", str(out)]) == 1
    assert not out.exists()
    assert "not in spec" in capsys.readouterr().err


def test_cli_prune_spec(spec, tmp_path):
    src = _write(tmp_path, generate_transitions(spec, ["A", "B"]))
    scene = tmp_path / "scenes.txt"
    scene.write_text("A A\nB B\n\nA A\nB B\n\nA B\nB A\n", encoding="utf-8")
    out = tmp_path / "pruned.json"
    assert main(["prune-spec", str(src), "--scenes", str(scene), "--out", str(out)]) == 0
    assert sorted(json.loads(out.read_text(encoding="utf-8"))["classes"]) == ["A", "B"]


# ------------------------------------------------------------ direction A example

def test_direction_a_fields_give_pairs_times_sides():
    raw = json.loads(DIRECTION_A.read_text(encoding="utf-8"))
    fields = ["SK", "ME", "DP", "FO", "SN", "RU"]
    out = generate_transitions(raw, fields)
    generated = [k for k in out["classes"] if k not in raw["classes"]]
    assert len(generated) == 6 * 5 * 4
    ClassSpec.from_dict(out).validate()
