"""Three NOSDRA-named incidents. Coordinates are provisional community/field centroids, not JIV points."""

from __future__ import annotations

from typing import Any

# Area in metres: all three sites sit in UTM 31N (3 E to 9 E).
AREA_CRS = "EPSG:32631"
WGS84 = "EPSG:4326"

# Hit if the NOSDRA/community point is inside a slick or within this distance (m).
# Community centroids are not JIV pins; 500 m is a stated tolerance, not a slick size.
HIT_DISTANCE_M = 500.0

SITES: dict[str, dict[str, Any]] = {
    "biseni_tein": {
        "id": "biseni_tein",
        "name": "Biseni/Tein",
        "state": "Bayelsa",
        "lga": "Yenagoa",
        "incident_date": "2025-12-15",
        "date_precision": "month",
        "lon": 6.37583,
        "lat": 5.11016,
        "coord_source": "community_centroid_provisional",
        "coord_note": "Biseni postcode centroid (569101). Not a NOSDRA JIV coordinate. Tein is in Biseni Kingdom; Fazino/Fadino Lake is the reported receiving water.",
        "press_window": "Pipeline rupture reported around December 2025; EDEN site visit 14 Feb 2026.",
    },
    "agge_bonga": {
        "id": "agge_bonga",
        "name": "Agge/Bonga",
        "state": "Bayelsa",
        "lga": "Ekeremor",
        "incident_date": "2026-01-24",
        "date_precision": "day",
        "lon": 5.39485,
        "lat": 5.13023,
        "coord_source": "community_centroid_provisional",
        "coord_note": "Agge settlement coordinate. Bonga FPSO is offshore; this point is the named receiving community on the Trans-Ramos, not the wellhead.",
        "press_window": "Community reports the spill began 24 Jan 2026 during Bonga field maintenance.",
    },
    "odidi_kantu": {
        "id": "odidi_kantu",
        "name": "Odidi-Kantu",
        "state": "Delta",
        "lga": "Warri South West",
        "incident_date": "2026-02-19",
        "date_precision": "day",
        "lon": 5.456,
        "lat": 5.548,
        "coord_source": "facility_centroid_provisional",
        "coord_note": "Odidi oil and gas field (OML 42) WGS84 from Global Energy Monitor. Kantu is a neighbouring riverine community; not a NOSDRA JIV pin.",
        "press_window": "Trans-Forcados Pipeline spill reported 19 Feb 2026 (Heritage Energy).",
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
