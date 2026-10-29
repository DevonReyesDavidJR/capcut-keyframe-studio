"""
Filmstrip & Contact Sheet Generator Module
Extracts video frames and stitches them into a SINGLE combined PNG contact sheet
using FFmpeg tile filter. Lightweight, zero disk clutter (~200KB per preview).
"""

import os
import shutil
import subprocess
from typing import Dict, Any, Optional, List

class FilmstripGenerator:
    """Generates a single stitched contact sheet / filmstrip image for rhythm review."""

    @staticmethod
    def is_ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None

    @classmethod
    def generate_filmstrip(
        cls,
        video_path: str,
        start_seconds: float = 0.0,
        duration_seconds: float = 1.0,
        cols: int = 5,
        rows: int = 2,
        tile_width: int = 200,
        output_png_path: str = "/tmp/capcut_filmstrip.png"
    ) -> Dict[str, Any]:
        """
        Extracts frames across the duration and merges them into 1 single PNG contact sheet.
        """
        if not cls.is_ffmpeg_available():
            return {
                "status": "error",
                "message": "FFmpeg chưa được cài đặt trên hệ thống."
            }

        if not os.path.exists(video_path):
            return {
                "status": "error",
                "message": f"Không tìm thấy file video nguồn: {video_path}"
            }

        duration_seconds = max(0.1, duration_seconds)
        total_tiles = cols * rows
        # Compute exact sampling fps to yield exactly total_tiles across the duration
        sample_fps = total_tiles / float(duration_seconds)

        # Video filter: sample fps -> scale tile width -> tile into grid
        vf_filter = f"fps={sample_fps:.3f},scale={tile_width}:-1,tile={cols}x{rows}"

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start_seconds:.3f}",
            "-t", f"{duration_seconds:.3f}",
            "-i", video_path,
            "-vf", vf_filter,
            "-frames:v", "1",
            output_png_path
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if not os.path.exists(output_png_path):
                return {"status": "error", "message": "Lỗi khi tạo ảnh filmstrip"}

            file_size_kb = round(os.path.getsize(output_png_path) / 1024.0, 1)

            # Generate frame timestamp breakdown
            frame_metadata = []
            step_s = duration_seconds / float(total_tiles)
            for idx in range(total_tiles):
                t_s = start_seconds + idx * step_s
                c = idx % cols
                r = idx // cols
                frame_metadata.append({
                    "index": idx + 1,
                    "time_s": round(t_s, 3),
                    "col": c,
                    "row": r
                })

            return {
                "status": "success",
                "file_path": output_png_path,
                "file_size_kb": file_size_kb,
                "cols": cols,
                "rows": rows,
                "total_tiles": total_tiles,
                "duration_seconds": round(duration_seconds, 3),
                "frames": frame_metadata
            }
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode("utf-8", errors="ignore") if e.stderr else str(e)
            return {"status": "error", "message": f"Lỗi FFmpeg: {err_msg[:200]}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

