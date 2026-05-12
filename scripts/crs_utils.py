"""CRS detection, transformation, and reprojection utilities."""

from pathlib import Path


def detect_crs(path: str) -> dict:
    """Detect CRS from a raster or vector file.

    Returns dict with: source (raster/vector), crs_string, epsg, proj4.
    """
    p = Path(path)
    ext = p.suffix.lower()

    raster_exts = {".tif", ".tiff", ".img", ".nc", ".hdf", ".h5"}
    vector_exts = {".shp", ".geojson", ".gpkg", ".json"}

    if ext in raster_exts:
        import rasterio
        with rasterio.open(path) as src:
            crs = src.crs
            return {
                "source": "raster",
                "crs_string": str(crs),
                "epsg": crs.to_epsg() if crs else None,
                "proj4": crs.to_proj4() if crs else None,
            }
    elif ext in vector_exts:
        import geopandas as gpd
        gdf = gpd.read_file(path)
        crs = gdf.crs
        return {
            "source": "vector",
            "crs_string": str(crs),
            "epsg": crs.to_epsg() if crs else None,
            "proj4": crs.to_proj4() if crs else None,
        }
    else:
        return {"error": f"Unsupported format: {ext}"}


def transform_point(x: float, y: float, src_crs: str, dst_crs: str) -> tuple:
    """Transform a single point between CRS.

    Returns (x_new, y_new) in destination CRS.
    """
    from pyproj import Transformer

    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    return transformer.transform(x, y)


def reproject_raster(src_path: str, dst_crs: str, dst_path: str,
                     resampling: str = "bilinear") -> str:
    """Reproject a raster to a target CRS.

    Args:
        src_path: Source raster path
        dst_crs: Target CRS (e.g., "EPSG:32645")
        dst_path: Output raster path
        resampling: Resampling method (bilinear, nearest, cubic, average)

    Returns: Output file path
    """
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling

    resampling_map = {
        "bilinear": Resampling.bilinear,
        "nearest": Resampling.nearest,
        "cubic": Resampling.cubic,
        "average": Resampling.average,
    }
    resamp = resampling_map.get(resampling, Resampling.bilinear)

    with rasterio.open(src_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update({
            "crs": dst_crs,
            "transform": transform,
            "width": width,
            "height": height,
        })

        with rasterio.open(dst_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=resamp,
                )

    return dst_path


def reproject_vector(src_path: str, dst_crs: str, dst_path: str) -> str:
    """Reproject a vector file to a target CRS.

    Args:
        src_path: Source vector path
        dst_crs: Target CRS (e.g., "EPSG:32645")
        dst_path: Output vector path

    Returns: Output file path
    """
    import geopandas as gpd

    gdf = gpd.read_file(src_path)
    gdf_proj = gdf.to_crs(dst_crs)
    gdf_proj.to_file(dst_path)

    return dst_path


def batch_reproject(directory: str, dst_crs: str, pattern: str = "*.tif",
                    resampling: str = "bilinear") -> list:
    """Reproject all matching files in a directory.

    Args:
        directory: Source directory
        dst_crs: Target CRS
        pattern: Glob pattern for files
        resampling: Resampling method for rasters

    Returns: List of output file paths
    """
    from pathlib import Path

    p = Path(directory)
    output_dir = p / "reprojected"
    output_dir.mkdir(exist_ok=True)

    results = []
    for f in sorted(p.glob(pattern)):
        ext = f.suffix.lower()
        out_path = str(output_dir / f.name)

        raster_exts = {".tif", ".tiff", ".img"}
        vector_exts = {".shp", ".geojson", ".gpkg"}

        if ext in raster_exts:
            reproject_raster(str(f), dst_crs, out_path, resampling)
            results.append(out_path)
        elif ext in vector_exts:
            reproject_vector(str(f), dst_crs, out_path)
            results.append(out_path)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CRS utilities")
    sub = parser.add_subparsers(dest="command")

    # detect
    p_detect = sub.add_parser("detect", help="Detect CRS of a file")
    p_detect.add_argument("--input", required=True)

    # reproject raster
    p_rr = sub.add_parser("reproject-raster", help="Reproject a raster")
    p_rr.add_argument("--input", required=True)
    p_rr.add_argument("--target-crs", required=True)
    p_rr.add_argument("--output", required=True)
    p_rr.add_argument("--resampling", default="bilinear")

    # reproject vector
    p_rv = sub.add_parser("reproject-vector", help="Reproject a vector")
    p_rv.add_argument("--input", required=True)
    p_rv.add_argument("--target-crs", required=True)
    p_rv.add_argument("--output", required=True)

    args = parser.parse_args()

    import json

    if args.command == "detect":
        result = detect_crs(args.input)
        print(json.dumps(result, indent=2))
    elif args.command == "reproject-raster":
        out = reproject_raster(args.input, args.target_crs, args.output, args.resampling)
        print(f"Saved: {out}")
    elif args.command == "reproject-vector":
        out = reproject_vector(args.input, args.target_crs, args.output)
        print(f"Saved: {out}")
    else:
        parser.print_help()
