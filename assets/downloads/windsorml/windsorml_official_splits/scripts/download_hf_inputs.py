"""Download WindsorML inputs needed to regenerate the split package.

Default behavior downloads the two small aggregate CSV files used by the split
generator. Large per-run
assets should be kept outside this repository, for example:

    python3 scripts/download_hf_inputs.py \
      --output-dir ../windsorml_hf_assets \
      --include-stls --include-wake-images --include-geometry-images \
      --workers 6 --allow-missing
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


REPO_ID = "neashton/windsorml"
REVISION = "main"
N_CASES = 355
RUN_IDS = list(range(N_CASES))
AGGREGATE_FILES = [
    "force_mom_all.csv",
    "geo_parameters_all.csv",
]

# z ranges from -0.4 to 0.4 over 10 images; indices 4 and 5 bracket z=0.
# x ranges from -0.5 to 1.0 over 80 images; indices 53, 55, and 57 are
# immediately behind the Windsor base at x=0.48 m.
WAKE_IMAGE_PATHS = [
    *(f"images/velocityxavg/view1_constz_scan_{index:04d}.png" for index in (4, 5)),
    *(f"images/velocityxavg/view2_constx_scan_{index:04d}.png" for index in (53, 55, 57)),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download WindsorML split-regeneration inputs.")
    parser.add_argument("--repo-id", default=REPO_ID, help=f"Hugging Face dataset repository. Default: {REPO_ID}")
    parser.add_argument("--revision", default=REVISION, help=f"Hub branch, tag, or revision. Default: {REVISION}")
    parser.add_argument("--output-dir", type=Path, default=Path("data"), help="Directory where files are written.")
    parser.add_argument("--include-stls", action="store_true", help="Download run_*/windsor_*.stl files.")
    parser.add_argument(
        "--include-wake-images",
        action="store_true",
        help="Download the five velocity PNGs per run used by the image_wake score.",
    )
    parser.add_argument(
        "--include-geometry-images",
        action="store_true",
        help="Download run_*/images/windsor_*.png side-view geometry images for the report.",
    )
    parser.add_argument("--runs", default="all", help="Run IDs for per-run downloads: all or a comma/range expression.")
    parser.add_argument("--workers", type=int, default=4, help="Parallel download workers.")
    parser.add_argument("--retries", type=int, default=6, help="Retries for throttling and transient failures.")
    parser.add_argument("--retry-sleep", type=float, default=4.0, help="Initial retry delay in seconds.")
    parser.add_argument("--overwrite", action="store_true", help="Redownload existing non-empty files.")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Finish successfully when a requested Hub file returns 404; all misses are still reported.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the requested file list without downloading.")
    return parser.parse_args()


def parse_run_expression(expr: str) -> list[int]:
    expr = expr.strip().lower()
    if expr == "all":
        return RUN_IDS.copy()
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
    invalid = [run for run in runs if run not in RUN_IDS]
    if invalid:
        raise SystemExit(f"Run IDs must be in 0..{N_CASES - 1}; invalid values: {invalid}")
    return runs


def hub_url(repo_id: str, revision: str, rel_path: str) -> str:
    encoded = "/".join(quote(part) for part in rel_path.split("/"))
    return f"https://huggingface.co/datasets/{repo_id}/resolve/{quote(revision, safe='')}/{encoded}"


def retry_delay(base: float, attempt: int, retry_after: str | None = None) -> float:
    if retry_after:
        try:
            return max(base, float(retry_after))
        except ValueError:
            pass
    return base * (2**attempt) + random.random()


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
    if destination.exists() and destination.stat().st_size > 0 and not overwrite:
        return rel_path, "exists"
    destination.parent.mkdir(parents=True, exist_ok=True)
    headers: dict[str, str] = {}
    if os.environ.get("HF_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['HF_TOKEN']}"

    for attempt in range(retries + 1):
        request = Request(hub_url(repo_id, revision, rel_path), headers=headers)
        part = destination.with_name(destination.name + ".part")
        try:
            with urlopen(request, timeout=180) as response, part.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            part.replace(destination)
            return rel_path, "ok"
        except HTTPError as exc:
            part.unlink(missing_ok=True)
            retryable = exc.code == 429 or 500 <= exc.code <= 599
            if retryable and attempt < retries:
                time.sleep(retry_delay(retry_sleep, attempt, exc.headers.get("Retry-After")))
                continue
            return rel_path, f"http_{exc.code}"
        except (OSError, URLError) as exc:
            part.unlink(missing_ok=True)
            if attempt < retries:
                time.sleep(retry_delay(retry_sleep, attempt))
                continue
            reason = getattr(exc, "reason", str(exc))
            return rel_path, f"error:{reason}"
    return rel_path, "failed"


def requested_files(args: argparse.Namespace) -> list[str]:
    files = AGGREGATE_FILES.copy()
    for run in parse_run_expression(args.runs):
        if args.include_stls:
            files.append(f"run_{run}/windsor_{run}.stl")
        if args.include_wake_images:
            files.extend(f"run_{run}/{path}" for path in WAKE_IMAGE_PATHS)
        if args.include_geometry_images:
            files.append(f"run_{run}/images/windsor_{run}.png")
    return files


def main() -> None:
    args = parse_args()
    files = requested_files(args)
    print(f"Repository: {args.repo_id}@{args.revision}")
    print(f"Output dir: {args.output_dir}")
    print(f"Files: {len(files)}")
    if args.dry_run:
        for path in files:
            print(path)
        return

    failures: list[tuple[str, str]] = []
    counts: dict[str, int] = {}
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
            counts[status] = counts.get(status, 0) + 1
            if status not in {"ok", "exists"}:
                failures.append((path, status))
                print(f"{status:<12s} {path}")

    print("Summary: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    if failures and not args.allow_missing:
        raise SystemExit(f"{len(failures)} downloads failed; rerun with --allow-missing only if the Hub mirror is incomplete.")


if __name__ == "__main__":
    main()
