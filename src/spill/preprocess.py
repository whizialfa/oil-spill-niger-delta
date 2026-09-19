"""Lee speckle filter, linear/dB conversion, and RTC raster I/O."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine
from scipy.ndimage import uniform_filter


def to_db(linear: np.ndarray, floor: float = 1e-10) -> np.ndarray:
    return 10.0 * np.log10(np.maximum(linear, floor))


def from_db(db: np.ndarray) -> np.ndarray:
    return np.power(10.0, db / 10.0)


def lee_filter(image: np.ndarray, size: int = 5) -> np.ndarray:
    """Standard Lee speckle filter on linear intensity."""
    img = np.asarray(image, dtype=np.float64)
    finite = np.isfinite(img)
    fill = float(np.nanmean(img[finite])) if finite.any() else 0.0
    work = np.where(finite, img, fill)
    mean = uniform_filter(work, size=size, mode="nearest")
    mean_sq = uniform_filter(work * work, size=size, mode="nearest")
    var = np.maximum(mean_sq - mean * mean, 0.0)
    overall = float(np.var(work)) + 1e-12
    weight = var / (var + overall)
    out = mean + weight * (work - mean)
    return np.where(finite, out, np.nan)


def read_backscatter(path: Path) -> tuple[np.ndarray, rasterio.Affine, str, dict]:
    """Read a single-band RTC/GRD GeoTIFF as linear sigma0.

    If values look like dB (median < 2 and some negatives), convert to linear.
    """
    path = Path(path)
    with rasterio.open(path) as src:
        band = src.read(1).astype(np.float64)
        transform = src.transform
        crs = src.crs.to_string() if src.crs else "EPSG:4326"
        nodata = src.nodata
        profile = src.profile
    if nodata is not None:
        band = np.where(band == nodata, np.nan, band)
    finite = band[np.isfinite(band)]
    if finite.size and float(np.nanmedian(finite)) < 2.0 and float(np.nanmin(finite)) < 0:
        linear = from_db(band)
    else:
        linear = band
    return linear, transform, crs, profile


def write_geotiff(
    path: Path,
    data: np.ndarray,
    transform: Affine,
    crs: str,
    nodata: float = -9999.0,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width = data.shape
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "nodata": nodata,
        "compress": "lzw",
    }
    out = np.where(np.isfinite(data), data, nodata).astype(np.float32)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(out, 1)
