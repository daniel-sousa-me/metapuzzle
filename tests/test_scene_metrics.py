from pathlib import Path

import pytest

from metapuzzle.cli import main
from metapuzzle.scene import ClassMap, load_scenes
from metapuzzle.scene_metrics import (
    SCENE_GATES,
    WINDOW_SIZES,
    dominant_class,
    largest_blob,
    report,
    same_position_overlap,
    scene_gates,
    transferable_blob,
    weighted_overlap,
    window_reuse,
)

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
    # excluding a class: the 5 remaining b cells all match
    assert same_position_overlap(g, g, exclude={"a"}) == (5, 1.0)
    assert same_position_overlap(g, g, exclude={"a", "b"}) is None  # no cells left
    assert weighted_overlap(g, g) == 1.0
    assert weighted_overlap(stripes(3, 4), stripes(3, 4)) == 1.0
    assert weighted_overlap(ClassMap.from_tokens(g), g) == 1.0


def test_same_position_shape_mismatch_is_none():
    assert same_position_overlap(grid(["a a"]), grid(["a", "a"])) is None
    assert weighted_overlap(grid(["a a"]), grid(["a", "a"])) is None


def test_same_position_partial():
    s = grid(["a b", "a a"])
    assert same_position_overlap(s, transpose(s)) == (2, 0.5)


def test_same_position_exclude_skips_either_map():
    # A's a cell is skipped; B's a cell (at the same position) is skipped too
    assert same_position_overlap(grid(["a b"]), grid(["b b"]), exclude={"a"}) == (1, 1.0)
    assert same_position_overlap(grid(["b b"]), grid(["a b"]), exclude={"a"}) == (1, 1.0)
    # the fraction is over the cells that remain, not over all cells
    assert same_position_overlap(grid(["b b"]), grid(["b c"]), exclude={"a"}) == (1, 0.5)
    assert same_position_overlap(grid(["b b"]), grid(["c c"]), exclude={"a"}) == (0, 0.0)


def test_weighted_overlap_values():
    # shares in A: a = 3/4, b = 1/4. Matching a cells weigh 4/3 each, the b cell weighs 4.
    # Matches: 3 a cells, total weight 3 * 4/3 + 4 = 8, so 4 / 8 = 0.5 (the mean of 1.0 and 0.0).
    assert weighted_overlap(grid(["a a a b"]), grid(["a a a a"])) == 0.5
    # plain same-position overlap of the same maps is 0.75
    assert same_position_overlap(grid(["a a a b"]), grid(["a a a a"])) == (3, 0.75)


def test_dominant_class_counts_both_maps():
    assert dominant_class(grid(["a a b"]), grid(["a b b"])) == ("a", 0.5)  # a 3 of 6; ties go by name
    assert dominant_class(grid(["a b"]), grid(["b b"])) == ("b", 0.75)


def test_background_match_only_is_discounted():
    # Class a covers 60 cells of each map; the 40 other cells sit at the same places in both
    # maps but each one changes class. A and B agree on the background and nowhere else.
    a, b = background_pair()
    assert sorted(set(x for r in a for x in r)) == ["a", "b", "c", "d", "e"]
    assert same_position_overlap(a, b) == (60, 0.6)
    assert same_position_overlap(a, b, exclude={"a"}) == (0, 0.0)
    # five classes, each carrying the same total weight: only the background class matches
    assert weighted_overlap(a, b) == pytest.approx(0.2)
    rep = report([a, b], names=("A", "B"))
    pair = rep["pairs"]["A-B"]
    assert pair["dominant"] == {"class": "a", "share": 0.6}
    assert pair["same_position"] == (60, 0.6)
    assert pair["same_position_excl_dominant"] == (0, 0.0)
    assert "A-B: same position 60 (60.0%)" in rep["text"]
    assert "    same position excl. dominant a (covers 60.0% of cells, gated): 0 (0.0%)" in rep["text"]
    assert "    weighted overlap: 20.0%" in rep["text"]
    # the gate reads the excluded value, so the background alone does not fail same-position
    assert not any("same-position" in f for f in rep["gates"]["failures"])


def background_pair():
    """10x10 maps: 2 cells in 5 are not class a, and each of them changes class in B."""

    def make(shift):
        return [
            ["a" if (x + 3 * y) % 5 >= 2 else "bcde"[(x + 2 * y + shift) % 4] for x in range(N)]
            for y in range(N)
        ]

    return make(0), make(1)


def test_two_class_balanced_pair_triggers_the_rule():
    # A and B are both half a, half b. The tie goes to a by name, and 50% is more than 40%,
    # so the gate reads the value without a. (A 50/50 two-class pair can never fall under 40%.)
    a = [list("aaaaabbbbb") for _ in range(10)]
    b = [list("aaaaabbbbb") if y < 5 else list("bbbbbaaaaa") for y in range(10)]
    assert dominant_class(a, b) == ("a", 0.5)
    assert same_position_overlap(a, b) == (50, 0.5)
    assert same_position_overlap(a, b, exclude={"a"}) == (25, 1.0)
    assert weighted_overlap(a, b) == 0.5
    ok, failures = scene_gates([a, b], names=("A", "B"))
    assert not ok and "A-B same-position excl. a 100.0% ≥ 25%" in failures


