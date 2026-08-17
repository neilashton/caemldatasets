"""Create WindsorML train/validation/test diagnostic plots."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from generate_splits import load_force_mom, run_id


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
DOCS_DIR = PACKAGE_ROOT / "docs"
MANIFEST = PACKAGE_ROOT / "splits" / "manifest.json"
OUT = DOCS_DIR / "split_diagnostics.png"


def ids(manifest: dict[str, list[str]], key: str) -> set[int]:
    return {run_id(case) for case in manifest[key]}


def load_scores(path: Path, column: str) -> dict[int, float]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {int(row["run"]): float(row[column]) for row in csv.DictReader(f) if row.get(column, "")}


def arrays(values: dict[int, float]) -> tuple[np.ndarray, np.ndarray]:
    runs = np.asarray(sorted(values))
    return runs, np.asarray([values[int(run)] for run in runs], dtype=float)


def plot_partitioned(
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
    masks = {
        "train": np.asarray([int(run) in train_ids for run in runs]),
        "val": np.asarray([int(run) in val_ids for run in runs]),
        "test": np.asarray([int(run) in test_ids for run in runs]),
    }
    sizes = {"train": 30, "val": 48, "test": 48}
    alpha = {"train": 0.58, "val": 0.95, "test": 0.95}
    for part in ("train", "val", "test"):
        ax.scatter(runs[masks[part]], values[masks[part]], s=sizes[part], color=colors[part], linewidth=0, alpha=alpha[part])
    ax.set_title(title)
    ax.set_xlabel("run ID")
    ax.set_ylabel(ylabel)
    ax.grid(True, color="#e1e6eb", lw=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    force_records, _ = load_force_mom()
    geometry_scores = load_scores(DATA_DIR / "chamfer_metrics.csv", "ood_score")
    image_scores = load_scores(DATA_DIR / "image_metrics.csv", "image_wake_score")
    runs, cd = arrays({run: values["cd"] for run, values in force_records.items()})
    _, geometry = arrays(geometry_scores)
    _, image_wake = arrays(image_scores)

    colors = {"train": "#cfd5dc", "val": "#c28f22", "test": "#2f8f61"}
    fig, axes = plt.subplots(2, 3, figsize=(14.0, 8.2), constrained_layout=True)
    panels = [
        ("full", cd, "Full seed-42 baseline", "Cd"),
        ("high_drag", cd, "High-drag holdout", "Cd"),
        ("low_drag", cd, "Low-drag holdout", "Cd"),
        ("geometry", geometry, "STL-Chamfer geometry holdout", "mean 10-NN Chamfer"),
        ("image_wake", image_wake, "Image-wake holdout", "low-speed wake score"),
        ("image_wake", cd, "Image-wake holdout on Cd", "Cd"),
    ]
    for ax, (prefix, values, title, ylabel) in zip(axes.flat, panels):
        plot_partitioned(
            ax,
            runs,
            values,
            ids(manifest, f"{prefix}_train"),
            ids(manifest, f"{prefix}_val"),
            ids(manifest, f"{prefix}_test"),
            title=title,
            ylabel=ylabel,
            colors=colors,
        )
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=colors[part], markeredgewidth=0, markersize=8, label=part)
        for part in ("train", "val", "test")
    ]
    fig.legend(handles=handles, frameon=False, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 0.995))
    fig.suptitle("WindsorML split diagnostics", fontsize=13)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=180)
    plt.close(fig)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
