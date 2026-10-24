# QGIS package

Open `oil_spill_niger_delta.qgz`.

Vectors (`../data/processed/*.geojson`): JIV points, slick footprints, 2.5 km site rings.
Rasters (`../data/processed/*_{sigma0_db,sigma0_db_pre,delta_db}.tif`): Lee VV in dB.

- Post / pre: gray stretch −28 to −4 dB (water dark, land bright). Post is on; pre is off.
- Change: blue = darkened after the incident, red = brighter, white = 0. Off by default.

This is a **new** project built from the Python pipeline. Do not treat it as an edit of `bonga_spill_2026.qgz`.
