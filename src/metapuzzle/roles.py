"""Role maps: author each scene as a grid of roles and let a solver pick the concrete classes.

A roles file has the scene file layout (three grids, blank line between them, '#' comments),
with role names as tokens. A roles spec (JSON) lists, per role, the classes it may take and
optional preference weights, plus optional ``fixed`` counts (a required total per class) and
``target_counts`` (the whole histogram). Without target_counts the solver chooses a histogram
that all three maps can realise.

``assign_classes`` returns three class maps that pass ``scene.validate_scenes``: identical class
histograms and, with rotation "none", identical class counts per border side and the same class
at each corner (the strict border rule). With rotation "quarter" the edges and the corners are
pooled, as the engine does.

Method. Cells are grouped as the border rule sees them: one group per side and per corner
(rotation none) or one edge pool and one corner pool (quarter), plus the interior. A skeleton
gives every group a class multiset, the same in all three maps, so the skeleton fixes the
histogram and the border counts. It is searched first by simulated annealing on a violation
count: for each map and group, every set of roles needs enough cells among its allowed classes,
and the fixed or target counts must hold. Max-flow then gives each map a class map for the
skeleton, and a second annealing swaps classes inside a group, which keeps the groups and the
histogram exact. The objective is the same-position overlap summed over all pairs, plus a
weighted preference term (weights) and an optional penalty for identical neighbours.

Limits: the histogram search is a heuristic. The exact checks in ``_goal`` prove some inputs
infeasible, and their errors name the roles and classes. Otherwise a failed search reports the
closest violations it found within ``iters``, which does not prove that no histogram exists.
"""
from __future__ import annotations

import json
import math
import random
from collections import Counter, deque
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Mapping, Sequence

from .board import Board, square_board
from .scene import ClassMap, SceneError, load_scenes, validate_scenes

NAMES = ("A", "B", "C")
ROTATIONS = ("none", "quarter")
_SPEC_KEYS = frozenset({"roles", "fixed", "target_counts"})

Container = tuple[str, tuple[int, ...]]  # (name, slot ids) of cells the border rule compares
Constraint = tuple[frozenset, int, tuple]  # (classes, cells needed, roles), from _hall


@dataclass(frozen=True)
class RoleDef:
    """Classes a role may take, with one preference weight per class (higher is preferred)."""

    classes: tuple[str, ...]
    weights: tuple[float, ...]


@dataclass(frozen=True)
class RolesSpec:
    roles: dict[str, RoleDef]
    fixed: dict[str, int]
    target_counts: dict[str, int] | None = None

    @property
    def allowed(self) -> dict[str, tuple[str, ...]]:
        return {r: d.classes for r, d in self.roles.items()}

    @property
    def weights(self) -> dict[tuple[str, str], float]:
        return {(r, c): w for r, d in self.roles.items() for c, w in zip(d.classes, d.weights)}


# ---------------------------------------------------------------- input


def _label(value, what: str) -> str:
    if not isinstance(value, str) or not value or any(ch.isspace() for ch in value) or "@" in value or "#" in value:
        raise SceneError(f"bad {what} {value!r}: use a non-empty label without spaces, '@' or '#'")
    return value


def _counts(obj, what: str) -> dict[str, int]:
    if not isinstance(obj, Mapping):
        raise SceneError(f"{what} must be an object mapping class to count")
    out: dict[str, int] = {}
    for c, n in obj.items():
        _label(c, f"{what} class")
        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise SceneError(f"{what} count for {c!r} must be a non-negative integer")
        out[c] = n
    return out


def parse_roles_spec(data) -> RolesSpec:
    """Build a RolesSpec from parsed JSON. Keys starting with '_' are ignored (comments)."""
    if not isinstance(data, Mapping):
        raise SceneError("roles spec must be a JSON object")
    unknown = [str(k) for k in data if k not in _SPEC_KEYS and not str(k).startswith("_")]
    if unknown:
        raise SceneError(f"unknown roles spec key(s): {', '.join(unknown)}")
    raw = data.get("roles")
    if not isinstance(raw, Mapping) or not raw:
        raise SceneError('roles spec needs a non-empty "roles" object')
    roles: dict[str, RoleDef] = {}
    for name, d in raw.items():
        _label(name, "role name")
        if not isinstance(d, Mapping) or not isinstance(d.get("classes"), list) or not d["classes"]:
            raise SceneError(f'role {name!r} needs a non-empty "classes" list')
        classes = tuple(_label(c, f"class of role {name!r}") for c in d["classes"])
        if len(set(classes)) != len(classes):
            raise SceneError(f"role {name!r} lists a class twice")
        weights = d.get("weights", [1] * len(classes))
        if (
            not isinstance(weights, list)
            or len(weights) != len(classes)
            or any(isinstance(w, bool) or not isinstance(w, (int, float)) or w <= 0 for w in weights)
        ):
            raise SceneError(f"role {name!r}: weights must be one positive number per class")
        roles[name] = RoleDef(classes, tuple(float(w) for w in weights))
    allowed = {c for d in roles.values() for c in d.classes}
    fixed = _counts(data.get("fixed", {}), "fixed")
    target = data.get("target_counts")
    target = None if target is None else _counts(target, "target_counts")
    for what, counts in (("fixed", fixed), ("target_counts", target or {})):
        for c in counts:
            if c not in allowed:
                raise SceneError(f"{what} class {c!r} is not allowed by any role")
    if target is not None:
        for c, n in fixed.items():
            if target.get(c, 0) != n:
                raise SceneError(f"fixed {c!r}={n} contradicts target_counts {c!r}={target.get(c, 0)}")
    return RolesSpec(roles, fixed, target)


