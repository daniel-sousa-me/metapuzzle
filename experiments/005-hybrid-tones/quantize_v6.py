"""Marching-tile classes for experiment 005 (v6, scenes only): diagonal runs, tips, tie rule.

Builds on quantize_v5 (merged classes, HOST = "darker", verify_edges). Three changes:

(0) Tie rule (coordinator request). When the differing neighbours tie between two tiers (2-2 for a
    dark cell touching both M and L), the LIGHTER tier is the mass. v5 resolved ties toward the darker
    tier, which made DM pieces where the cell's light neighbours showed olive against cream. Counted
    per image and reported as "tie cells" (ties) and "tie changes" (cells whose class differs from v5).

(a) Diagonal pieces, pattern g. A boundary that runs at 45 degrees is a run of cells, each one step
    right and one step down (or down-left) from the previous one, whose corner-to-corner diagonals lie
    on the boundary. Such a run is drawn as diag tiles (class <A><B>g, own tier A = base):
      candidate       a v5 c cell (two adjacent sides with the mass tier, no quarter, no approx), interior.
      orientation     the mass sides fix the rotation, as for c: sides {T,R} rot 0 (mass upper right,
                      boundary TL to BR), {R,B} rot 1 (TR to BL), {B,L} rot 2, {L,T} rot 3.
      run             consecutive candidates with the same rotation along the boundary direction:
                      (1,1) for rot 0 and 2 (TL-BR), (-1,1) for rot 1 and 3 (TR-BL). Runs of length >= 2.
      corner contacts on the base side of a run, the 8-neighbourhood gives the neighbours a quarter (v5
                      pattern i) at the corner the run touches. A diagonal passes through that corner only,
                      so those i cells become plain own tier ("cleared").
      strict check    a diag tile (and a cleared cell) keeps its change only if all four sides match the
                      neighbour's side profile (the verify_edges rule). Sides that meet a three-tier
                      junction (mixed neighbourhood) are accepted, as v5 already explains them as
                      "junction"; frame, approx and cap mismatches are never accepted. A fixed-point loop
                      reverts failing cells and runs left with one tile.
      Corner joins at run ends are not checked (verify_edges looks at sides only); run ends are reported.
    Diag tiles have T and R sides fully mass and L and B sides fully base (HALVES "g"); a straight line
    of them (a synthetic check: tier M above-right of the diagonal) keeps every tile with no reverts.

(b) Tips, pattern t. A cell with three mass sides and its base tier on the fourth side (v5 pattern p,
    "cap") is a one-cell protrusion of its own tier into the mass. Its own tier is the darker one under
    HOST = "darker", so the base pokes into the lighter mass. The protrusion gets a tip: the base rises
    to a peak at the middle (march_mask "tip"), which reads as a point rather than a dent. Rule: p with
    the own tier darker than the mass becomes t (same rotation); p with own lighter stays cap (p). Under
    HOST = "darker" every p is the first case, so caps are expected to be 0. Sides are unchanged (tip,
    cap and straight share the straight side profile), so verify_edges is unaffected.

(c) Bump and notch, b and n. Not applied (0 cells). A bump or notch bulges a straight by at most
    amplitude 0.3 of the cell, and both ends stay at the side midpoints. A one-row step of the boundary
    needs a vertical offset of a full cell between two neighbours, which one straight cannot give. The
    classes exist in classes-v7.json (and the ink set) and are validated, but no map uses them.

Outputs (in this folder):
  quantized-codes-v6.txt   three merged class maps (tokens), read by make_roles_v6.py
  boundary-budgets-v6.txt  per pair: classes, per-class max, surplus per image
  stdout is saved as quantize-report-v6.txt.
"""
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import quantize as q  # noqa: E402
import quantize_v4 as v4  # noqa: E402
import quantize_v5 as v5  # noqa: E402

TIER = v4.TIER
NAMES = q.NAMES
ROWS, COLS = q.ROWS, q.COLS
SIDE_OFF = v4.SIDE_OFF            # (dx, dy) for T, R, B, L
CORNER_OFF = v4.CORNER_OFF        # TL, TR, BR, BL
ORDER = v5.ORDER
PAIRS = v5.PAIRS
APPROX_ORDER = v5.APPROX_ORDER

