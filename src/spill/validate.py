"""NOSDRA/community point vs delineated footprint."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Point

from spill.sites import AREA_CRS, HIT_DISTANCE_M, WGS84


def validate_point(
    footprints: gpd.GeoDataFrame,
    lon: float,
    lat: float,
    hit_distance_m: float = HIT_DISTANCE_M,
) -> dict:
    point = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs=WGS84).to_crs(AREA_CRS)
    pt = point.geometry.iloc[0]
    if footprints is None or footprints.empty:
        return {
            "nosdra_point_in_footprint": False,
            "hit": False,
            "distance_to_nearest_slick_m": None,
            "hit_distance_m": hit_distance_m,
            "nearest_slick_id": None,
        }
    metric = footprints.to_crs(AREA_CRS)
    distances = metric.distance(pt)
    nearest_i = int(distances.idxmin())
    nearest_m = float(distances.min())
    inside = bool(metric.contains(pt).any() or metric.covers(pt).any())
    hit = inside or nearest_m <= hit_distance_m
    slick_id = metric.loc[nearest_i, "slick_id"] if "slick_id" in metric.columns else nearest_i
    return {
        "nosdra_point_in_footprint": inside,
        "hit": hit,
        "distance_to_nearest_slick_m": nearest_m,
        "hit_distance_m": hit_distance_m,
        "nearest_slick_id": int(slick_id) if slick_id is not None else None,
    }
