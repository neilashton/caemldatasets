## Official Splits

Recommended public splits are provided in `splits/manifest.json` using a flat
manifest format:

- `full`: seed-42 random public baseline, 400 train / 34 val / 50 test
- `medium`, `scarce`, and `super_scarce`: nested data-efficiency subsets with fixed val/test
- `geometry`: STL-surface Chamfer geometry OOD split
- `high_drag` and `low_drag`: force-regime OOD splits
- `rear_separation`: image-derived low-speed wake / rear-separation OOD split

The `full` split uses a seed-42 random run-ID procedure: `torch.randperm(500)`
is shifted to IDs `1..500`, the 16 hidden/unavailable cases are removed, the
first 400 public IDs become train, the next 50 become test, and the remaining
34 become validation. The manifest stores each partition sorted by run number.
For reference, these IDs match the public `DrivAerMLDefaultSplitIDs`
implementation in Noether.

The 16 unavailable or author-held-back run IDs are excluded from all public
train/val/test splits.

Chamfer geometry scores are documented in `data/chamfer_metrics.csv`. The
rear-separation image score is documented in `data/image_metrics.csv`; rows
include an observed/imputed flag.

The split rationale is documented in the LaTeX source at `docs/README.tex`
and the PDF export at `docs/README.pdf`.

To regenerate from a clean checkout, run
`python3 scripts/download_hf_inputs.py --output-dir data` to fetch the aggregate
`force_mom_all.csv` and `geo_parameters_all.csv` files, then run
`python3 scripts/generate_splits.py`. Optional downloader flags fetch the report
example PNGs, image-score PNGs, or STL files for full source recomputation.

```python
import json
from pathlib import Path

manifest = json.loads(Path("splits/manifest.json").read_text())
train_ids = manifest["full_train"]
val_ids = manifest["full_val"]
test_ids = manifest["full_test"]
```
