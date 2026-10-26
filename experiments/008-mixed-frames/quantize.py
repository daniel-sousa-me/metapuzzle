"""Rank-based quantization of three differently shaped tone targets into 6 classes.

Every map has 480 cells and gets the same class counts 58/86/96/96/86/58 for T0 (darkest)
.. T5 (lightest). Cells are ranked by tone (darkest first) and split by those counts, one
map at a time. Ties in flat regions are broken by a seeded random key (seed 1000 + k).

No shared frame is computed. `validate_scenes` compares border-side class counts only when
all three maps have the same shape (or strict_border=True), so with mixed shapes only the
global histograms must match. Border feasibility is checked by the prototype run itself
(pool sizes in `pieces_from_scenes`); see README.md.

Outputs (in this directory): scenes.txt, quantized/*.npy, quantized-preview.png.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from make_targets import SHAPES

HERE = Path(__file__).resolve().parent
TARGETS = HERE / "targets"
NAMES = ["tree", "sailboat", "panorama"]  # A (portrait), B (landscape), C (panorama)
LETTERS = dict(zip(NAMES, "ABC"))
# T0 (darkest) .. T5 (lightest); sums to 480. The brief's 60/90/100/100/90/60 sums to 500, so it is
# scaled to 480 cells by largest remainder: 500-count proportions x 0.96 -> 57.6/86.4/96/96/86.4/57.6.
COUNTS = [58, 86, 96, 96, 86, 58]
ROUND = 6  # tones are rounded so float noise does not break ties
UP = 12    # preview upscale (nearest)


def quantize(tone: np.ndarray, seed: int, counts=COUNTS) -> np.ndarray:
    """Rank all cells by tone and split them by counts (darkest first); seeded tie-break."""
    flat = np.round(tone.ravel(), ROUND)
    assert sum(counts) == flat.size
    tiebreak = np.random.default_rng(seed).random(flat.size)
    order = np.lexsort((tiebreak, flat))
    labels = np.empty(flat.size, dtype=int)
    start = 0
    for k, n in enumerate(counts):
        labels[order[start:start + n]] = k
        start += n
    return labels.reshape(tone.shape)


def write_scenes(maps: dict, path: Path) -> None:
    lines = [
        "# Mixed-frame mosaic, experiment 008. Three class maps with different shapes (cols x rows):",
        "# A = tree 20x24 (portrait), B = sailboat 30x16 (landscape), C = panorama 40x12.",
        "# T0 darkest .. T5 lightest; counts 58/86/96/96/86/58 in every map (480 cells each).",
        "",
    ]
    for name in NAMES:
        lines += [" ".join(f"T{k}" for k in row) for row in maps[name]]
        lines.append("")
    path.write_text("\n".join(lines))


def preview(tones: dict, classes: dict, path: Path) -> None:
    """Top row: targets as gray tones. Bottom row: classes (T0 black .. T5 white). Each panel at its own shape."""
    gap, label_h = 24, 22
    panels = [(name, SHAPES[name]) for name in NAMES]
    widths = [cols * UP for _, (cols, _) in panels]
    heights = [rows * UP for _, (_, rows) in panels]
    top_h, bot_h = max(heights), max(heights)
    canvas = Image.new("L", (sum(widths) + gap * 4, label_h + top_h + gap + label_h + bot_h + gap), 255)
    draw = ImageDraw.Draw(canvas)
    x = gap
    for name, (cols, rows), w, h in zip(NAMES, [s for _, s in panels], widths, heights):
        draw.text((x, 3), f"{LETTERS[name]} {name} target (0 dark, 1 light)", fill=0)
        t = Image.fromarray(np.round(tones[name] * 255).astype(np.uint8), "L")
        canvas.paste(t.resize((w, h), Image.NEAREST), (x, label_h))
        y2 = label_h + top_h + gap + label_h
        draw.text((x, y2 - label_h + 3), f"{LETTERS[name]} quantized (T0 black .. T5 white)", fill=0)
        q = Image.fromarray((classes[name] * 255 // 5).astype(np.uint8), "L")
        canvas.paste(q.resize((w, h), Image.NEAREST), (x, y2))
        x += w + gap
    canvas.save(path)


def main() -> None:
    tones = {name: np.load(TARGETS / f"{name}.npy") for name in NAMES}
    classes = {name: quantize(tones[name], seed=1000 + k) for k, name in enumerate(NAMES)}
    (HERE / "quantized").mkdir(exist_ok=True)
    for name in NAMES:
        np.save(HERE / "quantized" / f"{name}.npy", classes[name])
    write_scenes(classes, HERE / "scenes.txt")
    preview(tones, classes, HERE / "quantized-preview.png")
    for name in NAMES:
        hist = np.bincount(classes[name].ravel(), minlength=6)
        assert hist.tolist() == COUNTS, (name, hist)
        cols, rows = SHAPES[name]
        border = np.concatenate([classes[name][0], classes[name][-1], classes[name][1:-1, 0], classes[name][1:-1, -1]])
        print(f"{LETTERS[name]} {name} {cols}x{rows} counts {hist.tolist()} | border {np.bincount(border, minlength=6).tolist()}")
        for k in range(6):
            print(f"  T{k}: mean target tone {tones[name][classes[name] == k].mean():.3f}")


if __name__ == "__main__":
    main()
