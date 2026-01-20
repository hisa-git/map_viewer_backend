import asyncio
import os
from .grid import generate_grid
from .service import fetch_weather
from .cache import set_weather, weather_cache

CITY_NAME = os.getenv("WEATHER_CITY")

REGION = {
    "min_lat": float(os.getenv("WEATHER_MIN_LAT")),
    "max_lat": float(os.getenv("WEATHER_MAX_LAT")),
    "min_lon": float(os.getenv("WEATHER_MIN_LON")),
    "max_lon": float(os.getenv("WEATHER_MAX_LON")),
}

GRID_STEP = float(os.getenv("WEATHER_GRID_STEP", 0.05))
UPDATE_INTERVAL = int(os.getenv("WEATHER_UPDATE_INTERVAL", 1800))

async def weather_updater():
    if CITY_NAME:
        print(f"Starting weather updater for {CITY_NAME} region...")
    else:
        print("Starting weather updater for configured region...")
    
    grid = generate_grid(
        REGION["min_lat"],
        REGION["max_lat"],
        REGION["min_lon"],
        REGION["max_lon"],
        GRID_STEP
    )

    print(f"Generated grid with {len(grid)} points for region {REGION}")

    while True:
        tasks = [fetch_weather(lat, lon) for lat, lon in grid]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                continue
            set_weather(result["lat"], result["lon"], result)

        print(f"Weather updated. Cache size: {len(weather_cache)}")
        await asyncio.sleep(UPDATE_INTERVAL)
