"""
Cell Tower Data Fetcher

This script fetches cell tower data from OpenCellID for a given region defined by a GeoJSON file.

Setup Instructions:
1. Create a .env file in the same directory with your OpenCellID API key:
   OPENCELLID_API_KEY=your_api_key_here

2. Install required packages:
   pip install requests python-dotenv

Sample Usage:
   python find_cells.py --mcc 404 --mnc 45 --input region.geojson --output cells_data.json

Arguments:
   --mcc: Mobile Country Code (e.g., 404 for India)
   --mnc: Mobile Network Code (e.g., 45 for Airtel)
   --input: Path to input GeoJSON file containing region bbox
   --output: Path for output JSON file (default: cells_data.json)
"""

import json
import os
import argparse

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("OPENCELLID_API_KEY")

MCC=404
MNC=45

import json
import math

import requests


def calculate_area(min_lat, min_lon, max_lat, max_lon):
    """
    Calculate the approximate area (in km²) of a bounding box defined by
    its minimum and maximum latitudes and longitudes.

    Uses the approximation:
      - 1 degree latitude ≈ 111 km.
      - 1 degree longitude ≈ 111 km * cos(center latitude).

    Parameters:
      min_lat (float): Minimum latitude of the cell.
      min_lon (float): Minimum longitude of the cell.
      max_lat (float): Maximum latitude of the cell.
      max_lon (float): Maximum longitude of the cell.

    Returns:
      float: Approximate area of the cell in square kilometers.
    """
    # Difference in degrees
    lat_diff = max_lat - min_lat
    lon_diff = max_lon - min_lon

    # Conversion factor for latitude (km per degree)
    km_per_deg_lat = 111.0

    # Use the cell's center latitude for longitude conversion
    center_lat = (min_lat + max_lat) / 2.0
    km_per_deg_lon = 111.0 * math.cos(math.radians(center_lat))

    # Calculate area in km²
    area = (lat_diff * km_per_deg_lat) * (lon_diff * km_per_deg_lon)
    return area


def subdivide_cell(cell, threshold_area):
    """
    Check the area of the given cell. If the area is greater than threshold_area,
    subdivide the cell into two smaller cells along its longer side. The function
    is applied recursively so that all resulting cells have area <= threshold_area.

    Parameters:
      cell (tuple): A tuple (min_lat, min_lon, max_lat, max_lon) defining a cell.
      threshold_area (float): The maximum allowed area (in km²) for a cell.

    Returns:
      list: A list of cells (each as a tuple) that satisfy the area constraint.
    """
    min_lat, min_lon, max_lat, max_lon = cell
    cell_area = calculate_area(min_lat, min_lon, max_lat, max_lon)

    # If the cell area is within the acceptable threshold, return it.
    if cell_area <= threshold_area:
        return [cell]

    # Otherwise, subdivide the cell.
    # Compute the dimensions in kilometers.
    lat_km = (max_lat - min_lat) * 111.0
    center_lat = (min_lat + max_lat) / 2.0
    lon_km = (max_lon - min_lon) * (111.0 * math.cos(math.radians(center_lat)))

    # Decide which axis to split along (the longer side)
    if lon_km >= lat_km:
        # Split along the longitude axis
        mid_lon = (min_lon + max_lon) / 2.0
        cell1 = (min_lat, min_lon, max_lat, mid_lon)
        cell2 = (min_lat, mid_lon, max_lat, max_lon)
    else:
        # Split along the latitude axis
        mid_lat = (min_lat + max_lat) / 2.0
        cell1 = (min_lat, min_lon, mid_lat, max_lon)
        cell2 = (mid_lat, min_lon, max_lat, max_lon)

    # Recursively check the subdivided cells.
    cells = []
    cells.extend(subdivide_cell(cell1, threshold_area))
    cells.extend(subdivide_cell(cell2, threshold_area))
    return cells


