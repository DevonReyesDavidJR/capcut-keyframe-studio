"""
Stabilizer & Anchor Tracking Engine Module
Point-Lock Stabilization and Camera Motion Dampening for CapCut.
Tracks anchor point (center, face, product logo, or custom coordinate) across frames,
inverts displacement onto PositionX/PositionY keyframes, and applies auto-zoom to prevent edge clipping.
"""

import os
import math
import subprocess
import tempfile
import shutil
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image

class StabilizerEngine:
    """Calculates lock-point tracking & stabilization keyframes for CapCut segments."""

    @staticmethod
    def is_ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None

    @classmethod
    def track_and_stabilize(
        cls,
        video_path: str,
        start_seconds: float = 0.0,
        duration_seconds: float = 1.0,
        anchor_x_ratio: float = 0.5,    # 0.0 (left) to 1.0 (right), 0.5 = center
        anchor_y_ratio: float = 0.5,    # 0.0 (top) to 1.0 (bottom), 0.5 = center
        stabilize_mode: str = "dead_lock", # "dead_lock" (100% lock) or "smooth" (damped pan)
        smooth_window: int = 15,
        min_zoom: float = 1.12,
        fps: int = 30
    ) -> Dict[str, Any]:
        """
        Extracts sample frames, tracks the target anchor point across all frames,
        and generates inverted PositionX/PositionY keyframes + auto-zoom scale.
        """
        if not cls.is_ffmpeg_available():
            return {"status": "error", "message": "FFmpeg chưa được cài đặt."}

        if not os.path.exists(video_path):
            return {"status": "error", "message": f"Không tìm thấy file video: {video_path}"}

        duration_seconds = max(0.2, duration_seconds)
        total_frames = max(2, int(duration_seconds * fps))

        temp_dir = tempfile.mkdtemp(prefix="capcut_stab_")
        frame_pattern = os.path.join(temp_dir, "frame_%04d.png")

        # Extract frames scaled to 360px width for fast tracking
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start_seconds:.3f}",
            "-t", f"{duration_seconds:.3f}",
            "-i", video_path,
            "-vf", f"fps={fps},scale=360:-1",
            frame_pattern
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            frame_files = sorted([os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith(".png")])
            if len(frame_files) < 2:
                return {"status": "error", "message": "Không thể trích xuất đủ khung hình để phân tích."}

            im0 = Image.open(frame_files[0]).convert("L")
            w, h = im0.size

            # Anchor point in pixels
            anchor_x = int(anchor_x_ratio * w)
            anchor_y = int(anchor_y_ratio * h)

            half_template = 18
            search_radius = 24

            cur_x, cur_y = anchor_x, anchor_y
            raw_displacements = [(0, 0)] # (dx, dy) from initial anchor point

            # Track template frame-by-frame
            for i in range(1, len(frame_files)):
                im_prev = Image.open(frame_files[i - 1]).convert("L")
                im_cur = Image.open(frame_files[i]).convert("L")

                # Crop template from previous frame around current position
                t_x1 = max(0, cur_x - half_template)
                t_y1 = max(0, cur_y - half_template)
                t_x2 = min(w, cur_x + half_template)
                t_y2 = min(h, cur_y + half_template)
                tpl = im_prev.crop((t_x1, t_y1, t_x2, t_y2)).tobytes()
                tpl_len = len(tpl)

                best_sad = float("inf")
                best_dx, best_dy = 0, 0

                # Search around cur_x, cur_y with step=2 for high speed
                for s_dy in range(-search_radius, search_radius + 1, 2):
                    for s_dx in range(-search_radius, search_radius + 1, 2):
                        c_x1 = cur_x + s_dx - half_template
                        c_y1 = cur_y + s_dy - half_template
                        c_x2 = cur_x + s_dx + half_template
                        c_y2 = cur_y + s_dy + half_template

                        if 0 <= c_x1 and c_x2 <= w and 0 <= c_y1 and c_y2 <= h:
                            patch = im_cur.crop((c_x1, c_y1, c_x2, c_y2)).tobytes()
                            if len(patch) == tpl_len:
                                # Sum of Absolute Differences
                                sad = sum(abs(a - b) for a, b in zip(tpl, patch))
                                if sad < best_sad:
                                    best_sad = sad
                                    best_dx, best_dy = s_dx, s_dy

                cur_x += best_dx
                cur_y += best_dy
                raw_displacements.append((cur_x - anchor_x, cur_y - anchor_y))

            # Convert pixel displacements to CapCut normalized coordinates
            # CapCut coordinates:
            # PositionX: 0.0 center, +1.0 right edge, -1.0 left edge (range [-1, 1] relative to half width)
            # PositionY: 0.0 center, +1.0 top edge, -1.0 bottom edge (inverted Y)
            capcut_x_offsets = [dx / (w / 2.0) for dx, dy in raw_displacements]
            capcut_y_offsets = [-dy / (h / 2.0) for dx, dy in raw_displacements]

            # Invert offsets to counter-balance motion (stabilize)
            if stabilize_mode == "dead_lock":
                # 100% lock to initial anchor point
                comp_x = [-x for x in capcut_x_offsets]
                comp_y = [-y for y in capcut_y_offsets]
            else:
                # Smooth mode: subtract smoothed trajectory to remove high frequency shakes while keeping smooth pan
                win = min(len(capcut_x_offsets), max(3, smooth_window))
                smoothed_x = cls._moving_average(capcut_x_offsets, win)
                smoothed_y = cls._moving_average(capcut_y_offsets, win)
                comp_x = [-(orig - sm) for orig, sm in zip(capcut_x_offsets, smoothed_x)]
                comp_y = [-(orig - sm) for orig, sm in zip(capcut_y_offsets, smoothed_y)]

            # Calculate required auto-zoom to prevent black edges
            max_dev_x = max(abs(x) for x in comp_x) if comp_x else 0.0
            max_dev_y = max(abs(y) for y in comp_y) if comp_y else 0.0
            needed_zoom = 1.0 + max(max_dev_x, max_dev_y) * 1.3
            final_zoom = round(max(min_zoom, needed_zoom), 3)

            # Generate CapCut keyframe points
            frame_step_us = int(1_000_000 / fps)
            pos_x_kfs = []
            pos_y_kfs = []

            for idx in range(len(comp_x)):
                t_us = min(int(duration_seconds * 1_000_000), idx * frame_step_us)
                pos_x_kfs.append({
                    "id": str(cls.generate_uuid()),
                    "curveType": "FreeCurveInOut",
                    "time_offset": t_us,
                    "left_control": {"x": 0.0, "y": 0.0},
                    "right_control": {"x": float(frame_step_us * 0.35), "y": 0.0},
                    "values": [round(comp_x[idx], 4)],
                    "string_value": "",
                    "graphID": ""
                })
                pos_y_kfs.append({
                    "id": str(cls.generate_uuid()),
                    "curveType": "FreeCurveInOut",
                    "time_offset": t_us,
                    "left_control": {"x": 0.0, "y": 0.0},
                    "right_control": {"x": float(frame_step_us * 0.35), "y": 0.0},
                    "values": [round(comp_y[idx], 4)],
                    "string_value": "",
                    "graphID": ""
                })

            scale_kfs = [
                {
                    "id": str(cls.generate_uuid()),
                    "curveType": "Line",
                    "time_offset": 0,
                    "left_control": {"x": 0.0, "y": 0.0},
                    "right_control": {"x": 0.0, "y": 0.0},
                    "values": [final_zoom],
                    "string_value": "",
                    "graphID": ""
                },
                {
                    "id": str(cls.generate_uuid()),
                    "curveType": "Line",
                    "time_offset": int(duration_seconds * 1_000_000),
                    "left_control": {"x": 0.0, "y": 0.0},
                    "right_control": {"x": 0.0, "y": 0.0},
                    "values": [final_zoom],
                    "string_value": "",
                    "graphID": ""
                }
            ]

            return {
                "status": "success",
                "total_frames_tracked": len(frame_files),
                "duration_seconds": round(duration_seconds, 3),
                "auto_zoom": final_zoom,
                "max_deviation_x": round(max_dev_x, 4),
                "max_deviation_y": round(max_dev_y, 4),
                "stabilize_mode": stabilize_mode,
                "keyframes": [
                    {
                        "id": str(cls.generate_uuid()),
                        "material_id": "",
                        "property_type": "KFTypePositionX",
                        "keyframe_list": pos_x_kfs
                    },
                    {
                        "id": str(cls.generate_uuid()),
                        "material_id": "",
                        "property_type": "KFTypePositionY",
                        "keyframe_list": pos_y_kfs
                    },
                    {
                        "id": str(cls.generate_uuid()),
                        "material_id": "",
                        "property_type": "KFTypeScaleX",
                        "keyframe_list": scale_kfs
                    }
                ]
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def generate_uuid() -> str:
        import uuid
        return str(uuid.uuid4()).upper()

    @staticmethod
    def _moving_average(data: List[float], window: int) -> List[float]:
        res = []
        half = window // 2
        for i in range(len(data)):
            p_start = max(0, i - half)
            p_end = min(len(data), i + half + 1)
            res.append(sum(data[p_start:p_end]) / float(p_end - p_start))
        return res
