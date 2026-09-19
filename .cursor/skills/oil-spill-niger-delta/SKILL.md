---
name: oil-spill-niger-delta
description: >-
  Standing cuts for the Niger Delta Sentinel-1 oil-spill footprint paper
  (Biseni/Tein, Agge/Bonga, Odidi-Kantu). Use when computing slick area,
  NOSDRA hits, RTC ingest, QGIS export, or quoting km².
---

# Oil-spill Niger Delta

Original analysis. Not a replica of Bruno. Not part of `15-min-cities-nigeria`. Home folder: `Documents/Portfolio/Projects/oil-spill-niger-delta`, not `Paper replicas`.

## Claim

Per incident: look-alike-filtered dark-spot **slick area (km²)** plus **point-in-footprint** against a named NOSDRA incident. Quote `data/processed/spill_metrics.csv`. If `scene_source=synthetic_rtc_fixture`, do not quote that km² as a spill.

## Locked

- Sites: Biseni/Tein, Agge/Bonga, Odidi-Kantu
- Sensor: Sentinel-1 GRD / HyP3 RTC (amplitude). No SLC.
- No SNAP `gpt`. Native Python only.
- Fresh QGIS package from pipeline GeoJSON. Legacy `bonga_spill_2026.qgz` is extract-only if found.
- Area CRS: EPSG:32631
- GLCM min contrast: 0.15 on a fixed −32 to −16 dB scale, eroded core
- Interpreter: `python3.12` (Anaconda 3.12 on Wisdom's Mac: `/opt/anaconda3/bin/python3.12`)

## Coordinates

`src/spill/sites.py` is provisional community/field centroids, not JIV pins. Keep `coord_source`. 500 m hit tolerance is for that uncertainty.

## Do not

- Dump code into the 15-minute cities repo or into `Paper replicas`
- Update the legacy `.qgz` in place
- Call a fixture area a measured footprint
- Hatch look-alikes into the slick without the GLCM drop count in the table
- Commit RTC GeoTIFFs or GeoPackages
