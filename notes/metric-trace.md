# Metric trace

Headline, per incident:

1. **slick area (km²)** of look-alike-filtered dark-spot polygons
2. **NOSDRA-point-in-footprint** (plus a 500 m hit tolerance)

## Chain

NOSDRA-named incident (date + xy) → Sentinel-1 RTC/GRD scene → linear σ⁰ → Lee speckle filter → log σ⁰ (dB) → water mask → Otsu dark-spot mask with max-σ⁰ oil prior → connected components → GLCM contrast filter → polygons → area in [EPSG:32631](https://epsg.io/32631) (UTM 31N) → `spill_metrics.csv`

Quoted number: `data/processed/spill_metrics.csv`, column `slick_area_km2`. If `scene_source` is `synthetic_rtc_fixture`, that row is a **pipeline check**, not a spill area.

## What is not yet a NOSDRA pin

`src/spill/sites.py` stores community or field centroids. They are flagged `coord_source=*_provisional`. Replace them with JIV coordinates before any paper table. The 500 m hit radius exists because of that, not because slicks are 500 m wide.

## Calibration, without SNAP

The paper owns detection, discrimination, and validation. Geocoding and radiometric terrain correction are **not** reimplemented here.

- Preferred input: ASF HyP3 RTC GeoTIFF at `data/raw/{site_id}_rtc.tif` (σ⁰ or γ⁰, linear or dB).
- If that file is missing, the pipeline writes a synthetic RTC fixture so the code path can be tested.
- Fallback not implemented in v1: GRD SAFE + annotation LUT σ⁰ + GCP georeference. That would still not be full RTC; say so if it is added.

## Detection (v1, named so it can be swapped)

- Water: Otsu on the scene, then drop anything brighter than −12 dB.
- Dark spots: Otsu on water-only dB, keep the darker class at or below −22 dB, open, drop components under 20 pixels.
- Look-alikes: drop connected components whose eroded-core GLCM contrast is below 0.15. Contrast is computed on a fixed dB scale (−32 to −16) after a 2-pixel erosion so Lee speckle filtering cannot leak water texture into a uniform patch.
- Area CRS: EPSG:32631 for all three sites (longitudes 5.4–6.4 E).

## Sites (press dates, not JIV timestamps)

| id | name | date | date precision |
|---|---|---|---|
| biseni_tein | Biseni/Tein | 2025-12-15 | month (Dec 2025 reporting) |
| agge_bonga | Agge/Bonga | 2026-01-24 | day (community report) |
| odidi_kantu | Odidi-Kantu | 2026-02-19 | day (Trans-Forcados report) |

## Do not

- Call fixture km² a measured slick.
- Mix a community centroid with a JIV coordinate in the same column without `coord_source`.
- Run SNAP `gpt`.
- Dump this analysis into the 15-minute-cities Nigeria repo or into `Paper replicas`. This project sits in `Documents/Portfolio/Projects/`.
