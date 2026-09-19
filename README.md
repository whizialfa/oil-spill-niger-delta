# Oil-spill footprints — Niger Delta

Original Sentinel-1 analysis for three NOSDRA-named incidents in Bayelsa and Delta States. **This is not a paper replica.** Do not quote fixture kilometres as a spill area.

## Sites

| Site | State | Incident date | Date precision |
|---|---|---|---|
| Biseni/Tein | Bayelsa | 2025-12-15 | month (December 2025 reporting) |
| Agge/Bonga | Bayelsa | 2026-01-24 | day |
| Odidi-Kantu | Delta | 2026-02-19 | day |

Coordinates in `src/spill/sites.py` are **provisional** community or field centroids, not NOSDRA JIV pins.

## Headline metric

`slick_area_km2` in [`data/processed/spill_metrics.csv`](data/processed/spill_metrics.csv): area of GLCM-filtered dark-spot polygons in UTM 31N, plus `nosdra_point_in_footprint` / `hit`. Trace: [`notes/metric-trace.md`](notes/metric-trace.md).

## Run

```bash
export PYTHONPATH="$PWD/src"
python3.12 -m spill.pipeline
python3.12 -m pytest tests -q
```

On Wisdom's Mac the interpreter is `/opt/anaconda3/bin/python3.12`. This pipeline does not call SNAP `gpt`.

Place a real ASF HyP3 RTC GeoTIFF at `data/raw/{site_id}_rtc.tif` to replace the synthetic fixture. Site ids: `biseni_tein`, `agge_bonga`, `odidi_kantu`.

## QGIS

After a pipeline run, open [`qgis/oil_spill_niger_delta.qgz`](qgis/oil_spill_niger_delta.qgz). It is a **new** package pointing at `data/processed/*.geojson`. The legacy `bonga_spill_2026.qgz` is not edited; search log: [`notes/legacy-search.md`](notes/legacy-search.md).

## Layout

```
src/spill/     acquire, Lee, Otsu, GLCM, polygonize, validate, QGIS export
data/raw/      RTC GeoTIFFs (gitignored)
data/processed/ quoted csv + small GeoJSON
qgis/          fresh .qgz
notes/         metric trace
```
