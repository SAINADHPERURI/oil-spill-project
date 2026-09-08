import os
import time
import subprocess

SAR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sar"))
ML_DIR = os.path.dirname(os.path.abspath(__file__))
DETECTION_SCRIPT = os.path.join(ML_DIR, "generate_detection.py")
OUTPUT_DIR = os.path.join(ML_DIR, "output")

processed = set()

print("🛰️ Oil Spill Detection Watcher Started")
print(f"📂 Watching: {SAR_DIR}")
print("⏳ Waiting for new SAR images...\n")


while True:
    try:
        files = os.listdir(SAR_DIR)

        for filename in files:

            if not filename.lower().endswith((".tif", ".tiff")):
                continue

            if "_image" not in filename:
                continue

            image_path = os.path.join(SAR_DIR, filename)

            if image_path in processed:
                continue

            scenario = filename.rsplit("_image", 1)[0]

            mask_filename = scenario + "_mask.tif"
            mask_path = os.path.join(SAR_DIR, mask_filename)

            if not os.path.exists(mask_path):
                print(f"⚠️ Waiting for mask: {mask_filename}")
                continue

            output_id = "spill_01"

            print(f"\n🔍 New SAR image detected: {filename}")
            print(f"📄 Matching mask: {mask_filename}")
            print("⚙️ Running spill detection...")

            result = subprocess.run(
                [
                    os.path.join(
    os.path.dirname(os.path.dirname(ML_DIR)),
    ".venv",
    "Scripts",
    "python.exe"
),
                    DETECTION_SCRIPT,
                    "--image",
                    image_path,
                    "--mask",
                    mask_path,
                    "--output-id",
                    output_id,
                ],
                cwd=ML_DIR,
            )

            if result.returncode == 0:
                print("✅ Spill analysis completed")
                print(f"📊 Output: {OUTPUT_DIR}\\{output_id}.json")
                processed.add(image_path)
            else:
                print("❌ Spill detection failed")

    except Exception as e:
        print(f"❌ Watcher error: {e}")

    time.sleep(3)