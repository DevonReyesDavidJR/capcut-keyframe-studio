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
    def preset_flash_in_out(
        cls,
        rush_speed: float = 4.0,
        normal_speed: float = 1.0,
        rush_ratio: float = 0.2
    ) -> Dict[str, Any]:
        """
        Flash In / Out: Rushes in -> normal pace in the middle -> rushes out.
        """
        pts = [
            {"x": 0.0, "y": rush_speed},
            {"x": rush_ratio, "y": normal_speed},
            {"x": 1.0 - rush_ratio, "y": normal_speed},
            {"x": 1.0, "y": rush_speed}
        ]
        return cls.create_speed_material("Flash in out", pts)

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

    # ==========================================
    # APPLYING SPEED TO A SEGMENT (WITH TIMELINE RIPPLE)
    # ==========================================

    @classmethod
    def create_normal_speed_material(cls) -> Dict[str, Any]:
        """Constant 1.0x speed material, as CapCut creates for an untouched clip."""
        return {
            "id": cls.generate_uuid(),
            "type": "speed",
            "mode": 0,
            "speed": 1.0,
            "curve_speed": None
        }

    @classmethod
    def apply_speed_material(
        cls,
        data: Dict[str, Any],
        track: Dict[str, Any],
        segment_index: int,
        speed_mat: Dict[str, Any]
    ) -> int:
        """
        Attaches speed_mat to the segment, replacing its previous speed material, recomputes
        the segment's target duration and ripples later clips on the same track so the
        timeline stays gap-free and non-overlapping. Returns the duration change in us.
        """
        seg = track["segments"][segment_index]
        speeds = data.setdefault("materials", {}).setdefault("speeds", [])
        speed_ids = {s.get("id") for s in speeds}

        refs = seg.get("extra_material_refs", []) or []
        old_speed_refs = [r for r in refs if r in speed_ids]
        seg["extra_material_refs"] = [r for r in refs if r not in speed_ids] + [speed_mat["id"]]
        speeds.append(speed_mat)
        cls._prune_unreferenced_speeds(data, old_speed_refs)

        seg["speed"] = speed_mat["speed"]
        target = seg.setdefault("target_timerange", {"start": 0, "duration": 0})
        src_dur = (seg.get("source_timerange") or {}).get("duration") or target.get("duration", 0)
        new_dur = max(1, int(round(src_dur / max(0.01, speed_mat["speed"]))))
        return cls._resize_segment_with_ripple(data, track, segment_index, new_dur)

    @classmethod
    def reset_segment_speed(cls, data: Dict[str, Any], track: Dict[str, Any], segment_index: int) -> int:
        """Puts the segment back on a constant 1.0x speed material (keeps a valid speed ref)."""
        return cls.apply_speed_material(data, track, segment_index, cls.create_normal_speed_material())

    @staticmethod
    def _prune_unreferenced_speeds(data: Dict[str, Any], candidate_ids: List[str]) -> None:
        """Removes speed materials from candidate_ids that no segment references anymore."""
        if not candidate_ids:
            return
        still_used = set()
        for trk in data.get("tracks", []):
            for s in trk.get("segments", []):
                still_used.update(s.get("extra_material_refs", []) or [])
        drop = set(candidate_ids) - still_used
        if drop:
            materials = data.get("materials", {})
            materials["speeds"] = [m for m in materials.get("speeds", []) if m.get("id") not in drop]

    @staticmethod
    def _resize_segment_with_ripple(
        data: Dict[str, Any],
        track: Dict[str, Any],
        segment_index: int,
        new_duration_us: int
    ) -> int:
        """
        Sets a segment's target duration, rescales its keyframes to the new length,
        shifts every later clip on the track by the same delta and updates the
        project duration. Returns the delta in us.
        """
        segs = track.get("segments", [])
        seg = segs[segment_index]
        target = seg["target_timerange"]
        old_start = target.get("start", 0)
        old_dur = target.get("duration", 0)
        old_end = old_start + old_dur
        delta = new_duration_us - old_dur
        target["duration"] = new_duration_us

        # Keep the clip's own keyframes inside (and proportional to) its new length
        if old_dur > 0:
            ratio = new_duration_us / float(old_dur)
            for group in seg.get("common_keyframes", []) or []:
                for kf in group.get("keyframe_list", []):
                    kf["time_offset"] = min(new_duration_us, int(round(kf.get("time_offset", 0) * ratio)))

        if delta:
            for i, other in enumerate(segs):
                if i == segment_index:
                    continue
                o_range = other.get("target_timerange") or {}
                if o_range.get("start", 0) >= old_end - 1000:  # 1ms tolerance for rounding
                    o_range["start"] = max(0, o_range.get("start", 0) + delta)

        project_end = 0
        for trk in data.get("tracks", []):
            for s in trk.get("segments", []):
                r = s.get("target_timerange") or {}
                project_end = max(project_end, r.get("start", 0) + r.get("duration", 0))
        if project_end:
            data["duration"] = project_end
        return delta
