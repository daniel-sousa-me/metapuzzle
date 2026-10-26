"""Variant (ii): rotation none with extra flat-sided pieces, via run_prototype.

`metapuzzle prototype` has no --extra-flat option (only `solve` does, and it takes no class
spec). run_prototype calls pieces_from_scenes without extra_flat_pieces, so this script wraps
pieces_from_scenes with functools.partial to pass the count, then calls run_prototype unchanged.
Usage: python run_flat.py EXTRA OUT_DIR [--cell N] [--iters N]
"""
import argparse
import functools
import sys
from pathlib import Path

sys.path.insert(0, "/home/user/metapuzzle/src")
import metapuzzle.prototype as P  # noqa: E402

HERE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("extra", type=int)
    ap.add_argument("out")
    ap.add_argument("--cell", type=int, default=24)
    ap.add_argument("--iters", type=int, default=None)
    a = ap.parse_args()
    P.pieces_from_scenes = functools.partial(P.pieces_from_scenes, extra_flat_pieces=a.extra)
    res = P.run_prototype(HERE / "scenes.txt", HERE / "classes.json", a.out,
                          border="standard", rotation="none", cell=a.cell, iters=a.iters)
    s = res["shared"]
    print(f"extra={a.extra} shared AB/AC/BC={s['AB']}/{s['AC']}/{s['BC']} valid={res['valid']} "
          f"violations={len(res['violations'])} out={res['out_dir']}")
    for line in res["gate_lines"]:
        print(line)
    for v in res["violations"][:5]:
        print("  violation:", v)
    return 0 if res["valid"] else 2


if __name__ == "__main__":
    sys.exit(main())
