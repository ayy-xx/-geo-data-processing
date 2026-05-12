"""Vector operations: overlay, buffer, clip, merge, spatial join."""

import geopandas as gpd


def overlay(gdf_a: gpd.GeoDataFrame, gdf_b: gpd.GeoDataFrame,
            how: str = "intersection") -> gpd.GeoDataFrame:
    """Spatial overlay between two GeoDataFrames.

    Args:
        how: intersection, union, symmetric_difference, difference, identity

    Returns: result GeoDataFrame
    """
    return gpd.overlay(gdf_a, gdf_b, how=how)


def buffer(gdf: gpd.GeoDataFrame, distance: float,
           dissolve: bool = False) -> gpd.GeoDataFrame:
    """Create buffer around geometries.

    Args:
        distance: buffer distance in CRS units
        dissolve: merge overlapping buffers

    Returns: buffered GeoDataFrame
    """
    result = gdf.copy()
    result["geometry"] = gdf.buffer(distance)
    if dissolve:
        result = result.dissolve()
        result = result.explode(index_parts=True).reset_index(drop=True)
    return result


def clip(gdf: gpd.GeoDataFrame, mask_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Clip geometries to a mask.

    Returns: clipped GeoDataFrame
    """
    return gpd.clip(gdf, mask_gdf)


def merge(gdf_list: list) -> gpd.GeoDataFrame:
    """Merge multiple GeoDataFrames into one.

    Args:
        gdf_list: list of GeoDataFrames to merge

    Returns: merged GeoDataFrame
    """
    import pandas as pd
    return gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))


def spatial_join(target: gpd.GeoDataFrame, other: gpd.GeoDataFrame,
                 predicate: str = "intersects", how: str = "left") -> gpd.GeoDataFrame:
    """Spatial join between two GeoDataFrames.

    Args:
        target: target GeoDataFrame
        other: other GeoDataFrame to join
        predicate: spatial predicate (intersects, within, contains, etc.)
        how: join type (left, right, inner)

    Returns: joined GeoDataFrame
    """
    return gpd.sjoin(target, other, predicate=predicate, how=how)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vector operations")
    sub = parser.add_subparsers(dest="command")

    # buffer
    p_buf = sub.add_parser("buffer", help="Buffer geometries")
    p_buf.add_argument("--input", required=True)
    p_buf.add_argument("--distance", type=float, required=True)
    p_buf.add_argument("--dissolve", action="store_true")
    p_buf.add_argument("--output", required=True)

    # clip
    p_clip = sub.add_parser("clip", help="Clip geometries")
    p_clip.add_argument("--input", required=True)
    p_clip.add_argument("--mask", required=True)
    p_clip.add_argument("--output", required=True)

    # overlay
    p_ov = sub.add_parser("overlay", help="Spatial overlay")
    p_ov.add_argument("--a", required=True)
    p_ov.add_argument("--b", required=True)
    p_ov.add_argument("--how", default="intersection")
    p_ov.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.command == "buffer":
        gdf = gpd.read_file(args.input)
        result = buffer(gdf, args.distance, args.dissolve)
        result.to_file(args.output)
        print(f"Saved: {args.output}")
    elif args.command == "clip":
        gdf = gpd.read_file(args.input)
        mask_gdf = gpd.read_file(args.mask)
        result = clip(gdf, mask_gdf)
        result.to_file(args.output)
        print(f"Saved: {args.output}")
    elif args.command == "overlay":
        a = gpd.read_file(args.a)
        b = gpd.read_file(args.b)
        result = overlay(a, b, args.how)
        result.to_file(args.output)
        print(f"Saved: {args.output}")
