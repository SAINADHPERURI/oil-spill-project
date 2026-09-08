import pandas as pd
from datetime import datetime, timedelta
import re
def safe_str(val, default="Unknown"):
    """Returns a JSON-safe string, replacing NaN/None with a default."""
    if pd.isna(val):
        return default
    return str(val)

AIS_CSV_PATH = "../data/guam_2025.csv"

SPACE_BUFFER_DEG = 2.0 
TIME_BUFFER_HOURS = 48   

def parse_geometry(geom_str):
    """Extracts longitude and latitude floats from a 'POINT (lon lat)' string safely."""
    try:
        if pd.isna(geom_str):
            return None, None
        # Extract numbers using regex
        coords = re.findall(r"[-+]?\d*\.\d+|\d+", str(geom_str))
        if len(coords) >= 2:
            return float(coords[0]), float(coords[1]) # returns (lon, lat)
    except Exception:
        pass
    return None, None

def load_ais_data() -> pd.DataFrame:
    df = pd.read_csv(AIS_CSV_PATH)
    
    # 1. Standardize the date-time index column
    df["BaseDateTime"] = pd.to_datetime(df["base_date_time"])
    
    # 2. Unpack the geometry coordinate coordinates safely
    coords = df["geometry"].apply(parse_geometry)
    df["LON"] = [c[0] for c in coords]
    df["LAT"] = [c[1] for c in coords]
    
    return df

def score_vessels(origin: dict) -> list:
    df = load_ais_data()

    origin_time = datetime.fromisoformat(origin["estimated_time"].replace("Z", ""))
    time_min = origin_time - timedelta(hours=TIME_BUFFER_HOURS)
    time_max = origin_time + timedelta(hours=TIME_BUFFER_HOURS)

    # 1. Filter using the unpacked geospatial properties
    nearby = df[
        (df["BaseDateTime"] >= time_min)
        & (df["BaseDateTime"] <= time_max)
        & (df["LAT"].between(origin["lat"] - SPACE_BUFFER_DEG, origin["lat"] + SPACE_BUFFER_DEG))
        & (df["LON"].between(origin["lon"] - SPACE_BUFFER_DEG, origin["lon"] + SPACE_BUFFER_DEG))
    ].copy()

    if nearby.empty:
        return []

    # 2. Track metrics and assign risk score profiles
    results = []
    for mmsi, group in nearby.groupby("mmsi"):
        closest = group.iloc[(group["BaseDateTime"] - origin_time).abs().argsort()[:1]]
        row = closest.iloc[0]

        dist = ((row["LAT"] - origin["lat"]) ** 2 + (row["LON"] - origin["lon"]) ** 2) ** 0.5
        proximity_score = max(0, 1 - dist / SPACE_BUFFER_DEG)

        speed_std = group["sog"].std() if len(group) > 1 else 0
        anomaly_score = min(1, speed_std / 5) if pd.notna(speed_std) else 0

        time_gaps = group["BaseDateTime"].sort_values().diff().dt.total_seconds().fillna(0)
        gap_score = 1 if (time_gaps > 3600).any() else 0

        total_score = round(0.5 * proximity_score + 0.3 * anomaly_score + 0.2 * gap_score, 2)

        results.append({
            "mmsi": int(mmsi),
            "vessel_name": safe_str(row.get("vessel_name")),
            "vessel_type": safe_str(row.get("vessel_type")),
            "lat": float(row["LAT"]),
            "lon": float(row["LON"]),
            "distance_deg": round(dist, 4),
            "proximity_score": round(proximity_score, 2),
            "anomaly_score": round(anomaly_score, 2),
            "ais_gap_flag": bool(gap_score),
            "total_score": total_score,
        })

    results.sort(key=lambda x: x["total_score"], reverse=True)
    return results
