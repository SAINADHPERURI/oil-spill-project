import os
import numpy as np
import tifffile

# =========================
# CONFIG
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR = os.path.join(BASE_DIR, "dataset")

OUTPUT_DIR = os.path.join(BASE_DIR, "patches")

PATCH_SIZE = 256
STRIDE = 256

# SAR dB normalization range
SAR_MIN = -40.0
SAR_MAX = 5.0


def normalize_sar(image):
    """
    Normalize SAR dB values to [0, 1].
    Values outside the expected range are clipped.
    """

    image = np.clip(image, SAR_MIN, SAR_MAX)

    image = (image - SAR_MIN) / (SAR_MAX - SAR_MIN)

    return image.astype(np.float32)


def extract_patches(image, mask, image_name, output_split):

    h, w = image.shape

    image_output = os.path.join(
        OUTPUT_DIR,
        output_split,
        "images"
    )

    mask_output = os.path.join(
        OUTPUT_DIR,
        output_split,
        "masks"
    )

    os.makedirs(image_output, exist_ok=True)
    os.makedirs(mask_output, exist_ok=True)

    patch_id = 0

    for y in range(0, h - PATCH_SIZE + 1, STRIDE):

        for x in range(0, w - PATCH_SIZE + 1, STRIDE):

            image_patch = image[
                y:y + PATCH_SIZE,
                x:x + PATCH_SIZE
            ]

            mask_patch = mask[
                y:y + PATCH_SIZE,
                x:x + PATCH_SIZE
            ]

            # Skip completely empty mask patches
            if np.sum(mask_patch) == 0:
                continue

            image_filename = f"{image_name}_{patch_id:05d}.npy"
            mask_filename = f"{image_name}_{patch_id:05d}.npy"

            np.save(
                os.path.join(image_output, image_filename),
                image_patch
            )

            np.save(
                os.path.join(mask_output, mask_filename),
                mask_patch.astype(np.float32)
            )

            patch_id += 1

    return patch_id


def process_split(split):

    image_dir = os.path.join(
        DATASET_DIR,
        split,
        "images"
    )

    mask_dir = os.path.join(
        DATASET_DIR,
        split,
        "masks"
    )

    total_patches = 0

    image_files = [
        f for f in os.listdir(image_dir)
        if f.lower().endswith(".tif")
    ]

    print(f"\nProcessing {split}: {len(image_files)} images")

    for filename in sorted(image_files):

        image_path = os.path.join(
            image_dir,
            filename
        )

        mask_path = os.path.join(
            mask_dir,
            filename
        )

        if not os.path.exists(mask_path):
            print(f"WARNING: Missing mask for {filename}")
            continue

        print(f"Processing: {filename}")

        image = tifffile.imread(image_path)
        mask = tifffile.imread(mask_path)

        if image.shape != mask.shape:
            print(
                f"WARNING: Shape mismatch for {filename}: "
                f"{image.shape} vs {mask.shape}"
            )
            continue

        image = normalize_sar(image)

        mask = (mask > 0).astype(np.float32)

        patches = extract_patches(
            image,
            mask,
            os.path.splitext(filename)[0],
            split
        )

        print(f"  Created {patches} patches")

        total_patches += patches

    print(
        f"\n{split.upper()} TOTAL PATCHES: {total_patches}"
    )

    return total_patches


if __name__ == "__main__":

    print("===================================")
    print(" SAR DATASET PREPROCESSING")
    print("===================================")

    train_count = process_split("train")
    test_count = process_split("test")

    print("\n===================================")
    print(" PREPROCESSING COMPLETE")
    print("===================================")
    print(f"Train patches: {train_count}")
    print(f"Test patches : {test_count}")