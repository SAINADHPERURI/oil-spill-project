import os
import openai
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# Securely grab the API key from environment variables
# Get a free key at https://aistudio.google.com/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_mock_key_if_testing")

def generate_vessel_explanation(vessel_data: dict, spill_context: dict) -> str:
    """
    Takes structured data about a suspect vessel and generates a human-readable 
    explanation using Gemini describing why the vessel is flagged.
    """
    # Fallback response if the API key is not configured yet
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_mock_key_if_testing":
        return (
            f"Vessel {vessel_data.get('vessel_name')} (MMSI: {vessel_data.get('mmsi')}) "
            f"has a total risk score of {vessel_data.get('total_score')}. It was detected "
            f"{vessel_data.get('distance_deg')} degrees away from the calculated spill origin. "
            f"Anomalous speed shifts: {vessel_data.get('anomaly_score')}. "
            f"AIS gap flag: {vessel_data.get('ais_gap_flag')}."
        )

    # Initialize the client pointing to Gemini's OpenAI-compatible endpoint
    client = openai.OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=GEMINI_API_KEY
    )

    # Build a structured prompt describing the target telemetry anomalies
    prompt = f"""
    Analyze the following maritime telemetry data for a suspect vessel flagged near an oil spill incident.
    Write a concise, professional paragraph explaining why this vessel is considered a suspect. Focus strictly on the data evidence provided (proximity, speed anomalies, and signaling behavior).

    INCIDENT CONTEXT:
    - Estimated Spill Release Time: {spill_context.get('estimated_time')}
    - Target Center Coordinates: Lat {spill_context.get('lat')}, Lon {spill_context.get('lon')}

    VESSEL DATA METRICS:
    - Name: {vessel_data.get('vessel_name')}
    - Type: {vessel_data.get('vessel_type')}
    - MMSI: {vessel_data.get('mmsi')}
    - Distance to Spill Origin: {vessel_data.get('distance_deg')} degrees
    - Proximity Score (0 to 1, higher is closer): {vessel_data.get('proximity_score')}
    - Speed Anomaly Score (0 to 1, indicating sudden speed drops/shaping changes): {vessel_data.get('anomaly_score')}
    - AIS Gap Flag (True/False, indicating if the vessel turned off its transponder/went dark): {vessel_data.get('ais_gap_flag')}
    - Aggregate Risk Score: {vessel_data.get('total_score')}

    Response criteria: Max 3 punchy sentences. Maintain an authoritative maritime investigation tone. Do not repeat the prompt instructions.
    """

    try:
        completion = client.chat.completions.create(
    model="gemini-2.5-flash",
    reasoning_effort="none",  # Gemini 2.5 "thinks" by default, eating into max_tokens — turn it off
    messages=[
        {"role": "system", "content": "You are an expert maritime intelligence investigator evaluating tracking data for environmental non-compliance and illicit oil discharges."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.2,
    top_p=0.7,
    max_tokens=200
)
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Intelligence extraction temporarily offline. Analytics engine baseline score: {vessel_data.get('total_score')}."