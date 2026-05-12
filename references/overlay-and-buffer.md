# Overlay and Buffer Reference

## Spatial Overlay (geopandas)

```python
import geopandas as gpd

a = gpd.read_file("a.shp")
b = gpd.read_file("b.shp")

# Intersection: only overlapping areas
result = gpd.overlay(a, b, how="intersection")

# Union: all areas from both
result = gpd.overlay(a, b, how="union")

# Symmetric difference: non-overlapping areas
result = gpd.overlay(a, b, how="symmetric_difference")

# Difference: areas in A not in B
result = gpd.overlay(a, b, how="difference")

# Identity: A with B's attributes where they overlap
result = gpd.overlay(a, b, how="identity")
```

## Buffer

```python
# Fixed distance buffer (in CRS units)
gdf_buffered = gdf.copy()
gdf_buffered["geometry"] = gdf.buffer(1000)  # 1000 meters

# Variable buffer based on attribute
gdf_buffered["geometry"] = gdf.apply(
    lambda row: row.geometry.buffer(row["distance_m"]), axis=1
)

# Dissolve overlapping buffers
gdf_dissolved = gdf_buffered.dissolve()
```

## Clip

### Vector clip by vector

```python
gdf_clipped = gpd.clip(gdf, mask_gdf)
```

### Raster clip by vector

```python
import rasterio
from rasterio.mask import mask

with rasterio.open("raster.tif") as src:
    out_image, out_transform = mask(src, mask_gdf.geometry, crop=True)
    out_meta = src.meta.copy()
    out_meta.update({
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform,
    })

with rasterio.open("clipped.tif", "w", **out_meta) as dst:
    dst.write(out_image)
```

### Raster clip by bounding box

```python
from rasterio.windows import from_bounds

with rasterio.open("raster.tif") as src:
    window = from_bounds(minx, miny, maxx, maxy, src.transform)
    data = src.read(1, window=window)
```

## Mask (Raster Masking)

Masking retains values inside the mask polygon and sets outside values to nodata.

```python
import rasterio
from rasterio.mask import mask

with rasterio.open("raster.tif") as src:
    masked, transform = mask(
        src,
        mask_gdf.geometry,
        crop=True,           # crop to mask extent
        filled=True,         # fill outside with nodata
        nodata=src.nodata or -9999,
    )
    meta = src.meta.copy()
    meta.update({"height": masked.shape[1], "width": masked.shape[2], "transform": transform})

with rasterio.open("masked.tif", "w", **meta) as dst:
    dst.write(masked)
```

## Merge (Mosaic)

### Raster merge

```python
from rasterio.merge import merge
import rasterio
from pathlib import Path

files = sorted(Path("tiles/").glob("*.tif"))
srcs = [rasterio.open(f) for f in files]
mosaic, transform = merge(srcs)
meta = srcs[0].meta.copy()
meta.update({"height": mosaic.shape[1], "width": mosaic.shape[2], "transform": transform})

with rasterio.open("mosaic.tif", "w", **meta) as dst:
    dst.write(mosaic)

for src in srcs:
    src.close()
```

### Vector merge / dissolve

```python
# Merge multiple GeoDataFrames
gdf_merged = gpd.GeoDataFrame(pd.concat([gdf1, gdf2, gdf3], ignore_index=True))

# Dissolve by attribute (merge geometries with same value)
gdf_dissolved = gdf.dissolve(by="province", aggfunc={"area": "sum", "pop": "sum"})
```

## Spatial Join

```python
# Points within polygons
joined = gpd.sjoin(points_gdf, polygons_gdf, predicate="within", how="left")

# Nearest neighbor join
joined = gpd.sjoin_nearest(points_gdf, polygons_gdf, how="left", max_distance=5000)
```

Available predicates: `intersects`, `within`, `contains`, `overlaps`, `crosses`, `touches`.

## Resolution Alignment

When multiple rasters have different resolutions:

```python
import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np

def align_to_reference(reference_path, input_path, output_path, resampling="bilinear"):
    """Resample input raster to match reference resolution and extent."""
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
        ref_bounds = ref.bounds

    with rasterio.open(input_path) as src:
        data = src.read(1)
        out = np.empty((ref_height, ref_width), dtype=ref_meta["dtype"])

        reproject(
            source=data,
            destination=out,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=ref_transform,
            dst_crs=ref_crs,
            resampling=resamp,
        )

        ref_meta.update(dtype=out.dtype)
        with rasterio.open(output_path, "w", **ref_meta) as dst:
            dst.write(out, 1)

    return output_path
```

**Key decision**: Use nearest-neighbor resampling for categorical data (land use classes),
bilinear for continuous data (temperature, elevation).
