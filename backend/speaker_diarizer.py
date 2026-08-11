from __future__ import annotations

import re
import numpy as np
from typing import Dict, List, Any, Optional
from backend.audio_processor import AudioProcessor


class SpeakerDiarizer:
    """Generalized hybrid acoustic-semantic speaker separation engine distinguishing Driver vs. Pit Wall Engineer."""

    # Lexicon patterns for semantic attribution
    ENGINEER_PATTERNS = [
        r"\bbox\b", r"\bcopy\b", r"\bstrat\b", r"\bmode\b", r"\bdelta\b",
        r"\bgap\b", r"\bconfirm\b", r"\baffirm\b", r"\bunderstood\b",
        r"\bfail\b", r"\bdefault\b", r"\bscenario\b", r"\bmgu-?k\b",
        r"\blap\s+\d+", r"\blaps\s+to\s+go\b", r"\bbono\b", r"\bxavi\b", r"\bgp\b",
    ]

    DRIVER_PATTERNS = [
        r"\btyres?\b", r"\btires?\b", r"\bdead\b", r"\bno\s+grip\b",
        r"\bno\s+power\b", r"\bloss\s+of\b", r"\bhe\s+is\b", r"\bthey\s+are\b",
        r"\bgearbox\b", r"\bbalance\b", r"\bundersteer\b", r"\boversteer\b",
        r"\bneck\b", r"\bpuncture\b", r"\bpushing\b", r"\bintermediate\b",
        r"\binters\b", r"\bslicks\b", r"\bcheck\b", r"\bmate\b", r"\bguys\b",
        r"\bwhat\s+are\s+we\b", r"\bleave\s+me\b", r"\bkilling\s+me\b",
    ]

    def __init__(self):
        self.eng_regex = [re.compile(p, re.IGNORECASE) for p in self.ENGINEER_PATTERNS]
        self.drv_regex = [re.compile(p, re.IGNORECASE) for p in self.DRIVER_PATTERNS]

    def diarize(
        self,
        audio: np.ndarray,
        sr: int = 16000,
        whisper_segments: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Performs speaker diarization returning segmented turns labeled with Driver or Pit Wall."""
        duration = len(audio) / sr

        # If whisper segments provided with timestamps, use them; otherwise use acoustic VAD
        if whisper_segments and len(whisper_segments) > 0:
            raw_turns = whisper_segments
        else:
            vad_segments = AudioProcessor.segment_speech_turns(audio, sr)
            raw_turns = [{"start": s["start"], "end": s["end"], "text": ""} for s in vad_segments]

        diarized_turns = []
        for i, turn in enumerate(raw_turns):
            start_s = max(0.0, turn.get("start", 0.0))
            end_s = min(duration, turn.get("end", duration))
            text = turn.get("text", "").strip()

            # Slice audio segment for acoustic analysis
            start_idx = int(start_s * sr)
            end_idx = int(end_s * sr)
            turn_audio = audio[start_idx:end_idx] if end_idx > start_idx else audio

            acoustic = AudioProcessor.extract_acoustic_features(turn_audio, sr)

            # Scoring: Driver vs Engineer
            driver_score = 0.5  # Neutral prior

            # 1. Acoustic Cockpit Engine Noise vs Pit Wall Headset
            # Driver cockpit has high low-frequency energy (ratio > 1.2) and lower SNR (< 15dB)
            if acoustic["cockpit_noise_ratio"] > 1.35:
                driver_score += 0.25
            elif acoustic["cockpit_noise_ratio"] < 0.9:
                driver_score -= 0.25

            if acoustic["snr_db"] < 13.0:
                driver_score += 0.15
            elif acoustic["snr_db"] > 18.0:
                driver_score -= 0.20

            # Pitch elevation (Drivers under G-force/strain typically display higher F0 variance)
            if acoustic["f0_std"] > 25.0:
                driver_score += 0.10

            # 2. Semantic Analysis
            if text:
                drv_hits = sum(1 for rgx in self.drv_regex if rgx.search(text))
                eng_hits = sum(1 for rgx in self.eng_regex if rgx.search(text))
                driver_score += drv_hits * 0.35
                driver_score -= eng_hits * 0.35

            # First turn in F1 radio exchange is usually Driver initiating report or Engineer calling strategy
            # Clamp score
            driver_score = max(0.05, min(0.95, driver_score))

            is_driver = driver_score >= 0.5
            role = "driver" if is_driver else "engineer"
            speaker_label = "Driver" if is_driver else "Pit Wall"
            confidence = driver_score if is_driver else (1.0 - driver_score)

            diarized_turns.append({
                "turn_index": i + 1,
                "speaker": speaker_label,
                "role": role,
                "start": round(start_s, 2),
                "end": round(end_s, 2),
                "text": text,
                "confidence": round(confidence, 3),
                "acoustic_profile": {
                    "snr_db": acoustic["snr_db"],
                    "cockpit_noise_ratio": acoustic["cockpit_noise_ratio"],
                    "f0_mean": acoustic["f0_mean"],
                    "f0_std": acoustic["f0_std"],
                },
            })

        return diarized_turns
