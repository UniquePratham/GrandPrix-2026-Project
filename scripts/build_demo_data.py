#!/usr/bin/env python3
"""Regenerate the static demo payloads from the curated radio catalog.

Writes frontend/data/clips.json, which the deployed static demo reads when the
Python AI backend is not running.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import CURATED_RADIO_CATALOG


def payload(clip):
    base = clip["base_lap_time"]
    stress = clip["stress_lap_time"]
    stressed = clip["expected_mood"] == "Stressed"

    laps = []
    for lap in range(1, 61):
        lap_time = base + (lap * 0.012)
        if lap == clip["lap"]:
            lap_time = stress
        elif lap > clip["lap"]:
            lap_time = stress - ((lap - clip["lap"]) * 0.008)
        laps.append({"lap": lap, "lap_time": round(lap_time, 3)})

    pitch = 42.5 if stressed else 8.2
    jitter = 6.8 if stressed else 1.4
    urgency = round(clip["stress_level"] / 100, 2)

    return {
        "metadata": {
            "clip_id": clip["id"],
            "driver_name": clip["driver_name"],
            "racing_number": clip["racing_number"],
            "team": clip["team"],
            "grand_prix": clip["grand_prix"],
            "year": clip["year"],
            "lap": clip["lap"],
            "total_laps": 60,
            "audio_url": clip["audio_url"],
            "transcript": clip["transcript_raw"],
        },
        "stress_analysis": {
            "mood": clip["expected_mood"],
            "stress_score": clip["stress_level"],
            "confidence": 0.94,
            "signals": {
                "pitch_shift_hz": pitch,
                "vocal_jitter_pct": jitter,
                "speech_rate_wpm": 186 if stressed else 132,
                "urgency_score": urgency,
            },
            "explanation": [
                f"Fundamental frequency rose {pitch} Hz above the driver's session baseline.",
                f"Vocal jitter measured {jitter}% — {'above' if stressed else 'within'} the calm threshold.",
                f"Linguistic urgency scored {urgency} from word choice and repetition.",
                f"Lap time lost {clip['delta']} relative to the driver's clean-air baseline.",
            ],
        },
        "telemetry": {
            "snapshot": {
                "speed_kmh": 284 if stressed else 312,
                "gear": 7,
                "rpm": 11800,
                "tire_temps_celsius": {
                    "front_left": 108,
                    "front_right": 111,
                    "rear_left": 96,
                    "rear_right": 99,
                },
            },
            "lap_times": laps,
            "delta": clip["delta"],
            "base_lap_time": base,
            "stress_lap_time": stress,
        },
        "diarization": [
            {
                "speaker": turn["speaker"],
                "role": turn["role"],
                "text": turn["text"],
                "start": turn["start"],
                "end": turn["end"],
                "stress": turn["stress"],
            }
            for turn in clip["turns"]
        ],
    }


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "frontend", "data")
    os.makedirs(out_dir, exist_ok=True)

    data = {clip["id"]: payload(clip) for clip in CURATED_RADIO_CATALOG}
    out_path = os.path.join(out_dir, "clips.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)

    print(f"wrote {len(data)} clips to {out_path}")


if __name__ == "__main__":
    main()