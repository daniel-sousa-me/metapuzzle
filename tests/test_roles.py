import random
import time
from itertools import combinations

import pytest

from metapuzzle.board import square_board
from metapuzzle.cli import main
from metapuzzle.roles import (
    _shortfall,
    assign_classes,
    parse_roles_spec,
    write_scene_file,
)
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


def test_role_suffix_passes_through_to_scene_token():
    # Centre is interior on a 3x3 board; its role token carries @90, plain roles carry none.
    spec = {"roles": {"ring": {"classes": ["D"]}, "edge_m": {"classes": ["MD"]}}}
    grid = "ring ring ring\nring edge_m@90 ring\nring ring ring"
    maps = assign_classes(roles_maps(grid, grid, grid), spec, rotation="quarter", seed=0)
    for m in maps:
        assert m.cls[1][1] == "MD" and m.rot[1][1] == 90
        assert m.tokens()[1][1] == "MD@90"
        assert m.tokens()[0][0] == "D" and m.rot[0][0] == 0


# ---------------------------------------------------------------- feasibility check

def _brute_shortfall(supply, demand, allowed):
    """max over every set A of roles of sum(supply[A]) - sum(demand[classes allowed to A]), exponential."""
    roles = [r for r, n in supply.items() if n > 0]
    best = 0
    for size in range(len(roles) + 1):
        for sub in combinations(roles, size):
            cs = {c for r in sub for c in allowed[r]}
            best = max(best, sum(supply[r] for r in sub) - sum(demand.get(c, 0) for c in cs))
    return best


def test_shortfall_matches_hall_enumeration():
    rng = random.Random(0)
    for _ in range(300):
        classes = [f"c{i}" for i in range(rng.randint(1, 5))]
        roles = [f"r{i}" for i in range(rng.randint(1, 6))]
        allowed = {r: tuple(rng.sample(classes, rng.randint(1, len(classes)))) for r in roles}
        supply = {r: rng.randint(0, 4) for r in roles}
        demand = {c: rng.randint(0, 4) for c in classes}
        short, sub = _shortfall(supply, demand, allowed)
        assert short == _brute_shortfall(supply, demand, allowed), (supply, demand, allowed)
        if short:  # the returned roles are a violated set, with need - have equal to the shortfall
            need = sum(supply[r] for r in sub)
            have = sum(demand.get(c, 0) for c in {c for r in sub for c in allowed[r]})
            assert need - have == short


def test_thirty_roles_in_one_container_are_checked_in_polynomial_time():
    # The 6x6 interior holds 30 distinct roles. Subset enumeration would visit 2**30 sets.
    board = square_board(8, 8, rotation="quarter")
    kinds: dict[str, list[int]] = {}
    for slot in board.slots:
        kinds.setdefault(slot.kind, []).append(slot.id)
    rng = random.Random(1)
    pool = {"interior": [f"r{i:02d}" for i in range(30)] + [f"r{i:02d}" for i in range(6)],
            "edge": ["r00", "r01", "r02", "r03"] * 6,
            "corner": ["r04", "r05", "r06", "r07"]}
    for values in pool.values():
        rng.shuffle(values)
    first = [None] * 64
    for kind, ids in kinds.items():
        for p, role in zip(ids, pool[kind]):
            first[p] = role
    flats = [first]
    for _ in range(2):  # same role counts per container, placed differently
        f = list(first)
        for ids in kinds.values():
            vals = [first[p] for p in ids]
            rng.shuffle(vals)
            for p, v in zip(ids, vals):
                f[p] = v
        flats.append(f)
    maps = [[row[y * 8:(y + 1) * 8] for y in range(8)] for row in flats]
    classes = [f"K{j:02d}" for j in range(12)]
    spec = {"roles": {f"r{i:02d}": {"classes": sorted(rng.sample(classes, 3))} for i in range(30)}}
    start = time.perf_counter()
    out = assign_classes(maps, spec, rotation="quarter", seed=0, iters=2000)
    assert time.perf_counter() - start < 60
    validate_scenes([board] * 3, out)
    assert out[0].histogram() == out[1].histogram() == out[2].histogram()
