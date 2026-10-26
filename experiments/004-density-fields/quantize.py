"""Rank-based (histogram-matching) quantization of three tone targets into 6 classes.

Every image gets the same class counts: 60/90/100/100/90/60 for T0 (darkest) .. T5
(lightest). Cells are ranked by tone (darkest first) and split by those counts.

The scene validator also needs the frame to agree between images, for rotation "none"
per side (N, E, S, W edge cells) and per corner (NW, NE, SE, SW). So the frame is
fixed first and shared:
  * each corner gets one class, the rounded mean of the three images' own corner
    classes, used in all three maps;
  * each side gets a shared histogram: the mean of the three images' own side
    histograms (largest-remainder rounding);
  * each image then ranks its own cells inside every side (with that side's shared
    counts) and its interior cells (with the remaining counts), so the global counts
    still match exactly.

Ties (flat regions share one tone) are broken by a seeded random key per image and
region: image k uses seed 1000 + k. A deterministic tie-break is needed for the
ranking, but a row-major one would send the top of a flat region to a darker class
than the bottom, which is a spurious band; a seeded random key scatters the classes
inside a flat region instead.

Outputs (in this directory): scenes.txt, quantized/*.npy, quantized-preview.png.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
TARGETS = HERE / "targets"
NAMES = ["cat", "sailboat", "tree"]
COUNTS = [60, 90, 100, 100, 90, 60]  # T0 (darkest) .. T5 (lightest); sums to 500
ROWS, COLS = 25, 20
UP = 16
ROUND = 6  # tones are rounded so float noise does not break ties


def region_cells():
    """Flat indices for each frame cell group and the interior."""
    last_r, last_c = ROWS - 1, COLS - 1
    corners = {"NW": (0, 0), "NE": (0, last_c), "SW": (last_r, 0), "SE": (last_r, last_c)}
    sides = {
        "N": [(0, c) for c in range(1, last_c)],
        "S": [(last_r, c) for c in range(1, last_c)],
        "W": [(r, 0) for r in range(1, last_r)],
        "E": [(r, last_c) for r in range(1, last_r)],
    }
    frame = set(corners.values()) | {p for side in sides.values() for p in side}
    interior = [(r, c) for r in range(ROWS) for c in range(COLS) if (r, c) not in frame]
    flat = lambda cells: np.array([r * COLS + c for r, c in cells], dtype=int)
    return {k: flat([p]) for k, p in corners.items()}, {k: flat(v) for k, v in sides.items()}, flat(interior)


def quantize_global(tone: np.ndarray, seed: int, counts=COUNTS) -> np.ndarray:
    """Plain rank quantization over the whole image (no frame constraint)."""
    labels = np.empty(tone.size, dtype=int)
    for idx, k in _rank_assign(tone, np.arange(tone.size), counts, seed).items():
        labels[idx] = k
    return labels.reshape(tone.shape)


def _rank_assign(tone: np.ndarray, cells: np.ndarray, counts, seed: int) -> dict:
    """Rank the given flat cell indices by tone and split them by counts (darkest first)."""
    assert sum(counts) == cells.size
    flat = np.round(tone.ravel()[cells], ROUND)
    tiebreak = np.random.default_rng(seed).random(cells.size)
    order = cells[np.lexsort((tiebreak, flat))]
    out, start = {}, 0
    for k, n in enumerate(counts):
        for idx in order[start:start + n]:
            out[int(idx)] = k
        start += n
    return out


def _largest_remainder(frac: np.ndarray, total: int) -> list[int]:
    raw = frac * total
    counts = np.floor(raw).astype(int)
    for k in np.argsort(-(raw - counts), kind="stable")[: total - counts.sum()]:
        counts[k] += 1
    return counts.tolist()


def shared_frame(natural: dict):
    """Corner classes and per-side class counts shared by all three maps."""
    corners, sides, _ = region_cells()
    corner_class = {}
    for name_, cell in corners.items():
        mean = np.mean([natural[n].ravel()[cell[0]] for n in NAMES])
        corner_class[name_] = int(round(mean))
    side_counts = {}
    for s, cells in sides.items():
        frac = np.mean([np.bincount(natural[n].ravel()[cells], minlength=6) / cells.size for n in NAMES], axis=0)
        side_counts[s] = _largest_remainder(frac, cells.size)
    return corner_class, side_counts


def quantize(tone: np.ndarray, seed: int, corner_class: dict, side_counts: dict, counts=COUNTS) -> np.ndarray:
    assert tone.shape == (ROWS, COLS)
    corners, sides, interior = region_cells()
    labels = np.empty(tone.size, dtype=int)
    for name_, cell in corners.items():
        labels[cell] = corner_class[name_]
    for s, cells in sides.items():
        for idx, k in _rank_assign(tone, cells, side_counts[s], seed * 10 + ord(s)).items():
            labels[idx] = k
    used = np.bincount(labels[np.concatenate([np.array(list(corners.values())).ravel()] + list(sides.values()))],
                       minlength=6)
    inner = [c - u for c, u in zip(counts, used)]
    assert min(inner) >= 0, inner
    for idx, k in _rank_assign(tone, interior, inner, seed * 10 + ord("I")).items():
        labels[idx] = k
    return labels.reshape(tone.shape)


def write_scenes(maps: dict, path: Path) -> None:
    lines = [
        "# Density-field mosaic, experiment 004. Three 20x25 class maps (cols x rows).",
        "# A = cat, B = sailboat, C = tree. T0 darkest .. T5 lightest; counts 60/90/100/100/90/60 in every map.",
        "",
    ]
    for name in NAMES:
        lines += [" ".join(f"T{k}" for k in row) for row in maps[name]]
        lines.append("")
    path.write_text("\n".join(lines))


def preview(tones: dict, classes: dict, path: Path) -> None:
    """Top row: targets as gray tones. Bottom row: classes as gray (T0 black .. T5 white)."""
    gap, label_h = 24, 26
    w, h = COLS * UP, ROWS * UP
    canvas = Image.new("L", (3 * w + 4 * gap, 2 * h + 3 * gap + 2 * label_h), 255)
    draw = ImageDraw.Draw(canvas)
    for col, name in enumerate(NAMES):
        x = gap + col * (w + gap)
        draw.text((x, 4), f"{name} target (0 dark, 1 light)", fill=0)
        t = Image.fromarray(np.round(tones[name] * 255).astype(np.uint8), "L")
        canvas.paste(t.resize((w, h), Image.NEAREST), (x, label_h))
        y2 = label_h + h + gap + label_h
        draw.text((x, y2 - label_h + 4), f"{name} quantized (T0 black .. T5 white)", fill=0)
        q = Image.fromarray((classes[name] * 255 // 5).astype(np.uint8), "L")
        canvas.paste(q.resize((w, h), Image.NEAREST), (x, y2))
    canvas.save(path)


def main() -> None:
    tones = {name: np.load(TARGETS / f"{name}.npy") for name in NAMES}
    natural = {name: quantize_global(tones[name], seed=1000 + k) for k, name in enumerate(NAMES)}
    corner_class, side_counts = shared_frame(natural)
    print("shared corner classes:", corner_class)
    print("shared side counts:", side_counts)
    classes = {name: quantize(tones[name], 1000 + k, corner_class, side_counts) for k, name in enumerate(NAMES)}
    (HERE / "quantized").mkdir(exist_ok=True)
    for name in NAMES:
        np.save(HERE / "quantized" / f"{name}.npy", classes[name])
    write_scenes(classes, HERE / "scenes.txt")
    preview(tones, classes, HERE / "quantized-preview.png")
    for name in NAMES:
        hist = np.bincount(classes[name].ravel(), minlength=6)
        assert hist.tolist() == COUNTS, (name, hist)
        print(name, "counts", hist.tolist(), "| cells differing from plain global rank:",
              int((classes[name] != natural[name]).sum()))
        for k in range(6):
            print(f"  T{k}: mean target tone {tones[name][classes[name] == k].mean():.3f}")


if __name__ == "__main__":
    main()
