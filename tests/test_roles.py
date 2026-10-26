import pytest

from metapuzzle.board import square_board
from metapuzzle.cli import main
from metapuzzle.roles import assign_classes, parse_roles_spec, write_scene_file
from metapuzzle.scene import SceneError, load_scenes, validate_scenes
from metapuzzle.scene_metrics import same_position_overlap

SPEC = {
    "roles": {
        "petal": {"classes": ["GD", "GB", "GT"], "weights": [1, 1, 1]},
        "sea": {"classes": ["TE", "NT"]},
        "sky": {"classes": ["BL", "CR"]},
    },
    "fixed": {},
}

# 4 cols x 5 rows. Each side and the interior hold the same role multiset in all three maps,
# so the border rule can be met; the positions differ.
MAP_A = """
sky sky petal sky
sky petal petal sea
petal sea sea sky
sea petal sea petal
sky sea sea sky
"""
MAP_B = """
sky petal sky sky
sea sea petal petal
sky petal sea sea
petal sea petal sky
sky sea sea sky
"""
MAP_C = """
sky sky petal sky
petal sea sea sky
sea petal petal petal
sky petal sea sea
sky sea sea sky
"""


def roles_maps(*texts):
    return [[r.split() for r in t.strip().splitlines()] for t in texts]


def overlaps(maps):
    return sum(same_position_overlap(maps[i], maps[j])[0] for i, j in ((0, 1), (0, 2), (1, 2)))


def test_example_gives_identical_histograms_and_border_rule():
    maps = assign_classes(roles_maps(MAP_A, MAP_B, MAP_C), SPEC, seed=0)
    board = square_board(4, 5)
    validate_scenes([board] * 3, maps)  # identical histograms and strict border counts
    assert maps[0].histogram() == maps[1].histogram() == maps[2].histogram()
    for m, text in zip(maps, (MAP_A, MAP_B, MAP_C)):
        roles = roles_maps(text)[0]
        for y, row in enumerate(roles):
            for x, role in enumerate(row):
                assert m.cls[y][x] in SPEC["roles"][role]["classes"]


def test_quarter_rotation_pools_border_and_validates():
    maps = assign_classes(roles_maps(MAP_A, MAP_B, MAP_C), SPEC, rotation="quarter", seed=1)
    validate_scenes([square_board(4, 5, rotation="quarter")] * 3, maps)


def test_overlap_not_worse_than_greedy_start():
    greedy = assign_classes(roles_maps(MAP_A, MAP_B, MAP_C), SPEC, seed=0, iters=0)
    annealed = assign_classes(roles_maps(MAP_A, MAP_B, MAP_C), SPEC, seed=0, iters=20000)
    assert overlaps(annealed) <= overlaps(greedy)
    assert overlaps(annealed) < overlaps(greedy)  # the example has room to improve


def test_restarts_keep_the_best_run():
    one = assign_classes(roles_maps(MAP_A, MAP_B, MAP_C), SPEC, seed=0, iters=3000, restarts=1)
    many = assign_classes(roles_maps(MAP_A, MAP_B, MAP_C), SPEC, seed=0, iters=3000, restarts=6)
    assert overlaps(many) <= overlaps(one)


def test_target_counts_fix_the_histogram():
    target = {"BL": 7, "CR": 0, "GD": 2, "GB": 2, "GT": 2, "TE": 3, "NT": 4}
    spec = dict(SPEC, target_counts=target)
    maps = assign_classes(roles_maps(MAP_A, MAP_B, MAP_C), spec, seed=0)
    assert dict(maps[0].histogram()) == {k: v for k, v in target.items() if v} == dict(maps[2].histogram())


