"""Create AhmedML split diagnostic plots."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from generate_splits import load_force_mom, run_id


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
DATA_DIR = PACKAGE_ROOT / "data"
DOCS_DIR = PACKAGE_ROOT / "docs"
SPLITS_DIR = PACKAGE_ROOT / "splits"
MANIFEST = SPLITS_DIR / "manifest.json"
CHAMFER = DATA_DIR / "chamfer_metrics.csv"
IMAGE = DATA_DIR / "image_metrics.csv"
OUT = DOCS_DIR / "split_diagnostics.png"


def _ids(manifest: dict[str, list[str]], key: str) -> set[int]:
    return {run_id(case_id) for case_id in manifest[key]}


def _load_scores(path: Path, column: str) -> dict[int, float]:
    with path.open(encoding="utf-8", newline="") as f:
        return {int(row["run"]): float(row[column]) for row in csv.DictReader(f) if row.get(column, "") != ""}


def _arrays(values: dict[int, float]) -> tuple[np.ndarray, np.ndarray]:
    runs = np.asarray(sorted(values))
    arr = np.asarray([values[int(run)] for run in runs], dtype=float)
    return runs, arr


def _plot_partitioned(
    ax,
    runs: np.ndarray,
    values: np.ndarray,
    train_ids: set[int],
    val_ids: set[int],
    test_ids: set[int],
    *,
    title: str,
    ylabel: str,
    colors: dict[str, str],
) -> None:
    train = np.asarray([int(run) in train_ids for run in runs])
    val = np.asarray([int(run) in val_ids for run in runs])
    test = np.asarray([int(run) in test_ids for run in runs])
    ax.scatter(runs[train], values[train], s=30, color=colors["train"], linewidth=0, alpha=0.58)
    ax.scatter(runs[val], values[val], s=46, color=colors["val"], linewidth=0, alpha=0.95)
    ax.scatter(runs[test], values[test], s=46, color=colors["test"], linewidth=0, alpha=0.95)
    ax.set_title(title)
    ax.set_xlabel("run")
    ax.set_ylabel(ylabel)
    ax.grid(True, color="#e1e6eb", lw=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    force_records, _ = load_force_mom()
    geometry_scores = _load_scores(CHAMFER, "ood_score")
    image_scores = _load_scores(IMAGE, "image_wake_score")

    runs, cd = _arrays({rid: values["cd"] for rid, values in force_records.items()})
    _, geometry = _arrays(geometry_scores)
    _, image_wake = _arrays(image_scores)

    colors = {"train": "#cfd5dc", "val": "#c28f22", "test": "#2f8f61"}
    fig, axes = plt.subplots(2, 3, figsize=(14.0, 8.0), constrained_layout=True)
    panels = [
        ("full", cd, "Full random baseline", "Cd"),
        ("high_drag", cd, "High-drag holdout", "Cd"),
        ("low_drag", cd, "Low-drag holdout", "Cd"),
        ("geometry", geometry, "STL-Chamfer geometry holdout", "mean 10-NN Chamfer"),
        ("image_wake", image_wake, "Image wake holdout", "UxMean image wake score"),
        ("image_wake", cd, "Image wake holdout on Cd", "Cd"),
    ]
    for ax, (prefix, values, title, ylabel) in zip(axes.flat, panels):
        _plot_partitioned(
            ax,
            runs,
            values,
            _ids(manifest, f"{prefix}_train"),
            _ids(manifest, f"{prefix}_val"),
            _ids(manifest, f"{prefix}_test"),
            title=title,
            ylabel=ylabel,
            colors=colors,
        )
    legend_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=colors["train"], markeredgewidth=0, markersize=8, label="train"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=colors["val"], markeredgewidth=0, markersize=8, label="val"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=colors["test"], markeredgewidth=0, markersize=8, label="test"),
    ]
    fig.legend(handles=legend_handles, frameon=False, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 0.99))
    fig.suptitle("AhmedML split diagnostics", fontsize=13)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=180)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
