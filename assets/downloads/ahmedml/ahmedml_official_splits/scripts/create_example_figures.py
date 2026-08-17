"""Create low/high example figures for AhmedML split report."""

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
DEFAULT_ASSET_ROOT = Path(os.environ.get("AHMEDML_ASSET_ROOT", PACKAGE_ROOT.parent / "ahmedml_hf_assets"))
DOCS_DIR = PACKAGE_ROOT / "docs"


def default_asset_root() -> Path:
    return DEFAULT_ASSET_ROOT if DEFAULT_ASSET_ROOT.exists() else DATA_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create AhmedML report example figures.")
    parser.add_argument("--data-root", type=Path, default=DATA_DIR, help="Directory containing force and metric CSV files.")
    parser.add_argument("--asset-root", type=Path, default=default_asset_root(), help="Directory containing run_*/ STL and PNG assets.")
    parser.add_argument("--output-dir", type=Path, default=DOCS_DIR, help="Directory for PNG figures.")
    parser.add_argument("--max-stl-points", type=int, default=140000, help="Maximum STL vertices plotted per run.")
    return parser.parse_args()


def clean_row(row: dict[str, str]) -> dict[str, str]:
    return {key.strip(): value.strip() for key, value in row.items() if key is not None}


def load_force(data_root: Path) -> dict[int, dict[str, float]]:
    with (data_root / "force_mom_all.csv").open(encoding="utf-8-sig", newline="") as f:
        return {
            int(clean_row(row)["run"]): {
                "cd": float(clean_row(row)["cd"]),
                "cl": float(clean_row(row)["cl"]),
            }
            for row in csv.DictReader(f)
        }


def load_metric(path: Path, column: str) -> dict[int, float]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {int(row["run"]): float(row[column]) for row in csv.DictReader(f)}


def low_high(scores: dict[int, float]) -> tuple[int, int]:
    ordered = sorted(scores, key=lambda run: (scores[run], run))
    return ordered[0], ordered[-1]


def valid_png(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def read_rgb(path: Path) -> np.ndarray:
    if not valid_png(path):
        raise ValueError(f"Not a valid PNG: {path}")
    with Image.open(path) as img:
        return np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0


def scored_crop(path: Path) -> np.ndarray:
    rgb = read_rgb(path)
    height, width, _ = rgb.shape
    return rgb[int(0.30 * height):int(0.96 * height), int(0.08 * width):int(0.92 * width)]


def image_score(path: Path) -> float:
    crop = scored_crop(path)
    brightness = crop.mean(axis=2)
    chroma = crop.max(axis=2) - crop.min(axis=2)
    warm = np.clip(crop[:, :, 0] - crop[:, :, 2], 0.0, 1.0)
    return float(0.45 * brightness.mean() + 0.35 * chroma.mean() + 0.20 * warm.mean())


def uxmean_path(data_root: Path, run: int, axis: str, index: int) -> Path:
    return data_root / f"run_{run}" / "images" / "UxMean" / f"run_{run}-slice-UMean-0-{axis}-{index}.png"


def display_crop(path: Path, axis: str) -> np.ndarray:
    rgb = read_rgb(path)
    height, width, _ = rgb.shape
    if axis == "Y":
        return rgb[int(0.34 * height):int(0.98 * height), :]
    return rgb[int(0.20 * height):int(0.98 * height), int(0.04 * width):int(0.96 * width)]


def make_wake_examples(data_root: Path, asset_root: Path, output_dir: Path, force: dict[int, dict[str, float]]) -> None:
    scores = load_metric(data_root / "image_metrics.csv", "image_wake_score")
    low_run, high_run = low_high(scores)
    slices = [("Y", 4, "Y-4 centreline wake"), ("X", 14, "X-14 near-base wake")]

    fig, axes = plt.subplots(len(slices), 2, figsize=(10.8, 5.8), constrained_layout=True)
    if len(slices) == 1:
        axes = np.asarray([axes])
    for row, (axis, index, slice_label) in enumerate(slices):
        for col, (label, run) in enumerate([("Low image-wake score", low_run), ("High image-wake score", high_run)]):
            ax = axes[row, col]
            ax.imshow(display_crop(uxmean_path(asset_root, run, axis, index), axis))
            ax.set_axis_off()
            ax.set_title(
                f"{label}\n"
                f"run_{run}, {slice_label}, score={scores[run]:.4f}, "
                f"Cd={force[run]['cd']:.4f}, Cl={force[run]['cl']:.4f}",
                fontsize=9,
            )
    fig.suptitle("Image-wake split examples from UxMean Y-4 and near-base X-slice PNGs", fontsize=12)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "wake_score_examples.png", dpi=180)
    plt.close(fig)


def load_binary_stl_vertices(path: Path) -> np.ndarray:
    size = path.stat().st_size
    with path.open("rb") as f:
        f.read(80)
        count_data = f.read(4)
        if len(count_data) != 4:
            raise ValueError(f"Malformed STL: {path}")
        face_count = int(np.frombuffer(count_data, dtype="<u4")[0])
        expected_size = 84 + face_count * 50
        if expected_size != size:
            raise ValueError(f"Expected binary STL size {expected_size}, got {size}: {path}")
        dtype = np.dtype(
            [
                ("normal", "<f4", (3,)),
                ("vertices", "<f4", (3, 3)),
                ("attribute", "<u2"),
            ]
        )
        data = np.fromfile(f, dtype=dtype, count=face_count)
    return np.asarray(data["vertices"].reshape(-1, 3), dtype=np.float32)


