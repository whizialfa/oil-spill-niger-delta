"""Site pipeline: RTC -> Lee -> Otsu dark spots -> GLCM filter -> polygons -> quoted row."""

from __future__ import annotations

import argparse
import json

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

from spill.acquire import resolve_pre_scene, resolve_scene
from spill.export_qgis import write_qgz
from spill.detect import change_dark_spot_mask, local_dark_spot_mask, pin_diagnostics, water_mask
from spill.discriminate import filter_lookalikes
from spill.paths import DATA_PROCESSED, MAPS, ensure_dirs
from spill.polygonize import mask_to_polygons
from spill.preprocess import align_to, lee_filter, to_db, read_backscatter, write_geotiff
from spill.sites import AREA_CRS, all_sites, get_site
from spill.validate import validate_point


def _v2_area_km2(db, oil, transform, crs) -> float:
    kept, _ = filter_lookalikes(db, oil)
    footprints = mask_to_polygons(kept, transform, crs)
    if footprints.empty:
        return 0.0
    return float(footprints["area_km2"].sum())


def run_site(site_id: str, allow_synthetic: bool = True) -> dict:
    site = get_site(site_id)
    path, scene_source = resolve_scene(site, allow_synthetic=allow_synthetic)
    linear, transform, crs, _profile = read_backscatter(path)
    filtered = lee_filter(linear, size=5)
    db = to_db(filtered)
    water = water_mask(db)
    v2_oil, v2_report = local_dark_spot_mask(db, water, transform, site["lon"], site["lat"], crs)
    pin = pin_diagnostics(db, water, transform, site["lon"], site["lat"], crs)
    pre_path, pre_source = resolve_pre_scene(site)
    pre_db = None
    pin_db_pre = None
    pin_delta_db = None
    if pre_path is not None:
        pre_linear, pre_transform, pre_crs, _ = read_backscatter(pre_path)
        pre_linear = align_to(pre_linear, pre_transform, pre_crs, linear.shape, transform, crs)
        pre_db = to_db(lee_filter(pre_linear, size=5))
        oil, detect_report = change_dark_spot_mask(
            db, pre_db, water, transform, site["lon"], site["lat"], crs
        )
        detect_report["pre_scene_source"] = pre_source
        detect_report["v2_slick_area_km2"] = round(_v2_area_km2(db, v2_oil, transform, crs), 6)
        r, c = pin["pin_row"], pin["pin_col"]
        if pin["pin_inside_raster"] and np.isfinite(pre_db[r, c]):
            pin_db_pre = float(pre_db[r, c])
            if pin["pin_db"] is not None:
                pin_delta_db = float(pin["pin_db"] - pin_db_pre)
    else:
        oil, detect_report = v2_oil, v2_report
    kept, lookalike_report = filter_lookalikes(db, oil)
    footprints = mask_to_polygons(kept, transform, crs)
    footprints["site_id"] = site["id"]
    footprints["site_name"] = site["name"]
    footprints["incident_date"] = site["incident_date"]
    footprints["scene_source"] = scene_source
    check = validate_point(footprints, site["lon"], site["lat"])
    area = float(footprints["area_km2"].sum()) if not footprints.empty else 0.0
    row = {
        "site_id": site["id"],
        "site_name": site["name"],
        "state": site["state"],
        "lga": site["lga"],
        "incident_date": site["incident_date"],
        "date_precision": site["date_precision"],
        "lon": site["lon"],
        "lat": site["lat"],
        "coord_source": site["coord_source"],
        "scene_source": scene_source,
        "nosdra_id": site.get("nosdra_id"),
        "nosdra_bbl": site.get("estimated_bbl"),
        "nosdra_jiv_area_km2": site.get("nosdra_jiv_area_km2"),
        "habitat": site.get("habitat"),
        "cause": site.get("cause"),
        "slick_area_km2": round(area, 6),
        "methods_darkened_km2": round(area, 6),
        "quote_km2_as_slick": False,
        "n_slicks": int(len(footprints)),
        "nosdra_point_in_footprint": check["nosdra_point_in_footprint"],
        "hit": check["hit"],
        "distance_to_nearest_slick_m": check["distance_to_nearest_slick_m"],
        "hit_distance_m": check["hit_distance_m"],
        "crs_area": AREA_CRS,
        "pin_db": pin["pin_db"],
        "pin_db_pre": pin_db_pre,
        "pin_delta_db": pin_delta_db,
        "pin_on_water": pin["pin_on_water"],
        "nearest_water_m": pin["nearest_water_m"],
        **detect_report,
        **lookalike_report,
    }
    return {
        "row": row,
        "footprints": footprints,
        "db": db,
        "pre_db": pre_db,
        "water": water,
        "oil": oil,
        "kept": kept,
        "transform": transform,
        "crs": crs,
        "site": site,
    }


