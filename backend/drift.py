"""
Drift module — estimates spill origin point/time.

Prototype version:
Uses a simplified backward drift estimate while keeping
the same interface that can later be replaced by OpenDrift.
"""

from datetime import datetime, timedelta


# Your available AIS dataset covers 2025.
# This keeps the prototype synchronized with that dataset.
AIS_DATASET_START = datetime(2025, 1, 1, 0, 0, 0)


def estimate_origin(detection: dict) -> dict:
    """
    Estimate the origin of an oil spill by tracing backward.

    Input:
        detection = {
            "centroid": {"lat": ..., "lon": ...},
            "detected_at": "..."
        }

    Output:
        {
            "lat": ...,
            "lon": ...,
            "estimated_time": "...",
            "confidence": ...
        }
    """

    centroid = detection["centroid"]

    detected_at = datetime.fromisoformat(
        detection["detected_at"].replace("Z", "")
    )

    # ---------------------------------------------------------
    # Simplified backward drift model
    # ---------------------------------------------------------

    origin_lat = centroid["lat"] + 0.05
    origin_lon = centroid["lon"] - 0.03

    origin_time = detected_at - timedelta(hours=6)

    # ---------------------------------------------------------
    # Prototype AIS synchronization
    #
    # The available AIS dataset is from 2025.
    # If the simulated detection occurs outside that period,
    # shift the simulation into the AIS dataset's time range.
    # ---------------------------------------------------------

    if origin_time.year != 2025:
        origin_time = AIS_DATASET_START + timedelta(hours=12)

    return {
        "lat": round(origin_lat, 6),
        "lon": round(origin_lon, 6),
        "estimated_time": origin_time.isoformat() + "Z",
        "confidence": "prototype",
    }