# Diagonal run step (dx, dy) for each rotation: TL-BR for rot 0 and 2, TR-BL for rot 1 and 3.
DIAG_STEP = {0: (1, 1), 1: (-1, 1), 2: (1, 1), 3: (-1, 1)}
# Accept a diag side that meets a three-tier junction (v5 "junction" category). False = strict.
JUNCTION_OK = True
# Side profiles, T R B L, two halves each (clockwise). "g": mass on T and R, base on B and L.
HALVES = dict(v5.HALVES)
HALVES["g"] = [("m", "m"), ("m", "m"), ("b", "b"), ("b", "b")]
HALVES["t"] = v5.HALVES["s"]   # tip: straight profile (path from left and right midpoints)
HALVES["b"] = v5.HALVES["s"]   # bump: same endpoints as a straight
HALVES["n"] = v5.HALVES["s"]   # notch: same endpoints as a straight


def classify(tiers, tone, r: int, c: int):
    """v5.classify with the tie rule: returns (v4 cell, tie flag, changed-from-v5 flag).

    Counted neighbours are lighter than the cell (HOST = "darker"). The mass tier is the most
    frequent counted tier; a tie between tiers goes to the lighter one (v6). v5 used the darker one.
    """
    own = int(tiers[r, c])
    plain = v4.Cell(TIER[own], TIER[own], "plain", None, False)
    if q.FRAME[r, c]:
        return plain, False, False

    def at(dx: int, dy: int):
        rr, cc = r + dy, c + dx
        if 0 <= rr < ROWS and 0 <= cc < COLS:
            return int(tiers[rr, cc]), float(tone[rr, cc])
        return own, None

    side_at = [at(dx, dy) for dx, dy in SIDE_OFF]
    sides = [t for t, _ in side_at]
    side_tone = [v for _, v in side_at]
    corners = [at(dx, dy)[0] for dx, dy in CORNER_OFF]
    differing = [t for t in sides + corners if t > own]
    if not differing:
        return plain, False, False
    count = Counter(differing)
    n = max(count, key=lambda t: (count[t], t))         # v6: ties go to the lighter tier
    n_v5 = max(count, key=lambda t: (count[t], -t))     # v5: ties go to the darker tier
    tie = sum(1 for t in count if count[t] == count[n]) > 1
    mixed = len(count) > 1
    S = frozenset(k for k in range(4) if sides[k] == n)
    Q = [k for k in range(4) if corners[k] == n and k not in S and (k + 3) % 4 not in S]
    nbr = TIER[n]
    approx = None
    if len(S) == 4:
        code = nbr + TIER[own] + "d"
        return v4.Cell(code, code, "d", None, mixed), tie, n != n_v5
    if len(S) == 3:
        pattern, rot = "p", v4._rot_sides("p", S)
    elif len(S) == 2 and S in v4.OPPOSITE:
        approx = "strip"
        pick = min(S, key=lambda k: (side_tone[k] if side_tone[k] is not None else 0.0, k))
        pattern, rot = "s", pick
    elif len(S) == 2:
        pattern, rot = "c", v4._rot_sides("c", S)
        if Q:
            approx = "c+diag"
    elif len(S) == 1:
        pattern, rot = "s", v4._rot_sides("s", S)
        if Q:
            approx = "s+diag"
    else:  # no side has the mass tier: convex corner
        assert Q, "a differing neighbour must be a side or a corner"
        pattern, rot = "i", Q[0]
        if len(Q) > 1:
            approx = "i+multi"
    code = TIER[own] + nbr + pattern
    token = code if rot == 0 else f"{code}@{90 * rot}"
    return v4.Cell(code, token, pattern, approx, mixed), tie, n != n_v5


