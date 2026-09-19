"""Polygonize dark-spot masks and compute slick area in UTM metres."""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape

from spill.sites import AREA_CRS, WGS84


def mask_to_polygons(
    mask: np.ndarray,
    transform: rasterio.Affine,
    crs: str,
) -> gpd.GeoDataFrame:
    geoms = []
    for geom, value in shapes(mask.astype(np.uint8), mask=mask, transform=transform):
        if int(value) != 1:
            continue
        geoms.append(shape(geom))
    if not geoms:
        return gpd.GeoDataFrame(columns=["geometry", "area_km2"], geometry="geometry", crs=crs)
    gdf = gpd.GeoDataFrame({"geometry": geoms}, crs=crs)
    if gdf.crs is None:
        gdf = gdf.set_crs(crs)
    metric = gdf.to_crs(AREA_CRS)
    gdf["area_km2"] = metric.area.to_numpy() / 1e6
    gdf = gdf.to_crs(WGS84)
    gdf = gdf.dissolve().explode(index_parts=False).reset_index(drop=True)
    metric = gdf.to_crs(AREA_CRS)
    gdf["area_km2"] = metric.area.to_numpy() / 1e6
    gdf["slick_id"] = np.arange(1, len(gdf) + 1)
    return gdf
