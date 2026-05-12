# QA Checklist

Use this checklist before finalizing any geospatial analysis output.

## CRS Consistency

- [ ] All input files have known CRS (check with `rasterio.open().crs` or `gdf.crs`)
- [ ] CRS mismatch between inputs is resolved (reproject before analysis)
- [ ] Output CRS matches the intended target
- [ ] If CGCS2000 vs WGS84, document which one is used (they are ~1mm different)

## Nodata Handling

- [ ] Input nodata values are identified (`src.nodata`)
- [ ] Nodata is propagated correctly through all processing steps
- [ ] Output nodata is set explicitly in metadata
- [ ] No nodata values leak into valid data range (check value histograms)

## Resolution and Alignment

- [ ] Multi-raster inputs have matching resolution (if not, alignment step is documented)
- [ ] Multi-raster inputs have matching extent (if not, clipping/mosaicking is documented)
- [ ] Resampling method is appropriate: bilinear for continuous, nearest for categorical
- [ ] Output resolution matches target specification

## Value Range Validation

- [ ] NDVI in [-1, 1]
- [ ] Classification codes are integers (not floats)
- [ ] Temperature in expected range (Kelvin vs Celsius documented)
- [ ] Area calculations use projected CRS (not geographic) for correct units
- [ ] Percentage values in [0, 100] or [0, 1] (document which)

## Statistical Results

- [ ] p-values reported with significance threshold (typically 0.05)
- [ ] Effect sizes reported (not just p-values)
- [ ] Confidence intervals included where applicable
- [ ] Sample size / number of observations reported
- [ ] For Moran's I: weight matrix type documented
- [ ] For trend analysis: pre-whitening applied if autocorrelation present

## Spatial Operations

- [ ] Overlay operations: input geometries are valid (no self-intersections)
- [ ] Buffer operations: distance units match CRS units (meters for projected, degrees for geographic)
- [ ] Clip operations: clip geometry CRS matches input CRS
- [ ] Merge operations: all inputs have same CRS and schema

## File Output

- [ ] Output file exists and is readable
- [ ] Output file has correct CRS embedded
- [ ] Output file has correct nodata value set
- [ ] Output file can be opened in QGIS / ArcGIS
- [ ] File size is reasonable (not empty, not abnormally large)

## Documentation

- [ ] Processing steps are reproducible (script saved)
- [ ] Input files and paths are documented
- [ ] Key parameters are documented (resampling method, weight matrix, significance level)
- [ ] Any assumptions or limitations are noted
