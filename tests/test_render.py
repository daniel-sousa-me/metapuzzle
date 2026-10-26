import copy
import xml.etree.ElementTree as ET

import pytest
from PIL import Image

from metapuzzle.board import square_board
from metapuzzle.cli import main
from metapuzzle.optimize import solve
from metapuzzle.pieces import make_inventory
from metapuzzle.render import (
    flat_class_drawer,
    render_all,
    render_pieces_svg,
    render_solution_png,
    render_solution_svg,
)

SVG = "{http://www.w3.org/2000/svg}"


@pytest.fixture(scope="module")
def solution():
    boards = [square_board(6, 4), square_board(4, 6), square_board(8, 3)]
    return solve(boards, make_inventory(boards), seed=1, iters=3000)


def _slot_groups(svg):
    """(slot, piece, transform, fragment_xml) for every slot group, in document order."""
    out = []
    for g in ET.fromstring(svg).iter(SVG + "g"):
        if "data-slot" in g.attrib:
            frag = "".join(ET.tostring(c, encoding="unicode") for c in g)
            out.append((int(g.attrib["data-slot"]), g.attrib["data-piece"], g.attrib["transform"], frag))
    return out


def _counting(drawer):
    calls = []

    def wrapped(piece_id, cls, seed, size):
        calls.append(piece_id)
        return drawer(piece_id, cls, seed, size)

    return wrapped, calls


def test_one_group_per_slot(solution):
    for k in range(3):
        groups = _slot_groups(render_solution_svg(solution, k, flat_class_drawer()))
        assert sorted(g[0] for g in groups) == list(range(solution.boards[k].n_slots))
        assert all(t.startswith("translate(") and "rotate(" in t for _, _, t, _ in groups)


def test_same_piece_identical_artwork_across_solutions(solution):
    drawer = flat_class_drawer()
    frags, slots = {}, {}
    for k in range(3):
        for slot, pid, _, frag in _slot_groups(render_solution_svg(solution, k, drawer)):
            frags.setdefault(pid, set()).add(frag)
            slots.setdefault(pid, set()).add((k, slot))
    assert len(frags) == len(solution.pieces)
    assert all(len(f) == 1 for f in frags.values())
    # identical artwork, but the pieces really do sit in different positions
    assert any(len({slot for k, slot in s}) > 1 for s in slots.values())


def test_rotation_applied_only_when_requested(solution):
    sol = copy.deepcopy(solution)
    pid, (slot, _) = next(iter(sol.placements[0].items()))
    sol.placements[0][pid] = (slot, 90)
    groups = {pid_: t for _, pid_, t, _ in _slot_groups(render_solution_svg(sol, 0, flat_class_drawer()))}
    assert "rotate(90," in groups[str(pid)]
    groups = {pid_: t for _, pid_, t, _ in _slot_groups(render_solution_svg(sol, 0, flat_class_drawer(), rotate=False))}
    assert "rotate(90," not in groups[str(pid)] and "rotate(0," in groups[str(pid)]


def test_drawer_called_once_per_piece(solution, tmp_path):
    drawer, calls = _counting(flat_class_drawer())
    render_all(solution, drawer, tmp_path, "t", cell_size=16)
    assert sorted(calls, key=int) == [str(p.piece_id) for p in sorted(solution.pieces, key=lambda p: p.piece_id)]


def test_default_drawer_deterministic_and_seeded():
    d = flat_class_drawer()
    a = d("3", "any", 3, 40.0)
    assert a == d("3", "any", 3, 40.0)
    assert a != d("4", "any", 4, 40.0)
    assert a.count("<circle") == 12
    assert d("3", "any", 3, 40.0) != d("3", "other", 3, 40.0)  # class changes the colour
    assert 'fill="#ff0000"' in flat_class_drawer({"any": "#ff0000"})("0", "any", 0, 10.0)
    with pytest.raises(ValueError):
        flat_class_drawer({"any": "red"})


def test_png_dimensions(solution, tmp_path):
    svg = render_solution_svg(solution, 2, flat_class_drawer(), cell_size=20, margin=8)
    path = render_solution_png(svg, tmp_path / "c.png")
    with Image.open(path) as im:
        assert im.size == (2 * 8 + 8 * 20, 2 * 8 + 3 * 20)  # board C is 8x3


def test_render_all_files_and_contact_sheet(solution, tmp_path):
    written = render_all(solution, flat_class_drawer(), tmp_path, "demo", cell_size=20, labels=True)
    assert sorted(p.name for p in written.values()) == sorted(
        [f"demo-{n}.{e}" for n in "ABC" for e in ("svg", "png")] + ["demo-pieces.png"]
    )
    for name, board in zip("ABC", solution.boards):
        with Image.open(tmp_path / f"demo-{name}.png") as im:
            assert im.size == (2 * 8 + board.cols * 20, 2 * 8 + board.rows * 20)
    sheet = render_pieces_svg(solution, flat_class_drawer(), cell_size=20)
    root = ET.fromstring(sheet)
    cells = [int(g.attrib["data-piece"]) for g in root.iter(SVG + "g") if "data-piece" in g.attrib]
    assert cells == sorted(p.piece_id for p in solution.pieces)
    with Image.open(written["pieces.png"]) as im:
        assert im.size == (int(float(root.attrib["width"])), int(float(root.attrib["height"])))


def test_labels_and_grid_options(solution):
    svg = render_solution_svg(solution, 0, flat_class_drawer(), grid="strong", labels=True)
    assert svg.count("<text") == solution.boards[0].n_slots
    grid = [g for g in ET.fromstring(svg).iter(SVG + "g") if g.attrib.get("fill") == "none"]
    assert len(grid) == 1 and len(grid[0]) == solution.boards[0].n_slots
    assert grid[0].attrib["stroke-width"] == "1.2"
    assert "stroke-width" not in render_solution_svg(solution, 0, flat_class_drawer())
    with pytest.raises(ValueError):
        render_solution_svg(solution, 0, flat_class_drawer(), grid="bold")


def test_render_cli(solution, tmp_path, capsys):
    src = tmp_path / "sol.json"
    solution.save(src)
    out = tmp_path / "out"
    assert main(["render", str(src), "--out", str(out), "--cell", "16", "--grid", "faint", "--labels"]) == 0
    for name in "ABC":
        assert (out / f"sol-{name}.svg").exists() and (out / f"sol-{name}.png").exists()
    assert (out / "sol-pieces.png").exists()
