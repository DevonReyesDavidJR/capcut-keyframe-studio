"""
CapCut Keyframe Studio - Server
Lightweight HTTP Server providing REST API & UI hosting using Python standard library.
"""

import os
import sys
import json
import time
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.capcut_adapter import CapCutAdapter
from core.keyframe_engine import KeyframeEngine
from core.audio_analyzer import AudioAnalyzer

adapter = CapCutAdapter()

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
