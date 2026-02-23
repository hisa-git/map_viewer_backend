from fastapi import APIRouter
from core.metrics import REQUEST_COUNT
from core.weather.cache import get_weather_in_bbox

router = APIRouter()


@router.get("/weather/area")
async def weather_area(
    min_lat: float, max_lat: float,
    min_lon: float, max_lon: float,
    step: float = 0.05,
):
    REQUEST_COUNT.labels(endpoint="/weather/area").inc()
    points = get_weather_in_bbox(min_lat, max_lat, min_lon, max_lon, step)
    return {"points": points}