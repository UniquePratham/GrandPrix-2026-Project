from __future__ import annotations

import math
from typing import Dict, List, Any, Optional
from backend.config import CURATED_RADIO_CATALOG


class TelemetryService:
    """F1 Telemetry correlation service mapping radio stress events to lap performance and car metrics."""

    def __init__(self):
        pass

    def get_session_telemetry(
        self,
        session_id: str = "ham_monaco_stress",
        stress_level: float = 85.0,
        mood: str = "Stressed",
    ) -> Dict[str, Any]:
        """Generates comprehensive lap-by-lap telemetry and correlates stress impact on lap times."""
        # Find matching curated catalog item if available
        matched_item = None
        for item in CURATED_RADIO_CATALOG:
            if item["id"] == session_id:
                matched_item = item
                break

        driver_name = matched_item["driver_name"] if matched_item else "Lewis Hamilton"
        racing_number = matched_item["racing_number"] if matched_item else "44"
        grand_prix = matched_item["grand_prix"] if matched_item else "Monaco Grand Prix"
        target_lap = matched_item["lap"] if matched_item else 48
        base_lap_time = matched_item["base_lap_time"] if matched_item else 74.25

        # Compute dynamic degradation delta based on stress score
        # High stress (>70%) yields +0.8s to +1.8s lap penalty
        # Calm (<35%) yields optimal pace (< +0.1s delta)
        # Tired (35-70%) yields steady degradation (+0.5s to +1.0s)
        if mood == "Stressed":
            delta_seconds = round(0.4 + (stress_level / 100.0) * 1.3, 2)
        elif mood == "Tired":
            delta_seconds = round(0.3 + (stress_level / 100.0) * 0.9, 2)
        else:
            delta_seconds = round(0.02 + (stress_level / 100.0) * 0.15, 2)

        # Generate 60-lap race progression
        lap_data: List[Dict[str, Any]] = []
        for lap_num in range(1, 61):
            tire_age = (lap_num % 24) + 1
            # Normal lap time curve with tire degradation
            degradation = tire_age * 0.035
            lap_noise = math.sin(lap_num * 0.7) * 0.15
            current_lap_time = base_lap_time + degradation + lap_noise

            # Inject radio stress event at target lap window
            radio_event_here = False
            lap_stress = 15.0 + (tire_age * 0.8)
            if target_lap - 2 <= lap_num <= target_lap + 2:
                radio_event_here = True
                lap_stress = stress_level
                if lap_num == target_lap:
                    current_lap_time += delta_seconds
                else:
                    current_lap_time += delta_seconds * 0.6

            lap_data.append({
                "lap": lap_num,
                "lap_time": round(current_lap_time, 3),
                "sector_1": round(current_lap_time * 0.315, 3),
                "sector_2": round(current_lap_time * 0.395, 3),
                "sector_3": round(current_lap_time * 0.290, 3),
                "stress_index": round(lap_stress, 1),
                "tire_age": tire_age,
                "tire_wear_pct": min(100, int(tire_age * 4.2)),
                "has_radio_event": radio_event_here,
            })

        # Instantaneous 3D Car Telemetry Snapshot for the radio moment
        tire_temp_base = 98.0 if mood == "Calm" else (118.5 if mood == "Stressed" else 104.0)
        telemetry_snapshot = {
            "driver_name": driver_name,
            "racing_number": racing_number,
            "grand_prix": grand_prix,
            "current_lap": target_lap,
            "speed_kmh": 284 if mood != "Stressed" else 268,
            "gear": 7 if mood != "Stressed" else 6,
            "rpm": 11450 if mood != "Stressed" else 10800,
            "throttle_pct": 98 if mood == "Calm" else 82,
            "brake_pct": 0,
            "ers_deployment_pct": 68,
            "tire_compound": "SOFT" if "Monaco" in grand_prix else "MEDIUM",
            "tire_temps_celsius": {
                "front_left": round(tire_temp_base + 3.2, 1),
                "front_right": round(tire_temp_base + 1.8, 1),
                "rear_left": round(tire_temp_base + 5.6, 1),
                "rear_right": round(tire_temp_base + 4.9, 1),
            },
            "pace_loss_delta": f"+{delta_seconds:.2f}s",
            "pace_status": "CRITICAL DEGRADATION" if delta_seconds > 0.9 else ("NOMINAL" if delta_seconds < 0.25 else "MILD DEGRADATION"),
        }

        return {
            "snapshot": telemetry_snapshot,
            "lap_history": lap_data,
            "radio_lap": target_lap,
            "correlation_summary": {
                "lap_delta_penalty": f"+{delta_seconds:.2f}s",
                "worst_sector": "Sector 2 (Technical Section)" if "Monaco" in grand_prix else "Sector 3 (Traction Zone)",
                "recommended_action": "Pit for new compound within 2 laps" if mood == "Stressed" else ("Maintain delta and manage cooling" if mood == "Tired" else "Maintain current pace target"),
            },
        }
