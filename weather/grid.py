from typing import List, Tuple

def generate_grid(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    step: float
) -> List[Tuple[float, float]]:
    points = []
    lat = min_lat
    while lat <= max_lat:
        lon = min_lon
        while lon <= max_lon:
            points.append((round(lat, 5), round(lon, 5)))
            lon += step
        lat += step
    return points
