"""Download AhmedML split-regeneration inputs from Hugging Face.

Default behavior downloads only the aggregate CSV files needed by
scripts/generate_splits.py:

    python3 scripts/download_hf_inputs.py --output-dir data

For STL/PNG assets, prefer a directory outside this split package:

    python3 scripts/download_hf_inputs.py --output-dir ../ahmedml_hf_assets \
      --include-stls --include-wake-images
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import random
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


REPO_ID = "neashton/ahmedml"
REVISION = "main"
AGGREGATE_FILES = [
    "force_mom_all.csv",
    "geo_parameters_all.csv",
]
OPTIONAL_AGGREGATE_FILES = [
    "force_mom_varref_all.csv",
]
IMAGE_SLICES = {
    "X": range(22),
    "Y": range(9),
    "Z": range(6),
}
WAKE_IMAGE_SLICES = {
    "X": (14, 15, 16),
    "Y": (4,),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download source inputs for AhmedML split regeneration.")
    parser.add_argument("--repo-id", default=REPO_ID, help=f"Hugging Face dataset repo ID. Default: {REPO_ID}")
    parser.add_argument("--revision", default=REVISION, help=f"Hub revision, branch, or tag. Default: {REVISION}")
    parser.add_argument("--output-dir", type=Path, default=Path("data"), help="Directory where files are written.")
    parser.add_argument("--include-varref", action="store_true", help="Also download force_mom_varref_all.csv.")
    parser.add_argument("--include-images", action="store_true", help="Download all CpT and UxMean PNG images. This is large.")
    parser.add_argument("--include-wake-images", action="store_true", help="Download only UxMean PNG slices needed for the image_wake split.")
    parser.add_argument("--include-stls", action="store_true", help="Download run_*/ahmed_*.stl files. This is large.")
    parser.add_argument("--runs", default="all", help="Run IDs for optional STL/image downloads: all or a comma/range expression.")
    parser.add_argument("--workers", type=int, default=4, help="Parallel downloads. Default: 4.")
    parser.add_argument("--retries", type=int, default=6, help="Retries for HTTP 429 and transient network errors.")
    parser.add_argument("--retry-sleep", type=float, default=4.0, help="Initial retry sleep in seconds.")
    parser.add_argument("--overwrite", action="store_true", help="Redownload files that already exist.")
    parser.add_argument("--dry-run", action="store_true", help="Print the file list without downloading.")
    return parser.parse_args()


def parse_run_expression(expr: str) -> list[int]:
    expr = expr.strip().lower()
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
    invalid = sorted(run for run in runs if run < 1 or run > 500)
    if invalid:
        raise SystemExit(f"Invalid run IDs: {invalid[:10]}")
    return sorted(runs)


def hub_url(repo_id: str, revision: str, path: str) -> str:
    quoted_path = "/".join(quote(part) for part in path.split("/"))
    return f"https://huggingface.co/datasets/{repo_id}/resolve/{quote(revision, safe='')}/{quoted_path}"


def retry_delay(base_sleep: float, attempt: int, retry_after: str | None = None) -> float:
    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            pass
    jitter = random.uniform(0.0, base_sleep)
    return min(90.0, base_sleep * (2 ** max(0, attempt - 1)) + jitter)


def download_one(
    repo_id: str,
    revision: str,
    output_dir: Path,
    rel_path: str,
    overwrite: bool,
    retries: int,
    retry_sleep: float,
) -> tuple[str, str]:
    destination = output_dir / rel_path
    if destination.exists() and not overwrite:
        return rel_path, "skip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    headers = {}
    if os.environ.get("HF_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['HF_TOKEN']}"
    for attempt in range(retries + 1):
        request = Request(hub_url(repo_id, revision, rel_path), headers=headers)
        try:
            with urlopen(request, timeout=120) as response:
                destination.write_bytes(response.read())
            return rel_path, "ok"
        except HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code <= 599
            if retryable and attempt < retries:
                time.sleep(retry_delay(retry_sleep, attempt, exc.headers.get("Retry-After")))
                continue
            return rel_path, f"http_{exc.code}"
        except URLError as exc:
            if attempt < retries:
                time.sleep(retry_delay(retry_sleep, attempt))
                continue
            return rel_path, f"url_error:{exc.reason}"
    return rel_path, "failed"


def main() -> None:
    args = parse_args()
    files = AGGREGATE_FILES.copy()
    if args.include_varref:
        files.extend(OPTIONAL_AGGREGATE_FILES)
    runs = parse_run_expression(args.runs)
    if args.include_stls:
        files.extend(f"run_{run}/ahmed_{run}.stl" for run in runs)
    if args.include_images:
        for run in runs:
            for axis, indices in IMAGE_SLICES.items():
                files.extend(
                    f"run_{run}/images/CpT/run_{run}-slice-total(p)_coeffMean-{axis}-{idx}.png"
                    for idx in indices
                )
                files.extend(
                    f"run_{run}/images/UxMean/run_{run}-slice-UMean-0-{axis}-{idx}.png"
                    for idx in indices
                )
    elif args.include_wake_images:
        for run in runs:
            for axis, indices in WAKE_IMAGE_SLICES.items():
                files.extend(
                    f"run_{run}/images/UxMean/run_{run}-slice-UMean-0-{axis}-{idx}.png"
                    for idx in indices
                )

    print(f"Repository: {args.repo_id}@{args.revision}")
    print(f"Output dir: {args.output_dir}")
    print(f"Files: {len(files)}")
    if args.dry_run:
        for path in files:
            print(path)
        return

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [
            pool.submit(
                download_one,
                args.repo_id,
                args.revision,
                args.output_dir,
                path,
                args.overwrite,
                args.retries,
                args.retry_sleep,
            )
            for path in files
        ]
        for future in as_completed(futures):
            path, status = future.result()
            print(f"{status:<8s} {path}")


if __name__ == "__main__":
    main()
