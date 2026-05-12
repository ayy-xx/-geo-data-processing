# Trend Analysis Reference

## Mann-Kendall Test

Non-parametric test for monotonic trend in time series. No assumption of normality.

```python
import pymannkendall as mk

# Standard Mann-Kendall
result = mk.original_test(series)
print(result)
# MannKendall(trend='increasing', h=True, p=0.001, z=3.21, Tau=0.45,
#             s=120.0, var_s=1340.0, slope=0.012, intercept=0.5)
```

Output fields:
- `trend`: "increasing", "decreasing", or "no trend"
- `h`: True if trend is significant (p < alpha)
- `p`: p-value
- `z`: standard normal test statistic
- `Tau`: Kendall's Tau (strength)
- `slope`: Sen's slope (rate of change per unit time)
- `intercept`: intercept of the trend line

## Seasonal Mann-Kendall

For data with seasonal component (e.g., monthly data over years).

```python
# Reshape to (years, seasons)
import numpy as np
seasonal_data = series.reshape(-1, 12)  # 12 months
result = mk.seasonal_test(seasonal_data)
```

Or with pymannkendall directly:
```python
result = mk.seasonal_test(series, period=12)
```

## Sen's Slope

Median of all pairwise slopes. Robust to outliers.

```python
# Via pymannkendall (included in original_test result)
result = mk.original_test(series)
slope = result.slope      # change per time step
intercept = result.intercept

# Via scipy
from scipy.stats import theilslopes
slope, intercept, low, high = theilslopes(series, alpha=0.95)
```

## Pettitt Test

Non-parametric test for change point detection.

```python
result = mk.pettitt_test(series)
print(result)
# Pettitt_Test(trend='step', h=True, p=0.02, cp=45, U=234.0, mu1=0.5, mu2=0.8)
```

Output:
- `cp`: change point index (position in series)
- `mu1`, `mu2`: mean before and after change point
- `p`: p-value

## Pre-whitening

Remove autocorrelation before trend testing. Important when data has significant
lag-1 autocorrelation.

```python
import numpy as np

def pre_whiten(series):
    """Remove AR(1) component from series."""
    n = len(series)
    # Calculate lag-1 autocorrelation
    acf1 = np.corrcoef(series[:-1], series[1:])[0, 1]
    # Pre-whiten
    pw = np.zeros(n)
    pw[0] = series[0]
    for i in range(1, n):
        pw[i] = series[i] - acf1 * series[i - 1]
    return pw

# Usage
pw_series = pre_whiten(series)
result = mk.original_test(pw_series)
```

## Pixel-wise Trend (Raster Time Series)

Apply trend test to each pixel across a stack of rasters.

```python
import rasterio
import numpy as np
from pathlib import Path
import pymannkendall as mk

def pixel_trend(raster_dir, pattern="*.tif", method="mann_kendall"):
    """Compute trend for each pixel across time-series rasters.

    Args:
        raster_dir: directory containing time-series rasters
        pattern: file pattern
        method: "mann_kendall" or "sens_slope"

    Returns: tuple of (trend_raster, pvalue_raster, slope_raster)
    """
    files = sorted(Path(raster_dir).glob(pattern))

    # Read all rasters into a 3D array (time, height, width)
    with rasterio.open(files[0]) as src:
        meta = src.meta.copy()
        height, width = src.shape

    stack = np.zeros((len(files), height, width), dtype=np.float32)
    for i, f in enumerate(files):
        with rasterio.open(f) as src:
            stack[i] = src.read(1)

    # Apply trend test to each pixel
    trend = np.zeros((height, width), dtype=np.float32)
    pvalue = np.ones((height, width), dtype=np.float32)
    slope = np.zeros((height, width), dtype=np.float32)

    for row in range(height):
        for col in range(width):
            series = stack[:, row, col]
            if np.all(np.isnan(series)) or np.std(series) == 0:
                continue
            result = mk.original_test(series)
            trend[row, col] = {"increasing": 1, "decreasing": -1, "no trend": 0}[result.trend]
            pvalue[row, col] = result.p
            slope[row, col] = result.slope

    return trend, pvalue, slope, meta


def save_trend_rasters(trend, pvalue, slope, meta, output_dir):
    """Save trend results as GeoTIFF files."""
    import rasterio
    from pathlib import Path

    Path(output_dir).mkdir(exist_ok=True)
    meta.update(dtype="float32", nodata=-9999, count=1)

    for name, data in [("trend", trend), ("pvalue", pvalue), ("slope", slope)]:
        path = Path(output_dir) / f"{name}.tif"
        with rasterio.open(path, "w", **meta) as dst:
            dst.write(data, 1)
```

## Interpretation Guide

| Metric | Meaning | Typical threshold |
|---|---|---|
| p < 0.05 | Statistically significant trend | Standard significance level |
| p < 0.01 | Highly significant | Stricter threshold |
| slope > 0 | Increasing trend | Rate of change per time step |
| slope < 0 | Decreasing trend | Rate of change per time step |
| Tau close to ±1 | Strong monotonic trend | Higher = stronger |
| Change point at index k | Structural shift at time k | Compare mu1 vs mu2 |

## Common Pitfalls

1. **Autocorrelation**: Serial correlation inflates significance. Always check and pre-whiten
   if lag-1 autocorrelation > 0.2.

2. **Sen's slope vs linear regression**: Sen's slope is median-based, robust to outliers.
   Linear regression assumes normality and is sensitive to extremes.

3. **Seasonal data**: Use seasonal Mann-Kendall for monthly/quarterly data. Standard
   Mann-Kendall on seasonal data can detect spurious trends.

4. **Missing values**: pymannkendall handles NaN by default. But if >20% of values are
   missing, results may be unreliable.

5. **Non-monotonic trends**: Mann-Kendall only detects monotonic trends. For U-shaped or
   other non-monotonic patterns, consider segmented regression or wavelet analysis.