def load_roles_spec(path) -> RolesSpec:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SceneError(f"bad roles spec {path}: {e}") from e
    return parse_roles_spec(data)


def load_role_maps(path) -> list[ClassMap]:
    """Three role grids in a text or JSON file, laid out like a scene file."""
    return load_scenes(path)


def write_scene_file(maps: Sequence[ClassMap], path) -> None:
    """Write three class maps as a scene text file (readable by scene.load_scenes)."""
    if len(maps) != 3:
        raise SceneError(f"expected 3 class maps, got {len(maps)}")
    blocks = [f"# {NAMES[k]}\n" + "\n".join(" ".join(row) for row in m.tokens()) + "\n" for k, m in enumerate(maps)]
    Path(path).write_text("\n".join(blocks), encoding="utf-8")


def _grids(role_maps) -> list[list[list[str]]]:
    maps = list(role_maps)
    if len(maps) != 3:
        raise SceneError(f"expected 3 role maps, got {len(maps)}")
    grids = [[list(r) for r in (m.cls if isinstance(m, ClassMap) else m)] for m in maps]
    for k, g in enumerate(grids):
        if not g or not g[0] or len({len(r) for r in g}) != 1:
            raise SceneError(f"role map {NAMES[k]} is empty or has rows of different lengths")
    shape = (len(grids[0]), len(grids[0][0]))
    for k, g in enumerate(grids):
        if (len(g), len(g[0])) != shape:
            raise SceneError(
                f"role map {NAMES[k]} is {len(g[0])}x{len(g)} (cols x rows) but map A is {shape[1]}x{shape[0]}"
            )
    return grids


# ---------------------------------------------------------------- counting


def _containers(board: Board, rotation: str) -> list[Container]:
    """Groups the border rule compares, plus the interior. Slot ids are row-major."""
    keys: dict[str, list[int]] = {}
    for s in board.slots:
        if s.kind == "interior":
            key = "interior"
        elif rotation == "none":
            key = f"{s.kind} {s.home}"
        else:
            key = s.kind
        keys.setdefault(key, []).append(s.id)
    return [(k, tuple(v)) for k, v in keys.items()]


def _hall(counts: Mapping[str, int], allowed: Mapping[str, tuple[str, ...]]) -> list[Constraint]:
    """Constraints a class histogram must meet to take cells with these role counts.

    A histogram N can label the cells (role counts) iff for every set A of roles the classes
    allowed to A hold at least sum(counts[r] for r in A) cells of N (Hall's condition for the
    bipartite supply/demand problem). One constraint is kept per class set, the strongest one.
    """
    roles = sorted(r for r, n in counts.items() if n > 0)
    best: dict[frozenset, tuple[int, tuple]] = {}
    for size in range(1, len(roles) + 1):
        for sub in combinations(roles, size):
            cs = frozenset(c for r in sub for c in allowed[r])
            need = sum(counts[r] for r in sub)
            if cs not in best or need > best[cs][0]:
                best[cs] = (need, sub)
    return [(cs, need, sub) for cs, (need, sub) in best.items()]


def _deficit(hist: Mapping[str, int], cons: Sequence[tuple]) -> int:
    """Cells missing from the histogram over all constraints (0 when all hold)."""
    return sum(max(0, need - sum(hist.get(c, 0) for c in cs)) for _, cs, need, _ in cons)


