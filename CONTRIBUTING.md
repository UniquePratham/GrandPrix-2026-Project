# 🤝 Contributing to Silent Co-Driver

Thank you for your interest in contributing to **Silent Co-Driver: 3D F1 Radio Intelligence & Driver Stress Platform**!

---

## 📜 Code of Conduct & Core Philosophy

- **High Precision & Real Systems**: We prioritize authentic, robust engineering over superficial prototypes. Every AI model, audio processor, and telemetry calculator must be backed by real math and unit tests.
- **Visual Excellence**: The frontend must maintain an authentic Formula 1 pit wall aesthetic with dark mode glassmorphism, responsive telemetry HUDs, and 60 FPS 3D rendering.

---

## 🌿 Branching Strategy & Workflow

1. **Fork or Create Feature Branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. **Conventional Commit Messages**:
   - `feat(asr)`: Add multi-language transcription support
   - `fix(diarizer)`: Improve cockpit SNR threshold calculation
   - `perf(3d)`: Optimize Three.js shadow maps for lower VRAM usage
   - `test(pipeline)`: Add regression test for custom audio uploads
   - `docs(readme)`: Update architecture diagram

---

## 🏗️ Architecture Conventions

- **Backend (`backend/`)**:
  - Keep modules focused on single responsibilities (`audio_processor`, `speaker_diarizer`, `asr_engine`, `stress_analyzer`, `telemetry_service`).
  - Always include type hints and docstrings.
  - Do not hardcode driver names, racing numbers, or static rules; use dynamic acoustic and NLP heuristics.
- **Frontend (`frontend/`)**:
  - Use Vanilla JS and CSS for zero-scaffolding overhead and maximum performance.
  - Keep 3D scene logic encapsulated inside `F1Scene3D` class in `frontend/js/f1_scene_3d.js`.
  - Maintain the high-contrast F1 color palette (Neon Cyan `#00F0FF`, Racing Red `#FF1801`, Amber `#FFB800`, Carbon `#080A0F`).

---

## 🧪 Testing Checklist Before Pull Requests

Before submitting a Pull Request:

1. **Run Automated Test Suite**:
   ```bash
   python -m pytest tests/test_pipeline.py -v
   ```
   *Ensure all tests pass with 0 failures.*

2. **Verify Single-Command Launch**:
   ```bash
   python run.py
   ```
   *Verify that the 3D car renders, audio plays, waveform animates, and telemetry graphs update smoothly.*

3. **Check Static Assets & 3D Models**:
   - Ensure GLB models load without 404s or console warnings.
   - Verify procedural PBR fallback remains functional if external assets are unavailable.

---

## 📬 Submitting Changes

1. Push your branch to GitHub.
2. Open a Pull Request against the `main` branch.
3. Provide a concise summary of the changes made, the motivation, and screenshots/recordings of the 3D dashboard in action.
