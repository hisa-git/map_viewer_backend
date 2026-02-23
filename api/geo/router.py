import time
from fastapi import APIRouter, Query, HTTPException

from core.geo.cache import get_cached_chunk, cache_info
from core.geo.reader import get_layer_bounds
from core.metrics import REQUEST_COUNT
from config import LAYERS, LAYER_DEFAULTS, MAX_BBOX_AREA

router = APIRouter()


def _check_bbox(minx: float, miny: float, maxx: float, maxy: float):
    area = abs((maxx - minx) * (maxy - miny))
    if area > MAX_BBOX_AREA:
        raise HTTPException(400, f"BBox too large ({area:.0f}), reduce area.")


def _run(layer_name: str, minx: float, miny: float, maxx: float, maxy: float,
         simplify: float, limit: int) -> dict:
    _check_bbox(minx, miny, maxx, maxy)
    t0 = time.perf_counter()
    result, from_cache = get_cached_chunk(layer_name, minx, miny, maxx, maxy, simplify, limit)
    result.setdefault("metadata", {})
    result["metadata"]["query_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    result["metadata"]["from_cache"] = from_cache
    return result


@router.get("/chunk")
def get_chunk(
    minx: float, miny: float, maxx: float, maxy: float,
    simplify: float = Query(1.0),
    layer: str = Query("buildings"),
):
    REQUEST_COUNT.labels(endpoint="/chunk").inc()
    name = layer.lower()
    matched = next((k for k in LAYERS if k.startswith(name[0])), None)
    if not matched:
        raise HTTPException(400, f"Unknown layer: {layer}")
    d = LAYER_DEFAULTS[matched]
    return _run(matched, minx, miny, maxx, maxy, simplify, d["limit"])


@router.get("/chunk/buildings")
def chunk_buildings(
    minx: float, miny: float, maxx: float, maxy: float,
    simplify: float = 1.0, limit: int = 10000,
):
    REQUEST_COUNT.labels(endpoint="/chunk/buildings").inc()
    return _run("buildings", minx, miny, maxx, maxy, simplify, limit)


@router.get("/chunk/roads")
def chunk_roads(
    minx: float, miny: float, maxx: float, maxy: float,
    simplify: float = 0.0, limit: int = 5000,
):
    REQUEST_COUNT.labels(endpoint="/chunk/roads").inc()
    return _run("roads", minx, miny, maxx, maxy, simplify, limit)


@router.get("/chunk/water")
def chunk_water(
    minx: float, miny: float, maxx: float, maxy: float,
    simplify: float = 0.5, limit: int = 5000,
):
    REQUEST_COUNT.labels(endpoint="/chunk/water").inc()
    return _run("water", minx, miny, maxx, maxy, simplify, limit)


@router.get("/bounds")
def get_bounds():
    REQUEST_COUNT.labels(endpoint="/bounds").inc()
    return {name: list(get_layer_bounds(path)) for name, path in LAYERS.items()}


@router.get("/cache/stats")
def get_cache_stats():
    return cache_info()