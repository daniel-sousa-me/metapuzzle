"""Simulated-annealing solver for three low-overlap arrangements.

Energy = shared adjacencies (summed over the pairs AB, AC, BC)
       + cluster_weight * cluster penalty (sizes of shared components with 3+ pieces)
       + mismatch_weight * side mismatches (touching sides that do not mate, per solution).
A returned solution is "valid" when mismatches == 0. Moves keep every piece on a slot it
fits at slot level (boundary sides flat on a standard board, class map, forced rotation);
pairwise side mating is handled through the mismatch term.
"""
from __future__ import annotations

import itertools
import json
import math
import random
import time
from dataclasses import dataclass, field
from pathlib import Path

from .board import PROFILES, SIDE_DELTA, Board, mates, square_board
from .metrics import PAIR_INDEX, PAIR_NAMES, cluster_penalty, corner_order, shared_adjacencies
from .pieces import Piece, piece_from_dict, piece_to_dict, rotations_for_piece
from .scene import ClassMap, validate_scenes

DEFAULT_ITERS = 300_000
FLAT = PROFILES.index("flat")


@dataclass
class Solution:
    """Three placements (A, B, C) with their boards, the inventory, and run metadata."""

    boards: list[Board]
    pieces: list[Piece]
    placements: list[dict[int, tuple[int, int]]]
    class_maps: list[ClassMap] | None = None
    meta: dict = field(default_factory=dict)

    @property
    def board(self) -> Board:
        return self.boards[0]

    def to_dict(self) -> dict:
        return {
            "format": "metapuzzle-solution",
            "version": 1,
            "boards": [b.params() for b in self.boards],
            "pieces": [piece_to_dict(p) for p in self.pieces],
            "placements": [{str(p): [s, r] for p, (s, r) in sorted(pl.items())} for pl in self.placements],
            "class_maps": [m.tokens() for m in self.class_maps] if self.class_maps else None,
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Solution":
        if d.get("format") != "metapuzzle-solution":
            raise ValueError("not a metapuzzle solution file")
        params = d["boards"] if "boards" in d else [d["board"]] * 3
        boards = [square_board(**p) for p in params]
        pls = [{int(p): (int(v[0]), int(v[1])) for p, v in pl.items()} for pl in d["placements"]]
        maps = [ClassMap.from_tokens(g) for g in d["class_maps"]] if d.get("class_maps") else None
        return cls(boards, [piece_from_dict(p) for p in d["pieces"]], pls, maps, dict(d.get("meta", {})))

    def save(self, path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), separators=(",", ":")))

    @classmethod
    def load(cls, path) -> "Solution":
        return cls.from_dict(json.loads(Path(path).read_text()))


def _three_boards(boards) -> list[Board]:
    bl = [boards] * 3 if isinstance(boards, Board) else list(boards)
    if len(bl) != 3:
        raise ValueError("need one board or exactly three boards")
    if len({b.n_slots for b in bl}) != 1:
        raise ValueError("all three boards must have the same number of slots")
    return bl


