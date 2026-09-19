from __future__ import annotations

import geopandas as gpd
import numpy as np
from rasterio.transform import from_origin

from spill.detect import dark_spot_mask, water_mask
from spill.discriminate import filter_lookalikes
from spill.fixtures import build_synthetic_db
from spill.polygonize import mask_to_polygons
from spill.preprocess import from_db, lee_filter, to_db
from spill.sites import AREA_CRS, HIT_DISTANCE_M, get_site
from spill.pipeline import run_site
from spill.validate import validate_point


def test_pipeline_fixture_keeps_textured_slick():
    result = run_site("biseni_tein")
    row = result["row"]
    assert row["scene_source"] == "synthetic_rtc_fixture"
    assert row["components_dropped_low_texture"] >= 1
    assert row["n_slicks"] >= 1
    assert row["slick_area_km2"] > 0
    assert row["hit"] is True



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


def test_sites_have_provisional_flag():
    site = get_site("biseni_tein")
    assert "provisional" in site["coord_source"]
    assert site["incident_date"].startswith("2025")


def test_db_roundtrip():
    x = np.array([[0.01, 0.02]])
    assert np.allclose(from_db(to_db(x)), x)
