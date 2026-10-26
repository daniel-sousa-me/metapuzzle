"""Connector-class analysis of four solution files: prints one markdown table row per file.

Run from anywhere: python3 experiments/010-connector-classes/run.py
The "all pairs" column is the false-fit bound when every non-flat side of an andro board
shares one shape (andro mates with andro), so every pair of sides on different pieces is possible.
"""
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from metapuzzle.connectors import class_summary, contacts  # noqa: E402
from metapuzzle.optimize import Solution  # noqa: E402

FILES = [
    ("005 run-quarter 20x25", "experiments/005-hybrid-tones/run-quarter/solution.json"),
    ("006 run-quarter 8x10", "experiments/006-direction-b/run-quarter/solution.json"),
    ("001 25x20 standard none", "experiments/001-adjacency-baseline/25x20-standard-none.json"),
    ("001 25x20 standard quarter", "experiments/001-adjacency-baseline/25x20-standard-quarter.json"),
]


def all_pairs_bound(sol) -> int:
    """Possible pairs if every non-flat side is one shape: pairs on different pieces, minus actual contacts."""
    c = contacts(sol)
    per_piece = Counter(p for p, _ in c.nodes)
    same = sum(k * (k - 1) // 2 for k in per_piece.values())
    actual = len({(min(u, v), max(u, v)) for u, v in c.edges})
    return len(c.nodes) * (len(c.nodes) - 1) // 2 - same - actual


def main() -> None:
    print("| run | sides | classes | size min / median / max | largest class | false fits | ratio | all pairs | ratio |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, rel in FILES:
        sol = Solution.load(ROOT / rel)
        s = class_summary(sol)
        lg = s["largest"]
        sz = s["size"]
        profiles = s["profiles"]
        kind = "/".join(f"{k} {v}" for k, v in sorted(profiles.items()))
        pairs = all_pairs_bound(sol) if set(profiles) == {"andro"} else None
        pairs_txt = f"{pairs:,} | {pairs / s['intended']:.1f}" if pairs is not None else "- | -"
        print(
            f"| {name} | {s['sides']} ({kind}) | {s['classes']} | "
            f"{sz['min']} / {sz['median']:g} / {sz['max']} | {lg['size']} ({100 * lg['fraction']:.1f}%) | "
            f"{s['false_fits']:,} | {s['false_ratio']:.1f} | {pairs_txt} |"
        )


if __name__ == "__main__":
    main()
