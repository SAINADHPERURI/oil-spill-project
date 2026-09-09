
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=GEMINI_API_KEY,
    )


def _local_explanation(vessel_data: dict) -> str:
    """
    Deterministic fallback explanation.
    Used when Gemini is unavailable or rate-limited.
    """

    name = vessel_data.get("vessel_name", "Unknown vessel")
    mmsi = vessel_data.get("mmsi", "Unknown")
    total_score = float(vessel_data.get("total_score", 0))
    proximity = float(vessel_data.get("proximity_score", 0))
    anomaly = float(vessel_data.get("anomaly_score", 0))
    ais_gap = vessel_data.get("ais_gap_flag", False)
    distance = vessel_data.get("distance_deg", 0)

    evidence = []

    if proximity >= 0.7:
        evidence.append("high proximity to the estimated spill origin")
    elif proximity >= 0.4:
        evidence.append("moderate proximity to the estimated spill origin")

    if anomaly >= 0.7:
        evidence.append("significant behavioral/speed anomalies")
    elif anomaly >= 0.4:
        evidence.append("moderate behavioral anomalies")

    if ais_gap:
        evidence.append("an AIS signaling gap")

    if not evidence:
        evidence.append("the vessel's available tracking metrics")

    evidence_text = ", ".join(evidence)

    if total_score >= 0.75:
        risk = "high"
    elif total_score >= 0.5:
        risk = "moderate"
    else:
        risk = "low"

    return (
        f"{name} (MMSI {mmsi}) is classified as a {risk}-risk vessel "
        f"with a composite risk score of {total_score:.2f}. "
        f"The assessment is supported by {evidence_text}, "
        f"with an estimated separation of {distance:.4f} degrees "
        f"from the calculated spill origin."
    )


def generate_vessel_explanation(
    vessel_data: dict,
    spill_context: dict
) -> str:
    """
    Generate a concise maritime-investigation explanation using Gemini.

    Falls back to a deterministic local explanation if Gemini
    is unavailable or rate-limited.
    """

    if not GEMINI_API_KEY or client is None:
        print("GEMINI_API_KEY not configured.")
        print("Using local vessel explanation fallback.")
        return _local_explanation(vessel_data)

    prompt = f"""
Analyze the following maritime telemetry data for a vessel
flagged near an oil spill incident.

Write a concise, professional explanation of why the vessel
is considered a suspect.

Focus strictly on:
- proximity to the estimated spill origin
- speed/behavior anomalies
- AIS signaling gaps
- aggregate risk score

Do not invent information.
Do not claim the vessel caused the spill.
Use cautious maritime-investigation language.

INCIDENT CONTEXT:
Estimated Spill Release Time:
{spill_context.get("estimated_time")}

Estimated Spill Origin:
Lat {spill_context.get("lat")}
Lon {spill_context.get("lon")}

VESSEL DATA:
Name: {vessel_data.get("vessel_name")}
Type: {vessel_data.get("vessel_type")}
MMSI: {vessel_data.get("mmsi")}

Distance:
{vessel_data.get("distance_deg")} degrees

Proximity Score:
{vessel_data.get("proximity_score")}

Behavior Anomaly Score:
{vessel_data.get("anomaly_score")}

AIS Gap:
{vessel_data.get("ais_gap_flag")}

Aggregate Risk Score:
{vessel_data.get("total_score")}

Return ONLY a concise explanation of maximum 3 sentences.
"""

    try:
        completion = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert maritime intelligence "
                        "investigator evaluating vessel tracking "
                        "data for environmental incidents."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=180,
        )

        print("MODEL:", completion.model)

        if not completion.choices:
            print("Gemini returned no choices.")
            return _local_explanation(vessel_data)

        explanation = completion.choices[0].message.content

        print("CONTENT:", repr(explanation))

        if explanation and explanation.strip():
            print(
                f"Gemini explanation generated for "
                f"{vessel_data.get('vessel_name')}"
            )
            return explanation.strip()

        print("Gemini returned no text content.")
        print("Using local vessel explanation fallback.")

        return _local_explanation(vessel_data)

    except Exception as e:
        print("GEMINI ERROR:", repr(e))
        print("Using local vessel explanation fallback.")

        return _local_explanation(vessel_data)

