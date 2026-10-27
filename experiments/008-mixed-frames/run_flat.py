"""Variant (ii): rotation none with extra flat-sided pieces, via run_prototype.

Round 1 had to wrap pieces_from_scenes because `metapuzzle prototype` had no --extra-flat option.
It has one now, so this script just calls run_prototype(extra_flat=EXTRA); the same run is
`metapuzzle prototype --scenes scenes.txt --classes classes.json --out OUT --rotation none
--extra-flat EXTRA --cell 24`.
Usage: python run_flat.py EXTRA OUT_DIR [--cell N] [--iters N]
"""
import argparse
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
    res = P.run_prototype(HERE / "scenes.txt", HERE / "classes.json", a.out, border="standard",
                          rotation="none", cell=a.cell, iters=a.iters, extra_flat=a.extra)
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
