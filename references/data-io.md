# Data I/O Reference

## GeoTIFF (rasterio)

```python
import rasterio

# Read
with rasterio.open("data.tif") as src:
    data = src.read(1)  # first band as numpy array
    crs = src.crs
    transform = src.transform
    nodata = src.nodata
    bounds = src.bounds
    meta = src.meta

# Write
meta.update(dtype="float32", count=1, nodata=-9999)
with rasterio.open("output.tif", "w", **meta) as dst:
    dst.write(data, 1)
```

### Multi-band read

```python
with rasterio.open("multiband.tif") as src:
    all_bands = src.read()  # shape: (bands, height, width)
    band_names = [f"band_{i+1}" for i in range(src.count)]
```

### Windowed reading (large rasters)

```python
from rasterio.windows import Window

with rasterio.open("large.tif") as src:
    window = Window(col_off=0, row_off=0, width=1024, height=1024)
    chunk = src.read(1, window=window)
```

## NetCDF (xarray + rioxarray)

```python
import xarray as xr

ds = xr.open_dataset("data.nc")
# Access variables
var = ds["temperature"]
# Convert to raster-ready array with CRS
var.rio.write_crs("EPSG:4326", inplace=True)
var.rio.to_raster("output.tif")
```

### Time-series NetCDF

```python
ds = xr.open_dataset("timeseries.nc", chunks={"time": 12})  # dask-backed
monthly_mean = ds["precip"].groupby("time.month").mean()
```

## HDF4 (MODIS)

```python
from osgeo import gdal

# Open subdataset
ds = gdal.Open("MODIS.hdf")
subdatasets = ds.GetSubDatasets()
# subdatasets[0] = (path, description)
band = gdal.Open(subdatasets[0][0])
data = band.ReadAsArray()
```

For HDF5:
```python
import h5py
with h5py.File("data.h5", "r") as f:
    data = f["/group/dataset"][:]
```

## Shapefile (geopandas)

```python
import geopandas as gpd

gdf = gpd.read_file("data.shp")
# Chinese encoding
gdf = gpd.read_file("data.shp", encoding="gbk")
# Write
gdf.to_file("output.shp", encoding="utf-8")
```

### Attribute table operations

```python
# Filter by attribute
filtered = gdf[gdf["province"] == "新疆"]
# Select columns
subset = gdf[["name", "area", "geometry"]]
# Dissolve by attribute
dissolved = gdf.dissolve(by="province", aggfunc="sum")
```

## GeoJSON

```python
gdf = gpd.read_file("data.geojson")
# GeoJSON spec mandates WGS84 (EPSG:4326)
gdf.to_file("output.geojson", driver="GeoJSON")
```

## LAS/LAZ (point cloud)

```python
import laspy

las = laspy.read("pointcloud.las")
x, y, z = las.x, las.y, las.z
# Filter by classification
ground = las.points[las.classification == 2]
```

## GPS Trajectories

```python
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

df = pd.read_csv("trajectory.csv")  # columns: lon, lat, time
geometry = [Point(xy) for xy in zip(df["lon"], df["lat"])]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
```

## GRIB (meteorological)

```python
import xarray as xr
ds = xr.open_dataset("data.grib", engine="cfgrib")
```

## Station data to GeoDataFrame

```python
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

df = pd.read_csv("stations.csv")  # columns: station_id, lon, lat, value
geometry = [Point(xy) for xy in zip(df["lon"], df["lat"])]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
```
