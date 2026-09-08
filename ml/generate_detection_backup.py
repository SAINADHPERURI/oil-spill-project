"""
generate_detection.py

Turns a REAL SAR image + its ground-truth mask (from the Zenodo
Sentinel-1 Oil Spill dataset) into the detection JSON your backend
expects — replacing hand-typed spill_01.json with something computed
from actual pixels.

WHY THIS APPROACH (be ready to explain this to judges):
- The Zenodo dataset gives you real SAR images + real labeled masks,
  but the crops don't carry lat/lon geolocation metadata.
- Rather than faking a location entirely, we anchor each scenario to
  a REAL coordinate inside your AIS coverage area (e.g. a point from
  your Guam CSV), then convert pixel offsets from the mask's centroid
  into a lat/lon offset using a documented degrees-per-pixel scale.
- Area, shape, and centroid are all computed from the real mask —
  only the geolocation anchor is manually assigned.

Usage:
    python generate_detection.py --scenario guam_01

Add more entries to SCENARIOS below to generate more demo cases.
"""

import argparse
import json
import os
from datetime import datetime

import numpy as np
from PIL import Image
from skimage.measure import label, regionprops

# ---------------------------------------------------------------
# CONFIG — edit these to match your actual downloaded dataset files
# and the real-world anchor point you want each scenario tied to.
# ---------------------------------------------------------------

# Rough resolution assumption for the Sentinel-1 SAR crops (meters/pixel).
# Sentinel-1 IW GRD products are commonly ~10m/pixel; adjust if your
# dataset documentation states otherwise.
PIXEL_SIZE_M = 10.0

# How many degrees of latitude/longitude one pixel offset represents.
# ~0.00009 deg ≈ 10m at the equator. Adjust per scenario if needed.
DEG_PER_PIXEL = 0.00009

SCENARIOS = {
    "guam_01": {
        "image_path": "../data/sar/guam_01_image.tif",
        "mask_path": "../data/sar/guam_01_mask.tif",
        # Real anchor point — pick a coordinate that actually falls
        # inside your AIS CSV's coverage area/time window.
        "anchor_lat": 13.3811,
        "anchor_lon": 144.69066,
        "detected_at": "2025-01-01T12:00:00Z",
        "output_id": "spill_01",
    },
    # "guam_02": { ... add more scenarios here ... },
}


def load_mask(mask_path: str) -> np.ndarray:
    """Loads a mask TIFF and returns a binary array (1 = oil, 0 = background)."""
    img = Image.open(mask_path)
    arr = np.array(img)
    # Masks in this dataset are typically already 0/1 or 0/255 — normalize.
    if arr.max() > 1:
        arr = (arr > 0).astype(np.uint8)
    return arr


def analyze_mask(mask: np.ndarray) -> dict:
    """
    Computes centroid (pixel coords), area (pixels), and an elongation-based
    shape label from the largest connected oil region in the mask.
    """
    labeled = label(mask)
    regions = regionprops(labeled)
    if not regions:
        raise ValueError("No oil region found in this mask — check the file.")

    # Use the largest connected region (in case of noise/multiple blobs)
    largest = max(regions, key=lambda r: r.area)

    centroid_row, centroid_col = largest.centroid  # (row=y, col=x)
    area_px = largest.area
    eccentricity = largest.eccentricity  # 0 = circle, close to 1 = elongated line

    shape = "elongated" if eccentricity > 0.85 else ("stretched" if eccentricity > 0.6 else "round")

    return {
        "centroid_row": centroid_row,
        "centroid_col": centroid_col,
        "area_px": area_px,
        "eccentricity": round(float(eccentricity), 3),
        "shape": shape,
        "image_height": mask.shape[0],
        "image_width": mask.shape[1],
    }


def pixel_to_latlon(centroid_row, centroid_col, image_height, image_width, anchor_lat, anchor_lon):
    """
    Converts a pixel centroid to lat/lon by treating the anchor point as the
    image CENTER, and offsetting by (pixel distance from center) * DEG_PER_PIXEL.
    """
    center_row = image_height / 2
    center_col = image_width / 2

    row_offset_px = centroid_row - center_row
    col_offset_px = centroid_col - center_col

    # Row increases downward in image coords -> south -> subtract from lat
    lat = anchor_lat - (row_offset_px * DEG_PER_PIXEL)
    lon = anchor_lon + (col_offset_px * DEG_PER_PIXEL)
    return lat, lon


def generate(scenario_name: str):
    cfg = SCENARIOS[scenario_name]

    mask = load_mask(cfg["mask_path"])
    analysis = analyze_mask(mask)

    lat, lon = pixel_to_latlon(
        analysis["centroid_row"],
        analysis["centroid_col"],
        analysis["image_height"],
        analysis["image_width"],
        cfg["anchor_lat"],
        cfg["anchor_lon"],
    )

    area_km2 = round((analysis["area_px"] * (PIXEL_SIZE_M ** 2)) / 1_000_000, 2)

    detection = {
        "centroid": {"lat": round(lat, 5), "lon": round(lon, 5)},
        "area_km2": area_km2,
        "detected_at": cfg["detected_at"],
        "shape": analysis["shape"],
    }

    out_dir = "output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{cfg['output_id']}.json")
    with open(out_path, "w") as f:
        json.dump(detection, f, indent=2)

    print(f"Wrote {out_path}")
    print(json.dumps(detection, indent=2))
    print(f"(computed from real mask: eccentricity={analysis['eccentricity']}, area_px={analysis['area_px']})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True, choices=list(SCENARIOS.keys()))
    args = parser.parse_args()
    generate(args.scenario)