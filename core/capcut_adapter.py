"""
CapCut Adapter Module
Cross-platform reader, writer, and draft manager for CapCut Desktop (macOS & Windows).
"""

import os
import sys
import json
import glob
import time
import shutil
import platform
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

class CapCutAdapter:
    """Manages CapCut project discovery, reading, backing up, and updating."""

    @staticmethod
    def get_default_draft_paths() -> List[str]:
        """Returns standard locations for CapCut drafts on macOS and Windows."""
        paths = []
        home = Path.home()
        system = platform.system().lower()

        if "darwin" in system:  # macOS
            mac_paths = [
                home / "Movies" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft",
                home / "Library" / "Containers" / "com.lemon.lvoverseas" / "Data" / "Movies" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft",
            ]
            paths.extend([str(p) for p in mac_paths if p.exists()])
        elif "windows" in system:  # Windows
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            appdata = os.environ.get("APPDATA", "")
            win_paths = []
            if local_appdata:
                win_paths.append(Path(local_appdata) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft")
                win_paths.append(Path(local_appdata) / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft")
            if appdata:
                win_paths.append(Path(appdata) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft")
            paths.extend([str(p) for p in win_paths if p.exists()])
        else:  # Linux or generic
            generic_paths = [
                home / "Movies" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft",
                home / ".config" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft",
            ]
            paths.extend([str(p) for p in generic_paths if p.exists()])

        return paths

    def __init__(self, custom_draft_dir: Optional[str] = None):
        self.draft_dir = None
        if custom_draft_dir and os.path.exists(custom_draft_dir):
            self.draft_dir = custom_draft_dir
        else:
            default_paths = self.get_default_draft_paths()
            if default_paths:
                self.draft_dir = default_paths[0]

    def set_draft_dir(self, directory: str) -> bool:
        if os.path.exists(directory) and os.path.isdir(directory):
            self.draft_dir = directory
            return True
        return False

    def list_projects(self) -> List[Dict[str, Any]]:
        """Lists all CapCut projects in the draft directory with their metadata."""
        if not self.draft_dir or not os.path.exists(self.draft_dir):
            return []

        projects = []
        try:
            entries = os.listdir(self.draft_dir)
        except Exception:
            return []

        for entry in entries:
            if entry.startswith("."):
                continue
            project_path = os.path.join(self.draft_dir, entry)
            if not os.path.isdir(project_path):
                continue

            # Check for draft_info.json or draft_content.json
            info_file = os.path.join(project_path, "draft_info.json")
            if not os.path.exists(info_file):
                info_file = os.path.join(project_path, "draft_content.json")

            if not os.path.exists(info_file):
                continue

            try:
                stat = os.stat(info_file)
                modified_time = stat.st_mtime
                mod_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(modified_time))

                # Read basic info
                with open(info_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                proj_id = data.get("id", entry)
                proj_name = data.get("name", entry)
                duration_us = data.get("duration", 0)
                fps = data.get("fps", 30)

                tracks = data.get("tracks", [])
                video_tracks = sum(1 for t in tracks if t.get("type") == "video")
                audio_tracks = sum(1 for t in tracks if t.get("type") == "audio")
                text_tracks = sum(1 for t in tracks if t.get("type") == "text")

                cover_file = os.path.join(project_path, "draft_cover.jpg")
                has_cover = os.path.exists(cover_file)

                # Check available backups
                backup_files = glob.glob(os.path.join(project_path, "draft_info.json.bak*"))
                backup_files += glob.glob(os.path.join(project_path, "draft_content.json.bak*"))

                projects.append({
                    "id": proj_id,
                    "folder_name": entry,
                    "display_name": proj_name,
                    "project_path": project_path,
                    "info_file": info_file,
                    "duration_seconds": round(duration_us / 1000000.0, 2),
                    "fps": fps,
                    "video_tracks": video_tracks,
                    "audio_tracks": audio_tracks,
                    "text_tracks": text_tracks,
                    "modified_timestamp": modified_time,
                    "modified_time": mod_str,
                    "has_cover": has_cover,
                    "backup_count": len(backup_files)
                })
            except Exception as e:
                continue

        # Sort by latest modified
        projects.sort(key=lambda p: p["modified_timestamp"], reverse=True)
        return projects

    def load_project_details(self, folder_name: str) -> Dict[str, Any]:
        """Loads detailed track and segment breakdown of a project."""
        if not self.draft_dir:
            raise ValueError("Draft directory not found.")

        project_path = os.path.join(self.draft_dir, folder_name)
        info_file = os.path.join(project_path, "draft_info.json")
        if not os.path.exists(info_file):
            info_file = os.path.join(project_path, "draft_content.json")

        if not os.path.exists(info_file):
            raise FileNotFoundError(f"Project JSON not found in {project_path}")

        with open(info_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        materials = data.get("materials", {})
        video_mats = {v.get("id"): v for v in materials.get("videos", [])}
        audio_mats = {a.get("id"): a for a in materials.get("audios", [])}
        text_mats = {t.get("id"): t for t in materials.get("texts", [])}

        parsed_tracks = []
        for track_idx, track in enumerate(data.get("tracks", [])):
            track_type = track.get("type", "unknown")
            track_id = track.get("id", f"track_{track_idx}")

            segments = []
            for seg_idx, seg in enumerate(track.get("segments", [])):
                seg_id = seg.get("id", f"seg_{seg_idx}")
                mat_id = seg.get("material_id", "")
                target_range = seg.get("target_timerange", {})
                source_range = seg.get("source_timerange", {})

                start_us = target_range.get("start", 0)
                duration_us = target_range.get("duration", 0)
                end_us = start_us + duration_us

                source_start_us = source_range.get("start", 0) if source_range else 0
                source_duration_us = source_range.get("duration", 0) if source_range else 0

                common_kf = seg.get("common_keyframes", []) or []
                kf_summary = []
                for kf_group in common_kf:
                    ptype = kf_group.get("property_type", "unknown")
                    klist = kf_group.get("keyframe_list", [])
                    kf_summary.append({
                        "property": ptype,
                        "count": len(klist)
                    })

                # Determine readable name
                seg_name = f"Segment {seg_idx + 1}"
                file_path = ""
                if track_type == "video" and mat_id in video_mats:
                    m = video_mats[mat_id]
                    seg_name = m.get("material_name") or m.get("path") or seg_name
                    seg_name = os.path.basename(seg_name)
                    file_path = m.get("path", "")
                elif track_type == "audio" and mat_id in audio_mats:
                    m = audio_mats[mat_id]
                    seg_name = m.get("name") or m.get("path") or seg_name
                    seg_name = os.path.basename(seg_name)
                    file_path = m.get("path", "")
                elif track_type == "text" and mat_id in text_mats:
                    m = text_mats[mat_id]
                    seg_name = m.get("content") or seg_name
                    if len(seg_name) > 30:
                        seg_name = seg_name[:27] + "..."

                # Resolve draft placeholder in path if present
                if "##_draftpath_placeholder_" in file_path:
                    # Strip placeholder and attach actual project_path
                    parts = file_path.split("_##/")
                    if len(parts) == 2:
                        file_path = os.path.join(project_path, parts[1])

                segments.append({
                    "id": seg_id,
                    "index": seg_idx,
                    "name": seg_name,
                    "file_path": file_path,
                    "material_id": mat_id,
                    "start_seconds": round(start_us / 1000000.0, 3),
                    "duration_seconds": round(duration_us / 1000000.0, 3),
                    "end_seconds": round(end_us / 1000000.0, 3),
                    "source_start_seconds": round(source_start_us / 1000000.0, 3),
                    "source_duration_seconds": round(source_duration_us / 1000000.0, 3),
                    "source_start_us": source_start_us,
                    "start_us": start_us,
                    "duration_us": duration_us,
                    "end_us": end_us,
                    "speed": seg.get("speed", 1.0),
                    "keyframes": kf_summary,
                    "has_keyframes": len(common_kf) > 0,
                    "raw_common_keyframes": common_kf
                })

            parsed_tracks.append({
                "id": track_id,
                "index": track_idx,
                "type": track_type,
                "segment_count": len(segments),
                "segments": segments
            })

        # List available backups for this project
        backup_files = glob.glob(os.path.join(project_path, "draft_info.json.bak*"))
        backup_files += glob.glob(os.path.join(project_path, "draft_content.json.bak*"))
        backups = []
        for bf in sorted(backup_files, reverse=True):
            b_stat = os.stat(bf)
            backups.append({
                "filename": os.path.basename(bf),
                "path": bf,
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(b_stat.st_mtime))
            })

        canvas_cfg = data.get("canvas_config", {})
        c_w = canvas_cfg.get("width") or 1080
        c_h = canvas_cfg.get("height") or 1920

        return {
            "name": data.get("name", folder_name),
            "folder_name": folder_name,
            "project_path": project_path,
            "info_file": info_file,
            "fps": data.get("fps", 30),
            "duration_seconds": round(data.get("duration", 0) / 1000000.0, 2),
            "canvas_width": c_w,
            "canvas_height": c_h,
            "canvas_ratio": canvas_cfg.get("ratio", "9:16"),
            "tracks": parsed_tracks,
            "backups": backups
        }

    def backup_project(self, folder_name: str, label: str = "auto") -> str:
        """Creates a timestamped backup of the project JSON."""
        project_path = os.path.join(self.draft_dir, folder_name)
        info_file = os.path.join(project_path, "draft_info.json")
        if not os.path.exists(info_file):
            info_file = os.path.join(project_path, "draft_content.json")

        if not os.path.exists(info_file):
            raise FileNotFoundError(f"Project JSON not found in {project_path}")

        timestamp = int(time.time())
        backup_name = f"{os.path.basename(info_file)}.bak-{label}-{timestamp}"
        backup_path = os.path.join(project_path, backup_name)
        shutil.copy2(info_file, backup_path)
        return backup_path

    def restore_backup(self, folder_name: str, backup_filename: str) -> bool:
        """Restores a project JSON from a specific backup file."""
        project_path = os.path.join(self.draft_dir, folder_name)
        target_file = os.path.join(project_path, "draft_info.json")
        if not os.path.exists(target_file):
            target_file = os.path.join(project_path, "draft_content.json")

        backup_path = os.path.join(project_path, backup_filename)
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Make a safety backup of current state before restoring
        self.backup_project(folder_name, label="pre-restore")
        shutil.copy2(backup_path, target_file)
        return True

    def save_project_data(self, folder_name: str, data: Dict[str, Any]) -> str:
        """Safely saves modified project data with backup."""
        project_path = os.path.join(self.draft_dir, folder_name)
        info_file = os.path.join(project_path, "draft_info.json")
        if not os.path.exists(info_file):
            info_file = os.path.join(project_path, "draft_content.json")

        # Create backup first
        self.backup_project(folder_name, label="before-keyframe-update")

        # Atomic write via temp file
        temp_file = info_file + ".tmp_write"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        shutil.move(temp_file, info_file)
        return info_file
