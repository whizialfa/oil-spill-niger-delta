from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
MAPS = ROOT / "maps"
QGIS = ROOT / "qgis"
NOTES = ROOT / "notes"


def ensure_dirs() -> None:
    for path in (DATA_RAW, DATA_PROCESSED, MAPS, QGIS, NOTES):
        path.mkdir(parents=True, exist_ok=True)
