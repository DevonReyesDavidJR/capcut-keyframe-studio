"""
Stabilizer & Anchor Tracking Engine Module
Point-Lock Stabilization and Camera Motion Dampening for CapCut.
100% Pure Python Standard Library + Native FFmpeg (Zero external pip dependencies).
Tracks anchor point (center, face, product logo, or custom coordinate) across frames,
inverts displacement onto PositionX/PositionY keyframes, and applies auto-zoom to prevent edge clipping.
"""

import os
import math
import subprocess
import shutil
import uuid
from typing import List, Dict, Any, Optional, Tuple

class StabilizerEngine:
    """Calculates lock-point tracking & stabilization keyframes for CapCut segments."""

    @staticmethod
    def is_ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None

    @staticmethod
    def get_video_dimensions(video_path: str) -> Tuple[int, int]:
        """Probes video dimensions to preserve aspect ratio during tracking."""
        if shutil.which("ffprobe"):
            try:
                cmd = [
                    "ffprobe", "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height",
                    "-of", "csv=s=x:p=0",
                    video_path
                ]
                res = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode().strip()
                parts = res.split("x")
                if len(parts) == 2:
                    ow, oh = int(parts[0]), int(parts[1])
                    tw = 360
                    th = int(oh * (tw / float(ow)))
                    th = th if th % 2 == 0 else th + 1
                    return tw, th
            except Exception:
                pass
        return 360, 640

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
        min_zoom: float = 1.15,
        fps: int = 30
    ) -> Dict[str, Any]:
        """
        Extracts sample frames via FFmpeg rawvideo pipe, tracks the target anchor point across all frames,
        and generates inverted PositionX/PositionY keyframes + auto-zoom scale.
        """
        if not cls.is_ffmpeg_available():
            return {"status": "error", "message": "FFmpeg chưa được cài đặt trên máy của bạn."}

        if not os.path.exists(video_path):
            return {"status": "error", "message": f"Không tìm thấy file video: {video_path}"}

        duration_seconds = max(0.2, duration_seconds)
        tw, th = cls.get_video_dimensions(video_path)

        # Extract frames as raw grayscale bytes via stdout pipe (no temp files, no PIL needed)
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start_seconds:.3f}",
            "-t", f"{duration_seconds:.3f}",
            "-i", video_path,
            "-vf", f"fps={fps},scale={tw}:{th}",
            "-f", "rawvideo",
            "-pix_fmt", "gray",
            "pipe:1"
        ]

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_data, err = proc.communicate()
            if proc.returncode != 0 or not raw_data:
                return {"status": "error", "message": f"FFmpeg không thể đọc khung hình: {err.decode('utf-8', errors='ignore')}"}

            frame_size = tw * th
            total_frames = len(raw_data) // frame_size
            if total_frames < 2:
                return {"status": "error", "message": "Không thể trích xuất đủ khung hình để phân tích."}

            frames = [raw_data[i * frame_size : (i + 1) * frame_size] for i in range(total_frames)]

            # Anchor point in downscaled pixel coordinates
            anchor_x = int(anchor_x_ratio * tw)
            anchor_y = int(anchor_y_ratio * th)

            half_template = 16
            search_radius = 20

            cur_x, cur_y = anchor_x, anchor_y
            raw_displacements = [(0, 0)]  # (dx, dy) from initial anchor point

            # Track template frame-by-frame
            for i in range(1, len(frames)):
                f_prev = frames[i - 1]
                f_cur = frames[i]

                # Crop template from previous frame around current position
                t_x0 = max(0, min(tw - half_template * 2, cur_x - half_template))
                t_y0 = max(0, min(th - half_template * 2, cur_y - half_template))
                pw = half_template * 2
                ph = half_template * 2

                tpl_rows = [f_prev[(t_y0 + r) * tw + t_x0 : (t_y0 + r) * tw + t_x0 + pw] for r in range(ph)]

                best_sad = float("inf")
                best_dx, best_dy = 0, 0

                # Search around cur_x, cur_y with step=2 for high performance
                for s_dy in range(-search_radius, search_radius + 1, 2):
                    cy0 = t_y0 + s_dy
                    if cy0 < 0 or cy0 + ph > th:
                        continue
                    for s_dx in range(-search_radius, search_radius + 1, 2):
                        cx0 = t_x0 + s_dx
                        if cx0 < 0 or cx0 + pw > tw:
                            continue

                        sad = 0
                        for r in range(ph):
                            cur_row = f_cur[(cy0 + r) * tw + cx0 : (cy0 + r) * tw + cx0 + pw]
                            sad += sum(abs(a - b) for a, b in zip(tpl_rows[r], cur_row))
                            if sad >= best_sad:
                                break

                        if sad < best_sad:
                            best_sad = sad
                            best_dx = s_dx
                            best_dy = s_dy

                cur_x += best_dx
                cur_y += best_dy
                raw_displacements.append((cur_x - anchor_x, cur_y - anchor_y))

            # Convert pixel displacements to CapCut normalized coordinates:
            # PositionX: 0.0 center, +1.0 right edge, -1.0 left edge (relative to half width)
            # PositionY: 0.0 center, +1.0 top edge, -1.0 bottom edge (inverted Y)
            capcut_x_offsets = [dx / (tw / 2.0) for dx, dy in raw_displacements]
            capcut_y_offsets = [-dy / (th / 2.0) for dx, dy in raw_displacements]

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
                    "id": cls.generate_uuid(),
                    "curveType": "FreeCurveInOut",
                    "time_offset": t_us,
                    "left_control": {"x": 0.0, "y": 0.0},
                    "right_control": {"x": float(frame_step_us * 0.35), "y": 0.0},
                    "values": [round(comp_x[idx], 4)],
                    "string_value": "",
                    "graphID": ""
                })
                pos_y_kfs.append({
                    "id": cls.generate_uuid(),
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
                    "id": cls.generate_uuid(),
                    "curveType": "Line",
                    "time_offset": 0,
                    "left_control": {"x": 0.0, "y": 0.0},
                    "right_control": {"x": 0.0, "y": 0.0},
                    "values": [final_zoom],
                    "string_value": "",
                    "graphID": ""
                },
                {
                    "id": cls.generate_uuid(),
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
                "total_frames_tracked": total_frames,
                "duration_seconds": round(duration_seconds, 3),
                "auto_zoom": final_zoom,
                "max_deviation_x": round(max_dev_x, 4),
                "max_deviation_y": round(max_dev_y, 4),
                "stabilize_mode": stabilize_mode,
                "keyframes": [
                    {
                        "id": cls.generate_uuid(),
                        "material_id": "",
                        "property_type": "KFTypePositionX",
                        "keyframe_list": pos_x_kfs
                    },
                    {
                        "id": cls.generate_uuid(),
                        "material_id": "",
                        "property_type": "KFTypePositionY",
                        "keyframe_list": pos_y_kfs
                    },
                    {
                        "id": cls.generate_uuid(),
                        "material_id": "",
                        "property_type": "KFTypeScaleX",
                        "keyframe_list": scale_kfs
                    }
                ]
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def generate_uuid() -> str:
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
