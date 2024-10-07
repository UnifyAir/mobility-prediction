"""
This script finds the nearest cell locations from a list of cells (provided in a JSON file)
to a set of geographical coordinates extracted from a GeoJSON file. It calculates the distance 
using the Haversine formula (which computes the great-circle distance between two points on the Earth)
and then selects the top N (default: 20) closest cells. The resulting cells are saved to an output JSON file.

Usage:
    python find_nearest_cells.py <cells_data_path> <geolocation_path> [--output OUTPUT]

Example:
    python find_nearest_cells.py data/cells_data.json data/geolocation.json --output results.json
"""

import json
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import haversine_distances


def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def find_nearest_cells(cells_data, geolocation_data, top_n=20):
    results = []
    for cell in cells_data.get("cells", []):
        distances = []
        print("cell", cell)
        lat = cell.get("lat", None)
        lon = cell.get("lon", None)
        if (lat or lon) is None:
            print("Invalid Cell Data", json.dumps(cell, indent=4))
            continue
        cell_coords = np.radians([[lat, lon]])

        for geo_point in geolocation_data:
            geo_point = list(reversed(geo_point))
            geo_coords = np.radians([geo_point])
            distance = (
                haversine_distances(cell_coords, geo_coords)[0][0] * 6371
            )  # Convert to km

            distances.append(
                {"cell": cell, "geo_point": geo_point, "distance": distance}
            )

        # Sort by distance and pick top N closest points
        cell_with_distance = sorted(distances, key=lambda x: x["distance"])[0]
        results.append(cell_with_distance)
    nearest_cells = sorted(results, key=lambda x: x["distance"])[:top_n]
    nearest_cells = [data.get("cell") for data in nearest_cells]
    print(json.dumps(nearest_cells))
    return nearest_cells


def main(cells_data_path, geolocation_path, output_path):
    cells_data = load_json(cells_data_path)
    geolocation_data = load_json(geolocation_path)
    coordinates = (
        geolocation_data.get("features", {})[0]
        .get("geometry", {})
        .get("coordinates", [])
    )
    nearest_cells = find_nearest_cells(cells_data, coordinates)

    # Output the results
    output_path = Path(output_path)
    with open(output_path, "w") as f:
        json.dump({"cells": nearest_cells}, f, indent=2)

    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Find best cells for a path"
    )
    parser.add_argument("cells_data_path", type=str, help="Path to cells_data.json")
    parser.add_argument("geolocation_path", type=str, help="Path to geolocation.json")
    parser.add_argument(
        "--output", 
        type=str, 
        default="nearest_cells_output.json",
        help="Path to output JSON file (default: nearest_cells_output.json)"
    )

    args = parser.parse_args()
    main(args.cells_data_path, args.geolocation_path, args.output)
