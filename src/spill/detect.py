"""Water mask and Otsu dark-spot detection on log sigma0."""

from __future__ import annotations

import numpy as np
from pyproj import Transformer
from rasterio.transform import rowcol, xy
from skimage.filters import threshold_otsu
from skimage.morphology import disk, opening, remove_small_objects

from spill.sites import AREA_CRS, WGS84

# v2: swamp / creek, not open-ocean marine prior.
DETECTOR_VERSION = "v2_local_water"
CHANGE_DETECTOR_VERSION = "v3_prepost"
SEARCH_RADIUS_M = 3000.0
OIL_MARGIN_DB = 2.0
OIL_DB_MAX = -18.0
CHANGE_MARGIN_DB = 2.0


def water_mask(db: np.ndarray, land_db_max: float = -12.0) -> np.ndarray:
    """Water is the darker class in C-band coastal scenes.

    `land_db_max` is an oil-irrelevant prior: brighter than this is treated as land
    or ship even if Otsu would pull it in.
    """
    finite = np.isfinite(db)
    if finite.sum() < 16:
        return np.zeros(db.shape, dtype=bool)
    try:
        t = float(threshold_otsu(db[finite]))
    except ValueError:
        t = land_db_max
    water = finite & (db <= t) & (db <= land_db_max)
    return water


def dark_spot_mask(
    db: np.ndarray,
    water: np.ndarray,
    oil_db_max: float = -22.0,
    min_pixels: int = 20,
) -> np.ndarray:
    """Otsu on water-only log sigma0; keep the darker class below `oil_db_max`."""
    sample = db[water & np.isfinite(db)]
    if sample.size < 16:
        return np.zeros(db.shape, dtype=bool)
    try:
        t = float(threshold_otsu(sample))
    except ValueError:
        t = oil_db_max
    oil = water & np.isfinite(db) & (db <= t) & (db <= oil_db_max)
    return _clean_components(oil, min_pixels)


def _clean_components(oil: np.ndarray, min_pixels: int) -> np.ndarray:
    oil = opening(oil, disk(1))
    try:
        return remove_small_objects(oil, max_size=max(min_pixels - 1, 0))
    except TypeError:
        return remove_small_objects(oil, min_size=min_pixels)


def _pin_rowcol(transform, lon: float, lat: float, src_crs: str) -> tuple[int, int]:
    to_src = Transformer.from_crs(WGS84, src_crs, always_xy=True)
    x, y = to_src.transform(lon, lat)
    r, c = rowcol(transform, x, y)
    return int(r), int(c)


def jiv_window_mask(
    shape: tuple[int, int],
    transform,
    lon: float,
    lat: float,
    src_crs: str,
    radius_m: float = SEARCH_RADIUS_M,
) -> np.ndarray:
    """Pixels within `radius_m` of the JIV. Assumes square, north-up pixels."""
    r, c = _pin_rowcol(transform, lon, lat, src_crs)
    rows, cols = shape
    res = float(abs(transform.a))
    radius_px = radius_m / max(res, 1e-6)
    yy, xx = np.ogrid[:rows, :cols]
    return ((yy - r) ** 2 + (xx - c) ** 2) <= radius_px**2


def pin_diagnostics(
    db: np.ndarray,
    water: np.ndarray,
    transform,
    lon: float,
    lat: float,
    src_crs: str,
) -> dict:
    """Backscatter and water at the leak pin. The pin is often land, not the slick."""
    r, c = _pin_rowcol(transform, lon, lat, src_crs)
    rows, cols = db.shape
    inside = 0 <= r < rows and 0 <= c < cols
    pin_db = float(db[r, c]) if inside and np.isfinite(db[r, c]) else None
    pin_on_water = bool(inside and water[r, c])
    nearest_m = None
    if inside and water.any():
        ys, xs = np.where(water)
        i = int(np.argmin((ys - r) ** 2 + (xs - c) ** 2))
        to_utm = Transformer.from_crs(src_crs, AREA_CRS, always_xy=True)
        x0, y0 = xy(transform, r, c, offset="center")
        x1, y1 = xy(transform, int(ys[i]), int(xs[i]), offset="center")
        ux0, uy0 = to_utm.transform(x0, y0)
        ux1, uy1 = to_utm.transform(x1, y1)
        nearest_m = float(np.hypot(ux1 - ux0, uy1 - uy0))
    return {
        "pin_row": r,
        "pin_col": c,
        "pin_inside_raster": inside,
        "pin_db": pin_db,
        "pin_on_water": pin_on_water,
        "nearest_water_m": nearest_m,
    }


