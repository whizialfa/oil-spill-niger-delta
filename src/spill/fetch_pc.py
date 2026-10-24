"""Windowed Sentinel-1 GRD from Microsoft Planetary Computer. No Earthdata login."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds

from spill.acquire import rtc_path
from spill.paths import DATA_RAW, ensure_dirs
from spill.sites import get_site

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
SAS = "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-1-rtc"
COLLECTION = "sentinel-1-rtc"


def _post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode())


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode())


def sign_href(href: str) -> str:
    token = _get_json(SAS)["token"]
    sep = "&" if "?" in href else "?"
    return f"{href}{sep}{token}"


def search_grd(lon: float, lat: float, start: str, end: str, limit: int = 8) -> list[dict]:
    payload = {
        "collections": [COLLECTION],
        "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z",
        "intersects": {"type": "Point", "coordinates": [lon, lat]},
        "limit": limit,
    }
    feats = _post_json(STAC, payload).get("features", [])
    return feats


def _hour(feature: dict) -> int | None:
    dt = feature.get("properties", {}).get("datetime") or ""
    try:
        return int(dt[11:13])
    except (TypeError, ValueError):
        return None


def pick_feature(
    feats: list[dict],
    pick: str = "first",
    prefer_hour: int | None = None,
    prefer_orbit: int | None = None,
) -> dict:
    feats = sorted(feats, key=lambda f: f.get("properties", {}).get("datetime", ""))
    if prefer_orbit is not None:
        matched = [
            f for f in feats if f.get("properties", {}).get("sat:relative_orbit") == prefer_orbit
        ]
        if matched:
            feats = matched
    elif prefer_hour is not None:
        matched = [f for f in feats if _hour(f) is not None and abs(_hour(f) - prefer_hour) <= 2]
        if matched:
            feats = matched
    if pick == "last":
        return feats[-1]
    return feats[0]


def sidecar_hour(site_id: str) -> int | None:
    side = rtc_path(site_id).with_suffix(".json")
    if not side.exists():
        return None
    dt = json.loads(side.read_text(encoding="utf-8")).get("datetime") or ""
    try:
        return int(dt[11:13])
    except (TypeError, ValueError):
        return None


def window_vv(feature: dict, lon: float, lat: float, half_m: float, dest: Path) -> dict:
    from pyproj import Transformer

    href = sign_href(feature["assets"]["vv"]["href"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(href) as src:
        to_r = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        x, y = to_r.transform(lon, lat)
        west, south, east, north = x - half_m, y - half_m, x + half_m, y + half_m
        window = from_bounds(west, south, east, north, src.transform)
        window = window.round_offsets().round_lengths()
        data = src.read(1, window=window).astype(np.float64)
        transform = src.window_transform(window)
        profile = src.profile
        crs = src.crs.to_string() if src.crs else "EPSG:4326"
        nodata = src.nodata
    if nodata is not None:
        data = np.where(data == nodata, np.nan, data)
    profile.update(
        {
            "driver": "GTiff",
            "height": data.shape[0],
            "width": data.shape[1],
            "count": 1,
            "dtype": "float32",
            "crs": crs,
            "transform": transform,
            "compress": "lzw",
            "nodata": -9999.0,
        }
    )
    out = np.where(np.isfinite(data), data, -9999.0).astype(np.float32)
    with rasterio.open(dest, "w", **profile) as dst:
        dst.write(out, 1)
    props = feature.get("properties", {})
    meta = {
        "scene_source": "planetary_computer_s1_rtc",
        "scene_id": feature["id"],
        "datetime": props.get("datetime"),
        "polarization": "VV",
        "sat:relative_orbit": props.get("sat:relative_orbit"),
        "sat:orbit_state": props.get("sat:orbit_state"),
        "note": "Windowed Sentinel-1 RTC from Planetary Computer. Not SNAP gpt.",
    }
    dest.with_suffix(".json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def fetch_site(
    site_id: str,
    start: str,
    end: str,
    half_m: float = 12000.0,
    role: str = "post",
    pick: str = "first",
    prefer_hour: int | None = None,
    prefer_orbit: int | None = None,
    limit: int = 12,
) -> dict:
    ensure_dirs()
    site = get_site(site_id)
    feats = search_grd(site["lon"], site["lat"], start, end, limit=limit)
    if not feats:
        raise FileNotFoundError(f"No Sentinel-1 RTC on Planetary Computer for {site_id} {start}–{end}")
    chosen = pick_feature(feats, pick=pick, prefer_hour=prefer_hour, prefer_orbit=prefer_orbit)
    dest = rtc_path(site_id, role)
    meta = window_vv(chosen, site["lon"], site["lat"], half_m, dest)
    meta["site_id"] = site_id
    meta["role"] = role
    meta["n_candidates"] = len(feats)
    meta["candidates"] = [f["id"] for f in feats]
    search_name = f"{site_id}_pc_search.json" if role == "post" else f"{site_id}_pc_search_pre.json"
    (DATA_RAW / search_name).write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def fetch_pre_site(site_id: str, half_m: float = 12000.0) -> dict:
    site = get_site(site_id)
    return fetch_site(
        site_id,
        site["pre_start"],
        site["pre_end"],
        half_m=half_m,
        role="pre",
        pick="last",
        prefer_hour=sidecar_hour(site_id),
    )
