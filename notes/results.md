---
title: "The leak is not the slick"
subtitle: "Sentinel-1 misses three NOSDRA-confirmed swamp spills in the western Niger Delta"
author: Wisdom Akpabio
date: September 2026
keywords: Sentinel-1; oil spill; NOSDRA; Niger Delta; swamp; JIV; dark-spot
abstract: |
  Three NOSDRA-confirmed incidents in the western Niger Delta (Odidi-Kantu, Odimodi on the Trans-Ramos, and Opukushi) are tested against windowed Sentinel-1 RTC. The headline is a 500 m hit on the Joint Investigation Visit pin, not a slick area. The score is **0 hits out of 3**. Each pin sits on land or swamp, 41 to 266 metres from water. A marine −22 dB oil prior is empty on these creeks. Same-look pre and post pairs still miss. Odidi is the near miss at 570 m. Detector square kilometres are methods output and are not a measured slick.
---

<div class="glossary">

## Glossary

<dl>

<dt>JIV pin</dt>
<dd>The Joint Investigation Visit coordinate published on the NOSDRA Oil Spill Monitor. It marks the leak that was visited, not the centre of a floating film.</dd>

<dt>Hit</dt>
<dd>The JIV pin lies inside a kept dark-spot polygon, or within 500 m of one. Residual geolocation, not a community centroid. Headline metric.</dd>

<dt>methods_darkened_km2</dt>
<dd>Area of GLCM-filtered water that the detector called dark or darkened, in UTM 31N. Methods column. Do not quote it as slick area. Column <code>quote_km2_as_slick</code> is False on every row here.</dd>

<dt>v3_prepost</dt>
<dd>Water inside 3 km of the JIV that darkened by at least 2 dB between a same-look pre scene and the first post scene, and is at or below −18 dB.</dd>

<dt>RTC</dt>
<dd>Radiometrically terrain-corrected Sentinel-1 backscatter from Planetary Computer. Amplitude, VV. Not SLC. Not SNAP <code>gpt</code>.</dd>

</dl>

</div>

# 1. The finding

The spills are real. The dark spots at the pins are not.

NOSDRA lists all three incidents as confirmed. The volumes are 700, 2,466 and 1,322 barrels. Two JIV forms also give a spill area: 0.07 km² at Odimodi and 0.03 km² at Opukushi. Habitat is swamp (and inland water at Odidi).

The first same-look Sentinel-1 pair after each date does not put a dark-spot on the pin. Quoted table: `data/processed/headline.csv`. Full detector row: `data/processed/spill_metrics.csv`.

# 2. Sites

The west cluster only. Agge/Bonga 24 January 2026 has no public JIV and is not a headline site. Biseni/Tein is another system.

| Site | NOSDRA id | Date | Barrels | JIV area (km²) | Cause |
|---|---|---|---|---|---|
| Odidi-Kantu | 359834 | 2026-02-20 | 700 | none | corrosion |
| Odimodi (Trans-Ramos) | 466367 | 2026-04-21 | 2,466 | 0.070 | equipment |
| Opukushi | 466233 | 2025-12-26 | 1,322 | 0.029 | equipment |

Pins are `coord_source=nosdra_jiv` in `src/spill/sites.py`. Matches: `data/processed/nosdra_site_matches.csv`.

# 3. Method

Post scene: first Planetary Computer `sentinel-1-rtc` VV window after the incident, 12 km on a side, centred on the pin. Pre scene: last same-hour pass before the incident (12-day pair). Lee speckle on linear backscatter, then dB.

Water is the darker Otsu class, at or below −12 dB. Darkening is then restricted to water inside 3 km of the JIV. v3 keeps pixels that fell by at least 2 dB and sit at or below −18 dB. A GLCM contrast filter (0.15, fixed dB scale −32 to −16) drops low-texture patches. Area is EPSG:32631.

v1 used a scene-wide −22 dB marine prior. That floor is empty here. v2 used local dark water without a pre scene. v3 is the headline detector when a pre GeoTIFF exists.

A hit is 500 m. The rule is not relaxed when Odidi lands at 570 m.

# 4. Results

**0 / 3 hits.**

| Site | Pin on water | Pin (dB) | Water (m) | Nearest darkening (m) | Hit | methods km² |
|---|---|---|---|---|---|---|
| Odidi-Kantu | no | −2.3 | 41 | 570 | no | 0.260 |
| Odimodi | no | −7.4 | 266 | 1,248 | no | 0.028 |
| Opukushi | no | −7.7 | 184 | none | no | 0.000 |

Odidi’s pin is a bright land return. It got brighter after the incident (+4.4 dB), which is the opposite of an oil film. Local water, taken as a whole, darkened by 1.9 dB. That can be wind. It is not a reason to call 0.26 km² a slick.

Odimodi’s leftover patches sit more than a kilometre from the leak. NOSDRA’s own JIV area is 0.07 km².

Opukushi keeps nothing under v3. The v2 patch at 2.5 km was already dark on 20 December 2025, six days before the incident.

Figure: [`charts/jiv_miss.png`](../charts/jiv_miss.png). Six-kilometre pre/post plates: `maps/{site}_jiv_compare.png`. QGIS: `qgis/oil_spill_niger_delta.qgz`.

# 5. What the miss means

A C-band dark-spot recipe is a model of damping on open water. These leaks sit in swamp. The JIV pin is the pipe or the well, not a film centroid. Oil in vegetation and mud does not have to produce a −22 dB patch on the first overpass.

The honest sentence is not that there was no spill. It is that Sentinel-1 RTC, treated this way, does not confirm these three NOSDRA visits. That is the result. It is not a licence to loosen 500 m or to quote methods km².

# 6. What this paper is not

This is original analysis. It is not a replica of Bruno et al. It is not an offshore Bonga footprint map. It does not use SNAP `gpt`. Fixture kilometres from a synthetic RTC are a code check only.
