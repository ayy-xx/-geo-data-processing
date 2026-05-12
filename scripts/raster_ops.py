"""Raster operations: NDVI, reclassification, change detection, zonal statistics, mask, clip, merge."""

import numpy as np
from pathlib import Path


def calculate_index(band_paths: dict, index: str = "NDVI", output_path: str = None) -> str:
    """Calculate a spectral index from band files.

    Args:
        band_paths: dict mapping band names to file paths, e.g. {"nir": "nir.tif", "red": "red.tif"}
        index: index name (NDVI, NDWI, EVI, SAVI, NDBI)
        output_path: output file path

    Returns: output file path
    """
    import rasterio

    formulas = {
        "NDVI": lambda bands: (bands["nir"] - bands["red"]) / (bands["nir"] + bands["red"] + 1e-10),
        "NDWI": lambda bands: (bands["green"] - bands["nir"]) / (bands["green"] + bands["nir"] + 1e-10),
        "EVI": lambda bands: 2.5 * (bands["nir"] - bands["red"]) / (
            bands["nir"] + 6 * bands["red"] - 7.5 * bands["blue"] + 1),
        "SAVI": lambda bands: ((bands["nir"] - bands["red"]) / (bands["nir"] + bands["red"] + 0.5)) * 1.5,
        "NDBI": lambda bands: (bands["swir"] - bands["nir"]) / (bands["swir"] + bands["nir"] + 1e-10),
    }

    if index not in formulas:
        raise ValueError(f"Unsupported index: {index}. Choose from {list(formulas.keys())}")

    bands = {}
    meta = None
    for name, path in band_paths.items():
        with rasterio.open(path) as src:
            bands[name] = src.read(1).astype(np.float32)
            if meta is None:
                meta = src.meta.copy()

    result = formulas[index](bands)

    # Clip to valid range
    if index == "NDVI":
        result = np.clip(result, -1, 1)

    if output_path is None:
        output_path = f"{index.lower()}.tif"

    meta.update(dtype="float32", nodata=-9999, count=1)
    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(result, 1)

    return output_path


def reclassify(raster_path: str, rules: dict, output_path: str = None) -> str:
    """Reclassify raster values based on rules.

    Args:
        raster_path: input raster
        rules: dict mapping old_value -> new_value, or list of (min, max, new_value) tuples
        output_path: output file path

    Returns: output file path
    """
    import rasterio

    with rasterio.open(raster_path) as src:
        data = src.read(1)
        meta = src.meta.copy()
        nodata = src.nodata

    if isinstance(rules, dict):
        result = data.copy()
        for old_val, new_val in rules.items():
            result[data == old_val] = new_val
    elif isinstance(rules, list):
        result = np.full_like(data, nodata if nodata else -9999, dtype=np.int32)
        for low, high, new_val in rules:
            mask = (data >= low) & (data <= high)
            result[mask] = new_val

    if output_path is None:
        output_path = str(Path(raster_path).stem) + "_reclass.tif"

    meta.update(dtype=result.dtype, nodata=nodata)
    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(result, 1)

    return output_path


def change_detection(before_path: str, after_path: str, method: str = "differencing",
                     output_path: str = None) -> str:
    """Detect changes between two rasters.

    Args:
        before_path: earlier raster
        after_path: later raster
        method: "differencing" or "ratio" or "classification"
        output_path: output file path

    Returns: output file path
    """
    import rasterio

    with rasterio.open(before_path) as src:
        before = src.read(1).astype(np.float32)
        meta = src.meta.copy()

    with rasterio.open(after_path) as src:
        after = src.read(1).astype(np.float32)

    if method == "differencing":
        result = after - before
    elif method == "ratio":
        result = after / (before + 1e-10)
    elif method == "classification":
        result = np.zeros_like(before, dtype=np.int32)
        result[(before != after) & (before > 0) & (after > 0)] = 1
    else:
        raise ValueError(f"Unknown method: {method}")

    if output_path is None:
        output_path = "change_detection.tif"

    meta.update(dtype=result.dtype, nodata=-9999)
    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(result, 1)

    return output_path


def zonal_stats(zones_path: str, values_path: str, stat: str = "mean") -> dict:
    """Compute zonal statistics.

    Args:
        zones_path: raster with zone IDs
        values_path: raster with values to summarize
        stat: statistic to compute (mean, sum, min, max, std, count)

    Returns: dict mapping zone_id -> statistic value
    """
    import rasterio

    with rasterio.open(zones_path) as src:
        zones = src.read(1)
    with rasterio.open(values_path) as src:
        values = src.read(1).astype(np.float64)

    unique_zones = np.unique(zones)
    unique_zones = unique_zones[~np.isnan(unique_zones)]

    stat_func = {
        "mean": np.nanmean,
        "sum": np.nansum,
        "min": np.nanmin,
        "max": np.nanmax,
        "std": np.nanstd,
        "count": lambda x: np.count_nonzero(~np.isnan(x)),
    }[stat]

    results = {}
    for zone in unique_zones:
        mask = zones == zone
        if np.any(mask):
            results[int(zone)] = float(stat_func(values[mask]))

    return results


def align_rasters(reference_path: str, input_paths: list, output_dir: str = None,
                  resampling: str = "bilinear") -> list:
    """Align multiple rasters to a reference grid.

    Args:
        reference_path: reference raster for resolution/extent/CRS
        input_paths: list of rasters to align
        output_dir: output directory (default: same as input)
        resampling: "bilinear" (continuous) or "nearest" (categorical)

    Returns: list of output file paths
    """
    import rasterio
    from rasterio.warp import reproject, Resampling

    resampling_map = {
        "bilinear": Resampling.bilinear,
        "nearest": Resampling.nearest,
        "cubic": Resampling.cubic,
    }
    resamp = resampling_map.get(resampling, Resampling.bilinear)

    with rasterio.open(reference_path) as ref:
        ref_meta = ref.meta.copy()
        ref_transform = ref.transform
        ref_crs = ref.crs
        ref_width = ref.width
        ref_height = ref.height

    if output_dir is None:
        output_dir = str(Path(input_paths[0]).parent / "aligned")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    results = []
    for ip in input_paths:
        out_path = str(Path(output_dir) / Path(ip).name)
        with rasterio.open(ip) as src:
            data = src.read(1).astype(np.float32)
            out = np.empty((ref_height, ref_width), dtype=data.dtype)
            reproject(
                source=data,
                destination=out,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=ref_transform,
                dst_crs=ref_crs,
                resampling=resamp,
            )
            out_meta = ref_meta.copy()
            out_meta.update(dtype=out.dtype)
            with rasterio.open(out_path, "w", **out_meta) as dst:
                dst.write(out, 1)
        results.append(out_path)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Raster operations")
    sub = parser.add_subparsers(dest="command")

    # NDVI
    p_ndvi = sub.add_parser("ndvi", help="Calculate NDVI")
    p_ndvi.add_argument("--nir", required=True)
    p_ndvi.add_argument("--red", required=True)
    p_ndvi.add_argument("--output", default="ndvi.tif")

    # change detection
    p_cd = sub.add_parser("change", help="Change detection")
    p_cd.add_argument("--before", required=True)
    p_cd.add_argument("--after", required=True)
    p_cd.add_argument("--method", default="differencing")
    p_cd.add_argument("--output", default="change.tif")

    args = parser.parse_args()

    if args.command == "ndvi":
        out = calculate_index({"nir": args.nir, "red": args.red}, "NDVI", args.output)
        print(f"Saved: {out}")
    elif args.command == "change":
        out = change_detection(args.before, args.after, args.method, args.output)
        print(f"Saved: {out}")