def side_profile(token: str):
    """Per-side halves (T, R, B, L) of a token, rotated. v5.side_profile with the v6 HALVES."""
    code, _, deg = token.partition("@")
    if len(code) == 1:
        return [(code, code)] * 4
    r = (int(deg or 0) // 90) % 4
    out = [None] * 4
    for k, halves in enumerate(HALVES[code[2]]):
        out[(k + r) % 4] = tuple(code[0] if h == "b" else code[1] for h in halves)
    return out


def verify_edges(tokens, grid, frame):
    """v5.verify_edges with the v6 profiles. Categories as in v5; "other" must be 0."""
    n_edges, bad = 0, Counter()
    for r in range(ROWS):
        for c in range(COLS):
            for k, (dx, dy) in ((1, SIDE_OFF[1]), (2, SIDE_OFF[2])):
                rr, cc = r + dy, c + dx
                if not (0 <= rr < ROWS and 0 <= cc < COLS):
                    continue
                n_edges += 1
                a = side_profile(tokens[r][c])[k]
                b = side_profile(tokens[rr][cc])[(k + 2) % 4]
                if a[0] == b[1] and a[1] == b[0]:
                    continue
                x, y = grid[r][c], grid[rr][cc]
                if frame[r, c] or frame[rr, cc]:
                    bad["frame"] += 1
                elif x.approx or y.approx:
                    bad["approx"] += 1
                elif x.mixed or y.mixed:
                    bad["junction"] += 1
                elif x.pattern == "p" or y.pattern == "p":
                    bad["cap"] += 1
                else:
                    bad["other"] += 1
    return n_edges, bad


class Map:
    """One image: v4 cells, merged class and rotation per cell, and the diag / tip edits."""

    def __init__(self, tiers, tone):
        self.tiers = tiers
        self.tone = tone
        self.ties = 0
        self.changed = 0
        self.grid = []
        cls = [[None] * COLS for _ in range(ROWS)]
        deg = [[0] * COLS for _ in range(ROWS)]
        for r in range(ROWS):
            row = []
            for c in range(COLS):
                cell, tie, ch = classify(tiers, tone, r, c)
                self.ties += tie
                self.changed += ch
                row.append(cell)
                if cell.pattern == "plain":
                    cls[r][c] = TIER[int(tiers[r, c])]
                    continue
                m = v5.merged(cell, flip=True)
                cls[r][c], deg[r][c] = m
                # (b) tip: the base (darker, own) tier protrudes into the lighter mass.
                if cls[r][c][2] == "p" and ORDER[cls[r][c][0]] < ORDER[cls[r][c][1]]:
                    cls[r][c] = cls[r][c][:2] + "t"
            self.grid.append(row)
        self.base_cls = [row[:] for row in cls]
        self.base_deg = [row[:] for row in deg]
        self.cls, self.deg = cls, deg
        self.g_cells = {}      # (r, c) -> rotation of an active diag tile
        self.diag_chains = []  # runs of length >= 2 before the strict check
        self.reverted = Counter()
        self.cleared = {}      # (r, c) -> True: i cells made plain by a diagonal run

    # -- token access -------------------------------------------------------------------------
    def token(self, r, c):
        d = self.deg[r][c]
        return self.cls[r][c] if not d else f"{self.cls[r][c]}@{d}"

    def tokens(self):
        return [[self.token(r, c) for c in range(COLS)] for r in range(ROWS)]

    def profile(self, r, c):
        return side_profile(self.token(r, c))

    # -- (a) diagonal runs --------------------------------------------------------------------
    def _candidate(self, r, c):
        """Rotation if (r, c) can take a diag tile: a v5 c cell, interior, base on its two other sides."""
        if q.FRAME[r, c] or self.grid[r][c].pattern != "c" or self.grid[r][c].approx:
            return None
        return (self.deg[r][c] // 90) % 4  # base sides are left to the strict profile check

    def find_runs(self):
        cand = {}
        for r in range(ROWS):
            for c in range(COLS):
                k = self._candidate(r, c)
                if k is not None:
                    cand[(r, c)] = k
        runs = []
        for (r, c), k in cand.items():
            dx, dy = DIAG_STEP[k]
            if cand.get((r - dy, c - dx)) == k:      # not the start of its run
                continue
            run = [(r, c)]
            while cand.get((run[-1][0] + dy, run[-1][1] + dx)) == k:
                run.append((run[-1][0] + dy, run[-1][1] + dx))
            if len(run) >= 2:
                runs.append((k, run))
        self.n_candidates = len(cand)
        return runs

    def apply_diag(self):
        runs = self.find_runs()
        self.diag_chains = [len(run) for _, run in runs]
        for k, run in runs:
            for r, c in run:
                own, nbr = self.cls[r][c][0], self.cls[r][c][1]
                self.cls[r][c] = own + nbr + "g"
                self.g_cells[(r, c)] = k
        # Corner-only contacts: on the base side of a diagonal run, the 8-neighbourhood gives the
        # neighbours a quarter (v5 i) at the corner the run touches. A diagonal passes through that
        # corner only, so the quarter is cleared (the cell becomes plain own tier). Strict check below.
        for k, run in runs:
            for r, c in run:
                for j in ((k + 2) % 4, (k + 3) % 4):   # base sides of this rotation
                    dx, dy = SIDE_OFF[j]
                    rr, cc = r + dy, c + dx
                    if not (0 <= rr < ROWS and 0 <= cc < COLS):
                        continue
                    if (rr, cc) in self.g_cells or self.grid[rr][cc].pattern != "i":
                        continue
                    if (rr, cc) not in self.cleared:
                        self.cleared[(rr, cc)] = True
                        self.cls[rr][cc] = TIER[int(self.tiers[rr, cc])]
                        self.deg[rr][cc] = 0
        self._settle()

    def _sides_ok(self, r, c, junction_ok: bool = JUNCTION_OK) -> bool:
        """All four sides of (r, c) match their neighbours. With junction_ok, a mismatch is accepted
        when either cell is a three-tier junction (mixed): v5's "junction" category, which verify_edges
        already explains. Frame, approx and cap mismatches are never accepted."""
        prof = self.profile(r, c)
        for k, (dx, dy) in enumerate(SIDE_OFF):
            rr, cc = r + dy, c + dx
            if not (0 <= rr < ROWS and 0 <= cc < COLS):
                continue
            b = self.profile(rr, cc)[(k + 2) % 4]
            if prof[k][0] == b[1] and prof[k][1] == b[0]:
                continue
            x, y = self.grid[r][c], self.grid[rr][cc]
            if junction_ok and (x.mixed or y.mixed) and not (x.approx or y.approx or
                                                            q.FRAME[r, c] or q.FRAME[rr, cc]):
                continue
            return False
        return True

    def _revert(self, r, c, why):
        self.cls[r][c] = self.base_cls[r][c]
        self.deg[r][c] = self.base_deg[r][c]
        self.g_cells.pop((r, c), None)
        self.cleared.pop((r, c), None)
        self.reverted[why] += 1

    def _settle(self):
        changed = True
        while changed:
            changed = False
            for (r, c) in list(self.g_cells) + list(self.cleared):
                if not self._sides_ok(r, c):
                    self._revert(r, c, "side")
                    changed = True
            for (r, c), k in list(self.g_cells.items()):
                dx, dy = DIAG_STEP[k]
                nxt = self.g_cells.get((r + dy, c + dx)) == k
                prv = self.g_cells.get((r - dy, c - dx)) == k
                if not (nxt or prv):
                    self._revert(r, c, "single")
                    changed = True

    def pattern_counts(self):
        cnt = Counter()
        for r in range(ROWS):
            for c in range(COLS):
                if len(self.cls[r][c]) == 1:
                    cnt["plain"] += 1
                else:
                    cnt[self.cls[r][c][2]] += 1
        return cnt

    def diag_run_ends(self):
        """Run ends: diag tiles whose boundary corner (the far end of the run) touches no diag tile."""
        ends = 0
        for (r, c), k in self.g_cells.items():
            dx, dy = DIAG_STEP[k]
            for sgn in (1, -1):
                if (r + sgn * dy, c + sgn * dx) not in self.g_cells:
                    ends += 1
        return ends


def main() -> None:
    v2 = {n: np.load(q.TARGETS / f"{n}-v2.npy") for n in NAMES}
    tiers, _, target, _ = q.equalize_tiers(v2)
    for n in NAMES:
        ref = np.load(q.HERE / "quantized-v2" / f"{n}.npy")
        assert (ref == tiers[n]).all(), f"tiers of {n} differ from quantized-v2"

    maps = {n: Map(tiers[n], v2[n]) for n in NAMES}
    print("1. tiers (equalized, identical to quantized-v2). D / M / L totals per image:")
    for n in NAMES:
        h = np.bincount(tiers[n].ravel(), minlength=3)
        print(f"   {n:9s} tier totals D/M/L {h[0]}/{h[1]}/{h[2]}   target D/M/L {target[0]} / {target[1]} / {target[2]}")

    print("2. tie rule (2-2 and other ties go to the lighter tier):")
    for n in NAMES:
        m = maps[n]
        print(f"   {n:9s} cells with a tie among differing neighbours {m.ties:3d}; "
              f"cells whose mass tier changed from v5 {m.changed:3d}")
    print(f"   total ties {sum(m.ties for m in maps.values())}, total changed {sum(m.changed for m in maps.values())}")

    print("3. diagonal runs (45 degrees, strict side check):")
    for n in NAMES:
        m = maps[n]
        pre = m.find_runs()
        lens = Counter(len(run) for _, run in pre)
        m.apply_diag()
        print(f"   {n:9s} candidates (v5 c cells, interior, base on other sides) {m.n_candidates:3d}; "
              f"runs of length >= 2: {len(pre)} (lengths {dict(sorted(lens.items()))}); "
              f"reverted {dict(m.reverted)}; diag tiles kept {len(m.g_cells)}; run ends {m.diag_run_ends()}")

    print("4. protrusions: p (v5 cap) -> t (tip), darker own tier:")
    for n in NAMES:
        cnt = maps[n].pattern_counts()
        print(f"   {n:9s} tips {cnt['t']}; caps left {cnt['p']}")

    print("5. pattern counts per image (merged class letter; i is merged into c; plain cells not counted):")
    letters = ["s", "c", "p", "d", "g", "t", "b", "n"]
    print("   pattern   " + "  ".join(f"{n:>9s}" for n in NAMES))
    for p in letters:
        print(f"   {p:9s} " + "  ".join(f"{maps[n].pattern_counts()[p]:9d}" for n in NAMES))
    print("   plain     " + "  ".join(f"{maps[n].pattern_counts()['plain']:9d}" for n in NAMES))

    print("6. approximations per image (v5 detail, unchanged):")
    for a in APPROX_ORDER:
        print(f"   {a:9s} " + "  ".join(f"{n}={sum(1 for row in maps[n].grid for x in row if x.approx == a)}" for n in NAMES))

    print("7. edge check, shared edges whose halves disagree (v6 profiles; other must be 0):")
    print("   categories: frame, approx, junction, cap, other")
    totals = Counter()
    for n in NAMES:
        m = maps[n]
        n_edges, bad = verify_edges(m.tokens(), m.grid, q.FRAME)
        totals.update(bad)
        print(f"   {n:9s} shared edges {n_edges}  " + "  ".join(
            f"{k} {bad[k]}" for k in ("frame", "approx", "junction", "cap", "other")))
    print("   total: " + "  ".join(f"{k} {totals[k]}" for k in ("frame", "approx", "junction", "cap", "other")))
    print(f"   unexplained mismatches (other, must be 0): {totals['other']}")

    # Class histograms and budgets, one block per pair (as v5, with the new letters).
    hist = {n: Counter(m for row in maps[n].cls for m in row if len(m) == 3) for n in NAMES}
    classes = sorted({c for h in hist.values() for c in h}, key=lambda c: (ORDER[c[0]], ORDER[c[1]], c[2:]))
    print("8. merged class histogram per image (rotation dropped):")
    print("   class     " + "  ".join(f"{c:>4s}" for c in classes))
    for n in NAMES:
        print(f"   {n:9s} " + "  ".join(f"{hist[n][c]:4d}" for c in classes))
    lines = ["# Boundary budgets (v6), experiment 005. Merged classes per unordered pair (darker tier first).",
             "# max = per-class max over the three images; surplus = max - own. A = cat, B = sailboat, C = tree.", ""]
    hdr = f"{'class':6s} " + "".join(f"{n:>9s}" for n in NAMES) + f" {'max':>5s}" + "".join(
        f" {'sur_' + n[:3]:>8s}" for n in NAMES)
    lines.append(hdr)
    for pair in PAIRS:
        block = [c for c in classes if v5.pair_of(c) == pair]
        if not block:
            continue
        lines.append(f"Pair {pair[0]}-{pair[1]}")
        tmax = 0
        for c in block:
            counts = [hist[n][c] for n in NAMES]
            mx = max(counts)
            tmax += mx
            lines.append(f"{c:6s} " + "".join(f"{x:9d}" for x in counts) + f" {mx:5d}" + "".join(
                f" {mx - x:8d}" for x in counts))
        lines.append("")
    total_sur = {n: sum(max(hist[m][c] for m in NAMES) - hist[n][c] for c in classes) for n in NAMES}
    line = "Transition cells per image: " + ", ".join(
        f"{n} {sum(hist[n].values())}" for n in NAMES) + "; surplus to place (all pairs): " + ", ".join(
        f"{n} {total_sur[n]}" for n in NAMES)
    lines.append(line)
    print(line)
    (HERE / "boundary-budgets-v6.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    head = ["# Merged class maps (v6), experiment 005. A = cat, B = sailboat, C = tree.",
            "# Transition cells: merged class plus @degrees (clockwise); plain cells: tier only.", ""]
    body = []
    for n in NAMES:
        body += [f"# {n}"] + [" ".join(maps[n].token(r, c) for c in range(COLS)) for r in range(ROWS)] + [""]
    (HERE / "quantized-codes-v6.txt").write_text("\n".join(head + body), encoding="utf-8")
    print("wrote boundary-budgets-v6.txt and quantized-codes-v6.txt")


if __name__ == "__main__":
    main()
