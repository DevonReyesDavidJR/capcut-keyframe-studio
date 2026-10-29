"""
Speed Ramp Engine Module
Generates, transforms, and calculates CapCut curve_speed profiles.
Integrates with CapCut's materials.speeds and segment timerange systems.
"""

import uuid
import math
from typing import List, Dict, Any, Optional, Tuple

class SpeedRampEngine:
    """Core logic to construct, calculate, and apply CapCut speed curves."""

    @staticmethod
    def generate_uuid() -> str:
        return str(uuid.uuid4()).upper()

    @staticmethod
    def calculate_effective_speed(speed_points: List[Dict[str, float]]) -> float:
        """
        Calculates the effective average speed multiplier by integrating dt / v(x).
        Target Duration = Source Duration * Total Target Ratio.
        Average Speed = 1.0 / Total Target Ratio.
        """
        if not speed_points or len(speed_points) < 2:
            return 1.0

        sorted_pts = sorted(speed_points, key=lambda p: p["x"])
        total_target_ratio = 0.0

        for i in range(len(sorted_pts) - 1):
            p1 = sorted_pts[i]
            p2 = sorted_pts[i + 1]
            dx = max(0.0, p2["x"] - p1["x"])
            v1 = max(0.05, p1["y"])
            v2 = max(0.05, p2["y"])

            # Trapezoidal integration for duration contribution: integral of 1/v dx
            # If v1 == v2: dx / v1
            # If v1 != v2: ln(v2/v1) * dx / (v2 - v1)
            if abs(v2 - v1) < 1e-4:
                dt = dx / v1
            else:
                dt = (math.log(v2) - math.log(v1)) * (dx / (v2 - v1))
            total_target_ratio += dt

        if total_target_ratio <= 0.0:
            return 1.0

        return round(1.0 / total_target_ratio, 6)

    @classmethod
    def create_speed_material(
        cls,
        name: str,
        speed_points: List[Dict[str, float]],
        preset_id: str = "6768730851543880206"
    ) -> Dict[str, Any]:
        """
        Creates a CapCut material object for materials.speeds with mode=1 (curve speed).
        """
        avg_speed = cls.calculate_effective_speed(speed_points)
        return {
            "id": cls.generate_uuid(),
            "type": "speed",
            "mode": 1,
            "speed": avg_speed,
            "curve_speed": {
                "id": preset_id,
                "source_platform": 0,
                "name": name,
                "speed_points": speed_points
            }
        }

    # ==========================================
    # PRESET CURVES
    # ==========================================

    @classmethod
    def preset_hero(
        cls,
        fast_speed: float = 5.0,
        slow_speed: float = 0.4,
        slow_center_ratio: float = 0.5,
        slow_width_ratio: float = 0.3
    ) -> Dict[str, Any]:
        """
        Hero Curve: Fast entrance -> Dramatic Slow-Motion in the middle -> Fast exit.
        """
        half_w = slow_width_ratio / 2.0
        p_start_slow = max(0.05, slow_center_ratio - half_w)
        p_end_slow = min(0.95, slow_center_ratio + half_w)
        ramp_trans = 0.08

        pts = [
            {"x": 0.0, "y": fast_speed},
            {"x": max(0.0, p_start_slow - ramp_trans), "y": fast_speed},
            {"x": p_start_slow, "y": slow_speed},
            {"x": p_end_slow, "y": slow_speed},
            {"x": min(1.0, p_end_slow + ramp_trans), "y": fast_speed},
            {"x": 1.0, "y": fast_speed}
        ]
        return cls.create_speed_material("Hero", pts, preset_id="6768650238149267981")

    @classmethod
    def preset_bullet_time(
        cls,
        normal_speed: float = 1.0,
        ultra_slow: float = 0.2,
        trigger_ratio: float = 0.4,
        duration_ratio: float = 0.25
    ) -> Dict[str, Any]:
        """
        Bullet Time: Normal pace -> Instant deep slow-mo freeze -> Snaps back.
        """
        p1 = max(0.05, trigger_ratio)
        p2 = min(0.95, trigger_ratio + duration_ratio)
        trans = 0.05

        pts = [
            {"x": 0.0, "y": normal_speed},
            {"x": max(0.0, p1 - trans), "y": normal_speed},
            {"x": p1, "y": ultra_slow},
            {"x": p2, "y": ultra_slow},
            {"x": min(1.0, p2 + trans), "y": normal_speed},
            {"x": 1.0, "y": normal_speed}
        ]
        return cls.create_speed_material("Bullet", pts, preset_id="6768650238149267982")

    @classmethod
    def preset_flash_in(
        cls,
        rush_speed: float = 6.0,
        normal_speed: float = 1.0,
        rush_duration_ratio: float = 0.35
    ) -> Dict[str, Any]:
        """
        Flash In: Rockets in with extreme high speed -> settles into normal speed.
        """
        pts = [
            {"x": 0.0, "y": rush_speed},
            {"x": rush_duration_ratio * 0.7, "y": rush_speed},
            {"x": rush_duration_ratio, "y": normal_speed},
            {"x": 1.0, "y": normal_speed}
        ]
        return cls.create_speed_material("Flash in", pts, preset_id="6768731653402530307")

    @classmethod
    def preset_flash_out(
        cls,
        normal_speed: float = 1.0,
        rush_speed: float = 6.0,
        rush_start_ratio: float = 0.65
    ) -> Dict[str, Any]:
        """
        Flash Out: Normal pace -> Rockets out at high speed into the next cut.
        """
        pts = [
            {"x": 0.0, "y": normal_speed},
            {"x": rush_start_ratio, "y": normal_speed},
            {"x": rush_start_ratio + (1.0 - rush_start_ratio) * 0.3, "y": rush_speed},
            {"x": 1.0, "y": rush_speed}
        ]
        return cls.create_speed_material("Flash out", pts, preset_id="6768731653402530308")

    @classmethod
    def preset_jump_cut(
        cls,
        fast_speed: float = 4.5,
        normal_speed: float = 1.0
    ) -> Dict[str, Any]:
        """
        Jump Cut: Fast pulses with sudden drops.
        """
        pts = [
            {"x": 0.0, "y": fast_speed},
            {"x": 0.3, "y": normal_speed},
            {"x": 0.45, "y": fast_speed},
            {"x": 0.75, "y": fast_speed},
            {"x": 0.85, "y": normal_speed},
            {"x": 1.0, "y": normal_speed}
        ]
        return cls.create_speed_material("Jump cut", pts, preset_id="6768731594225095175")

    @classmethod
    def preset_montage(
        cls,
        peak_speed: float = 6.0,
        dip_speed: float = 0.3
    ) -> Dict[str, Any]:
        """
        Montage: Smooth undulating rhythm wave.
        """
        pts = [
            {"x": 0.0, "y": 2.0},
            {"x": 0.5, "y": peak_speed},
            {"x": 0.8, "y": dip_speed},
            {"x": 1.0, "y": 1.0}
        ]
        return cls.create_speed_material("Montage", pts, preset_id="6768648600848175619")

    # ==========================================
    # BEAT-SYNCED SPEED RAMP
    # ==========================================

    @classmethod
    def generate_beat_speed_ramp(
        cls,
        segment_start_us: int,
        segment_source_duration_us: int,
        beat_timestamps_us: List[int],
        fast_speed: float = 4.0,
        slow_speed: float = 0.35,
        slow_window_ms: int = 150
    ) -> Dict[str, Any]:
        """
        Generates a custom speed curve matching audio beats:
        Runs at fast_speed in between beats, dips into dramatic slow_speed right on each beat hit!
        """
        seg_end_us = segment_start_us + segment_source_duration_us
        relevant_beats = [b - segment_start_us for b in beat_timestamps_us if segment_start_us <= b <= seg_end_us]

        if not relevant_beats:
            # Fallback to standard Hero curve if no beats found
            return cls.preset_hero(fast_speed=fast_speed, slow_speed=slow_speed)

        slow_us = slow_window_ms * 1000
        dur_us = float(segment_source_duration_us)

        pts = [{"x": 0.0, "y": fast_speed}]

        for b_t in relevant_beats:
            norm_b = b_t / dur_us
            norm_w = (slow_us / 2.0) / dur_us

            t_start = max(0.01, norm_b - norm_w)
            t_end = min(0.99, norm_b + norm_w)

            pts.append({"x": round(max(0.0, t_start - 0.04), 4), "y": fast_speed})
            pts.append({"x": round(t_start, 4), "y": slow_speed})
            pts.append({"x": round(t_end, 4), "y": slow_speed})
            pts.append({"x": round(min(1.0, t_end + 0.04), 4), "y": fast_speed})

        pts.append({"x": 1.0, "y": fast_speed})

        # Deduplicate & ensure strictly ascending x
        clean_pts = []
        last_x = -1.0
        for p in sorted(pts, key=lambda x: x["x"]):
            if p["x"] > last_x + 0.005:
                clean_pts.append(p)
                last_x = p["x"]

        if clean_pts[-1]["x"] < 1.0:
            clean_pts.append({"x": 1.0, "y": fast_speed})

        return cls.create_speed_material("Beat Ramp", clean_pts)

