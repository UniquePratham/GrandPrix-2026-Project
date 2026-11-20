# 🏎️ Silent Co-Driver: 3D F1 Radio Intelligence & Driver Stress Platform

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Three.js](https://img.shields.io/badge/Three.js-r128-black?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org/)
[![CUDA](https://img.shields.io/badge/CUDA-RTX%204050%20Accelerated-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://developer.nvidia.com/cuda-zone)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Datasets%20%26%20Models-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

**Grand Prix Hackathon Submission — Problem Statement 1: "The Silent Co-Driver: Reading Driver Stress from Radio Calls"**  
*Theme: Artificial Intelligence in Racing Strategy & Decision-Making | Powered by Hugging Face*

[🚀 Quickstart](#-quickstart) • [✨ Key Innovations](#-key-innovations) • [🧠 Architecture](#-architecture) • [🧪 Test Suite](#-test-suite) • [📖 Setup Guide](SETUP.md) • [🤝 Contributing](CONTRIBUTING.md)

</div>

---

## 🌟 Overview

During high-intensity Formula 1 Grand Prix races, subtle early warning signs in a driver's voice—vocal tremor from high G-force acceleration, respiratory strain, psychological fatigue, or panic during sudden mechanical or tire degradation—are easily missed by pit wall race engineers who are overwhelmed by telemetry numbers, timing screens, and strategy simulations.

**Silent Co-Driver** is an authentic, multi-source AI race intelligence platform that:
1. **Ingests Team Radio Audio** from the **OpenF1 Live API**, **Hugging Face Hub (`MikCil/f1-team-radio`)**, and custom audio uploads.
2. **Separates Speakers with Generalized Diarization**: Accurately distinguishes **Driver (🏎️)** from **Pit Wall Engineer (🎧)** turns using a hybrid acoustic (cockpit engine harmonics vs. quiet headset) and semantic turn analyzer.
3. **Quantifies Real-Time Driver Stress**: Uses a **Multi-Modal Fused Stress Index (FSI)** combining acoustic prosody ($F_0$ pitch shift, vocal jitter), Whisper ASR transcription, and linguistic urgency scoring into `CALM`, `TIRED`, or `STRESSED` states.
4. **Correlates Stress Spikes with Lap Time Loss**: Maps radio events directly against 60-lap race telemetry to calculate exact pace degradation penalties ($+\Delta s$), sector times ($S_1, S_2, S_3$), and tire thermal telemetry.
5. **Renders an Interactive 3D Pit Wall Experience**: High-fidelity Three.js 3D Formula 1 viewport loading the user's **McLaren MP4/5 GLB** model with 360° OrbitControls, Cockpit T-Cam switching, and dynamic stress aura shaders.

---

## ✨ Key Innovations & Standout Features

- **🏎️ Interactive 3D McLaren MP4/5 Viewport**: Renders the 3D Formula 1 car in real-time with metallic PBR materials, carbon fiber aero elements, and spinning Pirelli slick tires.
- **⚡ Reactive 3D Vehicle Stress Aura**:
  - `CALM`: High-tech Neon Cyan underglow with steady RPM engine glow.
  - `STRESSED`: Pulsing Crimson Warning Aura with rapid flashing red rear rain light.
  - `TIRED`: Warm Amber fatigue aura.
- **📹 4 Dynamic Camera Presets**:
  - `🏎️ Cockpit T-Cam`: Driver helmet onboard perspective.
  - `⚡ Aero Profile`: Sidepod and airflow analysis angle.
  - `📊 Pit Wall 3/4`: High tactical telemetry overview.
  - `🏁 Front 3/4`: Action chasing view.
- **🗣️ Generalized Speaker Diarization**: Solves the core challenge of mixed radio dialogue without hardcoded static rules, attributing Driver vs. Pit Wall turns with confidence scores and acoustic profiles.
- **📈 Live Lap Telemetry Chart**: Real-time Chart.js interactive graph showing the exact lap penalty (e.g., $+1.57s$ loss on Lap 48) caused by high driver stress.
- **📡 Multi-Source Data Hub**: Switch instantly between live OpenF1 Grand Prix sessions (Bahrain, Monaco, Silverstone, Monza), Hugging Face datasets, and drag-and-drop custom audio.

---

## 🧠 System Architecture

```
                                  [ Audio Ingestion Layer ]
             OpenF1 Live API  |  Hugging Face Hub (MikCil)  |  Custom Audio Upload
                                            │
                                            ▼
                               [ Audio Processor & Normalizer ]
                         16kHz Mono • RMS Energy • Pitch F0 • Cockpit SNR
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
         [ Whisper ASR Engine ]                       [ Generalized Speaker Diarizer ]
   Hugging Face openai/whisper-base                   Cockpit Noise Profiling & Semantic
         (CUDA GPU Accelerated)                          (Driver 🏎️ vs. Pit Wall 🎧)
                    └───────────────────────┬───────────────────────┘
                                            ▼
                           [ Multi-Modal Fused Stress Recognizer ]
                      Vocal Prosody ($F_0$ + Jitter) + Linguistic Urgency
                               (CALM  •  TIRED  •  STRESSED)
                                            │
                                            ▼
                          [ Lap Telemetry Correlation Service ]
                     60-Lap Race Telemetry • Sector Times • Delta (+$s)
                                            │
                                            ▼
                          [ FastAPI Server & 3D Web Dashboard ]
                 Three.js McLaren MP4/5 3D Viewport • Canvas Waveform • Chart.js
```

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+ (Tested up to Python 3.14)
- (Optional) NVIDIA GPU with CUDA for sub-second Whisper transcription (CPU mode supported automatically).

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Launch Platform
```powershell
python run.py
```
The terminal will display your CUDA hardware accelerator status and automatically open `http://127.0.0.1:8000` in your browser.

---

## 🧪 Automated Test Suite

Run the full verification suite verifying all unit and integration layers:

```powershell
python -m pytest tests/test_pipeline.py -v
```

### Verified Test Matrix:
- `test_dataset_service_sources`: OpenF1 API & Hugging Face dataset connectors.
- `test_audio_processor_load_and_features`: 16kHz resampling, pitch $F_0$, jitter, cockpit SNR.
- `test_speaker_diarizer_driver_vs_engineer`: Accurate Driver vs. Pit Wall turn separation.
- `test_asr_engine_transcription`: Whisper speech-to-text with turn timestamps.
- `test_stress_analyzer_fsi_and_moods`: Fused Stress Index across Calm, Stressed, Tired.
- `test_telemetry_service_correlation`: Lap time degradation calculations.
- `test_api_health_endpoint`: Server health and CUDA hardware detection.
- `test_api_sources_endpoint`: Multi-source dataset catalog retrieval.
- `test_api_analyze_audio_curated`: Full AI pipeline on curated Grand Prix audio.
- `test_api_analyze_audio_base64`: Custom audio upload decoding and analysis.

---

## 📁 Repository Structure

```
GrandPrix 2026 Project/
├── assets/                          # 3D GLB Models & Driver Assets
│   ├── mclaren_mp45__formula_1.glb  # High-detail McLaren 3D Model (110MB)
│   ├── f1_car.png                   # Car telemetry render
│   └── f1_driver.png                # Driver portrait asset
├── backend/                         # Core Python & AI Services
│   ├── config.py                    # Multi-source configuration & endpoints
│   ├── dataset_service.py           # OpenF1 & Hugging Face ingestion engine
│   ├── audio_processor.py           # 16kHz normalizer & acoustic feature extractor
│   ├── speaker_diarizer.py          # Generalized Driver vs Pit Wall diarizer
│   ├── asr_engine.py                # Whisper ASR speech-to-text pipeline
│   ├── stress_analyzer.py           # Multi-modal Fused Stress Recognizer
│   ├── telemetry_service.py         # Lap pace degradation & sector correlation
│   └── app.py                       # FastAPI REST API & static file server
├── frontend/                        # Interactive 3D Pit Wall Dashboard
│   ├── css/pitwall.css              # Dark mode glassmorphism F1 design system
│   ├── js/f1_scene_3d.js            # Three.js 3D F1 Viewport with OrbitControls
│   ├── js/app.js                    # UI controller, audio player & Chart.js
│   └── index.html                   # Main Pit Wall Telemetry screen
├── tests/                           # Automated PyTest Test Suite
│   └── test_pipeline.py             # 10 unit and integration tests
├── artifacts/superpowers/           # Superpowers validation & execution artifacts
│   ├── brainstorm.md
│   ├── plan.md
│   ├── review.md
│   └── finish.md
├── run.py                           # Single-command application launcher
├── requirements.txt                 # Pinned dependencies
├── SETUP.md                         # Detailed environment setup guide
├── CONTRIBUTING.md                  # Development guidelines
├── .gitignore                       # Git ignore rules
└── README.md                        # Project documentation
```

---

## 🏆 Hackathon Compliance & Submission Checklist

- [x] **Combined Frontend + Backend**: Complete FastAPI server + Three.js 3D Pit Wall Dashboard.
- [x] **Hugging Face Hub Integration**: Ingests `MikCil/f1-team-radio` dataset and executes Hugging Face Whisper ASR models.
- [x] **Speaker Diarization**: Generalized separation of Driver (🏎️) vs Pit Wall (🎧).
- [x] **Pace Correlation**: Quantifies exact lap time penalty ($+\Delta s$) under driver stress.
- [x] **Interactive 3D Visuals**: 360° McLaren MP4/5 3D model with dynamic reactive stress auras.
- [x] **100% Automated Test Pass Rate**: Full unit and integration coverage in `pytest`.

---

## 📄 License & Attribution
- Built for the **Grand Prix Hackathon** (Plaksha University & DS Brar Center for Girls and Women in STEM, Powered by Hugging Face).
- Formula 1 radio dataset powered by `MikCil/f1-team-radio` and the OpenF1 project.

## Running

**Python API + web front end**

```bash
pip install -r requirements.txt
python run.py
```

Torch is optional; audio features degrade gracefully without it.
