import httpx
from typing import Dict

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

async def fetch_weather(lat: float, lon: float) -> Dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "relativehumidity_2m",
    }


    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(OPEN_METEO_URL, params=params)
        r.raise_for_status()
        data = r.json()

    current = data.get("current_weather", {})

    humidity = None
    hourly = data.get("hourly")
    if hourly:
        humidity_values = hourly.get("relativehumidity_2m")
        if humidity_values and len(humidity_values) > 0:
            humidity = humidity_values[0]

    return {
        "lat": lat,
        "lon": lon,
        "temperature": current.get("temperature"),
        "humidity": humidity,
    }
