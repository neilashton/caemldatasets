"""Compute WindsorML image-derived wake scores from velocity PNGs.

The score measures the area and intensity of low streamwise velocity in two
near-centreline z-constant views and three x-constant planes immediately behind
the body. Missing image scores can be imputed from the five nearest observed
cases in standardized force/geometry feature space; the CSV records whether
each score was observed or imputed.
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

import numpy as np
from PIL import Image


N_CASES = 355
RUN_IDS = list(range(N_CASES))
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
DEFAULT_ASSET_ROOT = Path(os.environ.get("WINDSORML_ASSET_ROOT", PACKAGE_ROOT.parent / "windsorml_hf_assets"))
CENTERLINE_Z_INDICES = (4, 5)
NEAR_WAKE_X_INDICES = (53, 55, 57)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute WindsorML velocity-image wake metrics.")
    parser.add_argument("--asset-root", type=Path, default=DEFAULT_ASSET_ROOT, help="Directory containing run_*/images assets.")
    parser.add_argument("--data-root", type=Path, default=DATA_DIR, help="Directory containing aggregate force/geometry CSVs.")
    parser.add_argument("--output", type=Path, default=DATA_DIR / "image_metrics.csv", help="CSV output path.")
    parser.add_argument("--neighbors", type=int, default=5, help="Nearest observed cases used to impute a missing score.")
    parser.add_argument("--no-impute", action="store_true", help="Leave missing scores blank instead of imputing them.")
    return parser.parse_args()


def clean_row(row: dict[str, str]) -> dict[str, str]:
    return {key.strip(): value.strip() for key, value in row.items() if key is not None}


def load_features(data_root: Path) -> tuple[dict[int, list[float]], list[str]]:
    force: dict[int, dict[str, float]] = {}
    with (data_root / "force_mom_all.csv").open(encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            row = clean_row(raw)
            force[int(row["run"])] = {key: float(value) for key, value in row.items() if key != "run"}

    geometry: dict[int, dict[str, float]] = {}
    with (data_root / "geo_parameters_all.csv").open(encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            row = clean_row(raw)
            geometry[int(row["run"])] = {key: float(value) for key, value in row.items() if key != "run"}

    missing = sorted(set(RUN_IDS) - set(force) | (set(RUN_IDS) - set(geometry)))
    if missing:
        raise ValueError(f"Aggregate CSVs are missing WindsorML runs: {missing}")
    force_fields = [field for field in ("cd", "cs", "cl", "cmy") if field in next(iter(force.values()))]
    geometry_fields = sorted(next(iter(geometry.values())).keys())
    labels = [f"force:{field}" for field in force_fields] + [f"geometry:{field}" for field in geometry_fields]
    features = {
        run: [force[run][field] for field in force_fields] + [geometry[run][field] for field in geometry_fields]
        for run in RUN_IDS
    }
    return features, labels


def valid_png(path: Path) -> bool:
    if path.name.startswith("._"):
        return False
    try:
        with path.open("rb") as f:
            return f.read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def read_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0


def image_path(asset_root: Path, run: int, view: str, index: int) -> Path:
    return asset_root / f"run_{run}" / "images" / "velocityxavg" / f"{view}_scan_{index:04d}.png"


def low_speed_score(rgb: np.ndarray, crop: tuple[float, float, float, float]) -> tuple[float, float]:
    height, width, _ = rgb.shape
    x0, x1, y0, y1 = crop
    region = rgb[int(y0 * height):int(y1 * height), int(x0 * width):int(x1 * width)]
    # The published velocity color map is orange at freestream and blue/purple
    # at low speed. B-R therefore gives a stable low-speed signal while
    # excluding the neutral gray body.
    coolness = np.clip(region[:, :, 2] - region[:, :, 0], 0.0, 1.0)
    area_fraction = float(np.mean(coolness > 0.03))
    intensity = float(np.mean(coolness))
    return area_fraction, 0.75 * area_fraction + 0.25 * intensity


def observed_run_score(asset_root: Path, run: int) -> tuple[float, float, float, int] | None:
    z_paths = [image_path(asset_root, run, "view1_constz", index) for index in CENTERLINE_Z_INDICES]
    x_paths = [image_path(asset_root, run, "view2_constx", index) for index in NEAR_WAKE_X_INDICES]
    paths = z_paths + x_paths
    if not all(valid_png(path) for path in paths):
        return None

    centreline = [low_speed_score(read_rgb(path), (0.43, 0.89, 0.47, 0.97)) for path in z_paths]
    near_base = [low_speed_score(read_rgb(path), (0.23, 0.77, 0.43, 0.96)) for path in x_paths]
    centreline_area = float(np.mean([value[0] for value in centreline]))
    near_base_area = float(np.mean([value[0] for value in near_base]))
    centreline_score = float(np.mean([value[1] for value in centreline]))
    near_base_score = float(np.mean([value[1] for value in near_base]))
    return 0.5 * centreline_score + 0.5 * near_base_score, centreline_area, near_base_area, len(paths)


def nearest_observed(
    features: dict[int, list[float]],
    observed_runs: list[int],
    target_run: int,
    count: int,
) -> list[int]:
    runs = RUN_IDS
    matrix = np.asarray([features[run] for run in runs], dtype=float)
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    stds[stds == 0.0] = 1.0
    standardized = (matrix - means) / stds
    target = standardized[target_run]
    ranked = sorted(observed_runs, key=lambda run: (float(np.linalg.norm(standardized[run] - target)), run))
    return ranked[: max(1, min(count, len(ranked)))]


def main() -> None:
    args = parse_args()
    features, _ = load_features(args.data_root)
    values: dict[int, tuple[float, float, float, int]] = {}
    observed: dict[int, bool] = {}
    neighbors: dict[int, list[int]] = {}
    for run in RUN_IDS:
        value = observed_run_score(args.asset_root, run)
        if value is not None:
            values[run] = value
            observed[run] = True

    observed_runs = sorted(values)
    missing_runs = sorted(set(RUN_IDS) - set(observed_runs))
    if not observed_runs:
        raise SystemExit(f"No complete targeted velocity-image sets found under {args.asset_root}")
    if missing_runs and args.no_impute:
        for run in missing_runs:
            observed[run] = False
            neighbors[run] = []
    else:
        for run in missing_runs:
            nearest = nearest_observed(features, observed_runs, run, args.neighbors)
            array = np.asarray([values[neighbor] for neighbor in nearest], dtype=float)
            values[run] = tuple(float(value) for value in array.mean(axis=0))  # type: ignore[assignment]
            observed[run] = False
            neighbors[run] = nearest

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "run",
            "image_wake_score",
            "image_wake_observed",
            "centreline_low_speed_area",
            "near_base_low_speed_area",
            "velocity_images",
            "velocity_slices",
            "imputation_neighbors",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for run in RUN_IDS:
            value = values.get(run)
            writer.writerow(
                {
                    "run": run,
                    "image_wake_score": "" if value is None else value[0],
                    "image_wake_observed": str(observed.get(run, False)).lower(),
                    "centreline_low_speed_area": "" if value is None else value[1],
                    "near_base_low_speed_area": "" if value is None else value[2],
                    "velocity_images": 0 if value is None or not observed.get(run, False) else int(value[3]),
                    "velocity_slices": "Z-4;Z-5;X-53;X-55;X-57",
                    "imputation_neighbors": ";".join(str(value) for value in neighbors.get(run, [])),
                }
            )
    print(f"Wrote {args.output}")
    print(f"Observed: {len(observed_runs)}; imputed/missing: {len(missing_runs)}")


if __name__ == "__main__":
    main()
