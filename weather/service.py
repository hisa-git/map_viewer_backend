import httpx
from typing import Dict

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

async def fetch_weather(lat: float, lon: float) -> Dict:
    """Fetch current weather for a single point"""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(OPEN_METEO_URL, params=params)
        r.raise_for_status()
        data = r.json()

    current = data.get("current_weather", {})
    return {
        "lat": lat,
        "lon": lon,
        "temperature": current.get("temperature"),
        "humidity": current.get("humidity"),
    }
