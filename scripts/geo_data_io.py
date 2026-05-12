"""Geographic data inspection and format detection utilities."""

import json
from pathlib import Path

import numpy as np


def inspect_raster(path: str) -> dict:
    """Inspect a raster file and return metadata summary.

    Returns dict with: crs, epsg, bounds, resolution, width, height, band_count,
    dtype, nodata, value_range (per band).
    """
    import rasterio

    p = Path(path)
    if not p.exists():
        return {"error": f"File not found: {path}"}

    try:
        with rasterio.open(path) as src:
            crs = src.crs
            epsg = crs.to_epsg() if crs else None
            bounds = src.bounds
            res = src.res
            nodata = src.nodata

            value_ranges = []
            for i in range(1, src.count + 1):
                band = src.read(i, masked=True)
                if band.count() > 0:
                    value_ranges.append({
                        "band": i,
                        "min": float(band.min()),
                        "max": float(band.max()),
                        "mean": float(band.mean()),
                    })
                else:
                    value_ranges.append({"band": i, "min": None, "max": None, "mean": None})

            return {
                "file": str(p.name),
                "format": p.suffix.lower(),
                "crs": str(crs) if crs else None,
                "epsg": epsg,
                "bounds": {"left": bounds.left, "bottom": bounds.bottom,
                           "right": bounds.right, "top": bounds.top},
                "resolution": {"x": res[0], "y": res[1]},
                "width": src.width,
                "height": src.height,
                "band_count": src.count,
                "dtype": str(src.dtypes[0]),
                "nodata": nodata,
                "value_ranges": value_ranges,
            }
    except Exception as e:
        return {"error": str(e)}


def inspect_vector(path: str) -> dict:
    """Inspect a vector file and return metadata summary.

    Returns dict with: crs, epsg, geometry_type, feature_count, bounds, columns.
    """
    import geopandas as gpd

    p = Path(path)
    if not p.exists():
        return {"error": f"File not found: {path}"}

    try:
        gdf = gpd.read_file(path)
        crs = gdf.crs
        epsg = crs.to_epsg() if crs else None
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]

        return {
            "file": str(p.name),
            "format": p.suffix.lower(),
            "crs": str(crs) if crs else None,
            "epsg": epsg,
            "geometry_type": gdf.geom_type.unique().tolist(),
            "feature_count": len(gdf),
            "bounds": {"left": bounds[0], "bottom": bounds[1],
                       "right": bounds[2], "top": bounds[3]},
            "columns": [c for c in gdf.columns if c != "geometry"],
            "dtypes": {c: str(gdf[c].dtype) for c in gdf.columns if c != "geometry"},
        }
    except Exception as e:
        return {"error": str(e)}


def auto_detect_format(path: str) -> str:
    """Detect file format type: raster, vector, pointcloud, tabular, unknown."""
    p = Path(path)
    ext = p.suffix.lower()

    raster_exts = {".tif", ".tiff", ".geotiff", ".img", ".nc", ".hdf", ".h4", ".h5",
                   ".hdf5", ".grib", ".grb", ".grd"}
    vector_exts = {".shp", ".geojson", ".json", ".gpkg", ".kml", ".gml"}
    pointcloud_exts = {".las", ".laz"}
    tabular_exts = {".csv", ".tsv", ".xlsx", ".xls"}

    if ext in raster_exts:
        return "raster"
    elif ext in vector_exts:
        return "vector"
    elif ext in pointcloud_exts:
        return "pointcloud"
    elif ext in tabular_exts:
        return "tabular"
    else:
        return "unknown"


def batch_inspect(directory: str, pattern: str = "*") -> list:
    """Inspect all matching files in a directory."""
    p = Path(directory)
    if not p.exists():
        return [{"error": f"Directory not found: {directory}"}]

    results = []
    for f in sorted(p.glob(pattern)):
        fmt = auto_detect_format(str(f))
        if fmt == "raster":
            results.append(inspect_raster(str(f)))
        elif fmt == "vector":
            results.append(inspect_vector(str(f)))
        else:
            results.append({"file": f.name, "format": fmt, "note": "Skipped (not raster/vector)"})

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspect geographic data files")
    parser.add_argument("--input", required=True, help="File or directory path")
    parser.add_argument("--pattern", default="*", help="Glob pattern for directory mode")
    parser.add_argument("--output", help="Save report to JSON file")
    args = parser.parse_args()

    p = Path(args.input)
    if p.is_dir():
        report = batch_inspect(args.input, args.pattern)
    else:
        fmt = auto_detect_format(args.input)
        if fmt == "raster":
            report = inspect_raster(args.input)
        elif fmt == "vector":
            report = inspect_vector(args.input)
        else:
            report = {"file": p.name, "format": fmt}

    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
