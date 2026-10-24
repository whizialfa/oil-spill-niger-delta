# Metric trace

Headline, per incident:

1. **hit** (JIV pin inside a kept dark-spot, or within 500 m)
2. Supporting: `pin_on_water`, `pin_db`, `nearest_water_m`, NOSDRA barrels and JIV area

`methods_darkened_km2` (also written as `slick_area_km2` for the old column name) is a methods area. `quote_km2_as_slick` is False. Do not quote it as a slick. Quoted table: `data/processed/headline.csv`. Score on this run: **0 / 3**.

## Chain

NOSDRA-named incident (date + xy) → post Sentinel-1 RTC → (optional pre RTC, warped to post grid) → Lee → dB → water mask → **v3 pre/post** if a pre scene exists (water in 3 km that darkened ≥2 dB and is ≤ −18 dB), else **v2 local dark-spot** → GLCM → polygons → area in [EPSG:32631](https://epsg.io/32631) (UTM 31N) → `spill_metrics.csv`

Quoted number: `data/processed/headline.csv`, column `hit`. If `scene_source` is `synthetic_rtc_fixture`, that row is a **pipeline check**, not a spill.

## NOSDRA pins (public Oil Spill Monitor)

Pulled from `https://oilspillmonitor.ng/api/spill-data.php?dataset=nosdra&format=json` (21,166 rows, no login). Quoted matches: `data/processed/nosdra_site_matches.csv`.

- Odidi-Kantu: NOSDRA id `359834`, HEOSL/2025/328, JIV 20 Feb 2026, 5.4733333 N, 5.4444444 E.
- Odimodi (Trans-Ramos): NOSDRA id `466367`, 028974, JIV 23 Apr 2026, 5.3000 N, 5.3684 E.
- Opukushi: NOSDRA id `466233`, 2025_000312, JIV 29 Dec 2025, 4.9243 N, 5.7599 E.

The 500 m hit radius is for residual geolocation error on a JIV pin, not a community centroid.

## Calibration, without SNAP

The paper owns detection, discrimination, and validation. Geocoding and radiometric terrain correction are **not** reimplemented here.

- Preferred input: ASF HyP3 RTC GeoTIFF at `data/raw/{site_id}_rtc.tif` (σ⁰ or γ⁰, linear or dB).
- If that file is missing, the pipeline writes a synthetic RTC fixture so the code path can be tested.
- Fallback not implemented in v1: GRD SAFE + annotation LUT σ⁰ + GCP georeference. That would still not be full RTC; say so if it is added.

## Detection (v2_local_water)

v1 used a scene-wide −22 dB marine prior. On these swamp RTC windows that floor is empty or nearly empty, and the JIV pins sit on bright land 40–270 m from water.

- Water: Otsu on the scene, then drop anything brighter than −12 dB.
- Search: only water inside 3 km of the JIV (the leak pin, not a slick centroid).
- Dark spots: keep local water darker than `min(local Otsu, local-water median − 2 dB, −18 dB)`, open, drop components under 20 pixels.
- Look-alikes: drop connected components whose eroded-core GLCM contrast is below 0.15. Contrast is computed on a fixed dB scale (−32 to −16) after a 2-pixel erosion so Lee speckle filtering cannot leak water texture into a uniform patch.
- Area CRS: EPSG:32631 for all three sites (longitudes 5.4–6.4 E).
- Extra quoted columns: `pin_db`, `pin_on_water`, `nearest_water_m`, `threshold_db`, `detector_version`.

## Detection (v3_prepost)

Used when `data/raw/{site_id}_rtc_pre.tif` is present. Same 3 km JIV window and −18 dB ceiling. Keep water that darkened by at least 2 dB (`post − pre`). Stable dark creeks that v2 flags are dropped. Pre is the last same-look Planetary Computer RTC before the incident date. Headline is `hit`. v3 area is `methods_darkened_km2`. `v2_slick_area_km2` stays as a methods column.

## Sites (west trio, all NOSDRA JIV)

| id | name | date | NOSDRA id |
|---|---|---|---|
| odidi_kantu | Odidi-Kantu | 2026-02-20 | 359834 |
| odimodi_ramos | Odimodi (Trans-Ramos) | 2026-04-21 | 466367 |
| opukushi | Opukushi | 2025-12-26 | 466233 |

Agge/Bonga 24 Jan 2026 is not a headline site (no public JIV). Biseni/Tein is a methods note only.

## First west-trio RTC run (detector v1, do not quote as slick area)

All three `scene_source=planetary_computer_s1_rtc`. Hit is False on every JIV.

| site | scene | slick_area_km2 | n_slicks | nearest slick (m) |
|---|---|---|---|---|
| odidi_kantu | S1A 2026-02-23T17:53Z | 0.0178 | 4 | 7711 |
| odimodi_ramos | S1A 2026-04-24T17:53Z | 0 | 0 | — |
| opukushi | S1A 2026-01-01T05:22Z | 0 | 0 | — |

These numbers are an untuned detector on swamp RTC, not a reported spill area.

Pin diagnosis (Lee dB at the JIV): Odidi −2.3 dB (bright land, water 41 m); Odimodi −7.4 dB (swamp, water 266 m); Opukushi −7.7 dB (swamp, water 184 m). Scene-wide fraction ≤ −22 dB is ~0.00–0.02%.

## Detector v2 RTC run (do not quote as slick area)

`detector_version=v2_local_water`. Dark water now appears inside each 3 km window. Every 500 m hit is still False. Pre-GLCM nearest oil is already 1.5–2.5 km from the pin, so the miss is not the texture filter.

| site | pin_db | nearest water (m) | slick_area_km2 | n_slicks | nearest slick (m) | hit |
|---|---|---|---|---|---|---|
| odidi_kantu | −2.34 | 41 | 0.0211 | 4 | 1762 | False |
| odimodi_ramos | −7.38 | 266 | 0.0028 | 1 | 1711 | False |
| opukushi | −7.69 | 184 | 0.0039 | 1 | 2492 | False |

NOSDRA listed JIV spill areas of 0.070 km² (Odimodi) and 0.029 km² (Opukushi). The leak pins are on land or swamp, not on a C-band dark slick.

## Detector v3 RTC run (do not quote as slick area)

Same-look 12-day pairs from Planetary Computer. Pre warped onto the post grid.

| site | pre | post | pin ΔdB | v3 km² | n | nearest (m) | hit | v2 km² |
|---|---|---|---|---|---|---|---|---|
| odidi_kantu | 2026-02-11T17:53Z | 2026-02-23T17:53Z | +4.42 | 0.2602 | 22 | 570 | False | 0.0211 |
| odimodi_ramos | 2026-04-12T17:53Z | 2026-04-24T17:53Z | +0.14 | 0.0281 | 6 | 1248 | False | 0.0028 |
| opukushi | 2025-12-20T05:22Z | 2026-01-01T05:22Z | −1.44 | 0.0000 | 0 | — | False | 0.0039 |

Opukushi’s v2 patch at 2.5 km was already dark before the incident and drops under v3. Odidi local water median darkened 1.87 dB (wind and oil are not separated). Nearest v3 darkening at Odidi is 570 m, still outside the 500 m hit. Do not loosen the hit.

## Do not

- Call fixture km² a measured slick.
- Mix a community centroid with a JIV coordinate in the same column without `coord_source`.
- Run SNAP `gpt`.
- Dump this analysis into the 15-minute-cities Nigeria repo or into `Paper replicas`. This project sits in `Documents/Portfolio/Projects/`.
