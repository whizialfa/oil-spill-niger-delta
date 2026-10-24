"""Build a fresh QGIS 3 project from pipeline GeoJSON. Does not touch any legacy .qgz."""

from __future__ import annotations

import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from spill.paths import DATA_PROCESSED, QGIS, ROOT, ensure_dirs
from spill.sites import all_sites

LAYERS = (
    {
        "name": "sites",
        "file": "sites.geojson",
        "geometry": "Polygon",
        "type": "fill",
        "color": "31,120,180,40",
        "outline": "31,120,180,255",
    },
    {
        "name": "footprints",
        "file": "footprints.geojson",
        "geometry": "Polygon",
        "type": "fill",
        "color": "227,26,28,140",
        "outline": "128,0,0,255",
    },
    {
        "name": "nosdra_points",
        "file": "nosdra_points.geojson",
        "geometry": "Point",
        "type": "marker",
        "color": "255,255,51,255",
        "outline": "0,0,0,255",
    },
)


# SAR stretch: water/oil dark, land bright.
SIGMA0_MIN_DB = -28.0
SIGMA0_MAX_DB = -4.0
DELTA_ABS_DB = 5.0


def _spatialref() -> str:
    return """
    <srs>
      <spatialrefsys nativeFormat="Wkt">
        <wkt>GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]</wkt>
        <proj4>+proj=longlat +datum=WGS84 +no_defs</proj4>
        <srsid>3452</srsid>
        <srid>4326</srid>
        <authid>EPSG:4326</authid>
        <description>WGS 84</description>
        <projectionacronym>longlat</projectionacronym>
        <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
        <geographicflag>true</geographicflag>
      </spatialrefsys>
    </srs>
    """


def _fill_renderer(color: str, outline: str) -> str:
    return f"""
    <renderer-v2 type="singleSymbol" symbollevels="0" forceraster="0" enableorderby="0" referencescale="-1">
      <symbols>
        <symbol type="fill" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" name="name" value=""/>
              <Option name="properties"/>
              <Option type="QString" name="type" value="collection"/>
            </Option>
          </data_defined_properties>
          <layer class="SimpleFill" locked="0" enabled="1" pass="0">
            <Option type="Map">
              <Option type="QString" name="color" value="{color}"/>
              <Option type="QString" name="outline_color" value="{outline}"/>
              <Option type="QString" name="outline_width" value="0.4"/>
              <Option type="QString" name="outline_width_unit" value="MM"/>
              <Option type="QString" name="style" value="solid"/>
            </Option>
          </layer>
        </symbol>
      </symbols>
    </renderer-v2>
    """


def _marker_renderer(color: str, outline: str) -> str:
    return f"""
    <renderer-v2 type="singleSymbol" symbollevels="0" forceraster="0" enableorderby="0" referencescale="-1">
      <symbols>
        <symbol type="marker" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" name="name" value=""/>
              <Option name="properties"/>
              <Option type="QString" name="type" value="collection"/>
            </Option>
          </data_defined_properties>
          <layer class="SimpleMarker" locked="0" enabled="1" pass="0">
            <Option type="Map">
              <Option type="QString" name="color" value="{color}"/>
              <Option type="QString" name="name" value="circle"/>
              <Option type="QString" name="outline_color" value="{outline}"/>
              <Option type="QString" name="outline_width" value="0.4"/>
              <Option type="QString" name="size" value="3.2"/>
              <Option type="QString" name="size_unit" value="MM"/>
            </Option>
          </layer>
        </symbol>
      </symbols>
    </renderer-v2>
    """


def _utm31_srs() -> str:
    return """
    <srs>
      <spatialrefsys nativeFormat="Wkt">
        <wkt>PROJCS["WGS 84 / UTM zone 31N",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",3],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1],AUTHORITY["EPSG","32631"]]</wkt>
        <proj4>+proj=utm +zone=31 +datum=WGS84 +units=m +no_defs</proj4>
        <srsid>2647</srsid>
        <srid>32631</srid>
        <authid>EPSG:32631</authid>
        <description>WGS 84 / UTM zone 31N</description>
        <projectionacronym>utm</projectionacronym>
        <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
        <geographicflag>false</geographicflag>
      </spatialrefsys>
    </srs>
    """


