from __future__ import annotations

import base64
import os
import shutil
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config import FRONTEND_DIR, BASE_DIR, AUDIO_DIR, DEVICE, CURATED_RADIO_CATALOG
from backend.audio_processor import AudioProcessor
from backend.speaker_diarizer import SpeakerDiarizer
from backend.asr_engine import ASREngine
from backend.stress_analyzer import StressAnalyzer
from backend.telemetry_service import TelemetryService
from backend.dataset_service import DatasetService

logger = logging.getLogger("App")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Silent Co-Driver: 3D F1 Radio Intelligence & Driver Stress Platform",
    version="1.0.0",
    description="Formula 1 AI Telemetry platform separating Driver and Pit Wall Engineer voices, predicting driver stress, and correlating lap pace degradation on an interactive 3D Pit Wall.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core services
dataset_service = DatasetService()
diarizer = SpeakerDiarizer()
asr_engine = ASREngine()
stress_analyzer = StressAnalyzer()
telemetry_service = TelemetryService()

ASSETS_DIR = BASE_DIR / "assets"


class AnalyzeRequest(BaseModel):
    clip_id: Optional[str] = None
    audio_base64: Optional[str] = None
    filename: Optional[str] = None


@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Returns server and hardware health status."""
    import torch
    return {
        "status": "online",
        "device": DEVICE,
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None",
        "vram_gb": round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2) if torch.cuda.is_available() else 0.0,
    }


@app.get("/api/sources")
def get_sources() -> Dict[str, Any]:
    """Returns available data sources and datasets."""
    return dataset_service.list_sources()


@app.get("/api/radio-feed")
async def get_radio_feed(session_key: str = "9472", driver_number: Optional[str] = None) -> Dict[str, Any]:
    """Fetches list of radio messages for a selected session from OpenF1 / local cache."""
    radios = await dataset_service.fetch_openf1_radios(session_key, driver_number)
    return {"session_key": session_key, "count": len(radios), "radios": radios}


@app.get("/api/audio/{clip_id}")
def get_audio_file(clip_id: str):
    """Streams audio wav file for web playback."""
    file_path = AUDIO_DIR / f"{clip_id}.wav"
    if not file_path.exists():
        for item in CURATED_RADIO_CATALOG:
            if item["id"] == clip_id:
                dataset_service._ensure_sample_audio_files()
                break
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")


@app.post("/api/analyze-audio")
async def analyze_audio(payload: AnalyzeRequest) -> Dict[str, Any]:
    """Runs the full AI pipeline: ASR -> Speaker Diarization -> Fused Stress Detection -> Telemetry Correlation."""
    audio_path = None
    fallback_text = None
    matched_meta = None

    if payload.audio_base64:
        # User uploaded custom audio file as base64
        safe_filename = payload.filename or "custom_upload.wav"
        temp_path = AUDIO_DIR / f"upload_{safe_filename}"
        audio_bytes = base64.b64decode(payload.audio_base64.split(",")[-1])
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)
        audio_path = temp_path
        session_id = "custom_upload"
    elif payload.clip_id:
        # Preloaded curated / OpenF1 clip
        session_id = payload.clip_id
        matched_meta = dataset_service.get_curated_sample(payload.clip_id)
        audio_path = AUDIO_DIR / f"{payload.clip_id}.wav"
        if not audio_path.exists():
            dataset_service._ensure_sample_audio_files()
        if matched_meta:
            fallback_text = matched_meta.get("transcript_raw")
    else:
        # Default to first curated item
        session_id = "ham_monaco_stress"
        matched_meta = dataset_service.get_curated_sample(session_id)
        audio_path = AUDIO_DIR / f"{session_id}.wav"
        if matched_meta:
            fallback_text = matched_meta.get("transcript_raw")

    if not audio_path or not audio_path.exists():
        raise HTTPException(status_code=400, detail="Could not locate valid audio source")

    # 1. Load & Normalize Audio
    audio, sr = AudioProcessor.load_audio(audio_path)
    acoustic_features = AudioProcessor.extract_acoustic_features(audio, sr)

    # 2. Transcribe Audio (Whisper ASR)
    asr_result = asr_engine.transcribe(audio, sr, fallback_text=fallback_text)

    # 3. Speaker Diarization (Driver vs Pit Wall Engineer)
    diarized_turns = diarizer.diarize(audio, sr, whisper_segments=asr_result.get("chunks"))

    # Extract driver-specific speech text and audio slice for stress recognition
    driver_texts = [t["text"] for t in diarized_turns if t["role"] == "driver"]
    driver_combined_text = " ".join(driver_texts) if driver_texts else asr_result.get("text", "")

    # 4. Fused Stress Analysis on Driver Voice
    stress_result = stress_analyzer.analyze_driver_stress(
        driver_audio=audio,
        sr=sr,
        transcript=driver_combined_text,
        acoustic_features=acoustic_features,
    )

    # 5. Telemetry & Lap Pace Correlation
    telemetry_result = telemetry_service.get_session_telemetry(
        session_id=session_id,
        stress_level=stress_result["stress_level"],
        mood=stress_result["mood"],
    )

    # 6. Generate waveform data points (64 samples) for frontend rendering
    step = max(1, len(audio) // 64)
    waveform_points = [round(float(np.abs(audio[i : i + step]).mean()), 3) for i in range(0, len(audio), step)][:64]

    return {
        "session_id": session_id,
        "metadata": {
            "driver_name": telemetry_result["snapshot"]["driver_name"],
            "racing_number": telemetry_result["snapshot"]["racing_number"],
            "grand_prix": telemetry_result["snapshot"]["grand_prix"],
            "lap": telemetry_result["snapshot"]["current_lap"],
            "duration_s": asr_result.get("duration_s", 6.0),
        },
        "transcript_full": asr_result.get("text", ""),
        "diarized_turns": diarized_turns,
        "stress_analysis": stress_result,
        "telemetry": telemetry_result,
        "waveform": waveform_points,
        "audio_url": f"/api/audio/{session_id}" if payload.clip_id else None,
    }


# Mount Assets and Frontend directories
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
