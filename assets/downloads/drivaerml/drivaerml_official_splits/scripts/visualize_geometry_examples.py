"""Build low/high geometry examples for the split report.

Creates geometry_split_examples.png. The script selects the lowest Chamfer
geometry score from geometry_train and the highest score from geometry_test,
then renders same-scale complete-car side-view PNGs plus a transparent overlay
when source images are available.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from generate_splits import _run_image_dir, run_id


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
DATA_DIR = PACKAGE_ROOT / "data"
DOCS_DIR = PACKAGE_ROOT / "docs"
SPLITS_DIR = PACKAGE_ROOT / "splits"
CHAMFER = DATA_DIR / "chamfer_metrics.csv"
MANIFEST = SPLITS_DIR / "manifest.json"
OUT = DOCS_DIR / "geometry_split_examples.png"
LOW_COLOR = np.array([47, 111, 176], dtype=np.float32) / 255.0
HIGH_COLOR = np.array([200, 92, 46], dtype=np.float32) / 255.0
BACKGROUND = np.array([1.0, 1.0, 1.0], dtype=np.float32)


def _load_scores() -> dict[int, float]:
    rows = csv.DictReader(CHAMFER.open(encoding="utf-8"))
    return {int(row["run"]): float(row["ood_score"]) for row in rows}


def _ids(manifest: dict[str, list[str]], key: str) -> set[int]:
    return {run_id(cid) for cid in manifest[key]}


def _example_runs() -> tuple[tuple[int, float], tuple[int, float]]:
    scores = _load_scores()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    train_ids = _ids(manifest, "geometry_train")
    test_ids = _ids(manifest, "geometry_test")
    low_run = min(train_ids, key=lambda rid: scores[rid])
    high_run = max(test_ids, key=lambda rid: scores[rid])
    return (low_run, scores[low_run]), (high_run, scores[high_run])


def _surface_side_path(run: int) -> Path | None:
    image_dir = _run_image_dir(run)
    if image_dir is None:
        return None
    path = image_dir / f"fig_run{run}_SRS_surf-ySide_grid.png"
    return path if path.exists() else None


def _read_png_rgb(path: Path) -> np.ndarray | None:
    if path.name.startswith("._"):
        return None
    try:
        with path.open("rb") as f:
            if f.read(8) != b"\x89PNG\r\n\x1a\n":
                return None
        with Image.open(path) as img:
            img = img.convert("RGB")
            arr = np.asarray(img, dtype=np.uint8)
    except Exception:
        return None

    return arr


def _foreground_mask(arr: np.ndarray) -> np.ndarray:
    return np.any(arr < 245, axis=2)


def _shared_crop_bbox(arrays: list[np.ndarray]) -> tuple[int, int, int, int]:
    masks = [_foreground_mask(arr) for arr in arrays]
    combined = np.logical_or.reduce(masks)
    h, w = combined.shape

    # Use dense rows/columns so tiny annotations do not define the crop, then
    # fall back to all foreground pixels if an unusual source image is sparse.
    min_col_pixels = max(8, int(0.02 * h))
    min_row_pixels = max(16, int(0.035 * w))
    xs = np.where(combined.sum(axis=0) >= min_col_pixels)[0]
    ys = np.where(combined.sum(axis=1) >= min_row_pixels)[0]
    if len(xs) == 0 or len(ys) == 0:
        ys, xs = np.where(combined)
    if len(xs) == 0 or len(ys) == 0:
        return (0, h, 0, w)

    pad_x = int(0.03 * w)
    pad_y = int(0.06 * h)
    left = max(0, xs.min() - pad_x)
    right = min(w, xs.max() + pad_x + 1)
    top = max(0, ys.min() - pad_y)
    bottom = min(h, ys.max() + pad_y + 1)
    return (top, bottom, left, right)


def _crop(arr: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    top, bottom, left, right = bbox
    return arr[top:bottom, left:right].astype(np.float32) / 255.0


def _example_image(run: int) -> tuple[np.ndarray | None, str]:
    path = _surface_side_path(run)
    if path is None:
        return None, "source complete-car PNG not found"
    arr = _read_png_rgb(path)
    if arr is None:
        return None, "source complete-car PNG could not be read"
    return arr, path.name


def _transparent_overlay(low_arr: np.ndarray, high_arr: np.ndarray) -> np.ndarray:
    low_mask = _foreground_mask((low_arr * 255.0).astype(np.uint8))
    high_mask = _foreground_mask((high_arr * 255.0).astype(np.uint8))
    canvas = np.ones(low_arr.shape, dtype=np.float32) * BACKGROUND

    alpha = 0.62
    canvas[low_mask] = (1.0 - alpha) * canvas[low_mask] + alpha * LOW_COLOR
    canvas[high_mask] = (1.0 - alpha) * canvas[high_mask] + alpha * HIGH_COLOR
    return np.clip(canvas, 0.0, 1.0)


def _plot_placeholder(ax: plt.Axes, title: str, run: int, score: float, filename: str) -> None:
    ax.set_facecolor("#f5f7fa")
    ax.text(
        0.5,
        0.5,
        f"run_{run}\nChamfer score={score:.6f}\n{filename}",
        ha="center",
        va="center",
        fontsize=10,
        color="#1f2933",
        transform=ax.transAxes,
    )
    ax.set_title(title, fontsize=10)


def _finish_axis(ax: plt.Axes, xlabel: str = "") -> None:
    ax.set_xlabel(xlabel, fontsize=7)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def main() -> None:
    low_example, high_example = _example_runs()
    examples = [
        ("Training-side low geometry score", *low_example),
        ("Transparent overlay", None, None),
        ("Geometry-test high geometry score", *high_example),
    ]

    low_arr, low_filename = _example_image(low_example[0])
    high_arr, high_filename = _example_image(high_example[0])
    fig = plt.figure(figsize=(11.5, 6.6), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.18])
    low_ax = fig.add_subplot(grid[0, 0])
    high_ax = fig.add_subplot(grid[0, 1])
    overlay_ax = fig.add_subplot(grid[1, :])

    if low_arr is not None and high_arr is not None:
        bbox = _shared_crop_bbox([low_arr, high_arr])
        low_crop = _crop(low_arr, bbox)
        high_crop = _crop(high_arr, bbox)
        overlay = _transparent_overlay(low_crop, high_crop)

        low_ax.imshow(low_crop)
        low_ax.set_title(
            f"{examples[0][0]}\nrun_{low_example[0]}, Chamfer score={low_example[1]:.6f}",
            fontsize=10,
        )
        _finish_axis(low_ax, low_filename)

        high_ax.imshow(high_crop)
        high_ax.set_title(
            f"{examples[2][0]}\nrun_{high_example[0]}, Chamfer score={high_example[1]:.6f}",
            fontsize=10,
        )
        _finish_axis(high_ax, high_filename)

        overlay_ax.imshow(overlay)
        overlay_ax.set_title(
            "Transparent overlay\nblue=train-side low, orange=geometry-test high",
            fontsize=10,
        )
        _finish_axis(overlay_ax, "same crop and camera")
    else:
        for ax, (title, run, score), arr, filename in [
            (low_ax, examples[0], low_arr, low_filename),
            (high_ax, examples[2], high_arr, high_filename),
        ]:
            if arr is None:
                _plot_placeholder(ax, title, run, score, filename)
            else:
                ax.imshow(arr.astype(np.float32) / 255.0)
                ax.set_title(f"{title}\nrun_{run}, Chamfer score={score:.6f}", fontsize=10)
            _finish_axis(ax, filename)
        overlay_ax.set_facecolor("#f5f7fa")
        overlay_ax.text(
            0.5,
            0.5,
            "Overlay unavailable\nboth source PNGs are required",
            ha="center",
            va="center",
            fontsize=10,
            color="#1f2933",
            transform=overlay_ax.transAxes,
        )
        overlay_ax.set_title(examples[1][0], fontsize=10)
        _finish_axis(overlay_ax, "")

    fig.suptitle("Geometry split examples: complete-car surface views and overlay", fontsize=13)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=180)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
