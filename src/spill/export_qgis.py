"""Build a fresh QGIS 3 project from pipeline GeoJSON. Does not touch any legacy .qgz."""

from __future__ import annotations

import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from spill.paths import DATA_PROCESSED, QGIS, ROOT, ensure_dirs

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


def build_qgs() -> str:
    layers = []
    tree = []
    projectlayers = []
    for spec in LAYERS:
        abs_path = DATA_PROCESSED / spec["file"]
        if not abs_path.exists():
            continue
        layer_id = spec["name"] + "_" + uuid.uuid4().hex[:12]
        rel = Path("..") / "data" / "processed" / spec["file"]
        rel_s = rel.as_posix()
        layers.append((layer_id, spec["name"], rel_s))
        tree.append(
            f'    <layer-tree-layer id="{layer_id}" name="{escape(spec["name"])}" '
            f'source="{escape(rel_s)}" providerKey="ogr" checked="Qt::Checked" expanded="1"/>'
        )
        projectlayers.append(_maplayer(layer_id, spec, rel_s))
    order = "\n".join(f"      <item>{lid}</item>" for lid, _n, _s in reversed(layers))
    tree_xml = "\n".join(reversed(tree))
    return f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.28.0-Firenze" projectname="oil-spill-niger-delta">
  <title>Niger Delta oil-spill footprints</title>
  <homePath path=""/>
  <projectCrs>
    {_spatialref()}
  </projectCrs>
  <layer-tree-group>
{tree_xml}
    <custom-order enabled="1">
{order}
    </custom-order>
  </layer-tree-group>
  <mapcanvas name="theMapCanvas" annotationsVisible="1">
    <units>degrees</units>
    {_spatialref()}
    <extent>
      <xmin>4.8</xmin>
      <ymin>4.7</ymin>
      <xmax>6.8</xmax>
      <ymax>5.9</ymax>
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
        "Open `oil_spill_niger_delta.qgz`. Layers are relative paths into "
        "`../data/processed/*.geojson` (sites, footprints, NOSDRA/community points).\n\n"
        "This is a **new** project built from the Python pipeline. Do not treat it as an "
        "edit of `bonga_spill_2026.qgz`. That file, if found, is a reference-layer source only.\n"
        "Bulk RTC GeoTIFFs stay in `data/raw/` and are not packaged here.\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    out = write_qgz()
    print(out.relative_to(ROOT) if out.is_relative_to(ROOT) else out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