def test_balanced_three_class_pair_does_not_trigger_the_rule():
    # dominant covers exactly 40% of the 20 cells: the rule needs more than 40%
    a = grid(["a a a a b b b c c c"])
    b = grid(["a a a a c c c b b b"])
    assert dominant_class(a, b) == ("a", 0.4)
    rep = report([a, b], names=("A", "B"))
    pair = rep["pairs"]["A-B"]
    assert pair["same_position"] == (4, 0.4)
    assert "(covers 40.0% of cells, not gated): 0 (0.0%)" in rep["text"]
    # the gate reads the plain value (40%), not the excluded one (0%)
    assert "A-B same-position 40.0% ≥ 25%" in rep["gates"]["failures"]


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
    assert main(["scene-metrics", str(EXAMPLE)]) == 3  # scene gates fail
    out = capsys.readouterr().out
    assert "A-B: same position" in out and "A-C:" in out and "B-C:" in out
    assert "transferable blob" in out
    assert out.splitlines()[-1].startswith("scene gates: FAIL (A-B same-position 66.2% ≥ 25%; ")


def test_cli_scene_metrics_exit_zero_when_gates_pass(tmp_path, capsys):
    path = tmp_path / "pass.txt"
    path.write_text("\n\n".join("\n".join(" ".join(row) for row in m) for m in (PASS_A, PASS_B, PASS_C)) + "\n")
    assert main(["scene-metrics", str(path)]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == "scene gates: PASS"


# Hand-built 10x10 class maps. Each failing pair trips one scene gate, or two where noted.
N = 10


def _map(f):
    return [["abcdef"[f(x, y)] for x in range(N)] for y in range(N)]


PASS_A = _map(lambda x, y: (x * x + 3 * y + x * y) % 6)
PASS_B = _map(lambda x, y: (x * 5 + y * y * 2 + 1) % 6)
PASS_C = _map(lambda x, y: (x * y) % 6)
# B keeps 30% of A's cells in place and relabels the rest: same-position 30%, almost no 2x2 reuse.
# The classes are balanced, so the weighted overlap (38%) trips too.
SAME_B = [[PASS_A[y][x] if (x * 7 + y * 3) % 10 < 3 else "abcdef"[("abcdef".index(PASS_A[y][x]) + 1) % 6]
           for x in range(N)] for y in range(N)]
# A checkerboard and the same checkerboard shifted one column: every 2x2 window reappears, no cell matches.
CHECK_A = _map(lambda x, y: (x + y) % 2)
CHECK_B = _map(lambda x, y: (x + 1 + y) % 2)


def _with_block(f, x0, y0):
    """Background from f (classes a-d) with a 4x3 block of class f at (x0, y0)."""
    g = [["abcd"[f(x, y)] for x in range(N)] for y in range(N)]
    for y in range(y0, y0 + 3):
        for x in range(x0, x0 + 4):
            g[y][x] = "f"
    return g


# A 4x3 block of class f in both maps, at different places: a 12-cell transferable blob.
BLOB_A = _with_block(lambda x, y: (x * 5 + y * y * 2 + 1) % 4, 0, 0)
BLOB_B = _with_block(lambda x, y: (x * 3 + y * 7 + 2) % 4, 5, 6)


def test_hand_built_maps_pass_every_scene_gate():
    assert scene_gates([PASS_A, PASS_B, PASS_C]) == (True, [])
    assert report([PASS_A, PASS_B, PASS_C])["gates"] == {"ok": True, "failures": []}


@pytest.mark.parametrize(
    "a, b, failures",
    [
        (PASS_A, SAME_B, ["A-B same-position 30.0% ≥ 25%", "A-B weighted overlap 38.0% ≥ 25%"]),
        (CHECK_A, CHECK_B, ["A-B 2x2 window reuse 100.0% ≥ 30%"]),
        (BLOB_A, BLOB_B, ["A-B transferable blob 12.0% ≥ 10% of cells"]),
    ],
)
def test_each_scene_gate_fails(a, b, failures):
    assert scene_gates([a, b], names=("A", "B")) == (False, failures)
    rep = report([a, b], names=("A", "B"))
    assert rep["gates"] == {"ok": False, "failures": failures}
    assert rep["text"].splitlines()[-1] == f"scene gates: FAIL ({'; '.join(failures)})"


def test_weighted_gate_fails_alone(monkeypatch):
    monkeypatch.setitem(SCENE_GATES, "same_position_below", 0.9)
    assert scene_gates([PASS_A, SAME_B], names=("A", "B")) == (False, ["A-B weighted overlap 38.0% ≥ 25%"])


def test_gate_limits_are_a_tunable_dict(monkeypatch):
    assert SCENE_GATES == {
        "same_position_below": 0.25,
        "weighted_overlap_below": 0.25,
        "window_2x2_plain_below": 0.30,
        "transferable_below": 0.10,
    }
    assert scene_gates([PASS_A, SAME_B], names=("A", "B"))[0] is False
    monkeypatch.setitem(SCENE_GATES, "same_position_below", 0.35)
    monkeypatch.setitem(SCENE_GATES, "weighted_overlap_below", 0.5)
    assert scene_gates([PASS_A, SAME_B], names=("A", "B")) == (True, [])


def test_example_scene_file_fails_every_pair():
    ok, failures = scene_gates(load_scenes([EXAMPLE]))
    assert not ok and len(failures) == 12  # four gates on each of the three pairs
    assert "A-B same-position 66.2% ≥ 25%" in failures
    assert "A-B weighted overlap 35.1% ≥ 25%" in failures
    assert "A-C 2x2 window reuse 57.1% ≥ 30%" in failures
    assert "B-C transferable blob 27.5% ≥ 10% of cells" in failures


def test_report_text_documents_rule_and_new_lines():
    rep = report([PASS_A, PASS_B, PASS_C])
    text = rep["text"]
    assert "same-position gate: where the pair's dominant class covers more than 40% of the cells" in text
    assert text.count("same position excl. dominant") == 3
    assert text.count("weighted overlap:") == 3
    assert "A-B: same position" in text and text.splitlines()[-1] == "scene gates: PASS"
