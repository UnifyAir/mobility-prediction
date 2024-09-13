import math
import json
from sklearn.metrics import pairwise

def haversine_sklearn(lon1, lat1, lon2, lat2):
    """
    Returns the great-circle distance (in meters) between two points,
    using sklearn's haversine_distances().

    sklearn's haversine_distances expects [lat, lon] in radians.
    It returns the distance in radians, which we then convert to meters.
    """
    # Convert degrees to radians
    lat1_rad, lon1_rad = map(math.radians, [lat1, lon1])
    lat2_rad, lon2_rad = map(math.radians, [lat2, lon2])

    # The function expects input shapes like [[lat, lon]]
    # and returns a 1x1 array for these two points.
    result_radians = pairwise.haversine_distances(
        [[lat1_rad, lon1_rad]],
        [[lat2_rad, lon2_rad]]
    )[0][0]

    # Convert to meters using Earth's average radius in meters
    distance_meters = 6371000.0 * result_radians
    return distance_meters

def interpolate(point1, point2, fraction):
    """
    Simple linear interpolation between two points.
    point1 and point2 are assumed to be [lon, lat].
    """
    lon1, lat1 = point1
    lon2, lat2 = point2
    lon = lon1 + fraction * (lon2 - lon1)
    lat = lat1 + fraction * (lat2 - lat1)
    return [lon, lat]


def read_geojson(file_path):
    """
    Reads a GeoJSON file from `file_path` and returns the JSON object.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

