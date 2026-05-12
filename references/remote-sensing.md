# Remote Sensing Reference

## Spectral Indices

### NDVI (Normalized Difference Vegetation Index)

```
NDVI = (NIR - Red) / (NIR + Red)
```

Range: [-1, 1]. Healthy vegetation > 0.3, bare soil ~0.1, water < 0.

```python
import rasterio
import numpy as np

with rasterio.open("nir.tif") as src:
    nir = src.read(1).astype(np.float32)
    meta = src.meta.copy()
with rasterio.open("red.tif") as src:
    red = src.read(1).astype(np.float32)

ndvi = (nir - red) / (nir + red + 1e-10)
ndvi = np.clip(ndvi, -1, 1)
```

### Other indices

| Index | Formula | Use |
|---|---|---|
| NDWI | (Green - NIR) / (Green + NIR) | Water body detection |
| EVI | 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1) | Enhanced vegetation, less saturation |
| SAVI | ((NIR - Red) / (NIR + Red + 0.5)) * 1.5 | Sparse vegetation |
| NDBI | (SWIR - NIR) / (SWIR + NIR) | Built-up area detection |
| MNDWI | (Green - SWIR) / (Green + SWIR) | Modified water index |

### MODIS scale factors

MODIS reflectance products often use scale_factor=0.0001. Apply before index calculation:

```python
nir = nir_raw * 0.0001
red = red_raw * 0.0001
```

## Classification

### Supervised classification

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
import numpy as np

# Prepare training data: X = [band1, band2, ...], y = class labels
X_train = np.column_stack([band1[train_mask], band2[train_mask], ...])
y_train = labels[train_mask]

# Train
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Predict on full image
X_all = np.column_stack([band1.ravel(), band2.ravel(), ...])
prediction = clf.predict(X_all).reshape(band1.shape)
```

### Unsupervised classification (K-means)

```python
from sklearn.cluster import KMeans

X = np.column_stack([band1.ravel(), band2.ravel(), ...])
kmeans = KMeans(n_clusters=5, random_state=42)
labels = kmeans.fit_predict(X).reshape(band1.shape)
```

### Classification accuracy

```python
from sklearn.metrics import classification_report, confusion_matrix

print(classification_report(y_true, y_pred))
cm = confusion_matrix(y_true, y_pred)
```

## Change Detection

### Image differencing

```python
diff = after_band - before_band
# Threshold to identify significant change
threshold = np.std(diff) * 1.5
change_mask = np.abs(diff) > threshold
```

### Post-classification comparison

```python
# Compare classified maps
changed = (before_class != after_class) & (before_class > 0) & (after_class > 0)

# Transition matrix
import pandas as pd
from_class = before_class[changed]
to_class = after_class[changed]
transition = pd.crosstab(from_class, to_class, margins=True)
```

### Change Vector Analysis (CVA)

```python
# Multi-band change magnitude
diff = after_bands - before_bands  # shape: (bands, h, w)
change_magnitude = np.sqrt(np.sum(diff**2, axis=0))
```

## Image Fusion (Pansharpening)

```python
import rasterio
import numpy as np

with rasterio.open("pan.tif") as src:
    pan = src.read(1).astype(np.float32)
with rasterio.open("multispectral.tif") as src:
    ms = src.read().astype(np.float32)  # shape: (bands, h, w)

# Brovey transform
ms_sum = np.sum(ms, axis=0, keepdims=True)
ms_sum[ms_sum == 0] = 1e-10
fused = ms * (pan / ms_sum)

# Or IHS method (requires resampling MS to Pan resolution first)
```

## Zonal Statistics with Raster

```python
import rasterio
import numpy as np

def zonal_mean(zones_path, values_path):
    with rasterio.open(zones_path) as src:
        zones = src.read(1)
    with rasterio.open(values_path) as src:
        values = src.read(1).astype(np.float64)

    results = {}
    for zone_id in np.unique(zones):
        if np.isnan(zone_id):
            continue
        mask = zones == zone_id
        results[int(zone_id)] = float(np.nanmean(values[mask]))
    return results
```

## Nodata Handling

Always check and handle nodata explicitly:

```python
with rasterio.open("data.tif") as src:
    nodata = src.nodata
    data = src.read(1, masked=True)  # masked array, nodata auto-masked

# Or manual mask
data = src.read(1)
if nodata is not None:
    mask = data == nodata
    data = data.astype(np.float32)
    data[mask] = np.nan
```

## Batch Processing

```python
from pathlib import Path
import rasterio

def batch_ndvi(nir_dir, red_dir, output_dir):
    nir_files = sorted(Path(nir_dir).glob("*.tif"))
    red_files = sorted(Path(red_dir).glob("*.tif"))
    Path(output_dir).mkdir(exist_ok=True)

    for nir_f, red_f in zip(nir_files, red_files):
        with rasterio.open(nir_f) as src:
            nir = src.read(1).astype(np.float32)
            meta = src.meta.copy()
        with rasterio.open(red_f) as src:
            red = src.read(1).astype(np.float32)

        ndvi = (nir - red) / (nir + red + 1e-10)
        meta.update(dtype="float32", nodata=-9999)
        out_path = Path(output_dir) / f"ndvi_{nir_f.stem}.tif"
        with rasterio.open(out_path, "w", **meta) as dst:
            dst.write(ndvi, 1)
```
