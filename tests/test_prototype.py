import pytest
from PIL import Image

from metapuzzle.classes import SAMPLE_SPEC_PATH
from metapuzzle.cli import main
from metapuzzle.optimize import Solution, validate_solution
from metapuzzle.prototype import run_prototype
from metapuzzle.board import square_board
from metapuzzle.scene import SceneError, load_scenes, pieces_from_scenes

# Identical histograms (canopy 14, sea 3, sun 3) and identical border counts: the frame is all canopy.
TINY_SCENES = """\
# A
canopy canopy canopy canopy
canopy sea  sun  canopy
canopy sun  sea  canopy
canopy sea  sun  canopy
canopy canopy canopy canopy

# B
canopy canopy canopy canopy
canopy sun sea canopy
canopy sea sun canopy
canopy sun sea canopy
canopy canopy canopy canopy

# C
canopy canopy canopy canopy
canopy sea sea canopy
canopy sun sun canopy
canopy sea sun canopy
canopy canopy canopy canopy
"""

FILES = [
    "solution.json", "metrics.txt", "solution-A.svg", "solution-A.png", "solution-B.svg",
    "solution-B.png", "solution-C.svg", "solution-C.png", "solution-pieces.png", "triptych.png",
    "triptych-grid.png", "grid-faint/solution-A.png", "grid-faint/solution-B.png",
    "grid-faint/solution-C.png", "summary.md",
]


@pytest.fixture
def scenes(tmp_path):
    path = tmp_path / "tiny.txt"
    path.write_text(TINY_SCENES)
    return path


def test_run_prototype_writes_outputs_and_valid_solution(tmp_path, scenes):
    out = tmp_path / "out"
    res = run_prototype(scenes, SAMPLE_SPEC_PATH, out, iters=3000)
    for name in FILES:
        assert (out / name).is_file(), name
    assert res["valid"] and res["violations"] == []
    sol = Solution.load(out / "solution.json")
    assert validate_solution(sol) == []
    assert [(b.cols, b.rows) for b in sol.boards] == [(4, 5)] * 3
    assert set(res["shared"]) == {"AB", "AC", "BC"}
    summary = (out / "summary.md").read_text()
    assert "| AB |" in summary and "- valid: yes" in summary and "solution.json" in summary
    piece_line, scene_line = res["gate_lines"]
    assert piece_line.startswith("piece gates: ") and scene_line.startswith("scene gates: ")
    assert "## Gates" in summary and f"- {piece_line}" in summary and f"- {scene_line}" in summary
    assert (out / "scene-metrics.txt").read_text().splitlines()[-1] == scene_line
    assert set(res["gates"]) == {"piece", "scene", "failures"}
    assert (piece_line == "piece gates: PASS") == res["gates"]["piece"]
    assert (scene_line == "scene gates: PASS") == res["gates"]["scene"]
    assert all(f.startswith(("piece: ", "scene: ")) for f in res["gates"]["failures"])
    with Image.open(out / "triptych.png") as im:
        assert im.height <= 600 and im.width > 3 * 4 * 48


def test_quarter_rotation_uses_spec_rotations(tmp_path, scenes):
    res = run_prototype(scenes, SAMPLE_SPEC_PATH, tmp_path / "q", rotation="quarter", iters=3000)
    sol = Solution.load(res["files"]["solution.json"])
    assert validate_solution(sol) == []
    assert {p.cls for p in sol.pieces} == {"canopy", "sea", "sun"}
    for piece in sol.pieces:  # the sample spec allows all four rotations for these classes
        assert piece.allowed_rotations == {0, 90, 180, 270}


def test_sizes_must_match_class_maps(tmp_path, scenes):
    with pytest.raises(SceneError, match="differ from the class map sizes"):
        run_prototype(scenes, SAMPLE_SPEC_PATH, tmp_path / "bad", sizes="8x10", iters=100)
    assert not (tmp_path / "bad").exists()


def test_cli_prototype(tmp_path, scenes, capsys):
    out = tmp_path / "cli"
    args = ["prototype", "--scenes", str(scenes), "--classes", str(SAMPLE_SPEC_PATH), "--out", str(out),
            "--sizes", "4x5,4x5,4x5", "--iters", "3000", "--cell", "24"]
    assert main(args) == 0
    text = capsys.readouterr().out
    assert "valid=True" in text and "piece gates: " in text and "scene gates: " in text
    assert (out / "triptych.png").is_file() and (out / "summary.md").is_file()
    assert validate_solution(Solution.load(out / "solution.json")) == []
    assert main(["prototype", "--scenes", str(scenes), "--classes", str(SAMPLE_SPEC_PATH),
                 "--out", str(tmp_path / "x"), "--sizes", "8x10"]) == 1
    assert "error" in capsys.readouterr().err


def _mixed_scenes(path):
    """Three concentric maps (canopy outside, then sea, then sun) in 6x8, 8x6 and 12x4 frames."""
    blocks = []
    for cols, rows in [(6, 8), (8, 6), (12, 4)]:
        cells = sorted((min(x, y, cols - 1 - x, rows - 1 - y), y, x) for y in range(rows) for x in range(cols))
        grid = [[""] * cols for _ in range(rows)]
        for i, (_, y, x) in enumerate(cells):
            grid[y][x] = "canopy" if i < 40 else "sea" if i < 44 else "sun"
        blocks.append("\n".join(" ".join(r) for r in grid))
    path.write_text("\n\n".join(blocks) + "\n")
    return path


@pytest.mark.parametrize("rotation", ["none", "quarter"])
def test_mixed_frames_with_class_maps_are_valid(tmp_path, rotation):
    scenes = _mixed_scenes(tmp_path / "mixed.txt")
    res = run_prototype(scenes, SAMPLE_SPEC_PATH, tmp_path / "out", rotation=rotation, cell=12)
    assert res["valid"] and res["violations"] == []
    sol = Solution.load(res["files"]["solution.json"])
    assert [(b.cols, b.rows) for b in sol.boards] == [(6, 8), (8, 6), (12, 4)]
    assert validate_solution(sol) == []
    assert all(x["flat_pieces_inside"] > 0 for x in res["seams"][:2])  # the smaller frames hold seams
    assert "interior seams (A / B / C)" in (tmp_path / "out" / "summary.md").read_text()


def test_extra_flat_option(tmp_path, capsys):
    scenes = _mixed_scenes(tmp_path / "mixed.txt")
    args = ["prototype", "--scenes", str(scenes), "--classes", str(SAMPLE_SPEC_PATH), "--out", str(tmp_path / "c"),
            "--rotation", "quarter", "--extra-flat", "4", "--cell", "12", "--iters", "2000"]
    assert main(args) == 0
    assert "valid=True" in capsys.readouterr().out
    sol = Solution.load(tmp_path / "c" / "solution.json")
    assert validate_solution(sol) == []
    assert "- extra_flat: 4" in (tmp_path / "c" / "summary.md").read_text()
    flat = lambda pieces: sum("flat" in p.sides for p in pieces)  # noqa: E731
    boards = [square_board(c, r, "standard", "quarter") for c, r in [(6, 8), (8, 6), (12, 4)]]
    maps = load_scenes(scenes)
    assert flat(sol.pieces) >= flat(pieces_from_scenes(boards, maps)) + 4
