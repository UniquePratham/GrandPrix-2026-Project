from __future__ import annotations

import json
import logging
import math
import wave
import struct
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx

from backend.config import (
    AUDIO_DIR,
    DATA_DIR,
    OPENF1_RADIO_ENDPOINT,
    OPENF1_LAPS_ENDPOINT,
    OPENF1_SESSIONS_ENDPOINT,
    HF_DATASETS,
    CURATED_RADIO_CATALOG,
)

logger = logging.getLogger("DatasetService")
logging.basicConfig(level=logging.INFO)


class DatasetService:
    """Multi-source audio & telemetry dataset engine supporting OpenF1, Hugging Face, and local caches."""

    def __init__(self):
        self.audio_dir = AUDIO_DIR
        self.data_dir = DATA_DIR
        self._ensure_sample_audio_files()

    def _ensure_sample_audio_files(self) -> None:
        """Generates clean synthetic cockpit & radio WAV files for offline demoing if remote files are inaccessible."""
        for item in CURATED_RADIO_CATALOG:
            wav_path = self.audio_dir / f"{item['id']}.wav"
            if not wav_path.exists():
                self._generate_synthetic_f1_radio(wav_path, item["expected_mood"])

    def _generate_synthetic_f1_radio(self, file_path: Path, mood: str) -> None:
        """Synthesizes a realistic 16kHz F1 team radio audio wave with engine harmonics and voice modulation."""
        sample_rate = 16000
        duration_s = 6.0
        num_samples = int(sample_rate * duration_s)

        # Harmonic engine rumble frequencies (V6 turbo hybrid RPM harmonics around 120Hz, 240Hz, 360Hz)
        base_f0 = 160.0 if mood == "Calm" else (280.0 if mood == "Stressed" else 110.0)
        jitter = 1.25 if mood == "Stressed" else 1.02

        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            # Engine background drone
            engine_noise = 0.15 * math.sin(2 * math.pi * 125 * t) + 0.08 * math.sin(2 * math.pi * 250 * t)

            # Modulated radio voice formant proxy
            if t < 3.8:
                # Driver turn: higher pitch jitter + bandpass radio distortion
                voice_freq = base_f0 * (1.0 + 0.15 * math.sin(2 * math.pi * 4.5 * t * jitter))
                voice = 0.45 * math.sin(2 * math.pi * voice_freq * t) * (0.8 + 0.2 * math.sin(2 * math.pi * 12 * t))
                # Add slight radio crackle / noise
                cockpit_ambient = 0.08 * (math.sin(2 * math.pi * 800 * t) * math.sin(2 * math.pi * 3200 * t))
                sample_val = engine_noise + voice + cockpit_ambient
            elif t < 4.2:
                # Mic click gap
                sample_val = 0.02 * math.sin(2 * math.pi * 1000 * t)
            else:
                # Engineer turn: clear pit wall headset tone (cleaner, no engine rumble)
                eng_freq = 135.0
                voice = 0.4 * math.sin(2 * math.pi * eng_freq * t)
                sample_val = 0.02 * engine_noise + voice

            # Clamp and convert to 16-bit PCM
            sample_val = max(-0.95, min(0.95, sample_val))
            pcm_val = int(sample_val * 32767)
            frames.extend(struct.pack("<h", pcm_val))

        with wave.open(str(file_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(frames)

    def list_sources(self) -> Dict[str, Any]:
        """Returns the list of available multi-source providers and datasets."""
        return {
            "huggingface_datasets": HF_DATASETS,
            "openf1_live_sessions": [
                {"meeting_name": "Bahrain Grand Prix", "session_key": "9472", "year": 2024},
                {"meeting_name": "Monaco Grand Prix", "session_key": "9515", "year": 2024},
                {"meeting_name": "British Grand Prix (Silverstone)", "session_key": "9550", "year": 2024},
                {"meeting_name": "Italian Grand Prix (Monza)", "session_key": "9590", "year": 2024},
            ],
            "curated_catalog": CURATED_RADIO_CATALOG,
        }

    async def fetch_openf1_radios(self, session_key: str = "9472", driver_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries the live OpenF1 API for team radio audio URLs and metadata."""
        params: Dict[str, Any] = {"session_key": session_key}
        if driver_number:
            params["driver_number"] = driver_number

        cache_file = self.data_dir / f"openf1_radio_{session_key}_{driver_number or 'all'}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read cache {cache_file}: {e}")

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(OPENF1_RADIO_ENDPOINT, params=params)
                if response.status_code == 200:
                    data = response.json()
                    # Cache successful result
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    return data
        except Exception as e:
            logger.warning(f"OpenF1 API request failed or timed out: {e}. Falling back to curated catalog.")

        # Fallback to curated catalog if OpenF1 network is unavailable
        return [
            {
                "session_key": session_key,
                "driver_number": item["racing_number"],
                "date": f"{item['year']}-05-26T15:42:10.000Z",
                "recording_url": item["audio_url"],
                "curated_id": item["id"],
                "driver_name": item["driver_name"],
                "grand_prix": item["grand_prix"],
            }
            for item in CURATED_RADIO_CATALOG
        ]

    async def fetch_openf1_laps(self, session_key: str = "9472", driver_number: str = "44") -> List[Dict[str, Any]]:
        """Queries live OpenF1 API for lap times and sector performance."""
        cache_file = self.data_dir / f"openf1_laps_{session_key}_{driver_number}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read cache {cache_file}: {e}")

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(OPENF1_LAPS_ENDPOINT, params={"session_key": session_key, "driver_number": driver_number})
                if response.status_code == 200:
                    data = response.json()
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    return data
        except Exception as e:
            logger.warning(f"OpenF1 laps API request failed: {e}. Generating realistic telemetry curve.")

        # Generate synthetic realistic lap times with telemetry
        laps = []
        base_lap = 78.5
        for lap_num in range(1, 60):
            noise = (lap_num % 7) * 0.12 - 0.2
            lap_duration = base_lap + (lap_num * 0.04) + noise
            # Spike around lap 48
            if 46 <= lap_num <= 50:
                lap_duration += 1.45
            laps.append({
                "lap_number": lap_num,
                "lap_duration": round(lap_duration, 3),
                "duration_sector_1": round(lap_duration * 0.32, 3),
                "duration_sector_2": round(lap_duration * 0.38, 3),
                "duration_sector_3": round(lap_duration * 0.30, 3),
                "is_pit_out_lap": lap_num in (18, 42),
            })
        return laps

    def get_curated_sample(self, sample_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a specific curated sample with ground truth metadata."""
        for item in CURATED_RADIO_CATALOG:
            if item["id"] == sample_id:
                wav_path = self.audio_dir / f"{item['id']}.wav"
                return {**item, "local_audio_path": str(wav_path)}
        return None
