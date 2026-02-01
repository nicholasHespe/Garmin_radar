#!/usr/bin/env python3
"""Parse radar coordinates from .map files and generate RADAR_STATIONS dictionary"""
import os
import re
from pathlib import Path

coords_dir = Path('radar_transparencies/coordinates')
radar_stations = {}

# BOM radar images are 512x512 pixels
ORIGINAL_SIZE = 512

# Cropping parameters from CropAndResize function
BORDER = 70 + 16  # 86
DOWN = 70

# Calculate cropped dimensions
# crop((border, border+down, width-border, height-border+down))
# Removes: left=86, top=156, right=86, bottom=16
CROPPED_WIDTH = ORIGINAL_SIZE - (2 * BORDER)  # 512 - 172 = 340
CROPPED_HEIGHT = ORIGINAL_SIZE - (BORDER + DOWN) - (BORDER - DOWN)  # 512 - 156 - 16 = 340

# Final resized dimensions
FINAL_SIZE = 240

for map_file in sorted(coords_dir.glob('*.map')):
    radar_id = map_file.stem

    with open(map_file, 'r') as f:
        lines = f.readlines()

    # Line 2 has the name and range (e.g., "06 Geraldton (128 km)")
    name_line = lines[1].strip()

    # Extract name and range
    name_match = re.search(r'\d+\s+(.+?)\s+\((\d+)\s+km\)', name_line)
    if name_match:
        name = name_match.group(1)
        range_km = int(name_match.group(2))
    else:
        name = name_line
        range_km = 128  # Default if not found

    # Line 4 has center_longitude
    lon_line = lines[3].strip()
    lon = float(lon_line.split('=')[1].strip())

    # Line 5 has center_latitude
    lat_line = lines[4].strip()
    lat = float(lat_line.split('=')[1].strip())

    # Calculate scale (meters per pixel)
    # Range is radius, so diameter is 2 * range
    diameter_m = range_km * 2 * 1000  # Convert km to meters

    # Original scale (before cropping)
    original_scale = diameter_m / ORIGINAL_SIZE

    # Geographic extent of cropped area
    cropped_extent_m = CROPPED_WIDTH * original_scale

    # Final scale after resize to 240x240
    scale_m_per_px = cropped_extent_m / FINAL_SIZE

    radar_stations[radar_id] = {
        'name': name,
        'lat': lat,
        'lon': lon,
        'scale': round(scale_m_per_px, 2)
    }

# Print the dictionary in Python format
print("RADAR_STATIONS = {")
for radar_id in sorted(radar_stations.keys()):
    info = radar_stations[radar_id]
    print(f"    '{radar_id}': {{'name': '{info['name']}', 'lat': {info['lat']}, 'lon': {info['lon']}, 'scale': {info['scale']}}},")
print("}")

print(f"\nTotal radar stations: {len(radar_stations)}")