def _minmax_origin() -> str:
    return """
      <minMaxOrigin>
        <limits>MinMax</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Exact</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>0.0</stdDevFactor>
      </minMaxOrigin>
    """


def _gray_renderer() -> str:
    return f"""
    <pipe>
      <rasterrenderer opacity="1" alphaBand="-1" grayBand="1" type="singlebandgray" nodataColor="">
        <rasterTransparency/>
        {_minmax_origin()}
        <contrastEnhancement>
          <minValue>{SIGMA0_MIN_DB}</minValue>
          <maxValue>{SIGMA0_MAX_DB}</maxValue>
          <algorithm>StretchToMinimumMaximum</algorithm>
        </contrastEnhancement>
      </rasterrenderer>
      <brightnesscontrast brightness="0" contrast="0" gamma="1"/>
      <huesaturation colorizeOn="0" grayscaleMode="0" saturation="0" invertColors="0"/>
    </pipe>
    """


def _delta_renderer() -> str:
    lo, hi = -DELTA_ABS_DB, DELTA_ABS_DB
    return f"""
    <pipe>
      <rasterrenderer opacity="1" band="1" type="singlebandpseudocolor" classificationMin="{lo}" classificationMax="{hi}" nodataColor="">
        <rasterTransparency/>
        {_minmax_origin()}
        <rastershader>
          <colorrampshader colorRampType="INTERPOLATED" classificationMode="1" clip="0" minimumValue="{lo}" maximumValue="{hi}">
            <item value="{lo}" label="-5 dB darker" alpha="255" color="#0571b0"/>
            <item value="0" label="0" alpha="255" color="#f7f7f7"/>
            <item value="{hi}" label="+5 dB brighter" alpha="255" color="#ca0020"/>
          </colorrampshader>
        </rastershader>
      </rasterrenderer>
      <brightnesscontrast brightness="0" contrast="0" gamma="1"/>
    </pipe>
    """


def _raster_layer(layer_id: str, name: str, rel_source: str, kind: str) -> str:
    renderer = _delta_renderer() if kind == "delta" else _gray_renderer()
    return f"""
  <maplayer type="raster" hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories">
    <id>{layer_id}</id>
    <datasource>{escape(rel_source)}</datasource>
    <keywordList><value></value></keywordList>
    <layername>{escape(name)}</layername>
    {_utm31_srs()}
    <provider>gdal</provider>
    {renderer}
  </maplayer>
"""


def _maplayer(layer_id: str, spec: dict, rel_source: str) -> str:
    renderer = (
        _marker_renderer(spec["color"], spec["outline"])
        if spec["type"] == "marker"
        else _fill_renderer(spec["color"], spec["outline"])
    )
    name = escape(spec["name"])
    return f"""
  <maplayer type="vector" geometry="{spec["geometry"]}" hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories">
    <id>{layer_id}</id>
    <datasource>{escape(rel_source)}</datasource>
    <keywordList><value></value></keywordList>
    <layername>{name}</layername>
    {_spatialref()}
    <provider encoding="UTF-8">ogr</provider>
    {renderer}
  </maplayer>
"""


def _raster_specs() -> list[dict]:
    specs = []
    for site in all_sites():
        sid, name = site["id"], site["name"]
        specs.extend(
            [
                {
                    "group": f"{name} scenes",
                    "name": f"{name} post VV (dB)",
                    "file": f"{sid}_sigma0_db.tif",
                    "kind": "sigma0",
                    "checked": True,
                },
                {
                    "group": f"{name} scenes",
                    "name": f"{name} pre VV (dB)",
                    "file": f"{sid}_sigma0_db_pre.tif",
                    "kind": "sigma0",
                    "checked": False,
                },
                {
                    "group": f"{name} scenes",
                    "name": f"{name} change (dB)",
                    "file": f"{sid}_delta_db.tif",
                    "kind": "delta",
                    "checked": False,
                },
            ]
        )
    return specs


