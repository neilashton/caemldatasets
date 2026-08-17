"""Compute AhmedML image-derived wake scores from downloaded UxMean PNGs.

The metric is intentionally simple and reproducible: for each run, it reads the
Y-4 centreline/near-centreline slice and three near-base X slices, crops out the
upper background-dominated band, and averages a color-intensity score over the
lower flow region. The resulting score is used for the `image_wake` OOD split.
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

import numpy as np
from PIL import Image


N_CASES = 500
RUN_IDS = list(range(1, N_CASES + 1))
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
DEFAULT_ASSET_ROOT = Path(os.environ.get("AHMEDML_ASSET_ROOT", PACKAGE_ROOT.parent / "ahmedml_hf_assets"))
CENTERLINE_Y_INDEX = 4
NEAR_WAKE_X_INDICES = (14, 15, 16)


def default_data_root() -> Path:
    return DEFAULT_ASSET_ROOT if DEFAULT_ASSET_ROOT.exists() else DATA_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute AhmedML UxMean image wake metrics.")
    parser.add_argument("--data-root", type=Path, default=default_data_root(), help="Directory containing run_*/images/UxMean PNGs.")
    parser.add_argument("--output", type=Path, default=DATA_DIR / "image_metrics.csv", help="CSV output path.")
    parser.add_argument("--min-images", type=int, default=4, help="Minimum targeted UxMean PNGs required for an observed score.")
    return parser.parse_args()


def _valid_png(path: Path) -> bool:
    if path.name.startswith("._"):
        return False
    try:
        with path.open("rb") as f:
            return f.read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def _image_score(path: Path) -> float | None:
    if not _valid_png(path):
        return None
    try:
        with Image.open(path) as img:
            rgb = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    except Exception:
        return None

    height, width, _ = rgb.shape
    # The upper band in AhmedML UxMean slices is mostly uniform far-field color.
    # The lower central region contains the visible body/wake/ground structure.
    crop = rgb[int(0.30 * height):int(0.96 * height), int(0.08 * width):int(0.92 * width)]
    brightness = crop.mean(axis=2)
    chroma = crop.max(axis=2) - crop.min(axis=2)
    warm = np.clip(crop[:, :, 0] - crop[:, :, 2], 0.0, 1.0)
    return float(0.45 * brightness.mean() + 0.35 * chroma.mean() + 0.20 * warm.mean())


def uxmean_path(data_root: Path, run: int, axis: str, index: int) -> Path:
    return data_root / f"run_{run}" / "images" / "UxMean" / f"run_{run}-slice-UMean-0-{axis}-{index}.png"


def target_uxmean_images(data_root: Path, run: int) -> list[tuple[str, Path]]:
    return [
        (f"Y-{CENTERLINE_Y_INDEX}", uxmean_path(data_root, run, "Y", CENTERLINE_Y_INDEX)),
        *[(f"X-{index}", uxmean_path(data_root, run, "X", index)) for index in NEAR_WAKE_X_INDICES],
    ]


def run_image_score(data_root: Path, run: int, min_images: int) -> tuple[float, int]:
    scores: dict[str, float] = {}
    for label, path in target_uxmean_images(data_root, run):
        score = _image_score(path)
        if score is not None:
            scores[label] = score
    if len(scores) < min_images:
        return float("nan"), len(scores)
    y_score = scores.get(f"Y-{CENTERLINE_Y_INDEX}")
    x_scores = [scores[f"X-{index}"] for index in NEAR_WAKE_X_INDICES if f"X-{index}" in scores]
    if y_score is None or len(x_scores) != len(NEAR_WAKE_X_INDICES):
        return float("nan"), len(scores)
    return float(0.5 * y_score + 0.5 * np.mean(x_scores)), len(scores)


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["run", "image_wake_score", "image_wake_observed", "uxmean_images", "uxmean_slices"],
        )
        writer.writeheader()
        for run in RUN_IDS:
            score, count = run_image_score(args.data_root, run, args.min_images)
            observed = not np.isnan(score)
            writer.writerow(
                {
                    "run": run,
                    "image_wake_score": "" if not observed else score,
                    "image_wake_observed": str(observed).lower(),
                    "uxmean_images": count,
                    "uxmean_slices": "Y-4;X-14;X-15;X-16",
                }
            )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
