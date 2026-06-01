---
name: geo-data-processing
description: >-
  Comprehensive geographic data processing and analysis for GIS professionals. Supports raster
  (GeoTIFF, NetCDF, HDF), vector (Shapefile, GeoJSON), point clouds, GPS trajectories, and
  meteorological data. Core capabilities: spatial statistics and interpolation (Kriging, IDW,
  variogram modeling), overlay and buffer analysis (spatial overlay, buffer, clip, mask, merge,
  dissolve), remote sensing image processing (NDVI, classification, change detection, image fusion),
  hot/cold spot analysis (Getis-Ord Gi*), Moran's I analysis (global and local, LISA), and trend
  analysis (Mann-Kendall, Sen's slope, Pettitt test). Handles CRS transformation, resolution
  alignment, nodata management, and multi-format I/O. Use when the user asks about spatial analysis,
  GIS processing, remote sensing, geostatistics, 地理数据处理, 空间统计, 遥感图像处理, 热点分析,
  莫兰指数, 趋势分析, 克里金插值, 叠加分析, 缓冲区分析, 掩膜提取, 裁剪, 栅格合并, NDVI计算,
  土地利用变化, 坐标系转换, 分辨率对齐, or any geospatial data workflow.
---

# Geo Data Processing

Turn geospatial data and analysis requests into reproducible, publication-ready Python workflows.
This skill does not invent data, projections, or statistical results — it inspects what you have,
plans the pipeline, and generates code you can rerun.

## Chinese-user operating mode

When the user writes in Chinese or uses Chinese GIS terminology:

- Accept Chinese input naturally. Produce Python code with English variable names and function names.
- Preserve Chinese explanations in comments and bilingual output sections.
- For Chinese-facing projects, write code with English variables/functions and add a Chinese comment on every executable line unless the user relaxes this requirement.
- Use Chinese names for output tables, figure titles, legends, field names, folders, and method documents when the user is writing a Chinese thesis/report.
- After generating or modifying code, run a code review pass before treating the work as complete. Check paths, units, nodata handling, masks, resampling choices, aggregation scale, and output names.
- Map Chinese GIS terms to English library concepts using the table below. For the full mapping,
  open `references/chinese-author-alignment.md`.

| 中文 | English | Library concept |
|---|---|---|
| 投影转换 | CRS reprojection | `rasterio.warp.reproject`, `gdf.to_crs()` |
| 叠加分析 | Spatial overlay | `gpd.overlay()` |
| 缓冲区 | Buffer | `gdf.buffer()` |
| 插值 | Interpolation | `pykrige`, `scipy.interpolate` |
| 重采样 | Resampling | `rasterio.warp.reproject` with `Resampling` |
| 掩膜 | Mask | `rasterio.mask.mask()` |
| 像元 | Pixel / Cell | raster grid unit |
| 矢量 | Vector | point/line/polygon features |
| 栅格 | Raster | gridded data |
| 属性表 | Attribute table | `GeoDataFrame` columns |
| 拓扑 | Topology | geometry spatial relationships |
| 分辨率对齐 | Resolution alignment | resample all inputs to a common grid |

## Workflow

### Step -1: Organize the project

For multi-step geospatial projects, establish a stable structure before heavy processing:

```text
project/
├── 代码/
├── 数据结果/
├── 图表/
├── 说明文档/
└── 质量检查/
```

Rules learned from large raster projects:

- Put scripts in `代码/`. In Chinese-facing projects, every generated script line should have a Chinese comment.
- Put computed data in `数据结果/`. Every major result folder must contain a nearby `数据说明.md` that explains data sources, processing steps, formulas, units, fields, and one small calculation example when useful.
- Put figures in `图表/`, narrative method/result notes in `说明文档/`, and validation tables/logs in `质量检查/`.
- If outputs become messy, do not immediately rerun everything. First archive or copy the latest trusted outputs into a clean directory and write a directory explanation.
- Important stages may use independent repositories or result packages, but the final thesis/report delivery should have one consolidated directory.

### Step 0: Confirm folders

Before any processing, ask the user two questions:

1. **数据文件夹**: 输入数据存放在哪个目录？
2. **输出文件夹**: 分析结果输出到哪个目录？

If the user has already specified paths in their message, skip the question for that item.
Use `pathlib.Path` for all paths in generated code.

After the output folder is confirmed, initialize a git repository in it to track all
generated scripts, intermediate results, and configuration:

```bash
cd <output_folder>
git init
```

Create a `.gitignore` to exclude large raw data files but track scripts and config:

```text
# Track
*.py
*.md
*.json
*.txt

# Ignore raw data (adjust patterns to actual data formats)
*.tif
*.tiff
*.shp
*.shx
*.dbf
*.prj
*.cpg
*.nc
*.hdf
*.h5
```

Make an initial commit with the analysis plan and any generated scripts. This way the
entire analysis workflow is version-controlled and reproducible.

### Step 1: Identify data type and analysis task

Classify input data:

- **Raster**: GeoTIFF, NetCDF, HDF, GRIB — gridded data with resolution and CRS
- **Vector**: Shapefile, GeoJSON, GeoPackage — point/line/polygon features
- **Tabular with coordinates**: CSV/Lat-Lon columns — needs conversion to GeoDataFrame
- **Point cloud**: LAS/LAZ — 3D point data
- **Trajectory**: GPS tracks, GPX — time-stamped location sequences

Classify analysis type into one or more domains:

| Domain | Trigger keywords |
|---|---|
| Spatial statistics | interpolation, Kriging, IDW, variogram, 插值, 克里金 |
| Overlay & buffer | overlay, buffer, clip, mask, merge, dissolve, 叠加, 缓冲区, 裁剪, 掩膜, 合并 |
| Remote sensing | NDVI, classification, change detection, band math, 遥感, 分类, 变化检测 |
| Hot spot / Moran's I | hot spot, cold spot, Gi*, Moran's I, LISA, 热点, 莫兰指数 |
| Trend analysis | Mann-Kendall, Sen's slope, trend, Pettitt, 趋势分析 |
| CRS & alignment | reprojection, CRS, resolution alignment, 投影, 坐标系, 分辨率对齐 |

If the task spans multiple domains, plan the pipeline order: I/O and CRS alignment first,
then analysis, then validation.

For raster calculations, ask the user what analytical scale they need when it is unclear:

- pixel/cell scale (`逐像元`)
- month scale (`月尺度`)
- annual scale (`年尺度`)
- multi-year mean (`多年平均`)
- cumulative change (`累计变化`)
- regional or category summary (`分区/类型汇总`)

Default to pixel-first processing, then aggregate by region, category, year, or month. Avoid computing regional means first and then using those means for mechanism analysis unless the user explicitly requests a regional-average model.

### Step 2: Inspect data and environment

For each input file, check:

- File format and readability
- CRS (EPSG code, proj4 string)
- Resolution / cell size (raster) or geometry type (vector)
- Spatial extent / bounding box
- Nodata value and encoding
- Value range (raster) or attribute columns (vector)

For multi-year or monthly raster series, also check:

- Expected years and months are complete.
- File naming can be parsed reliably into year/month/factor.
- All rasters share compatible CRS, transform, shape, resolution, nodata, and valid masks.
- The relationship between month-scale, annual-scale, multi-year mean, and cumulative outputs is stated before calculation.

Use `scripts/geo_data_io.py` for automated inspection.

Check Python environment for required libraries. If a critical library is missing,
report the blocker and provide the install command. Do not silently fall back to a
different library without telling the user.

### Step 3: Select library stack

Use `references/library-selection.md` to choose the right library for each operation.

Default stacks:

| Task | Default library | Fallback |
|---|---|---|
| Raster I/O | `rasterio` | `GDAL` (for HDF subdatasets) |
| Vector I/O | `geopandas` | `fiona` + `shapely` |
| NetCDF / HDF | `xarray` + `rioxarray` | `netCDF4` |
| Spatial statistics | `pysal/esda` | `scipy` + `numpy` |
| Kriging | `pykrige` | `gstools` |
| Interpolation | `scipy.interpolate` | `pykrige` |
| Classification | `scikit-learn` | — |
| Trend analysis | `pymannkendall` | `scipy.stats` |

Report the selected stack to the user before proceeding.

### Step 4: Plan the analysis pipeline

Break the analysis into reproducible steps. For each step, note:

- Input files and their paths
- Operation and parameters
- Output files and their paths
- Potential issues (CRS mismatch, resolution mismatch, nodata propagation, memory)

**Resolution alignment**: When multiple raster inputs have different resolutions:

1. Report the resolution of each input file.
2. Ask the user: "这些栅格数据分辨率不一致，是否需要统一重采样？"
3. If yes, ask: "以哪个数据为基准？或是否上传新的基准数据？"
4. Resample all other inputs to match the reference resolution and extent using nearest-neighbor
   for categorical rasters (land use, vegetation type, administrative/zone masks) and bilinear
   for continuous rasters (temperature, precipitation, PET, NDVI-like indices, elevation).
5. Use `scripts/crs_utils.py` for the resampling operation.

For unit-sensitive raster analysis:

- Use intensity/depth units such as `mm`, `℃`, and index values as the main analysis units for continuous variables.
- Treat volume, total water amount, and area-weighted totals as supplementary tables or management interpretation unless the user explicitly chooses them as the main metric.
- Do not combine different units directly in one score. Standardize indicators to unitless scores before weighted ranking.

### Step 5: Generate and execute code

Write Python scripts following the patterns in `scripts/`. Rules:

- Use `pathlib.Path` for all paths — never hardcode OS-specific separators.
- For Chinese-facing projects, use English variable/function names and add Chinese comments to every executable line.
- Handle nodata explicitly at every step: check for nodata, propagate correctly, set output nodata.
- Include progress reporting for batch operations (print percentage or use `tqdm`).
- Write intermediate results to the output folder when the pipeline has more than 3 steps.
- Use context managers (`with` statements) for all rasterio/gdal dataset handles.
- For large rasters that may not fit in memory, use windowed reading (`rasterio.windows`).
- Write `数据说明.md` next to each major data output folder, including source files, formulas, units, field definitions, processing scale, and a small example when the formula is not obvious.
- After code generation, review the code before running or finalizing it. Confirm the script follows the selected scale, uses the right resampling method, preserves masks, writes Chinese output names when required, and keeps units consistent.

### Step 6: Validate results

Use `references/qa-checklist.md` for the validation checklist:

- Output CRS matches expected CRS
- Output extent is within expected bounds
- Output resolution matches target (if aligned)
- Value ranges are sane (e.g., NDVI in [-1, 1], classification codes are integers)
- Nodata is handled correctly (no nodata values leaking into data range)
- For statistical outputs: p-values, confidence intervals, effect sizes are reported
- Effective pixel counts are explained, especially when they differ from a classification mask or land-use mask.
- Scale and unit checks are explicit: pixel maxima, regional means, whole-area means, and cumulative sums are not compared as if they were the same quantity.
- For conservation/decomposition analyses, include residual or closure checks where applicable.

Generate summary statistics and optional visualization (histogram, quick map) for validation.

### Step 7: Report results

Use this output format:

```text
分析结果摘要
- 分析类型: [spatial statistics / overlay / remote sensing / hotspot / Moran's I / trend]
- 输入数据: [file list with format, CRS, resolution]
- 处理流程: [numbered steps executed]
- 输出文件: [absolute paths to output files]

技术详情
- 坐标系统: [source and target CRS]
- 空间范围: [extent in target CRS]
- 分辨率: [cell size or feature count]
- 关键参数: [analysis-specific parameters used]

结果解读
- [key findings in user's language]

风险和注意事项
- [nodata handling, CRS assumptions, scale effects, edge effects, etc.]
```

When the user writes in Chinese, include the Chinese summary section. Otherwise, use English.

After generating the report, commit the final scripts and results to the git repository:

```bash
cd <output_folder>
git add -A
git commit -m "完成分析: [分析类型简述]"
```

### Step 8: Completion notice

After all processing, validation, and reporting are done, display a clear completion notice:

```text
========================================
  数据处理已完成
========================================
- 分析类型: [analysis type]
- 输出目录: [output folder path]
- 输出文件数: [count]
- Git仓库: [output folder] (已初始化，所有脚本已提交)
- 日志/报告: [path to report file if saved]
========================================
```

This notice signals to the user that the workflow is fully complete and they can review
the outputs. If the user is running interactively, also list the output files with their
paths so they can open them directly.

| File | Open when |
|---|---|
| `references/library-selection.md` | Choosing between rasterio/GDAL, geopandas/fiona, pysal/scipy |
| `references/crs-and-projections.md` | CRS detection, transformation, or projection issues arise |
| `references/data-io.md` | Reading unfamiliar formats or handling complex NetCDF/HDF structures |
| `references/spatial-statistics.md` | Kriging, IDW, variogram, or spatial autocorrelation tasks |
| `references/overlay-and-buffer.md` | Spatial overlay, buffer, clip, mask, merge, dissolve, or spatial join |
| `references/remote-sensing.md` | NDVI, classification, change detection, image fusion, or atmospheric correction |
| `references/hotspot-morans.md` | Getis-Ord Gi*, global/local Moran's I, or LISA cluster analysis |
| `references/trend-analysis.md` | Mann-Kendall, Sen's slope, Pettitt test, or seasonal trend analysis |
| `references/chinese-author-alignment.md` | User writes in Chinese or needs bilingual GIS terminology |
| `references/qa-checklist.md` | Before finalizing output or validating analysis results |