def _transport(supply: Mapping[str, int], demand: Mapping[str, int], allowed) -> dict[tuple[str, str], int] | None:
    """Max flow from role counts to class counts. Returns the flow per (role, class), or None."""
    total = sum(supply.values())
    if total != sum(demand.values()):
        return None
    cap: dict = {}

    def add(u, v, c) -> None:
        cap.setdefault(u, {})[v] = cap.get(u, {}).get(v, 0) + c
        cap.setdefault(v, {}).setdefault(u, 0)

    for r, n in supply.items():
        if n <= 0:
            continue
        add("S", ("r", r), n)
        for c in allowed[r]:
            if demand.get(c, 0) > 0:
                add(("r", r), ("c", c), total)
    for c, n in demand.items():
        if n > 0:
            add(("c", c), "T", n)
    flow = 0
    while True:  # Edmonds-Karp on a graph with a handful of nodes
        parent: dict = {"S": None}
        queue = deque(["S"])
        while queue and "T" not in parent:
            u = queue.popleft()
            for v, res in cap.get(u, {}).items():
                if res > 0 and v not in parent:
                    parent[v] = u
                    queue.append(v)
        if "T" not in parent:
            break
        path = []
        v = "T"
        while parent[v] is not None:
            path.append((parent[v], v))
            v = parent[v]
        push = min(cap[u][v] for u, v in path)
        for u, v in path:
            cap[u][v] -= push
            cap[v][u] += push
        flow += push
    if flow != total:
        return None
    out: dict[tuple[str, str], int] = {}
    for r, n in supply.items():
        for c in (allowed[r] if n > 0 else ()):
            f = cap.get(("c", c), {}).get(("r", r), 0)  # reverse residual = flow on (r, c)
            if f:
                out[(r, c)] = f
    return out


def _goal(spec: RolesSpec, all_classes: Sequence[str], cells: int, flat, allowed) -> dict[str, int]:
    """Histogram constraints as {class: count}: the exact target, or the fixed counts.

    Also checks the necessary conditions that need no search, and raises with the roles and
    classes involved when one fails.
    """
    if sum(spec.fixed.values()) > cells:
        raise SceneError(f"fixed counts sum to {sum(spec.fixed.values())}, more than the {cells} cells")
    if spec.target_counts is not None:
        target = {c: spec.target_counts.get(c, 0) for c in all_classes}
        if sum(target.values()) != cells:
            raise SceneError(f"target_counts sum to {sum(target.values())} but the maps have {cells} cells")
        problems = []
        for k, cells_k in enumerate(flat):
            for cs, need, sub in _hall(Counter(cells_k), allowed):
                have = sum(target[c] for c in cs)
                if need > have:
                    problems.append(
                        f"map {NAMES[k]}: roles {', '.join(sub)} need {need} cells from classes "
                        f"{', '.join(sorted(cs))}, target_counts gives them {have}"
                    )
        if problems:
            raise SceneError("no common histogram: " + "; ".join(problems))
        return target
    for c, n in spec.fixed.items():
        for k, cells_k in enumerate(flat):
            if n and not any(c in allowed[r] for r in set(cells_k)):
                raise SceneError(
                    f"no common histogram: fixed class {c!r} needs {n} cells, but no role in map {NAMES[k]} allows it"
                )
    return dict(spec.fixed)


# ---------------------------------------------------------------- search


def _accept(delta: float, temp: float, rng: random.Random) -> bool:
    return delta <= 0 or rng.random() < math.exp(-delta / temp)


def _skeleton_failure(containers, cons, M, N, goal, iters: int) -> str:
    worst = []
    for g, cl in enumerate(cons):
        for k, cs, need, sub in cl:
            have = sum(M[g].get(c, 0) for c in cs)
            if need > have:
                worst.append((need - have, (
                    f"roles {', '.join(sub)} of map {NAMES[k]} need {need} cells from classes "
                    f"{', '.join(sorted(cs))} in {containers[g][0]}; the histogram gives them {have}"
                )))
    worst.sort(key=lambda t: -t[0])
    parts = [text for _, text in worst[:3]]
    parts += [f"class {c!r} is {N[c]} in the histogram, required {goal[c]}" for c in sorted(goal) if N[c] != goal[c]]
    return f"no common histogram found in {iters} iterations: " + ("; ".join(parts) or "unknown cause")


