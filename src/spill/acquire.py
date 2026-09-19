"""Resolve an RTC scene path: local GeoTIFF, else synthetic fixture. No SNAP."""

from __future__ import annotations

import json
from pathlib import Path

from spill.fixtures import write_synthetic_rtc
from spill.paths import DATA_RAW, ensure_dirs


def rtc_path(site_id: str) -> Path:
    return DATA_RAW / f"{site_id}_rtc.tif"


def _sidecar_source(path: Path) -> str | None:
    side = path.with_suffix(".json")
    if not side.exists():
        return None
    try:
        payload = json.loads(side.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload.get("scene_source")


def resolve_scene(site: dict, allow_synthetic: bool = True) -> tuple[Path, str]:
    """Return (geotiff, scene_source).

    Drop a real ASF HyP3 RTC (linear or dB sigma0/gamma0, map-projected) at
    `data/raw/{site_id}_rtc.tif` to replace the fixture. This module does not
    call SNAP gpt.
    """
    ensure_dirs()
    path = rtc_path(site["id"])
    if path.exists():
        return path, _sidecar_source(path) or "local_rtc"
    if not allow_synthetic:
        raise FileNotFoundError(
            f"No RTC at {path}. Place an ASF HyP3 RTC GeoTIFF there, or rerun with the fixture."
        )
    write_synthetic_rtc(site, path)
    return path, "synthetic_rtc_fixture"
