# Legacy QGIS search

Target file: `bonga_spill_2026.qgz` (handoff: extract site boundaries and verified incident points only; do not update in place).

Searched 19 Sep 2026 on this machine:

- `/Users/atimakaduh/Downloads` (handoff markdown only; no `.qgz`)
- `/Users/atimakaduh/Documents` (no `.qgz`)
- `/workspace`, `/home/ubuntu`, `/opt` (no project `.qgz`; plan file only)

**Result:** file not found. Not a blocker. Pipeline sites come from `src/spill/sites.py` until the package turns up.

If the file is located later:

1. Copy it into `data/raw/legacy/` (gitignored).
2. Unzip the `.qgz` / `.qgs` and list layer datasources.
3. Export site polygons and incident points to `data/raw/legacy/*.geojson`.
4. Feed those as inputs. Leave the legacy project unmodified.
5. Keep shipping `qgis/oil_spill_niger_delta.qgz` from Python outputs.
