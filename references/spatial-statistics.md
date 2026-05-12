# Spatial Statistics Reference

## Variogram Modeling

The variogram describes spatial autocorrelation. Three steps:

1. Compute experimental variogram from data
2. Fit a theoretical model (spherical, exponential, Gaussian)
3. Validate with cross-validation

### Theoretical models

| Model | Equation | Range behavior |
|---|---|---|
| Spherical | `γ(h) = c₀ + c·[1.5(h/a) - 0.5(h/a)³]` for h ≤ a | Reaches sill at range a |
| Exponential | `γ(h) = c₀ + c·[1 - exp(-h/a)]` | Approaches sill asymptotically |
| Gaussian | `γ(h) = c₀ + c·[1 - exp(-(h/a)²)]` | Very smooth, approaches sill fast |

Where: c₀ = nugget, c = partial sill, a = range.

### Code: pykrige

```python
from pykrige.ok import OrdinaryKriging

OK = OrdinaryKriging(
    lon, lat, values,
    variogram_model="spherical",
    verbose=True,
    enable_plotting=False,
)
z_pred, ss_pred = OK.execute("grid", grid_lon, grid_lat)
```

### Code: gstools

```python
import gstools as gs

# Fit variogram
bin_center, gamma = gs.vario_estimate((lon, lat), values)
model = gs.Spherical(dim=2)
model.fit_variogram(bin_center, gamma)

# Kriging
krige = gs.krige.Ordinary(model, (lon, lat), values)
krige((grid_lon, grid_lat), mesh_type="structured")
field = krige.field
```

## Kriging Types

| Type | When to use | Key difference |
|---|---|---|
| Ordinary Kriging | Default for most spatial interpolation | Assumes constant unknown mean |
| Universal Kriging | Trend in data (e.g., elevation gradient) | Models drift as polynomial |
| Block Kriging | Averaging over areas, not points | Predicts block means |
| Kriging with External Drift | Secondary variable available | Uses covariate to explain trend |

## IDW (Inverse Distance Weighting)

Simple interpolation. Weight decreases with distance.

```python
from scipy.interpolate import RBFInterpolator

# IDW-like with RBF
interp = RBFInterpolator(
    points, values, kernel="thin_plate_sparse"
)
grid_values = interp(grid_points)
```

Manual IDW:
```python
def idw(points, values, query_points, power=2, radius=None):
    from scipy.spatial import cKDTree
    tree = cKDTree(points)
    if radius:
        indices = tree.query_ball_point(query_points, radius)
    else:
        dists, indices = tree.query(query_points, k=len(points))
        indices = [indices] * len(query_points)

    result = np.zeros(len(query_points))
    for i, idx in enumerate(indices):
        if len(idx) == 0:
            result[i] = np.nan
            continue
        d = np.linalg.norm(query_points[i] - points[idx], axis=1)
        d[d == 0] = 1e-10  # avoid division by zero
        w = 1.0 / d ** power
        result[i] = np.sum(w * values[idx]) / np.sum(w)
    return result
```

### IDW parameter selection

| Parameter | Guidance |
|---|---|
| Power (p) | p=2 is standard. Higher p → more local influence. |
| Search radius | Use variogram range or data density. No radius = global search. |
| Min neighbors | At least 3-5 points for stability. |

## Spatial Autocorrelation (Global Moran's I)

Measures whether similar values cluster together.

```python
from esda.moran import Moran
from libpysal.weights import Queen, KNN

# Build weights
w = Queen.from_dataframe(gdf)  # or KNN.from_dataframe(gdf, k=8)
w.transform = "r"  # row-standardize

# Global Moran's I
moran = Moran(gdf["value"], w)
print(f"I = {moran.I:.4f}, p = {moran.p_sim:.4f}, z = {moran.z_sim:.4f}")
```

Interpretation:
- I > 0: similar values cluster (positive autocorrelation)
- I < 0: dissimilar values cluster (negative autocorrelation)
- I ≈ 0: random pattern
- p < 0.05: statistically significant

## Cross-Validation

```python
from sklearn.model_selection import KFold

def cross_validate_kriging(coords, values, model="spherical", n_splits=5):
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    errors = []
    for train_idx, test_idx in kf.split(coords):
        OK = OrdinaryKriging(
            coords[train_idx, 0], coords[train_idx, 1], values[train_idx],
            variogram_model=model,
        )
        pred, _ = OK.execute("points", coords[test_idx, 0], coords[test_idx, 1])
        errors.extend(pred - values[test_idx])
    errors = np.array(errors)
    return {
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "mae": float(np.mean(np.abs(errors))),
        "me": float(np.mean(errors)),  # mean error (bias)
    }
```
