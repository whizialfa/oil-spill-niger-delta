---
name: oil-spill-niger-delta
description: >-
  Standing cuts for the Niger Delta Sentinel-1 oil-spill paper
  (Odidi-Kantu, Odimodi Trans-Ramos, Opukushi). Use when quoting hits,
  NOSDRA pins, RTC ingest, QGIS export, or methods km².
---

# Oil-spill Niger Delta

Original analysis. Not a replica of Bruno. Not part of `15-min-cities-nigeria`. Home folder: `Documents/Portfolio/Projects/oil-spill-niger-delta`, not `Paper replicas`.

## Claim

Headline: **hit** at the NOSDRA JIV pin (500 m). This run is **0 / 3**. Quote `data/processed/headline.csv`. Do not quote `methods_darkened_km2` or `slick_area_km2` as a slick (`quote_km2_as_slick=False`). Mast: "The leak is not the slick."

## Locked

- Sites: Odidi-Kantu, Odimodi (Trans-Ramos), Opukushi. West cluster only.
- Not headline: Agge/Bonga 24 Jan 2026 (no public JIV), Biseni/Tein (small flowline, other system).
- Sensor: Sentinel-1 RTC (Planetary Computer or HyP3). Amplitude. No SLC.
- No SNAP `gpt`. Native Python only.
- Fresh QGIS package from pipeline GeoJSON.
- Area CRS: EPSG:32631
- Detector: `v3_prepost` when `{site}_rtc_pre.tif` exists (water that darkened ≥2 dB). Else `v2_local_water`. Do not quote v1 −22 dB scene-wide km².
- Interpreter: `/opt/anaconda3/bin/python3.12`

## Coordinates

Headline sites are `coord_source=nosdra_jiv`. 500 m hit is residual geolocation, not a community centroid.

## Do not

- Dump code into the 15-minute cities repo or into `Paper replicas`
- Push until Wisdom says the project is done
- Quote methods km² (0.26 / 0.028 / 0.00) as a slick area
- Quote a fixture km² or an Agge centroid as a JIV
- Loosen the 500 m hit because Odidi landed at 570 m
- Call Bonny a fourth headline site
- Commit RTC GeoTIFFs or GeoPackages
