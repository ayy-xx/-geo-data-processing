# Chinese Author Alignment

Use this file when the user writes in Chinese or needs bilingual GIS terminology.

## Core Terminology

| 中文 | English | Library concept |
|---|---|---|
| 地理信息系统 | GIS | Geographic Information System |
| 栅格数据 | Raster | gridded data (GeoTIFF, NetCDF) |
| 矢量数据 | Vector | point/line/polygon (Shapefile, GeoJSON) |
| 坐标参考系统 | CRS | `rasterio.crs`, `gdf.crs` |
| 投影转换 | CRS reprojection | `rasterio.warp.reproject`, `gdf.to_crs()` |
| 地理坐标系 | Geographic CRS | lon/lat (EPSG:4326) |
| 投影坐标系 | Projected CRS | metric units (UTM, Albers) |
| 分辨率 | Resolution | cell size, `src.res` |
| 空间范围 | Extent / Bounds | bounding box |
| 无值 / 缺失值 | Nodata | `src.nodata` |
| 像元 | Pixel / Cell | raster grid unit |
| 重采样 | Resampling | `Resampling.bilinear`, `Resampling.nearest` |
| 双线性插值 | Bilinear interpolation | continuous data resampling |
| 最近邻 | Nearest neighbor | categorical data resampling |
| 叠加分析 | Spatial overlay | `gpd.overlay()` |
| 缓冲区 | Buffer | `gdf.buffer()` |
| 裁剪 | Clip | `gpd.clip()`, `rasterio.mask.mask()` |
| 掩膜 | Mask | `rasterio.mask.mask()` |
| 合并 | Merge / Mosaic | `rasterio.merge.merge()` |
| 溶解 | Dissolve | `gdf.dissolve()` |
| 空间连接 | Spatial join | `gpd.sjoin()` |
| 插值 | Interpolation | Kriging, IDW |
| 克里金插值 | Kriging | `pykrige`, `gstools` |
| 反距离权重 | IDW | `scipy.interpolate` |
| 变异函数 | Variogram | spatial autocorrelation model |
| 块金效应 | Nugget | micro-scale variation |
| 基台值 | Sill | total variance |
| 变程 | Range | distance of correlation |
| 空间自相关 | Spatial autocorrelation | Moran's I |
| 莫兰指数 | Moran's I | `esda.Moran` |
| 热点分析 | Hot spot analysis | Getis-Ord Gi* |
| 局部空间自相关 | LISA | Local Moran's I |
| 趋势分析 | Trend analysis | Mann-Kendall |
| 检验统计量 | Test statistic | z-score, tau |
| 显著性水平 | Significance level | p-value |
| 转移矩阵 | Transition matrix | land use change |
| 分类 | Classification | supervised/unsupervised |
| 监督分类 | Supervised classification | Random Forest, SVM |
| 非监督分类 | Unsupervised classification | K-means |
| 归一化植被指数 | NDVI | (NIR-Red)/(NIR+Red) |
| 变化检测 | Change detection | image differencing |
| 遥感 | Remote sensing | satellite imagery |
| 数字高程模型 | DEM | elevation raster |
| 土地利用 | Land use | classification map |
| 行政区划 | Administrative boundaries | polygons |
| 属性表 | Attribute table | GeoDataFrame columns |
| 拓扑 | Topology | spatial relationships |

## Common Chinese GIS Data Sources

| 数据源 | English name | URL |
|---|---|---|
| 资源环境科学与数据中心 | Resource and Environment Science and Data Center | resdc.cn |
| 国家地球系统科学数据中心 | National Earth System Science Data Center | geodata.cn |
| 国家青藏高原科学数据中心 | National Tibetan Plateau Data Center | tpdc.ac.cn |
| 地理空间数据云 | Geospatial Data Cloud | gscloud.cn |
| 中国科学院空天信息创新研究院 | AIRCAS | aircas.ac.cn |

## Common Chinese Projection Systems

| 名称 | EPSG | 说明 |
|---|---|---|
| CGCS 2000 | 4490 | 国家标准地理坐标系 |
| CGCS 2000 / 高斯-克吕克 | 4491-4501 | 6度分带 |
| CGCS 2000 / 高斯-克吕克 | 4502-4512 | 3度分带 |
| 北京54 | 214xx | 旧基准面，Krassovsky椭球 |
| 西安80 | 23xx | 旧基准面，IAG75椭球 |

## Bilingual Intake Questions

When the user provides Chinese input, clarify with these questions if needed:

```text
请确认以下信息：
1. 输入数据的坐标系是什么？（WGS84 / CGCS2000 / 其他）
2. 输出数据需要什么坐标系？
3. 分辨率要求是多少？（如：1km, 500m, 30m）
4. 输出文件格式？（GeoTIFF / Shapefile / CSV）
5. 分析结果需要中文还是英文标注？
```

## Chinese Encoding in Shapefiles

Chinese shapefiles often use GBK encoding for attribute fields:

```python
gdf = gpd.read_file("data.shp", encoding="gbk")
# Write with UTF-8 for compatibility
gdf.to_file("output.shp", encoding="utf-8")
```

## Common Pitfalls for Chinese Users

1. **GBK encoding**: Always specify `encoding="gbk"` when reading Chinese shapefiles.
2. **CGCS2000 vs WGS84**: Nearly identical for most work. Don't reproject unless necessary.
3. **Deprecated proj4 strings**: Chinese datasets often use old proj4 definitions.
   Convert to EPSG codes where possible.
4. **Missing CRS info**: Many Chinese datasets lack CRS metadata. Infer from coordinate range.
5. **Albers for China**: Use standard parallels 25N and 47N, central meridian 105E.
