import torch
from pathlib import Path
from typing import Dict, List, Any

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
CACHE_DIR = BASE_DIR / "cache"
AUDIO_DIR = CACHE_DIR / "audio"
DATA_DIR = CACHE_DIR / "data"

for d in [CACHE_DIR, AUDIO_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Hardware & Model Configuration (Auto-detects CUDA on GPU VMs or falls back cleanly to CPU)
DEVICE = "cuda" if (os.environ.get("FORCE_CPU", "0") != "1" and torch.cuda.is_available()) else "cpu"
ASR_MODEL_ID = "openai/whisper-base"
AUDIO_EMOTION_MODEL_ID = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
TEXT_EMOTION_MODEL_ID = "SamLowe/roberta-base-go_emotions"

# OpenF1 API Configuration
OPENF1_BASE_URL = "https://api.openf1.org/v1"
OPENF1_RADIO_ENDPOINT = f"{OPENF1_BASE_URL}/team_radio"
OPENF1_LAPS_ENDPOINT = f"{OPENF1_BASE_URL}/laps"
OPENF1_SESSIONS_ENDPOINT = f"{OPENF1_BASE_URL}/sessions"
OPENF1_DRIVERS_ENDPOINT = f"{OPENF1_BASE_URL}/drivers"

# Hugging Face Datasets
HF_DATASETS = [
    {
        "id": "MikCil/f1-team-radio",
        "name": "F1 Team Radio Transcriptions (14k clips)",
        "description": "Comprehensive audio clips with manual transcripts from 2023-2024 races.",
    },
    {
        "id": "scriptaudio/f1-team-radio",
        "name": "Historical F1 Radio Archive",
        "description": "Team radio exchanges across multiple modern Grand Prix sessions.",
    },
    {
        "id": "VforVitorio/f1-strategy-dataset",
        "name": "F1 Strategy & Radio NLP",
        "description": "Multi-modal F1 dataset combining telemetry and team radio dialogue.",
    },
]

# Curated High-Impact F1 Radio Exchanges with Verified Ground Truth
CURATED_RADIO_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "ham_monaco_stress",
        "driver_id": "hamilton",
        "driver_name": "Lewis Hamilton",
        "racing_number": "44",
        "team": "Mercedes",
        "grand_prix": "Monaco Grand Prix",
        "year": 2024,
        "lap": 48,
        "base_lap_time": 74.25,
        "stress_lap_time": 75.82,
        "delta": "+1.57s",
        "audio_url": "https://livetiming.formula1.com/static/2024/2024-05-26_Monaco_Grand_Prix/2024-05-26_Race/TeamRadio/LEWHAM01_48_20240526_154210.mp3",
        "transcript_raw": "These tyres are completely dead guys, I cannot keep the rear on the track! He is all over my gearbox!",
        "expected_mood": "Stressed",
        "stress_level": 88,
        "turns": [
            {
                "speaker": "Driver",
                "role": "driver",
                "text": "These tyres are completely dead guys, I cannot keep the rear on the track! He is all over my gearbox!",
                "start": 0.0,
                "end": 4.6,
                "stress": "Stressed",
            },
            {
                "speaker": "Pit Wall",
                "role": "engineer",
                "text": "Copy Lewis, Bono here. Managing gaps behind. Mode 7 when available.",
                "start": 4.8,
                "end": 7.5,
                "stress": "Calm",
            },
        ],
    },
    {
        "id": "ver_bahrain_lead",
        "driver_id": "verstappen",
        "driver_name": "Max Verstappen",
        "racing_number": "1",
        "team": "Red Bull Racing",
        "grand_prix": "Bahrain Grand Prix",
        "year": 2024,
        "lap": 22,
        "base_lap_time": 94.12,
        "stress_lap_time": 94.18,
        "delta": "+0.06s",
        "audio_url": "https://livetiming.formula1.com/static/2024/2024-03-02_Bahrain_Grand_Prix/2024-03-02_Race/TeamRadio/MAXVER01_22_20240302_162510.mp3",
        "transcript_raw": "Car balance is feeling good, shifting is smooth. We can extend this stint.",
        "expected_mood": "Calm",
        "stress_level": 18,
        "turns": [
            {
                "speaker": "Driver",
                "role": "driver",
                "text": "Car balance is feeling good, shifting is smooth. We can extend this stint.",
                "start": 0.0,
                "end": 3.8,
                "stress": "Calm",
            },
            {
                "speaker": "Pit Wall",
                "role": "engineer",
                "text": "Understood Max. Gap to Perez is 8.4 seconds. Box target lap 28.",
                "start": 4.0,
                "end": 7.2,
                "stress": "Calm",
            },
        ],
    },
    {
        "id": "lec_silverstone_tire",
        "driver_id": "leclerc",
        "driver_name": "Charles Leclerc",
        "racing_number": "16",
        "team": "Ferrari",
        "grand_prix": "British Grand Prix",
        "year": 2024,
        "lap": 34,
        "base_lap_time": 90.45,
        "stress_lap_time": 91.68,
        "delta": "+1.23s",
        "audio_url": "https://livetiming.formula1.com/static/2024/2024-07-07_British_Grand_Prix/2024-07-07_Race/TeamRadio/CHALEC01_34_20240707_153500.mp3",
        "transcript_raw": "Rain is getting heavier in turn 15! We need intermediate tyres now, box box box!",
        "expected_mood": "Stressed",
        "stress_level": 92,
        "turns": [
            {
                "speaker": "Driver",
                "role": "driver",
                "text": "Rain is getting heavier in turn 15! We need intermediate tyres now, box box box!",
                "start": 0.0,
                "end": 4.2,
                "stress": "Stressed",
            },
            {
                "speaker": "Pit Wall",
                "role": "engineer",
                "text": "Box this lap Charles, box for inters.",
                "start": 4.5,
                "end": 6.8,
                "stress": "Calm",
            },
        ],
    },
    {
        "id": "nor_hungary_tired",
        "driver_id": "norris",
        "driver_name": "Lando Norris",
        "racing_number": "4",
        "team": "McLaren",
        "grand_prix": "Hungarian Grand Prix",
        "year": 2024,
        "lap": 61,
        "base_lap_time": 80.15,
        "stress_lap_time": 81.02,
        "delta": "+0.87s",
        "audio_url": "https://livetiming.formula1.com/static/2024/2024-07-21_Hungarian_Grand_Prix/2024-07-21_Race/TeamRadio/LANNOR01_61_20240721_161500.mp3",
        "transcript_raw": "My neck is killing me on the high speed turns... cockpit temp is unbearable. Doing my best to hold delta.",
        "expected_mood": "Tired",
        "stress_level": 74,
        "turns": [
            {
                "speaker": "Driver",
                "role": "driver",
                "text": "My neck is killing me on the high speed turns... cockpit temp is unbearable. Doing my best to hold delta.",
                "start": 0.0,
                "end": 5.4,
                "stress": "Tired",
            },
            {
                "speaker": "Pit Wall",
                "role": "engineer",
                "text": "9 laps to go Lando. You're doing a fantastic job, keep the rhythm.",
                "start": 5.7,
                "end": 8.9,
                "stress": "Calm",
            },
        ],
    },
    {
        "id": "alo_monza_engine",
        "driver_id": "alonso",
        "driver_name": "Fernando Alonso",
        "racing_number": "14",
        "team": "Aston Martin",
        "grand_prix": "Italian Grand Prix",
        "year": 2024,
        "lap": 18,
        "base_lap_time": 82.30,
        "stress_lap_time": 83.45,
        "delta": "+1.15s",
        "audio_url": "https://livetiming.formula1.com/static/2024/2024-09-01_Italian_Grand_Prix/2024-09-01_Race/TeamRadio/FERALO01_18_20240901_152000.mp3",
        "transcript_raw": "No power on the straight! Loss of deployment! Check telemetry immediately!",
        "expected_mood": "Stressed",
        "stress_level": 84,
        "turns": [
            {
                "speaker": "Driver",
                "role": "driver",
                "text": "No power on the straight! Loss of deployment! Check telemetry immediately!",
                "start": 0.0,
                "end": 4.1,
                "stress": "Stressed",
            },
            {
                "speaker": "Pit Wall",
                "role": "engineer",
                "text": "Fail 8-4 default 0-1 on the wheel. Fail 8-4. Resetting MGU-K.",
                "start": 4.3,
                "end": 7.6,
                "stress": "Calm",
            },
        ],
    },
]
