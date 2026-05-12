# CRS and Projections Reference

## Common CRS Codes

| CRS | EPSG | Use case |
|---|---|---|
| WGS 84 (lon/lat) | 4326 | Global data, GPS, GeoJSON spec |
| CGCS 2000 | 4490 | Chinese national standard geodetic CRS |
| WGS 84 / UTM zones | 326xx (N) / 327xx (S) | Metric projection, zone-specific |
| Albers Equal Area | ESRI:102025 or custom | Area-preserving analysis for China |
| Lambert Conformal Conic | custom | Weather/climate data |
| Beijing 1954 | 214xx | Legacy Chinese data |
| Xian 1980 | 23xx | Legacy Chinese data |

## CRS Detection

```python
import rasterio
import geopandas as gpd

# Raster
with rasterio.open("data.tif") as src:
    crs = src.crs
    epsg = crs.to_epsg()  # may return None if not EPSG-defined

# Vector
gdf = gpd.read_file("data.shp")
crs = gdf.crs
epsg = gdf.crs.to_epsg()
```

If `to_epsg()` returns `None`, the CRS is likely defined by a proj4 string rather than
an EPSG code. Use `crs.to_proj4()` to inspect.

## CRS Transformation

### Raster reprojection

```python
from rasterio.warp import calculate_default_transform, reproject, Resampling

dst_crs = "EPSG:32645"
with rasterio.open("input.tif") as src:
    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds
    )
    kwargs = src.meta.copy()
    kwargs.update({"crs": dst_crs, "transform": transform, "width": width, "height": height})
    with rasterio.open("output.tif", "w", **kwargs) as dst:
        for i in range(1, src.count + 1):
            reproject(
                source=rasterio.band(src, i),
                destination=rasterio.band(dst, i),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.bilinear
            )
```

### Vector reprojection

```python
gdf = gpd.read_file("input.shp")
gdf_projected = gdf.to_crs("EPSG:32645")
gdf_projected.to_file("output.shp")
```

### Point transformation

```python
from pyproj import Transformer

transformer = Transformer.from_crs("EPSG:4326", "EPSG:32645", always_xy=True)
x, y = transformer.transform(lon, lat)
```

## Albers Equal Area for China

A commonly used projection for China-wide analysis:

```python
from pyproj import CRS

albers_china = CRS.from_proj4(
    "+proj=aea +lat_1=25 +lat_2=47 +lat_0=36 +lon_0=105 "
    "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)
```

Parameters: standard parallels at 25N and 47N, central meridian at 105E, origin at 36N.

## Chinese Geodetic Systems

| System | EPSG | Notes |
|---|---|---|
| CGCS 2000 | 4490 | Current national standard. Nearly identical to WGS 84 for most applications. |
| Beijing 1954 | 214xx (zone-dependent) | Legacy. Uses Krassovsky ellipsoid. |
| Xian 1980 | 23xx (zone-dependent) | Legacy. Uses IAG75 ellipsoid. |

CGCS 2000 and WGS 84 differ by <1mm at the ellipsoid level. For most GIS work, they are
interchangeable. However, if the data has been processed through a Chinese geodetic adjustment,
use the declared CRS.

## Common Pitfalls

1. **Axis order**: Some CRS definitions use (lat, lon) instead of (lon, lat). Always use
   `always_xy=True` in pyproj to enforce (x, y) = (lon, lat) order.

2. **Proj4 string deprecation**: Many Chinese datasets store CRS as proj4 strings. These may
   use deprecated datum names (e.g., `+datum=beijing54`). Convert to EPSG or WKT where possible.

3. **Datum shift**: Transforming between Beijing 54 / Xian 80 and WGS 84 / CGCS 2000 requires
   a datum shift. The default transformation may have 10-100m误差. For high-precision work,
   use a grid-based transformation if available.

4. **Missing CRS metadata**: Some Chinese datasets have no CRS information. Infer from:
   - Coordinate range: lon/lat if values are in [-180, 180] / [-90, 90]
   - File naming: `_wgs84`, `_albers`, `_utm45n`
   - Data source documentation
