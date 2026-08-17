## Recommended splits

The committed split manifest is available at `splits/manifest.json` in the
WindsorML split package. It contains sorted `run_N` identifiers for the
following deterministic train/validation/test families:

- `full`: seed-42 random baseline using the companion package's approximately 80/10/10 ratio
- `medium`, `scarce`, `super_scarce`: nested data-efficiency subsets with fixed validation and test sets
- `geometry`: STL-Chamfer shape OOD holdout
- `high_drag`, `low_drag`: fixed-reference drag-coefficient OOD holdouts
- `image_wake`: image-derived low-speed wake OOD holdout

For normal benchmark use, consume the committed manifest directly. The scripts
and metric CSVs are included to document and reproduce the construction; large
STL and PNG inputs are downloaded separately from the WindsorML dataset repo.

```python
import json
from pathlib import Path

manifest = json.loads(Path("splits/manifest.json").read_text())
train_ids = manifest["full_train"]
val_ids = manifest["full_val"]
test_ids = manifest["full_test"]
```
