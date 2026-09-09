import os
import argparse
import numpy as np
import torch
import tifffile

from unet import UNet


# ============================================================
# CONFIG
# ============================================================

PATCH_SIZE = 256
THRESHOLD = 0.5

MODEL_PATH = r".\ml\models\oil_spill_unet.pth"

# Defaults kept for backward compatibility — override via --image / --output
DEFAULT_INPUT_IMAGE = r".\data\sar\guam_01_image.tif"
DEFAULT_OUTPUT_MASK = r".\ml\output\predicted_spill_mask.tif"


# Same SAR normalization used during training
SAR_MIN = -40.0
SAR_MAX = 5.0


# ============================================================
# PREPROCESSING
# ============================================================

def normalize_sar(image):
    image = np.clip(image, SAR_MIN, SAR_MAX)
    image = (image - SAR_MIN) / (SAR_MAX - SAR_MIN)
    return image.astype(np.float32)


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default=DEFAULT_INPUT_IMAGE, help="Path to the input SAR image")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_MASK, help="Path to write the predicted mask")
    args = parser.parse_args()

    INPUT_IMAGE = args.image
    OUTPUT_MASK = args.output

    print("===================================")
    print(" SAR → U-NET OIL SPILL PREDICTION")
    print("===================================")

    device = torch.device("cpu")
    print("Device:", device)

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print("\nLoading trained U-Net...")

    model = UNet(in_channels=1, out_channels=1)

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=True
    )

    model.load_state_dict(checkpoint)
    model.to(device)
    model.eval()

    print("Model loaded successfully.")

    # --------------------------------------------------------
    # Load SAR image
    # --------------------------------------------------------

    print("\nLoading SAR image:")
    print(INPUT_IMAGE)

    image = tifffile.imread(INPUT_IMAGE)

    print("Original shape:", image.shape)
    print("Original dtype:", image.dtype)

    image = normalize_sar(image)

    height, width = image.shape

    print("Normalized range:",
          float(image.min()),
          "to",
          float(image.max()))

    # --------------------------------------------------------
    # Pad image so dimensions are divisible by 256
    # --------------------------------------------------------

    padded_height = int(
        np.ceil(height / PATCH_SIZE) * PATCH_SIZE
    )

    padded_width = int(
        np.ceil(width / PATCH_SIZE) * PATCH_SIZE
    )

    padded = np.zeros(
        (padded_height, padded_width),
        dtype=np.float32
    )

    padded[:height, :width] = image

    # --------------------------------------------------------
    # Prediction canvas
    # --------------------------------------------------------

    probability_sum = np.zeros(
        (padded_height, padded_width),
        dtype=np.float32
    )

    prediction_count = np.zeros(
        (padded_height, padded_width),
        dtype=np.float32
    )

    total_patches = (
        (padded_height // PATCH_SIZE)
        * (padded_width // PATCH_SIZE)
    )

    patch_number = 0

    # --------------------------------------------------------
    # Run U-Net patch by patch
    # --------------------------------------------------------

    print("\nRunning U-Net inference...")
    print("Total patches:", total_patches)

    with torch.no_grad():

        for y in range(0, padded_height, PATCH_SIZE):

            for x in range(0, padded_width, PATCH_SIZE):

                patch = padded[
                    y:y + PATCH_SIZE,
                    x:x + PATCH_SIZE
                ]

                tensor = torch.from_numpy(
                    patch
                ).unsqueeze(0).unsqueeze(0)

                tensor = tensor.to(device)

                logits = model(tensor)

                probability = torch.sigmoid(
                    logits
                )[0, 0].cpu().numpy()

                probability_sum[
                    y:y + PATCH_SIZE,
                    x:x + PATCH_SIZE
                ] += probability

                prediction_count[
                    y:y + PATCH_SIZE,
                    x:x + PATCH_SIZE
                ] += 1

                patch_number += 1

                if patch_number % 10 == 0:
                    print(
                        f"Processed {patch_number}/{total_patches}"
                    )

    # --------------------------------------------------------
    # Average predictions
    # --------------------------------------------------------

    probability_map = (
        probability_sum /
        np.maximum(prediction_count, 1)
    )

    # Remove padding
    probability_map = probability_map[
        :height,
        :width
    ]

    # --------------------------------------------------------
    # Convert probability → binary mask
    # --------------------------------------------------------

    predicted_mask = (
        probability_map >= THRESHOLD
    ).astype(np.uint8)

    # --------------------------------------------------------
    # Save predicted mask
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(OUTPUT_MASK),
        exist_ok=True
    )

    tifffile.imwrite(
        OUTPUT_MASK,
        predicted_mask
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    spill_pixels = int(
        predicted_mask.sum()
    )

    total_pixels = predicted_mask.size

    spill_percentage = (
        spill_pixels / total_pixels
    ) * 100

    print("\n===================================")
    print(" PREDICTION COMPLETE")
    print("===================================")

    print("Predicted mask shape:", predicted_mask.shape)

    print("Spill pixels:", spill_pixels)

    print(
        f"Spill percentage: {spill_percentage:.4f}%"
    )

    print("\nPredicted mask saved to:")
    print(OUTPUT_MASK)


if __name__ == "__main__":
    main()