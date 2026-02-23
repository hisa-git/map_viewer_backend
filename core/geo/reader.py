from pathlib import Path
import geopandas as gpd
import fiona

_bounds_cache: dict[str, tuple] = {}


def read_layer_bbox(path: Path, minx_m: float, miny_m: float,
                    maxx_m: float, maxy_m: float) -> gpd.GeoDataFrame:
    return gpd.read_file(str(path), bbox=(minx_m, miny_m, maxx_m, maxy_m))


def get_layer_bounds(path: Path) -> tuple[float, float, float, float]:
    key = str(path)
    if key not in _bounds_cache:
        with fiona.open(key) as src:
            _bounds_cache[key] = src.bounds
    return _bounds_cache[key]