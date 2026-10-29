"""
AI Frame Inspector Module
Analyzes keyframe animations frame-by-frame (at 30fps/60fps) to detect motion jerkiness,
acceleration anomalies, beat misalignment, and visual clipping.
Provides AI diagnostic scores and automated frame trajectory optimization.
"""

import math
from typing import List, Dict, Any, Optional, Tuple

class FrameAIInspector:
    """Frame-by-frame motion analyzer and AI assistant."""

    @classmethod
    def evaluate_keyframes_at_frame(
        cls,
        keyframe_list: List[Dict[str, Any]],
        time_offset_us: int
    ) -> float:
        """
        Calculates interpolated property value at an exact microsecond timestamp.
        Supports linear and Bezier FreeCurveInOut curves.
        """
        if not keyframe_list:
            return 0.0

        # Sort keyframes by time
        sorted_kfs = sorted(keyframe_list, key=lambda k: k.get("time_offset", 0))

        # Boundary checks
        if time_offset_us <= sorted_kfs[0]["time_offset"]:
            return float(sorted_kfs[0].get("values", [0.0])[0])
        if time_offset_us >= sorted_kfs[-1]["time_offset"]:
            return float(sorted_kfs[-1].get("values", [0.0])[0])

        # Find enclosing pair
        k1 = sorted_kfs[0]
        k2 = sorted_kfs[-1]
        for i in range(len(sorted_kfs) - 1):
            if sorted_kfs[i]["time_offset"] <= time_offset_us <= sorted_kfs[i + 1]["time_offset"]:
                k1 = sorted_kfs[i]
                k2 = sorted_kfs[i + 1]
                break

        t1 = k1["time_offset"]
        t2 = k2["time_offset"]
        v1 = float(k1.get("values", [0.0])[0])
        v2 = float(k2.get("values", [0.0])[0])

        if t2 == t1:
            return v1

        progress = (time_offset_us - t1) / float(t2 - t1)

        # Check curve type
        curve_type = k1.get("curveType", "Line")
        if curve_type in ["FreeCurveInOut", "CurveInOut"]:
            # Cubic Hermite / Bezier interpolation
            # Ease-in-out S-curve factor: 3*p^2 - 2*p^3
            eased = progress * progress * (3.0 - 2.0 * progress)
            return v1 + (v2 - v1) * eased
        else:
            # Linear
            return v1 + (v2 - v1) * progress

    @classmethod
    def inspect_segment_frames(
        cls,
        segment: Dict[str, Any],
        fps: int = 30,
        beat_timestamps_us: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Performs exhaustive frame-by-frame analysis of a segment's keyframe motion.
        """
        target_range = segment.get("target_timerange", {})
        start_us = target_range.get("start", 0)
        dur_us = target_range.get("duration", 0)
        seg_end_us = start_us + dur_us

        if dur_us <= 0:
            return {"status": "error", "message": "Segment has zero duration"}

        frame_step_us = int(1_000_000 / fps)
        total_frames = max(1, int(dur_us / frame_step_us))

        # Extract property keyframes
        common_kfs = segment.get("common_keyframes", [])
        prop_map = {g.get("property_type"): g.get("keyframe_list", []) for g in common_kfs}

        pos_x_kfs = prop_map.get("KFTypePositionX", [])
        pos_y_kfs = prop_map.get("KFTypePositionY", [])
        scale_kfs = prop_map.get("KFTypeScaleX", [])
        rot_kfs = prop_map.get("KFTypeRotation", [])
        alpha_kfs = prop_map.get("KFTypeAlpha", [])

        frames_data = []
        velocities = []
        accelerations = []
        jerks = []

        # Sample values frame-by-frame
        for f_idx in range(total_frames + 1):
            t_offset = min(dur_us, f_idx * frame_step_us)
            global_t = start_us + t_offset

            x_val = cls.evaluate_keyframes_at_frame(pos_x_kfs, t_offset) if pos_x_kfs else 0.0
            y_val = cls.evaluate_keyframes_at_frame(pos_y_kfs, t_offset) if pos_y_kfs else 0.0
            scale_val = cls.evaluate_keyframes_at_frame(scale_kfs, t_offset) if scale_kfs else 1.0
            rot_val = cls.evaluate_keyframes_at_frame(rot_kfs, t_offset) if rot_kfs else 0.0
            alpha_val = cls.evaluate_keyframes_at_frame(alpha_kfs, t_offset) if alpha_kfs else 1.0

            frames_data.append({
                "frame_index": f_idx,
                "time_offset_s": round(t_offset / 1_000_000.0, 3),
                "time_offset_us": t_offset,
                "global_time_s": round(global_t / 1_000_000.0, 3),
                "position_x": round(x_val, 4),
                "position_y": round(y_val, 4),
                "scale": round(scale_val, 4),
                "rotation": round(rot_val, 2),
                "alpha": round(alpha_val, 2),
                "velocity": 0.0,
                "acceleration": 0.0,
                "status": "normal",
                "notes": []
            })

        # Calculate Velocities & Accelerations
        dt = 1.0 / fps
        for i in range(len(frames_data) - 1):
            cur = frames_data[i]
            nxt = frames_data[i + 1]
            dx = nxt["position_x"] - cur["position_x"]
            dy = nxt["position_y"] - cur["position_y"]
            ds = nxt["scale"] - cur["scale"]
            # Combined motion displacement magnitude
            disp = math.sqrt(dx * dx + dy * dy + ds * ds)
            v = disp / dt
            cur["velocity"] = round(v, 3)
            velocities.append(v)

        if len(frames_data) > 0:
            frames_data[-1]["velocity"] = 0.0

        # Calculate Acceleration
        for i in range(len(velocities) - 1):
            a = (velocities[i + 1] - velocities[i]) / dt
            frames_data[i]["acceleration"] = round(a, 2)
            accelerations.append(a)

        # AI Heuristic Anomaly Detection
        issues = []
        max_vel = max(velocities) if velocities else 0.0
        avg_vel = sum(velocities) / len(velocities) if velocities else 0.0

        for i in range(1, len(frames_data) - 1):
            frame = frames_data[i]
            prev_f = frames_data[i - 1]
            next_f = frames_data[i + 1]

            # 1. Harsh Jerk / Sudden acceleration spike check
            a_cur = abs(frame.get("acceleration", 0.0))
            if a_cur > 8.0:  # Excessive acceleration threshold
                frame["status"] = "warning"
                frame["notes"].append("Chuyển động có gia tốc tăng vọt (nguy cơ giật hình)")
                issues.append({
                    "frame": frame["frame_index"],
                    "time_s": frame["time_offset_s"],
                    "type": "jerk",
                    "severity": "medium",
                    "description": f"Frame {frame['frame_index']} có độ tăng tốc đột ngột ({a_cur:.1f}), chuyển động có thể bị gắt."
                })

            # 2. Sudden Direction Reversal (Lắc giật ngược chiều)
            vx1 = frame["position_x"] - prev_f["position_x"]
            vx2 = next_f["position_x"] - frame["position_x"]
            vy1 = frame["position_y"] - prev_f["position_y"]
            vy2 = next_f["position_y"] - frame["position_y"]

            if (vx1 * vx2 < -0.005) or (vy1 * vy2 < -0.005):
                frame["status"] = "warning"
                frame["notes"].append("Đảo chiều chuyển động đột ngột")
                issues.append({
                    "frame": frame["frame_index"],
                    "time_s": frame["time_offset_s"],
                    "type": "reversal",
                    "severity": "high",
                    "description": f"Frame {frame['frame_index']} bị khựng do đổi hướng đột ngột."
                })

            # 3. Off-screen Clipping (vượt quá màn hình quá xa khi không phải transition)
            if abs(frame["position_x"]) > 1.8 or abs(frame["position_y"]) > 2.0:
                frame["status"] = "notice"
                frame["notes"].append("Vật thể nằm hoàn toàn ngoài màn hình")

        # 4. Beat Alignment Evaluation
        beat_sync_info = {"status": "none", "score": 100}
        if beat_timestamps_us:
            # Find nearest beat to segment start or peak
            seg_beats = [b for b in beat_timestamps_us if start_us <= b <= seg_end_us]
            if seg_beats:
                # Find frame with max velocity / transition peak
                peak_frame_idx = 0
                max_v = -1
                for idx, v in enumerate(velocities):
                    if v > max_v:
                        max_v = v
                        peak_frame_idx = idx

                peak_time_us = start_us + frames_data[peak_frame_idx]["time_offset_us"]
                closest_beat = min(seg_beats, key=lambda b: abs(b - peak_time_us))
                diff_ms = round((peak_time_us - closest_beat) / 1000.0, 1)

                if abs(diff_ms) <= 40:
                    beat_sync_info = {
                        "status": "perfect",
                        "score": 100,
                        "diff_ms": diff_ms,
                        "description": f"Chuyển động khớp hoàn hảo với Beat âm thanh (lệch {diff_ms:+}ms)."
                    }
                elif abs(diff_ms) <= 90:
                    beat_sync_info = {
                        "status": "good",
                        "score": 85,
                        "diff_ms": diff_ms,
                        "description": f"Khá khớp với Beat nhạc (lệch {diff_ms:+}ms, khoảng {round(diff_ms/33.3):+} frame)."
                    }
                else:
                    beat_sync_info = {
                        "status": "misaligned",
                        "score": 60,
                        "diff_ms": diff_ms,
                        "description": f"Đỉnh chuyển động bị lệch {diff_ms:+}ms so với beat nhạc. Nên dịch chuyển {round(-diff_ms/33.3):+} frame."
                    }
                    issues.append({
                        "frame": peak_frame_idx,
                        "time_s": frames_data[peak_frame_idx]["time_offset_s"],
                        "type": "beat_mismatch",
                        "severity": "medium",
                        "description": beat_sync_info["description"]
                    })

        # Calculate Overall AI Quality Score (0 - 100)
        penalty = len([i for i in issues if i["severity"] == "high"]) * 15
        penalty += len([i for i in issues if i["severity"] == "medium"]) * 8
        if beat_sync_info.get("score"):
            score = max(20, min(100, int(100 - penalty * 0.7 - (100 - beat_sync_info["score"]) * 0.3)))
        else:
            score = max(20, min(100, 100 - penalty))

        return {
            "status": "success",
            "fps": fps,
            "total_frames": total_frames,
            "duration_seconds": round(dur_us / 1_000_000.0, 3),
            "ai_score": score,
            "beat_sync": beat_sync_info,
            "issues_count": len(issues),
            "issues": issues,
            "frames": frames_data
        }

    @classmethod
    def autofix_segment_motion(
        cls,
        segment: Dict[str, Any],
        fps: int = 30
    ) -> List[Dict[str, Any]]:
        """
        AI Auto-Tune: Replaces jittery frame points with a smooth mathematical Bezier trajectory.
        Preserves start and end poses while removing mid-flight jerkiness.
        """
        common_kfs = segment.get("common_keyframes", []) or []
        dur_us = segment.get("target_timerange", {}).get("duration", 3_000_000)

        optimized_groups = []
        for group in common_kfs:
            ptype = group.get("property_type")
            klist = group.get("keyframe_list", [])
            if len(klist) <= 2:
                optimized_groups.append(group)
                continue

            # Keep first and last, generate smooth curve
            v_start = klist[0].get("values", [0.0])[0]
            v_end = klist[-1].get("values", [0.0])[0]
            t_end = klist[-1].get("time_offset", dur_us)

            # Generate smooth Bezier with tangent handles
            tangent_dx = float(t_end * 0.4)
            smooth_kfs = [
                {
                    "id": klist[0].get("id"),
                    "curveType": "FreeCurveInOut",
                    "time_offset": 0,
                    "left_control": {"x": 0.0, "y": 0.0},
                    "right_control": {"x": tangent_dx, "y": 0.0},
                    "values": [v_start],
                    "string_value": "",
                    "graphID": ""
                },
                {
                    "id": klist[-1].get("id"),
                    "curveType": "FreeCurveInOut",
                    "time_offset": t_end,
                    "left_control": {"x": -tangent_dx, "y": 0.0},
                    "right_control": {"x": 0.0, "y": 0.0},
                    "values": [v_end],
                    "string_value": "",
                    "graphID": ""
                }
            ]

            optimized_groups.append({
                "id": group.get("id"),
                "material_id": group.get("material_id", ""),
                "property_type": ptype,
                "keyframe_list": smooth_kfs
            })

        return optimized_groups
