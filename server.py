"""
CapCut Keyframe Studio - Server
Lightweight HTTP Server providing REST API & UI hosting using Python standard library.
"""

import os
import sys
import json
import time
import urllib.parse
import subprocess
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.capcut_adapter import CapCutAdapter
from core.keyframe_engine import KeyframeEngine
from core.audio_analyzer import AudioAnalyzer
from core.frame_ai_inspector import FrameAIInspector
from core.filmstrip_generator import FilmstripGenerator
from core.speed_ramp_engine import SpeedRampEngine
from core.stabilizer_engine import StabilizerEngine

adapter = CapCutAdapter()
_frame_cache: Dict[str, Any] = {}

class CapCutAPIHandler(SimpleHTTPRequestHandler):
    """Handles REST API calls and serves static Web UI assets."""

    def translate_path(self, path):
        """Map web requests to the /web directory."""
        clean_path = path.split("?", 1)[0].split("#", 1)[0]
        if clean_path.startswith("/api/") or clean_path.startswith("/cover"):
            return super().translate_path(path)

        # Serve static assets from BASE_DIR / 'web'
        rel_path = clean_path.lstrip("/")
        if not rel_path or rel_path == "":
            rel_path = "index.html"
        return os.path.join(str(BASE_DIR / "web"), rel_path)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # Serve cover image
        if path == "/cover":
            folder_name = params.get("name", [""])[0]
            if folder_name and adapter.draft_dir:
                cover_path = os.path.join(adapter.draft_dir, folder_name, "draft_cover.jpg")
                if os.path.exists(cover_path):
                    self.send_response(200)
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Cache-Control", "max-age=3600")
                    self.end_headers()
                    with open(cover_path, "rb") as f:
                        self.wfile.write(f.read())
                    return
            self.send_error(404, "Cover not found")
            return

        # Serve filmstrip contact sheet
        if path == "/filmstrip":
            fpath = params.get("path", ["/tmp/capcut_filmstrip.png"])[0]
            if os.path.exists(fpath):
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                with open(fpath, "rb") as f:
                    self.wfile.write(f.read())
                return
            self.send_error(404, "Filmstrip not found")
            return

        # Serve Media Frame / Thumbnail
        if path == "/api/media_frame":
            file_path = params.get("path", [""])[0]
            time_s = float(params.get("t", [0.0])[0])
            width = int(params.get("w", [160])[0])
            height = int(params.get("h", [90])[0])
            quality = int(params.get("q", [6])[0])

            if not file_path or not os.path.exists(file_path):
                self.send_error(404, "Media file not found")
                return

            ext = os.path.splitext(file_path)[1].lower()
            cache_key = f"{file_path}_{time_s:.2f}_{width}_{height}"
            if cache_key in _frame_cache:
                data, mime = _frame_cache[cache_key]
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Cache-Control", "public, max-age=86400")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            if ext in [".png", ".jpg", ".jpeg", ".webp"]:
                try:
                    with open(file_path, "rb") as f:
                        data = f.read()
                    mime = "image/png" if ext == ".png" else "image/jpeg"
                    if len(_frame_cache) < 400:
                        _frame_cache[cache_key] = (data, mime)
                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                except Exception as e:
                    self.send_error(500, str(e))
                    return

            elif ext in [".mp4", ".mov", ".m4v", ".webm"]:
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{time_s:.3f}",
                    "-i", file_path,
                    "-vframes", "1",
                    "-vf", f"scale={width}:{height}",
                    "-f", "image2",
                    "-c:v", "mjpeg",
                    "-q:v", str(quality),
                    "pipe:1"
                ]
                try:
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out, _ = proc.communicate()
                    if proc.returncode == 0 and out:
                        if len(_frame_cache) < 400:
                            _frame_cache[cache_key] = (out, "image/jpeg")
                        self.send_response(200)
                        self.send_header("Content-Type", "image/jpeg")
                        self.send_header("Cache-Control", "public, max-age=86400")
                        self.send_header("Content-Length", str(len(out)))
                        self.end_headers()
                        self.wfile.write(out)
                        return
                except Exception as e:
                    self.send_error(500, str(e))
                    return

            self.send_error(400, "Unsupported media type")
            return

        # API: List Projects
        if path == "/api/projects":
            try:
                projects = adapter.list_projects()
                self._send_json({
                    "status": "success",
                    "draft_dir": adapter.draft_dir,
                    "projects": projects
                })
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 500)
            return

        # API: Project Details
        if path == "/api/project":
            folder_name = params.get("name", [""])[0]
            if not folder_name:
                self._send_json({"status": "error", "message": "Missing project name parameter"}, 400)
                return
            try:
                details = adapter.load_project_details(folder_name)
                self._send_json({"status": "success", "data": details})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 500)
            return

        # API: Audio Beats from track
        if path == "/api/audio_beats":
            folder_name = params.get("name", [""])[0]
            track_idx = int(params.get("track", [0])[0])
            seg_idx = int(params.get("seg", [0])[0])
            bpm = float(params.get("bpm", [120.0])[0])
            use_bpm = params.get("use_bpm", ["false"])[0].lower() == "true"

            try:
                details = adapter.load_project_details(folder_name)
                audio_file = ""
                duration_us = int(details.get("duration_seconds", 15) * 1_000_000)

                for trk in details.get("tracks", []):
                    if trk.get("index") == track_idx or trk.get("type") == "audio":
                        segs = trk.get("segments", [])
                        if segs and seg_idx < len(segs):
                            audio_file = segs[seg_idx].get("file_path", "")
                            duration_us = segs[seg_idx].get("duration_us", duration_us)
                            break

                beats = []
                if not use_bpm and audio_file and os.path.exists(audio_file):
                    beats = AudioAnalyzer.detect_beats_from_file(audio_file)

                # Fallback to BPM if no beats detected from audio or use_bpm is true
                if not beats:
                    beats = AudioAnalyzer.generate_bpm_beats(bpm, duration_us)

                self._send_json({
                    "status": "success",
                    "count": len(beats),
                    "beats_us": beats,
                    "audio_file": os.path.basename(audio_file) if audio_file else "BPM Mode"
                })
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 500)
            return

        # Static files fallback
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        # Set custom draft directory
        if path == "/api/set_draft_dir":
            new_dir = payload.get("directory", "")
            if adapter.set_draft_dir(new_dir):
                self._send_json({"status": "success", "draft_dir": adapter.draft_dir})
            else:
                self._send_json({"status": "error", "message": "Directory does not exist"}, 400)
            return

        # Apply Preset to segments
        if path == "/api/apply_preset":
            self._handle_apply_preset(payload)
            return

        # Apply Beat Sync
        if path == "/api/apply_beat_sync":
            self._handle_apply_beat_sync(payload)
            return

        # Batch replicate keyframes
        if path == "/api/batch_replicate":
            self._handle_batch_replicate(payload)
            return

        # Smooth curves
        if path == "/api/smooth_curves":
            self._handle_smooth_curves(payload)
            return

        # Shift keyframes
        if path == "/api/shift_keyframes":
            self._handle_shift_keyframes(payload)
            return

        # Clear keyframes
        if path == "/api/clear_keyframes":
            self._handle_clear_keyframes(payload)
            return

        # AI Frame Inspection
        if path == "/api/ai_inspect_frames":
            self._handle_ai_inspect_frames(payload)
            return

        # AI Auto-Fix Frames
        if path == "/api/ai_autofix_frames":
            self._handle_ai_autofix_frames(payload)
            return

        # Filmstrip Contact Sheet Generation
        if path == "/api/generate_filmstrip":
            self._handle_generate_filmstrip(payload)
            return

        # Speed Ramp Master
        if path == "/api/apply_speed_ramp":
            self._handle_apply_speed_ramp(payload)
            return

        if path == "/api/reset_speed":
            self._handle_reset_speed(payload)
            return

        # Lock-Point Stabilizer
        if path == "/api/apply_stabilizer":
            self._handle_apply_stabilizer(payload)
            return

        # Restore backup
        if path == "/api/restore_backup":
            folder_name = payload.get("folder_name", "")
            backup_filename = payload.get("backup_filename", "")
            try:
                adapter.restore_backup(folder_name, backup_filename)
                self._send_json({"status": "success", "message": "Restored successfully"})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 500)
            return

        self.send_error(404, "Endpoint not found")

    # ==========================================
    # POST Handlers
    # ==========================================

    def _handle_apply_preset(self, payload: Dict[str, Any]):
        folder_name = payload.get("folder_name", "")
        targets = payload.get("targets", [])  # List of {"track_index": int, "segment_index": int}
        preset_name = payload.get("preset", "smooth_zoom_in")
        params = payload.get("params", {})
        replace_existing = payload.get("replace", True)

        try:
            project_path = os.path.join(adapter.draft_dir, folder_name)
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracks = data.get("tracks", [])
            modified_count = 0

            for target in targets:
                t_idx = target.get("track_index")
                s_idx = target.get("segment_index")

                if t_idx is None or s_idx is None or t_idx >= len(tracks):
                    continue
                track = tracks[t_idx]
                segs = track.get("segments", [])
                if s_idx >= len(segs):
                    continue

                seg = segs[s_idx]
                dur_us = seg.get("target_timerange", {}).get("duration", 3_000_000)

                # Generate keyframes based on preset
                new_kf_groups = []
                if preset_name == "smooth_zoom_in":
                    new_kf_groups = KeyframeEngine.preset_smooth_zoom(
                        duration_us=dur_us,
                        start_scale=float(params.get("start_scale", 1.0)),
                        end_scale=float(params.get("end_scale", 1.25)),
                        curve_mode=params.get("curve_mode", "smooth")
                    )
                elif preset_name == "smooth_zoom_out":
                    new_kf_groups = KeyframeEngine.preset_smooth_zoom(
                        duration_us=dur_us,
                        start_scale=float(params.get("start_scale", 1.25)),
                        end_scale=float(params.get("end_scale", 1.0)),
                        curve_mode=params.get("curve_mode", "smooth")
                    )
                elif preset_name == "camera_shake":
                    new_kf_groups = KeyframeEngine.preset_camera_shake(
                        duration_us=dur_us,
                        intensity=float(params.get("intensity", 0.03)),
                        frequency_hz=float(params.get("frequency_hz", 14.0)),
                        rotation_deg=float(params.get("rotation_deg", 1.2)),
                        decay=bool(params.get("decay", False))
                    )
                elif preset_name == "slow_pan":
                    new_kf_groups = KeyframeEngine.preset_slow_pan(
                        duration_us=dur_us,
                        direction=params.get("direction", "right"),
                        pan_distance=float(params.get("pan_distance", 0.15)),
                        zoom_scale=float(params.get("zoom_scale", 1.15))
                    )
                elif preset_name == "elastic_bounce":
                    new_kf_groups = KeyframeEngine.preset_elastic_bounce(
                        duration_us=dur_us,
                        peak_scale=float(params.get("peak_scale", 1.25)),
                        base_scale=float(params.get("base_scale", 1.0)),
                        bounce_duration_ms=int(params.get("bounce_duration_ms", 600))
                    )
                elif preset_name == "whip_pan":
                    new_kf_groups = KeyframeEngine.preset_whip_pan(
                        duration_us=dur_us,
                        direction=params.get("direction", "right"),
                        whip_duration_ms=int(params.get("whip_duration_ms", 350)),
                        is_transition_out=bool(params.get("is_transition_out", True))
                    )
                elif preset_name == "breathing_pulse":
                    new_kf_groups = KeyframeEngine.preset_breathing_pulse(
                        duration_us=dur_us,
                        min_scale=float(params.get("min_scale", 1.0)),
                        max_scale=float(params.get("max_scale", 1.08)),
                        period_seconds=float(params.get("period_seconds", 2.0))
                    )
                elif preset_name == "fade_opacity":
                    new_kf_groups = KeyframeEngine.preset_fade_opacity(
                        duration_us=dur_us,
                        fade_type=params.get("fade_type", "in"),
                        fade_duration_ms=int(params.get("fade_duration_ms", 500))
                    )
                elif preset_name == "rhythmic_switch_entrance":
                    new_kf_groups = KeyframeEngine.preset_rhythmic_switch_entrance(
                        duration_us=dur_us,
                        direction=params.get("direction", "up"),
                        target_pos=float(params.get("target_pos", -0.50)),
                        offscreen_pos=float(params.get("offscreen_pos", -1.60)),
                        transition_duration_ms=int(params.get("transition_duration_ms", 250)),
                        overshoot=float(params.get("overshoot", 0.08)),
                        fps=int(data.get("fps", 30))
                    )
                elif preset_name == "rhythmic_switch_exit":
                    new_kf_groups = KeyframeEngine.preset_rhythmic_switch_exit(
                        duration_us=dur_us,
                        direction=params.get("direction", "down"),
                        current_pos=float(params.get("current_pos", -0.50)),
                        offscreen_pos=float(params.get("offscreen_pos", -1.60)),
                        transition_duration_ms=int(params.get("transition_duration_ms", 200)),
                        fps=int(data.get("fps", 30))
                    )
                elif preset_name == "rhythmic_pulse_step":
                    new_kf_groups = KeyframeEngine.preset_rhythmic_pulse_step(
                        duration_us=dur_us,
                        interval_seconds=float(params.get("interval_seconds", 1.0)),
                        motion_type=params.get("motion_type", "bounce"),
                        bounce_scale=float(params.get("bounce_scale", 1.15)),
                        bounce_duration_ms=int(params.get("bounce_duration_ms", 150))
                    )

                if new_kf_groups:
                    self._apply_groups_to_segment(seg, new_kf_groups, replace_existing)
                    modified_count += 1

            # Save modified draft
            adapter.save_project_data(folder_name, data)
            self._send_json({
                "status": "success",
                "message": f"Applied preset '{preset_name}' to {modified_count} clip(s)."
            })
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _handle_apply_beat_sync(self, payload: Dict[str, Any]):
        folder_name = payload.get("folder_name", "")
        targets = payload.get("targets", [])
        beats_us = payload.get("beats_us", [])
        bounce_scale = float(payload.get("bounce_scale", 1.18))
        bounce_duration_ms = int(payload.get("bounce_duration_ms", 140))
        mode = payload.get("mode", "bounce")
        replace_existing = payload.get("replace", True)

        try:
            project_path = os.path.join(adapter.draft_dir, folder_name)
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracks = data.get("tracks", [])
            modified_count = 0

            for target in targets:
                t_idx = target.get("track_index")
                s_idx = target.get("segment_index")

                if t_idx is None or s_idx is None or t_idx >= len(tracks):
                    continue
                track = tracks[t_idx]
                segs = track.get("segments", [])
                if s_idx >= len(segs):
                    continue

                seg = segs[s_idx]
                trange = seg.get("target_timerange", {})
                start_us = trange.get("start", 0)
                dur_us = trange.get("duration", 3_000_000)

                new_kf_groups = KeyframeEngine.generate_beat_bounce_keyframes(
                    segment_start_us=start_us,
                    segment_duration_us=dur_us,
                    beat_timestamps_us=beats_us,
                    bounce_scale=bounce_scale,
                    bounce_duration_ms=bounce_duration_ms,
                    mode=mode
                )

                if new_kf_groups:
                    self._apply_groups_to_segment(seg, new_kf_groups, replace_existing)
                    modified_count += 1

            adapter.save_project_data(folder_name, data)
            self._send_json({
                "status": "success",
                "message": f"Applied beat sync to {modified_count} clip(s)."
            })
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _handle_batch_replicate(self, payload: Dict[str, Any]):
        folder_name = payload.get("folder_name", "")
        source_target = payload.get("source", {})  # {"track_index": int, "segment_index": int}
        dest_targets = payload.get("destinations", [])
        mode = payload.get("mode", "stretch")

        try:
            project_path = os.path.join(adapter.draft_dir, folder_name)
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracks = data.get("tracks", [])
            s_t_idx = source_target.get("track_index")
            s_s_idx = source_target.get("segment_index")

            if s_t_idx is None or s_s_idx is None or s_t_idx >= len(tracks):
                raise ValueError("Invalid source clip")

            src_seg = tracks[s_t_idx]["segments"][s_s_idx]
            src_keyframes = src_seg.get("common_keyframes", [])
            src_dur_us = src_seg.get("target_timerange", {}).get("duration", 1)

            if not src_keyframes:
                raise ValueError("Source clip has no keyframes to copy")

            modified_count = 0
            for dt in dest_targets:
                dt_idx = dt.get("track_index")
                ds_idx = dt.get("segment_index")
                if dt_idx is None or ds_idx is None or dt_idx >= len(tracks):
                    continue

                dest_seg = tracks[dt_idx]["segments"][ds_idx]
                dest_dur_us = dest_seg.get("target_timerange", {}).get("duration", 1)

                replicated_groups = KeyframeEngine.replicate_keyframes(
                    source_keyframes=src_keyframes,
                    source_duration_us=src_dur_us,
                    target_duration_us=dest_dur_us,
                    mode=mode
                )

                dest_seg["common_keyframes"] = replicated_groups
                modified_count += 1

            adapter.save_project_data(folder_name, data)
            self._send_json({
                "status": "success",
                "message": f"Successfully replicated keyframes to {modified_count} clip(s)."
            })
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _handle_smooth_curves(self, payload: Dict[str, Any]):
        folder_name = payload.get("folder_name", "")
        targets = payload.get("targets", [])
        smoothness = float(payload.get("smoothness", 0.35))

        try:
            project_path = os.path.join(adapter.draft_dir, folder_name)
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracks = data.get("tracks", [])
            modified_count = 0

            for target in targets:
                t_idx = target.get("track_index")
                s_idx = target.get("segment_index")
                if t_idx is None or s_idx is None or t_idx >= len(tracks):
                    continue

                seg = tracks[t_idx]["segments"][s_idx]
                cur_kfs = seg.get("common_keyframes", [])
                if cur_kfs:
                    seg["common_keyframes"] = KeyframeEngine.convert_to_smooth_curves(cur_kfs, smoothness=smoothness)
                    modified_count += 1

            adapter.save_project_data(folder_name, data)
            self._send_json({
                "status": "success",
                "message": f"Converted keyframes to smooth Bezier curves in {modified_count} clip(s)."
            })
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _handle_shift_keyframes(self, payload: Dict[str, Any]):
        folder_name = payload.get("folder_name", "")
        targets = payload.get("targets", [])
        delta_ms = int(payload.get("delta_ms", 0))

        try:
            project_path = os.path.join(adapter.draft_dir, folder_name)
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracks = data.get("tracks", [])
            modified_count = 0
            delta_us = delta_ms * 1000

            for target in targets:
                t_idx = target.get("track_index")
                s_idx = target.get("segment_index")
                if t_idx is None or s_idx is None or t_idx >= len(tracks):
                    continue

                seg = tracks[t_idx]["segments"][s_idx]
                cur_kfs = seg.get("common_keyframes", [])
                dur_us = seg.get("target_timerange", {}).get("duration", 0)
                if cur_kfs:
                    seg["common_keyframes"] = KeyframeEngine.shift_keyframes(cur_kfs, delta_us, dur_us)
                    modified_count += 1

            adapter.save_project_data(folder_name, data)
            self._send_json({
                "status": "success",
                "message": f"Shifted keyframes by {delta_ms}ms in {modified_count} clip(s)."
            })
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _handle_clear_keyframes(self, payload: Dict[str, Any]):
        folder_name = payload.get("folder_name", "")
        targets = payload.get("targets", [])
        property_filter = payload.get("property", "all")  # "all" or specific property like "KFTypeScaleX"

        try:
            project_path = os.path.join(adapter.draft_dir, folder_name)
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracks = data.get("tracks", [])
            modified_count = 0

            for target in targets:
                t_idx = target.get("track_index")
                s_idx = target.get("segment_index")
                if t_idx is None or s_idx is None or t_idx >= len(tracks):
                    continue

                seg = tracks[t_idx]["segments"][s_idx]
                if property_filter == "all":
                    seg["common_keyframes"] = []
                else:
                    cur_kfs = seg.get("common_keyframes", [])
                    seg["common_keyframes"] = [g for g in cur_kfs if g.get("property_type") != property_filter]
                modified_count += 1

            adapter.save_project_data(folder_name, data)
            self._send_json({
                "status": "success",
                "message": f"Cleared keyframes from {modified_count} clip(s)."
            })
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _apply_groups_to_segment(self, seg: Dict[str, Any], new_groups: List[Dict[str, Any]], replace_existing: bool):
        existing_groups = seg.get("common_keyframes", []) or []
        if replace_existing:
            # Replace matching property types, keep other properties intact
            new_prop_types = {g.get("property_type") for g in new_groups}
            retained = [g for g in existing_groups if g.get("property_type") not in new_prop_types]
            seg["common_keyframes"] = retained + new_groups
        else:
            seg["common_keyframes"] = existing_groups + new_groups

    def _handle_ai_inspect_frames(self, payload: Dict[str, Any]):
        folder_name = payload.get("folder_name", "")
        track_idx = payload.get("track_index", 0)
        seg_idx = payload.get("segment_index", 0)
        fps = int(payload.get("fps", 30))

        try:
            project_path = os.path.join(adapter.draft_dir, folder_name)
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracks = data.get("tracks", [])
            if track_idx >= len(tracks) or seg_idx >= len(tracks[track_idx].get("segments", [])):
                raise ValueError("Clip index out of bounds")

            seg = tracks[track_idx]["segments"][seg_idx]

            # Try to grab audio beats if any audio track exists
            beats = []
            for t in tracks:
                if t.get("type") == "audio":
                    for a_seg in t.get("segments", []):
                        m_id = a_seg.get("material_id")
                        for a_mat in data.get("materials", {}).get("audios", []):
                            if a_mat.get("id") == m_id:
                                a_path = a_mat.get("path", "")
                                if "##_draftpath_placeholder_" in a_path:
                                    parts = a_path.split("_##/")
                                    if len(parts) == 2:
                                        a_path = os.path.join(project_path, parts[1])
                                if os.path.exists(a_path):
                                    beats = AudioAnalyzer.detect_beats_from_file(a_path, max_duration_sec=60)
                                    break
                    if beats:
                        break

            report = FrameAIInspector.inspect_segment_frames(
                segment=seg,
                fps=fps,
                beat_timestamps_us=beats
            )

            self._send_json(report)
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _handle_ai_autofix_frames(self, payload: Dict[str, Any]):
        folder_name = payload.get("folder_name", "")
        targets = payload.get("targets", [])
        fps = int(payload.get("fps", 30))

        try:
            project_path = os.path.join(adapter.draft_dir, folder_name)
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracks = data.get("tracks", [])
            modified_count = 0

            for target in targets:
                t_idx = target.get("track_index")
                s_idx = target.get("segment_index")
                if t_idx is None or s_idx is None or t_idx >= len(tracks):
                    continue

                seg = tracks[t_idx]["segments"][s_idx]
                optimized = FrameAIInspector.autofix_segment_motion(seg, fps=fps)
                seg["common_keyframes"] = optimized
                modified_count += 1

            adapter.save_project_data(folder_name, data)
            self._send_json({
                "status": "success",
                "message": f"AI đã tự động tinh chỉnh và làm mượt {modified_count} clip."
            })
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _handle_generate_filmstrip(self, payload: Dict[str, Any]):
        folder_name = payload.get("folder_name", "")
        track_idx = payload.get("track_index", 0)
        seg_idx = payload.get("segment_index", 0)
        cols = int(payload.get("cols", 5))
        rows = int(payload.get("rows", 2))
        tile_width = int(payload.get("tile_width", 220))

        try:
            project_path = os.path.join(adapter.draft_dir, folder_name)
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracks = data.get("tracks", [])
            if track_idx >= len(tracks) or seg_idx >= len(tracks[track_idx].get("segments", [])):
                raise ValueError("Clip index out of bounds")

            seg = tracks[track_idx]["segments"][seg_idx]
            mat_id = seg.get("material_id")

            # Find matching video file path
            video_file = ""
            for v_mat in data.get("materials", {}).get("videos", []):
                if v_mat.get("id") == mat_id:
                    v_path = v_mat.get("path", "")
                    if "##_draftpath_placeholder_" in v_path:
                        parts = v_path.split("_##/")
                        if len(parts) == 2:
                            v_path = os.path.join(project_path, parts[1])
                    if os.path.exists(v_path):
                        video_file = v_path
                        break

            if not video_file or not os.path.exists(video_file):
                raise FileNotFoundError("Không tìm thấy file video gốc của clip này trên ổ đĩa.")

            # Calculate source start and duration in seconds
            source_range = seg.get("source_timerange", {})
            start_s = source_range.get("start", 0) / 1_000_000.0
            dur_s = source_range.get("duration", seg.get("target_timerange", {}).get("duration", 1_000_000)) / 1_000_000.0

            # Safe output PNG path in /tmp
            clean_name = f"filmstrip_{os.path.basename(folder_name)}_{track_idx}_{seg_idx}.png"
            output_png = os.path.join("/tmp", clean_name)

            result = FilmstripGenerator.generate_filmstrip(
                video_path=video_file,
                start_seconds=start_s,
                duration_seconds=dur_s,
                cols=cols,
                rows=rows,
                tile_width=tile_width,
                output_png_path=output_png
            )

            if result.get("status") == "success":
                result["image_url"] = f"/filmstrip?path={urllib.parse.quote(output_png)}&t={int(time.time())}"

            self._send_json(result)
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _handle_apply_speed_ramp(self, payload: Dict[str, Any]):
        folder_name = payload.get("folder_name", "")
        targets = payload.get("targets", [])
        preset = payload.get("preset", "hero")
        params = payload.get("params", {})
        use_beat = payload.get("use_beat", False)
        beats_us = payload.get("beats_us", [])

        try:
            project_path = os.path.join(adapter.draft_dir, folder_name)
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "materials" not in data:
                data["materials"] = {}
            if "speeds" not in data["materials"]:
                data["materials"]["speeds"] = []

            tracks = data.get("tracks", [])
            modified_count = 0

            for target in targets:
                t_idx = target.get("track_index")
                s_idx = target.get("segment_index")

                if t_idx is None or s_idx is None or t_idx >= len(tracks):
                    continue
                track = tracks[t_idx]
                segs = track.get("segments", [])
                if s_idx >= len(segs):
                    continue

                seg = segs[s_idx]
                src_dur = seg.get("source_timerange", {}).get("duration", 3_000_000)
                seg_start_us = seg.get("target_timerange", {}).get("start", 0)

                # Generate speed material
                if use_beat and beats_us:
                    speed_mat = SpeedRampEngine.generate_beat_speed_ramp(
                        segment_start_us=seg_start_us,
                        segment_source_duration_us=src_dur,
                        beat_timestamps_us=beats_us,
                        fast_speed=float(params.get("fast_speed", 4.0)),
                        slow_speed=float(params.get("slow_speed", 0.35))
                    )
                elif preset == "hero":
                    speed_mat = SpeedRampEngine.preset_hero(
                        fast_speed=float(params.get("fast_speed", 5.0)),
                        slow_speed=float(params.get("slow_speed", 0.4))
                    )
                elif preset == "bullet":
                    speed_mat = SpeedRampEngine.preset_bullet_time(
                        ultra_slow=float(params.get("ultra_slow", 0.2))
                    )
                elif preset == "flash_in":
                    speed_mat = SpeedRampEngine.preset_flash_in(
                        rush_speed=float(params.get("rush_speed", 6.0))
                    )
                elif preset == "flash_out":
                    speed_mat = SpeedRampEngine.preset_flash_out(
                        rush_speed=float(params.get("rush_speed", 6.0))
                    )
                elif preset == "jump_cut":
                    speed_mat = SpeedRampEngine.preset_jump_cut(
                        fast_speed=float(params.get("fast_speed", 4.5))
                    )
                elif preset == "montage":
                    speed_mat = SpeedRampEngine.preset_montage(
                        peak_speed=float(params.get("peak_speed", 6.0)),
                        dip_speed=float(params.get("dip_speed", 0.3))
                    )
                else:
                    speed_mat = SpeedRampEngine.preset_hero()

                # Add speed object to materials.speeds
                data["materials"]["speeds"].append(speed_mat)

                # Update segment references and timing
                seg["speed"] = speed_mat["speed"]
                if "extra_material_refs" not in seg:
                    seg["extra_material_refs"] = []
                # Remove existing speed refs from extra_material_refs
                existing_speed_ids = {s.get("id") for s in data["materials"]["speeds"]}
                seg["extra_material_refs"] = [r for r in seg["extra_material_refs"] if r not in existing_speed_ids]
                seg["extra_material_refs"].append(speed_mat["id"])

                # Update target duration: target_duration = int(source_duration / effective_speed)
                new_target_dur = int(src_dur / speed_mat["speed"])
                if "target_timerange" in seg:
                    seg["target_timerange"]["duration"] = new_target_dur

                modified_count += 1

            adapter.save_project_data(folder_name, data)
            self._send_json({
                "status": "success",
                "message": f"Đã áp dụng Speed Ramp '{preset}' cho {modified_count} clip."
            })
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _handle_reset_speed(self, payload: Dict[str, Any]):
        folder_name = payload.get("folder_name", "")
        targets = payload.get("targets", [])

        try:
            project_path = os.path.join(adapter.draft_dir, folder_name)
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracks = data.get("tracks", [])
            modified_count = 0

            for target in targets:
                t_idx = target.get("track_index")
                s_idx = target.get("segment_index")
                if t_idx is None or s_idx is None or t_idx >= len(tracks):
                    continue

                seg = tracks[t_idx]["segments"][s_idx]
                src_dur = seg.get("source_timerange", {}).get("duration", 3_000_000)

                seg["speed"] = 1.0
                if "target_timerange" in seg:
                    seg["target_timerange"]["duration"] = src_dur

                # Remove speed references
                all_speeds = {s.get("id") for s in data.get("materials", {}).get("speeds", [])}
                if "extra_material_refs" in seg:
                    seg["extra_material_refs"] = [r for r in seg["extra_material_refs"] if r not in all_speeds]

                modified_count += 1

            adapter.save_project_data(folder_name, data)
            self._send_json({
                "status": "success",
                "message": f"Đã khôi phục tốc độ chuẩn (1.0x) cho {modified_count} clip."
            })
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _handle_apply_stabilizer(self, payload: Dict[str, Any]):
        folder_name = payload.get("folder_name", "")
        targets = payload.get("targets", [])
        anchor_mode = payload.get("anchor_mode", "center")  # "center", "face", "chest", "custom"
        anchor_x = float(payload.get("anchor_x_ratio", 0.5))
        anchor_y = float(payload.get("anchor_y_ratio", 0.5))
        stabilize_mode = payload.get("stabilize_mode", "dead_lock")  # "dead_lock" or "smooth"
        smooth_window = int(payload.get("smooth_window", 15))
        min_zoom = float(payload.get("min_zoom", 1.15))
        fps = int(payload.get("fps", 30))

        if anchor_mode == "center":
            anchor_x, anchor_y = 0.5, 0.5
        elif anchor_mode == "face":
            anchor_x, anchor_y = 0.5, 0.30
        elif anchor_mode == "chest":
            anchor_x, anchor_y = 0.5, 0.55
        else:
            anchor_x = max(0.05, min(0.95, anchor_x))
            anchor_y = max(0.05, min(0.95, anchor_y))

        try:
            project_path = os.path.join(adapter.draft_dir, folder_name)
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracks = data.get("tracks", [])
            modified_count = 0
            details = []

            for target in targets:
                t_idx = target.get("track_index")
                s_idx = target.get("segment_index")
                if t_idx is None or s_idx is None or t_idx >= len(tracks):
                    continue

                track = tracks[t_idx]
                segs = track.get("segments", [])
                if s_idx >= len(segs):
                    continue

                seg = segs[s_idx]
                mat_id = seg.get("material_id")

                # Locate video media path
                video_file = ""
                for v_mat in data.get("materials", {}).get("videos", []):
                    if v_mat.get("id") == mat_id:
                        v_path = v_mat.get("path", "")
                        if "##_draftpath_placeholder_" in v_path:
                            parts = v_path.split("_##/")
                            if len(parts) == 2:
                                v_path = os.path.join(project_path, parts[1])
                        if os.path.exists(v_path):
                            video_file = v_path
                            break

                if not video_file or not os.path.exists(video_file):
                    continue

                source_range = seg.get("source_timerange", {})
                start_s = source_range.get("start", 0) / 1_000_000.0
                dur_s = source_range.get("duration", seg.get("target_timerange", {}).get("duration", 1_000_000)) / 1_000_000.0

                stab_res = StabilizerEngine.track_and_stabilize(
                    video_path=video_file,
                    start_seconds=start_s,
                    duration_seconds=dur_s,
                    anchor_x_ratio=anchor_x,
                    anchor_y_ratio=anchor_y,
                    stabilize_mode=stabilize_mode,
                    smooth_window=smooth_window,
                    min_zoom=min_zoom,
                    fps=fps
                )

                if stab_res.get("status") == "success":
                    self._apply_groups_to_segment(seg, stab_res["keyframes"], replace_existing=True)
                    modified_count += 1
                    details.append({
                        "track_index": t_idx,
                        "segment_index": s_idx,
                        "auto_zoom": stab_res.get("auto_zoom"),
                        "total_frames": stab_res.get("total_frames_tracked"),
                        "max_deviation_x": stab_res.get("max_deviation_x"),
                        "max_deviation_y": stab_res.get("max_deviation_y")
                    })
                else:
                    raise RuntimeError(f"Lỗi theo dõi và chống rung: {stab_res.get('message')}")

            if modified_count > 0:
                adapter.save_project_data(folder_name, data)
                self._send_json({
                    "status": "success",
                    "message": f"Đã chống rung khóa mốc và tự động zoom an toàn cho {modified_count} clip.",
                    "details": details
                })
            else:
                self._send_json({
                    "status": "error",
                    "message": "Không tìm thấy file video hợp lệ của các clip được chọn để phân tích chống rung."
                }, 400)

        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

    def _send_json(self, data: Any, status_code: int = 200):
        response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)

def run_server(port: int = 8765):
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, CapCutAPIHandler)
    print(f"CapCut Keyframe Studio Server running at http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    port = 8765
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