def build_qgs() -> str:
    layers = []
    projectlayers = []
    vector_tree = []
    for spec in LAYERS:
        abs_path = DATA_PROCESSED / spec["file"]
        if not abs_path.exists():
            continue
        layer_id = spec["name"] + "_" + uuid.uuid4().hex[:12]
        rel_s = (Path("..") / "data" / "processed" / spec["file"]).as_posix()
        layers.append(layer_id)
        vector_tree.append(
            f'      <layer-tree-layer id="{layer_id}" name="{escape(spec["name"])}" '
            f'source="{escape(rel_s)}" providerKey="ogr" checked="Qt::Checked" expanded="0"/>'
        )
        projectlayers.append(_maplayer(layer_id, spec, rel_s))

    raster_groups: dict[str, list[str]] = {}
    for spec in _raster_specs():
        abs_path = DATA_PROCESSED / spec["file"]
        if not abs_path.exists():
            continue
        layer_id = spec["file"].replace(".", "_") + "_" + uuid.uuid4().hex[:8]
        rel_s = (Path("..") / "data" / "processed" / spec["file"]).as_posix()
        layers.append(layer_id)
        checked = "Qt::Checked" if spec["checked"] else "Qt::Unchecked"
        raster_groups.setdefault(spec["group"], []).append(
            f'      <layer-tree-layer id="{layer_id}" name="{escape(spec["name"])}" '
            f'source="{escape(rel_s)}" providerKey="gdal" checked="{checked}" expanded="0"/>'
        )
        projectlayers.append(_raster_layer(layer_id, spec["name"], rel_s, spec["kind"]))

    tree_parts = [
        '    <layer-tree-group name="JIVs and slicks" checked="Qt::Checked" expanded="1">',
        *vector_tree,
        "    </layer-tree-group>",
    ]
    for group_name, children in raster_groups.items():
        tree_parts.append(
            f'    <layer-tree-group name="{escape(group_name)}" checked="Qt::Checked" expanded="1">'
        )
        tree_parts.extend(children)
        tree_parts.append("    </layer-tree-group>")

    order = "\n".join(f"      <item>{lid}</item>" for lid in layers)
    return f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.28.0-Firenze" projectname="oil-spill-niger-delta">
  <title>Niger Delta oil-spill footprints</title>
  <homePath path=""/>
  <projectCrs>
    {_spatialref()}
  </projectCrs>
  <layer-tree-group>
{chr(10).join(tree_parts)}
    <custom-order enabled="0">
{order}
    </custom-order>
  </layer-tree-group>
  <mapcanvas name="theMapCanvas" annotationsVisible="1">
    <units>degrees</units>
    {_spatialref()}
    <extent>
      <xmin>5.25</xmin>
      <ymin>4.85</ymin>
      <xmax>5.85</xmax>
      <ymax>5.55</ymax>
    </extent>
  </mapcanvas>
  <projectlayers>
{"".join(projectlayers)}
  </projectlayers>
  <layerorder>
{order}
  </layerorder>
  <properties>
    <Paths>
      <Absolute type="bool">false</Absolute>
    </Paths>
  </properties>
</qgis>
"""


def write_qgz(path: Path | None = None) -> Path:
    ensure_dirs()
    path = path or (QGIS / "oil_spill_niger_delta.qgz")
    qgs_name = "oil_spill_niger_delta.qgs"
    xml = build_qgs()
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(qgs_name, xml)
    readme = QGIS / "README.md"
    readme.write_text(
        "# QGIS package\n\n"
        "Open `oil_spill_niger_delta.qgz`.\n\n"
        "Vectors (`../data/processed/*.geojson`): JIV points, slick footprints, 2.5 km site rings.\n"
        "Rasters (`../data/processed/*_{sigma0_db,sigma0_db_pre,delta_db}.tif`): Lee VV in dB.\n\n"
        "- Post / pre: gray stretch −28 to −4 dB (water dark, land bright). Post is on; pre is off.\n"
        "- Change: blue = darkened after the incident, red = brighter, white = 0. Off by default.\n\n"
        "This is a **new** project built from the Python pipeline. Do not treat it as an "
        "edit of `bonga_spill_2026.qgz`.\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    out = write_qgz()
    print(out.relative_to(ROOT) if out.is_relative_to(ROOT) else out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
