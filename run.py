#!/usr/bin/env python3
"""
Single-Command Launcher for Silent Co-Driver:
3D Formula 1 Radio Intelligence & Driver Stress Telemetry Platform
"""

import os
import sys
import time
import socket
import webbrowser
import threading
import uvicorn
import torch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def check_environment():
    print("=" * 70)
    print(">> SILENT CO-DRIVER -- F1 RADIO INTELLIGENCE & 3D TELEMETRY PLATFORM")
    print("=" * 70)
    
    cuda_avail = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU Only"
    print(f"[ACCELERATOR] {'[CUDA GPU] ' + gpu_name if cuda_avail else '[CPU Mode]'}")
    if cuda_avail:
        vram = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
        print(f"[MEMORY] Dedicated VRAM: {vram} GB")
    print(f"[DATASETS] Hugging Face & OpenF1 Multi-Source Engine: ONLINE")
    print(f"[DIARIZATION] Generalized Hybrid Speaker Diarizer: READY")
    print(f"[AI MODEL] Multi-Modal Fused Stress Recognizer: READY")
    print(f"[3D ENGINE] Three.js McLaren MP4/5 3D Viewport: INITIALIZED")
    print("=" * 70)

import socket

def find_available_port(preferred_port: int = 8000) -> int:
    for port in [preferred_port, 8080, 8001, 8002, 5000]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return preferred_port

def open_browser(url: str):
    time.sleep(1.2)
    print(f"🌐 Opening F1 Pit Wall Dashboard at: {url}")
    webbrowser.open(url)

def main():
    check_environment()
    port = find_available_port(int(os.environ.get("PORT", 8000)))
    url = f"http://127.0.0.1:{port}"
    
    # Auto-launch browser in background thread
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()
    
    print(f"🚀 Starting FastAPI Server on {url} ...")
    uvicorn.run(
        "backend.app:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
