from pathlib import Path
import numpy as np
from shapely.geometry import box
from pyproj import Transformer

from core.geo.reader import read_layer_bbox

WGS84 = 4326
EPSG3857 = 3857

_to_m   = Transformer.from_crs(WGS84, EPSG3857, always_xy=True)
#_to_wgs = Transformer.from_crs(EPSG3857, WGS84, always_xy=True)


def _wgs_bbox_to_meters(minx: float, miny: float,
                         maxx: float, maxy: float
                         ) -> tuple[float, float, float, float]:
    minx_m, miny_m = _to_m.transform(minx, miny)
    maxx_m, maxy_m = _to_m.transform(maxx, maxy)
    if minx_m > maxx_m:
        minx_m, maxx_m = maxx_m, minx_m
    if miny_m > maxy_m:
        miny_m, maxy_m = maxy_m, miny_m
    return minx_m, miny_m, maxx_m, maxy_m


def query_layer(path: Path,
                minx: float, miny: float, maxx: float, maxy: float,
                simplify: float, limit: int) -> dict:
    minx_m, miny_m, maxx_m, maxy_m = _wgs_bbox_to_meters(minx, miny, maxx, maxy)

    gdf = read_layer_bbox(path, minx_m, miny_m, maxx_m, maxy_m)

    empty = {"type": "FeatureCollection", "features": [], "metadata": {"count": 0}}
    if gdf.empty:
        return empty

    region = box(minx_m, miny_m, maxx_m, maxy_m)
    gdf = gdf[gdf.intersects(region)]
    if gdf.empty:
        return empty

    if limit and len(gdf) > limit:
        gdf = gdf.sample(n=limit, random_state=42)

    if simplify > 0:
        gdf = gdf.assign(
            geometry=gdf.geometry.simplify(simplify, preserve_topology=True)
        )

    gdf = gdf.to_crs(WGS84)

    features = [
        {
            "type": "Feature",
            "geometry": geom.__geo_interface__,
            "properties": props,
        }
        for geom, props in zip(
            gdf.geometry,
            gdf.drop(columns="geometry").to_dict("records"),
        )
    ]

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {"count": len(features)},
    }