def validate_solution(sol: Solution) -> list[str]:
    """Return a list of problems; an empty list means the solution is valid."""
    errs: list[str] = []
    if len(sol.placements) != 3 or len(sol.boards) != 3:
        return ["need exactly three boards and three placements"]
    by_id = {p.piece_id: p for p in sol.pieces}
    if len(by_id) != len(sol.pieces):
        errs.append("duplicate piece ids")
    for k, (pl, b) in enumerate(zip(sol.placements, sol.boards)):
        name = "ABC"[k]
        if set(pl) != set(by_id):
            errs.append(f"{name}: placed pieces differ from inventory")
            continue
        slots = [s for s, _ in pl.values()]
        if sorted(slots) != list(range(b.n_slots)):
            errs.append(f"{name}: placement is not a bijection onto the slots")
            continue
        at = {s: pid for pid, (s, _) in pl.items()}
        cm = sol.class_maps[k] if sol.class_maps else None
        for pid, (s, r) in pl.items():
            sl = b.slots[s]
            piece = by_id[pid]
            forced = None
            if cm:
                if piece.cls != cm.cls[sl.y][sl.x]:
                    errs.append(f"{name}: piece {pid} class {piece.cls} on cell of class {cm.cls[sl.y][sl.x]}")
                forced = cm.rot[sl.y][sl.x] or None
            if r not in rotations_for_piece(b, piece, s, forced):
                errs.append(f"{name}: piece {pid} cannot sit in slot {s} at rotation {r}")
        for s, sl in enumerate(b.slots):
            for d, (dx, dy) in enumerate(SIDE_DELTA):
                x, y = sl.x + dx, sl.y + dy
                if not (0 <= x < b.cols and 0 <= y < b.rows) or b.slot_at(x, y) < s:
                    continue
                a, c = at[s], at[b.slot_at(x, y)]
                pa, pc = by_id[a], by_id[c]
                qa, qc = pl[a][1] // 90, pl[c][1] // 90
                if not mates(pa.sides[(d - qa) % 4], pc.sides[(d + 2 - qc) % 4]):
                    errs.append(f"{name}: pieces {a} and {c} touch with sides that do not mate")
    if sol.meta.get("distinct_corner_orders") and not errs:
        orders = [corner_order(pl, b) for pl, b in zip(sol.placements, sol.boards)]
        if len(set(orders)) != 3:
            errs.append(f"corner orders are not pairwise distinct: {orders}")
    return errs


def _components_cost(edges) -> int:
    return cluster_penalty(edges) if len(edges) >= 2 else 0


