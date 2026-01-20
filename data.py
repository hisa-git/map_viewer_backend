import geopandas as gpd
from pyproj import Transformer

BUILDINGS_PATH = "../data/ukraine-251121-free.shp/gis_osm_buildings_a_free_1.shp"
ROADS_PATH = "../data/roads.geojson"
WATER_PATH = "../data/ukraine-251121-free.shp/gis_osm_water_a_free_1.shp"


def load_layer(path, force_crs=None):
    g = gpd.read_file(path)
    print(f"[LOAD] {path}")
    print(f"  Original CRS: {g.crs}")
    print(f"  Bounds: {g.total_bounds}")
    
    if g.crs is None:
        print(f"  WARNING: No CRS, assuming EPSG:4326")
        g = g.set_crs(4326)
    
    if force_crs:
        g = g.to_crs(force_crs)
    
    g = g.to_crs(3857)
    print(f"  After conversion: {g.crs}")
    print(f"  New bounds: {g.total_bounds}")
    
    _ = g.sindex
    return g

buildings = load_layer(BUILDINGS_PATH)
roads = load_layer(ROADS_PATH)
water = load_layer(WATER_PATH)

to_m = Transformer.from_crs(4326, 3857, always_xy=True)
to_wgs = Transformer.from_crs(3857, 4326, always_xy=True)