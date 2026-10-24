"""West-trio headline sites. All three are NOSDRA JIV leak pins (often land next to swamp water)."""

from __future__ import annotations

from typing import Any

# Area in metres: all three sites sit in UTM 31N (3 E to 9 E).
AREA_CRS = "EPSG:32631"
WGS84 = "EPSG:4326"

# Hit if the JIV point is inside a slick or within this distance (m).
HIT_DISTANCE_M = 500.0

SITES: dict[str, dict[str, Any]] = {
    "odidi_kantu": {
        "id": "odidi_kantu",
        "name": "Odidi-Kantu",
        "state": "Delta",
        "lga": "Warri South West",
        "incident_date": "2026-02-20",
        "date_precision": "day",
        "lon": 5.4444444,
        "lat": 5.4733333,
        "coord_source": "nosdra_jiv",
        "nosdra_id": "359834",
        "incident_number": "HEOSL/2025/328",
        "estimated_bbl": 700.0,
        "nosdra_jiv_area_km2": None,
        "habitat": "swamp, inland water",
        "cause": "corrosion",
        "coord_note": "NOSDRA JIV: 28\" Trans-Forcados Pipeline at Odidi-Kantu (Heritage). Habitat swamp and inland water.",
        "press_window": "Incident and JIV 20 Feb 2026.",
        "pre_start": "2026-02-01",
        "pre_end": "2026-02-19",
    },
    "odimodi_ramos": {
        "id": "odimodi_ramos",
        "name": "Odimodi (Trans-Ramos)",
        "state": "Delta",
        "lga": "Burutu",
        "incident_date": "2026-04-21",
        "date_precision": "day",
        "lon": 5.3683667,
        "lat": 5.2999944,
        "coord_source": "nosdra_jiv",
        "nosdra_id": "466367",
        "incident_number": "028974",
        "estimated_bbl": 2466.0,
        "nosdra_jiv_area_km2": 0.06991,
        "habitat": "swamp",
        "cause": "equipment",
        "coord_note": "NOSDRA JIV: 24\" Trans-Ramos Pipeline at Odimodi (Renaissance). Ramos stand-in for the missing Agge/Bonga 24 Jan 2026 row. Habitat swamp.",
        "press_window": "Incident 21 Apr 2026; JIV 23 Apr 2026.",
        "pre_start": "2026-04-01",
        "pre_end": "2026-04-20",
    },
    "opukushi": {
        "id": "opukushi",
        "name": "Opukushi",
        "state": "Bayelsa",
        "lga": "Ekeremor",
        "incident_date": "2025-12-26",
        "date_precision": "day",
        "lon": 5.7599461,
        "lat": 4.9243239,
        "coord_source": "nosdra_jiv",
        "nosdra_id": "466233",
        "incident_number": "2025_000312",
        "estimated_bbl": 1322.0,
        "nosdra_jiv_area_km2": 0.0292,
        "habitat": "swamp",
        "cause": "equipment",
        "coord_note": "NOSDRA JIV: Well 11L Opuhushi at Opukushi (Renaissance). NOSDRA lists the well as Opuhushi. Habitat swamp.",
        "press_window": "Incident 26 Dec 2025; JIV 29 Dec 2025.",
        "pre_start": "2025-12-06",
        "pre_end": "2025-12-25",
    },
}


def get_site(site_id: str) -> dict[str, Any]:
    try:
        return dict(SITES[site_id])
    except KeyError as exc:
        known = ", ".join(SITES)
        raise KeyError(f"Unknown site {site_id!r}. Known: {known}") from exc


def all_sites() -> list[dict[str, Any]]:
    return [dict(v) for v in SITES.values()]
