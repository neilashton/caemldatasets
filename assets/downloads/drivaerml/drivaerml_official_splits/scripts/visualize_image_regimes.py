"""Visualize image-inspired DrivAerML flow-regime splits.

Creates image_regimes.png from data/image_metrics.csv, splits/manifest.json, and
force_mom_all.csv.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from generate_splits import load_force_mom, run_id


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
DATA_DIR = PACKAGE_ROOT / "data"
DOCS_DIR = PACKAGE_ROOT / "docs"
SPLITS_DIR = PACKAGE_ROOT / "splits"
MANIFEST = SPLITS_DIR / "manifest.json"
METRICS = DATA_DIR / "image_metrics.csv"
OUT = DOCS_DIR / "image_regimes.png"


def _ids(manifest: dict[str, list[str]], key: str) -> set[int]:
    return {run_id(cid) for cid in manifest[key]}


def _load_metrics() -> dict[str, dict[int, float | bool]]:
    rows = list(csv.DictReader(METRICS.open(encoding="utf-8")))
    result: dict[str, dict[int, float | bool]] = {}
    for row in rows:
        rid = int(row["run"])
        result.setdefault("run", {})[rid] = rid
        for key, value in row.items():
            if key == "run":
                continue
            if key.endswith("_observed"):
                result.setdefault(key, {})[rid] = value == "true"
            else:
                result.setdefault(key, {})[rid] = float(value)
    return result


def _arrays(values: dict[int, float | bool]) -> tuple[np.ndarray, np.ndarray]:
    runs = np.asarray(sorted(values))
    arr = np.asarray([values[int(r)] for r in runs])
    return runs, arr


def _plot_partitioned(
    ax,
    runs: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    train_ids: set[int],
    val_ids: set[int],
    test_ids: set[int],
    *,
    title: str,
    xlabel: str,
    ylabel: str,
) -> None:
    train = np.asarray([int(r) in train_ids for r in runs])
    val = np.asarray([int(r) in val_ids for r in runs])
    test = np.asarray([int(r) in test_ids for r in runs])
    ax.scatter(x[train], y[train], s=22, color="#aeb7c2", linewidth=0, alpha=0.62, label="train")
    ax.scatter(x[val], y[val], s=30, color="#c28f22", linewidth=0, alpha=0.95, label="val")
    ax.scatter(x[test], y[test], s=30, color="#2f8f61", linewidth=0, alpha=0.95, label="test")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, color="#e1e6eb", lw=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    metrics = _load_metrics()
    records, force_source = load_force_mom()
    if force_source == "deterministic_proxy_missing_force_mom_all_csv":
        raise SystemExit(
            "force_mom_all.csv is required for image_regimes.png. "
            "Run after `python3 scripts/download_hf_inputs.py --output-dir data`, "
            "or set DRIVAERML_DATA_ROOT to a directory containing it."
        )
    runs, _ = _arrays(metrics["run"])
    cd = np.asarray([records[int(r)]["cd"] for r in runs], dtype=float)

    def score(name: str) -> tuple[np.ndarray, np.ndarray]:
        _, y = _arrays(metrics[f"{name}_score"])
        _, observed = _arrays(metrics[f"{name}_observed"])
        return y.astype(float), observed.astype(bool)

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 3.9), constrained_layout=True)

    y, _obs = score("rear_separation")
    train_ids = _ids(manifest, "rear_separation_train")
    val_ids = _ids(manifest, "rear_separation_val")
    test_ids = _ids(manifest, "rear_separation_test")
    _plot_partitioned(
        axes[0],
        runs,
        runs,
        y,
        train_ids,
        val_ids,
        test_ids,
        title="Rear-separation split score",
        xlabel="run",
        ylabel="rear_separation score",
    )
    _plot_partitioned(
        axes[1],
        runs,
        runs,
        cd,
        train_ids,
        val_ids,
        test_ids,
        title="Rear-separation split on Cd",
        xlabel="run",
        ylabel="Cd",
    )
    legend = axes[0].legend(frameon=True, loc="lower left")
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("none")
    legend.get_frame().set_alpha(0.78)

    fig.suptitle("DrivAerML image-derived flow-regime split diagnostics", fontsize=12)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=180)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