def local_dark_spot_mask(
    db: np.ndarray,
    water: np.ndarray,
    transform,
    lon: float,
    lat: float,
    src_crs: str,
    search_radius_m: float = SEARCH_RADIUS_M,
    oil_margin_db: float = OIL_MARGIN_DB,
    oil_db_max: float = OIL_DB_MAX,
    min_pixels: int = 20,
) -> tuple[np.ndarray, dict]:
    """Dark water inside a JIV search radius.

    v1 used a scene-wide −22 dB marine prior. Swamp creeks here sit near −16 to
    −18 dB, so that floor emptied the mask. v2 keeps water pixels that are
    darker than the local-water median by `oil_margin_db`, and not brighter
    than `oil_db_max` (−18 dB).
    """
    window = jiv_window_mask(db.shape, transform, lon, lat, src_crs, search_radius_m)
    local_water = water & window & np.isfinite(db)
    zeros = np.zeros(db.shape, dtype=bool)
    report = {
        "detector_version": DETECTOR_VERSION,
        "search_radius_m": search_radius_m,
        "oil_margin_db": oil_margin_db,
        "oil_db_max": oil_db_max,
        "local_water_px": int(local_water.sum()),
        "threshold_db": None,
        "local_water_median_db": None,
        "local_otsu_db": None,
    }
    if local_water.sum() < 16:
        return zeros, report
    sample = db[local_water]
    try:
        t_otsu = float(threshold_otsu(sample))
    except ValueError:
        t_otsu = oil_db_max
    t_margin = float(np.median(sample)) - oil_margin_db
    t = min(t_otsu, t_margin, oil_db_max)
    oil = local_water & (db <= t)
    oil = _clean_components(oil, min_pixels)
    report.update(
        {
            "threshold_db": t,
            "local_water_median_db": float(np.median(sample)),
            "local_otsu_db": t_otsu,
        }
    )
    return oil, report


def change_dark_spot_mask(
    post_db: np.ndarray,
    pre_db: np.ndarray,
    water: np.ndarray,
    transform,
    lon: float,
    lat: float,
    src_crs: str,
    search_radius_m: float = SEARCH_RADIUS_M,
    change_margin_db: float = CHANGE_MARGIN_DB,
    oil_db_max: float = OIL_DB_MAX,
    min_pixels: int = 20,
) -> tuple[np.ndarray, dict]:
    """Water that darkened after the incident, inside the JIV search radius.

    `delta = post − pre`. Oil is expected to be more negative. Stable dark
    creeks that v2 would keep are dropped if they did not darken.
    """
    window = jiv_window_mask(post_db.shape, transform, lon, lat, src_crs, search_radius_m)
    valid = water & window & np.isfinite(post_db) & np.isfinite(pre_db)
    delta = post_db - pre_db
    zeros = np.zeros(post_db.shape, dtype=bool)
    sample = delta[valid]
    report = {
        "detector_version": CHANGE_DETECTOR_VERSION,
        "search_radius_m": search_radius_m,
        "change_margin_db": change_margin_db,
        "oil_db_max": oil_db_max,
        "local_water_px": int(valid.sum()),
        "median_delta_db": float(np.median(sample)) if sample.size else None,
        "darkened_px_raw": 0,
    }
    if valid.sum() < 16:
        return zeros, report
    oil = valid & (delta <= -change_margin_db) & (post_db <= oil_db_max)
    report["darkened_px_raw"] = int(oil.sum())
    oil = _clean_components(oil, min_pixels)
    return oil, report