def get_grid_cells(min_lat, min_lon, max_lat, max_lon, cell_size_km=2):
    """
    Divide the overall bounding box into grid cells, each approximately cell_size_km x cell_size_km.
    Returns a list of cells as tuples: (cell_min_lat, cell_min_lon, cell_max_lat, cell_max_lon).
    """
    km_per_deg_lat = 111.0  # 1 degree latitude ≈ 111 km.
    # Use the center latitude of the entire bbox for the longitude conversion.
    lat_center = (min_lat + max_lat) / 2.0
    km_per_deg_lon = 111.0 * math.cos(math.radians(lat_center))

    # Determine the degree increments for the desired cell size.
    lat_step = cell_size_km / km_per_deg_lat
    lon_step = cell_size_km / km_per_deg_lon

    grid_cells = []
    lat = min_lat
    while lat < max_lat:
        cell_max_lat = min(lat + lat_step, max_lat)
        lon = min_lon
        while lon < max_lon:
            cell_max_lon = min(lon + lon_step, max_lon)
            grid_cells.append((lat, lon, cell_max_lat, cell_max_lon))
            lon += lon_step
        lat += lat_step
    # return grid_cells
    threshold_area = cell_size_km * cell_size_km
    final_cells = []
    for cell in grid_cells:
        subdivided = subdivide_cell(cell, threshold_area)
        final_cells.extend(subdivided)

    return final_cells


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch cell tower data for a given region.')
    parser.add_argument('--mcc', type=int, required=True,
                      help='Mobile Country Code')
    parser.add_argument('--mnc', type=int, required=True,
                      help='Mobile Network Code')
    parser.add_argument('--input', type=str, required=True,
                      help='Input GeoJSON file path containing the region bbox')
    parser.add_argument('--output', type=str, default='cells_data.json',
                      help='Output JSON file path for cell tower data (default: cells_data.json)')

    args = parser.parse_args()

    # Update global constants
    global MCC, MNC
    MCC = args.mcc
    MNC = args.mnc

    # Load the GeoJSON file
    with open(args.input, "r") as f:
        geojson_data = json.load(f)

    # Read the bounding box from the GeoJSON.
    # GeoJSON bbox format is: [min_longitude, min_latitude, max_longitude, max_latitude]
    if "bbox" not in geojson_data:
        raise ValueError("The GeoJSON does not contain a 'bbox' key.")

    geojson_bbox = geojson_data["bbox"]
    if len(geojson_bbox) != 4:
        raise ValueError("The 'bbox' does not have 4 values.")

    min_lon, min_lat, max_lon, max_lat = geojson_bbox
    print("GeoJSON Bounding Box:")
    print(f"  Minimum Longitude: {min_lon}")
    print(f"  Minimum Latitude:  {min_lat}")
    print(f"  Maximum Longitude: {max_lon}")
    print(f"  Maximum Latitude:  {max_lat}")

    # Break the region into 2 km x 2 km grid cells (approx. 4 km² each)
    grid_cells = get_grid_cells(min_lat, min_lon, max_lat, max_lon, cell_size_km=2)

    # Your API key for OpenCellID (replace with your actual key)
    base_url = "https://opencellid.org/cell/getInArea"

    # Initialize a list to store all cell data
    all_cells_data = []

    # Loop over each grid cell and create the API URL
    for idx, cell in enumerate(grid_cells):
        cell_min_lat, cell_min_lon, cell_max_lat, cell_max_lon = cell
        # The API expects BBOX in the order: min_lat, min_lon, max_lat, max_lon.
        bbox_str = f"{cell_min_lat},{cell_min_lon},{cell_max_lat},{cell_max_lon}"
        url = f"{base_url}?key={API_KEY}&BBOX={bbox_str}&mcc={MCC}&mnc={MNC}&radio=LTE&format=json"
        print(f"Cell {idx+1} API URL: {url}")
        cell_area = calculate_area(
            cell_min_lat, cell_min_lon, cell_max_lat, cell_max_lon
        )
        print("Cell Area: ", cell_area)

        # Optionally, uncomment the following lines to perform the API call:
        print(f"Processing cell {idx+1}/{len(grid_cells)}") 

        response = requests.get(url)
        if response.status_code == 200:
            try:
                cell_data = response.json()
                print("Records received", cell_data.get('count', None))
                if 'cells' in cell_data:
                    all_cells_data.extend(cell_data['cells'])
            except json.JSONDecodeError:
                print(f"Error: Could not parse JSON response for cell {idx+1}")
        else:
            print(f"Error for cell {idx+1}: Status code {response.status_code}")

    # Create the final merged output
    output_data = {
        "cells": all_cells_data
    }

    # Save the merged data to a file
    output_file = args.output
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nProcessing complete. Found {len(all_cells_data)} cells.")
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
