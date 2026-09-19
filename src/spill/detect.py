"""Water mask and Otsu dark-spot detection on log sigma0."""

from __future__ import annotations

import numpy as np
from skimage.filters import threshold_otsu
from skimage.morphology import disk, opening, remove_small_objects


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
    oil = opening(oil, disk(1))
    oil = remove_small_objects(oil, max_size=max(min_pixels - 1, 0))
    return oil
