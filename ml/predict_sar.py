import argparse
from pathlib import Path

import numpy as np
import torch
import tifffile

from unet import UNet


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = PROJECT_ROOT / "ml" / "models" / "oil_spill_unet.pth"
DEFAULT_INPUT = PROJECT_ROOT / "data" / "sar" / "guam_01_image.tif"
DEFAULT_OUTPUT = PROJECT_ROOT / "ml" / "output" / "predicted_spill_mask.tif"

PATCH_SIZE = 256
STRIDE = 256
THRESHOLD = 0.5


def normalize_sar(image):
    image = image.astype(np.float32)
    image = np.clip(image, -40.0, 5.0)
    image = (image + 40.0) / 45.0
    return image


def predict(image_path, output_path, model_path):
    print("=" * 60)
    print("U-NET SAR OIL SPILL PREDICTION")
    print("=" * 60)
    print(f"Input : {image_path}")
    print(f"Output: {output_path}")

    device = torch.device("cpu")

    print("Loading model...")
    model = UNet(in_channels=1, out_channels=1)
    checkpoint = torch.load(model_path, map_location=device)

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model.to(device)
    model.eval()

    print("Reading SAR image...")
    image = tifffile.imread(str(image_path))

    if image.ndim > 2:
        image = image.squeeze()

    original_height, original_width = image.shape

    image = normalize_sar(image)

    pad_height = (PATCH_SIZE - original_height % PATCH_SIZE) % PATCH_SIZE
    pad_width = (PATCH_SIZE - original_width % PATCH_SIZE) % PATCH_SIZE

    padded = np.pad(
        image,
        ((0, pad_height), (0, pad_width)),
        mode="reflect"
    )

    height, width = padded.shape

    prediction = np.zeros((height, width), dtype=np.float32)
    count = np.zeros((height, width), dtype=np.float32)

    total_patches = 0

    print(f"Image size: {original_height} x {original_width}")

    with torch.no_grad():
        for y in range(0, height, STRIDE):
            for x in range(0, width, STRIDE):

                patch = padded[
                    y:y + PATCH_SIZE,
                    x:x + PATCH_SIZE
                ]

                tensor = torch.from_numpy(
                    patch
                ).float().unsqueeze(0).unsqueeze(0).to(device)

                logits = model(tensor)
                probability = torch.sigmoid(logits)

                prediction[
                    y:y + PATCH_SIZE,
                    x:x + PATCH_SIZE
                ] += probability.squeeze().cpu().numpy()

                count[
                    y:y + PATCH_SIZE,
                    x:x + PATCH_SIZE
                ] += 1

                total_patches += 1

    prediction /= np.maximum(count, 1)

    prediction = prediction[:original_height, :original_width]

    mask = (prediction >= THRESHOLD).astype(np.uint8)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(str(output_path), mask)

    spill_pixels = int(mask.sum())
    total_pixels = mask.size
    spill_percentage = (spill_pixels / total_pixels) * 100

    print("-" * 60)
    print(f"Processed patches : {total_patches}")
    print(f"Output shape      : {mask.shape}")
    print(f"Spill pixels      : {spill_pixels}")
    print(f"Spill percentage  : {spill_percentage:.4f}%")
    print(f"Saved prediction  : {output_path}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--image",
        default=str(DEFAULT_INPUT)
    )

    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT)
    )

    parser.add_argument(
        "--model",
        default=str(DEFAULT_MODEL)
    )

    args = parser.parse_args()

    predict(
        Path(args.image),
        Path(args.output),
        Path(args.model)
    )


if __name__ == "__main__":
    main()