def _find_skeleton(containers, gcounts, allowed, weights, goal, all_classes, cont_of, rng, iters) -> list[Counter]:
    """Per container, a class multiset that every map's role counts can take (annealed)."""
    G = len(containers)
    cons = [
        [(k, cs, need, sub) for k in range(3) for cs, need, sub in _hall(gcounts[k][g], allowed)]
        for g in range(G)
    ]
    # Greedy start: map A's role counts, each cell to the allowed class with the lowest count per weight.
    M: list[Counter] = []
    for g in range(G):
        m: Counter = Counter()
        for r, n in sorted(gcounts[0][g].items()):
            for _ in range(n):
                c = min(allowed[r], key=lambda x: (m[x] / weights[(r, x)], x))
                m[c] += 1
        M.append(m)
    N: Counter = Counter()
    for m in M:
        N.update(m)

    def pen(c: str, n: int) -> int:
        return abs(n - goal[c]) if c in goal else 0

    defi = [_deficit(M[g], cons[g]) for g in range(G)]
    fixed_cost = sum(pen(c, N[c]) for c in goal)
    cost = sum(defi) + fixed_cost
    T = len(cont_of)
    for it in range(iters):
        if cost == 0:
            break
        temp = 2.0 * (0.05 / 2.0) ** (it / max(1, iters - 1))
        if G > 1 and rng.random() < 0.4:
            # Exchange: class c leaves container g for d, and d leaves h for c. Histogram unchanged.
            g, h = rng.sample(range(G), 2)
            c = rng.choice([x for x, n in M[g].items() if n > 0])
            d = rng.choice([x for x, n in M[h].items() if n > 0])
            if c == d:
                continue
            ng = Counter(M[g])
            ng[c] -= 1
            ng[d] += 1
            nh = Counter(M[h])
            nh[d] -= 1
            nh[c] += 1
            dg = _deficit(ng, cons[g]) - defi[g]
            dh = _deficit(nh, cons[h]) - defi[h]
            if _accept(dg + dh, temp, rng):
                M[g], M[h] = ng, nh
                defi[g] += dg
                defi[h] += dh
        else:
            # Replace: one cell of container g (drawn by size) changes class c to d.
            g = cont_of[rng.randrange(T)]
            c = rng.choice([x for x, n in M[g].items() if n > 0])
            d = rng.choice(all_classes)
            if c == d:
                continue
            ng = Counter(M[g])
            ng[c] -= 1
            ng[d] += 1
            dg = _deficit(ng, cons[g]) - defi[g]
            dfix = pen(c, N[c] - 1) - pen(c, N[c]) + pen(d, N[d] + 1) - pen(d, N[d])
            if _accept(dg + dfix, temp, rng):
                M[g] = ng
                N[c] -= 1
                N[d] += 1
                defi[g] += dg
                fixed_cost += dfix
        cost = sum(defi) + fixed_cost
    if cost:
        raise SceneError(_skeleton_failure(containers, cons, M, N, goal, iters))
    return M


def _initial_arrangement(containers, flat, M, allowed) -> list[list[str]]:
    """Per map, a class per cell that meets every container's multiset (max-flow per container)."""
    out = []
    for k in range(3):
        cls: list = [None] * len(flat[k])
        for g, (name, cells) in enumerate(containers):
            supply = Counter(flat[k][p] for p in cells)
            flow = _transport(supply, M[g], allowed)
            if flow is None:
                raise SceneError(f"internal: skeleton of {name!r} does not fit map {NAMES[k]}")
            pools: dict[str, list[str]] = {r: [] for r in supply}
            for (r, c), f in flow.items():
                pools[r].extend([c] * f)
            for p in cells:
                cls[p] = pools[flat[k][p]].pop()
        out.append(cls)
    return out


def _arrange(cls0, flat, containers, allowed, weights, board, rng, iters, pref_weight, max_same, adj_weight):
    """Anneal class swaps inside containers. Every swap keeps each container's histogram."""
    T = len(cls0[0])
    cls = [list(r) for r in cls0]
    cont_of = [0] * T
    for g, (_, cells) in enumerate(containers):
        for p in cells:
            cont_of[p] = g
    wmax = {r: max(weights[(r, c)] for c in allowed[r]) for r in allowed}

    def pref(k: int, p: int) -> float:
        r = flat[k][p]
        return 1.0 - weights[(r, cls[k][p])] / wmax[r]

    nbrs = [s.neighbors for s in board.slots]
    edges = board.adjacencies
    limit = None if max_same is None else max_same * board.n_adjacencies
    eq = sum(cls[a][p] == cls[b][p] for a, b in combinations(range(3), 2) for p in range(T))
    pref_total = sum(pref(k, p) for k in range(3) for p in range(T))
    same = [sum(row[a] == row[b] for a, b in edges) for row in cls]

    def cost() -> float:
        c = eq + pref_weight * pref_total
        if limit is not None:
            c += adj_weight * sum(max(0.0, s - limit) for s in same)
        return c

    def swap(k: int, p: int, q: int) -> None:
        nonlocal eq, pref_total
        row = cls[k]
        others = [cls[m] for m in range(3) if m != k]
        touched = {(min(p, n), max(p, n)) for n in nbrs[p]} | {(min(q, n), max(q, n)) for n in nbrs[q]}

        def local() -> tuple[int, int, float]:
            e = sum(o[x] == row[x] for o in others for x in (p, q))
            s = sum(row[a] == row[b] for a, b in touched)
            return e, s, pref(k, p) + pref(k, q)

        e0, s0, f0 = local()
        row[p], row[q] = row[q], row[p]
        e1, s1, f1 = local()
        eq += e1 - e0
        pref_total += f1 - f0
        same[k] += s1 - s0

    cur = cost()
    best, best_cls = cur, [list(r) for r in cls]
    for it in range(iters):
        temp = 1.0 * (0.01 ** (it / max(1, iters - 1)))
        k = rng.randrange(3)
        p = rng.randrange(T)
        q = rng.choice(containers[cont_of[p]][1])
        if q == p or cls[k][q] == cls[k][p]:
            continue
        if cls[k][q] not in allowed[flat[k][p]] or cls[k][p] not in allowed[flat[k][q]]:
            continue
        swap(k, p, q)
        new = cost()
        if _accept(new - cur, temp, rng):
            cur = new
            if cur < best:
                best, best_cls = cur, [list(r) for r in cls]
        else:
            swap(k, p, q)
    return best_cls, best


