#!/usr/bin/env python3
"""Compute STL-based Chamfer geometry splits for WindsorML.

This is intentionally standalone so it can be copied to the machine that has
the STL files. It expects a WindsorML-style directory layout:

    DATA_ROOT/
      run_0/windsor_0.stl
      run_1/windsor_1.stl
      ...

Outputs:
  - sampled point clouds cached as NPZ files
  - chamfer_metrics.csv with nearest-neighbor and outlier scores
  - chamfer_manifest.json with geometry_{train,val,test}
  - optional chamfer_distance_matrix.npy, a symmetric NxN float32 matrix
  - optional sparse train subsets when a base manifest with full_train exists

Install dependencies on the data machine:

    python -m pip install numpy scipy trimesh

Example:

    python compute_chamfer_splits.py \
      --data-root ../windsorml_hf_assets \
      --output-dir /tmp/windsorml_chamfer \
      --samples 4096 \
      --workers 16 \
      --allow-missing
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


N_CASES = 355
PUBLIC_RUN_IDS = list(range(N_CASES))
DEFAULT_TEST_FRACTION = 0.2
DEFAULT_VAL_FRACTION = 0.1
DEFAULT_SEED = 42
cKDTree = None
trimesh = None


@dataclass(frozen=True)
class RunFile:
    run_id: int
    stl_path: Path


def case_id(run_id: int) -> str:
    return f"run_{run_id}"


def run_id(case: str) -> int:
    if not case.startswith("run_"):
        raise ValueError(f"bad case id: {case!r}")
    return int(case.split("_", 1)[1])


def require_dependencies() -> None:
    global cKDTree, trimesh
    try:
        from scipy.spatial import cKDTree as scipy_ckdtree
    except Exception as exc:  # pragma: no cover - dependency guard
        raise SystemExit(
            "Missing dependency scipy. Install with: python -m pip install numpy scipy trimesh"
        ) from exc
    try:
        import trimesh as trimesh_module
    except Exception as exc:  # pragma: no cover - dependency guard
        raise SystemExit(
            "Missing dependency trimesh. Install with: python -m pip install numpy scipy trimesh"
        ) from exc
    cKDTree = scipy_ckdtree
    trimesh = trimesh_module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute STL-surface Chamfer distances and WindsorML geometry splits.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        required=True,
        help="Directory containing run_N/windsor_N.stl files and aggregate CSVs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where matrices, metrics, and manifests will be written.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=4096,
        help="Surface sample count per STL. 4096 is a practical first pass; 10000+ is better for final splits.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Thread workers used for pairwise nearest-neighbor queries.",
    )
    parser.add_argument(
        "--sample-workers",
        type=int,
        default=1,
        help="Thread workers used while loading and sampling STLs.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Base random seed for deterministic surface sampling and split selection.",
    )
    parser.add_argument(
        "--k-neighbors",
        type=int,
        default=10,
        help="K used for the local-isolation geometry score.",
    )
    parser.add_argument(
        "--test-fraction",
        type=float,
        default=DEFAULT_TEST_FRACTION,
        help="Fraction held out as OOD test for geometry.",
    )
    parser.add_argument(
        "--val-fraction",
        type=float,
        default=DEFAULT_VAL_FRACTION,
        help="Overall validation fraction. Validation is sampled from the train-side pool.",
    )
    parser.add_argument(
        "--score",
        choices=["knn", "medoid", "mean"],
        default="knn",
        help="Score used to rank OOD geometry cases.",
    )
    parser.add_argument(
        "--center",
        choices=["none", "bbox", "centroid"],
        default="none",
        help="How to remove translation before Chamfer. Use none when STLs share a common coordinate frame.",
    )
    parser.add_argument(
        "--scale-mode",
        choices=["global_median_bbox", "per_mesh_bbox", "none"],
        default="global_median_bbox",
        help="How to scale coordinates before Chamfer. global_median_bbox keeps real relative vehicle size.",
    )
    parser.add_argument(
        "--runs",
        type=str,
        default="public",
        help=(
            "Run IDs to process: public, all, or a comma/range expression like "
            "0,1,10-20. For WindsorML, public and all both mean 0..354."
        ),
    )
    parser.add_argument(
        "--base-manifest",
        type=Path,
        default=None,
        help=(
            "Optional existing split manifest. If it contains full_train/full_val/full_test, "
            "the script also writes geometry_medium/scarce/super_scarce splits."
        ),
    )
    parser.add_argument(
        "--force-resample",
        action="store_true",
        help="Ignore cached point clouds and resample all STLs.",
    )
    parser.add_argument(
        "--force-matrix",
        action="store_true",
        help="Recompute the Chamfer matrix even if a compatible matrix already exists.",
    )
    parser.add_argument(
        "--write-matrix",
        action="store_true",
        help="Write chamfer_distance_matrix.npy and its metadata JSON. Omitted by default to keep the split package lean.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Process the subset of requested runs whose STLs exist. Without this, missing STLs are an error.",
    )
    parser.add_argument(
        "--write-csv-matrix",
        action="store_true",
        help="Also write chamfer_distance_matrix.csv from the in-memory matrix.",
    )
    return parser.parse_args()


def parse_run_expression(expr: str) -> list[int]:
    expr = expr.strip().lower()
    if expr == "public":
        return PUBLIC_RUN_IDS.copy()
    if expr == "all":
        return list(range(N_CASES))

    result: set[int] = set()
    for token in expr.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start_s, end_s = token.split("-", 1)
            start, end = int(start_s), int(end_s)
            if start > end:
                start, end = end, start
            result.update(range(start, end + 1))
        else:
            result.add(int(token))
    runs = sorted(result)
    bad = [rid for rid in runs if rid < 0 or rid >= N_CASES]
    if bad:
        raise SystemExit(f"Run IDs must be in 0..{N_CASES - 1}; bad values: {bad}")
    return runs


def discover_files(data_root: Path, requested_runs: Iterable[int], allow_missing: bool) -> list[RunFile]:
    files: list[RunFile] = []
    missing: list[int] = []
    for rid in requested_runs:
        path = data_root / f"run_{rid}" / f"windsor_{rid}.stl"
        if path.exists() and path.stat().st_size > 0:
            files.append(RunFile(rid, path))
        else:
            missing.append(rid)

    if missing and not allow_missing:
        preview = ", ".join(str(x) for x in missing[:20])
        suffix = " ..." if len(missing) > 20 else ""
        raise SystemExit(
            f"Missing {len(missing)} requested STL files under {data_root}: {preview}{suffix}\n"
            "Use --allow-missing to compute with the available subset."
        )
    if not files:
        raise SystemExit(f"No STL files found under {data_root}")
    return files


def load_mesh(path: Path) -> "trimesh.Trimesh":
    mesh = trimesh.load_mesh(path, process=False)
    if isinstance(mesh, trimesh.Scene):
        geometries = [g for g in mesh.geometry.values() if len(g.faces) > 0]
        if not geometries:
            raise ValueError(f"{path} did not contain any mesh geometry")
        mesh = trimesh.util.concatenate(geometries)
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError(f"{path} loaded as unsupported object: {type(mesh)!r}")
    if len(mesh.faces) == 0:
        raise ValueError(f"{path} has no faces")
    return mesh


def sample_mesh_surface(mesh: "trimesh.Trimesh", count: int, seed: int) -> np.ndarray:
    """Area-sample points from a triangular mesh using a local RNG."""
    rng = np.random.default_rng(seed)
    areas = np.asarray(mesh.area_faces, dtype=np.float64)
    total_area = float(np.sum(areas))
    if not math.isfinite(total_area) or total_area <= 0.0:
        raise ValueError("mesh surface area is zero or invalid")

    face_indices = rng.choice(len(mesh.faces), size=count, replace=True, p=areas / total_area)
    triangles = np.asarray(mesh.vertices[mesh.faces[face_indices]], dtype=np.float64)

    u = rng.random(count)
    v = rng.random(count)
    outside = (u + v) > 1.0
    u[outside] = 1.0 - u[outside]
    v[outside] = 1.0 - v[outside]
    points = triangles[:, 0] + u[:, None] * (triangles[:, 1] - triangles[:, 0]) + v[:, None] * (
        triangles[:, 2] - triangles[:, 0]
    )
    return np.asarray(points, dtype=np.float32)


def cache_path(cache_dir: Path, run: RunFile, samples: int, seed: int) -> Path:
    source = f"{run.stl_path.resolve()}:{run.stl_path.stat().st_size}:{samples}:{seed}:{run.run_id}"
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    return cache_dir / f"run_{run.run_id:03d}_samples_{samples}_{digest}.npz"


def sample_one(run: RunFile, cache_dir: Path, samples: int, seed: int, force: bool) -> tuple[int, np.ndarray, np.ndarray, np.ndarray]:
    cache = cache_path(cache_dir, run, samples, seed)
    if cache.exists() and not force:
        data = np.load(cache)
        points = np.asarray(data["points"], dtype=np.float32)
        bbox_min = np.asarray(data["bbox_min"], dtype=np.float32)
        bbox_max = np.asarray(data["bbox_max"], dtype=np.float32)
        if points.shape == (samples, 3):
            return run.run_id, points, bbox_min, bbox_max

    mesh = load_mesh(run.stl_path)
    points = sample_mesh_surface(mesh, samples, seed + run.run_id)
    bbox_min = np.asarray(mesh.bounds[0], dtype=np.float32)
    bbox_max = np.asarray(mesh.bounds[1], dtype=np.float32)
    np.savez_compressed(
        cache,
        run_id=np.asarray(run.run_id, dtype=np.int32),
        points=points,
        bbox_min=bbox_min,
        bbox_max=bbox_max,
        source=str(run.stl_path),
        samples=np.asarray(samples, dtype=np.int32),
        seed=np.asarray(seed, dtype=np.int32),
    )
    return run.run_id, points, bbox_min, bbox_max


def sample_point_clouds(
    runs: list[RunFile],
    cache_dir: Path,
    samples: int,
    seed: int,
    workers: int,
    force: bool,
) -> tuple[list[int], list[np.ndarray], np.ndarray, np.ndarray]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    print(f"Sampling/caching {len(runs)} STL point clouds with {samples} points each...")

    outputs: list[tuple[int, np.ndarray, np.ndarray, np.ndarray]] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = [pool.submit(sample_one, run, cache_dir, samples, seed, force) for run in runs]
        for idx, future in enumerate(as_completed(futures), start=1):
            outputs.append(future.result())
            if idx == len(futures) or idx % 25 == 0:
                print(f"  sampled {idx}/{len(futures)}")

    outputs.sort(key=lambda x: x[0])
    run_ids = [x[0] for x in outputs]
    clouds = [x[1] for x in outputs]
    bbox_min = np.stack([x[2] for x in outputs])
    bbox_max = np.stack([x[3] for x in outputs])
    print(f"Sampling complete in {time.time() - started:.1f}s")
    return run_ids, clouds, bbox_min, bbox_max


def normalize_clouds(
    clouds: list[np.ndarray],
    bbox_min: np.ndarray,
    bbox_max: np.ndarray,
    center: str,
    scale_mode: str,
) -> tuple[list[np.ndarray], dict[str, float | str]]:
    result: list[np.ndarray] = []
    bbox_diag = np.linalg.norm(bbox_max - bbox_min, axis=1)
    global_scale = float(np.median(bbox_diag))
    if not math.isfinite(global_scale) or global_scale <= 0:
        global_scale = 1.0

    for idx, points in enumerate(clouds):
        pts = points.astype(np.float32, copy=True)
        if center == "bbox":
            pts -= ((bbox_min[idx] + bbox_max[idx]) * 0.5).astype(np.float32)
        elif center == "centroid":
            pts -= pts.mean(axis=0, keepdims=True)

        if scale_mode == "global_median_bbox":
            scale = global_scale
        elif scale_mode == "per_mesh_bbox":
            scale = float(bbox_diag[idx]) if bbox_diag[idx] > 0 else 1.0
        else:
            scale = 1.0
        pts /= np.float32(scale)
        result.append(pts)

    metadata: dict[str, float | str] = {
        "center": center,
        "scale_mode": scale_mode,
        "global_median_bbox_diag": global_scale,
    }
    return result, metadata


def pair_chamfer_rms(i: int, j: int, clouds: list[np.ndarray], trees: list[cKDTree]) -> tuple[int, int, float]:
    a_to_b, _ = trees[j].query(clouds[i], k=1)
    b_to_a, _ = trees[i].query(clouds[j], k=1)
    chamfer = float(np.sqrt(0.5 * (np.mean(a_to_b * a_to_b) + np.mean(b_to_a * b_to_a))))
    return i, j, chamfer


def matrix_metadata_path(output_dir: Path) -> Path:
    return output_dir / "chamfer_distance_matrix.meta.json"


def matrix_is_compatible(output_dir: Path, run_ids: list[int], args: argparse.Namespace) -> bool:
    matrix_path = output_dir / "chamfer_distance_matrix.npy"
    meta_path = matrix_metadata_path(output_dir)
    if not matrix_path.exists() or not meta_path.exists():
        return False
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return (
        meta.get("run_ids") == run_ids
        and meta.get("samples") == args.samples
        and meta.get("seed") == args.seed
        and meta.get("center") == args.center
        and meta.get("scale_mode") == args.scale_mode
        and meta.get("metric") == "symmetric_chamfer_rms"
    )


def compute_chamfer_matrix(
    run_ids: list[int],
    clouds: list[np.ndarray],
    output_dir: Path,
    args: argparse.Namespace,
    normalization_metadata: dict[str, float | str],
) -> np.ndarray:
    matrix_path = output_dir / "chamfer_distance_matrix.npy"
    if matrix_is_compatible(output_dir, run_ids, args) and not args.force_matrix:
        print(f"Loading existing compatible matrix: {matrix_path}")
        return np.load(matrix_path)

    n = len(clouds)
    print(f"Building {n} KD trees...")
    trees = [cKDTree(points) for points in clouds]
    matrix = np.zeros((n, n), dtype=np.float32)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    started = time.time()
    print(f"Computing {len(pairs)} pairwise symmetric Chamfer RMS distances...")

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(pair_chamfer_rms, i, j, clouds, trees) for i, j in pairs]
        for done, future in enumerate(as_completed(futures), start=1):
            i, j, value = future.result()
            matrix[i, j] = matrix[j, i] = np.float32(value)
            if done == len(futures) or done % 1000 == 0:
                elapsed = time.time() - started
                rate = done / elapsed if elapsed > 0 else 0.0
                remaining = (len(futures) - done) / rate if rate > 0 else float("nan")
                print(
                    f"  pairs {done}/{len(futures)} "
                    f"({100 * done / len(futures):5.1f}%), ETA {remaining / 60:5.1f} min"
                )

    if args.write_matrix:
        np.save(matrix_path, matrix)
        metadata = {
            "run_ids": run_ids,
            "samples": args.samples,
            "seed": args.seed,
            "center": args.center,
            "scale_mode": args.scale_mode,
            "metric": "symmetric_chamfer_rms",
            "created_unix_time": time.time(),
            **normalization_metadata,
        }
        matrix_metadata_path(output_dir).write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        print(f"Matrix written: {matrix_path}")
    return matrix


def write_csv_matrix(path: Path, run_ids: list[int], matrix: np.ndarray) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["run", *[case_id(rid) for rid in run_ids]])
        for rid, row in zip(run_ids, matrix):
            writer.writerow([case_id(rid), *[f"{float(x):.8g}" for x in row]])


def metric_values(run_ids: list[int], matrix: np.ndarray, k_neighbors: int) -> tuple[list[dict[str, float | int]], dict[int, float]]:
    n = len(run_ids)
    if n < 2:
        raise SystemExit("At least two STL files are required to compute Chamfer metrics")
    k = min(max(1, k_neighbors), n - 1)
    means = matrix.sum(axis=1) / (n - 1)
    medoid_index = int(np.argmin(means))
    medoid_run = run_ids[medoid_index]
    rows: list[dict[str, float | int]] = []
    knn_scores: dict[int, float] = {}

    for idx, rid in enumerate(run_ids):
        nonself = np.delete(matrix[idx], idx)
        sorted_dist = np.sort(nonself)
        nearest = float(sorted_dist[0])
        knn_mean = float(np.mean(sorted_dist[:k]))
        mean_all = float(means[idx])
        medoid_distance = float(matrix[idx, medoid_index])
        knn_scores[rid] = knn_mean
        rows.append(
            {
                "run": rid,
                "nearest_neighbor_chamfer": nearest,
                f"mean_{k}_nn_chamfer": knn_mean,
                "mean_all_chamfer": mean_all,
                "medoid_chamfer": medoid_distance,
                "medoid_run": medoid_run,
            }
        )
    return rows, knn_scores


def score_map(
    run_ids: list[int],
    matrix: np.ndarray,
    metrics: list[dict[str, float | int]],
    score_name: str,
    k_neighbors: int,
) -> dict[int, float]:
    if score_name == "knn":
        key = f"mean_{min(max(1, k_neighbors), len(run_ids) - 1)}_nn_chamfer"
    elif score_name == "medoid":
        key = "medoid_chamfer"
    else:
        key = "mean_all_chamfer"
    return {int(row["run"]): float(row[key]) for row in metrics}


def split_pool(pool: list[int], val_fraction_of_pool: float, seed: int, salt: str) -> tuple[list[int], list[int]]:
    rng_seed = hashlib.sha256(f"{seed}:{salt}".encode("utf-8")).digest()[:8]
    rng = random.Random(int.from_bytes(rng_seed, "big"))
    shuffled = pool.copy()
    rng.shuffle(shuffled)
    n_val = round(len(pool) * val_fraction_of_pool)
    val = sorted(shuffled[:n_val])
    train = sorted(shuffled[n_val:])
    return train, val


def ranked_ood_split(
    scores: dict[int, float],
    test_fraction: float,
    val_fraction: float,
    seed: int,
    salt: str,
) -> tuple[list[int], list[int], list[int]]:
    ranked = sorted(scores, key=lambda rid: (scores[rid], rid))
    n_test = round(len(ranked) * test_fraction)
    test = sorted(ranked[-n_test:])
    pool = sorted(ranked[:-n_test])
    val_fraction_of_pool = val_fraction / (1.0 - test_fraction)
    train, val = split_pool(pool, val_fraction_of_pool, seed, salt)
    return train, val, test


def make_case_ids(values: Iterable[int]) -> list[str]:
    return [case_id(rid) for rid in sorted(values)]


def farthest_order(pool: list[int], run_to_index: dict[int, int], matrix: np.ndarray, seed: int) -> list[int]:
    if not pool:
        return []

    mean_dist = {
        rid: float(np.mean([matrix[run_to_index[rid], run_to_index[other]] for other in pool if other != rid]))
        for rid in pool
    }
    first = max(pool, key=lambda rid: (mean_dist[rid], -rid))
    selected = [first]
    remaining = [rid for rid in pool if rid != first]

    rng_seed = hashlib.sha256(f"{seed}:geometry_sparse_order".encode("utf-8")).digest()[:8]
    rng = random.Random(int.from_bytes(rng_seed, "big"))
    tie_break = {rid: rng.random() for rid in pool}

    while remaining:
        next_rid = max(
            remaining,
            key=lambda rid: (
                min(matrix[run_to_index[rid], run_to_index[chosen]] for chosen in selected),
                tie_break[rid],
            ),
        )
        selected.append(next_rid)
        remaining.remove(next_rid)
    return selected


def load_base_manifest(path: Path | None) -> dict[str, list[str]]:
    if path is None:
        candidate = Path(__file__).resolve().parents[1] / "splits" / "manifest.json"
        if not candidate.exists():
            return {}
        path = candidate
    if not path.exists():
        raise SystemExit(f"Base manifest does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_row(row: dict[str, str]) -> dict[str, str]:
    return {key.strip(): value.strip() for key, value in row.items() if key is not None}


def load_imputation_features(data_root: Path) -> dict[int, list[float]]:
    tables: list[dict[int, dict[str, float]]] = []
    for filename in ["force_mom_all.csv", "geo_parameters_all.csv"]:
        path = data_root / filename
        if not path.exists():
            raise SystemExit(f"Missing {path}; aggregate CSVs are required to impute absent STL scores")
        records: dict[int, dict[str, float]] = {}
        with path.open(encoding="utf-8-sig", newline="") as f:
            for raw in csv.DictReader(f):
                row = _clean_row(raw)
                records[int(row["run"])] = {key: float(value) for key, value in row.items() if key != "run"}
        tables.append(records)

    missing = sorted(set(PUBLIC_RUN_IDS) - set(tables[0]) | (set(PUBLIC_RUN_IDS) - set(tables[1])))
    if missing:
        raise SystemExit(f"Aggregate CSVs are missing WindsorML runs: {missing}")
    fields = [sorted(next(iter(table.values())).keys()) for table in tables]
    return {
        run: [value for table, names in zip(tables, fields) for name in names for value in [table[run][name]]]
        for run in PUBLIC_RUN_IDS
    }


def complete_metrics(
    requested_runs: list[int],
    metrics: list[dict[str, float | int]],
    scores: dict[int, float],
    data_root: Path,
    neighbor_count: int = 5,
) -> tuple[list[dict[str, float | int | str | bool]], dict[int, float], int]:
    rows_by_run = {int(row["run"]): row for row in metrics}
    observed_runs = sorted(rows_by_run)
    missing_runs = sorted(set(requested_runs) - set(observed_runs))
    complete_scores = scores.copy()
    complete_rows: dict[int, dict[str, float | int | str | bool]] = {}
    for run in observed_runs:
        complete_rows[run] = {
            **rows_by_run[run],
            "geometry_observed": True,
            "imputation_neighbors": "",
        }

    if missing_runs:
        features = load_imputation_features(data_root)
        all_matrix = np.asarray([features[run] for run in PUBLIC_RUN_IDS], dtype=float)
        means = all_matrix.mean(axis=0)
        stds = all_matrix.std(axis=0)
        stds[stds == 0.0] = 1.0
        standardized = (all_matrix - means) / stds
        numeric_fields = [key for key in metrics[0] if key not in {"run", "medoid_run"}]
        for run in missing_runs:
            nearest = sorted(
                observed_runs,
                key=lambda candidate: (float(np.linalg.norm(standardized[candidate] - standardized[run])), candidate),
            )[: max(1, min(neighbor_count, len(observed_runs)))]
            row: dict[str, float | int | str | bool] = {
                "run": run,
                "geometry_observed": False,
                "medoid_run": int(metrics[0]["medoid_run"]),
                "imputation_neighbors": ";".join(str(value) for value in nearest),
            }
            for field in numeric_fields:
                row[field] = float(np.mean([float(rows_by_run[candidate][field]) for candidate in nearest]))
            complete_scores[run] = float(np.mean([scores[candidate] for candidate in nearest]))
            complete_rows[run] = row
    return [complete_rows[run] for run in sorted(complete_rows)], complete_scores, len(missing_runs)


def write_metrics_csv(
    path: Path,
    metrics: list[dict[str, float | int | str | bool]],
    scores: dict[int, float],
) -> None:
    metric_fields = [key for key in metrics[0] if key not in {"run", "geometry_observed", "imputation_neighbors"}]
    fieldnames = ["run", "geometry_observed", *metric_fields, "ood_score", "imputation_neighbors"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics:
            out = dict(row)
            out["ood_score"] = scores[int(row["run"])]
            writer.writerow(out)


def build_manifest(
    run_ids: list[int],
    matrix: np.ndarray,
    scores: dict[int, float],
    args: argparse.Namespace,
) -> dict[str, list[str]]:
    train, val, test = ranked_ood_split(
        scores,
        test_fraction=args.test_fraction,
        val_fraction=args.val_fraction,
        seed=args.seed,
        salt="geometry_val_selection",
    )
    manifest: dict[str, list[str]] = {
        "geometry_train": make_case_ids(train),
        "geometry_val": make_case_ids(val),
        "geometry_test": make_case_ids(test),
    }

    base = load_base_manifest(args.base_manifest)
    required = {"full_train", "full_val", "full_test"}
    if not required <= set(base):
        return manifest

    available = set(run_ids)
    full_train = [run_id(cid) for cid in base["full_train"] if run_id(cid) in available]
    if len(full_train) < 20:
        return manifest

    run_to_index = {rid: idx for idx, rid in enumerate(run_ids)}
    order = farthest_order(full_train, run_to_index, matrix, args.seed)
    medium = round(len(order) / 3)
    scarce = round(len(order) / 6)
    super_scarce = max(1, round(len(order) / 36))
    sparse_sets = {
        "geometry_medium": sorted(order[:medium]),
        "geometry_scarce": sorted(order[:scarce]),
        "geometry_super_scarce": sorted(order[:super_scarce]),
    }
    for name, ids in sparse_sets.items():
        manifest[f"{name}_train"] = make_case_ids(ids)
        manifest[f"{name}_val"] = [cid for cid in base["full_val"] if run_id(cid) in available]
        manifest[f"{name}_test"] = [cid for cid in base["full_test"] if run_id(cid) in available]
    manifest["geometry_sparse_order"] = make_case_ids(order)
    return manifest


def summarize_split(name: str, manifest: dict[str, list[str]]) -> str:
    return (
        f"{name}: "
        f"train={len(manifest.get(name + '_train', []))}, "
        f"val={len(manifest.get(name + '_val', []))}, "
        f"test={len(manifest.get(name + '_test', []))}"
    )


def main() -> None:
    args = parse_args()
    require_dependencies()
    args.data_root = args.data_root.expanduser().resolve()
    args.output_dir = args.output_dir.expanduser().resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    requested_runs = parse_run_expression(args.runs)
    run_files = discover_files(args.data_root, requested_runs, args.allow_missing)
    print(f"Found {len(run_files)} STL files under {args.data_root}")

    run_ids, raw_clouds, bbox_min, bbox_max = sample_point_clouds(
        run_files,
        cache_dir=args.output_dir / "point_cloud_cache",
        samples=args.samples,
        seed=args.seed,
        workers=args.sample_workers,
        force=args.force_resample,
    )
    clouds, normalization_metadata = normalize_clouds(
        raw_clouds,
        bbox_min,
        bbox_max,
        center=args.center,
        scale_mode=args.scale_mode,
    )
    matrix = compute_chamfer_matrix(run_ids, clouds, args.output_dir, args, normalization_metadata)
    if args.write_csv_matrix:
        write_csv_matrix(args.output_dir / "chamfer_distance_matrix.csv", run_ids, matrix)

    metrics, _knn_scores = metric_values(run_ids, matrix, args.k_neighbors)
    observed_scores = score_map(run_ids, matrix, metrics, args.score, args.k_neighbors)
    complete_rows, scores, missing_count = complete_metrics(
        requested_runs,
        metrics,
        observed_scores,
        args.data_root,
    )
    write_metrics_csv(args.output_dir / "chamfer_metrics.csv", complete_rows, scores)

    manifest = build_manifest(run_ids, matrix, scores, args)
    manifest_path = args.output_dir / "chamfer_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print()
    print("Chamfer split summary")
    print("=" * 60)
    print(f"Runs: {len(requested_runs)} ({len(run_ids)} observed STL, {missing_count} imputed)")
    print(f"Metric: symmetric Chamfer RMS; score={args.score}")
    print(f"Metrics: {args.output_dir / 'chamfer_metrics.csv'}")
    if args.write_matrix:
        print(f"Matrix:  {args.output_dir / 'chamfer_distance_matrix.npy'}")
    else:
        print("Matrix:  not written; pass --write-matrix to save the full NPY")
    print(f"Manifest: {manifest_path}")
    print("  " + summarize_split("geometry", manifest))
    for prefix in ["geometry_medium", "geometry_scarce", "geometry_super_scarce"]:
        if f"{prefix}_train" in manifest:
            print("  " + summarize_split(prefix, manifest))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Interrupted")
