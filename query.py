from shapely.geometry import box
from pyproj import Transformer

TARGET_CRS = 3857
WGS84 = 4326

to_m = Transformer.from_crs(WGS84, TARGET_CRS, always_xy=True)
to_wgs = Transformer.from_crs(TARGET_CRS, WGS84, always_xy=True)


def query_layer(layer, minx, miny, maxx, maxy, simplify, limit):
    minx_m, miny_m = to_m.transform(minx, miny)
    maxx_m, maxy_m = to_m.transform(maxx, maxy)

    if minx_m > maxx_m:
        minx_m, maxx_m = maxx_m, minx_m
    if miny_m > maxy_m:
        miny_m, maxy_m = maxy_m, miny_m

    region = box(minx_m, miny_m, maxx_m, maxy_m)

    candidates = list(layer.sindex.intersection(region.bounds))
    if not candidates:
        return {"type": "FeatureCollection", "features": [], "metadata": {"count": 0}}

    sel = layer.iloc[candidates]
    sel = sel[sel.intersects(region)]

    sel = sel.copy()

    if limit and len(sel) > limit:
        sel = sel.sample(n=limit, random_state=42)

    if simplify > 0:
        sel = sel.copy()
        sel["geometry"] = sel["geometry"].apply(lambda g: g.simplify(simplify, preserve_topology=True))

    sel = sel.to_crs(WGS84)

    feats = []
    for _, row in sel.iterrows():
        feats.append({"type": "Feature", "geometry": row.geometry.__geo_interface__, "properties": row.drop(labels=["geometry"]).to_dict()})

    return {"type": "FeatureCollection", "features": feats, "metadata": {"count": len(feats)}}