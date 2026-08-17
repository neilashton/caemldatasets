"""Download DrivAerML split-regeneration inputs from Hugging Face.

Default behavior downloads only the aggregate CSV files needed by
scripts/generate_splits.py and the diagnostic plots:

    python3 scripts/download_hf_inputs.py --output-dir data

Optional flags pull the PNGs used by report figures, the PNGs used to recompute
the rear-separation image score, or the STL files used to recompute
chamfer_metrics.csv. STL downloads are intentionally opt-in because they are
large.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


REPO_ID = "neashton/drivaerml"
REVISION = "main"
HIDDEN_TEST_IDS = {
    167, 211, 218, 221, 248, 282, 291, 295,
    316, 325, 329, 364, 370, 376, 403, 473,
}
PUBLIC_RUN_IDS = [run for run in range(1, 501) if run not in HIDDEN_TEST_IDS]
AGGREGATE_FILES = [
    "force_mom_all.csv",
    "geo_parameters_all.csv",
]
REPORT_IMAGE_FILES = [
    "run_294/images/fig_run294_SRS_surf-ySide_grid.png",
    "run_393/images/fig_run393_SRS_surf-ySide_grid.png",
    "run_100/images/fig_run100_SRS_magUMeanNormTrim_yNormal-2_yNormal_p00000.png",
    "run_406/images/fig_run406_SRS_magUMeanNormTrim_yNormal-2_yNormal_p00000.png",
]
REAR_XNORMAL_POSITIONS = [
    "p43000",
    "p45000",
    "p47000",
    "p49000",
    "p51000",
    "p53000",
    "p55000",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download source inputs for DrivAerML split regeneration.",
    )
    parser.add_argument(
        "--repo-id",
        default=REPO_ID,
        help=f"Hugging Face dataset repo ID. Default: {REPO_ID}",
    )
    parser.add_argument(
        "--revision",
        default=REVISION,
        help=f"Hub revision, branch, or tag. Default: {REVISION}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Directory where files are written, preserving dataset-relative paths.",
    )
    parser.add_argument(
        "--runs",
        default="public",
        help="Run IDs for optional per-run downloads: public, all, or a comma/range expression like 1,10-20.",
    )
    parser.add_argument(
        "--include-report-images",
        action="store_true",
        help="Download the four PNGs needed to render the committed example figures from source images.",
    )
    parser.add_argument(
        "--include-image-score-pngs",
        action="store_true",
        help="Download centreline and near-rear xNormal PNGs used to recompute image_metrics.csv.",
    )
    parser.add_argument(
        "--include-stls",
        action="store_true",
        help="Download run_*/drivaer_*.stl files needed to recompute chamfer_metrics.csv. This is large.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Parallel downloads. Default: 8.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Redownload files that already exist.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the file list without downloading.",
    )
    return parser.parse_args()


def parse_run_expression(expr: str) -> list[int]:
    expr = expr.strip().lower()
    if expr == "public":
        return PUBLIC_RUN_IDS.copy()
    if expr == "all":
        return list(range(1, 501))

    runs: set[int] = set()
    for part in expr.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = [int(value) for value in part.split("-", 1)]
            if start > end:
                start, end = end, start
            runs.update(range(start, end + 1))
        else:
            runs.add(int(part))
    bad = sorted(run for run in runs if run < 1 or run > 500)
    if bad:
        raise SystemExit(f"Run IDs must be in 1..500, got: {bad[:10]}")
    return sorted(runs)


def image_score_files(run_ids: list[int]) -> list[str]:
    paths = []
    for run in run_ids:
        prefix = f"run_{run}/images/fig_run{run}_SRS"
        paths.append(f"{prefix}_magUMeanNormTrim_yNormal-2_yNormal_p00000.png")
        paths.extend(
            f"{prefix}_magUMeanNormTrim_xNormal-2_xNormal_{position}.png"
            for position in REAR_XNORMAL_POSITIONS
        )
    return paths


def stl_files(run_ids: list[int]) -> list[str]:
    return [f"run_{run}/drivaer_{run}.stl" for run in run_ids]


def resolve_url(repo_id: str, revision: str, relpath: str) -> str:
    escaped_path = quote(relpath, safe="/")
    escaped_revision = quote(revision, safe="")
    return f"https://huggingface.co/datasets/{repo_id}/resolve/{escaped_revision}/{escaped_path}"


def request_for(url: str) -> Request:
    headers = {}
    token = os.environ.get("HF_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return Request(url, headers=headers)


def download_one(repo_id: str, revision: str, output_dir: Path, relpath: str, overwrite: bool) -> str:
    target = output_dir / relpath
    if target.exists() and target.stat().st_size > 0 and not overwrite:
        return f"skip {relpath}"

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    url = resolve_url(repo_id, revision, relpath)
    try:
        with urlopen(request_for(url), timeout=120) as response, tmp.open("wb") as f:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
        tmp.replace(target)
    except (HTTPError, URLError) as exc:
        if tmp.exists():
            tmp.unlink()
        raise RuntimeError(f"failed {relpath}: {exc}") from exc
    return f"ok   {relpath}"


def main() -> None:
    args = parse_args()
    run_ids = parse_run_expression(args.runs)
    paths: set[str] = set(AGGREGATE_FILES)

    if args.include_report_images:
        paths.update(REPORT_IMAGE_FILES)
    if args.include_image_score_pngs:
        paths.update(image_score_files(run_ids))
    if args.include_stls:
        paths.update(stl_files(run_ids))

    selected = sorted(paths)
    print(f"Repository: {args.repo_id}@{args.revision}")
    print(f"Output dir: {args.output_dir}")
    print(f"Files: {len(selected)}")
    if args.include_stls:
        print("STL download requested; this can require tens of GB for all public runs.")
    if args.dry_run:
        for relpath in selected:
            print(relpath)
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    errors = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {
            pool.submit(download_one, args.repo_id, args.revision, args.output_dir, relpath, args.overwrite): relpath
            for relpath in selected
        }
        for future in as_completed(futures):
            try:
                print(future.result())
            except RuntimeError as exc:
                errors.append(str(exc))
                print(errors[-1], file=sys.stderr)

    if errors:
        raise SystemExit(f"{len(errors)} download(s) failed")


if __name__ == "__main__":
    main()