def _write_preview(result: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from rasterio.plot import plotting_extent

    site = result["site"]
    db = result["db"]
    extent = plotting_extent(db, result["transform"])
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6), constrained_layout=True)
    axes[0].imshow(db, cmap="gray", extent=extent, origin="upper", vmin=-32, vmax=-6)
    axes[0].set_title("Post Lee σ⁰ (dB)")
    if result.get("pre_db") is not None:
        delta = db - result["pre_db"]
        axes[1].imshow(delta, cmap="RdBu", extent=extent, origin="upper", vmin=-6, vmax=6)
        axes[1].set_title("Post − pre (dB)")
        version = "v3"
    else:
        axes[1].imshow(result["oil"], cmap="gray", extent=extent, origin="upper")
        axes[1].set_title("Local dark spots (v2)")
        version = "v2"
    axes[2].imshow(result["kept"], cmap="gray", extent=extent, origin="upper")
    axes[2].set_title("After GLCM filter")
    for ax in axes:
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.tick_params(labelsize=7)
    fig.suptitle(f"{site['name']} — {result['row']['scene_source']} — {version}", fontsize=11)
    MAPS.mkdir(parents=True, exist_ok=True)
    fig.savefig(MAPS / f"{site['id']}_detect.png", dpi=120)
    plt.close(fig)


def run_all(site_ids: list[str] | None = None, allow_synthetic: bool = True) -> pd.DataFrame:
    ensure_dirs()
    sites = [get_site(s) for s in site_ids] if site_ids else all_sites()
    rows = []
    frames = []
    points = []
    for site in sites:
        result = run_site(site["id"], allow_synthetic=allow_synthetic)
        rows.append(result["row"])
        fp = result["footprints"]
        if not fp.empty:
            frames.append(fp)
        points.append(
            {
                "site_id": site["id"],
                "site_name": site["name"],
                "incident_date": site["incident_date"],
                "coord_source": site["coord_source"],
                "geometry": Point(site["lon"], site["lat"]),
            }
        )
        write_geotiff(
            DATA_PROCESSED / f"{site['id']}_sigma0_db.tif",
            result["db"],
            result["transform"],
            result["crs"],
        )
        if result.get("pre_db") is not None:
            write_geotiff(
                DATA_PROCESSED / f"{site['id']}_sigma0_db_pre.tif",
                result["pre_db"],
                result["transform"],
                result["crs"],
            )
            write_geotiff(
                DATA_PROCESSED / f"{site['id']}_delta_db.tif",
                result["db"] - result["pre_db"],
                result["transform"],
                result["crs"],
            )
        _write_preview(result)

    metrics = pd.DataFrame(rows)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(DATA_PROCESSED / "spill_metrics.csv", index=False)
    headline_cols = [
        "site_id",
        "site_name",
        "nosdra_id",
        "incident_date",
        "nosdra_bbl",
        "nosdra_jiv_area_km2",
        "habitat",
        "cause",
        "hit",
        "pin_on_water",
        "pin_db",
        "nearest_water_m",
        "distance_to_nearest_slick_m",
        "hit_distance_m",
        "methods_darkened_km2",
        "quote_km2_as_slick",
        "detector_version",
    ]
    present = [c for c in headline_cols if c in metrics.columns]
    metrics.loc[:, present].to_csv(DATA_PROCESSED / "headline.csv", index=False)

    pts = gpd.GeoDataFrame(points, geometry="geometry", crs="EPSG:4326")
    pts.to_file(DATA_PROCESSED / "nosdra_points.geojson", driver="GeoJSON")
    site_polys = pts.copy()
    site_polys["geometry"] = pts.to_crs(AREA_CRS).buffer(2500).to_crs("EPSG:4326")
    site_polys.to_file(DATA_PROCESSED / "sites.geojson", driver="GeoJSON")

    if frames:
        footprints = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs="EPSG:4326")
    else:
        footprints = gpd.GeoDataFrame(columns=["geometry"], geometry="geometry", crs="EPSG:4326")
    footprints.to_file(DATA_PROCESSED / "footprints.geojson", driver="GeoJSON")

    gpkg = DATA_PROCESSED / "oil_spill_results.gpkg"
    if gpkg.exists():
        gpkg.unlink()
    pts.to_file(gpkg, layer="nosdra_points", driver="GPKG")
    site_polys.to_file(gpkg, layer="sites", driver="GPKG")
    if not footprints.empty:
        footprints.to_file(gpkg, layer="footprints", driver="GPKG")

    (DATA_PROCESSED / "run_manifest.json").write_text(
        json.dumps(
            {
                "n_sites": len(rows),
                "quoted_table": "headline.csv",
                "headline_metric": "hit",
                "n_hits": int(metrics["hit"].sum()) if "hit" in metrics.columns else 0,
                "do_not_quote": "methods_darkened_km2",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_qgz()
    return metrics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Niger Delta oil-spill footprint pipeline")
    parser.add_argument("--site", action="append", dest="sites", help="Site id (repeatable)")
    parser.add_argument(
        "--no-synthetic",
        action="store_true",
        help="Fail if data/raw/{site}_rtc.tif is missing instead of writing a fixture",
    )
    args = parser.parse_args(argv)
    metrics = run_all(args.sites, allow_synthetic=not args.no_synthetic)
    print(metrics.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
