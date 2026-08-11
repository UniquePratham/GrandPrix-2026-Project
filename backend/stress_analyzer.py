from __future__ import annotations

import logging
import re
import numpy as np
from typing import Dict, Any, List
from backend.audio_processor import AudioProcessor

logger = logging.getLogger("StressAnalyzer")


class StressAnalyzer:
    """Multi-modal Fused Stress Recognition Engine for racing drivers."""

    # Semantic Urgency & Stress lexicons
    HIGH_STRESS_WORDS = [
        "dead", "no grip", "cannot", "destroying", "puncture", "damage", "unbelievable",
        "killing me", "disaster", "no power", "loss of", "box now", "traffic", "understeer",
        "oversteer", "crash", "off the track", "rear gone", "sliding", "impossible",
    ]

    TIRED_FATIGUE_WORDS = [
        "neck", "tired", "exhausted", "hurts", "temp", "unbearable", "struggling",
        "long stint", "heavy", "pain", "drinking", "vision", "degraded",
    ]

    CALM_WORDS = [
        "good", "balance", "smooth", "fine", "extend", "manageable", "copy",
        "understood", "happy with", "pace is good", "settled", "no problem",
    ]

    def __init__(self):
        self.high_stress_patterns = [re.compile(r"\b" + re.escape(w) + r"\b", re.IGNORECASE) for w in self.HIGH_STRESS_WORDS]
        self.fatigue_patterns = [re.compile(r"\b" + re.escape(w) + r"\b", re.IGNORECASE) for w in self.TIRED_FATIGUE_WORDS]
        self.calm_patterns = [re.compile(r"\b" + re.escape(w) + r"\b", re.IGNORECASE) for w in self.CALM_WORDS]

    def analyze_driver_stress(
        self,
        driver_audio: np.ndarray,
        sr: int = 16000,
        transcript: str = "",
        acoustic_features: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Calculates the comprehensive Fused Stress Index (FSI) for the driver's voice."""
        if acoustic_features is None:
            acoustic_features = AudioProcessor.extract_acoustic_features(driver_audio, sr)

        f0_mean = acoustic_features.get("f0_mean", 150.0)
        f0_std = acoustic_features.get("f0_std", 15.0)
        jitter = acoustic_features.get("jitter", 0.02)
        rms = acoustic_features.get("rms_energy", 0.1)

        # 1. Acoustic Prosodic Stress Score (0 - 100)
        # Baseline F0 for male/female drivers under neutral driving: ~120 - 160 Hz
        # High stress/G-force F0: > 220 - 320 Hz
        pitch_score = max(0.0, min(100.0, ((f0_mean - 120.0) / 160.0) * 100.0))
        jitter_score = max(0.0, min(100.0, (jitter / 0.12) * 100.0))
        energy_score = max(0.0, min(100.0, (rms / 0.45) * 100.0))

        acoustic_stress_score = 0.50 * pitch_score + 0.35 * jitter_score + 0.15 * energy_score

        # 2. Semantic Urgency & Linguistic Emotion Score (0 - 100)
        text = transcript or ""
        stress_hits = sum(1 for p in self.high_stress_patterns if p.search(text))
        fatigue_hits = sum(1 for p in self.fatigue_patterns if p.search(text))
        calm_hits = sum(1 for p in self.calm_patterns if p.search(text))

        semantic_stress_score = 30.0  # neutral baseline
        if stress_hits > 0:
            semantic_stress_score = min(100.0, 60.0 + (stress_hits * 18.0))
        elif fatigue_hits > 0:
            semantic_stress_score = min(80.0, 50.0 + (fatigue_hits * 14.0))
        elif calm_hits > 0:
            semantic_stress_score = max(5.0, 30.0 - (calm_hits * 12.0))

        # 3. Fused Stress Index (FSI)
        fused_stress_index = 0.55 * acoustic_stress_score + 0.45 * semantic_stress_score

        # 4. Mood Categorization & Fatigue Detection
        explanations = []
        if fatigue_hits >= 1 or (acoustic_stress_score < 40.0 and f0_mean < 130.0 and fatigue_hits > 0):
            mood = "Tired"
            fused_stress_index = max(55.0, min(78.0, fused_stress_index))
            explanations.append("Linguistic markers indicate physical exhaustion and cockpit thermal fatigue.")
            explanations.append(f"Depressed fundamental frequency ({f0_mean:.1f}Hz) and lower voice energy.")
        elif fused_stress_index >= 66.0 or stress_hits >= 1:
            mood = "Stressed"
            fused_stress_index = max(68.0, min(98.0, fused_stress_index))
            explanations.append(f"Elevated vocal pitch ({f0_mean:.1f}Hz) indicates acute physiological stress under acceleration.")
            if jitter > 0.06:
                explanations.append(f"High vocal jitter ({jitter:.3f}) correlates with respiratory strain.")
            if stress_hits > 0:
                explanations.append(f"Urgent race feedback detected in radio transcript.")
        else:
            mood = "Calm"
            fused_stress_index = max(8.0, min(35.0, fused_stress_index))
            explanations.append("Stable pitch frequency and calm communicative cadence.")
            explanations.append("No telemetry panic indicators or extreme vocal tremors.")

        confidence = round(min(0.98, max(0.72, 0.80 + (abs(fused_stress_index - 50.0) / 150.0))), 2)

        return {
            "mood": mood,
            "stress_level": round(fused_stress_index, 1),
            "confidence": confidence,
            "metrics": {
                "f0_mean_hz": round(f0_mean, 1),
                "f0_std_hz": round(f0_std, 1),
                "vocal_jitter": round(jitter, 4),
                "acoustic_stress_score": round(acoustic_stress_score, 1),
                "semantic_stress_score": round(semantic_stress_score, 1),
                "snr_db": acoustic_features.get("snr_db", 12.0),
            },
            "explanations": explanations,
        }
