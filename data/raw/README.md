# Raw inputs

Put ASF HyP3 RTC GeoTIFFs here:

- `biseni_tein_rtc.tif`
- `agge_bonga_rtc.tif`
- `odidi_kantu_rtc.tif`

Not committed. If a file is missing, `spill.pipeline` writes a synthetic fixture with sidecar `{site_id}_rtc.json` (`scene_source=synthetic_rtc_fixture`).

If `bonga_spill_2026.qgz` is found, copy it to `legacy/` in this folder and extract layers. Do not overwrite it.
