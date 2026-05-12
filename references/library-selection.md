# Library Selection Guide

Choose the right Python library for each geospatial operation. Default to the recommended
option unless a specific constraint forces the fallback.

## Raster I/O

| Task | Recommended | When to use fallback |
|---|---|---|
| Read/write GeoTIFF | `rasterio` | — |
| Read HDF4 subdatasets (MODIS) | `GDAL` via `osgeo` | `rasterio` cannot open HDF4 directly |
| Read NetCDF with time dims | `xarray` + `rioxarray` | `netCDF4` for low-level variable access |
| Read GRIB | `cfgrib` + `xarray` | `pygrib` for GRIB1 |
| Large raster (>2GB) | `rasterio` with windowed reading | `dask.array` for out-of-core computation |

```bash
pip install rasterio rioxarray xarray netCDF4 h5py pyhdf cfgrib
```

## Vector I/O

| Task | Recommended | When to use fallback |
|---|---|---|
| Read/write Shapefile | `geopandas` | `fiona` for pure I/O without DataFrame |
| Read GeoJSON | `geopandas` | `json` + `shapely` for simple parsing |
| Geometry manipulation | `shapely` | `geopandas` for batch operations |
| Spatial join | `geopandas.sjoin` | — |
| Read GeoPackage | `geopandas` | `fiona` |

```bash
pip install geopandas shapely fiona pyproj
```

## Spatial Statistics

| Task | Recommended | When to use fallback |
|---|---|---|
| Moran's I (global/local) | `pysal/esda` | Manual implementation with `scipy` |
| Getis-Ord Gi* | `pysal/esda` | Manual implementation with `scipy` |
| Spatial weights matrix | `pysal/libpysal` | Manual distance matrix with `scipy.spatial` |
| Kriging | `pykrige` | `gstools` for advanced variogram models |
| IDW | `scipy.interpolate.RBF` | Manual implementation |
| Variogram fitting | `pykrige` or `gstools` | `scipy.optimize.curve_fit` |

```bash
pip install pysal esda libpysal mapclassify pykrige gstools
```

Minimal pysal install (if full pysal has conflicts):
```bash
pip install esda libpysal mapclassify splot
```

## Remote Sensing

| Task | Recommended | When to use fallback |
|---|---|---|
| NDVI / band math | `rasterio` + `numpy` | — |
| Classification (RF, SVM) | `scikit-learn` | — |
| Change detection | `rasterio` + `numpy` | — |
| Atmospheric correction | `py6s` | Manual DOS correction |
| Pansharpening | `rasterio` + `numpy` | — |

```bash
pip install scikit-learn
```

## Trend Analysis

| Task | Recommended | When to use fallback |
|---|---|---|
| Mann-Kendall test | `pymannkendall` | `scipy.stats.kendalltau` + manual S statistic |
| Sen's slope | `pymannkendall` | `scipy.stats.theilslopes` |
| Pettitt test | `pymannkendall` | Manual implementation |
| Seasonal Kendall | `pymannkendall` | Manual implementation with monthly grouping |

```bash
pip install pymannkendall
```

## DEM / Hydrology

| Task | Recommended | When to use fallback |
|---|---|---|
| Fill sinks | `richdem` | `pysheds` |
| Flow direction/accumulation | `richdem` | `pysheds` |
| Slope/aspect | `rasterio` + `numpy` | `richdem` |
| Watershed delineation | `pysheds` | `whitebox` |

```bash
pip install richdem pysheds
```

## CRS and Projections

| Task | Recommended | Notes |
|---|---|---|
| CRS detection | `rasterio` / `geopandas` | Both use `pyproj` under the hood |
| CRS transformation | `pyproj` | Always use `Transformer.from_crs()` |
| EPSG lookup | `pyproj` | `pyproj.CRS.from_epsg()` |

```bash
pip install pyproj
```

## Memory Management

For rasters larger than available RAM:

| Strategy | Library | Use case |
|---|---|---|
| Windowed reading | `rasterio.windows` | Process tiles sequentially |
| Dask arrays | `dask.array` | Parallel chunk-based computation |
| Chunked NetCDF | `xarray` with `chunks=` | Time-series of large rasters |

## Full environment setup

```bash
# Core geospatial stack
pip install rasterio geopandas shapely fiona pyproj rioxarray xarray

# Spatial statistics
pip install esda libpysal mapclassify pykrige gstools pymannkendall

# Scientific computing
pip install numpy scipy scikit-learn pandas

# Optional: large data support
pip install dask netCDF4 h5py

# Optional: DEM/hydrology
pip install richdem pysheds
```
