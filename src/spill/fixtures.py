"""Synthetic RTC scenes so the pipeline can run without SNAP or Earthdata."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from pyproj import Transformer
from rasterio.transform import Affine

from spill.preprocess import from_db, write_geotiff
from spill.sites import AREA_CRS, WGS84


def _utm_center(lon: float, lat: float) -> tuple[float, float]:
    t = Transformer.from_crs(WGS84, AREA_CRS, always_xy=True)
    return t.transform(lon, lat)


def build_synthetic_db(
    rows: int = 256,
    cols: int = 256,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Land rim, mid-tone water, textured oil ellipse, low-texture look-alike."""
    rng = rng or np.random.default_rng(7)
    yy, xx = np.mgrid[0:rows, 0:cols]
    db = np.full((rows, cols), -18.0)
    land = (xx < 18) | (yy < 18) | (xx > cols - 19) | (yy > rows - 19)
    db[land] = -8.0
    cy, cx = rows // 2, cols // 2
    oil = ((yy - cy) / 22.0) ** 2 + ((xx - cx) / 40.0) ** 2 <= 1.0
    texture = 2.6 * np.sin(xx / 2.4) * np.sin(yy / 3.1)
    db[oil] = -28.0 + texture[oil]
    look_y, look_x = int(rows * 0.22), int(cols * 0.78)
    look = (np.abs(yy - look_y) < 22) & (np.abs(xx - look_x) < 22)
    look = look & ~land & ~oil
    db[look] = -27.2
    speckle = rng.normal(0.0, 0.35, size=db.shape)
    db = db + speckle
    db[look] = -27.2 + rng.normal(0.0, 0.02, size=db[look].shape)
    db[land] = -8.0 + rng.normal(0.0, 0.2, size=db[land].shape)
    return db


def write_synthetic_rtc(site: dict, path: Path, res_m: float = 10.0) -> dict:
    """Write a GeoTIFF in UTM 31N centred on the site point, plus a sidecar JSON."""
    db = build_synthetic_db()
    linear = from_db(db)
    x, y = _utm_center(float(site["lon"]), float(site["lat"]))
    rows, cols = linear.shape
    west = x - (cols / 2.0) * res_m
    north = y + (rows / 2.0) * res_m
    transform = Affine(res_m, 0.0, west, 0.0, -res_m, north)
    write_geotiff(path, linear, transform, AREA_CRS)
    meta = {
        "site_id": site["id"],
        "scene_source": "synthetic_rtc_fixture",
        "crs": AREA_CRS,
        "res_m": res_m,
        "note": "Not Sentinel-1. Land/water/oil/look-alike constructed so detection and the GLCM filter can be tested. Do not quote fixture km2 as a spill area.",
    }
    sidecar = path.with_suffix(".json")
    sidecar.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta
