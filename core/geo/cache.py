from functools import lru_cache
from config import GEO_CACHE_SIZE


@lru_cache(maxsize=GEO_CACHE_SIZE)
def _cached_query(layer_name: str, minx: float, miny: float,
                  maxx: float, maxy: float,
                  simplify: float, limit: int) -> str:
    import json
    from core.geo.query import query_layer
    from config import LAYERS
    result = query_layer(LAYERS[layer_name], minx, miny, maxx, maxy, simplify, limit)
    return json.dumps(result)


def get_cached_chunk(layer_name: str, minx: float, miny: float,
                     maxx: float, maxy: float,
                     simplify: float, limit: int) -> tuple[dict, bool]:
    import json

    key_minx = round(minx, 4)
    key_miny = round(miny, 4)
    key_maxx = round(maxx, 4)
    key_maxy = round(maxy, 4)

    info_before = _cached_query.cache_info()
    raw = _cached_query(layer_name, key_minx, key_miny,
                        key_maxx, key_maxy, simplify, limit)
    info_after = _cached_query.cache_info()

    from_cache = info_after.hits > info_before.hits
    return json.loads(raw), from_cache


def cache_info() -> dict:
    info = _cached_query.cache_info()
    return {
        "hits":    info.hits,
        "misses":  info.misses,
        "size":    info.currsize,
        "maxsize": info.maxsize,
    }