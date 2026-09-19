"""Named look-alike filter: drop low-texture dark patches (wind-shadow style)."""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from skimage.feature import graycomatrix, graycoprops
from skimage.morphology import disk, erosion


def _glcm_contrast(window: np.ndarray, levels: int = 32, vmin: float = -32.0, vmax: float = -16.0) -> float:
    finite = np.isfinite(window)
    if finite.sum() < 16:
        return 0.0
    scaled = np.clip((window - vmin) / (vmax - vmin), 0, 1)
    scaled = np.where(finite, scaled, 0)
    bins = np.rint(scaled * (levels - 1)).astype(np.uint8)
    glcm = graycomatrix(
        bins,
        distances=[1],
        angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
        levels=levels,
        symmetric=True,
        normed=True,
    )
    contrast = graycoprops(glcm, "contrast").mean()
    return float(contrast)


def filter_lookalikes(
    db: np.ndarray,
    oil_mask: np.ndarray,
    min_contrast: float = 0.15,
    pad: int = 4,
) -> tuple[np.ndarray, dict]:
    """Keep connected dark spots whose core GLCM contrast exceeds `min_contrast`.

    Low-contrast dark water (wind shadow, some biogenic films) is dropped. The
    threshold is a v1 named parameter, not a fitted classifier.
    """
    labeled, n = ndi.label(oil_mask)
    kept = np.zeros_like(oil_mask)
    dropped = 0
    kept_n = 0
    rows, cols = db.shape
    for lab in range(1, n + 1):
        ys, xs = np.where(labeled == lab)
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, rows)
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, cols)
        window = db[y0:y1, x0:x1].copy()
        inside = labeled[y0:y1, x0:x1] == lab
        core = erosion(inside, disk(2))
        if core.sum() < 16:
            core = inside
        fill = float(np.nanmean(window[core]))
        # Score the eroded core so a 5-pixel Lee window cannot leak water
        # texture into a uniform look-alike. Surroundings set to the core mean.
        window = np.where(core, window, fill)
        contrast = _glcm_contrast(window)
        if contrast >= min_contrast:
            kept[labeled == lab] = True
            kept_n += 1
        else:
            dropped += 1
    report = {
        "components_in": int(n),
        "components_kept": int(kept_n),
        "components_dropped_low_texture": int(dropped),
        "min_contrast": min_contrast,
    }
    return kept, report
