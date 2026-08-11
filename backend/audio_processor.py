from __future__ import annotations

import io
import wave
import numpy as np
import scipy.signal
from pathlib import Path
from typing import Dict, Tuple, Any, List, Union


class AudioProcessor:
    """Acoustic feature extractor and audio normalizer optimized for motorsport radio communications."""

    TARGET_SAMPLE_RATE = 16000

    @classmethod
    def load_audio(cls, source: Union[str, Path, bytes]) -> Tuple[np.ndarray, int]:
        """Loads and converts audio to a 16kHz float32 mono numpy array [-1.0, 1.0]."""
        sr = cls.TARGET_SAMPLE_RATE
        n_channels = 1
        sampwidth = 2
        raw_bytes = b""

        try:
            if isinstance(source, (str, Path)):
                with wave.open(str(source), "rb") as wf:
                    sr = wf.getframerate()
                    n_channels = wf.getnchannels()
                    sampwidth = wf.getsampwidth()
                    n_frames = wf.getnframes()
                    raw_bytes = wf.readframes(n_frames)
            elif isinstance(source, bytes):
                with wave.open(io.BytesIO(source), "rb") as wf:
                    sr = wf.getframerate()
                    n_channels = wf.getnchannels()
                    sampwidth = wf.getsampwidth()
                    n_frames = wf.getnframes()
                    raw_bytes = wf.readframes(n_frames)
        except Exception:
            # Fallback: Read raw bytes directly as int16 PCM
            if isinstance(source, (str, Path)):
                with open(str(source), "rb") as f:
                    raw_bytes = f.read()
            elif isinstance(source, bytes):
                raw_bytes = source
            sr = cls.TARGET_SAMPLE_RATE
            n_channels = 1
            sampwidth = 2

        # Decode PCM
        if sampwidth == 2:
            audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 1:
            audio = (np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        elif sampwidth == 4:
            audio = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            audio = np.frombuffer(raw_bytes, dtype=np.float32)

        # Multi-channel to mono
        if n_channels > 1:
            audio = audio.reshape(-1, n_channels).mean(axis=1)

        # Resample to 16kHz if needed
        if sr != cls.TARGET_SAMPLE_RATE:
            num_target_samples = int(len(audio) * cls.TARGET_SAMPLE_RATE / sr)
            audio = scipy.signal.resample(audio, num_target_samples)
            sr = cls.TARGET_SAMPLE_RATE

        # Peak normalization
        max_val = np.max(np.abs(audio))
        if max_val > 1e-5:
            audio = audio / max_val * 0.95

        return audio.astype(np.float32), sr

    @classmethod
    def extract_acoustic_features(cls, audio: np.ndarray, sr: int = 16000) -> Dict[str, Any]:
        """Computes comprehensive acoustic, pitch, and cockpit noise features for stress and speaker analysis."""
        if len(audio) == 0:
            return {
                "rms_energy": 0.0,
                "f0_mean": 0.0,
                "f0_std": 0.0,
                "jitter": 0.0,
                "spectral_centroid": 0.0,
                "snr_db": 20.0,
                "cockpit_noise_ratio": 0.0,
            }

        # 1. RMS Energy
        frame_len = int(0.025 * sr)  # 25ms
        hop_len = int(0.010 * sr)    # 10ms
        num_frames = max(1, (len(audio) - frame_len) // hop_len + 1)
        
        rms_frames = []
        for i in range(num_frames):
            frame = audio[i * hop_len : i * hop_len + frame_len]
            rms_frames.append(np.sqrt(np.mean(frame**2) + 1e-8))
        rms_energy = float(np.mean(rms_frames))

        # 2. Pitch (F0) estimation via Short-Time Autocorrelation
        f0_list = []
        min_lag = int(sr / 400.0)  # Max 400 Hz
        max_lag = int(sr / 75.0)   # Min 75 Hz

        for i in range(0, num_frames, 2):  # Every 20ms
            frame = audio[i * hop_len : i * hop_len + frame_len]
            if np.max(np.abs(frame)) < 0.05:
                continue
            corr = np.correlate(frame, frame, mode="full")
            corr = corr[len(frame) - 1 :]
            if len(corr) > max_lag:
                search_region = corr[min_lag:max_lag]
                if len(search_region) > 0 and np.max(search_region) > 0.3 * corr[0]:
                    peak_lag = min_lag + np.argmax(search_region)
                    f0 = sr / float(peak_lag)
                    f0_list.append(f0)

        f0_mean = float(np.mean(f0_list)) if f0_list else 150.0
        f0_std = float(np.std(f0_list)) if len(f0_list) > 1 else 10.0

        # Pitch Jitter (period perturbation)
        if len(f0_list) > 2:
            diffs = np.abs(np.diff(f0_list))
            jitter = float(np.mean(diffs) / (f0_mean + 1e-6))
        else:
            jitter = 0.02

        # 3. Spectral Centroid & Cockpit Low-Frequency Engine Drone (<350Hz)
        freqs, psd = scipy.signal.welch(audio, fs=sr, nperseg=min(512, len(audio)))
        psd_norm = psd / (np.sum(psd) + 1e-12)
        spectral_centroid = float(np.sum(freqs * psd_norm))

        # Cockpit noise ratio (Energy in 80-400Hz engine combustion band vs high band)
        low_band_mask = (freqs >= 80) & (freqs <= 400)
        high_band_mask = (freqs > 400) & (freqs <= 4000)
        low_energy = np.sum(psd[low_band_mask]) + 1e-10
        high_energy = np.sum(psd[high_band_mask]) + 1e-10
        cockpit_noise_ratio = float(low_energy / (high_energy + 1e-6))

        # Estimated SNR
        sorted_rms = np.sort(rms_frames)
        noise_floor = np.mean(sorted_rms[: max(1, int(len(sorted_rms) * 0.15))]) + 1e-6
        signal_peak = np.mean(sorted_rms[int(len(sorted_rms) * 0.85) :]) + 1e-6
        snr_db = float(20 * np.log10(signal_peak / noise_floor))

        return {
            "rms_energy": round(rms_energy, 4),
            "f0_mean": round(f0_mean, 2),
            "f0_std": round(f0_std, 2),
            "jitter": round(jitter, 4),
            "spectral_centroid": round(spectral_centroid, 1),
            "cockpit_noise_ratio": round(cockpit_noise_ratio, 3),
            "snr_db": round(snr_db, 2),
        }

    @classmethod
    def segment_speech_turns(cls, audio: np.ndarray, sr: int = 16000) -> List[Dict[str, Any]]:
        """Segments audio into speech turns using energy thresholding and silence gap detection."""
        duration = len(audio) / sr
        frame_len = int(0.05 * sr)  # 50ms frames
        hop_len = int(0.025 * sr)   # 25ms step
        num_frames = (len(audio) - frame_len) // hop_len + 1

        energies = []
        for i in range(num_frames):
            frame = audio[i * hop_len : i * hop_len + frame_len]
            energies.append(np.sum(frame**2))

        energies = np.array(energies)
        thresh = np.percentile(energies, 35) + 1e-5
        active = energies > thresh

        # Smooth activity
        kernel = np.ones(5) / 5.0
        smoothed = np.convolve(active.astype(float), kernel, mode="same") > 0.4

        segments = []
        in_seg = False
        start_t = 0.0

        for i, is_act in enumerate(smoothed):
            t = (i * hop_len) / sr
            if is_act and not in_seg:
                in_seg = True
                start_t = t
            elif not is_act and in_seg:
                # Require at least 0.4s segment
                if t - start_t >= 0.4:
                    segments.append({"start": round(start_t, 2), "end": round(t, 2)})
                in_seg = False

        if in_seg and (duration - start_t >= 0.4):
            segments.append({"start": round(start_t, 2), "end": round(duration, 2)})

        # Fallback if no clean segmentation
        if not segments:
            segments.append({"start": 0.0, "end": round(duration, 2)})

        return segments
