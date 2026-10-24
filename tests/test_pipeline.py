from __future__ import annotations

import geopandas as gpd
import numpy as np
from rasterio.transform import from_origin

from spill.detect import change_dark_spot_mask, dark_spot_mask, local_dark_spot_mask, water_mask
from spill.discriminate import filter_lookalikes
from spill.fixtures import build_synthetic_db
from spill.polygonize import mask_to_polygons
from spill.preprocess import from_db, lee_filter, to_db
from spill.sites import AREA_CRS, HIT_DISTANCE_M, get_site
from spill.pipeline import run_site
from spill.validate import validate_point


def test_pipeline_fixture_keeps_textured_slick(tmp_path, monkeypatch):
    import spill.acquire as acquire
    import spill.pipeline as pipeline

    monkeypatch.setattr(acquire, "DATA_RAW", tmp_path)
    monkeypatch.setattr(pipeline, "DATA_PROCESSED", tmp_path)
    monkeypatch.setattr(pipeline, "MAPS", tmp_path)
    result = run_site("opukushi", allow_synthetic=True)
    row = result["row"]
    assert row["scene_source"] == "synthetic_rtc_fixture"
    assert row["components_dropped_low_texture"] >= 1
    assert row["n_slicks"] >= 1
    assert row["slick_area_km2"] > 0
    assert row["hit"] is True
    assert row["detector_version"] == "v2_local_water"
    assert row["quote_km2_as_slick"] is False



def test_lee_filter_reduces_variance():
    rng = np.random.default_rng(0)
    img = np.ones((40, 40)) * 0.02
    noisy = img * rng.lognormal(0, 0.4, img.shape)
    filtered = lee_filter(noisy, size=5)
    assert filtered.var() < noisy.var()


def test_synthetic_dark_spot_and_lookalike():
    db = build_synthetic_db()
    water = water_mask(db)
    oil = dark_spot_mask(db, water)
    kept, report = filter_lookalikes(db, oil)
    assert water.sum() > 1000
    assert oil.sum() > 50
    assert kept.sum() > 30
    assert report["components_dropped_low_texture"] >= 1
    assert kept.sum() < oil.sum()


def test_polygon_area_and_hit():
    db = build_synthetic_db()
    water = water_mask(db)
    oil = dark_spot_mask(db, water)
    kept, _ = filter_lookalikes(db, oil)
    transform = from_origin(200000.0, 600000.0, 10.0, 10.0)
    gdf = mask_to_polygons(kept, transform, AREA_CRS)
    assert not gdf.empty
    assert float(gdf.area_km2.sum()) > 0
    metric = gdf.to_crs(AREA_CRS)
    pt = metric.geometry.iloc[0].centroid
    wgs = gpd.GeoSeries([pt], crs=AREA_CRS).to_crs("EPSG:4326").iloc[0]
    check = validate_point(gdf, wgs.x, wgs.y)
    assert check["hit"] is True
    assert check["nosdra_point_in_footprint"] is True


def test_miss_when_point_is_far():
    db = build_synthetic_db()
    water = water_mask(db)
    oil = dark_spot_mask(db, water)
    kept, _ = filter_lookalikes(db, oil)
    transform = from_origin(200000.0, 600000.0, 10.0, 10.0)
    gdf = mask_to_polygons(kept, transform, AREA_CRS)
    check = validate_point(gdf, 0.0, 0.0)
    assert check["hit"] is False
    assert check["distance_to_nearest_slick_m"] > HIT_DISTANCE_M


def test_jiv_sites_are_flagged():
    for site_id in ("odidi_kantu", "odimodi_ramos", "opukushi"):
        site = get_site(site_id)
        assert site["coord_source"] == "nosdra_jiv"
        assert site["estimated_bbl"] > 0


def test_db_roundtrip():
    x = np.array([[0.01, 0.02]])
    assert np.allclose(from_db(to_db(x)), x)


def test_local_mask_keeps_near_swamp_dark_and_drops_far():
    db = np.full((200, 200), -8.0)
    yy, xx = np.mgrid[0:200, 0:200]
    creek = np.abs(yy - 95) < 6
    db[creek] = -16.2
    near = creek & (np.abs(xx - 115) < 12)
    db[near] = -20.5
    far = creek & (np.abs(xx - 175) < 12)
    db[far] = -28.0
    db[98:103, 98:103] = -2.0
    transform = from_origin(200000.0, 602000.0, 10.0, 10.0)
    x, y = transform * (100.5, 100.5)
    wgs = gpd.GeoSeries.from_xy([x], [y], crs=AREA_CRS).to_crs("EPSG:4326").iloc[0]
    water = water_mask(db)
    assert water[95, 115]
    v1 = dark_spot_mask(db, water, oil_db_max=-22.0)
    assert not v1[95, 115]
    oil, report = local_dark_spot_mask(
        db, water, transform, float(wgs.x), float(wgs.y), AREA_CRS, search_radius_m=400.0
    )
    assert report["local_water_px"] > 16
    assert oil[95, 115]
    assert not oil[95, 175]


def test_change_mask_drops_stable_dark_water():
    post = np.full((80, 80), -8.0)
    pre = np.full((80, 80), -8.0)
    yy, xx = np.mgrid[0:80, 0:80]
    creek = np.abs(yy - 40) < 5
    pre[creek] = -16.5
    post[creek] = -16.5
    near = creek & (np.abs(xx - 45) < 8)
    post[near] = -20.5
    far = creek & (np.abs(xx - 70) < 8)
    pre[far] = -20.5
    post[far] = -20.5
    post[38:43, 38:43] = -2.0
    pre[38:43, 38:43] = -2.0
    transform = from_origin(200000.0, 600800.0, 10.0, 10.0)
    x, y = transform * (40.5, 40.5)
    wgs = gpd.GeoSeries.from_xy([x], [y], crs=AREA_CRS).to_crs("EPSG:4326").iloc[0]
    water = water_mask(post)
    oil, report = change_dark_spot_mask(
        post, pre, water, transform, float(wgs.x), float(wgs.y), AREA_CRS, search_radius_m=400.0
    )
    assert report["detector_version"] == "v3_prepost"
    assert oil[40, 45]
    assert not oil[40, 70]
