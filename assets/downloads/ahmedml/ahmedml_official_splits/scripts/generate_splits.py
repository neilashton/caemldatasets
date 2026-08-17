"""Generate deterministic train/val/test splits for the AhmedML dataset.

Outputs:
  - splits/manifest.json
  - data/parameter_geometry_metrics.csv

Split families:
  1. full         - Noether-compatible seed-42 random split, 400/50/50
  2. medium       - same val/test as full, train is 1/3 subsample
  3. scarce       - same val/test as full, train is 1/6 subsample
  4. super_scarce - same val/test as full, train is 1/36 subsample
  5. geometry     - OOD STL-Chamfer local-isolation split
  6. high_drag    - OOD high-drag split from force_mom_all.csv
  7. low_drag     - OOD low-drag split from force_mom_all.csv
  8. image_wake   - OOD image-derived wake split from UxMean PNGs

For every OOD split, the validation set is drawn from the training-side
population so hyperparameter tuning does not see the held-out extreme regime.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import random
from pathlib import Path

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
DATA_DIR = PACKAGE_ROOT / "data"
SPLITS_DIR = PACKAGE_ROOT / "splits"
DATA_ROOT = Path(os.environ.get("AHMEDML_DATA_ROOT", DATA_DIR))
CHAMFER_METRICS = "chamfer_metrics.csv"
IMAGE_METRICS = "image_metrics.csv"
PARAMETER_GEOMETRY_METRICS = "parameter_geometry_metrics.csv"

N_CASES = 500
RUN_IDS = list(range(1, N_CASES + 1))
SEED = 42
MEDIUM_FRACTION = 1 / 3
SCARCE_FRACTION = 1 / 6
SUPER_SCARCE_FRACTION = 1 / 36
OOD_TEST_FRACTION = 0.2
VAL_FRACTION = 0.1
TEST_FRACTION = 0.2
VAL_FRACTION_OF_POOL = VAL_FRACTION / (1 - TEST_FRACTION)


# Noether AhmedMLDefaultSplitIDs, generated from torch.randperm(500) with seed
# 42. AhmedML has no hidden-test exclusion in that default split.
FULL_TRAIN_IDS = [
    1, 2, 3, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 21, 23, 25, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 39, 40,
    42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 57, 58, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72,
    73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100,
    101, 102, 103, 105, 106, 107, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 125, 126,
    128, 129, 130, 131, 132, 134, 135, 136, 137, 138, 139, 140, 141, 143, 144, 145, 146, 147, 148, 149, 151, 152,
    153, 154, 155, 156, 157, 159, 160, 161, 162, 163, 164, 166, 167, 168, 169, 170, 171, 172, 174, 175, 176, 178,
    179, 181, 182, 183, 184, 185, 186, 189, 190, 192, 193, 194, 195, 198, 200, 201, 202, 204, 206, 209, 211, 212,
    213, 214, 216, 217, 218, 219, 220, 221, 223, 224, 225, 227, 229, 231, 232, 233, 235, 236, 237, 238, 239, 240,
    242, 243, 244, 245, 246, 248, 249, 250, 251, 254, 255, 256, 257, 259, 261, 262, 264, 265, 266, 267, 268, 269,
    270, 272, 273, 274, 276, 277, 278, 279, 282, 283, 285, 286, 287, 288, 289, 292, 293, 294, 296, 297, 299, 300,
    301, 302, 305, 306, 307, 308, 309, 310, 313, 314, 315, 316, 317, 318, 319, 320, 323, 325, 326, 327, 330, 331,
    332, 333, 334, 335, 336, 338, 339, 340, 342, 343, 344, 345, 346, 347, 348, 349, 351, 353, 355, 356, 357, 358,
    359, 360, 361, 362, 365, 367, 368, 369, 370, 371, 373, 374, 375, 377, 378, 379, 381, 383, 384, 385, 386, 388,
    389, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 402, 404, 406, 407, 408, 409, 411, 412, 413, 414, 415,
    416, 417, 418, 419, 420, 421, 422, 425, 426, 427, 430, 431, 433, 434, 435, 437, 438, 439, 440, 442, 443, 444,
    445, 446, 448, 449, 450, 451, 452, 453, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469,
    470, 471, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 488, 489, 490, 491, 492, 493,
    495, 496, 497, 498, 499, 500,
]

FULL_VAL_IDS = [
    24, 26, 29, 38, 41, 55, 59, 104, 108, 124, 133, 142, 158, 173, 180, 188, 196, 197, 199, 205, 207, 210, 222, 226,
    230, 258, 263, 280, 281, 284, 290, 291, 295, 304, 312, 337, 350, 354, 363, 372, 387, 403, 405, 424, 428, 429,
    432, 455, 472, 494,
]

FULL_TEST_IDS = [
    4, 11, 12, 19, 20, 22, 56, 109, 127, 150, 165, 177, 187, 191, 203, 208, 215, 228, 234, 241, 247, 252, 253, 260,
    271, 275, 298, 303, 311, 321, 322, 324, 328, 329, 341, 352, 364, 366, 376, 380, 382, 390, 401, 410, 423, 436,
    441, 447, 454, 487,
]


def case_id(run_id: int) -> str:
    return f"run_{run_id}"


def run_id(case_id_value: str) -> int:
    if not case_id_value.startswith("run_"):
        raise ValueError(f"Malformed case ID: {case_id_value!r}")
    return int(case_id_value.split("_", 1)[1])


def make_case_ids(values: list[int]) -> list[str]:
    return [case_id(value) for value in sorted(values)]


def _rng(salt: str) -> random.Random:
    seed_bytes = hashlib.sha256(f"{SEED}:{salt}".encode("utf-8")).digest()[:8]
    return random.Random(int.from_bytes(seed_bytes, "big"))


def _unit_hash(run: int, salt: str) -> float:
    seed = hashlib.sha256(f"{SEED}:{salt}:{run}".encode("utf-8")).digest()[:8]
    return int.from_bytes(seed, "big") / 2**64


def _split_pool(pool: list[int], *, salt: str) -> tuple[list[int], list[int]]:
    shuffled = pool.copy()
    _rng(salt).shuffle(shuffled)
    n_val = round(len(pool) * VAL_FRACTION_OF_POOL)
    val = sorted(shuffled[:n_val])
    train = sorted(shuffled[n_val:])
    return train, val


def _candidate_paths(filename: str) -> list[Path]:
    roots = [
        DATA_ROOT,
        DATA_ROOT / "dataset",
        DATA_DIR,
        DATA_DIR / "dataset",
        PACKAGE_ROOT,
        PACKAGE_ROOT / "dataset",
        Path.cwd(),
        Path.cwd() / "data",
    ]
    seen: set[Path] = set()
    paths: list[Path] = []
    for root in roots:
        path = root / filename
        key = path.resolve() if path.exists() else path.absolute()
        if key not in seen:
            paths.append(path)
            seen.add(key)
    return paths


def _clean_row(row: dict[str, str]) -> dict[str, str]:
    return {key.strip(): value.strip() for key, value in row.items() if key is not None}


def _float(value: str) -> float:
    return float(value.replace(" ", ""))


def load_force_mom() -> tuple[dict[int, dict[str, float]], str]:
    for path in _candidate_paths("force_mom_all.csv"):
        if not path.exists():
            continue
        records: dict[int, dict[str, float]] = {}
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                clean = _clean_row(row)
                rid = int(clean["run"])
                records[rid] = {"cd": _float(clean["cd"]), "cl": _float(clean["cl"])}
        missing = sorted(set(RUN_IDS) - set(records))
        if missing:
            raise ValueError(f"{path} is missing run IDs: {missing[:10]}")
        return records, str(path)
    raise FileNotFoundError("force_mom_all.csv not found; run scripts/download_hf_inputs.py")


def load_geo_parameters() -> tuple[dict[int, dict[str, float]], dict[int, bool], str]:
    for path in _candidate_paths("geo_parameters_all.csv"):
        if not path.exists():
            continue
        observed_records: dict[int, dict[str, float]] = {}
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                clean = _clean_row(row)
                rid = int(clean["run"])
                observed_records[rid] = {
                    key: _float(value)
                    for key, value in clean.items()
                    if key != "run"
                }
        if not observed_records:
            raise ValueError(f"{path} has no geometry rows")

        keys = sorted(next(iter(observed_records.values())).keys())
        means = {
            key: float(np.mean([record[key] for record in observed_records.values()]))
            for key in keys
        }
        records: dict[int, dict[str, float]] = {}
        observed: dict[int, bool] = {}
        for rid in RUN_IDS:
            if rid in observed_records:
                records[rid] = observed_records[rid]
                observed[rid] = True
            else:
                records[rid] = means.copy()
                observed[rid] = False
        return records, observed, str(path)
    raise FileNotFoundError("geo_parameters_all.csv not found; run scripts/download_hf_inputs.py")


def _standardized_matrix(records: dict[int, dict[str, float]], fields: list[str], runs: list[int]) -> np.ndarray:
    matrix = np.asarray([[records[rid][field] for field in fields] for rid in runs], dtype=float)
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    stds[stds == 0.0] = 1.0
    return (matrix - means) / stds


def _pairwise_distances(matrix: np.ndarray) -> np.ndarray:
    diff = matrix[:, None, :] - matrix[None, :, :]
    return np.sqrt(np.sum(diff * diff, axis=2))


def geometry_isolation_scores(
    geo_records: dict[int, dict[str, float]],
) -> tuple[dict[int, float], dict[int, float]]:
    runs = RUN_IDS.copy()
    fields = sorted(next(iter(geo_records.values())).keys())
    matrix = _standardized_matrix(geo_records, fields, runs)
    distances = _pairwise_distances(matrix)
    np.fill_diagonal(distances, np.inf)
    nearest_10 = np.sort(distances, axis=1)[:, :10]
    finite = np.where(np.isfinite(distances), distances, np.nan)
    mean_10 = nearest_10.mean(axis=1)
    mean_all = np.nanmean(finite, axis=1)
    return (
        {rid: float(mean_10[idx]) for idx, rid in enumerate(runs)},
        {rid: float(mean_all[idx]) for idx, rid in enumerate(runs)},
    )


def write_parameter_geometry_metrics(
    scores: dict[int, float],
    mean_all: dict[int, float],
    observed: dict[int, bool],
) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / PARAMETER_GEOMETRY_METRICS
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run",
                "geometry_observed",
                "ood_score",
                "mean_10_nn_parameter_distance",
                "mean_all_parameter_distance",
            ],
        )
        writer.writeheader()
        for rid in RUN_IDS:
            writer.writerow(
                {
                    "run": rid,
                    "geometry_observed": str(observed[rid]).lower(),
                    "ood_score": scores[rid],
                    "mean_10_nn_parameter_distance": scores[rid],
                    "mean_all_parameter_distance": mean_all[rid],
                }
            )


def load_metric_scores(
    filename: str,
    value_column: str,
    *,
    observed_column: str | None = None,
) -> tuple[dict[int, float], str]:
    for path in _candidate_paths(filename):
        if not path.exists():
            continue
        scores: dict[int, float] = {}
        unobserved: list[int] = []
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                clean = _clean_row(row)
                rid = int(clean["run"])
                if observed_column and clean.get(observed_column, "true").lower() != "true":
                    unobserved.append(rid)
                    continue
                value = clean.get(value_column, "")
                if value == "":
                    unobserved.append(rid)
                    continue
                scores[rid] = _float(value)
        missing = sorted(set(RUN_IDS) - set(scores))
        if missing or unobserved:
            missing_preview = ", ".join(str(x) for x in (missing + unobserved)[:12])
            raise ValueError(
                f"{path} does not contain complete observed {value_column} scores; "
                f"missing/unobserved runs include: {missing_preview}"
            )
        return scores, str(path)
    raise FileNotFoundError(f"{filename} not found; compute it before running this generator")


def load_chamfer_scores() -> tuple[dict[int, float], str]:
    return load_metric_scores(CHAMFER_METRICS, "ood_score")


def load_image_wake_scores() -> tuple[dict[int, float], str]:
    return load_metric_scores(IMAGE_METRICS, "image_wake_score", observed_column="image_wake_observed")


def force_scores(records: dict[int, dict[str, float]]) -> dict[str, dict[int, float]]:
    cd = {rid: row["cd"] for rid, row in records.items()}
    return {
        "high_drag": cd,
        "low_drag": {rid: -value for rid, value in cd.items()},
    }


def ranked_ood_split(scores: dict[int, float], *, salt: str) -> tuple[list[int], list[int], list[int]]:
    ranked = sorted(scores, key=lambda rid: (scores[rid], rid))
    n_test = round(len(ranked) * OOD_TEST_FRACTION)
    test = sorted(ranked[-n_test:])
    pool = sorted(ranked[:-n_test])
    train, val = _split_pool(pool, salt=salt)
    return train, val, test


def diverse_training_order(
    force_records: dict[int, dict[str, float]],
    geo_records: dict[int, dict[str, float]],
) -> list[int]:
    train_pool = FULL_TRAIN_IDS.copy()
    feature_rows: dict[int, list[float]] = {rid: [] for rid in train_pool}

    for field in ["cd", "cl"]:
        values = np.asarray([force_records[rid][field] for rid in train_pool], dtype=float)
        mean = float(values.mean())
        std = float(values.std()) or 1.0
        for rid in train_pool:
            feature_rows[rid].append((force_records[rid][field] - mean) / std)

    for field in sorted(next(iter(geo_records.values())).keys()):
        values = np.asarray([geo_records[rid][field] for rid in train_pool], dtype=float)
        mean = float(values.mean())
        std = float(values.std()) or 1.0
        for rid in train_pool:
            feature_rows[rid].append((geo_records[rid][field] - mean) / std)

    def distance(a: int, b: int) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(feature_rows[a], feature_rows[b])))

    first = max(
        train_pool,
        key=lambda rid: (
            math.sqrt(sum(value * value for value in feature_rows[rid])),
            _unit_hash(rid, "scarce_first_tie_break"),
        ),
    )
    selected = [first]
    remaining = [rid for rid in train_pool if rid != first]
    while remaining:
        next_rid = max(
            remaining,
            key=lambda rid: (
                min(distance(rid, chosen) for chosen in selected),
                _unit_hash(rid, "scarce_tie_break"),
            ),
        )
        selected.append(next_rid)
        remaining.remove(next_rid)
    return selected


def _validate_noether_full_split() -> None:
    groups = {
        "full_train": FULL_TRAIN_IDS,
        "full_val": FULL_VAL_IDS,
        "full_test": FULL_TEST_IDS,
    }
    seen: dict[int, str] = {}
    for name, ids in groups.items():
        if len(ids) != len(set(ids)):
            raise AssertionError(f"{name} contains duplicate run IDs")
        for rid in ids:
            if rid < 1 or rid > N_CASES:
                raise AssertionError(f"{name} has invalid run ID {rid}")
            if rid in seen:
                raise AssertionError(f"run {rid} appears in {seen[rid]} and {name}")
            seen[rid] = name
    if set(seen) != set(RUN_IDS):
        raise AssertionError("full split does not cover all AhmedML runs")
    if (len(FULL_TRAIN_IDS), len(FULL_VAL_IDS), len(FULL_TEST_IDS)) != (400, 50, 50):
        raise AssertionError("unexpected full split sizes")


def generate_splits() -> tuple[dict[str, list[str]], str, str, str, str]:
    _validate_noether_full_split()
    force_records, force_source = load_force_mom()
    geo_records, geo_observed, geo_source = load_geo_parameters()
    parameter_geometry_scores, parameter_geometry_mean_all = geometry_isolation_scores(geo_records)
    write_parameter_geometry_metrics(parameter_geometry_scores, parameter_geometry_mean_all, geo_observed)
    geometry_scores, geometry_source = load_chamfer_scores()
    image_wake_scores, image_source = load_image_wake_scores()

    splits: dict[str, list[str]] = {}
    splits["full_train"] = make_case_ids(FULL_TRAIN_IDS)
    splits["full_val"] = make_case_ids(FULL_VAL_IDS)
    splits["full_test"] = make_case_ids(FULL_TEST_IDS)

    order = diverse_training_order(force_records, geo_records)
    n_medium = round(len(FULL_TRAIN_IDS) * MEDIUM_FRACTION)
    n_scarce = round(len(FULL_TRAIN_IDS) * SCARCE_FRACTION)
    n_super_scarce = round(len(FULL_TRAIN_IDS) * SUPER_SCARCE_FRACTION)
    splits["medium_train"] = make_case_ids(sorted(order[:n_medium]))
    splits["medium_val"] = splits["full_val"]
    splits["medium_test"] = splits["full_test"]
    splits["scarce_train"] = make_case_ids(sorted(order[:n_scarce]))
    splits["scarce_val"] = splits["full_val"]
    splits["scarce_test"] = splits["full_test"]
    splits["super_scarce_train"] = make_case_ids(sorted(order[:n_super_scarce]))
    splits["super_scarce_val"] = splits["full_val"]
    splits["super_scarce_test"] = splits["full_test"]

    for name, scores in force_scores(force_records).items():
        train, val, test = ranked_ood_split(scores, salt=f"{name}_val_selection")
        splits[f"{name}_train"] = make_case_ids(train)
        splits[f"{name}_val"] = make_case_ids(val)
        splits[f"{name}_test"] = make_case_ids(test)

    train, val, test = ranked_ood_split(geometry_scores, salt="geometry_val_selection")
    splits["geometry_train"] = make_case_ids(train)
    splits["geometry_val"] = make_case_ids(val)
    splits["geometry_test"] = make_case_ids(test)

    train, val, test = ranked_ood_split(image_wake_scores, salt="image_wake_val_selection")
    splits["image_wake_train"] = make_case_ids(train)
    splits["image_wake_val"] = make_case_ids(val)
    splits["image_wake_test"] = make_case_ids(test)
    return splits, force_source, geo_source, geometry_source, image_source


def validate_splits(splits: dict[str, list[str]]) -> None:
    all_cases = {case_id(rid) for rid in RUN_IDS}
    split_names = sorted({key.rsplit("_", 1)[0] for key in splits})
    for name in split_names:
        train = set(splits[f"{name}_train"])
        val = set(splits[f"{name}_val"])
        test = set(splits[f"{name}_test"])
        assert not (train & val), f"{name}: train/val overlap"
        assert not (train & test), f"{name}: train/test overlap"
        assert not (val & test), f"{name}: val/test overlap"
        assert train | val | test <= all_cases, f"{name}: non-AhmedML run included"

    assert (len(splits["full_train"]), len(splits["full_val"]), len(splits["full_test"])) == (400, 50, 50)
    for prefix in ["medium", "scarce", "super_scarce"]:
        assert splits[f"{prefix}_val"] == splits["full_val"], f"{prefix}_val must equal full_val"
        assert splits[f"{prefix}_test"] == splits["full_test"], f"{prefix}_test must equal full_test"

    assert set(splits["super_scarce_train"]) < set(splits["scarce_train"])
    assert set(splits["scarce_train"]) < set(splits["medium_train"])
    assert set(splits["medium_train"]) < set(splits["full_train"])

    for prefix in ["full", "geometry", "high_drag", "low_drag", "image_wake"]:
        total = len(splits[f"{prefix}_train"]) + len(splits[f"{prefix}_val"]) + len(splits[f"{prefix}_test"])
        assert total == N_CASES, f"{prefix}: expected {N_CASES} cases, got {total}"

    for prefix in ["geometry", "high_drag", "low_drag", "image_wake"]:
        assert (
            len(splits[f"{prefix}_train"]),
            len(splits[f"{prefix}_val"]),
            len(splits[f"{prefix}_test"]),
        ) == (350, 50, 100), f"{prefix}: unexpected OOD split sizes"


def main() -> None:
    splits, force_source, geo_source, geometry_source, image_source = generate_splits()
    validate_splits(splits)

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    output = SPLITS_DIR / "manifest.json"
    output.write_text(json.dumps(splits, indent=4) + "\n", encoding="utf-8")

    print("AhmedML Splits")
    print("=" * 60)
    print(f"  Runs: {N_CASES}")
    print(f"  Seed: {SEED}")
    print(f"  Force/moment source: {force_source}")
    print(f"  Geometry-parameter source: {geo_source}")
    print(f"  STL-Chamfer source: {geometry_source}")
    print(f"  Image-wake source: {image_source}")
    print()
    print(f"  {'Split':<18s} {'Train':>6s} {'Val':>6s} {'Test':>6s} {'Total':>6s}")
    print(f"  {'-' * 46}")
    for name in sorted({key.rsplit('_', 1)[0] for key in splits}):
        n_train = len(splits[f"{name}_train"])
        n_val = len(splits[f"{name}_val"])
        n_test = len(splits[f"{name}_test"])
        print(f"  {name:<18s} {n_train:>6d} {n_val:>6d} {n_test:>6d} {n_train + n_val + n_test:>6d}")
    print()
    print(f"  Manifest: {output}")
    print(f"  STL-Chamfer metrics: {DATA_DIR / CHAMFER_METRICS}")
    print(f"  Image metrics: {DATA_DIR / IMAGE_METRICS}")
    print(f"  Parameter geometry metrics: {DATA_DIR / PARAMETER_GEOMETRY_METRICS}")
    print(f"  Keys: {len(splits)}")
    print("All validations passed.")


if __name__ == "__main__":
    main()
