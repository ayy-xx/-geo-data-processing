"""Spatial statistics and interpolation utilities."""

import numpy as np


def kriging_interpolation(lon, lat, values, grid_lon, grid_lat,
                          model="spherical", verbose=False):
    """Ordinary Kriging interpolation.

    Args:
        lon, lat: 1D arrays of station coordinates
        values: 1D array of station values
        grid_lon, grid_lat: 1D arrays of grid coordinates
        model: variogram model (spherical, exponential, gaussian, linear)
        verbose: print variogram parameters

    Returns: 2D array of interpolated values (len(grid_lat) x len(grid_lon))
    """
    from pykrige.ok import OrdinaryKriging

    OK = OrdinaryKriging(
        np.array(lon), np.array(lat), np.array(values),
        variogram_model=model,
        verbose=verbose,
        enable_plotting=False,
    )
    z, ss = OK.execute("grid", grid_lon, grid_lat)
    return z


def idw_interpolation(lon, lat, values, grid_lon, grid_lat, power=2, k=None):
    """Inverse Distance Weighting interpolation.

    Args:
        lon, lat: 1D arrays of station coordinates
        values: 1D array of station values
        grid_lon, grid_lat: 1D arrays of grid coordinates
        power: distance decay exponent (default 2)
        k: number of nearest neighbors (None = use all)

    Returns: 2D array of interpolated values
    """
    from scipy.spatial import cKDTree

    points = np.column_stack([lon, lat])
    tree = cKDTree(points)

    grid_x, grid_y = np.meshgrid(grid_lon, grid_lat)
    grid_points = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    if k is None:
        k = len(points)

    dists, indices = tree.query(grid_points, k=k)
    if k == 1:
        dists = dists[:, np.newaxis]
        indices = indices[:, np.newaxis]

    dists = np.clip(dists, 1e-10, None)
    weights = 1.0 / dists ** power
    weighted_values = weights * values[indices]
    result = np.sum(weighted_values, axis=1) / np.sum(weights, axis=1)

    return result.reshape(len(grid_lat), len(grid_lon))


def fit_variogram(lon, lat, values, model="spherical"):
    """Fit a variogram to point data.

    Args:
        lon, lat: coordinates
        values: observed values
        model: theoretical model type

    Returns: dict with nugget, sill, range
    """
    import gstools as gs

    coords = (np.array(lon), np.array(lat))
    bin_center, gamma = gs.vario_estimate(coords, np.array(values))

    model_map = {
        "spherical": gs.Spherical,
        "exponential": gs.Exponential,
        "gaussian": gs.Gaussian,
        "linear": gs.Linear,
    }
    model_class = model_map.get(model, gs.Spherical)
    fit_model = model_class(dim=2)
    fit_model.fit_variogram(bin_center, gamma)

    return {
        "nugget": float(fit_model.nugget),
        "sill": float(fit_model.sill),
        "range": float(fit_model.len_scale),
        "model": model,
    }


def cross_validate(points, values, method="kriging", model="spherical", n_splits=5):
    """Cross-validation for interpolation methods.

    Args:
        points: Nx2 array of coordinates
        values: 1D array of values
        method: "kriging" or "idw"
        model: variogram model for kriging
        n_splits: number of CV folds

    Returns: dict with rmse, mae, me
    """
    from sklearn.model_selection import KFold

    points = np.array(points)
    values = np.array(values)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    errors = []

    for train_idx, test_idx in kf.split(points):
        if method == "kriging":
            from pykrige.ok import OrdinaryKriging
            OK = OrdinaryKriging(
                points[train_idx, 0], points[train_idx, 1], values[train_idx],
                variogram_model=model,
            )
            pred, _ = OK.execute("points", points[test_idx, 0], points[test_idx, 1])
        else:
            pred = idw_interpolation(
                points[train_idx, 0], points[train_idx, 1], values[train_idx],
                points[test_idx, 0], points[test_idx, 1],
            )
            if pred.ndim > 1:
                pred = pred.ravel()

        errors.extend(pred - values[test_idx])

    errors = np.array(errors)
    return {
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "mae": float(np.mean(np.abs(errors))),
        "me": float(np.mean(errors)),
    }


if __name__ == "__main__":
    import argparse
    import json
    import pandas as pd

    parser = argparse.ArgumentParser(description="Spatial statistics tools")
    sub = parser.add_subparsers(dest="command")

    # kriging
    p_k = sub.add_parser("kriging", help="Kriging interpolation")
    p_k.add_argument("--input", required=True, help="CSV with lon, lat, value columns")
    p_k.add_argument("--model", default="spherical")
    p_k.add_argument("--output", required=True)
    p_k.add_argument("--resolution", type=float, default=0.01)

    # idw
    p_i = sub.add_parser("idw", help="IDW interpolation")
    p_i.add_argument("--input", required=True)
    p_i.add_argument("--power", type=float, default=2)
    p_i.add_argument("--output", required=True)
    p_i.add_argument("--resolution", type=float, default=0.01)

    args = parser.parse_args()

    if args.command in ("kriging", "idw"):
        import rasterio
        df = pd.read_csv(args.input)
        lon = df["lon"].values
        lat = df["lat"].values
        values = df["value"].values

        grid_lon = np.arange(lon.min(), lon.max(), args.resolution)
        grid_lat = np.arange(lat.min(), lat.max(), args.resolution)

        if args.command == "kriging":
            result = kriging_interpolation(lon, lat, values, grid_lon, grid_lat, args.model)
        else:
            result = idw_interpolation(lon, lat, values, grid_lon, grid_lat, args.power)

        transform = rasterio.transform.from_bounds(
            grid_lon[0], grid_lat[0], grid_lon[-1], grid_lat[-1],
            len(grid_lon), len(grid_lat)
        )
        meta = {
            "driver": "GTiff",
            "dtype": result.dtype,
            "width": len(grid_lon),
            "height": len(grid_lat),
            "count": 1,
            "crs": "EPSG:4326",
            "transform": transform,
        }
        with rasterio.open(args.output, "w", **meta) as dst:
            dst.write(result, 1)
        print(f"Saved: {args.output}")