def sample_vertices(vertices: np.ndarray, max_points: int, seed: int) -> np.ndarray:
    if len(vertices) <= max_points:
        return vertices
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(vertices), size=max_points, replace=False)
    return vertices[idx]


def setup_projection_axis(ax, all_vertices: np.ndarray, dims: tuple[int, int], title: str) -> None:
    x = all_vertices[:, dims[0]]
    y = all_vertices[:, dims[1]]
    pad_x = 0.04 * max(1e-9, float(x.max() - x.min()))
    pad_y = 0.08 * max(1e-9, float(y.max() - y.min()))
    ax.set_xlim(float(x.min() - pad_x), float(x.max() + pad_x))
    ax.set_ylim(float(y.min() - pad_y), float(y.max() + pad_y))
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title, fontsize=10)
    ax.grid(True, color="#e1e6eb", lw=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def scatter_projection(ax, vertices: np.ndarray, dims: tuple[int, int], color: str, alpha: float, label: str | None = None) -> None:
    ax.scatter(vertices[:, dims[0]], vertices[:, dims[1]], s=0.18, color=color, alpha=alpha, linewidth=0, label=label)


def make_geometry_examples(data_root: Path, asset_root: Path, output_dir: Path, force: dict[int, dict[str, float]], max_points: int) -> None:
    scores = load_metric(data_root / "chamfer_metrics.csv", "ood_score")
    low_run, high_run = low_high(scores)
    low_vertices = sample_vertices(load_binary_stl_vertices(asset_root / f"run_{low_run}" / f"ahmed_{low_run}.stl"), max_points, low_run)
    high_vertices = sample_vertices(load_binary_stl_vertices(asset_root / f"run_{high_run}" / f"ahmed_{high_run}.stl"), max_points, high_run)
    all_vertices = np.vstack([low_vertices, high_vertices])

    low_color = "#6b7280"
    high_color = "#087f8c"
    fig, axes = plt.subplots(2, 2, figsize=(10.4, 6.2), constrained_layout=True)

    setup_projection_axis(axes[0, 0], all_vertices, (0, 2), "Low geometry score: side view")
    scatter_projection(axes[0, 0], low_vertices, (0, 2), low_color, 0.08)
    axes[0, 0].set_xlabel("x")
    axes[0, 0].set_ylabel("z")
    axes[0, 0].text(
        0.02,
        0.96,
        f"run_{low_run}\nscore={scores[low_run]:.5f}\nCd={force[low_run]['cd']:.4f}, Cl={force[low_run]['cl']:.4f}",
        transform=axes[0, 0].transAxes,
        va="top",
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": "#d8dee6", "alpha": 0.85, "pad": 3},
    )

    setup_projection_axis(axes[0, 1], all_vertices, (0, 2), "High geometry score: side view")
    scatter_projection(axes[0, 1], high_vertices, (0, 2), high_color, 0.08)
    axes[0, 1].set_xlabel("x")
    axes[0, 1].set_ylabel("z")
    axes[0, 1].text(
        0.02,
        0.96,
        f"run_{high_run}\nscore={scores[high_run]:.5f}\nCd={force[high_run]['cd']:.4f}, Cl={force[high_run]['cl']:.4f}",
        transform=axes[0, 1].transAxes,
        va="top",
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": "#d8dee6", "alpha": 0.85, "pad": 3},
    )

    setup_projection_axis(axes[1, 0], all_vertices, (0, 1), "Overlay: top view")
    scatter_projection(axes[1, 0], low_vertices, (0, 1), low_color, 0.06, "low")
    scatter_projection(axes[1, 0], high_vertices, (0, 1), high_color, 0.06, "high")
    axes[1, 0].set_xlabel("x")
    axes[1, 0].set_ylabel("y")
    axes[1, 0].legend(frameon=False, markerscale=6, loc="upper left")

    setup_projection_axis(axes[1, 1], all_vertices, (0, 2), "Overlay: side view")
    scatter_projection(axes[1, 1], low_vertices, (0, 2), low_color, 0.06, "low")
    scatter_projection(axes[1, 1], high_vertices, (0, 2), high_color, 0.06, "high")
    axes[1, 1].set_xlabel("x")
    axes[1, 1].set_ylabel("z")
    axes[1, 1].legend(frameon=False, markerscale=6, loc="upper left")

    fig.suptitle("STL-Chamfer geometry split examples", fontsize=12)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "geometry_score_examples.png", dpi=180)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    force = load_force(args.data_root)
    make_wake_examples(args.data_root, args.asset_root, args.output_dir, force)
    make_geometry_examples(args.data_root, args.asset_root, args.output_dir, force, args.max_stl_points)
    print(f"Wrote {args.output_dir / 'wake_score_examples.png'}")
    print(f"Wrote {args.output_dir / 'geometry_score_examples.png'}")


if __name__ == "__main__":
    main()
