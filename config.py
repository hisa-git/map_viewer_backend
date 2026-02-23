from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "data"

LAYERS: dict[str, Path] = {
    "buildings": DATA_DIR / "buildings_3857.fgb",
    "roads":     DATA_DIR / "roads_3857.fgb",
    "water":     DATA_DIR / "water_3857.fgb",
}

LAYER_DEFAULTS: dict[str, dict] = {
    "buildings": {"simplify": 1.0,  "limit": 10000},
    "roads":     {"simplify": 0.0,  "limit": 5000},
    "water":     {"simplify": 0.5,  "limit": 5000},
}

MAX_BBOX_AREA = 1_000_000_000

GEO_CACHE_SIZE = 40