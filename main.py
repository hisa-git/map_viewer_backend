from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import time
import asyncio
from weather.cache import get_weather_in_bbox
from weather.updater import weather_updater

from data import buildings, roads, water, to_m, to_wgs
from query import query_layer

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def start_updater():
    asyncio.create_task(weather_updater())

def run(layer, *args):
    t0 = time.time()
    r = query_layer(layer, *args)
    r.setdefault("metadata", {})
    r["metadata"]["query_ms"] = round((time.time()-t0)*1000, 2)
    return r


@app.get("/chunk")
def get_chunk(
    minx: float, miny: float, maxx: float, maxy: float,
    simplify: float = Query(1.0),
    limit: int = Query(10000),
    layer: str = Query("buildings")
):
    lname = layer.lower()
    if lname.startswith("b"):
        l = buildings
    elif lname.startswith("r"):
        l = roads
    elif lname.startswith("w"):
        l = water
    else:
        return {"error": "unknown layer", "layer": layer}

    return run(l, minx, miny, maxx, maxy, simplify, limit)


@app.get("/chunk/buildings")
def c_b(minx: float, miny: float, maxx: float, maxy: float,
        simplify: float = 1.0, limit: int = 10000):
    return run(buildings, minx, miny, maxx, maxy, simplify, limit)


@app.get("/chunk/roads")
def c_r(minx: float, miny: float, maxx: float, maxy: float,
        simplify: float = 0.0, limit: int = 5000):
    return run(roads, minx, miny, maxx, maxy, simplify, limit)


@app.get("/chunk/water")
def c_w(minx: float, miny: float, maxx: float, maxy: float,
        simplify: float = 0.5, limit: int = 5000):
    return run(water, minx, miny, maxx, maxy, simplify, limit)


@app.get("/bounds")
def get_bounds():
    return {
        "buildings": buildings.total_bounds.tolist(),
        "roads": roads.total_bounds.tolist(),
        "water": water.total_bounds.tolist()
    }

@app.get("/weather/area")
async def weather_area(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    step: float = 0.05,
):
    points = get_weather_in_bbox(min_lat, max_lat, min_lon, max_lon, step)
    return {"points": points} 