def solve(
    boards,
    pieces: list[Piece],
    class_maps: list[ClassMap] | None = None,
    seed: int = 0,
    iters: int | None = None,
    cluster_weight: float = 0.25,
    mismatch_weight: float = 1.5,
    distinct_corner_orders: bool = False,
) -> Solution:
    """Find three placements minimizing shared adjacencies.

    boards: one Board (used for all three solutions) or three Boards with equal slot
    counts (different aspect ratios allowed). Deterministic given `seed`.
    """
    t_start = time.perf_counter()
    bl = _three_boards(boards)
    n = bl[0].n_slots
    if len(pieces) != n:
        raise ValueError(f"{len(pieces)} pieces for boards of {n} slots")
    if len({p.piece_id for p in pieces}) != n:
        raise ValueError("duplicate piece ids")
    if class_maps is not None:
        validate_scenes(bl, class_maps, strict_border=False)
        if sorted(p.cls for p in pieces) != sorted(c for c in class_maps[0].histogram().elements()):
            raise ValueError("piece classes do not match the class maps")
    iters = DEFAULT_ITERS if iters is None else iters
    rng = random.Random(seed)
    rand = rng.random
    randrange = rng.randrange

    # ---- piece types, profile codes, side compatibility ------------------------------
    sig_ids: dict[tuple, int] = {}
    ptype = []
    type_piece: list[Piece] = []
    for p in pieces:
        key = (p.sides, p.allowed_rotations, p.cls if class_maps else "")
        if key not in sig_ids:
            sig_ids[key] = len(sig_ids)
            type_piece.append(p)
        ptype.append(sig_ids[key])
    nt = len(sig_ids)
    mate_m = [[mates(a, b) for b in PROFILES] for a in PROFILES]
    sc = [[PROFILES.index(s) for s in p.sides] for p in pieces]
    tcodes = [[PROFILES.index(s) for s in p.sides] for p in type_piece]
    always = [[True] * nt for _ in range(nt)]
    for a in range(nt):
        for b in range(nt):
            ra = [r // 90 for r in type_piece[a].allowed_rotations]
            rb = [r // 90 for r in type_piece[b].allowed_rotations]
            always[a][b] = all(
                mate_m[tcodes[a][(d - qa) & 3]][tcodes[b][(d + 2 - qb) & 3]] for qa in ra for qb in rb for d in range(4)
            )
    risky_t = [not all(always[a][b] and always[b][a] for b in range(nt)) for a in range(nt)]
    risky_p = [risky_t[t] for t in ptype]
    risky_list = [i for i in range(n) if risky_p[i]]
    multi_rot = any(len(p.allowed_rotations) > 1 for p in pieces)
    # pieces able to present a flat side toward board direction d (for seam moves)
    flat_helpers = [
        [i for i in risky_list if any(sc[i][(d - r // 90) & 3] == FLAT for r in pieces[i].allowed_rotations)]
        for d in range(4)
    ]

    # ---- per-solution geometry and slot-level options ---------------------------------
    X = [[s.x for s in b.slots] for b in bl]
    Y = [[s.y for s in b.slots] for b in bl]
    nbrs = [[s.neighbors for s in b.slots] for b in bl]
    nbd = []
    for b in bl:
        rows = []
        for s in b.slots:
            row = []
            for d, (dx, dy) in enumerate(SIDE_DELTA):
                x, y = s.x + dx, s.y + dy
                if 0 <= x < b.cols and 0 <= y < b.rows:
                    row.append((d, b.slot_at(x, y)))
            rows.append(tuple(row))
        nbd.append(rows)
    memo: dict[tuple, tuple[int, ...]] = {}
    OPT: list[list[list[tuple[int, ...]]]] = []
    for k, b in enumerate(bl):
        per_t = []
        for t in range(nt):
            tp = type_piece[t]
            row = []
            for s in b.slots:
                cell_cls, forced = None, None
                if class_maps:
                    cell_cls = class_maps[k].cls[s.y][s.x]
                    forced = class_maps[k].rot[s.y][s.x] or None
                if cell_cls is not None and cell_cls != tp.cls:
                    row.append(())
                    continue
                mk = (t, s.boundary_sides, forced)
                if mk not in memo:
                    memo[mk] = tuple(r // 90 for r in rotations_for_piece(b, tp, s.id, forced))
                row.append(memo[mk])
            per_t.append(row)
        OPT.append(per_t)
    CAND = [[[s for s in range(n) if OPT[k][t][s]] for t in range(nt)] for k in range(3)]
    count_t = [0] * nt
    for t in ptype:
        count_t[t] += 1
    for k in range(3):
        for t in range(nt):
            if not CAND[k][t]:
                raise ValueError(f"piece of type {type_piece[t].shape_type}/{type_piece[t].home} fits no slot of board {'ABC'[k]}")

    # ---- frozen corners (distinct corner orders) ---------------------------------------
    frozen = [set() for _ in range(3)]
    pre: list[dict[int, int]] = [{}, {}, {}]  # slot -> piece idx
    corner_slots = []
    for b in bl:
        c, r = b.cols, b.rows
        corner_slots.append([0, c - 1, r * c - 1, (r - 1) * c])
    if distinct_corner_orders:
        if bl[0].border != "standard":
            raise ValueError("distinct_corner_orders needs a standard border")
        cps = sorted(i for i in range(n) if all(OPT[k][ptype[i]][s] for k in range(3) for s in corner_slots[k]))
        if len(cps) != 4:
            raise ValueError(
                f"distinct_corner_orders needs exactly 4 pieces that fit every corner; found {len(cps)} (use free corners)"
            )
        perms = list(itertools.permutations(cps[1:]))
        rng.shuffle(perms)
        used = 0
        for k in range(3):
            for perm in perms:
                order = [cps[0], *perm]
                if all(OPT[k][ptype[pc]][s] for pc, s in zip(order, corner_slots[k])):
                    perms.remove(perm)
                    break
            else:
                raise ValueError("no corner order fits the class maps")
            for pc, s in zip(order, corner_slots[k]):
                pre[k][s] = pc
                frozen[k].add(s)
            used += 1

    # ---- initial placement -------------------------------------------------------------
    def init_state(k: int):
        for _attempt in range(40):
            pools = [[] for _ in range(nt)]
            taken = set(pre[k].values())
            for i in range(n):
                if i not in taken:
                    pools[ptype[i]].append(i)
            for pool in pools:
                rng.shuffle(pool)
            at = [-1] * n
            pos = [0] * n
            rot = [0] * n
            for s, pc in pre[k].items():
                at[s] = pc
                pos[pc] = s
                rot[pc] = OPT[k][ptype[pc]][s][0]
            free = [s for s in range(n) if at[s] < 0]
            cnt = {s: sum(count_t[t] for t in range(nt) if OPT[k][t][s]) for s in free}
            rng.shuffle(free)
            free.sort(key=lambda s: cnt[s])
            ok = True
            for s in free:
                avail = [t for t in range(nt) if pools[t] and OPT[k][t][s]]
                if not avail:
                    ok = False
                    break
                tot = sum(len(pools[t]) for t in avail)
                r_ = randrange(tot)
                for t in avail:
                    if r_ < len(pools[t]):
                        break
                    r_ -= len(pools[t])
                pc = pools[t].pop()
                at[s] = pc
                pos[pc] = s
                opts = OPT[k][t][s]
                rot[pc] = opts[randrange(len(opts))]
            if ok:
                return at, pos, rot
        raise ValueError(f"could not build a valid initial placement for solution {'ABC'[k]}")

    at, pos, rot = [], [], []
    for k in range(3):
        a_, p_, r_ = init_state(k)
        at.append(a_)
        pos.append(p_)
        rot.append(r_)

    # ---- bookkeeping -------------------------------------------------------------------
    oth = [[(l, pi) for pi, (i, j) in enumerate(PAIR_INDEX) for l in ((j,) if i == k else (i,) if j == k else ())] for k in range(3)]

    def edges_of(k: int) -> set:
        out = set()
        for s in range(n):
            for t in nbrs[k][s]:
                if s < t:
                    a, b = at[k][s], at[k][t]
                    out.add((a, b) if a < b else (b, a))
        return out

    E_sol = [edges_of(k) for k in range(3)]
    S = [E_sol[i] & E_sol[j] for i, j in PAIR_INDEX]
    cc = [_components_cost(s) for s in S]
    prim = sum(len(s) for s in S)
    clu = sum(cc)

    def mism_slot(k: int, s: int, skip: int) -> int:
        a = at[k][s]
        qa = rot[k][a]
        ra = risky_p[a]
        ca = sc[a]
        c = 0
        atk, rk = at[k], rot[k]
        for d, t in nbd[k][s]:
            if t == skip:
                continue
            b = atk[t]
            if (ra or risky_p[b]) and not mate_m[ca[(d - qa) & 3]][sc[b][(d + 2 - rk[b]) & 3]]:
                c += 1
        return c

    def total_mism() -> int:
        m = 0
        for k in range(3):
            for s in range(n):
                for d, t in nbd[k][s]:
                    if s < t:
                        a, b = at[k][s], at[k][t]
                        if not mate_m[sc[a][(d - rot[k][a]) & 3]][sc[b][(d + 2 - rot[k][b]) & 3]]:
                            m += 1
        return m

    M = total_mism()

    def pick_rot(k: int, p: int, s: int) -> int:
        opts = OPT[k][ptype[p]][s]
        cur = rot[k][p]
        if len(opts) == 1:
            return opts[0]
        if not risky_p[p]:
            return cur if cur in opts else opts[randrange(len(opts))]
        best, best_c = [], 99
        for q in opts:
            rot[k][p] = q
            c = mism_slot(k, s, -1)
            if c < best_c:
                best, best_c = [q], c
            elif c == best_c:
                best.append(q)
        if cur in best:
            return cur
        return best[randrange(len(best))]

    def snapshot():
        return [x[:] for x in pos], [x[:] for x in rot]

    best_valid = None  # (value, snapshot)
    best_any = None  # (energy, snapshot)

    def record() -> None:
        nonlocal best_valid, best_any
        val = prim + cluster_weight * clu
        if M == 0 and (best_valid is None or val < best_valid[0]):
            best_valid = (val, snapshot())
        e = val + mismatch_weight * M
        if best_any is None or e < best_any[0]:
            best_any = (e, snapshot())

    record()
    t_hi, t_lo = 0.6, 0.05
    ratio = t_lo / t_hi
    T = t_hi
    it = 0
    exp = math.exp
    done = M == 0 and prim == 0 and clu == 0
    bad_list: list = []
    bad_pieces: set = set()
    last_scan = -999

    def scan(k: int, x: int, sl: int, excl: int, out: list) -> None:
        atk = at[k]
        for t in nbrs[k][sl]:
            if t == excl:
                continue
            r_ = atk[t]
            for l, pi in oth[k]:
                pl_ = pos[l]
                sa, sb = pl_[x], pl_[r_]
                dx = X[l][sa] - X[l][sb]
                dy = Y[l][sa] - Y[l][sb]
                if dx * dx + dy * dy == 1:
                    out.append((pi, x, r_) if x < r_ else (pi, r_, x))

    while it < iters and not done:
        it += 1
        if not (it & 127):
            T = t_hi * ratio ** (it / iters)
        r0 = rand()
        k = s = t = -1
        if multi_rot and r0 < 0.04:
            k = randrange(3)
            s = randrange(n)
            p = at[k][s]
            opts = OPT[k][ptype[p]][s]
            if len(opts) < 2 or s in frozen[k]:
                continue
            cur = rot[k][p]
            new = opts[randrange(len(opts))]
            if new == cur:
                continue
            if risky_p[p]:
                old_m = mism_slot(k, s, -1)
                rot[k][p] = new
                dm = mism_slot(k, s, -1) - old_m
                dE = mismatch_weight * dm
                if dE <= 0 or rand() < exp(-dE / T):
                    M += dm
                else:
                    rot[k][p] = cur
                    continue
            else:
                rot[k][p] = new
            continue
        if M and risky_list and r0 < 0.3:
            if it - last_scan >= 64 or not bad_list:
                last_scan = it
                bad_list = []
                bad_pieces = set()
                for k_ in range(3):
                    atk_, rk_ = at[k_], rot[k_]
                    for p_ in risky_list:
                        sp_ = pos[k_][p_]
                        for d_, t_ in nbd[k_][sp_]:
                            b_ = atk_[t_]
                            if not mate_m[sc[p_][(d_ - rk_[p_]) & 3]][sc[b_][(d_ + 2 - rk_[b_]) & 3]]:
                                bad_list.append((k_, p_, d_))
                                bad_pieces.add(p_)
                                bad_pieces.add(b_)
            if not bad_list:
                continue
            k, p, d = bad_list[randrange(len(bad_list))]
            sp = pos[k][p]
            qp = rot[k][p]
            tt = -1
            for d_, t_ in nbd[k][sp]:
                if d_ == d:
                    tt = t_
            b = at[k][tt]
            if mate_m[sc[p][(d - qp) & 3]][sc[b][(d + 2 - rot[k][b]) & 3]]:
                continue
            p_flat = sc[p][(d - qp) & 3] == FLAT
            pool = flat_helpers[(d + 2) & 3] if p_flat else flat_helpers[d]
            if rand() < 0.5:
                pool = [h for h in pool if h in bad_pieces] or pool
            if not pool:
                continue
            helper = pool[randrange(len(pool))]
            if helper == p or helper == b:
                continue
            target = tt if p_flat else sp
            s, t = pos[k][helper], target
        elif S and r0 > 0.7 and prim:
            ne = [i for i in range(3) if S[i]]
            pi = ne[randrange(len(ne))]
            e = tuple(S[pi])[randrange(len(S[pi]))]
            x = e[randrange(2)]
            k = PAIR_INDEX[pi][randrange(2)]
            s = pos[k][x]
        else:
            k = randrange(3)
            s = randrange(n)
        if t < 0:
            p = at[k][s]
            cl = CAND[k][ptype[p]]
            t = cl[randrange(len(cl))]
        if t == s or s in frozen[k] or t in frozen[k]:
            continue
        atk = at[k]
        p, q = atk[s], atk[t]
        if not OPT[k][ptype[q]][s] or not OPT[k][ptype[p]][t]:
            continue
        rem: list = []
        add: list = []
        scan(k, p, s, t, rem)
        scan(k, q, t, s, rem)
        scan(k, p, t, s, add)
        scan(k, q, s, t, add)
        dprim = len(add) - len(rem)
        dclu = 0
        new_cc = None
        if add or rem:
            new_cc = {}
            aff = {x[0] for x in rem} | {x[0] for x in add}
            for pi in aff:
                ns = set(S[pi])
                for x in rem:
                    if x[0] == pi:
                        ns.discard((x[1], x[2]))
                for x in add:
                    if x[0] == pi:
                        ns.add((x[1], x[2]))
                new_cc[pi] = (_components_cost(ns), ns)
                dclu += new_cc[pi][0] - cc[pi]
        rk = rot[k]
        dm = 0
        swapped = False
        if risky_p[p] or risky_p[q]:
            old_m = mism_slot(k, s, -1) + mism_slot(k, t, s)
            save = (rk[p], rk[q])
            atk[s], atk[t] = q, p
            pos[k][p], pos[k][q] = t, s
            rk[q] = rk[q] if rk[q] in OPT[k][ptype[q]][s] else OPT[k][ptype[q]][s][0]
            rk[p] = pick_rot(k, p, t)
            rk[q] = pick_rot(k, q, s)
            dm = mism_slot(k, s, -1) + mism_slot(k, t, s) - old_m
            swapped = True
        dE = dprim + cluster_weight * dclu + mismatch_weight * dm
        if dE <= 0 or rand() < exp(-dE / T):
            if not swapped:
                atk[s], atk[t] = q, p
                pos[k][p], pos[k][q] = t, s
                rk[p] = pick_rot(k, p, t)
                rk[q] = pick_rot(k, q, s)
            prim += dprim
            M += dm
            if new_cc:
                for pi, (c_, ns) in new_cc.items():
                    clu += c_ - cc[pi]
                    cc[pi] = c_
                    S[pi] = ns
            if M == 0:
                if prim == 0 and clu == 0:
                    record()
                    done = True
                elif best_valid is None or prim + cluster_weight * clu < best_valid[0]:
                    record()
            elif best_valid is None and prim + cluster_weight * clu + mismatch_weight * M < best_any[0]:
                record()
        elif swapped:
            atk[s], atk[t] = p, q
            pos[k][p], pos[k][q] = s, t
            rk[p], rk[q] = save

    chosen = best_valid[1] if best_valid else best_any[1]
    fpos, frot = chosen
    placements = []
    for k in range(3):
        placements.append({pieces[i].piece_id: (fpos[k][i], frot[k][i] * 90) for i in range(n)})
    shared = {}
    total_clu = 0
    for name, (i, j) in zip(PAIR_NAMES, PAIR_INDEX):
        cnt, pairs = shared_adjacencies(placements[i], placements[j], bl[i], bl[j])
        shared[name] = cnt
        total_clu += cluster_penalty(pairs)
    sol = Solution(bl, list(pieces), placements, class_maps, {})
    mism = len(validate_solution(sol))
    sol.meta = {
        "seed": seed,
        "iters": iters,
        "iters_used": it,
        "energy": sum(shared.values()) + cluster_weight * total_clu,
        "shared": shared,
        "cluster_penalty": total_clu,
        "valid": mism == 0,
        "violations": mism,
        "distinct_corner_orders": bool(distinct_corner_orders),
        "elapsed_s": round(time.perf_counter() - t_start, 3),
    }
    return sol
