"""Create WindsorML geometry and image-wake examples for the report."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
DOCS_DIR = PACKAGE_ROOT / "docs"
DEFAULT_ASSET_ROOT = Path(os.environ.get("WINDSORML_ASSET_ROOT", PACKAGE_ROOT.parent / "windsorml_hf_assets"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create WindsorML report example figures.")
    parser.add_argument("--data-root", type=Path, default=DATA_DIR, help="Directory containing force and metric CSVs.")
    parser.add_argument("--asset-root", type=Path, default=DEFAULT_ASSET_ROOT, help="Directory containing run_*/ PNG assets.")
    parser.add_argument("--output-dir", type=Path, default=DOCS_DIR, help="Directory for report figures.")
    return parser.parse_args()


def clean_row(row: dict[str, str]) -> dict[str, str]:
    return {key.strip(): value.strip() for key, value in row.items() if key is not None}


def load_force(data_root: Path) -> dict[int, dict[str, float]]:
    with (data_root / "force_mom_all.csv").open(encoding="utf-8-sig", newline="") as f:
        return {
            int(clean_row(raw)["run"]): {
                "cd": float(clean_row(raw)["cd"]),
                "cl": float(clean_row(raw)["cl"]),
            }
            for raw in csv.DictReader(f)
        }


def load_metric(path: Path, column: str, observed_column: str) -> tuple[dict[int, float], set[int]]:
    scores: dict[int, float] = {}
    observed: set[int] = set()
    with path.open(encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            row = clean_row(raw)
            if row.get(column, ""):
                run = int(row["run"])
                scores[run] = float(row[column])
                if row.get(observed_column, "true").lower() == "true":
                    observed.add(run)
    return scores, observed


def low_high(scores: dict[int, float], observed: set[int]) -> tuple[int, int]:
    ordered = sorted(observed, key=lambda run: (scores[run], run))
    if not ordered:
        raise ValueError("No observed metric cases are available for examples")
    return ordered[0], ordered[-1]


def read_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0


def velocity_path(asset_root: Path, run: int, view: str, index: int) -> Path:
    return asset_root / f"run_{run}" / "images" / "velocityxavg" / f"{view}_scan_{index:04d}.png"


def wake_crop(rgb: np.ndarray, view: str) -> np.ndarray:
    height, width, _ = rgb.shape
    if view == "view1_constz":
        return rgb[int(0.37 * height):int(0.98 * height), int(0.04 * width):int(0.94 * width)]
    return rgb[int(0.28 * height):int(0.98 * height), int(0.14 * width):int(0.86 * width)]


def make_wake_examples(data_root: Path, asset_root: Path, output_dir: Path, force: dict[int, dict[str, float]]) -> tuple[int, int]:
    scores, observed = load_metric(data_root / "image_metrics.csv", "image_wake_score", "image_wake_observed")
    low_run, high_run = low_high(scores, observed)
    views = [("view1_constz", 5, "near-centreline z-plane"), ("view2_constx", 53, "near-base x-plane")]
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 6.2), constrained_layout=True)
    for row, (view, index, label) in enumerate(views):
        for col, (score_label, run) in enumerate([("Low wake score", low_run), ("High wake score", high_run)]):
            axes[row, col].imshow(wake_crop(read_rgb(velocity_path(asset_root, run, view, index)), view))
            axes[row, col].set_axis_off()
            axes[row, col].set_title(
                f"{score_label}: run_{run}\n{label}, score={scores[run]:.4f}, "
                f"Cd={force[run]['cd']:.4f}, Cl={force[run]['cl']:.4f}",
                fontsize=9,
            )
    fig.suptitle("Image-wake split examples from streamwise-velocity PNGs", fontsize=12)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "wake_score_examples.png", dpi=180)
    plt.close(fig)
    return low_run, high_run


def geometry_path(asset_root: Path, run: int) -> Path:
    return asset_root / f"run_{run}" / "images" / f"windsor_{run}.png"


def transparent_silhouette(rgb: np.ndarray, color: str, alpha: float) -> np.ndarray:
    color_rgb = np.asarray([int(color[index:index + 2], 16) for index in (1, 3, 5)], dtype=np.float32) / 255.0
    brightness = rgb.mean(axis=2)
    mask = brightness > 0.08
    rgba = np.zeros((*rgb.shape[:2], 4), dtype=np.float32)
    rgba[:, :, :3] = color_rgb
    rgba[:, :, 3] = mask.astype(np.float32) * alpha
    return rgba


def content_bounds(images: list[np.ndarray], padding: int = 20) -> tuple[slice, slice]:
    mask = np.zeros(images[0].shape[:2], dtype=bool)
    for rgb in images:
        mask |= rgb.mean(axis=2) > 0.08
    rows, cols = np.where(mask)
    if len(rows) == 0:
        return slice(0, images[0].shape[0]), slice(0, images[0].shape[1])
    y0, y1 = max(0, int(rows.min()) - padding), min(images[0].shape[0], int(rows.max()) + padding + 1)
    x0, x1 = max(0, int(cols.min()) - padding), min(images[0].shape[1], int(cols.max()) + padding + 1)
    return slice(y0, y1), slice(x0, x1)


def make_geometry_examples(data_root: Path, asset_root: Path, output_dir: Path, force: dict[int, dict[str, float]]) -> tuple[int, int]:
    scores, observed = load_metric(data_root / "chamfer_metrics.csv", "ood_score", "geometry_observed")
    available = {run for run in observed if geometry_path(asset_root, run).exists()}
    low_run, high_run = low_high(scores, available)
    low_rgb = read_rgb(geometry_path(asset_root, low_run))
    high_rgb = read_rgb(geometry_path(asset_root, high_run))
    union_y, union_x = content_bounds([low_rgb, high_rgb], padding=28)
    low_y, low_x = content_bounds([low_rgb], padding=28)
    high_y, high_x = content_bounds([high_rgb], padding=28)

    fig = plt.figure(figsize=(11.0, 5.8), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=(1.0, 1.15))
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[1, :])]
    for ax, rgb, label, run in [
        (axes[0], low_rgb[low_y, low_x], "Low geometry score", low_run),
        (axes[1], high_rgb[high_y, high_x], "High geometry score", high_run),
    ]:
        ax.imshow(rgb)
        ax.set_axis_off()
        ax.set_title(
            f"{label}: run_{run}\nscore={scores[run]:.5f}, Cd={force[run]['cd']:.4f}, Cl={force[run]['cl']:.4f}",
            fontsize=9,
        )
    axes[2].imshow(transparent_silhouette(low_rgb[union_y, union_x], "#6b7280", 0.55))
    axes[2].imshow(transparent_silhouette(high_rgb[union_y, union_x], "#008c95", 0.55))
    axes[2].set_axis_off()
    axes[2].set_title(f"Transparent side-view overlay: run_{low_run} (gray) and run_{high_run} (teal)", fontsize=10)
    fig.suptitle("STL-Chamfer geometry split examples", fontsize=12)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "geometry_score_examples.png", dpi=180)
    plt.close(fig)
    return low_run, high_run


def main() -> None:
    args = parse_args()
    force = load_force(args.data_root)
    wake_runs = make_wake_examples(args.data_root, args.asset_root, args.output_dir, force)
    geometry_runs = make_geometry_examples(args.data_root, args.asset_root, args.output_dir, force)
    print(f"Wrote {args.output_dir / 'wake_score_examples.png'} using runs {wake_runs}")
    print(f"Wrote {args.output_dir / 'geometry_score_examples.png'} using runs {geometry_runs}")


if __name__ == "__main__":
    main()
