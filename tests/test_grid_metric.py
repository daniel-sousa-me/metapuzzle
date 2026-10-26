import json
import re
import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from metapuzzle.cli import main
from metapuzzle.grid_metric import edge_contrast, grid_score

REPO = Path(__file__).resolve().parents[1]
COLS, ROWS, CELL, MARGIN = 4, 3, 48, 8


def _size(scale: int = 1) -> tuple[int, int]:
    return scale * (2 * MARGIN + COLS * CELL), scale * (2 * MARGIN + ROWS * CELL)


def _flat_png(path: Path) -> Path:
    """Checkerboard of two flat colours: every neighbouring pair differs, nothing varies inside a cell."""
    w, h = _size()
    img = np.full((h, w, 3), 255, np.uint8)
    for r in range(ROWS):
        for c in range(COLS):
            colour = (200, 30, 30) if (r + c) % 2 == 0 else (30, 30, 200)
            img[MARGIN + r * CELL : MARGIN + (r + 1) * CELL, MARGIN + c * CELL : MARGIN + (c + 1) * CELL] = colour
    Image.fromarray(img).save(path)
    return path


def _noise_png(path: Path) -> Path:
    """Uniform random noise over the whole image: same texture on both sides of every edge."""
    w, h = _size()
    Image.fromarray(np.random.default_rng(0).integers(0, 256, (h, w, 3), dtype=np.uint8)).save(path)
    return path


def test_flat_cells_are_fully_visible(tmp_path):
    m = edge_contrast(_flat_png(tmp_path / "flat.png"), COLS, ROWS, CELL, MARGIN)
    assert m["visible_fraction"] == 1.0
    assert m["line_fraction"] == 1.0
    assert m["n_segments"] == ROWS * (COLS - 1) + COLS * (ROWS - 1)
    assert m["n_lines"] == (COLS - 1) + (ROWS - 1)
    assert m["within_median"] == {"v": 0.0, "h": 0.0}
    assert grid_score(m) == 5.0


def test_uniform_noise_is_invisible(tmp_path):
    m = edge_contrast(_noise_png(tmp_path / "noise.png"), COLS, ROWS, CELL, MARGIN)
    assert m["visible_fraction"] <= 0.05
    assert m["line_fraction"] == 0.0
    assert grid_score(m) == 1.0


def test_integer_render_scale_is_accounted_for(tmp_path):
    flat = Image.open(_flat_png(tmp_path / "flat.png"))
    doubled = flat.resize(_size(2), Image.NEAREST)
    doubled.save(tmp_path / "flat2.png")
    m = edge_contrast(tmp_path / "flat2.png", COLS, ROWS, CELL, MARGIN)
    assert m["visible_fraction"] == 1.0


def test_wrong_geometry_is_error(tmp_path):
    with pytest.raises(ValueError, match="expected"):
        edge_contrast(_flat_png(tmp_path / "flat.png"), COLS + 1, ROWS, CELL, MARGIN)


def test_grid_score_bands():
    fractions = (0.0, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.71, 1.0)
    assert [grid_score(f) for f in fractions] == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]
    assert grid_score({"visible_fraction": 0.55}) == 4.0


def _synthetic_run(tmp_path: Path) -> Path:
    run = tmp_path / "run"
    run.mkdir()
    (run / "summary.md").write_text(
        "# Prototype summary\n\n## Parameters\n\n- sizes: 4x3, 4x3, 4x3\n- cell: 48\n- valid: yes\n",
        encoding="utf-8",
    )
    board = {"cols": COLS, "rows": ROWS, "border": "standard", "rotation": "none"}
    (run / "solution.json").write_text(json.dumps({"format": "metapuzzle-solution", "boards": [board] * 3}))
    for name in "ABC":
        shutil.copy(_flat_png(tmp_path / "flat.png"), run / f"solution-{name}.png")
    return run


def test_cli_grid_metric_on_synthetic_run(tmp_path, capsys):
    assert main(["grid-metric", str(_synthetic_run(tmp_path))]) == 0
    lines = [ln for ln in capsys.readouterr().out.splitlines() if re.match(r"^[ABC] ", ln)]
    assert len(lines) == 3
    assert all("visible 1.000" in ln and "lines 1.000" in ln and "score 5" in ln for ln in lines)


def test_cli_grid_metric_on_experiment_run(capsys):
    run = REPO / "experiments" / "002-direction-a" / "run-none"
    if not run.is_dir():
        pytest.skip("experiment run folder not present")
    assert main(["grid-metric", str(run)]) == 0
    rows = re.findall(r"^([ABC]) +visible ([\d.]+) +lines ([\d.]+) +score (\d)", capsys.readouterr().out, re.M)
    assert [r[0] for r in rows] == ["A", "B", "C"]
    assert all(0.0 <= float(v) <= 1.0 and 0.0 <= float(l) <= 1.0 and 1 <= int(s) <= 5 for _, v, l, s in rows)


def test_cli_grid_metric_missing_run_is_error(tmp_path, capsys):
    assert main(["grid-metric", str(tmp_path)]) == 1
    assert "error" in capsys.readouterr().err
