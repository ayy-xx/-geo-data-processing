# Geo Data Processing Skill

A comprehensive geographic data processing and analysis skill for GIS professionals.

## When to Use

- Spatial statistics and interpolation (Kriging, IDW, variogram)
- Overlay, buffer, clip, mask, merge operations
- Remote sensing processing (NDVI, classification, change detection)
- Hot/cold spot analysis (Getis-Ord Gi*)
- Moran's I analysis (global and local, LISA)
- Trend analysis (Mann-Kendall, Sen's slope, Pettitt)
- CRS transformation and resolution alignment

## When NOT to Use

- Simple CSV/chart plotting (use standard tools)
- 3D visualization or VR/AR
- Database management (PostGIS setup)
- Real-time streaming data

## File Structure

```
geo-data-processing/
├── SKILL.md                          # Entry point and workflow
├── README.md                         # This file
├── evals/
│   └── evals.json                    # Test cases
├── references/
│   ├── library-selection.md          # Library selection guide
│   ├── crs-and-projections.md        # CRS handling
│   ├── data-io.md                    # Data read/write
│   ├── spatial-statistics.md         # Kriging, IDW, variogram
│   ├── overlay-and-buffer.md         # Overlay, buffer, clip, mask, merge
│   ├── remote-sensing.md             # NDVI, classification, change detection
│   ├── hotspot-morans.md             # Gi*, Moran's I, LISA
│   ├── trend-analysis.md             # Mann-Kendall, Sen's slope, Pettitt
│   ├── chinese-author-alignment.md   # Chinese-English terminology
│   └── qa-checklist.md               # Quality assurance checklist
└── scripts/
    ├── geo_data_io.py                # Data inspection
    ├── spatial_stats.py              # Spatial statistics
    ├── raster_ops.py                 # Raster operations
    ├── vector_ops.py                 # Vector operations
    ├── hotspot_analysis.py           # Hot spot analysis
    ├── trend_analysis.py             # Trend analysis
    └── crs_utils.py                  # CRS utilities
```

## Supported Data Formats

| Format | Type | Library |
|---|---|---|
| GeoTIFF | Raster | rasterio |
| NetCDF | Raster | xarray + rioxarray |
| HDF4/HDF5 | Raster | GDAL / h5py |
| GRIB | Raster | cfgrib |
| Shapefile | Vector | geopandas |
| GeoJSON | Vector | geopandas |
| GeoPackage | Vector | geopandas |
| LAS/LAZ | Point cloud | laspy |
| CSV with coordinates | Tabular | pandas + shapely |

## Quick Start

Example: Calculate NDVI and run trend analysis

```python
# 1. Calculate NDVI from NIR and Red bands
from scripts.raster_ops import calculate_index
ndvi_path = calculate_index({"nir": "nir.tif", "red": "red.tif"}, "NDVI", "ndvi.tif")

# 2. Run pixel-wise Mann-Kendall trend on time series
from scripts.trend_analysis import pixel_trend, save_trend_rasters
from pathlib import Path
files = sorted(Path("ndvi_series/").glob("*.tif"))
trend, pvalue, slope, meta = pixel_trend([str(f) for f in files])
save_trend_rasters(trend, pvalue, slope, meta, "output/")
```

## Reference Map

| File | Purpose |
|---|---|
| library-selection.md | Choose between rasterio/GDAL, geopandas/fiona, pysal/scipy |
| crs-and-projections.md | CRS detection, transformation, Chinese geodetic systems |
| data-io.md | Read/write GeoTIFF, NetCDF, HDF, Shapefile, GeoJSON |
| spatial-statistics.md | Kriging, IDW, variogram modeling, cross-validation |
| overlay-and-buffer.md | Spatial overlay, buffer, clip, mask, merge, resolution alignment |
| remote-sensing.md | NDVI, band math, classification, change detection |
| hotspot-morans.md | Getis-Ord Gi*, Moran's I, LISA clusters |
| trend-analysis.md | Mann-Kendall, Sen's slope, Pettitt, seasonal trends |
| chinese-author-alignment.md | Chinese-English GIS terminology mapping |
| qa-checklist.md | Pre-delivery quality assurance checklist |
