# 🛠️ Environment Setup & Installation Guide

This guide provides step-by-step instructions to set up, configure, and run **Silent Co-Driver** on Windows, Linux, and cloud environments (such as Vultr GPU/CPU instances).

---

## 📋 System Prerequisites

| Component | Recommended Specification | Minimum Specification |
| :--- | :--- | :--- |
| **Operating System** | Windows 10/11 or Ubuntu 22.04+ | Any standard 64-bit OS |
| **Python** | Python 3.10 – 3.14 | Python 3.9+ |
| **Hardware / GPU** | NVIDIA GeForce RTX (e.g., RTX 4050 6GB) | Modern multi-core CPU |
| **RAM** | 16 GB | 8 GB |
| **Disk Space** | 2 GB available | 1 GB available |

---

## ⚡ Quickstart Installation

### 1. Clone or Open the Repository
```bash
git clone https://github.com/UniquePratham/silent-co-driver.git
cd silent-co-driver
```

### 2. Create and Activate a Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

#### Standard Installation (with PyTorch):
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### For CUDA GPU Acceleration (NVIDIA RTX / CUDA 12.x):
If your machine has an NVIDIA GPU, ensure PyTorch with CUDA support is installed:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
```

---

## 🚀 Running the Application

### Single-Command Launch:
```powershell
python run.py
```

- Hardware detection will print your GPU/CPU configuration.
- The FastAPI backend will start on `http://127.0.0.1:8000`.
- The 3D Pit Wall Dashboard will automatically open in your default browser.

### Manual Server Launch:
```bash
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```
Then navigate to `http://127.0.0.1:8000` in Google Chrome, Edge, or Firefox.

---

## 🧪 Running Automated Tests

Run the full verification suite using `pytest`:

```bash
python -m pytest tests/test_pipeline.py -v
```

All 10 tests should pass, verifying:
- Multi-source dataset ingestion (OpenF1 & Hugging Face).
- 16kHz audio normalization and acoustic feature extraction.
- Speaker diarization (Driver 🏎️ vs. Pit Wall 🎧).
- Whisper ASR transcription on GPU/CPU.
- Fused Stress Recognition (`CALM`, `TIRED`, `STRESSED`).
- Lap pace telemetry correlation.
- FastAPI REST endpoints and 3D asset serving.

---

## 🌐 Deploying to Cloud (e.g., Vultr / Hugging Face Spaces)

### Deploying to Hugging Face Spaces:
1. Create a new Space on [huggingface.co/spaces](https://huggingface.co/spaces) selecting the **Docker** or **Gradio/FastAPI** SDK.
2. Push repository files to the Space git remote.
3. The FastAPI app and static 3D frontend will run natively.

### Running with Docker:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t f1-silent-codriver .
docker run -p 8000:8000 f1-silent-codriver
```
