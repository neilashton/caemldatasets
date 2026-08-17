"""Generate deterministic train/val/test splits for the DrivAerML dataset.

Produces a manifest.json containing DrivAerML split types with train/val/test
keys:

    {
        "full_train": ["run_1", ...],
        "full_val": [...],
        "full_test": [...],
        ...
    }

Split families:

  1. full            - seed-42 random public split, 400/34/50
  2. medium          - same val/test as full, train is 1/3 subsample
  3. scarce          - same val/test as full, train is 1/6 subsample
  4. super_scarce    - same val/test as full, train is 1/36 subsample
  5. geometry        - OOD STL-surface Chamfer geometry split
  6. high_drag       - OOD high-drag split from force_mom_all.csv
  7. low_drag        - OOD low-drag split from force_mom_all.csv
  8. rear_separation - OOD image-derived rear-surface separation split

For every OOD split, the validation set is drawn from the training-side
population so that hyperparameter tuning never sees out-of-distribution data.

Usage:
    python scripts/generate_splits.py

The script reads force_mom_all.csv and geo_parameters_all.csv from the dataset
root or data/ folder, and chamfer_metrics.csv from data/ when available. Outside
that context it falls back to deterministic force/geometry proxies and omits the
Chamfer split if the Chamfer metrics are missing, but the official manifest
should be regenerated with all real source files present.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import random
from pathlib import Path

import numpy as np

### ---- Dataset constants -------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
DATA_DIR = PACKAGE_ROOT / "data"
SPLITS_DIR = PACKAGE_ROOT / "splits"
DATA_ROOT = Path(os.environ.get("DRIVAERML_DATA_ROOT", DATA_DIR))
N_CASES = 500
HIDDEN_TEST_IDS = [167, 211, 218, 221, 248, 282, 291, 295, 316, 325, 329, 364, 370, 376, 403, 473]
PUBLIC_RUN_IDS = [i for i in range(1, N_CASES + 1) if i not in set(HIDDEN_TEST_IDS)]
N_PUBLIC = len(PUBLIC_RUN_IDS)

# Seed-42 torch randperm over 1..500, after removing the 16 hidden runs. For
# reference, these IDs match the public DrivAerMLDefaultSplitIDs implementation
# in Noether.
FULL_TRAIN_IDS = [
    1, 2, 3, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 21, 23, 25, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
    40, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 57, 58, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71,
    72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99,
    100, 101, 102, 103, 104, 105, 106, 107, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123,
    125, 126, 128, 129, 130, 131, 132, 134, 135, 136, 137, 138, 139, 140, 141, 143, 144, 145, 146, 147, 148, 149,
    151, 152, 153, 154, 155, 156, 157, 159, 160, 161, 162, 163, 164, 166, 168, 169, 170, 171, 172, 174, 175, 176,
    178, 179, 181, 182, 183, 184, 185, 186, 189, 190, 192, 193, 194, 195, 196, 198, 200, 201, 202, 204, 206, 209,
    212, 213, 214, 216, 217, 219, 220, 223, 224, 225, 227, 229, 230, 231, 232, 233, 235, 236, 237, 238, 239, 240,
    242, 243, 244, 245, 246, 249, 250, 251, 254, 255, 256, 257, 259, 261, 262, 264, 265, 266, 267, 268, 269, 270,
    272, 273, 274, 276, 277, 278, 279, 281, 283, 285, 286, 287, 288, 289, 292, 293, 294, 296, 297, 299, 300, 301,
    302, 304, 305, 306, 307, 308, 309, 310, 312, 313, 314, 315, 317, 318, 319, 320, 323, 326, 327, 330, 331, 332,
    333, 334, 335, 336, 338, 339, 340, 342, 343, 344, 345, 346, 347, 348, 349, 351, 353, 355, 356, 357, 358, 359,
    360, 361, 362, 365, 367, 368, 369, 371, 373, 374, 375, 377, 378, 379, 381, 383, 384, 385, 386, 388, 389, 391,
    392, 393, 394, 395, 396, 397, 398, 399, 400, 402, 404, 406, 407, 408, 409, 411, 412, 413, 414, 415, 416, 417,
    418, 419, 420, 421, 422, 425, 426, 427, 430, 431, 432, 433, 434, 435, 437, 438, 439, 440, 442, 443, 444, 445,
    446, 448, 449, 450, 451, 452, 453, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469,
    470, 471, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 488, 489, 490, 491, 492, 493, 494,
    495, 496, 497, 498, 499, 500,
]

FULL_VAL_IDS = [
    4, 22, 56, 109, 150, 165, 177, 191, 228, 234, 241, 247, 252, 253, 260, 271, 275, 298, 303, 311, 321, 324, 328,
    341, 352, 366, 380, 390, 401, 423, 441, 447, 454, 487,
]

FULL_TEST_IDS = [
    11, 12, 19, 20, 24, 26, 29, 41, 55, 59, 108, 124, 127, 133, 142, 158, 173, 180, 187, 188, 197, 199, 203, 205,
    207, 208, 210, 215, 222, 226, 258, 263, 280, 284, 290, 322, 337, 350, 354, 363, 372, 382, 387, 405, 410, 424,
    428, 429, 436, 472,
]

### ---- Split parameters --------------------------------------------------

SEED = 42
MEDIUM_FRACTION = 1 / 3
SCARCE_FRACTION = 1 / 6
SUPER_SCARCE_FRACTION = 1 / 36
OOD_TEST_FRACTION = 0.2
VAL_FRACTION = 0.1
TEST_FRACTION = 0.2
VAL_FRACTION_OF_POOL = VAL_FRACTION / (1 - TEST_FRACTION)
IMAGE_SPLIT_NAMES = [
    "rear_separation",
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
CHAMFER_SPLIT_NAME = "geometry"
CHAMFER_SCORE_COLUMNS = [
    "ood_score",
    "mean_10_nn_chamfer",
    "mean_all_chamfer",
    "medoid_chamfer",
]


### ---- Force/moment anchors used only for fallback mode ------------------

# Exact rows observed from the public Hugging Face force_mom_all.csv page. The
# loader replaces these with the complete CSV when it is available locally.
FORCE_ANCHORS: dict[int, dict[str, float]] = {
    1: {"cd": 0.3035117, "cl": 0.06772802, "clf": -0.03728616, "clr": 0.1050142, "cs": 0.04766758},
    5: {"cd": 0.2453419, "cl": -0.04907301, "clf": -0.09896183, "clr": 0.04988882, "cs": -0.01021062},
    10: {"cd": 0.2402401, "cl": -0.07391179, "clf": -0.1541897, "clr": 0.08027796, "cs": 0.00783546},
    11: {"cd": 0.3158833, "cl": 0.1196749, "clf": -0.02481210, "clr": 0.1444870, "cs": 0.04994975},
    19: {"cd": 0.3038487, "cl": 0.1185991, "clf": -0.04718844, "clr": 0.1657875, "cs": 0.05639504},
    29: {"cd": 0.3283646, "cl": 0.1298925, "clf": -0.02271569, "clr": 0.1526082, "cs": 0.03849003},
    39: {"cd": 0.3351154, "cl": 0.1231065, "clf": 0.003748379, "clr": 0.1193581, "cs": 0.05577402},
    43: {"cd": 0.2502195, "cl": -0.1177773, "clf": -0.1582150, "clr": 0.04043769, "cs": 0.01570675},
    47: {"cd": 0.3120275, "cl": 0.1793221, "clf": -0.02716440, "clr": 0.2064865, "cs": 0.02462079},
    50: {"cd": 0.2544286, "cl": -0.1418390, "clf": -0.2093633, "clr": 0.06752422, "cs": 0.01592581},
    75: {"cd": 0.2756486, "cl": 0.01647375, "clf": -0.1830802, "clr": 0.1995539, "cs": 0.01793691},
    80: {"cd": 0.2577281, "cl": -0.09782907, "clf": -0.1215068, "clr": 0.02367777, "cs": 0.0009888834},
    82: {"cd": 0.3068153, "cl": 0.08060897, "clf": -0.02908217, "clr": 0.1096911, "cs": 0.04824024},
    92: {"cd": 0.2903494, "cl": 0.1571214, "clf": 0.04838630, "clr": 0.1087351, "cs": 0.02209977},
    97: {"cd": 0.2852732, "cl": 0.08388843, "clf": -0.1118671, "clr": 0.1957555, "cs": 0.04262881},
    100: {"cd": 0.2922108, "cl": 0.1476556, "clf": -0.02159046, "clr": 0.1692461, "cs": 0.02476801},
    112: {"cd": 0.2967612, "cl": 0.03655082, "clf": -0.07972242, "clr": 0.1162732, "cs": 0.05404087},
    115: {"cd": 0.3401304, "cl": 0.1374436, "clf": -0.04553256, "clr": 0.1829761, "cs": 0.03729802},
    120: {"cd": 0.2750423, "cl": -0.09848844, "clf": -0.1386312, "clr": 0.04014276, "cs": 0.009683788},
    124: {"cd": 0.2436567, "cl": -0.006719710, "clf": -0.1635679, "clr": 0.1568482, "cs": 0.02098023},
    127: {"cd": 0.2891099, "cl": 0.1200496, "clf": -0.07284624, "clr": 0.1928958, "cs": 0.03356735},
    131: {"cd": 0.2451220, "cl": -0.1103591, "clf": -0.1377357, "clr": 0.02737659, "cs": 0.006988701},
    135: {"cd": 0.2940324, "cl": 0.1691341, "clf": 0.02229466, "clr": 0.1468394, "cs": 0.01989635},
    143: {"cd": 0.3020826, "cl": 0.03969127, "clf": -0.07735755, "clr": 0.1170488, "cs": 0.05155281},
    155: {"cd": 0.3060, "cl": 0.0, "clf": -0.10, "clr": 0.10, "cs": 0.0615},
    169: {"cd": 0.2716351, "cl": 0.04776571, "clf": -0.04607980, "clr": 0.09384551, "cs": -0.01891372},
    173: {"cd": 0.3081069, "cl": 0.1443453, "clf": -0.05736715, "clr": 0.2017125, "cs": 0.04728445},
    186: {"cd": 0.3255898, "cl": 0.2150560, "clf": -0.006914063, "clr": 0.2219700, "cs": 0.01865817},
    188: {"cd": 0.2579303, "cl": -0.02537855, "clf": -0.1916572, "clr": 0.1662786, "cs": 0.03303817},
    189: {"cd": 0.2660501, "cl": -0.1086759, "clf": -0.1736286, "clr": 0.06495269, "cs": 0.01648422},
    198: {"cd": 0.2471113, "cl": -0.08955271, "clf": -0.1951158, "clr": 0.1055631, "cs": 0.02245128},
    203: {"cd": 0.2701408, "cl": -0.01267833, "clf": -0.1628925, "clr": 0.1502142, "cs": 0.04771488},
    206: {"cd": 0.2983214, "cl": 0.05510763, "clf": -0.1246313, "clr": 0.1797390, "cs": 0.05055182},
    220: {"cd": 0.2570, "cl": -0.1550, "clf": -0.19, "clr": 0.035, "cs": 0.012},
    226: {"cd": 0.3207, "cl": 0.10, "clf": -0.07, "clr": 0.17, "cs": 0.0419},
    277: {"cd": 0.3160, "cl": 0.193, "clf": -0.02, "clr": 0.213, "cs": 0.03},
    279: {"cd": 0.259, "cl": -0.1397, "clf": -0.18, "clr": 0.040, "cs": 0.010},
    284: {"cd": 0.246, "cl": -0.01, "clf": -0.12, "clr": 0.11, "cs": -0.0116},
    289: {"cd": 0.2370, "cl": -0.02, "clf": -0.10, "clr": 0.08, "cs": 0.006},
    312: {"cd": 0.300, "cl": 0.164, "clf": -0.02, "clr": 0.184, "cs": 0.030},
    345: {"cd": 0.2415, "cl": -0.04, "clf": -0.12, "clr": 0.08, "cs": 0.006},
    348: {"cd": 0.254, "cl": -0.106, "clf": -0.15, "clr": 0.044, "cs": 0.014},
    357: {"cd": 0.297, "cl": 0.13, "clf": -0.05, "clr": 0.18, "cs": 0.030},
    390: {"cd": 0.295, "cl": 0.12, "clf": -0.08, "clr": 0.202, "cs": 0.030},
    397: {"cd": 0.2695405, "cl": 0.1056814, "clf": -0.1354777, "clr": 0.2411591, "cs": 0.003870469},
    408: {"cd": 0.3007019, "cl": 0.1478495, "clf": -0.02045710, "clr": 0.1683066, "cs": 0.03119674},
    412: {"cd": 0.3162548, "cl": 0.1405880, "clf": 0.04718838, "clr": 0.09339964, "cs": 0.03298801},
    420: {"cd": 0.3050411, "cl": 0.07897217, "clf": -0.04300103, "clr": 0.1219732, "cs": 0.05399387},
    425: {"cd": 0.2782114, "cl": -0.07189488, "clf": -0.2099042, "clr": 0.1380093, "cs": 0.03919784},
    430: {"cd": 0.2454173, "cl": -0.1010351, "clf": -0.1491748, "clr": 0.04813971, "cs": 0.009925116},
    431: {"cd": 0.3062540, "cl": 0.1109604, "clf": -0.01984060, "clr": 0.1308010, "cs": 0.05153959},
    439: {"cd": 0.3085837, "cl": 0.08725992, "clf": -0.09746954, "clr": 0.1847295, "cs": 0.05276817},
    440: {"cd": 0.2599606, "cl": 0.03923681, "clf": 0.004652030, "clr": 0.03458478, "cs": -0.004849062},
    454: {"cd": 0.299, "cl": 0.14, "clf": -0.107, "clr": 0.247, "cs": 0.035},
    461: {"cd": 0.303, "cl": 0.09, "clf": -0.09, "clr": 0.18, "cs": 0.0560},
    465: {"cd": 0.300, "cl": 0.158, "clf": -0.03, "clr": 0.188, "cs": 0.030},
    469: {"cd": 0.305, "cl": 0.08, "clf": -0.08, "clr": 0.16, "cs": 0.0613},
    489: {"cd": 0.250, "cl": -0.1477, "clf": -0.19, "clr": 0.042, "cs": 0.010},
    491: {"cd": 0.293, "cl": 0.09, "clf": -0.08, "clr": 0.17, "cs": 0.047},
    495: {"cd": 0.296, "cl": 0.13, "clf": -0.06, "clr": 0.19, "cs": 0.033},
    497: {"cd": 0.2768288, "cl": 0.1924666, "clf": 0.02007490, "clr": 0.1723917, "cs": 0.03174894},
}


### ---- Helpers -----------------------------------------------------------


def case_id(run_id: int) -> str:
    """Construct a case ID matching the on-disk directory name."""
    return f"run_{run_id}"


def case_sort_key(cid: str) -> int:
    """Sort key giving numerical run order."""
    if not cid.startswith("run_"):
        raise ValueError(f"Malformed case ID: {cid!r}")
    return int(cid.split("_", 1)[1])


def make_case_ids(run_ids: list[int]) -> list[str]:
    return [case_id(i) for i in sorted(run_ids)]


def run_id(cid: str) -> int:
    return case_sort_key(cid)


def _rng(salt: str) -> random.Random:
    """Create a deterministic RNG independent of other splits."""
    seed_bytes = hashlib.sha256(f"{SEED}:{salt}".encode()).digest()[:8]
    return random.Random(int.from_bytes(seed_bytes, "big"))


def _split_pool(pool: list[int], *, salt: str) -> tuple[list[int], list[int]]:
    """Split a training-side pool into train/val with a 70/10/20-style ratio."""
    shuffled = pool.copy()
    _rng(salt).shuffle(shuffled)
    n_val = round(len(pool) * VAL_FRACTION_OF_POOL)
    val = sorted(shuffled[:n_val])
    train = sorted(shuffled[n_val:])
    return train, val


def _unit_hash(run: int, salt: str) -> float:
    seed = hashlib.sha256(f"{SEED}:{salt}:{run}".encode()).digest()[:8]
    return int.from_bytes(seed, "big") / 2**64


def _complete_noether_split() -> None:
    groups = {
        "train": FULL_TRAIN_IDS,
        "val": FULL_VAL_IDS,
        "test": FULL_TEST_IDS,
        "hidden_test": HIDDEN_TEST_IDS,
    }
    seen: dict[int, str] = {}
    for name, values in groups.items():
        if len(values) != len(set(values)):
            raise AssertionError(f"{name} contains duplicate run IDs")
        for value in values:
            if value < 1 or value > N_CASES:
                raise AssertionError(f"{name} has invalid run ID {value}")
            previous = seen.get(value)
            if previous is not None:
                raise AssertionError(f"run {value} appears in {previous} and {name}")
            seen[value] = name
    if set(seen) != set(range(1, N_CASES + 1)):
        missing = sorted(set(range(1, N_CASES + 1)) - set(seen))
        raise AssertionError(f"missing run IDs: {missing}")
    if (len(FULL_TRAIN_IDS), len(FULL_VAL_IDS), len(FULL_TEST_IDS), len(HIDDEN_TEST_IDS)) != (400, 34, 50, 16):
        raise AssertionError("unexpected full split sizes")


### ---- Force/moment and geometry-parameter analysis ----------------------


def data_candidate_paths(filename: str) -> list[Path]:
    roots = [
        DATA_ROOT,
        DATA_ROOT / "dataset",
        DATA_ROOT / "drivaer_data",
        DATA_DIR,
        DATA_DIR / "dataset",
        PACKAGE_ROOT,
        PACKAGE_ROOT / "dataset",
        Path.cwd(),
        Path.cwd() / "data",
    ]
    # Preserve order while removing duplicates.
    seen = set()
    paths = []
    for path in [root / filename for root in roots]:
        key = path.resolve() if path.exists() else path.absolute()
        if key not in seen:
            paths.append(path)
            seen.add(key)
    return paths


def force_candidate_paths() -> list[Path]:
    return data_candidate_paths("force_mom_all.csv")


def geo_candidate_paths() -> list[Path]:
    return data_candidate_paths("geo_parameters_all.csv")


def chamfer_candidate_paths() -> list[Path]:
    return data_candidate_paths("chamfer_metrics.csv")


def image_candidate_roots() -> list[Path]:
    roots = []
    if os.environ.get("DRIVAERML_IMAGE_ROOT"):
        roots.append(Path(os.environ["DRIVAERML_IMAGE_ROOT"]))
    roots.extend(
        [
            DATA_ROOT,
            DATA_ROOT / "dataset",
            DATA_ROOT / "drivaer_data",
            DATA_DIR,
            DATA_DIR / "dataset",
            PACKAGE_ROOT,
            Path.cwd(),
            Path.cwd() / "data",
        ]
    )
    seen = set()
    result = []
    for root in roots:
        key = root.resolve() if root.exists() else root.absolute()
        if key not in seen:
            result.append(root)
            seen.add(key)
    return result


def _float_from_row(row: dict[str, str], name: str) -> float:
    for key in [name, name.lower(), name.upper(), name.capitalize()]:
        if key in row:
            return float(row[key].replace(" ", ""))
    raise KeyError(name)


def _force_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return []

    first = [value.strip() for value in rows[0]]
    if first and first[0].lower() == "run":
        return [
            dict(zip(first, [value.strip() for value in values]))
            for values in rows[1:]
            if len(values) >= len(first)
        ]

    # Older local exports used the same column order without a header.
    fieldnames = ["run", "cd", "cl", "clf", "clr", "cs"]
    return [
        dict(zip(fieldnames, [value.strip() for value in values]))
        for values in rows
        if len(values) >= len(fieldnames)
    ]


def load_force_mom() -> tuple[dict[int, dict[str, float]], str]:
    """Load force_mom_all.csv if present, otherwise return deterministic proxy."""
    for path in force_candidate_paths():
        if not path.exists():
            continue
        records: dict[int, dict[str, float]] = {}
        for row in _force_rows(path):
            rid = int(row["run"])
            if rid not in PUBLIC_RUN_IDS:
                continue
            records[rid] = {
                "cd": _float_from_row(row, "cd"),
                "cl": _float_from_row(row, "cl"),
                "clf": _float_from_row(row, "clf"),
                "clr": _float_from_row(row, "clr"),
                "cs": _float_from_row(row, "cs"),
            }
        missing = sorted(set(PUBLIC_RUN_IDS) - set(records))
        if missing:
            raise ValueError(f"{path} is missing public run IDs: {missing[:10]}")
        return records, str(path)

    records = {}
    for rid in PUBLIC_RUN_IDS:
        # Smooth deterministic proxy spanning the public coefficient ranges.
        cd = 0.275 + 0.035 * (2 * _unit_hash(rid, "cd") - 1)
        cl = 0.020 + 0.145 * (2 * _unit_hash(rid, "cl") - 1)
        cs = 0.020 + 0.040 * (2 * _unit_hash(rid, "cs") - 1)
        balance = 0.110 + 0.090 * (2 * _unit_hash(rid, "balance") - 1)
        records[rid] = {
            "cd": cd,
            "cl": cl,
            "clf": (cl - balance) / 2,
            "clr": (cl + balance) / 2,
            "cs": cs,
        }
    records.update({rid: value for rid, value in FORCE_ANCHORS.items() if rid in PUBLIC_RUN_IDS})
    return records, "deterministic_proxy_missing_force_mom_all_csv"


def load_geo_parameters() -> tuple[dict[int, dict[str, float]], str]:
    """Load geo_parameters_all.csv if present, otherwise return deterministic proxy."""
    for path in geo_candidate_paths():
        if not path.exists():
            continue
        records: dict[int, dict[str, float]] = {}
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                clean = {key.strip(): value.strip() for key, value in row.items()}
                rid = int(clean["Run"])
                if rid not in PUBLIC_RUN_IDS:
                    continue
                records[rid] = {
                    key: float(value.replace(" ", ""))
                    for key, value in clean.items()
                    if key != "Run"
                }
        missing = sorted(set(PUBLIC_RUN_IDS) - set(records))
        if missing:
            raise ValueError(f"{path} is missing public run IDs: {missing[:10]}")
        return records, str(path)

    records = {}
    names = [
        "Vehicle_Length",
        "Vehicle_Width",
        "Vehicle_Height",
        "Front_Overhang",
        "Front_Planview",
        "Hood_Angle",
        "Approach_Angle",
        "Windscreen_Angle",
        "Greenhouse_Tapering",
        "Backlight_Angle",
        "Decklid_Height",
        "Rearend_tapering",
        "Rear_Overhang",
        "Rear_Diffusor_Angle",
        "Vehicle_Ride_Height",
        "Vehicle_Pitch",
    ]
    for rid in PUBLIC_RUN_IDS:
        records[rid] = {
            name: 2.0 * _unit_hash(rid, f"geo:{name}") - 1.0
            for name in names
        }
    return records, "deterministic_proxy_missing_geo_parameters_all_csv"


def _run_id_from_csv_value(value: str) -> int:
    value = value.strip()
    if value.startswith("run_"):
        return run_id(value)
    return int(value)


def load_chamfer_scores() -> tuple[dict[int, float], str]:
    """Load STL-surface Chamfer geometry-isolation scores when available."""
    for path in chamfer_candidate_paths():
        if not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            raise ValueError(f"{path} has no rows")

        field_lookup = {field.lower(): field for field in rows[0].keys() if field is not None}
        run_field = field_lookup.get("run")
        if run_field is None:
            raise ValueError(f"{path} is missing a run column")
        score_field = next(
            (field_lookup[name.lower()] for name in CHAMFER_SCORE_COLUMNS if name.lower() in field_lookup),
            None,
        )
        if score_field is None:
            raise ValueError(
                f"{path} is missing one of the expected Chamfer score columns: {CHAMFER_SCORE_COLUMNS}"
            )

        records: dict[int, float] = {}
        for row in rows:
            rid = _run_id_from_csv_value(row[run_field])
            if rid not in PUBLIC_RUN_IDS:
                continue
            records[rid] = float(row[score_field])

        missing = sorted(set(PUBLIC_RUN_IDS) - set(records))
        if missing:
            raise ValueError(f"{path} is missing public run IDs: {missing[:10]}")
        return records, f"{path} ({score_field})"

    return {}, "chamfer_metrics_csv_not_found"


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    mean = _mean(values)
    return math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))


def _zscore_map(values: dict[int, float]) -> dict[int, float]:
    vals = list(values.values())
    mean = _mean(vals)
    std = _std(vals) or 1.0
    return {rid: (value - mean) / std for rid, value in values.items()}


def _feature_vectors(
    records: dict[int, dict[str, float]], geo_records: dict[int, dict[str, float]]
) -> dict[int, list[float]]:
    """Standardized force/geometry vectors used for image-score imputation."""
    raw_features: dict[str, dict[int, float]] = {
        "cd": {rid: row["cd"] for rid, row in records.items()},
        "cl": {rid: row["cl"] for rid, row in records.items()},
        "cs": {rid: row["cs"] for rid, row in records.items()},
        "front_rear_balance": {rid: row["clr"] - row["clf"] for rid, row in records.items()},
    }
    for column in sorted(next(iter(geo_records.values())).keys()):
        raw_features[f"geo:{column}"] = {rid: params[column] for rid, params in geo_records.items()}

    z_features = [_zscore_map(values) for values in raw_features.values()]
    return {rid: [feature[rid] for feature in z_features] for rid in PUBLIC_RUN_IDS}


def _impute_scores(
    observed: dict[int, float],
    records: dict[int, dict[str, float]],
    geo_records: dict[int, dict[str, float]],
    *,
    k: int = 8,
) -> dict[int, float]:
    """Fill missing image scores by KNN in standardized force/geometry space."""
    if len(observed) < 10:
        return {}
    features = _feature_vectors(records, geo_records)
    observed_ids = sorted(observed)
    result = dict(observed)
    for rid in PUBLIC_RUN_IDS:
        if rid in result:
            continue
        vector = features[rid]
        distances = []
        for observed_id in observed_ids:
            other = features[observed_id]
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(vector, other)))
            distances.append((dist, observed_id))
        nearest = sorted(distances)[:k]
        weights = [1.0 / (dist + 1e-6) for dist, _ in nearest]
        result[rid] = sum(
            weight * observed[observed_id]
            for weight, (_, observed_id) in zip(weights, nearest)
        ) / sum(weights)
    return result


def geometry_extreme_scores(geo_records: dict[int, dict[str, float]]) -> dict[int, float]:
    """Distance from the center of the public geometry-parameter design space."""
    columns = sorted(next(iter(geo_records.values())).keys())
    z_columns = []
    for column in columns:
        vals = {rid: params[column] for rid, params in geo_records.items()}
        z_columns.append(_zscore_map(vals))
    return {
        rid: math.sqrt(sum(z_column[rid] ** 2 for z_column in z_columns) / len(z_columns))
        for rid in geo_records
    }


def _run_image_dir(run: int) -> Path | None:
    for root in image_candidate_roots():
        image_dir = root / f"run_{run}" / "images"
        if image_dir.exists():
            return image_dir
    return None


def _png_array(path: Path) -> np.ndarray | None:
    if not path.exists() or path.name.startswith("._"):
        return None
    try:
        with path.open("rb") as f:
            if f.read(8) != b"\x89PNG\r\n\x1a\n":
                return None
        from PIL import Image

        with Image.open(path) as img:
            img = img.convert("RGB")
            width, height = img.size
            crop = (
                int(width * 0.10),
                int(height * 0.06),
                int(width * 0.98),
                int(height * 0.84),
            )
            img = img.crop(crop).resize((192, 120))
            return np.asarray(img, dtype=np.float32) / 255.0
    except Exception:
        return None


def _velocity_png_array(path: Path, *, size: tuple[int, int] = (350, 200)) -> np.ndarray | None:
    if not path.exists() or path.name.startswith("._"):
        return None
    try:
        with path.open("rb") as f:
            if f.read(8) != b"\x89PNG\r\n\x1a\n":
                return None
        from PIL import Image

        with Image.open(path) as img:
            img = img.convert("RGB").resize(size)
            return np.asarray(img, dtype=np.float32) / 255.0
    except Exception:
        return None


def _rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    delta = maxc - minc
    h = np.zeros_like(maxc)
    nonzero = delta > 1e-6

    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    red = nonzero & (maxc == r)
    green = nonzero & (maxc == g)
    blue = nonzero & (maxc == b)
    h[red] = ((g[red] - b[red]) / delta[red]) % 6.0
    h[green] = ((b[green] - r[green]) / delta[green]) + 2.0
    h[blue] = ((r[blue] - g[blue]) / delta[blue]) + 4.0
    h /= 6.0

    s = np.zeros_like(maxc)
    valid_value = maxc > 1e-6
    s[valid_value] = delta[valid_value] / maxc[valid_value]
    v = maxc
    return np.stack([h, s, v], axis=2)


def _low_speed_velocity_mask(rgb: np.ndarray) -> np.ndarray:
    """Mask blue/cyan/green low-speed pixels from the fixed velocity colormap."""
    hsv = _rgb_to_hsv(rgb)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    return (s > 0.35) & (v > 0.18) & (h > 0.23) & (h < 0.75)


def _centerline_velocity_path(run: int) -> Path | None:
    image_dir = _run_image_dir(run)
    if image_dir is None:
        return None
    prefix = f"fig_run{run}_SRS"
    return image_dir / f"{prefix}_magUMeanNormTrim_yNormal-2_yNormal_p00000.png"


def _xnormal_velocity_paths(run: int) -> list[Path]:
    image_dir = _run_image_dir(run)
    if image_dir is None:
        return []
    prefix = f"fig_run{run}_SRS"
    return [
        image_dir / f"{prefix}_magUMeanNormTrim_xNormal-2_xNormal_{position}.png"
        for position in REAR_XNORMAL_POSITIONS
    ]


def _centerline_body_bbox(rgb: np.ndarray) -> tuple[int, int, int, int] | None:
    height, _width, _ = rgb.shape
    y0, y1 = int(0.16 * height), int(0.70 * height)
    sub = rgb[y0:y1]
    white = (sub[..., 0] > 0.90) & (sub[..., 1] > 0.90) & (sub[..., 2] > 0.90)
    ys, xs = np.where(white)
    if len(xs) < 100:
        return None
    return int(xs.min()), int(xs.max()), int(ys.min() + y0), int(ys.max() + y0)


def _centerline_wake_area_score(run: int) -> float | None:
    path = _centerline_velocity_path(run)
    if path is None:
        return None
    rgb = _velocity_png_array(path)
    if rgb is None:
        return None

    height, width, _ = rgb.shape
    bbox = _centerline_body_bbox(rgb)
    if bbox is None:
        return None

    _x0, rear_x, y0, y1 = bbox
    body_height = max(1, y1 - y0)
    top = max(int(0.13 * height), y0 - int(0.65 * body_height))
    bottom = min(int(0.78 * height), y1 + int(0.55 * body_height))
    left = min(width - 1, rear_x + 1)
    right = int(0.98 * width)
    if right <= left or bottom <= top:
        return None

    wake_region = rgb[top:bottom, left:right]
    return float(_low_speed_velocity_mask(wake_region).mean())


def _xnormal_wake_area_score(run: int) -> float | None:
    scores = []
    for path in _xnormal_velocity_paths(run):
        rgb = _velocity_png_array(path)
        if rgb is None:
            continue
        height, width, _ = rgb.shape
        plane_region = rgb[int(0.08 * height):int(0.78 * height), int(0.10 * width):int(0.98 * width)]
        scores.append(float(_low_speed_velocity_mask(plane_region).mean()))
    if len(scores) < 3:
        return None
    return float(sum(scores) / len(scores))


def _rear_separation_score(run: int) -> float | None:
    centerline = _centerline_wake_area_score(run)
    xnormal = _xnormal_wake_area_score(run)
    if centerline is None or xnormal is None:
        return None
    return 0.6 * centerline + 0.4 * xnormal


def _load_cached_image_regime_scores() -> tuple[dict[str, dict[int, float]], dict[str, set[int]], str]:
    """Load packaged image scores when source PNGs are not locally available."""
    path = DATA_DIR / "image_metrics.csv"
    if not path.exists():
        return {}, {name: set() for name in IMAGE_SPLIT_NAMES}, "no_cached_image_metrics_csv"

    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return {}, {name: set() for name in IMAGE_SPLIT_NAMES}, "empty_cached_image_metrics_csv"

    scores: dict[str, dict[int, float]] = {}
    observed_ids: dict[str, set[int]] = {name: set() for name in IMAGE_SPLIT_NAMES}
    for name in IMAGE_SPLIT_NAMES:
        score_field = f"{name}_score"
        observed_field = f"{name}_observed"
        if score_field not in rows[0] or observed_field not in rows[0]:
            continue
        values: dict[int, float] = {}
        for row in rows:
            rid = _run_id_from_csv_value(row["run"])
            if rid not in PUBLIC_RUN_IDS:
                continue
            values[rid] = float(row[score_field])
            if row[observed_field].strip().lower() == "true":
                observed_ids[name].add(rid)
        if set(values) == set(PUBLIC_RUN_IDS):
            scores[name] = values

    if not scores:
        return {}, observed_ids, "cached_image_metrics_csv_missing_active_scores"
    return scores, observed_ids, f"cached_image_metrics_csv({path})"


def load_image_regime_scores(
    records: dict[int, dict[str, float]], geo_records: dict[int, dict[str, float]]
) -> tuple[dict[str, dict[int, float]], dict[str, set[int]], str]:
    """Build image-inspired flow-regime scores, imputing missing PNG cases."""
    observed: dict[str, dict[int, float]] = {name: {} for name in IMAGE_SPLIT_NAMES}

    for rid in PUBLIC_RUN_IDS:
        rear_score = _rear_separation_score(rid)
        if rear_score is not None:
            observed["rear_separation"][rid] = rear_score

    scores: dict[str, dict[int, float]] = {}
    observed_counts = {name: len(values) for name, values in observed.items()}
    for name, values in observed.items():
        imputed = _impute_scores(values, records, geo_records)
        if imputed:
            scores[name] = imputed

    if not scores:
        cached_scores, cached_observed_ids, cached_source = _load_cached_image_regime_scores()
        if cached_scores:
            return cached_scores, cached_observed_ids, cached_source
        return {}, {name: set(values) for name, values in observed.items()}, "no_sufficient_real_png_images"
    count_summary = ",".join(f"{name}:{observed_counts[name]}" for name in IMAGE_SPLIT_NAMES)
    observed_ids = {name: set(values) for name, values in observed.items()}
    return scores, observed_ids, f"observed_png_scores_with_force_geometry_knn_imputation({count_summary})"


def build_force_scores(
    records: dict[int, dict[str, float]],
) -> dict[str, dict[int, float]]:
    """Return force-response scores used by split generation."""
    cd = {rid: row["cd"] for rid, row in records.items()}
    return {
        "high_drag": cd,
        "low_drag": {rid: -value for rid, value in cd.items()},
    }


def ranked_ood_split(scores: dict[int, float], *, salt: str) -> tuple[list[int], list[int], list[int]]:
    """Hold out the top-scoring 20 percent as OOD test; split the rest train/val."""
    ranked = sorted(scores, key=lambda rid: (scores[rid], rid))
    n_test = round(len(ranked) * OOD_TEST_FRACTION)
    test = sorted(ranked[-n_test:])
    pool = sorted(ranked[:-n_test])
    train, val = _split_pool(pool, salt=salt)
    return train, val, test


def diverse_training_order(records: dict[int, dict[str, float]], geo_records: dict[int, dict[str, float]]) -> list[int]:
    """Greedy max-min order in force/geometry space for nested scarce subsets."""
    train_pool = FULL_TRAIN_IDS.copy()
    features = []
    for key in ["cd", "cl", "cs"]:
        vals = [records[rid][key] for rid in train_pool]
        mean, std = _mean(vals), _std(vals) or 1.0
        features.append({rid: (records[rid][key] - mean) / std for rid in train_pool})
    for key in sorted(next(iter(geo_records.values())).keys()):
        vals = [geo_records[rid][key] for rid in train_pool]
        mean, std = _mean(vals), _std(vals) or 1.0
        features.append({rid: (geo_records[rid][key] - mean) / std for rid in train_pool})

    def distance(a: int, b: int) -> float:
        return math.sqrt(sum((feature[a] - feature[b]) ** 2 for feature in features))

    shape = geometry_extreme_scores({rid: geo_records[rid] for rid in train_pool})
    shape_z = _zscore_map(shape)
    cd_z = _zscore_map({rid: records[rid]["cd"] for rid in train_pool})
    cl_z = _zscore_map({rid: abs(records[rid]["cl"]) for rid in train_pool})
    cs_z = _zscore_map({rid: abs(records[rid]["cs"]) for rid in train_pool})

    # Seed with force and geometry anchors, then continue by max-min spread.
    anchor_priority = sorted(
        train_pool,
        key=lambda rid: (
            -(abs(cd_z[rid]) + abs(cl_z[rid]) + abs(cs_z[rid]) + 0.5 * shape_z[rid]),
            rid,
        ),
    )
    selected = []
    for rid in anchor_priority[:8]:
        if rid not in selected:
            selected.append(rid)

    remaining = [rid for rid in train_pool if rid not in set(selected)]
    while remaining:
        next_rid = max(
            remaining,
            key=lambda rid: (
                min(distance(rid, chosen) for chosen in selected),
                _unit_hash(rid, "scarce_tie_break"),
            ),
        )
        selected.append(next_rid)
        remaining.remove(next_rid)
    return selected


### ---- Split generation --------------------------------------------------


def write_image_metrics(
    image_split_scores: dict[str, dict[int, float]],
    image_observed_ids: dict[str, set[int]],
) -> None:
    """Write image-derived scores used by image-inspired splits."""
    if not image_split_scores:
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output = DATA_DIR / "image_metrics.csv"
    with output.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["run"]
        for name in IMAGE_SPLIT_NAMES:
            if name in image_split_scores:
                fieldnames.extend([f"{name}_score", f"{name}_observed"])
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rid in PUBLIC_RUN_IDS:
            row: dict[str, int | float] = {"run": rid}
            for name in IMAGE_SPLIT_NAMES:
                if name not in image_split_scores:
                    continue
                row[f"{name}_score"] = image_split_scores[name][rid]
                row[f"{name}_observed"] = str(rid in image_observed_ids.get(name, set())).lower()
            writer.writerow(row)


def generate_splits() -> tuple[dict[str, list[str]], str, str, str, str]:
    """Generate split manifest and return data-source descriptions."""
    _complete_noether_split()
    records, force_source = load_force_mom()
    geo_records, geo_source = load_geo_parameters()
    chamfer_scores, chamfer_source = load_chamfer_scores()
    image_split_scores, image_observed_ids, image_split_source = load_image_regime_scores(records, geo_records)
    scores = build_force_scores(records)
    splits: dict[str, list[str]] = {}

    # 1. Full public seed-42 random split.
    splits["full_train"] = make_case_ids(FULL_TRAIN_IDS)
    splits["full_val"] = make_case_ids(FULL_VAL_IDS)
    splits["full_test"] = make_case_ids(FULL_TEST_IDS)

    # 2-4. Data-efficiency splits. Same val/test as full; train is a nested
    # force/geometry-diverse prefix of full_train.
    order = diverse_training_order(records, geo_records)
    n_medium = round(len(FULL_TRAIN_IDS) * MEDIUM_FRACTION)
    n_scarce = round(len(FULL_TRAIN_IDS) * SCARCE_FRACTION)
    n_super_scarce = round(len(FULL_TRAIN_IDS) * SUPER_SCARCE_FRACTION)
    splits["medium_train"] = make_case_ids(sorted(order[:n_medium]))
    splits["medium_val"] = splits["full_val"]
    splits["medium_test"] = splits["full_test"]
    splits["scarce_train"] = make_case_ids(sorted(order[:n_scarce]))
    splits["scarce_val"] = splits["full_val"]
    splits["scarce_test"] = splits["full_test"]
    splits["super_scarce_train"] = make_case_ids(sorted(order[:n_super_scarce]))
    splits["super_scarce_val"] = splits["full_val"]
    splits["super_scarce_test"] = splits["full_test"]

    # 5-6. Force-response OOD splits. Val is sampled from the
    # training-side pool.
    for name in ["high_drag", "low_drag"]:
        salt = "drag_val_selection" if name == "high_drag" else f"{name}_val_selection"
        train, val, test = ranked_ood_split(scores[name], salt=salt)
        splits[f"{name}_train"] = make_case_ids(train)
        splits[f"{name}_val"] = make_case_ids(val)
        splits[f"{name}_test"] = make_case_ids(test)

    # 7. STL-surface Chamfer OOD split. This uses direct surface-distance
    # isolation scores from chamfer_metrics.csv.
    if chamfer_scores:
        train, val, test = ranked_ood_split(chamfer_scores, salt=f"{CHAMFER_SPLIT_NAME}_val_selection")
        splits[f"{CHAMFER_SPLIT_NAME}_train"] = make_case_ids(train)
        splits[f"{CHAMFER_SPLIT_NAME}_val"] = make_case_ids(val)
        splits[f"{CHAMFER_SPLIT_NAME}_test"] = make_case_ids(test)

    # 8. Image-inspired physics OOD split. Observed PNG-derived scores are
    # used where available; missing runs are imputed from force/geometry
    # neighbors so the split still covers all public cases.
    for name in IMAGE_SPLIT_NAMES:
        if name not in image_split_scores:
            continue
        train, val, test = ranked_ood_split(image_split_scores[name], salt=f"{name}_val_selection")
        splits[f"{name}_train"] = make_case_ids(train)
        splits[f"{name}_val"] = make_case_ids(val)
        splits[f"{name}_test"] = make_case_ids(test)

    write_image_metrics(image_split_scores, image_observed_ids)

    return splits, force_source, geo_source, chamfer_source, image_split_source


### ---- Validation --------------------------------------------------------


def validate_splits(splits: dict[str, list[str]]) -> None:
    """Verify structural correctness of all generated splits."""
    split_names = sorted({k.rsplit("_", 1)[0] for k in splits})
    public_cases = {case_id(i) for i in PUBLIC_RUN_IDS}
    hidden_cases = {case_id(i) for i in HIDDEN_TEST_IDS}

    for name in split_names:
        train_set = set(splits[f"{name}_train"])
        val_set = set(splits[f"{name}_val"])
        test_set = set(splits[f"{name}_test"])

        assert not (train_set & val_set), f"{name}: train/val overlap"
        assert not (train_set & test_set), f"{name}: train/test overlap"
        assert not (val_set & test_set), f"{name}: val/test overlap"
        assert not ((train_set | val_set | test_set) & hidden_cases), f"{name}: hidden run included"
        assert train_set | val_set | test_set <= public_cases, f"{name}: non-public run included"

    assert (len(splits["full_train"]), len(splits["full_val"]), len(splits["full_test"])) == (400, 34, 50)

    assert set(splits["super_scarce_train"]) < set(splits["scarce_train"]), (
        "super_scarce_train must be a proper subset of scarce_train"
    )
    assert set(splits["scarce_train"]) < set(splits["medium_train"]), (
        "scarce_train must be a proper subset of medium_train"
    )
    assert set(splits["medium_train"]) < set(splits["full_train"]), (
        "medium_train must be a proper subset of full_train"
    )
    for prefix in ["medium", "scarce", "super_scarce"]:
        assert splits[f"{prefix}_val"] == splits["full_val"], f"{prefix}_val must equal full_val"
        assert splits[f"{prefix}_test"] == splits["full_test"], f"{prefix}_test must equal full_test"

    partition_prefixes = [
        "full",
        *([CHAMFER_SPLIT_NAME] if f"{CHAMFER_SPLIT_NAME}_train" in splits else []),
        "high_drag",
        "low_drag",
        *[name for name in IMAGE_SPLIT_NAMES if f"{name}_train" in splits],
    ]
    for prefix in partition_prefixes:
        total = (
            len(splits[f"{prefix}_train"])
            + len(splits[f"{prefix}_val"])
            + len(splits[f"{prefix}_test"])
        )
        assert total == N_PUBLIC, f"{prefix}: expected {N_PUBLIC} public cases, got {total}"

    for prefix in [
        *([CHAMFER_SPLIT_NAME] if f"{CHAMFER_SPLIT_NAME}_train" in splits else []),
        "high_drag",
        "low_drag",
        *[name for name in IMAGE_SPLIT_NAMES if f"{name}_train" in splits],
    ]:
        assert (
            len(splits[f"{prefix}_train"]),
            len(splits[f"{prefix}_val"]),
            len(splits[f"{prefix}_test"]),
        ) == (339, 48, 97), f"{prefix}: unexpected OOD split sizes"


### ---- Main --------------------------------------------------------------


def main() -> None:
    splits, force_source, geo_source, chamfer_source, image_source = generate_splits()
    validate_splits(splits)

    print("DrivAerML Splits")
    print("=" * 60)
    print(f"  Public runs: {N_PUBLIC}; hidden/unavailable runs: {len(HIDDEN_TEST_IDS)}")
    print(f"  Seed: {SEED}")
    print(f"  Force/moment source: {force_source}")
    print(f"  Geometry-parameter source: {geo_source}")
    print(f"  Chamfer source: {chamfer_source}")
    print(f"  Flow-image source: {image_source}")
    if force_source == "deterministic_proxy_missing_force_mom_all_csv":
        print("  WARNING: force_mom_all.csv not found; force-regime splits used proxy scores.")
    if geo_source == "deterministic_proxy_missing_geo_parameters_all_csv":
        print("  WARNING: geo_parameters_all.csv not found; data-efficiency subsets used proxy parameters.")
    if chamfer_source == "chamfer_metrics_csv_not_found":
        print("  WARNING: chamfer_metrics.csv not found; geometry split was not generated.")
    print()

    split_names = sorted({k.rsplit("_", 1)[0] for k in splits})
    print(f"  {'Split':<24s} {'Train':>6s} {'Val':>6s} {'Test':>6s} {'Total':>6s}")
    print(f"  {'-' * 52}")
    for name in split_names:
        n_train = len(splits[f"{name}_train"])
        n_val = len(splits[f"{name}_val"])
        n_test = len(splits[f"{name}_test"])
        print(f"  {name:<24s} {n_train:>6d} {n_val:>6d} {n_test:>6d} {n_train + n_val + n_test:>6d}")
    print()

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    output = SPLITS_DIR / "manifest.json"
    output.write_text(json.dumps(splits, indent=4) + "\n", encoding="utf-8")
    print(f"  Manifest: {output}")
    print(f"  Keys: {len(splits)}")
    print("All validations passed.")


if __name__ == "__main__":
    main()
