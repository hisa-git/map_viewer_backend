# Map Viewer Backend

Backend service for the Map Viewer application.

The service provides vector map layers (buildings, roads, water), geospatial chunk queries, and aggregated weather data for the frontend. All spatial data is normalized to a common projection and optimized for fast bounding-box queries.

## Stack

- Python
- FastAPI
- Uvicorn
- GeoPandas
- Shapely
- PyProj
- HTTPX

## Data and Coordinate System

The backend works internally in **Web Mercator (EPSG:3857)**.

Source datasets may be provided in different formats and coordinate systems (Shapefile, GeoJSON, with or without CRS defined), but **all layers are automatically converted to EPSG:3857 at load time**.

If a dataset has no CRS defined, it is assumed to be **EPSG:4326 (WGS84)**.

Supported input formats:

- `.shp` (ESRI Shapefile)
- `.geojson`

An R-tree spatial index is built for each layer after loading.

## Required Data

Download OpenStreetMap-based datasets from GeoFabrik:

[https://download.geofabrik.de/europe.html](https://download.geofabrik.de/europe.html)

Example directory structure:

```
data/
├── ukraine-251121-free.shp/
│   ├── gis_osm_buildings_a_free_1.shp
│   ├── gis_osm_water_a_free_1.shp
│   └── ...
├── roads.geojson
```

## Environment Configuration

Weather region settings are configured via environment variables.

Create a `.env` file in the project root:

```
WEATHER_CITY=Mykolaiv
WEATHER_MIN_LAT=46.8
WEATHER_MAX_LAT=47.2
WEATHER_MIN_LON=31.5
WEATHER_MAX_LON=32.5
WEATHER_GRID_STEP=0.05
WEATHER_UPDATE_INTERVAL=1800
```

Example above describes the **Mykolaiv region (Ukraine)**.

All values are loaded at runtime and used to generate the weather grid.
This allows changing the target city or region **without modifying code**.

## Data Loading Logic

At startup the backend:

1. Reads vector files using GeoPandas
2. Detects or assigns CRS
3. Reprojects all layers to EPSG:3857
4. Builds spatial indexes for fast bounding box queries

This logic is implemented in `load_layer()`.

## API Endpoints

GET /chunk?layer=buildings&minx=…&miny=…&maxx=…&maxy=…&simplify=…&limit=…
Generic endpoint for any layer

GET /chunk/buildings
GET /chunk/roads
GET /chunk/water

GET /bounds
Returns total bounds for all available layers

GET /weather/area?min_lat=…&max_lat=…&min_lon=…&max_lon=…&step=…
Aggregated weather data for a geographic region

All spatial query coordinates must be provided in **EPSG:3857** unless stated otherwise.

## Running

Install dependencies:

```
pip install -r requirements.txt
```

Start the server:

```
uvicorn main:app
```
