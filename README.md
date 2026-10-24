# The leak is not the slick

Sentinel-1 misses three NOSDRA-confirmed swamp spills in the western Niger Delta. **This is not a paper replica.** It lives under `Documents/Portfolio/Projects/`, not `Paper replicas`. Headline is **0 / 3 hits**. Do not quote detector kilometres as a slick area.

## Sites

| Site | State | Incident date | NOSDRA id |
|---|---|---|---|
| Odidi-Kantu | Delta | 2026-02-20 | 359834 |
| Odimodi (Trans-Ramos) | Delta | 2026-04-21 | 466367 |
| Opukushi | Bayelsa | 2025-12-26 | 466233 |

Headline coordinates in `src/spill/sites.py` are NOSDRA JIV pins. Agge/Bonga and Biseni/Tein are not headline sites.

## Headline metric

`hit` in [`data/processed/headline.csv`](data/processed/headline.csv): JIV pin inside a kept dark-spot, or within 500 m. This run is 0 / 3. `methods_darkened_km2` is methods only. Brief: [`notes/brief.md`](notes/brief.md). Results: [`notes/results.md`](notes/results.md). Trace: [`notes/metric-trace.md`](notes/metric-trace.md).

## Run

```bash
export PYTHONPATH="$PWD/src"
python3.12 -m spill.pipeline
python3.12 -m pytest tests -q
```

On Wisdom's Mac the interpreter is `/opt/anaconda3/bin/python3.12`. This pipeline does not call SNAP `gpt`.

Windowed Planetary Computer RTC is written to `data/raw/{site_id}_rtc.tif`. Site ids: `odidi_kantu`, `odimodi_ramos`, `opukushi`.

## QGIS

After a pipeline run, open [`qgis/oil_spill_niger_delta.qgz`](qgis/oil_spill_niger_delta.qgz). It loads JIV points, footprints, and Lee-filtered pre/post/change rasters from `data/processed/`. Post VV is on (gray −28 to −4 dB). Pre and change start off. The legacy `bonga_spill_2026.qgz` is not edited; search log: [`notes/legacy-search.md`](notes/legacy-search.md).

## Layout

```
src/spill/     acquire, Lee, Otsu, GLCM, polygonize, validate, QGIS export
data/raw/      RTC GeoTIFFs (gitignored)
data/processed/ quoted csv + small GeoJSON
qgis/          fresh .qgz
notes/         metric trace, results, brief
charts/        JIV miss figure
```
