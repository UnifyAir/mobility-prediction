import argparse
import csv
import sys

from common_utils import haversine_sklearn, read_geojson


def geojson_to_csv_rows(geojson_data):
    """
    Given a GeoJSON object, yield rows of (lat, long, dist),
    where dist is distance from the previous point in meters.
    If there are multiple LineString features, each is handled
    independently. The first point in each LineString has dist=0.
    """
    features = geojson_data.get("features", [])
    for feature in features:
        geometry = feature.get("geometry", {})
        if geometry.get("type") == "LineString":
            coordinates = geometry.get("coordinates", [])
            if not coordinates:
                continue

            # Coordinates are [longitude, latitude].
            # We'll produce rows in the format: lat, long, dist
            prev_lat = None
            prev_lon = None

            for i, (lon, lat) in enumerate(coordinates):
                if i == 0:
                    dist = 0
                else:
                    dist = haversine_sklearn(prev_lon, prev_lat, lon, lat)

                yield (lat, lon, round(dist))
                prev_lat = lat
                prev_lon = lon


def main():
    parser = argparse.ArgumentParser(
        description="Convert GeoJSON with LineString geometry to CSV rows of lat, long, dist."
    )
    parser.add_argument("input_geojson", help="Path to the input GeoJSON file")
    parser.add_argument(
        "-o",
        "--output_csv",
        default="-",
        help="Path to the output CSV file (default: stdout)",
    )
    args = parser.parse_args()

    # Use the common_utils function to read the GeoJSON
    geojson_data = read_geojson(args.input_geojson)

    # Decide where to write CSV data
    if args.output_csv == "-":
        output_handle = sys.stdout
    else:
        output_handle = open(args.output_csv, "w", newline="", encoding="utf-8")

    # Create a CSV writer
    writer = csv.writer(output_handle)
    # Write header
    writer.writerow(["lat", "long", "dist"])

    # Write rows
    for lat, lon, dist in geojson_to_csv_rows(geojson_data):
        writer.writerow([lat, lon, dist])

    if args.output_csv != "-":
        output_handle.close()


if __name__ == "__main__":
    main()
