"""Generate deterministic train/validation/test splits for WindsorML.

Split families:
  1. full         - seed-42 random split, approximately 80/10/10
  2. medium       - same val/test as full, train is 1/3 subsample
  3. scarce       - same val/test as full, train is 1/6 subsample
  4. super_scarce - same val/test as full, train is 1/36 subsample
  5. geometry     - OOD STL-Chamfer local-isolation split
  6. high_drag    - OOD high-drag split from fixed-reference force coefficients
  7. low_drag     - OOD low-drag split from fixed-reference force coefficients
  8. image_wake   - OOD image-derived low-speed wake split

For every OOD split, validation is drawn from the training-side population so
model selection does not see the held-out extreme regime.
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
DATA_ROOT = Path(os.environ.get("WINDSORML_DATA_ROOT", DATA_DIR))
CHAMFER_METRICS = "chamfer_metrics.csv"
IMAGE_METRICS = "image_metrics.csv"

N_CASES = 355
RUN_IDS = list(range(N_CASES))
SEED = 42
FULL_TRAIN_COUNT = 284
FULL_VAL_COUNT = 35
FULL_TEST_COUNT = 36
MEDIUM_FRACTION = 1 / 3
SCARCE_FRACTION = 1 / 6
SUPER_SCARCE_FRACTION = 1 / 36
OOD_TEST_FRACTION = 0.2
VAL_FRACTION = 0.1
VAL_FRACTION_OF_POOL = VAL_FRACTION / (1 - OOD_TEST_FRACTION)


def case_id(run: int) -> str:
    return f"run_{run}"


def run_id(case: str) -> int:
    if not case.startswith("run_"):
        raise ValueError(f"Malformed case ID: {case!r}")
    return int(case.split("_", 1)[1])


def make_case_ids(values: list[int]) -> list[str]:
    return [case_id(value) for value in sorted(values)]


def _rng(salt: str) -> random.Random:
    seed_bytes = hashlib.sha256(f"{SEED}:{salt}".encode("utf-8")).digest()[:8]
    return random.Random(int.from_bytes(seed_bytes, "big"))


def _unit_hash(run: int, salt: str) -> float:
    seed = hashlib.sha256(f"{SEED}:{salt}:{run}".encode("utf-8")).digest()[:8]
    return int.from_bytes(seed, "big") / 2**64


# Generated once with torch.randperm(355, generator=torch.Generator().manual_seed(42)).
# The IDs are committed so split regeneration does not require PyTorch.
FULL_TRAIN_IDS = [
    0, 1, 2, 3, 4, 5, 6, 9, 10, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22, 24, 26, 29, 30, 31, 33, 34, 35,
    36, 38, 39, 40, 41, 42, 45, 48, 49, 52, 53, 54, 55, 59, 60, 61, 62, 63, 64, 65, 67, 68, 70, 71, 72, 73,
    74, 75, 76, 78, 79, 80, 81, 82, 84, 86, 87, 88, 90, 91, 92, 93, 96, 101, 102, 103, 105, 106, 107, 108,
    109, 110, 111, 112, 114, 115, 116, 117, 118, 119, 120, 121, 122, 124, 126, 127, 128, 129, 131, 132, 133,
    134, 135, 138, 140, 141, 142, 143, 144, 145, 146, 147, 150, 151, 152, 153, 154, 155, 157, 158, 159, 160,
    161, 162, 163, 164, 165, 166, 167, 169, 170, 171, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183,
    184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204,
    205, 206, 207, 208, 209, 211, 212, 213, 214, 215, 217, 218, 219, 220, 221, 223, 224, 225, 226, 227, 228,
    229, 230, 231, 233, 234, 235, 237, 238, 239, 240, 241, 243, 245, 246, 247, 248, 249, 251, 252, 254, 255,
    258, 259, 260, 261, 262, 263, 264, 265, 266, 268, 269, 271, 272, 275, 276, 277, 278, 280, 281, 282, 284,
    285, 286, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 301, 302, 303, 304, 306, 307, 308, 309,
    310, 311, 312, 313, 314, 315, 316, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 332,
    334, 335, 337, 338, 339, 340, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353,
]
FULL_VAL_IDS = [
    8, 11, 25, 27, 37, 43, 44, 46, 50, 51, 56, 57, 77, 83, 94, 99, 137, 149, 156, 168, 210, 222, 236, 242,
    244, 250, 267, 273, 274, 279, 287, 300, 305, 317, 331,
]
FULL_TEST_IDS = [
    7, 18, 23, 28, 32, 47, 58, 66, 69, 85, 89, 95, 97, 98, 100, 104, 113, 123, 125, 130, 136, 139, 148, 172,
    216, 232, 253, 256, 257, 270, 283, 299, 333, 336, 341, 354,
]


def _split_pool(pool: list[int], *, salt: str) -> tuple[list[int], list[int]]:
    shuffled = pool.copy()
    _rng(salt).shuffle(shuffled)
    n_val = round(len(pool) * VAL_FRACTION_OF_POOL)
    return sorted(shuffled[n_val:]), sorted(shuffled[:n_val])


def _candidate_paths(filename: str) -> list[Path]:
    roots = [DATA_ROOT, DATA_DIR, PACKAGE_ROOT, Path.cwd(), Path.cwd() / "data"]
    paths: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        path = root / filename
        key = path.resolve() if path.exists() else path.absolute()
        if key not in seen:
            paths.append(path)
            seen.add(key)
    return paths


def _clean_row(row: dict[str, str]) -> dict[str, str]:
    return {key.strip(): value.strip() for key, value in row.items() if key is not None}


def load_table(filename: str) -> tuple[dict[int, dict[str, float]], str]:
    for path in _candidate_paths(filename):
        if not path.exists():
            continue
        records: dict[int, dict[str, float]] = {}
        with path.open(encoding="utf-8-sig", newline="") as f:
            for raw in csv.DictReader(f):
                row = _clean_row(raw)
                records[int(row["run"])] = {key: float(value) for key, value in row.items() if key != "run"}
        missing = sorted(set(RUN_IDS) - set(records))
        if missing:
            raise ValueError(f"{path} is missing WindsorML runs: {missing}")
        return records, str(path)
    raise FileNotFoundError(f"{filename} not found; run scripts/download_hf_inputs.py")


def load_force_mom() -> tuple[dict[int, dict[str, float]], str]:
    records, source = load_table("force_mom_all.csv")
    required = {"cd", "cl"}
    if not required <= set(next(iter(records.values()))):
        raise ValueError(f"{source} must contain {sorted(required)}")
    return records, source


def load_geo_parameters() -> tuple[dict[int, dict[str, float]], str]:
    return load_table("geo_parameters_all.csv")


def _standardized_matrix(records: dict[int, dict[str, float]], fields: list[str], runs: list[int]) -> np.ndarray:
    matrix = np.asarray([[records[run][field] for field in fields] for run in runs], dtype=float)
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    stds[stds == 0.0] = 1.0
    return (matrix - means) / stds


def load_metric_scores(filename: str, column: str) -> tuple[dict[int, float], str]:
    for path in _candidate_paths(filename):
        if not path.exists():
            continue
        scores: dict[int, float] = {}
        with path.open(encoding="utf-8-sig", newline="") as f:
            for raw in csv.DictReader(f):
                row = _clean_row(raw)
                if row.get(column, ""):
                    scores[int(row["run"])] = float(row[column])
        missing = sorted(set(RUN_IDS) - set(scores))
        if missing:
            raise ValueError(f"{path} is missing {column} for runs: {missing}")
        return scores, str(path)
    raise FileNotFoundError(f"{filename} not found; compute it before running this generator")


def force_scores(records: dict[int, dict[str, float]]) -> dict[str, dict[int, float]]:
    cd = {run: row["cd"] for run, row in records.items()}
    return {"high_drag": cd, "low_drag": {run: -value for run, value in cd.items()}}


def ranked_ood_split(scores: dict[int, float], *, salt: str) -> tuple[list[int], list[int], list[int]]:
    ranked = sorted(scores, key=lambda run: (scores[run], run))
    n_test = round(len(ranked) * OOD_TEST_FRACTION)
    test = sorted(ranked[-n_test:])
    train, val = _split_pool(sorted(ranked[:-n_test]), salt=salt)
    return train, val, test


def diverse_training_order(
    force_records: dict[int, dict[str, float]],
    geo_records: dict[int, dict[str, float]],
) -> list[int]:
    feature_rows: dict[int, list[float]] = {run: [] for run in FULL_TRAIN_IDS}
    for field in ["cd", "cl"]:
        values = np.asarray([force_records[run][field] for run in FULL_TRAIN_IDS], dtype=float)
        mean, std = float(values.mean()), float(values.std()) or 1.0
        for run in FULL_TRAIN_IDS:
            feature_rows[run].append((force_records[run][field] - mean) / std)
    for field in sorted(next(iter(geo_records.values())).keys()):
        values = np.asarray([geo_records[run][field] for run in FULL_TRAIN_IDS], dtype=float)
        mean, std = float(values.mean()), float(values.std()) or 1.0
        for run in FULL_TRAIN_IDS:
            feature_rows[run].append((geo_records[run][field] - mean) / std)

    def distance(a: int, b: int) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(feature_rows[a], feature_rows[b])))

    first = max(
        FULL_TRAIN_IDS,
        key=lambda run: (
            math.sqrt(sum(value * value for value in feature_rows[run])),
            _unit_hash(run, "sparse_first_tie_break"),
        ),
    )
    selected = [first]
    remaining = [run for run in FULL_TRAIN_IDS if run != first]
    while remaining:
        next_run = max(
            remaining,
            key=lambda run: (
                min(distance(run, chosen) for chosen in selected),
                _unit_hash(run, "sparse_tie_break"),
            ),
        )
        selected.append(next_run)
        remaining.remove(next_run)
    return selected


def generate_splits() -> tuple[dict[str, list[str]], tuple[str, str, str, str]]:
    force_records, force_source = load_force_mom()
    geo_records, geo_source = load_geo_parameters()
    geometry_scores, geometry_source = load_metric_scores(CHAMFER_METRICS, "ood_score")
    image_scores, image_source = load_metric_scores(IMAGE_METRICS, "image_wake_score")

    splits: dict[str, list[str]] = {
        "full_train": make_case_ids(FULL_TRAIN_IDS),
        "full_val": make_case_ids(FULL_VAL_IDS),
        "full_test": make_case_ids(FULL_TEST_IDS),
    }
    order = diverse_training_order(force_records, geo_records)
    sizes = {
        "medium": round(len(FULL_TRAIN_IDS) * MEDIUM_FRACTION),
        "scarce": round(len(FULL_TRAIN_IDS) * SCARCE_FRACTION),
        "super_scarce": max(1, round(len(FULL_TRAIN_IDS) * SUPER_SCARCE_FRACTION)),
    }
    for name, size in sizes.items():
        splits[f"{name}_train"] = make_case_ids(order[:size])
        splits[f"{name}_val"] = splits["full_val"]
        splits[f"{name}_test"] = splits["full_test"]

    score_families = {**force_scores(force_records), "geometry": geometry_scores, "image_wake": image_scores}
    for name, scores in score_families.items():
        train, val, test = ranked_ood_split(scores, salt=f"{name}_val_selection")
        splits[f"{name}_train"] = make_case_ids(train)
        splits[f"{name}_val"] = make_case_ids(val)
        splits[f"{name}_test"] = make_case_ids(test)
    return splits, (force_source, geo_source, geometry_source, image_source)


def validate_splits(splits: dict[str, list[str]]) -> None:
    all_cases = {case_id(run) for run in RUN_IDS}
    families = sorted({key.rsplit("_", 1)[0] for key in splits})
    for name in families:
        train = set(splits[f"{name}_train"])
        val = set(splits[f"{name}_val"])
        test = set(splits[f"{name}_test"])
        assert not (train & val), f"{name}: train/val overlap"
        assert not (train & test), f"{name}: train/test overlap"
        assert not (val & test), f"{name}: val/test overlap"
        assert train | val | test <= all_cases, f"{name}: invalid run included"

    assert (len(splits["full_train"]), len(splits["full_val"]), len(splits["full_test"])) == (284, 35, 36)
    for name in ["medium", "scarce", "super_scarce"]:
        assert splits[f"{name}_val"] == splits["full_val"]
        assert splits[f"{name}_test"] == splits["full_test"]
    assert set(splits["super_scarce_train"]) < set(splits["scarce_train"])
    assert set(splits["scarce_train"]) < set(splits["medium_train"])
    assert set(splits["medium_train"]) < set(splits["full_train"])

    for name in ["full"]:
        sizes = tuple(len(splits[f"{name}_{part}"]) for part in ("train", "val", "test"))
        assert sizes == (284, 35, 36), f"{name}: unexpected sizes {sizes}"
        assert set().union(*(set(splits[f"{name}_{part}"]) for part in ("train", "val", "test"))) == all_cases
    for name in ["geometry", "high_drag", "low_drag", "image_wake"]:
        sizes = tuple(len(splits[f"{name}_{part}"]) for part in ("train", "val", "test"))
        assert sizes == (248, 36, 71), f"{name}: unexpected sizes {sizes}"
        assert set().union(*(set(splits[f"{name}_{part}"]) for part in ("train", "val", "test"))) == all_cases


def main() -> None:
    splits, sources = generate_splits()
    validate_splits(splits)
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    output = SPLITS_DIR / "manifest.json"
    output.write_text(json.dumps(splits, indent=4) + "\n", encoding="utf-8")

    print("WindsorML Splits")
    print("=" * 60)
    print(f"  Runs: {N_CASES}")
    print(f"  Seed: {SEED}")
    for label, source in zip(["Force/moment", "Geometry parameters", "STL-Chamfer", "Image wake"], sources):
        print(f"  {label} source: {source}")
    print()
    print(f"  {'Split':<18s} {'Train':>6s} {'Val':>6s} {'Test':>6s} {'Total':>6s}")
    print(f"  {'-' * 46}")
    for name in sorted({key.rsplit('_', 1)[0] for key in splits}):
        sizes = [len(splits[f"{name}_{part}"]) for part in ("train", "val", "test")]
        print(f"  {name:<18s} {sizes[0]:>6d} {sizes[1]:>6d} {sizes[2]:>6d} {sum(sizes):>6d}")
    print(f"\n  Manifest: {output}")
    print("All validations passed.")


if __name__ == "__main__":
    main()
