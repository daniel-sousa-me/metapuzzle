import json

import pytest

from metapuzzle.board import square_board
from metapuzzle.scene import ClassMap, SceneError, load_scenes, parse_text, parse_token, pieces_from_scenes, validate_scenes


def grid(cols, rows, f):
    return ClassMap.from_tokens([[f(x, y) for x in range(cols)] for y in range(rows)])


def test_parse_token():
    assert parse_token("sky") == ("sky", 0)
    assert parse_token("sky@0") == ("sky", 0)
    assert parse_token("sky@90") == ("sky", 90)
    for bad in ("sky@45", "@90", "sky@x", "a@1@2"):
        with pytest.raises(SceneError):
            parse_token(bad)


def test_parse_text_and_load(tmp_path):
    text = "# A\na b\nb a\n\nb a\na b\n\na a\nb b\n"
    maps = parse_text(text)
    assert len(maps) == 3 and maps[0].cls == [["a", "b"], ["b", "a"]]
    p = tmp_path / "s.txt"
    p.write_text(text)
    assert len(load_scenes([p])) == 3
    j = tmp_path / "s.json"
    j.write_text(json.dumps({"maps": [["a b", "b a"], ["b a", "a b"], ["a a", "b b"]]}))
    assert load_scenes(j)[2].cls == [["a", "a"], ["b", "b"]]
    with pytest.raises(SceneError):
        load_scenes([p, p])


def test_ragged_rows_rejected():
    with pytest.raises(SceneError):
        parse_text("a b\na\n")


def test_valid_scenes_and_inventory():
    b = square_board(4, 3, "tray")
    maps = [grid(4, 3, lambda x, y: "sky" if y == 0 else "sea"), grid(4, 3, lambda x, y: "sky" if y == 2 else "sea"),
            grid(4, 3, lambda x, y: "sky" if y == 1 else "sea")]
    validate_scenes(b, maps)
    inv = pieces_from_scenes(b, maps)
    assert len(inv) == 12 and sum(p.cls == "sky" for p in inv) == 4


def test_histogram_mismatch():
    b = square_board(4, 3, "tray")
    maps = [grid(4, 3, lambda x, y: "a"), grid(4, 3, lambda x, y: "a"), grid(4, 3, lambda x, y: "b" if x == 0 else "a")]
    with pytest.raises(SceneError, match="histograms"):
        validate_scenes(b, maps)


def test_dimension_mismatch():
    b = square_board(4, 3, "tray")
    maps = [grid(4, 3, lambda x, y: "a")] * 2 + [grid(3, 4, lambda x, y: "a")]
    with pytest.raises(SceneError, match="board"):
        validate_scenes(b, maps)


def test_border_side_counts_checked_without_rotation():
    b = square_board(5, 4)
    mk = lambda top: grid(5, 4, lambda x, y: "sky" if (y == 0 and top) or (y == 3 and not top) else "sea")
    maps = [mk(True), mk(False), mk(True)]
    # histograms match (5 sky each) but the top side holds different classes
    with pytest.raises(SceneError, match="border"):
        validate_scenes(b, maps)
    validate_scenes(b, maps, strict_border=False)


def test_border_pooled_under_quarter():
    b = square_board(5, 4, rotation="quarter")
    mk = lambda top: grid(5, 4, lambda x, y: "sky" if (y == 0 and 0 < x < 4) == top and 0 < x < 4 and y in (0, 3) else "sea")
    maps = [mk(True), mk(False), mk(True)]
    validate_scenes(b, maps)


def test_orientation_suffix_rules():
    b = square_board(4, 3, "tray")
    m = grid(4, 3, lambda x, y: "a@90" if (x, y) == (1, 1) else "a")
    with pytest.raises(SceneError, match="quarter"):
        validate_scenes(b, [m] * 3)
    bq = square_board(4, 3, "tray", "quarter")
    validate_scenes(bq, [m] * 3)
    bs = square_board(5, 4, "standard", "quarter")
    mb = grid(5, 4, lambda x, y: "a@90" if (x, y) == (0, 1) else "a")
    with pytest.raises(SceneError, match="border"):
        validate_scenes(bs, [mb] * 3)


def test_bad_label():
    with pytest.raises(SceneError):
        parse_text("a@b\n")


def test_pieces_from_scenes_standard_mixed_frames():
    bs = [square_board(c, r) for c, r in [(8, 12), (12, 8), (16, 6)]]
    maps = [grid(c, r, lambda x, y: "sky" if y < r // 2 else "sea") for c, r in [(8, 12), (12, 8), (16, 6)]]
    maps[1] = grid(12, 8, lambda x, y: "sky" if x < 6 else "sea")
    maps[2] = grid(16, 6, lambda x, y: "sky" if x < 8 else "sea")
    inv = pieces_from_scenes(bs, maps)
    assert len(inv) == 96 and sum(p.cls == "sky" for p in inv) == 48
