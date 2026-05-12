# Hot Spot Analysis and Moran's I Reference

## Getis-Ord Gi* Hot Spot Analysis

Gi* identifies statistically significant hot spots (high values clustered)
and cold spots (low values clustered).

### Weight matrix construction

```python
from libpysal.weights import Queen, Rook, KNN, DistanceBand

# Contiguity-based (polygons)
w = Queen.from_dataframe(gdf)   # shared edge or vertex
w = Rook.from_dataframe(gdf)    # shared edge only

# Distance-based (points or polygons)
w = DistanceBand.from_dataframe(gdf, threshold=5000)  # 5km radius

# K-nearest neighbors
w = KNN.from_dataframe(gdf, k=8)

# Row standardize
w.transform = "r"
```

### Gi* calculation

```python
from esda.getisord import G_Local

gi = G_Local(gdf["value"], w, star=True)  # star=True for Gi*

gdf["gi_z"] = gi.Zs
gdf["gi_p"] = gi.p_sim
```

### Classification

```python
import numpy as np

def classify_hotspots(gdf, z_col="gi_z", p_col="gi_p"):
    """Classify into hot/cold spot categories."""
    conditions = [
        (gdf[z_col] > 2.58) & (gdf[p_col] < 0.01),   # 99% confidence hot
        (gdf[z_col] > 1.96) & (gdf[p_col] < 0.05),   # 95% confidence hot
        (gdf[z_col] > 1.65) & (gdf[p_col] < 0.10),   # 90% confidence hot
        (gdf[z_col] < -2.58) & (gdf[p_col] < 0.01),  # 99% confidence cold
        (gdf[z_col] < -1.96) & (gdf[p_col] < 0.05),  # 95% confidence cold
        (gdf[z_col] < -1.65) & (gdf[p_col] < 0.10),  # 90% confidence cold
    ]
    labels = ["Hot 99%", "Hot 95%", "Hot 90%", "Cold 99%", "Cold 95%", "Cold 90%"]
    gdf["hotspot_class"] = np.select(conditions, labels, default="Not Significant")
    return gdf
```

## Moran's I (Global)

Measures overall spatial autocorrelation in the dataset.

```python
from esda.moran import Moran

w = Queen.from_dataframe(gdf)
w.transform = "r"

moran = Moran(gdf["value"], w, permutations=999)
print(f"I = {moran.I:.4f}")
print(f"p-value = {moran.p_sim:.4f}")
print(f"z-score = {moran.z_sim:.4f}")
```

Interpretation:
- I > 0, p < 0.05: significant positive autocorrelation (clustering)
- I < 0, p < 0.05: significant negative autocorrelation (dispersion)
- |I| ≈ 0 or p > 0.05: no significant pattern

## Local Moran's I (LISA)

Identifies local clusters and outliers.

```python
from esda.moran import Moran_Local

w = Queen.from_dataframe(gdf)
w.transform = "r"

lisa = Moran_Local(gdf["value"], w, permutations=999)

gdf["lisa_I"] = lisa.Is
gdf["lisa_p"] = lisa.p_sim
gdf["lisa_q"] = lisa.q  # quadrant: 1=HH, 2=LH, 3=LL, 4=HL
```

### LISA cluster types

| Quadrant | Meaning | Code |
|---|---|---|
| 1 (HH) | High surrounded by high | Hot spot |
| 2 (LH) | Low surrounded by high | Spatial outlier |
| 3 (LL) | Low surrounded by low | Cold spot |
| 4 (HL) | High surrounded by low | Spatial outlier |

### Classification

```python
def classify_lisa(gdf, p_col="lisa_p", q_col="lisa_q"):
    sig = gdf[p_col] < 0.05
    conditions = [
        sig & (gdf[q_col] == 1),  # HH
        sig & (gdf[q_col] == 3),  # LL
        sig & (gdf[q_col] == 2),  # LH
        sig & (gdf[q_col] == 4),  # HL
    ]
    labels = ["High-High", "Low-Low", "Low-High", "High-Low"]
    gdf["lisa_class"] = np.select(conditions, labels, default="Not Significant")
    return gdf
```

## Visualization

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(1, 1, figsize=(10, 8))
gdf.plot(column="hotspot_class", ax=ax, legend=True,
         categorical=True, cmap="RdBu_r")
ax.set_title("Hot Spot Analysis (Getis-Ord Gi*)")
plt.tight_layout()
plt.savefig("hotspot_map.png", dpi=300)
```

## Common Pitfalls

1. **Weight matrix choice matters**: Queen vs distance-based can give very different results.
   Document your choice and justify it.

2. **Row standardization**: Always use `w.transform = "r"` for Moran's I and LISA.
   Gi* works with both binary and row-standardized weights.

3. **Multiple testing**: With many locations, some significant results are expected by chance.
   Consider FDR correction: `from esda import fdr_correction`.

4. **Edge effects**: Features at the boundary have fewer neighbors, which can bias results.
   Consider using distance-based weights instead of contiguity.

5. **Modifiable areal unit problem (MAUP)**: Results change with aggregation level.
   Test sensitivity to different zonal definitions.
