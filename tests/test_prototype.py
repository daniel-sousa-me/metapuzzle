import pytest
from PIL import Image

from metapuzzle.classes import SAMPLE_SPEC_PATH
from metapuzzle.cli import main
from metapuzzle.optimize import Solution, validate_solution
from metapuzzle.prototype import run_prototype
from metapuzzle.scene import SceneError

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
    assert "valid=True" in capsys.readouterr().out
    assert (out / "triptych.png").is_file() and (out / "summary.md").is_file()
    assert validate_solution(Solution.load(out / "solution.json")) == []
    assert main(["prototype", "--scenes", str(scenes), "--classes", str(SAMPLE_SPEC_PATH),
                 "--out", str(tmp_path / "x"), "--sizes", "8x10"]) == 1
    assert "error" in capsys.readouterr().err