# ---------------------------------------------------------------- API


def assign_classes(
    role_maps,
    roles_spec,
    *,
    rotation: str = "none",
    seed: int = 0,
    iters: int = 20000,
    restarts: int = 1,
    pref_weight: float = 0.25,
    max_same_neighbour: float | None = None,
    adjacency_weight: float = 1.0,
) -> list[ClassMap]:
    """Solve three role maps into three class maps that pass ``validate_scenes``.

    role_maps: three ClassMaps (or grids of role names) of equal shape, in map order A, B, C.
    roles_spec: a RolesSpec or the parsed JSON dict (see module docstring).
    rotation: "none" (per-side border counts, corners fixed per slot) or "quarter" (pooled).
    iters: annealing iterations for each of the two phases. With 0, the greedy start is returned.
    restarts: runs with seeds seed, seed+1, ...; the run with the lowest objective is kept. The
        skeleton draw dominates the result, so a few restarts usually lower the overlap noticeably.
    pref_weight: weight of the role-weight preference term (0 disables it).
    max_same_neighbour: if set, penalise a map whose share of identical adjacent pairs exceeds it.

    Raises SceneError when the inputs are inconsistent or no common histogram is found, and
    ValueError for an unknown rotation.
    """
    if rotation not in ROTATIONS:
        raise ValueError(f"rotation must be one of {ROTATIONS}")
    spec = roles_spec if isinstance(roles_spec, RolesSpec) else parse_roles_spec(roles_spec)
    grids = _grids(role_maps)
    rows, cols = len(grids[0]), len(grids[0][0])
    board = square_board(cols, rows, "standard", rotation)
    T = board.n_slots
    allowed = spec.allowed
    weights = spec.weights
    flat = [[r for row in g for r in row] for g in grids]
    for k in range(3):
        for r in sorted(set(flat[k])):
            if r not in allowed:
                raise SceneError(f"map {NAMES[k]} uses role {r!r}, which the roles spec does not define")
    all_classes = sorted({c for d in spec.roles.values() for c in d.classes})
    goal = _goal(spec, all_classes, T, flat, allowed)
    containers = _containers(board, rotation)
    cont_of = [0] * T
    for g, (_, cells) in enumerate(containers):
        for p in cells:
            cont_of[p] = g
    gcounts = [[Counter(flat[k][p] for p in cells) for _, cells in containers] for k in range(3)]
    best: tuple[float, list] | None = None
    first_error: SceneError | None = None
    for r in range(max(1, restarts)):
        rng = random.Random(seed + r)
        try:
            M = _find_skeleton(containers, gcounts, allowed, weights, goal, all_classes, cont_of, rng, iters)
        except SceneError as e:
            first_error = first_error or e
            continue
        cls0 = _initial_arrangement(containers, flat, M, allowed)
        cls, value = _arrange(cls0, flat, containers, allowed, weights, board, rng, iters, pref_weight,
                              max_same_neighbour, adjacency_weight)
        if best is None or value < best[0]:
            best = (value, cls)
    if best is None:
        raise first_error
    cls = best[1]
    maps = [
        ClassMap([row[y * cols:(y + 1) * cols] for y in range(rows)], [[0] * cols for _ in range(rows)])
        for row in cls
    ]
    validate_scenes([board] * 3, maps)  # self-check against the scene rules
    return maps
