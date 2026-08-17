"""Build illustrative high/low image examples for the split report."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from generate_splits import _run_image_dir


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
DATA_DIR = PACKAGE_ROOT / "data"
DOCS_DIR = PACKAGE_ROOT / "docs"
METRICS = DATA_DIR / "image_metrics.csv"
OUT = DOCS_DIR / "image_split_examples.png"

EXAMPLES = [
    ("rear_separation", "centreline", "Rear separation"),
]


def _observed_rows(metric: str) -> list[dict[str, str]]:
    rows = list(csv.DictReader(METRICS.open(encoding="utf-8")))
    return [row for row in rows if row[f"{metric}_observed"] == "true"]


def _example_run(metric: str, high: bool) -> tuple[int, float]:
    rows = _observed_rows(metric)
    key = lambda row: float(row[f"{metric}_score"])
    row = max(rows, key=key) if high else min(rows, key=key)
    return int(row["run"]), float(row[f"{metric}_score"])


def _centreline_paths(run: int) -> list[Path]:
    image_dir = _run_image_dir(run)
    if image_dir is None:
        return []
    prefix = f"fig_run{run}_SRS"
    return [
        image_dir / f"{prefix}_magUMeanNormTrim_yNormal-2_yNormal_p00000.png",
        image_dir / f"{prefix}_CptMeanTrim_yNormal-2_yNormal_p00000.png",
        image_dir / f"{prefix}_CpMeanTrim_yNormal-2_yNormal_p00000.png",
    ]


def _display_png_array(path: Path) -> np.ndarray | None:
    if not path.exists() or path.name.startswith("._"):
        return None
    try:
        with path.open("rb") as f:
            if f.read(8) != b"\x89PNG\r\n\x1a\n":
                return None
        with Image.open(path) as img:
            img = img.convert("RGB")
            width, height = img.size
            # Keep the full centreline field and colorbar, trimming only the
            # mostly empty lower margin from the exported ParaView image.
            img = img.crop((0, 0, width, int(height * 0.91)))
            return np.asarray(img, dtype=np.float32) / 255.0
    except Exception:
        return None


def _first_image(run: int, kind: str):
    paths = _centreline_paths(run) if kind == "centreline" else []
    for path in paths:
        arr = _display_png_array(path)
        if arr is not None:
            return arr, path.name
    return None, "source PNG not found"


def main() -> None:
    fig, axes = plt.subplots(len(EXAMPLES), 2, figsize=(11.5, 4.2), constrained_layout=True, squeeze=False)

    for row_idx, (metric, kind, title) in enumerate(EXAMPLES):
        for col_idx, high in enumerate([False, True]):
            run, score = _example_run(metric, high)
            arr, filename = _first_image(run, kind)
            ax = axes[row_idx, col_idx]
            if arr is None:
                ax.set_facecolor("#f5f7fa")
                ax.text(
                    0.5,
                    0.5,
                    f"run_{run}\nscore={score:.3f}\n{filename}",
                    ha="center",
                    va="center",
                    fontsize=11,
                    color="#1f2933",
                    transform=ax.transAxes,
                )
            else:
                ax.imshow(arr)
            ax.set_xticks([])
            ax.set_yticks([])
            label = "high" if high else "low"
            ax.set_title(f"{title}: {label} score\ncentreline y=0, run_{run}, score={score:.3f}", fontsize=10)
            ax.set_xlabel(filename, fontsize=7)
            for spine in ax.spines.values():
                spine.set_visible(False)

    fig.suptitle("Image-derived split examples: centreline low vs. high observed-score cases", fontsize=13)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=180)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
