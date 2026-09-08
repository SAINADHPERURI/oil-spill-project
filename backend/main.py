"""
Oil Spill Attribution — Backend API
Run with: uvicorn main:app --reload
"""
from insights import generate_vessel_explanation
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import json
import os

from attribution import score_vessels
from drift import estimate_origin

app = FastAPI(title="Oil Spill Attribution API")

# Allow the React frontend (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all local port variations to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ML_OUTPUT_DIR = "../ml/output"


class SpillRequest(BaseModel):
    spill_id: str  # matches a filename in ml/output/, e.g. "spill_01"


@app.get("/")
def root():
    return {"status": "ok", "message": "Oil Spill Attribution API running"}



@app.post("/api/spill-analysis")
def analyze_spill(req: SpillRequest):
    """
    Full pipeline: read ML detection output -> estimate origin (drift) ->
    score nearby AIS vessels -> generate AI explanations -> return to frontend.
    """
    # 1. Load the detection output your ML teammate pushes to ml/output/
    mask_path = os.path.join(ML_OUTPUT_DIR, f"{req.spill_id}.json")
    if not os.path.exists(mask_path):
        raise HTTPException(status_code=404, detail="Spill profile dataset payload not found.")

    with open(mask_path, "r") as f:
        detection = json.load(f)

    # 2. Estimate origin point/time by running drift backward
    origin = estimate_origin(detection)

    # 3. Score AIS vessels near that origin window
    suspects = score_vessels(origin)

    # 4. NEW: Loop through top 3 suspects and append NVIDIA NIM intelligence insights
    for vessel in suspects[:3]:
        explanation = generate_vessel_explanation(vessel, origin)
        vessel["ai_explanation"] = explanation

    return {
        "detection": detection,
        "origin": origin,
        "suspects": suspects,
    }
