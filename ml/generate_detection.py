import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage


PIXEL_SIZE_M = 10
DEG_PER_PIXEL = 0.00009

# Prototype anchor for the current Guam demo image
ANCHOR_LAT = 13.3811
ANCHOR_LON = 144.69066


def analyze_spill(mask_path):
    mask = tifffile.imread(mask_path)

    # Convert prediction to binary
    mask = mask > 0

    if not np.any(mask):
        raise ValueError("No oil spill detected in predicted mask.")

    # Connected components
    labeled, num_objects = ndimage.label(mask)

    objects = ndimage.find_objects(labeled)

    best_label = None
    best_area = 0

    for label_id, obj in enumerate(objects, start=1):
        if obj is None:
            continue

        area = np.sum(labeled[obj] == label_id)

        if area > best_area:
            best_area = area
            best_label = label_id

    spill = labeled == best_label

    # Coordinates
    rows, cols = np.where(spill)

    centroid_row = rows.mean()
    centroid_col = cols.mean()

    lat = ANCHOR_LAT + centroid_row * DEG_PER_PIXEL
    lon = ANCHOR_LON + centroid_col * DEG_PER_PIXEL

    # Area
    pixel_area_m2 = PIXEL_SIZE_M * PIXEL_SIZE_M
    area_km2 = (best_area * pixel_area_m2) / 1_000_000

    # Shape
    height = rows.max() - rows.min() + 1
    width = cols.max() - cols.min() + 1

    aspect_ratio = max(height, width) / max(1, min(height, width))

    if aspect_ratio < 1.5:
        shape = "round"
    elif aspect_ratio < 3:
        shape = "irregular"
    else:
        shape = "elongated"

    return {
        "centroid": {
            "lat": round(lat, 6),
            "lon": round(lon, 6)
        },
        "area_km2": round(area_km2, 3),
        "shape": shape,
        "spill_pixels": int(best_area)
    }


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--image",
        required=True,
        help="Original SAR image"
    )

    parser.add_argument(
        "--mask",
        required=True,
        help="Predicted U-Net mask"
    )

    parser.add_argument(
        "--output-id",
        default="spill_01"
    )

    args = parser.parse_args()

    print("=" * 40)
    print(" OIL SPILL DETECTION")
    print("=" * 40)

    print("\nSAR image:")
    print(args.image)

    print("\nPredicted mask:")
    print(args.mask)

    result = analyze_spill(args.mask)

    detection = {
        "spill_id": args.output_id,
        "centroid": result["centroid"],
        "area_km2": result["area_km2"],
        "detected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "shape": result["shape"],
        "spill_pixels": result["spill_pixels"],
        "source_image": Path(args.image).name,
        "source_mask": Path(args.mask).name
    }

    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"{args.output_id}.json"

    with open(output_file, "w") as f:
        json.dump(detection, f, indent=2)

    print("\n========================================")
    print(" DETECTION COMPLETE")
    print("========================================")

    print(f"Area       : {detection['area_km2']} km²")
    print(f"Shape      : {detection['shape']}")
    print(f"Centroid   : {detection['centroid']}")
    print(f"Spill px   : {detection['spill_pixels']}")

    print("\nSaved:")
    print(output_file)


if __name__ == "__main__":
    main()