import json

from metapuzzle.cli import main
from metapuzzle.optimize import Solution, validate_solution


def test_solve_report_round_trip(tmp_path, capsys):
    out = tmp_path / "sol.json"
    assert main(["solve", "--cols", "10", "--rows", "8", "--seed", "1", "--out", str(out)]) == 0
    data = json.loads(out.read_text())
    assert data["format"] == "metapuzzle-solution" and len(data["placements"]) == 3 and len(data["pieces"]) == 80
    assert data["boards"][0] == {"cols": 10, "rows": 8, "border": "standard", "rotation": "none"}
    sol = Solution.load(out)
    assert validate_solution(sol) == []
    capsys.readouterr()
    assert main(["report", str(out)]) == 0
    text = capsys.readouterr().out
    assert "AB: shared=0" in text and "validity: OK" in text and "piece gates: PASS" in text.splitlines()
    assert main(["report", str(out), "--json"]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert rep["total_shared"] == 0


def test_sizes_option_mixed_frames(tmp_path, capsys):
    out = tmp_path / "mixed.json"
    code = main(["solve", "--sizes", "8x12,12x8,16x6", "--rotation", "quarter", "--out", str(out)])
    assert code == 0
    sol = Solution.load(out)
    assert [(b.cols, b.rows) for b in sol.boards] == [(8, 12), (12, 8), (16, 6)]
    assert main(["report", str(out)]) == 0


def test_sizes_unequal_piece_counts_is_error(capsys):
    assert main(["solve", "--sizes", "8x12,12x8,16x7"]) == 1
    assert "error" in capsys.readouterr().err


def test_scenes_and_options(tmp_path):
    maps = tmp_path / "scenes.txt"
    rows = lambda f: "\n".join(" ".join(f(x, y) for x in range(6)) for y in range(4))
    blocks = [rows(lambda x, y: "a" if y < 2 else "b"), rows(lambda x, y: "a" if x < 3 else "b"), rows(lambda x, y: "a" if (x + y) % 2 == 0 else "b")]
    maps.write_text("\n\n".join(blocks) + "\n")
    out = tmp_path / "s.json"
    assert main(["solve", "--border", "tray", "--scenes", str(maps), "--out", str(out)]) == 0
    sol = Solution.load(out)
    assert sol.class_maps is not None and validate_solution(sol) == []
    out2 = tmp_path / "t.json"
    assert main(["solve", "--free-corners", "--distinct-corner-orders", "--extra-flat", "2", "--out", str(out2)]) == 0
    assert Solution.load(out2).meta["distinct_corner_orders"] is True


def test_scene_error_reported(tmp_path, capsys):
    p = tmp_path / "bad.txt"
    p.write_text("a b\nb a\n\na a\nb b\n\na a\na a\n")
    assert main(["solve", "--border", "tray", "--scenes", str(p)]) == 1
    assert "histograms" in capsys.readouterr().err
