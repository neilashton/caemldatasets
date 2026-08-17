"""Visualize the DrivAerML force- and geometry-regime split logic.

Creates force_regimes.png. The script reads force_mom_all.csv and
geo_parameters_all.csv when available. It also reads chamfer_metrics.csv when
available to show the STL-surface geometry split.

Usage:
    python scripts/visualize_flow_regimes.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from generate_splits import (
    load_chamfer_scores,
    load_force_mom,
    run_id,
)


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
DATA_DIR = PACKAGE_ROOT / "data"
DOCS_DIR = PACKAGE_ROOT / "docs"
SPLITS_DIR = PACKAGE_ROOT / "splits"
OUT = DOCS_DIR / "force_regimes.png"
MANIFEST = SPLITS_DIR / "manifest.json"


def _ids(manifest: dict[str, list[str]], key: str) -> set[int]:
    return {run_id(cid) for cid in manifest[key]}


def _array(records: dict[int, dict[str, float]], field: str) -> tuple[np.ndarray, np.ndarray]:
    runs = np.asarray(sorted(records))
    values = np.asarray([records[int(r)][field] for r in runs], dtype=float)
    return runs, values


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
    train_mask = np.asarray([int(r) in train_ids for r in runs])
    val_mask = np.asarray([int(r) in val_ids for r in runs])
    test_mask = np.asarray([int(r) in test_ids for r in runs])
    ax.scatter(runs[train_mask], values[train_mask], s=30, color=colors["train"], linewidth=0, alpha=0.58)
    ax.scatter(runs[val_mask], values[val_mask], s=46, color=colors["val"], linewidth=0, alpha=0.95)
    ax.scatter(runs[test_mask], values[test_mask], s=46, color=colors["test"], linewidth=0, alpha=0.95)
    ax.set_title(title)
    ax.set_xlabel("run")
    ax.set_ylabel(ylabel)
    ax.grid(True, color="#e1e6eb", lw=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def main() -> None:
    records, force_source = load_force_mom()
    if force_source == "deterministic_proxy_missing_force_mom_all_csv":
        raise SystemExit(
            "force_mom_all.csv is required for force_regimes.png. "
            "Run after `python3 scripts/download_hf_inputs.py --output-dir data`, "
            "or set DRIVAERML_DATA_ROOT to a directory containing it."
        )
    chamfer_scores, _ = load_chamfer_scores()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    runs, cd = _array(records, "cd")
    chamfer = np.asarray([chamfer_scores[int(r)] for r in runs]) if chamfer_scores else None

    full_train = _ids(manifest, "full_train")
    full_val = _ids(manifest, "full_val")
    full_test = _ids(manifest, "full_test")
    high_drag_train = _ids(manifest, "high_drag_train")
    high_drag_val = _ids(manifest, "high_drag_val")
    high_drag_test = _ids(manifest, "high_drag_test")
    low_drag_train = _ids(manifest, "low_drag_train")
    low_drag_val = _ids(manifest, "low_drag_val")
    low_drag_test = _ids(manifest, "low_drag_test")
    geometry_train = _ids(manifest, "geometry_train") if "geometry_train" in manifest else set()
    geometry_val = _ids(manifest, "geometry_val") if "geometry_val" in manifest else set()
    geometry_test = _ids(manifest, "geometry_test") if "geometry_test" in manifest else set()

    colors = {
        "train": "#cfd5dc",
        "val": "#c28f22",
        "test": "#2f8f61",
    }

    axes = plt.figure(figsize=(11.0, 11.0), constrained_layout=True).subplot_mosaic(
        [
            ["full", "high"],
            ["low", "geometry_cd"],
            ["geometry_chamfer", "geometry_chamfer"],
        ]
    )
    fig = axes["full"].figure

    _plot_partitioned(
        axes["full"], runs, cd, full_train, full_val, full_test,
        title="Full random baseline", ylabel="Cd", colors=colors,
    )
    _plot_partitioned(
        axes["high"], runs, cd, high_drag_train, high_drag_val, high_drag_test,
        title="High-drag holdout", ylabel="Cd", colors=colors,
    )
    _plot_partitioned(
        axes["low"], runs, cd, low_drag_train, low_drag_val, low_drag_test,
        title="Low-drag holdout", ylabel="Cd", colors=colors,
    )
    _plot_partitioned(
        axes["geometry_cd"], runs, cd, geometry_train, geometry_val, geometry_test,
        title="Geometry holdout on Cd", ylabel="Cd", colors=colors,
    )

    ax = axes["geometry_chamfer"]
    if chamfer is not None:
        _plot_partitioned(
            ax, runs, chamfer, geometry_train, geometry_val, geometry_test,
            title="Geometry holdout", ylabel="mean 10-NN Chamfer", colors=colors,
        )
    else:
        ax.text(0.5, 0.5, "data/chamfer_metrics.csv not found", ha="center", va="center")
        ax.set_axis_off()

    legend_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=colors["train"], markeredgewidth=0, markersize=8, label="train"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=colors["val"], markeredgewidth=0, markersize=8, label="val"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=colors["test"], markeredgewidth=0, markersize=8, label="test"),
    ]
    fig.legend(handles=legend_handles, frameon=False, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 0.975))

    fig.suptitle("DrivAerML force and geometry split diagnostics", fontsize=12)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=180)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