def test_infeasible_target_names_role_and_class():
    # Map A has three 'stone' cells, which only OC can take, but the target gives OC one cell.
    spec = {
        "roles": {"stone": {"classes": ["OC"]}, "sky": {"classes": ["BL", "CR"]},
                  "petal": {"classes": ["GD", "GB", "GT"]}, "sea": {"classes": ["TE", "NT"]}},
        "target_counts": {"OC": 1, "BL": 7, "GD": 6, "TE": 6},
    }
    a = MAP_A.replace("petal petal sea", "stone stone sea", 1).replace("petal sea sea sky", "stone sea sea sky")
    with pytest.raises(SceneError, match="stone.*OC"):
        assign_classes(roles_maps(a, MAP_B, MAP_C), spec, seed=0)


def test_infeasible_fixed_count_fails_the_search():
    # 'sea' may also take OC, so every map can hold the one fixed OC cell; map A still needs three.
    spec = {
        "roles": {"stone": {"classes": ["OC"]}, "sky": {"classes": ["BL", "CR"]},
                  "petal": {"classes": ["GD", "GB", "GT"]}, "sea": {"classes": ["TE", "NT", "OC"]}},
        "fixed": {"OC": 1},
    }
    a = MAP_A.replace("petal petal sea", "stone stone sea", 1).replace("petal sea sea sky", "stone sea sea sky")
    with pytest.raises(SceneError, match="no common histogram found.*stone"):
        assign_classes(roles_maps(a, MAP_B, MAP_C), spec, seed=0, iters=3000)


def test_bad_specs_are_rejected():
    with pytest.raises(SceneError, match="classes"):
        parse_roles_spec({"roles": {"sky": {"classes": []}}})
    with pytest.raises(SceneError, match="weights"):
        parse_roles_spec({"roles": {"sky": {"classes": ["BL", "CR"], "weights": [1]}}})
    with pytest.raises(SceneError, match="unknown"):
        parse_roles_spec({"roles": {"sky": {"classes": ["BL"]}}, "fixd": {}})
    with pytest.raises(SceneError, match="not in the roles spec|does not define"):
        assign_classes(roles_maps(MAP_A.replace("sky", "moon", 1), MAP_B, MAP_C), SPEC)


def test_write_scene_file_round_trip(tmp_path):
    maps = assign_classes(roles_maps(MAP_A, MAP_B, MAP_C), SPEC, seed=0)
    path = tmp_path / "scenes.txt"
    write_scene_file(maps, path)
    loaded = load_scenes(path)
    assert [m.cls for m in loaded] == [m.cls for m in maps]
    validate_scenes([square_board(4, 5)] * 3, loaded)


def test_cli_writes_scenes_and_reports(tmp_path, capsys):
    roles = tmp_path / "roles.txt"
    roles.write_text(f"{MAP_A}\n{MAP_B}\n{MAP_C}")
    spec = tmp_path / "spec.json"
    spec.write_text(
        '{"roles": {"petal": {"classes": ["GD", "GB", "GT"]}, "sea": {"classes": ["TE", "NT"]}, '
        '"sky": {"classes": ["BL", "CR"]}}}'
    )
    out = tmp_path / "scenes.txt"
    assert main(["roles-to-scenes", str(roles), "--spec", str(spec), "--out", str(out), "--seed", "2"]) == 0
    text = capsys.readouterr().out
    assert "histogram:" in text and "same-position A-B" in text and "validate_scenes OK" in text
    validate_scenes([square_board(4, 5)] * 3, load_scenes(out))


def test_cli_infeasible_exits_1(tmp_path, capsys):
    roles = tmp_path / "roles.txt"
    roles.write_text(f"{MAP_A}\n{MAP_B}\n{MAP_C}")
    spec = tmp_path / "spec.json"
    spec.write_text('{"roles": {"petal": {"classes": ["GD"]}, "sea": {"classes": ["TE"]}, '
                    '"sky": {"classes": ["BL"]}}, "target_counts": {"GD": 1, "TE": 1, "BL": 18}}')
    code = main(["roles-to-scenes", str(roles), "--spec", str(spec), "--out", str(tmp_path / "x.txt")])
    assert code == 1
    assert "no common histogram" in capsys.readouterr().err
