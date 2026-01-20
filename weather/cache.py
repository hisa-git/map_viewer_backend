import time
from typing import Dict, Tuple, List

weather_cache: Dict[Tuple[float, float], dict] = {}

def set_weather(lat: float, lon: float, data: dict):
    weather_cache[(lat, lon)] = {
        **data,
        "updated_at": int(time.time())
    }

def get_weather(lat: float, lon: float) -> dict | None:
    return weather_cache.get((lat, lon))

def get_weather_in_bbox(
    min_lat: float, max_lat: float,
    min_lon: float, max_lon: float,
    step: float = None
) -> List[dict]:
    result = []
    for (lat, lon), data in weather_cache.items():
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            result.append({
                "lat": lat,
                "lon": lon,
                **data
            })
    return result
