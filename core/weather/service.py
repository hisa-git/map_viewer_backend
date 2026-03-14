import httpx
from datetime import datetime, timezone
from typing import Dict, List, Optional
from .cache import get_weather, set_weather

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

FIELDS_CONFIG = {
    "temperature": "current_weather",
    "windspeed": "current_weather",
    "winddirection": "current_weather",
    "humidity": "hourly:relativehumidity_2m",
    "pressure": "hourly:pressure_msl",
}


class WeatherSource:
    async def fetch(self, lat: float, lon: float) -> Dict:
        raise NotImplementedError


class OpenMeteoSource(WeatherSource):
    HOURLY_FIELDS = [v.split(":", 1)[1] for v in FIELDS_CONFIG.values() if v.startswith("hourly:")]

    async def fetch(self, lat: float, lon: float) -> Dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": any(v == "current_weather" for v in FIELDS_CONFIG.values()),
            "hourly": ",".join(self.HOURLY_FIELDS) if self.HOURLY_FIELDS else None,
            "timezone": "auto",
        }
        params = {k: v for k, v in params.items() if v is not None}

        async with httpx.AsyncClient(timeout=20) as client:
            try:
                resp = await client.get(OPEN_METEO_URL, params=params)
                resp.raise_for_status()
                return resp.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                return {"error": str(e)}


async def fetch_weather(lat: float, lon: float, source: WeatherSource) -> dict:
    cached = get_weather(lat, lon)
    now_ts = int(datetime.now(timezone.utc).timestamp())

    if cached and cached.get("updated_at", 0) > now_ts - 3600:
        return cached

    data = await source.fetch(lat, lon)
    result: Dict[str, Optional[float]] = {"lat": lat, "lon": lon}

    current = data.get("current_weather", {})
    for field, source_field in FIELDS_CONFIG.items():
        if source_field == "current_weather":
            result[field] = current.get(field)

    hourly = data.get("hourly", {})
    times: List[str] = hourly.get("time", [])
    if times:
        now = datetime.now(timezone.utc)
        closest_idx = min(
            range(len(times)),
            key=lambda i: abs(datetime.fromisoformat(times[i]).replace(tzinfo=timezone.utc) - now))
        for field, source_field in FIELDS_CONFIG.items():
            if source_field.startswith("hourly:"):
                param_name = source_field.split(":", 1)[1]
                values = hourly.get(param_name, [])
                result[field] = values[closest_idx] if values else None

    set_weather(lat, lon, result)
    return result