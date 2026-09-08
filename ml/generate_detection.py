import argparse
import json
import os
from datetime import datetime, timezone

import numpy as np
from PIL import Image
from skimage.measure import label, regionprops

PIXEL_SIZE_M = 10.0
DEG_PER_PIXEL = 0.00009

DEFAULT_ANCHOR_LAT = 13.3811
DEFAULT_ANCHOR_LON = 144.69066


def load_mask(mask_path):
    img = Image.open(mask_path)
    arr = np.array(img)

    if arr.max() > 1:
        arr = (arr > 0).astype(np.uint8)

    return arr


def analyze_mask(mask):
    labeled = label(mask)
    regions = regionprops(labeled)

    if not regions:
        raise ValueError("No oil region found in mask.")

    largest = max(regions, key=lambda r: r.area)

    row, col = largest.centroid
    area_px = largest.area
    eccentricity = float(largest.eccentricity)

    if eccentricity > 0.85:
        shape = "elongated"
    elif eccentricity > 0.6:
        shape = "stretched"
    else:
        shape = "round"

    return {
        "centroid_row": float(row),
        "centroid_col": float(col),
        "area_px": int(area_px),
        "eccentricity": round(eccentricity, 3),
        "shape": shape,
        "image_height": mask.shape[0],
        "image_width": mask.shape[1],
    }


def pixel_to_latlon(
    centroid_row,
    centroid_col,
    image_height,
    image_width,
    anchor_lat,
    anchor_lon,
):
    center_row = image_height / 2
    center_col = image_width / 2

    row_offset = centroid_row - center_row
    col_offset = centroid_col - center_col

    lat = anchor_lat - (row_offset * DEG_PER_PIXEL)
    lon = anchor_lon + (col_offset * DEG_PER_PIXEL)

    return lat, lon


def generate(image_path, mask_path, output_id="spill_01"):
    print(f"🛰️ Image: {image_path}")
    print(f"🎯 Mask:  {mask_path}")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"SAR image not found: {image_path}")

    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Mask not found: {mask_path}")

    mask = load_mask(mask_path)

    analysis = analyze_mask(mask)

    lat, lon = pixel_to_latlon(
        analysis["centroid_row"],
        analysis["centroid_col"],
        analysis["image_height"],
        analysis["image_width"],
        DEFAULT_ANCHOR_LAT,
        DEFAULT_ANCHOR_LON,
    )

    area_km2 = round(
        (analysis["area_px"] * PIXEL_SIZE_M ** 2) / 1_000_000,
        2,
    )

    detected_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    detection = {
        "spill_id": output_id,
        "centroid": {
            "lat": round(lat, 5),
            "lon": round(lon, 5),
        },
        "area_km2": area_km2,
        "detected_at": detected_at,
        "shape": analysis["shape"],
        "eccentricity": analysis["eccentricity"],
        "source_image": os.path.basename(image_path),
        "source_mask": os.path.basename(mask_path),
    }

    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "output",
    )

    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(
        output_dir,
        f"{output_id}.json",
    )

    with open(output_path, "w") as f:
        json.dump(detection, f, indent=2)

    print("\n✅ Oil spill analysis completed")
    print(json.dumps(detection, indent=2))
    print(f"\n📄 Output: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--image",
        required=True,
        help="Path to SAR image",
    )

    parser.add_argument(
        "--mask",
        required=True,
        help="Path to ground-truth/predicted mask",
    )

    parser.add_argument(
        "--output-id",
        default="spill_01",
    )

    args = parser.parse_args()

    generate(
        args.image,
        args.mask,
        args.output_id,
    )