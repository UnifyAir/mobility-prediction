"""
This script reads a GeoJSON file and "smooths" (densifies) the coordinates of any LineString geometries
by inserting intermediate points along each segment. For each pair of consecutive coordinates, if the 
distance between them (calculated using the Haversine formula via sklearn) is greater than a specified 
interval (default is 10 meters), the script interpolates additional points every `interval` meters.

The modified GeoJSON data is then either printed to the standard output or saved to a specified output file.

Sample usage:
    python smooth_geojson.py input.geojson -o output.geojson -i 10

Arguments:
    input_geojson : Path to the input GeoJSON file.
    -o, --output : Path to the output GeoJSON file (default: stdout).
    -i, --interval : Interval in meters for densification (default: 10).
"""

import argparse
import json
import numpy as np
from common_utils import haversine_sklearn, interpolate, read_geojson

def smooth_coordinates(coords, interval=10):
    """
    “Smooth” (densify) a list of coordinates. For each pair of consecutive
    coordinates, if the distance is greater than the given interval,
    inserts intermediate coordinates every `interval` meters.
    """
    if not coords:
        return []

    smoothed = [coords[0]]
    for i in range(1, len(coords)):
        start = smoothed[-1]  # always use the last (possibly interpolated) point as the start
        end = coords[i]
        d = haversine_sklearn(start[0], start[1], end[0], end[1])
        if d > interval:
            # Determine how many full `interval` segments fit in the total distance.
            num_points = int(d // interval)
            # Insert intermediate points at every `interval` meters along the segment.
            for j in range(1, num_points + 1):
                fraction = (j * interval) / d
                # Avoid duplicating the endpoint when fraction == 1
                if fraction < 1:
                    smoothed.append(interpolate(start, end, fraction))
            smoothed.append(end)
        else:
            smoothed.append(end)

    return smoothed

def main():
    parser = argparse.ArgumentParser(
        description='Smooth (densify) LineString coordinates in a GeoJSON file using sklearn haversine_distances.'
    )
    parser.add_argument(
        'input_geojson',
        help='Path to the input GeoJSON file'
    )
    parser.add_argument(
        '-o', '--output',
        default='-',
        help='Path to the output GeoJSON file (default: stdout)'
    )
    parser.add_argument(
        '-i', '--interval',
        type=float,
        default=10,
        help='Interval in meters for densification (default: 10)'
    )

    args = parser.parse_args()

    # ---------------------------
    # 1) Read the input GeoJSON
    # ---------------------------
    geojson_data = read_geojson(args.input_geojson)

    # -----------------------------
    # 2) Smooth the LineString(s)
    # -----------------------------
    for feature in geojson_data.get("features", []):
        geometry = feature.get("geometry", {})
        if geometry.get("type") == "LineString":
            original_coords = geometry.get("coordinates", [])
            geometry["coordinates"] = smooth_coordinates(
                original_coords,
                interval=args.interval
            )

    # ---------------------------
    # 3) Write out the results
    # ---------------------------
    if args.output == '-':
        # Print to standard output
        print(json.dumps(geojson_data, indent=4))
    else:
        # Write to file
        with open(args.output, 'w') as out_file:
            json.dump(geojson_data, out_file, indent=4)

if __name__ == '__main__':
    main()

