"""Hot spot analysis: Getis-Ord Gi* and Moran's I (global and local)."""

import numpy as np


def global_morans_i(gdf, column, weight_type="queen", permutations=999):
    """Compute Global Moran's I.

    Args:
        gdf: GeoDataFrame with geometry and attribute column
        column: column name for analysis
        weight_type: "queen", "rook", "knn", or "distance"
        permutations: number of permutations for significance test

    Returns: dict with I, p, z, expected_I
    """
    from esda.moran import Moran
    from libpysal.weights import Queen, Rook, KNN, DistanceBand

    w = _build_weights(gdf, weight_type)
    moran = Moran(gdf[column], w, permutations=permutations)

    return {
        "I": float(moran.I),
        "p": float(moran.p_sim),
        "z": float(moran.z_sim),
        "expected_I": float(moran.EI),
        "interpretation": _interpret_morans(moran.I, moran.p_sim),
    }


def local_morans_i(gdf, column, weight_type="queen", permutations=999):
    """Compute Local Moran's I (LISA).

    Args:
        gdf: GeoDataFrame
        column: attribute column
        weight_type: weight matrix type
        permutations: permutation count

    Returns: GeoDataFrame with lisa_I, lisa_p, lisa_q, lisa_class columns
    """
    from esda.moran import Moran_Local

    w = _build_weights(gdf, weight_type)
    lisa = Moran_Local(gdf[column], w, permutations=permutations)

    result = gdf.copy()
    result["lisa_I"] = lisa.Is
    result["lisa_p"] = lisa.p_sim
    result["lisa_q"] = lisa.q

    # Classify
    sig = result["lisa_p"] < 0.05
    conditions = [
        sig & (result["lisa_q"] == 1),
        sig & (result["lisa_q"] == 3),
        sig & (result["lisa_q"] == 2),
        sig & (result["lisa_q"] == 4),
    ]
    labels = ["High-High", "Low-Low", "Low-High", "High-Low"]
    result["lisa_class"] = np.select(conditions, labels, default="Not Significant")

    return result


def getis_ord_gi_star(gdf, column, weight_type="distance", threshold=None):
    """Compute Getis-Ord Gi* hot spot statistics.

    Args:
        gdf: GeoDataFrame
        column: attribute column
        weight_type: "distance", "queen", "knn"
        threshold: distance threshold for distance weights (in CRS units)

    Returns: GeoDataFrame with gi_z, gi_p, hotspot_class columns
    """
    from esda.getisord import G_Local

    w = _build_weights(gdf, weight_type, threshold)
    gi = G_Local(gdf[column], w, star=True)

    result = gdf.copy()
    result["gi_z"] = gi.Zs
    result["gi_p"] = gi.p_sim

    # Classify hot/cold spots
    z = result["gi_z"]
    p = result["gi_p"]
    conditions = [
        (z > 2.58) & (p < 0.01),
        (z > 1.96) & (p < 0.05),
        (z > 1.65) & (p < 0.10),
        (z < -2.58) & (p < 0.01),
        (z < -1.96) & (p < 0.05),
        (z < -1.65) & (p < 0.10),
    ]
    labels = ["Hot 99%", "Hot 95%", "Hot 90%", "Cold 99%", "Cold 95%", "Cold 90%"]
    result["hotspot_class"] = np.select(conditions, labels, default="Not Significant")

    return result


def _build_weights(gdf, weight_type="queen", threshold=None):
    """Build spatial weights matrix."""
    from libpysal.weights import Queen, Rook, KNN, DistanceBand

    if weight_type == "queen":
        w = Queen.from_dataframe(gdf)
    elif weight_type == "rook":
        w = Rook.from_dataframe(gdf)
    elif weight_type == "knn":
        w = KNN.from_dataframe(gdf, k=8)
    elif weight_type == "distance":
        if threshold is None:
            # Auto-calculate threshold as mean nearest-neighbor distance * 2
            from scipy.spatial import cKDTree
            coords = np.array([(g.x, g.y) for g in gdf.geometry.centroid])
            tree = cKDTree(coords)
            dists, _ = tree.query(coords, k=2)
            threshold = float(np.mean(dists[:, 1]) * 2)
        w = DistanceBand.from_dataframe(gdf, threshold=threshold)
    else:
        raise ValueError(f"Unknown weight type: {weight_type}")

    w.transform = "r"
    return w


def _interpret_morans_i(I, p):
    """Interpret Moran's I result."""
    if p > 0.05:
        return "No significant spatial autocorrelation"
    elif I > 0:
        return f"Significant positive autocorrelation (clustering), I={I:.4f}"
    else:
        return f"Significant negative autocorrelation (dispersion), I={I:.4f}"


if __name__ == "__main__":
    import argparse
    import geopandas as gpd

    parser = argparse.ArgumentParser(description="Hot spot analysis")
    sub = parser.add_subparsers(dest="command")

    # Moran's I
    p_mi = sub.add_parser("morans", help="Global and local Moran's I")
    p_mi.add_argument("--input", required=True)
    p_mi.add_argument("--column", required=True)
    p_mi.add_argument("--weight", default="queen")
    p_mi.add_argument("--output", required=True)

    # Gi*
    p_gi = sub.add_parser("gi", help="Getis-Ord Gi* hot spot analysis")
    p_gi.add_argument("--input", required=True)
    p_gi.add_argument("--column", required=True)
    p_gi.add_argument("--weight", default="distance")
    p_gi.add_argument("--threshold", type=float)
    p_gi.add_argument("--output", required=True)

    args = parser.parse_args()
    import json

    gdf = gpd.read_file(args.input)

    if args.command == "morans":
        global_result = global_morans_i(gdf, args.column, args.weight)
        print("Global Moran's I:", json.dumps(global_result, indent=2))
        lisa_result = local_morans_i(gdf, args.column, args.weight)
        lisa_result.to_file(args.output)
        print(f"Saved LISA results: {args.output}")
    elif args.command == "gi":
        result = getis_ord_gi_star(gdf, args.column, args.weight, args.threshold)
        result.to_file(args.output)
        print(f"Saved Gi* results: {args.output}")
        # Print summary
        counts = result["hotspot_class"].value_counts()
        print("\nHot spot summary:")
        print(counts.to_string())
