## Official Splits

Recommended public splits are provided in `splits/manifest.json` using a flat
manifest format:

- `full`: Noether-compatible seed-42 random baseline, 400 train / 50 val / 50 test
- `medium`, `scarce`, and `super_scarce`: nested data-efficiency subsets with fixed val/test
- `geometry`: STL-Chamfer OOD split
- `high_drag` and `low_drag`: force-regime OOD splits
- `image_wake`: image-derived UxMean wake OOD split

The `full` split uses a seed-42 random run-ID procedure: `torch.randperm(500)`
is shifted to IDs `1..500`, the first 400 IDs become train, the next 50 become
validation, and the final 50 become test. The manifest stores each partition
sorted by run number. These IDs match Noether's `AhmedMLDefaultSplitIDs`.

Drag-regime splits are generated from `data/force_mom_all.csv`. Geometry scores
are generated from local `run_*/ahmed_*.stl` files and written to
`data/chamfer_metrics.csv`. Image-wake scores are generated from local
`run_*/images/UxMean/*-X-*.png` files and written to `data/image_metrics.csv`.
The geometry-parameter CSV is used only for the nested data-efficiency ordering;
run 500 is mean-imputed there because it is absent from `geo_parameters_all.csv`.

The split rationale is documented in the LaTeX source at `docs/README.tex` and
the PDF export at `docs/README.pdf`.

To regenerate from a clean checkout, run
`python3 scripts/download_hf_inputs.py --output-dir data --include-stls --include-images`
to fetch `force_mom_all.csv`, `geo_parameters_all.csv`, STLs, and PNG images.
Then run `scripts/compute_chamfer_splits.py`, copy its `chamfer_metrics.csv`
into `data/`, run `scripts/compute_image_metrics.py`, and finally run
`python3 scripts/generate_splits.py` and `python3 scripts/visualize_splits.py`.

```python
import json
from pathlib import Path

manifest = json.loads(Path("splits/manifest.json").read_text())
train_ids = manifest["full_train"]
val_ids = manifest["full_val"]
test_ids = manifest["full_test"]
```
