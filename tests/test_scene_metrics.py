from pathlib import Path

import pytest

from metapuzzle.cli import main
from metapuzzle.scene import ClassMap, load_scenes
from metapuzzle.scene_metrics import WINDOW_SIZES, largest_blob, report, same_position_overlap, transferable_blob, window_reuse

EXAMPLE = Path(__file__).resolve().parent.parent / "docs" / "design" / "scenes-8x10.txt"


def grid(rows):
    return [r.split() for r in rows]


def transpose(g):
    return [list(r) for r in zip(*g)]


def checker(rows, cols):
    return [["a" if (x + y) % 2 == 0 else "b" for x in range(cols)] for y in range(rows)]


def stripes(rows, cols):
    return [["a" if y % 2 == 0 else "b" for _ in range(cols)] for y in range(rows)]


def test_identical_maps_give_one():
    g = grid(["a a b", "a b b", "b b a"])
    assert same_position_overlap(g, g) == (9, 1.0)
    for h, w in WINDOW_SIZES:
        assert window_reuse(g, g, h, w) == 1.0
        assert window_reuse(g, g, h, w, allow_rotation=True) == 1.0
    assert same_position_overlap(ClassMap.from_tokens(g), g) == (9, 1.0)


def test_same_position_shape_mismatch_is_none():
    assert same_position_overlap(grid(["a a"]), grid(["a", "a"])) is None


def test_same_position_partial():
    s = grid(["a b", "a a"])
    assert same_position_overlap(s, transpose(s)) == (2, 0.5)


def test_map_and_transpose():
    g = grid(["a a a a", "b b b b"])  # horizontal stripes, 2x4
    t = transpose(g)  # vertical stripes, 4x2
    assert same_position_overlap(g, t) is None
    assert window_reuse(g, t, 1, 2) == 0.0
    assert window_reuse(g, t, 1, 2, allow_rotation=True) == 1.0
    assert window_reuse(g, t, 2, 1) == 0.0
    assert window_reuse(g, t, 2, 1, allow_rotation=True) == 1.0
    # translation only: a horizontal 4-run does not fit a vertical 4-run
    assert transferable_blob(g, t) == 1


def test_checkerboard_vs_stripes():
    c, s = checker(4, 4), stripes(4, 4)
    # classes agree exactly on the even columns
    assert same_position_overlap(c, s) == (8, 0.5)
    assert window_reuse(c, s, 1, 2) == 0.0
    assert window_reuse(c, s, 1, 2, allow_rotation=True) == 1.0
    # stripes alternate down each column, so vertical dominoes match without rotation
    assert window_reuse(c, s, 2, 1) == 1.0
    assert window_reuse(c, s, 2, 1, allow_rotation=True) == 1.0
    for rot in (False, True):
        assert window_reuse(c, s, 2, 2, rot) == 0.0
        assert window_reuse(c, s, 3, 3, rot) == 0.0
    # checkerboard classes are never 4-adjacent; stripes form 4-runs
    assert largest_blob(c) == {"a": 1, "b": 1}
    assert largest_blob(s) == {"a": 4, "b": 4}
    assert transferable_blob(c, s) == 1


def test_largest_blob():
    assert largest_blob(grid(["a a a", "a b b"])) == {"a": 4, "b": 2}
    assert largest_blob(grid(["a b", "b a"])) == {"a": 1, "b": 1}


def test_transferable_blob_components_matter():
    # two separate a cells in B cannot hold an a-domino
    assert transferable_blob(grid(["a a"]), grid(["a b a"])) == 1
    # a horizontal run of 4 overlaps a 2x2 block in at most 2 cells
    assert transferable_blob(grid(["a a a a"]), grid(["a a", "a a"])) == 2
    # an L-tromino of a fits inside B's 2x2 block of a (B's blob is 4, A's is 3)
    assert transferable_blob(grid(["a a", "a b"]), grid(["b a a", "b a a"])) == 3


def test_transferable_blob_self_is_largest_blob():
    g = grid(["a a b", "a b b", "b b a"])
    assert max(largest_blob(g).values()) == 5
    assert transferable_blob(g, g) == 5


def test_report_three_maps():
    maps = [grid(["a a", "b b"]), grid(["a a", "b b"]), checker(2, 2)]
    rep = report(maps)
    assert rep["names"] == ["A", "B", "C"]
    assert list(rep["pairs"]) == ["A-B", "A-C", "B-C"]
    assert rep["pairs"]["A-B"]["same_position"] == (4, 1.0)
    assert rep["pairs"]["A-B"]["window_reuse"]["2x2"] == {"plain": 1.0, "rot": 1.0}
    assert rep["pairs"]["A-B"]["window_reuse"]["3x3"] is None  # does not fit in a 2x2 map
    assert rep["histograms"]["A"] == {"a": 2, "b": 2}
    assert rep["shapes"]["A"] == (2, 2)
    assert "A-B: same position 4 (100.0%)" in rep["text"]
    assert "C" in rep["text"]


def test_report_custom_names_and_errors():
    rep = report([grid(["a b"]), grid(["b a"])], names=("X", "Y"))
    assert list(rep["pairs"]) == ["X-Y"]
    with pytest.raises(ValueError):
        report([grid(["a b"]), grid(["b a"])], names=("X",))
    with pytest.raises(ValueError):
        window_reuse(grid(["a b"]), grid(["a b"]), 2, 2)


def test_example_scene_file():
    maps = load_scenes([EXAMPLE])
    rep = report(maps)
    assert rep["shapes"] == {"A": (8, 10), "B": (8, 10), "C": (8, 10)}
    assert rep["histograms"]["A"] == rep["histograms"]["B"] == rep["histograms"]["C"]
    max_blob_a = max(rep["largest_blobs"]["A"].values())
    for key, p in rep["pairs"].items():
        cnt, frac = p["same_position"]
        assert 0 <= cnt <= 80 and frac == cnt / 80
        for h, w in WINDOW_SIZES:
            v = p["window_reuse"][f"{h}x{w}"]
            assert 0.0 <= v["plain"] <= v["rot"] <= 1.0
        assert 1 <= p["transferable_blob"] <= max_blob_a, key


def test_cli_scene_metrics(capsys):
    assert main(["scene-metrics", str(EXAMPLE)]) == 0
    out = capsys.readouterr().out
    assert "A-B: same position" in out and "A-C:" in out and "B-C:" in out
    assert "transferable blob" in out
