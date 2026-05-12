"""Trend analysis: Mann-Kendall, Sen's slope, Pettitt test, pixel-wise trends."""

import numpy as np


def mann_kendall(series):
    """Mann-Kendall trend test.

    Args:
        series: 1D array-like of time series values

    Returns: dict with trend, h, p, z, tau, s, slope, intercept
    """
    import pymannkendall as mk

    result = mk.original_test(series)
    return {
        "trend": result.trend,
        "h": bool(result.h),
        "p": float(result.p),
        "z": float(result.z),
        "tau": float(result.Tau),
        "s": float(result.s),
        "slope": float(result.slope),
        "intercept": float(result.intercept),
    }


def sens_slope(series):
    """Sen's slope estimator with confidence interval.

    Args:
        series: 1D array-like

    Returns: dict with slope, intercept, ci_low, ci_high
    """
    from scipy.stats import theilslopes

    slope, intercept, ci_low, ci_high = theilslopes(series, alpha=0.95)
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
    }


def seasonal_mann_kendall(series, period=12):
    """Seasonal Mann-Kendall test.

    Args:
        series: 1D array of seasonal data (e.g., 12 months per year)
        period: number of seasons per year

    Returns: dict with trend, h, p, z, tau, slope
    """
    import pymannkendall as mk

    result = mk.seasonal_test(series, period=period)
    return {
        "trend": result.trend,
        "h": bool(result.h),
        "p": float(result.p),
        "z": float(result.z),
        "tau": float(result.Tau),
        "slope": float(result.slope),
    }


def pettitt_test(series):
    """Pettitt change point test.

    Args:
        series: 1D array-like

    Returns: dict with trend, h, p, cp, U, mu1, mu2
    """
    import pymannkendall as mk

    result = mk.pettitt_test(series)
    return {
        "trend": result.trend,
        "h": bool(result.h),
        "p": float(result.p),
        "cp": int(result.cp),
        "U": float(result.U),
        "mu1": float(result.mu1),
        "mu2": float(result.mu2),
    }


def pixel_trend(raster_paths, method="mann_kendall", period=None):
    """Compute trend for each pixel across a time series of rasters.

    Args:
        raster_paths: list of raster file paths (ordered by time)
        method: "mann_kendall", "sens_slope", or "seasonal_mann_kendall"
        period: period for seasonal test (e.g., 12 for monthly data)

    Returns: tuple of (trend_array, pvalue_array, slope_array, meta_dict)
    """
    import rasterio

    with rasterio.open(raster_paths[0]) as src:
        meta = src.meta.copy()
        height, width = src.shape

    n = len(raster_paths)
    stack = np.zeros((n, height, width), dtype=np.float32)

    for i, path in enumerate(raster_paths):
        with rasterio.open(path) as src:
            stack[i] = src.read(1)

    trend = np.zeros((height, width), dtype=np.float32)
    pvalue = np.ones((height, width), dtype=np.float32)
    slope = np.zeros((height, width), dtype=np.float32)

    for row in range(height):
        for col in range(width):
            series = stack[:, row, col]
            if np.all(np.isnan(series)) or np.nanstd(series) == 0:
                continue

            try:
                if method == "mann_kendall":
                    result = mann_kendall(series)
                elif method == "seasonal_mann_kendall" and period:
                    result = seasonal_mann_kendall(series, period)
                else:
                    result = mann_kendall(series)

                trend_map = {"increasing": 1, "decreasing": -1, "no trend": 0}
                trend[row, col] = trend_map.get(result["trend"], 0)
                pvalue[row, col] = result["p"]
                slope[row, col] = result["slope"]
            except Exception:
                continue

    return trend, pvalue, slope, meta


def save_trend_rasters(trend, pvalue, slope, meta, output_dir):
    """Save pixel-wise trend results as GeoTIFF files."""
    import rasterio
    from pathlib import Path

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    meta.update(dtype="float32", nodata=-9999, count=1)

    for name, data in [("trend", trend), ("pvalue", pvalue), ("slope", slope)]:
        path = Path(output_dir) / f"{name}.tif"
        with rasterio.open(path, "w", **meta) as dst:
            dst.write(data, 1)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Trend analysis tools")
    sub = parser.add_subparsers(dest="command")

    # Single series
    p_mk = sub.add_parser("mann-kendall", help="Mann-Kendall test on CSV")
    p_mk.add_argument("--input", required=True, help="CSV with 'value' column")
    p_mk.add_argument("--output", help="Save results to JSON")

    # Pixel-wise
    p_pixel = sub.add_parser("pixel", help="Pixel-wise trend on raster stack")
    p_pixel.add_argument("--input-dir", required=True)
    p_pixel.add_argument("--pattern", default="*.tif")
    p_pixel.add_argument("--method", default="mann_kendall")
    p_pixel.add_argument("--period", type=int)
    p_pixel.add_argument("--output-dir", required=True)

    args = parser.parse_args()

    if args.command == "mann-kendall":
        import pandas as pd
        df = pd.read_csv(args.input)
        series = df["value"].values
        result = mann_kendall(series)
        print(json.dumps(result, indent=2))
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)

    elif args.command == "pixel":
        from pathlib import Path
        files = sorted(Path(args.input_dir).glob(args.pattern))
        files = [str(f) for f in files]
        print(f"Processing {len(files)} rasters...")
        trend, pvalue, slope, meta = pixel_trend(files, args.method, args.period)
        save_trend_rasters(trend, pvalue, slope, meta, args.output_dir)
        print(f"Saved trend rasters to {args.output_dir}")
