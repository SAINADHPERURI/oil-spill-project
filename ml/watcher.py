import time
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAR_DIR = PROJECT_ROOT / "data" / "sar"

PYTHON = PROJECT_ROOT.parent / ".venv" / "Scripts" / "python.exe"

PREDICT_SCRIPT = PROJECT_ROOT / "ml" / "predict_sar.py"
DETECT_SCRIPT = PROJECT_ROOT / "ml" / "generate_detection.py"

PREDICTED_MASK = PROJECT_ROOT / "ml" / "output" / "predicted_spill_mask.tif"

OUTPUT_ID = "spill_01"


def process_image(image_path):

    print("\n" + "=" * 50)
    print("NEW SAR IMAGE DETECTED")
    print("=" * 50)
    print(f"Image: {image_path.name}")

    # --------------------------------------------------
    # STEP 1: U-NET PREDICTION
    # --------------------------------------------------

    print("\n[1/2] Running U-Net prediction...")

    result = subprocess.run(
    [
        str(PYTHON),
        str(PREDICT_SCRIPT),
    ],
    cwd=str(PROJECT_ROOT),
)

    if result.returncode != 0:
        print("U-Net prediction failed.")
        return

    if not PREDICTED_MASK.exists():
        print("Predicted mask was not created.")
        return

    # --------------------------------------------------
    # STEP 2: DETECTION
    # --------------------------------------------------

    print("\n[2/2] Running spill detection...")

    result = subprocess.run(
        [
            str(PYTHON),
            str(DETECT_SCRIPT),
            "--image",
            str(image_path),
            "--mask",
            str(PREDICTED_MASK),
            "--output-id",
            OUTPUT_ID,
        ],
        cwd=str(PROJECT_ROOT),
    )

    if result.returncode != 0:
        print("Detection failed.")
        return

    print("\n" + "=" * 50)
    print("PIPELINE COMPLETE")
    print("=" * 50)


def main():

    print("=" * 50)
    print(" OIL SPILL SAR WATCHER")
    print("=" * 50)

    print(f"\nWatching:")
    print(SAR_DIR)

    processed = set()

    while True:

        images = list(SAR_DIR.glob("*_image.tif"))

        for image_path in images:

            if image_path in processed:
                continue

            try:
                process_image(image_path)
                processed.add(image_path)

            except Exception as e:
                print(f"Error processing {image_path.name}: {e}")

        time.sleep(5)


if __name__ == "__main__":
    main()