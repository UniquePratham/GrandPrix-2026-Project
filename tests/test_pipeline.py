from __future__ import annotations

import base64
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.config import AUDIO_DIR, CURATED_RADIO_CATALOG
from backend.audio_processor import AudioProcessor
from backend.speaker_diarizer import SpeakerDiarizer
from backend.asr_engine import ASREngine
from backend.stress_analyzer import StressAnalyzer
from backend.telemetry_service import TelemetryService
from backend.dataset_service import DatasetService
from backend.app import app


@pytest.fixture
def test_client():
    return TestClient(app)


def test_dataset_service_sources():
    ds = DatasetService()
    sources = ds.list_sources()
    assert "huggingface_datasets" in sources
    assert len(sources["huggingface_datasets"]) >= 2
    assert "curated_catalog" in sources
    assert len(sources["curated_catalog"]) >= 5


def test_audio_processor_load_and_features():
    ds = DatasetService()
    sample = ds.get_curated_sample("ham_monaco_stress")
    assert sample is not None

    audio, sr = AudioProcessor.load_audio(sample["local_audio_path"])
    assert sr == 16000
    assert len(audio) > 0

    features = AudioProcessor.extract_acoustic_features(audio, sr)
    assert "rms_energy" in features
    assert "f0_mean" in features
    assert "jitter" in features
    assert "snr_db" in features
    assert "cockpit_noise_ratio" in features
    assert features["cockpit_noise_ratio"] > 0


def test_speaker_diarizer_driver_vs_engineer():
    diarizer = SpeakerDiarizer()
    audio = np.zeros(16000 * 6, dtype=np.float32)
    # Mock driver segment followed by engineer segment
    segments = [
        {"start": 0.0, "end": 3.5, "text": "These tyres are completely dead guys, I cannot turn!"},
        {"start": 3.8, "end": 6.0, "text": "Copy Lewis, Bono here. Managing gaps behind. Mode 7."},
    ]
    turns = diarizer.diarize(audio, sr=16000, whisper_segments=segments)
    assert len(turns) == 2
    assert turns[0]["role"] == "driver"
    assert turns[0]["speaker"] == "Driver"
    assert turns[1]["role"] == "engineer"
    assert turns[1]["speaker"] == "Pit Wall"


def test_asr_engine_transcription():
    asr = ASREngine()
    audio = np.zeros(16000 * 3, dtype=np.float32)
    res = asr.transcribe(audio, sr=16000, fallback_text="Box this lap Charles, box box.")
    assert "text" in res
    assert len(res["text"]) > 0
    assert "chunks" in res


def test_stress_analyzer_fsi_and_moods():
    analyzer = StressAnalyzer()
    audio = np.zeros(16000 * 4, dtype=np.float32)

    # 1. Test Stressed Driver
    res_stressed = analyzer.analyze_driver_stress(
        audio, transcript="No grip, these tyres are completely dead, disaster!"
    )
    assert res_stressed["mood"] == "Stressed"
    assert res_stressed["stress_level"] > 60.0

    # 2. Test Calm Driver
    res_calm = analyzer.analyze_driver_stress(
        audio, transcript="Car balance is feeling good, pace is smooth."
    )
    assert res_calm["mood"] == "Calm"
    assert res_calm["stress_level"] < 40.0

    # 3. Test Tired Driver
    res_tired = analyzer.analyze_driver_stress(
        audio, transcript="My neck is killing me on the high speed turns, cockpit temp is unbearable."
    )
    assert res_tired["mood"] == "Tired"
    assert 40.0 <= res_tired["stress_level"] <= 85.0


def test_telemetry_service_correlation():
    ts = TelemetryService()
    res = ts.get_session_telemetry(
        session_id="ham_monaco_stress", stress_level=88.0, mood="Stressed"
    )
    assert "snapshot" in res
    assert "lap_history" in res
    assert len(res["lap_history"]) == 60
    assert "pace_loss_delta" in res["snapshot"]
    assert float(res["snapshot"]["pace_loss_delta"].replace("+", "").replace("s", "")) > 0.5


def test_api_health_endpoint(test_client):
    response = test_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "device" in data
    assert "cuda_available" in data


def test_api_sources_endpoint(test_client):
    response = test_client.get("/api/sources")
    assert response.status_code == 200
    data = response.json()
    assert "curated_catalog" in data


def test_api_analyze_audio_curated(test_client):
    response = test_client.post(
        "/api/analyze-audio",
        json={"clip_id": "ham_monaco_stress"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "stress_analysis" in data
    assert "diarized_turns" in data
    assert "telemetry" in data
    assert "waveform" in data
    assert len(data["waveform"]) > 0


def test_api_analyze_audio_base64(test_client):
    # Dummy base64 wav
    sample_bytes = np.zeros(16000, dtype=np.int16).tobytes()
    b64_str = base64.b64encode(sample_bytes).decode("utf-8")
    response = test_client.post(
        "/api/analyze-audio",
        json={"audio_base64": b64_str, "filename": "test.wav"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "stress_analysis" in data
