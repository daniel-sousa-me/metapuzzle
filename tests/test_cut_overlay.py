import pytest
from PIL import Image

from metapuzzle.board import square_board
from metapuzzle.classes import SAMPLE_SPEC_PATH
from metapuzzle.cli import main
from metapuzzle.optimize import Solution, solve
from metapuzzle.pieces import make_inventory
from metapuzzle.prototype import (
    CUT_RUN_MIN,
    cut_stats,
    cuts_report_text,
    flat_seams,
    run_prototype,
    seam_counts,
    straight_runs,
)
from metapuzzle.render import cut_outline_d

# Same tiny three-map set as test_prototype.py: a canopy frame, with the interior of each map
# differing. Two surplus flat pieces per board sit inside as seams when extra_flat=2.
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


@pytest.fixture
def scenes(tmp_path):
    path = tmp_path / "tiny.txt"
    path.write_text(TINY_SCENES)
    return path


def test_cut_overlay_writes_images_and_report(tmp_path, scenes):
    out = tmp_path / "out"
    res = run_prototype(scenes, SAMPLE_SPEC_PATH, out, iters=3000, cell=24, extra_flat=2, cut_overlay=True)
    assert res["valid"]
    for name in ("A", "B", "C"):
        cuts = out / f"solution-{name}-cuts.png"
        assert cuts.is_file() and f"solution-{name}-cuts.png" in res["files"]
        with Image.open(cuts) as im, Image.open(out / f"solution-{name}.png") as plain:
            assert im.size == plain.size  # the normal render, with the outlines on top
    report = (out / "cuts-report.txt").read_text()
    sol = Solution.load(out / "solution.json")
    assert report == cuts_report_text(cut_stats(sol))
    for name, seams in zip("ABC", seam_counts(sol)):
        assert f"{name}  4x5  interior flat seams {seams['seams']} " in report
    assert "cut overlay: on" in (out / "summary.md").read_text()


def test_cut_outline_line_count(tmp_path):
    for rotation in ("none", "quarter"):
        boards = [square_board(6, 4, rotation=rotation), square_board(4, 6, rotation=rotation),
                  square_board(8, 3, rotation=rotation)]
        sol = solve(boards, make_inventory(boards), seed=1, iters=1500)
        by_id = {p.piece_id: p for p in sol.pieces}
        for k, board in enumerate(boards):
            path = cut_outline_d(sol, k, cell_size=24)
            # Each cell has four sides, one subpath each; a non-flat side is one bump (one arc).
            nonflat = sum(
                1 for pid, (_, rot) in sol.placements[k].items()
                for side in range(4) if by_id[pid].sides[(side - rot // 90) % 4] != "flat"
            )
            assert path.count("M") == 4 * board.n_slots
            assert path.count("A") == nonflat
            flat_subpaths = path.count("M") - path.count("A")
            assert flat_subpaths == 4 * board.n_slots - nonflat
        if rotation == "quarter":
            assert any(rot for pl in sol.placements for _, rot in pl.values())


def test_straight_runs_and_seam_consistency(tmp_path, scenes):
    seams = [("V", 3, 0), ("V", 3, 1), ("V", 3, 2), ("V", 3, 5), ("V", 3, 6), ("H", 2, 0), ("H", 2, 1)]
    runs = straight_runs(seams)
    assert sorted(runs) == [("H", 2, 0, 2), ("V", 3, 0, 3), ("V", 3, 5, 2)]
    assert [r for r in runs if r[3] >= CUT_RUN_MIN] == [("V", 3, 0, 3)]

    res = run_prototype(scenes, SAMPLE_SPEC_PATH, tmp_path / "seams", iters=3000, extra_flat=2, cut_overlay=True)
    sol = Solution.load(res["files"]["solution.json"])
    for k, counted in enumerate(seam_counts(sol)):
        assert len(flat_seams(sol, k)) == counted["seams"] > 0
    for st in cut_stats(sol):
        assert st["vertical"] + st["horizontal"] == st["seams"]
        assert st["run_seams"] == sum(r[3] for r in st["runs"]) <= st["seams"]


def test_cut_overlay_off_writes_no_cut_files(tmp_path, scenes):
    out = tmp_path / "plain"
    res = run_prototype(scenes, SAMPLE_SPEC_PATH, out, iters=3000)
    assert not any("cuts" in name for name in res["files"])
    assert not list(out.glob("*cuts*"))
    assert "cut overlay" not in (out / "summary.md").read_text()


def test_cli_cut_overlay_flag(tmp_path, scenes, capsys):
    out = tmp_path / "cli"
    args = ["prototype", "--scenes", str(scenes), "--classes", str(SAMPLE_SPEC_PATH), "--out", str(out),
            "--sizes", "4x5,4x5,4x5", "--iters", "3000", "--cell", "24", "--cut-overlay"]
    assert main(args) == 0
    assert "valid=True" in capsys.readouterr().out
    for name in ("A", "B", "C"):
        assert (out / f"solution-{name}-cuts.png").is_file()
    assert (out / "cuts-report.txt").is_file()
