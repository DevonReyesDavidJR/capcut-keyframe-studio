#!/usr/bin/env python3
"""
CapCut Keyframe Studio Pro - Native Desktop Edition
===================================================
A 100% native, zero-dependency desktop application for CapCut project editing.
Runs locally directly on macOS and Windows without web browser or HTTP server.

Features:
- Native Multi-Layer Composite Preview Monitor
- Visual Multi-Track Timeline with Keyframe Diamonds & Playhead
- 1-Click Rhythmic Keyframe Presets (Switch In/Out, 1s/2s Pulse, Bounce, Shake)
- Speed Ramping Master (Hero Ramp, Bullet Time, Flash, Beat-Sync)
- Point-Lock Keyframe Stabilizer (Dead-Lock & Smooth Damping with Auto-Zoom)
- AI Frame Inspector & Single-File Summary Filmstrip PNG Generator
- 100% Safe Atomic Draft Backup & Rollback Manager
"""

import os
import sys
import time
import json
import math
import shutil
import platform
import subprocess
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.capcut_adapter import CapCutAdapter
from core.keyframe_engine import KeyframeEngine
from core.speed_ramp_engine import SpeedRampEngine
from core.stabilizer_engine import StabilizerEngine

# ==============================================================================
# COLOR PALETTE & DESIGN SYSTEM (CapCut Dark Pro Style)
# ==============================================================================
THEME = {
    "bg_app": "#121316",         # Main background
    "bg_panel": "#181a20",       # Left/Right containers
    "bg_card": "#21242d",        # Control boxes / cards
    "bg_header": "#15161c",      # Top header
    "bg_input": "#2a2e39",       # Input fields / comboboxes
    "border": "#2e323e",         # Separators
    "accent_cyan": "#00f2fe",    # CapCut neon cyan
    "accent_blue": "#3b82f6",    # Action blue
    "accent_green": "#10b981",   # Success emerald
    "accent_yellow": "#f59e0b",  # Warning amber
    "accent_red": "#ef4444",     # Delete red
    "accent_purple": "#8b5cf6",  # Special purple
    "text_main": "#f3f4f6",      # Bright white text
    "text_muted": "#9ca3af",     # Subdued gray text
    "timeline_track": "#1e2129", # Track horizontal row
    "clip_video": "#2563eb",     # Video clip rectangle
    "clip_image": "#7c3aed",     # Image clip rectangle
    "clip_audio": "#059669",     # Audio clip rectangle
    "keyframe_diamond": "#facc15"# Yellow diamond
}


# ==============================================================================
# FAST LOCAL MEDIA RENDERER & IN-MEMORY CACHE
# ==============================================================================
class LocalMediaRenderer:
    """Handles extracting, downscaling, and caching video & image frames locally."""

    def __init__(self, temp_cache_dir: Optional[str] = None):
        if not temp_cache_dir:
            temp_cache_dir = os.path.join(BASE_DIR, ".preview_cache")
        self.cache_dir = temp_cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.mem_cache: Dict[str, tk.PhotoImage] = {}
        self.failed_paths = set()
        self.lock = threading.Lock()

    def clear_cache(self):
        with self.lock:
            self.mem_cache.clear()
            self.failed_paths.clear()

    @staticmethod
    def _is_image(path: str) -> bool:
        ext = os.path.splitext(path)[1].lower()
        return ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]

    @staticmethod
    def _is_video(path: str) -> bool:
        ext = os.path.splitext(path)[1].lower()
        return ext in [".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"]

    def get_layer_frame(
        self,
        file_path: str,
        target_w: int,
        target_h: int,
        clip_time_sec: float = 0.0
    ) -> Optional[tk.PhotoImage]:
        """Returns a tk.PhotoImage scaled to (target_w, target_h)."""
        if not file_path or not os.path.exists(file_path):
            return None

        # Build cache key
        target_w = max(16, target_w)
        target_h = max(16, target_h)
        is_vid = self._is_video(file_path)
        t_key = f"{round(clip_time_sec, 2):.2f}" if is_vid else "img"
        cache_key = f"{file_path}_{target_w}x{target_h}_{t_key}"

        with self.lock:
            if cache_key in self.mem_cache:
                return self.mem_cache[cache_key]

        if file_path in self.failed_paths:
            return None

        try:
            photo = None
            if not is_vid and self._is_image(file_path):
                # Static image: downscale with sips (macOS) or ffmpeg
                photo = self._render_image_scaled(file_path, target_w, target_h)
            elif is_vid:
                # Video: extract frame with ffmpeg
                photo = self._render_video_frame(file_path, target_w, target_h, clip_time_sec)

            if photo:
                with self.lock:
                    self.mem_cache[cache_key] = photo
                return photo
            else:
                self.failed_paths.add(file_path)
                return None
        except Exception as e:
            self.failed_paths.add(file_path)
            return None

    def _render_image_scaled(self, src_path: str, target_w: int, target_h: int) -> Optional[tk.PhotoImage]:
        # Fast path 1: sips on macOS (5-15ms)
        if platform.system() == "Darwin" and shutil.which("sips"):
            cache_file = os.path.join(self.cache_dir, f"scaled_{abs(hash(src_path))}_{target_w}x{target_h}.png")
            if not os.path.exists(cache_file):
                cmd = ["sips", "-z", str(target_h), str(target_w), src_path, "--out", cache_file]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            if os.path.exists(cache_file):
                return tk.PhotoImage(file=cache_file)

        # Fast path 2: ffmpeg pipe
        cmd = [
            "ffmpeg", "-y", "-i", src_path,
            "-vf", f"scale={target_w}:{target_h}",
            "-vframes", "1",
            "-f", "image2pipe", "-vcodec", "png", "pipe:1"
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
        if res.returncode == 0 and res.stdout:
            return tk.PhotoImage(data=res.stdout)

        # Fallback to direct PhotoImage (without scaling)
        try:
            return tk.PhotoImage(file=src_path)
        except Exception:
            return None

    def _render_video_frame(
        self,
        src_path: str,
        target_w: int,
        target_h: int,
        time_sec: float
    ) -> Optional[tk.PhotoImage]:
        time_str = f"{max(0.0, time_sec):.3f}"
        cmd = [
            "ffmpeg", "-ss", time_str, "-i", src_path,
            "-vf", f"scale={target_w}:{target_h}",
            "-vframes", "1",
            "-strict", "-1",
            "-f", "image2pipe", "-vcodec", "png", "pipe:1"
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
        if res.returncode == 0 and res.stdout:
            try:
                return tk.PhotoImage(data=res.stdout)
            except Exception:
                pass
        return None


# ==============================================================================
# KEYFRAME INTERPOLATION ENGINE
# ==============================================================================
class KeyframeInterpolator:
    """Evaluates position and scale values for any clip at time T."""

    @staticmethod
    def evaluate_property(keyframe_list: List[Dict[str, Any]], offset_us: int, default_val: float) -> float:
        if not keyframe_list:
            return default_val
        if len(keyframe_list) == 1:
            vals = keyframe_list[0].get("values", [default_val])
            return float(vals[0]) if vals else default_val

        # Sort by time_offset
        sorted_kfs = sorted(keyframe_list, key=lambda k: k.get("time_offset", 0))

        if offset_us <= sorted_kfs[0].get("time_offset", 0):
            return float(sorted_kfs[0].get("values", [default_val])[0])
        if offset_us >= sorted_kfs[-1].get("time_offset", 0):
            return float(sorted_kfs[-1].get("values", [default_val])[0])

        # Find enclosing pair
        for i in range(len(sorted_kfs) - 1):
            k1 = sorted_kfs[i]
            k2 = sorted_kfs[i + 1]
            t1 = k1.get("time_offset", 0)
            t2 = k2.get("time_offset", 0)
            if t1 <= offset_us <= t2:
                v1 = float(k1.get("values", [default_val])[0])
                v2 = float(k2.get("values", [default_val])[0])
                span = t2 - t1
                if span <= 0:
                    return v1
                ratio = (offset_us - t1) / float(span)
                # Linear or smooth interpolation
                return v1 + ratio * (v2 - v1)

        return default_val


# ==============================================================================
# MAIN DESKTOP APPLICATION CLASS
# ==============================================================================
class CapCutStudioDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🎬 CapCut Keyframe Studio Pro - Native Desktop Edition")
        self.root.geometry("1440x920")
        self.root.minsize(1100, 700)
        self.root.configure(bg=THEME["bg_app"])

        # Core Engines
        self.adapter = CapCutAdapter()
        self.renderer = LocalMediaRenderer()
        self.interpolator = KeyframeInterpolator()

        # State
        self.projects_list: List[Dict[str, Any]] = []
        self.current_project_folder: Optional[str] = None
        self.current_project: Optional[Dict[str, Any]] = None
        self.current_time_sec: float = 0.0
        self.is_playing: bool = False
        self.loop_playback: bool = True
        self.play_timer_id = None
        self.selected_layer_id: Optional[str] = None
        self.selected_clip_id: Optional[str] = None
        self.layer_visibility: Dict[str, bool] = {}  # segment_id -> bool

        # Setup Custom Styles
        self._setup_styles()

        # Build UI Layout
        self._build_header_bar()
        self._build_main_split()
        self._build_timeline_bar()
        self._bind_keyboard_shortcuts()

        # Load initial projects
        self._refresh_projects()

    # --------------------------------------------------------------------------
    # STYLES SETUP
    # --------------------------------------------------------------------------
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Global backgrounds
        style.configure(".", background=THEME["bg_panel"], foreground=THEME["text_main"], font=("Helvetica", 10))

        # Frames & Labelframes
        style.configure("TFrame", background=THEME["bg_panel"])
        style.configure("Card.TFrame", background=THEME["bg_card"], relief="flat")
        style.configure("TLabelframe", background=THEME["bg_card"], foreground=THEME["accent_cyan"], relief="groove")
        style.configure("TLabelframe.Label", background=THEME["bg_card"], foreground=THEME["accent_cyan"], font=("Helvetica", 11, "bold"))

        # Notebook (Tabs)
        style.configure("TNotebook", background=THEME["bg_app"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=THEME["bg_card"],
            foreground=THEME["text_muted"],
            padding=[14, 8],
            font=("Helvetica", 10, "bold")
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", THEME["accent_cyan"])],
            foreground=[("selected", "#000000")]
        )

        # Buttons
        style.configure(
            "Primary.TButton",
            background=THEME["accent_cyan"],
            foreground="#000000",
            font=("Helvetica", 10, "bold"),
            padding=[12, 6]
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#38ef7d"), ("pressed", "#00c6ff")]
        )

        style.configure(
            "Action.TButton",
            background=THEME["bg_card"],
            foreground=THEME["text_main"],
            font=("Helvetica", 10),
            padding=[10, 5]
        )
        style.map(
            "Action.TButton",
            background=[("active", THEME["border"])],
            foreground=[("active", THEME["accent_cyan"])]
        )

        style.configure(
            "Danger.TButton",
            background=THEME["accent_red"],
            foreground="#ffffff",
            font=("Helvetica", 10, "bold"),
            padding=[10, 5]
        )

        # Combobox
        style.configure(
            "TCombobox",
            fieldbackground=THEME["bg_input"],
            background=THEME["bg_card"],
            foreground=THEME["text_main"],
            darkcolor=THEME["border"],
            lightcolor=THEME["border"],
            arrowcolor=THEME["accent_cyan"]
        )

        # Scale / Sliders
        style.configure(
            "Horizontal.TScale",
            background=THEME["bg_panel"],
            troughcolor=THEME["bg_input"],
            sliderrelief="flat"
        )

        # Treeview (Active Layers Table)
        style.configure(
            "Treeview",
            background=THEME["bg_card"],
            fieldbackground=THEME["bg_card"],
            foreground=THEME["text_main"],
            rowheight=26,
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background=THEME["bg_header"],
            foreground=THEME["accent_cyan"],
            font=("Helvetica", 9, "bold"),
            borderwidth=1,
            relief="flat"
        )
        style.map("Treeview", background=[("selected", "#1e3a8a")], foreground=[("selected", "#ffffff")])

    # --------------------------------------------------------------------------
    # HEADER BAR
    # --------------------------------------------------------------------------
    def _build_header_bar(self):
        header = tk.Frame(self.root, bg=THEME["bg_header"], height=56, padx=16, pady=8)
        header.pack(side="top", fill="x")

        # Logo & App Title
        title_box = tk.Frame(header, bg=THEME["bg_header"])
        title_box.pack(side="left")
        lbl_logo = tk.Label(
            title_box,
            text="🎬 CAPCUT KEYFRAME STUDIO PRO",
            bg=THEME["bg_header"],
            fg=THEME["accent_cyan"],
            font=("Helvetica", 13, "bold")
        )
        lbl_logo.pack(side="left")
        lbl_tag = tk.Label(
            title_box,
            text=" [Native Desktop Local]",
            bg=THEME["bg_header"],
            fg=THEME["accent_green"],
            font=("Helvetica", 10, "bold")
        )
        lbl_tag.pack(side="left")

        # Project Selector Combobox
        proj_box = tk.Frame(header, bg=THEME["bg_header"], padx=20)
        proj_box.pack(side="left", fill="x", expand=True)

        tk.Label(proj_box, text="Dự án CapCut:", bg=THEME["bg_header"], fg=THEME["text_muted"]).pack(side="left", padx=5)
        self.proj_combo = ttk.Combobox(proj_box, state="readonly", width=36)
        self.proj_combo.pack(side="left", padx=5)
        self.proj_combo.bind("<<ComboboxSelected>>", self._on_project_selected)

        btn_browse = ttk.Button(proj_box, text="📂 Chọn Thư Mục Khác...", style="Action.TButton", command=self._browse_custom_dir)
        btn_browse.pack(side="left", padx=5)

        btn_refresh = ttk.Button(proj_box, text="🔄 Làm Mới", style="Action.TButton", command=self._refresh_projects)
        btn_refresh.pack(side="left", padx=5)

        # Project Stats Badges
        self.stats_frame = tk.Frame(header, bg=THEME["bg_header"])
        self.stats_frame.pack(side="right")

        self.lbl_duration = tk.Label(self.stats_frame, text="⏱️ 00.00s", bg=THEME["bg_card"], fg=THEME["text_main"], padx=8, pady=4)
        self.lbl_duration.pack(side="left", padx=3)

        self.lbl_fps = tk.Label(self.stats_frame, text="⚡ 30 fps", bg=THEME["bg_card"], fg=THEME["text_main"], padx=8, pady=4)
        self.lbl_fps.pack(side="left", padx=3)

        self.lbl_tracks = tk.Label(self.stats_frame, text="🎞️ 0 Tracks", bg=THEME["bg_card"], fg=THEME["text_main"], padx=8, pady=4)
        self.lbl_tracks.pack(side="left", padx=3)

        self.btn_backup_badge = tk.Button(
            self.stats_frame,
            text="🛡️ Sao Lưu",
            bg=THEME["bg_card"],
            fg=THEME["accent_yellow"],
            relief="flat",
            padx=8,
            pady=2,
            command=self._show_backup_manager
        )
        self.btn_backup_badge.pack(side="left", padx=3)

    # --------------------------------------------------------------------------
    # MAIN SPLIT CONTAINER (Left: Operations Notebook | Right: Preview & Layers)
    # --------------------------------------------------------------------------
    def _build_main_split(self):
        self.split_pane = tk.PanedWindow(self.root, orient="horizontal", bg=THEME["bg_app"], sashwidth=4, sashrelief="flat")
        self.split_pane.pack(side="top", fill="both", expand=True, padx=8, pady=4)

        # Left Operations Notebook
        self.left_frame = tk.Frame(self.split_pane, bg=THEME["bg_panel"], padx=6, pady=6)
        self.split_pane.add(self.left_frame, minsize=460, width=540)

        # Right Preview Monitor & Active Layers
        self.right_frame = tk.Frame(self.split_pane, bg=THEME["bg_panel"], padx=6, pady=6)
        self.split_pane.add(self.right_frame, minsize=480)

        # Populate Left & Right
        self._build_operations_notebook()
        self._build_preview_monitor()

    # --------------------------------------------------------------------------
    # LEFT OPERATIONS NOTEBOOK
    # --------------------------------------------------------------------------
    def _build_operations_notebook(self):
        self.notebook = ttk.Notebook(self.left_frame)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Presets Nhịp Chuyển Động
        tab_rhythm = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_rhythm, text="⚡ Nhịp Chuyển Động")
        self._build_tab_rhythm(tab_rhythm)

        # Tab 2: Speed Ramping Master
        tab_speed = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_speed, text="🏎️ Speed Ramp")
        self._build_tab_speed(tab_speed)

        # Tab 3: Chống Rung Khóa Mốc (Stabilizer Point-Lock)
        tab_stab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_stab, text="🎯 Chống Rung Khóa Mốc")
        self._build_tab_stabilizer(tab_stab)

        # Tab 4: AI Frame Inspector & Filmstrip
        tab_ai = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_ai, text="🤖 AI Nhịp & Filmstrip")
        self._build_tab_ai_inspector(tab_ai)

        # Tab 5: Quản lý Bản Sao Lưu (Rollback)
        tab_backup = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab_backup, text="🛡️ Bản Sao Lưu")
        self._build_tab_backups(tab_backup)

    # --------------------------------------------------------------------------
    # TAB 1: RHYTHMIC KEYFRAME PRESETS
    # --------------------------------------------------------------------------
    def _build_tab_rhythm(self, parent):
        scroll_canvas = tk.Canvas(parent, bg=THEME["bg_panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=scroll_canvas.yview)
        inner = tk.Frame(scroll_canvas, bg=THEME["bg_panel"])
        inner.bind("<Configure>", lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.create_window((0, 0), window=inner, anchor="nw")
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 1-Click Rhythmic Presets Group
        group_1click = ttk.LabelFrame(inner, text="⚡ 1-CLICK RHYTHMIC PRESETS (ÁP DỤNG TỨC THÌ)", padding=10)
        group_1click.pack(fill="x", pady=6)

        presets = [
            ("🔁 Đảo Nhịp In / Out (Switch Clip)", "switch_in_out", "So le nhịp vào/ra giữa các clip liên tiếp (chuẩn Halloween/Sale)"),
            ("⏱️ Nhịp Đều 1 Giây (1s Pulse)", "pulse_1s", "Chu kỳ phóng to thu nhỏ mỗi 1.0 giây theo nhịp TVC"),
            ("⏱️ Nhịp Dài 2 Giây (2s Slow Push)", "pulse_2s", "Đẩy từ từ khung hình mỗi 2.0 giây"),
            ("💥 Giật Nảy Đàn Hồi (Elastic Bounce)", "bounce", "Hiệu ứng nảy lò xo overshoot cực nảy ở đầu clip"),
            ("🔍 Punch-In Zoom (Giật Phóng Nhanh)", "punch_zoom", "Giật phóng cận cảnh 1.35x rồi thu về 1.0x"),
            ("🌊 Lắc Rung Nhẹ (Subtle Shake)", "shake", "Hiệu ứng rung cầm tay tự nhiên sống động")
        ]

        for title, preset_code, desc in presets:
            btn_card = tk.Frame(group_1click, bg=THEME["bg_card"], padx=8, pady=6, highlightbackground=THEME["border"], highlightthickness=1)
            btn_card.pack(fill="x", pady=4)

            top_row = tk.Frame(btn_card, bg=THEME["bg_card"])
            top_row.pack(fill="x")
            tk.Label(top_row, text=title, bg=THEME["bg_card"], fg=THEME["accent_cyan"], font=("Helvetica", 10, "bold")).pack(side="left")

            btn_apply = tk.Button(
                top_row,
                text="Áp Dụng",
                bg=THEME["accent_cyan"],
                fg="#000000",
                font=("Helvetica", 9, "bold"),
                relief="flat",
                padx=8,
                pady=2,
                command=lambda p=preset_code: self._apply_rhythm_preset(p)
            )
            btn_apply.pack(side="right")

            tk.Label(btn_card, text=desc, bg=THEME["bg_card"], fg=THEME["text_muted"], font=("Helvetica", 9), anchor="w").pack(fill="x", pady=(2, 0))

        # Target Configuration Group
        group_target = ttk.LabelFrame(inner, text="⚙️ CẤU HÌNH PHẠM VI ÁP DỤNG", padding=10)
        group_target.pack(fill="x", pady=6)

        row1 = tk.Frame(group_target, bg=THEME["bg_card"])
        row1.pack(fill="x", pady=3)
        tk.Label(row1, text="Áp dụng cho Track:", bg=THEME["bg_card"], fg=THEME["text_main"]).pack(side="left", padx=5)
        self.rhythm_track_combo = ttk.Combobox(row1, state="readonly", width=22)
        self.rhythm_track_combo["values"] = ["Tất cả Video Track", "Chỉ Track đang chọn", "Track 0 (Chính)", "Track 1 (Overlay 1)"]
        self.rhythm_track_combo.current(0)
        self.rhythm_track_combo.pack(side="left", padx=5)

        row2 = tk.Frame(group_target, bg=THEME["bg_card"])
        row2.pack(fill="x", pady=3)
        tk.Label(row2, text="Đường cong Bezier:", bg=THEME["bg_card"], fg=THEME["text_main"]).pack(side="left", padx=5)
        self.rhythm_curve_combo = ttk.Combobox(row2, state="readonly", width=22)
        self.rhythm_curve_combo["values"] = ["FreeCurveInOut (Mượt)", "FreeCurveIn", "FreeCurveOut", "Line (Tuyến tính)"]
        self.rhythm_curve_combo.current(0)
        self.rhythm_curve_combo.pack(side="left", padx=5)

        # Scale parameters
        row3 = tk.Frame(group_target, bg=THEME["bg_card"])
        row3.pack(fill="x", pady=3)
        tk.Label(row3, text="Scale Bắt đầu:", bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(side="left", padx=5)
        self.spin_scale_start = ttk.Spinbox(row3, from_=0.5, to=3.0, increment=0.05, width=6)
        self.spin_scale_start.set(1.0)
        self.spin_scale_start.pack(side="left", padx=5)

        tk.Label(row3, text="Scale Đỉnh:", bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(side="left", padx=10)
        self.spin_scale_peak = ttk.Spinbox(row3, from_=0.5, to=3.0, increment=0.05, width=6)
        self.spin_scale_peak.set(1.25)
        self.spin_scale_peak.pack(side="left", padx=5)

        # Action Buttons
        btn_box = tk.Frame(inner, bg=THEME["bg_panel"])
        btn_box.pack(fill="x", pady=10)

        btn_save = tk.Button(
            btn_box,
            text="🚀 GHI KEYFRAME VÀO CAPCUT (TỰ ĐỘNG SAO LƯU)",
            bg=THEME["accent_cyan"],
            fg="#000000",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self._save_keyframes_to_capcut
        )
        btn_save.pack(fill="x", pady=3)

        btn_clear = tk.Button(
            btn_box,
            text="🧼 Xóa Toàn Bộ Keyframe Trên Track Đã Chọn",
            bg=THEME["bg_card"],
            fg=THEME["accent_red"],
            relief="flat",
            padx=10,
            pady=5,
            command=self._clear_keyframes_on_track
        )
        btn_clear.pack(fill="x", pady=3)

    # --------------------------------------------------------------------------
    # TAB 2: SPEED RAMPING MASTER
    # --------------------------------------------------------------------------
    def _build_tab_speed(self, parent):
        group_presets = ttk.LabelFrame(parent, text="🏎️ CÁC MẪU UỐN TỐC ĐỘ (SPEED CURVE PRESETS)", padding=10)
        group_presets.pack(fill="x", pady=6)

        speed_presets = [
            ("🌟 Hero Ramp", "hero_ramp", "Nhanh 2.5x -> Chậm 0.3x đỉnh điểm -> Nhanh 3.0x"),
            ("⏱️ Bullet-Time Slowmo", "bullet_time", "1.0x -> 0.15x siêu chậm giữa hành động -> 1.0x"),
            ("⚡ Flash-In / Flash-Out", "flash_in_out", "4.0x vút nhanh vào -> 1.0x -> 4.0x vút ra"),
            ("🥁 Beat-Synced Speed", "beat_sync", "Uốn nhịp tốc độ dồn dập theo nhịp 0.5s"),
            ("🔄 Reset 1.0x Bình Thường", "reset", "Đưa clip trở về tốc độ gốc 1.0x không uốn")
        ]

        for title, code, desc in speed_presets:
            card = tk.Frame(group_presets, bg=THEME["bg_card"], padx=8, pady=6, highlightbackground=THEME["border"], highlightthickness=1)
            card.pack(fill="x", pady=4)

            top = tk.Frame(card, bg=THEME["bg_card"])
            top.pack(fill="x")
            tk.Label(top, text=title, bg=THEME["bg_card"], fg=THEME["accent_cyan"], font=("Helvetica", 10, "bold")).pack(side="left")

            btn = tk.Button(
                top,
                text="Áp Dụng",
                bg=THEME["accent_cyan"],
                fg="#000000",
                font=("Helvetica", 9, "bold"),
                relief="flat",
                padx=8,
                pady=2,
                command=lambda c=code: self._apply_speed_ramp(c)
            )
            btn.pack(side="right")
            tk.Label(card, text=desc, bg=THEME["bg_card"], fg=THEME["text_muted"], font=("Helvetica", 9)).pack(anchor="w")

        # Curve Visualizer mini canvas
        group_viz = ttk.LabelFrame(parent, text="📈 BIỂU ĐỒ ĐƯỜNG CONG TỐC ĐỘ (SPEED CURVE VISUALIZER)", padding=10)
        group_viz.pack(fill="both", expand=True, pady=6)

        self.speed_canvas = tk.Canvas(group_viz, bg="#0e1014", height=130, highlightthickness=0)
        self.speed_canvas.pack(fill="both", expand=True, pady=4)
        self._draw_speed_curve_preview("hero_ramp")

    def _draw_speed_curve_preview(self, preset_code: str):
        self.speed_canvas.delete("all")
        w = self.speed_canvas.winfo_width() or 400
        h = self.speed_canvas.winfo_height() or 130

        # Draw baseline (1.0x)
        mid_y = h * 0.6
        self.speed_canvas.create_line(20, mid_y, w - 20, mid_y, fill=THEME["border"], dash=(4, 4))
        self.speed_canvas.create_text(w - 15, mid_y, text="1.0x", fill=THEME["text_muted"], font=("Helvetica", 8), anchor="w")

        # Draw curve based on preset
        points = []
        if preset_code == "hero_ramp":
            points = [(20, h * 0.3), (w * 0.3, h * 0.4), (w * 0.5, h * 0.85), (w * 0.7, h * 0.4), (w - 20, h * 0.25)]
        elif preset_code == "bullet_time":
            points = [(20, mid_y), (w * 0.35, mid_y), (w * 0.5, h * 0.9), (w * 0.65, mid_y), (w - 20, mid_y)]
        elif preset_code == "flash_in_out":
            points = [(20, h * 0.2), (w * 0.3, mid_y), (w * 0.7, mid_y), (w - 20, h * 0.2)]
        else:
            points = [(20, mid_y), (w - 20, mid_y)]

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            self.speed_canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=THEME["accent_cyan"], width=3, smooth=True)

        for p in points:
            self.speed_canvas.create_oval(p[0]-4, p[1]-4, p[0]+4, p[1]+4, fill=THEME["accent_yellow"], outline="")

    # --------------------------------------------------------------------------
    # TAB 3: STABILIZER POINT-LOCK (CHỐNG RUNG KHÓA MỐC)
    # --------------------------------------------------------------------------
    def _build_tab_stabilizer(self, parent):
        info_box = tk.Frame(parent, bg=THEME["bg_card"], padx=10, pady=8, highlightbackground=THEME["border"], highlightthickness=1)
        info_box.pack(fill="x", pady=6)

        tk.Label(
            info_box,
            text="🎯 CÔNG NGHỆ CHỐNG RUNG KHÓA TRỤC CỐ ĐỊNH",
            bg=THEME["bg_card"],
            fg=THEME["accent_cyan"],
            font=("Helvetica", 10, "bold")
        ).pack(anchor="w")

        msg = (
            "Khóa mốc tại 1 điểm cố định (logo, mắt, mặt sản phẩm) và giữ trục tọa độ\n"
            "để loại bỏ rung lắc hoàn toàn. Tự động phóng to (Auto-Zoom 1.05x - 1.25x)\n"
            "và bù trừ keyframe chuyển động để cảnh quay luôn nằm trong khung hình chính."
        )
        tk.Label(info_box, text=msg, bg=THEME["bg_card"], fg=THEME["text_muted"], font=("Helvetica", 9), justify="left").pack(anchor="w", pady=4)

        # Settings
        group_opt = ttk.LabelFrame(parent, text="⚙️ THÔNG SỐ CHỐNG RUNG", padding=10)
        group_opt.pack(fill="x", pady=6)

        row1 = tk.Frame(group_opt, bg=THEME["bg_card"])
        row1.pack(fill="x", pady=4)
        tk.Label(row1, text="Chế độ chống rung:", bg=THEME["bg_card"], fg=THEME["text_main"]).pack(side="left", padx=5)
        self.stab_mode_combo = ttk.Combobox(row1, state="readonly", width=24)
        self.stab_mode_combo["values"] = ["Khóa Mốc Tuyệt Đối (Dead-Lock)", "Giảm Rung Mượt (Smooth Damping)"]
        self.stab_mode_combo.current(0)
        self.stab_mode_combo.pack(side="left", padx=5)

        row2 = tk.Frame(group_opt, bg=THEME["bg_card"])
        row2.pack(fill="x", pady=4)
        tk.Label(row2, text="Tự động phóng to (Auto-Zoom):", bg=THEME["bg_card"], fg=THEME["text_main"]).pack(side="left", padx=5)
        self.stab_zoom_combo = ttk.Combobox(row2, state="readonly", width=10)
        self.stab_zoom_combo["values"] = ["1.05x", "1.10x", "1.15x", "1.20x", "1.25x"]
        self.stab_zoom_combo.current(1)
        self.stab_zoom_combo.pack(side="left", padx=5)

        row3 = tk.Frame(group_opt, bg=THEME["bg_card"])
        row3.pack(fill="x", pady=4)
        tk.Label(row3, text="Bán kính tìm kiếm:", bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(side="left", padx=5)
        self.spin_search_radius = ttk.Spinbox(row3, from_=16, to=96, increment=8, width=6)
        self.spin_search_radius.set(32)
        self.spin_search_radius.pack(side="left", padx=5)

        # Action Button
        btn_stab = tk.Button(
            parent,
            text="🎯 PHÂN TÍCH & TẠO KEYFRAME CHỐNG RUNG KHÓA MỐC",
            bg=THEME["accent_cyan"],
            fg="#000000",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=12,
            pady=10,
            command=self._execute_stabilizer
        )
        btn_stab.pack(fill="x", pady=12)

    # --------------------------------------------------------------------------
    # TAB 4: AI FRAME INSPECTOR & FILMSTRIP (USER REQUEST #1 & #2)
    # --------------------------------------------------------------------------
    def _build_tab_ai_inspector(self, parent):
        info_box = tk.Frame(parent, bg=THEME["bg_card"], padx=10, pady=8, highlightbackground=THEME["border"], highlightthickness=1)
        info_box.pack(fill="x", pady=6)

        tk.Label(
            info_box,
            text="🤖 AI PHÂN TÍCH NHỊP & XUẤT 1 FILE PNG FILMSTRIP DUY NHẤT",
            bg=THEME["bg_card"],
            fg=THEME["accent_cyan"],
            font=("Helvetica", 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            info_box,
            text="Tách các frame đại diện của video và gộp thành 1 tấm ảnh PNG tổng\nđể review nhịp cắt nhanh, không tốn dung lượng ổ cứng.",
            bg=THEME["bg_card"],
            fg=THEME["text_muted"],
            font=("Helvetica", 9),
            justify="left"
        ).pack(anchor="w", pady=4)

        # Rhythm Stats Frame
        self.ai_stats_card = tk.Frame(parent, bg=THEME["bg_card"], padx=10, pady=8)
        self.ai_stats_card.pack(fill="x", pady=6)
        self.lbl_ai_rhythm_summary = tk.Label(
            self.ai_stats_card,
            text="Chưa phân tích. Nhấn nút bên dưới để quét nhịp video.",
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            font=("Helvetica", 9),
            justify="left"
        )
        self.lbl_ai_rhythm_summary.pack(anchor="w")

        # Action Buttons
        btn_inspect = tk.Button(
            parent,
            text="🔍 PHÂN TÍCH NHỊP VIDEO TIMELINE",
            bg=THEME["accent_blue"],
            fg="#ffffff",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=10,
            pady=8,
            command=self._analyze_video_rhythm
        )
        btn_inspect.pack(fill="x", pady=4)

        btn_filmstrip = tk.Button(
            parent,
            text="🖼️ XUẤT FILMSTRIP TỔNG (1 FILE PNG DUY NHẤT)",
            bg=THEME["accent_green"],
            fg="#ffffff",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=10,
            pady=8,
            command=self._generate_single_png_filmstrip
        )
        btn_filmstrip.pack(fill="x", pady=4)

    # --------------------------------------------------------------------------
    # TAB 5: BACKUPS & ROLLBACK
    # --------------------------------------------------------------------------
    def _build_tab_backups(self, parent):
        tk.Label(
            parent,
            text="🛡️ LỊCH SỬ BẢN SAO LƯU DỰ ÁN (AN TOÀN TUYỆT ĐỐI)",
            bg=THEME["bg_panel"],
            fg=THEME["accent_cyan"],
            font=("Helvetica", 10, "bold")
        ).pack(anchor="w", pady=4)

        self.backup_tree = ttk.Treeview(parent, columns=("time", "filename"), show="headings", height=8)
        self.backup_tree.heading("time", text="Thời Gian Sao Lưu")
        self.backup_tree.heading("filename", text="Tên File Bản Sao")
        self.backup_tree.column("time", width=150)
        self.backup_tree.column("filename", width=250)
        self.backup_tree.pack(fill="both", expand=True, pady=6)

        btn_box = tk.Frame(parent, bg=THEME["bg_panel"])
        btn_box.pack(fill="x", pady=6)

        btn_restore = tk.Button(
            btn_box,
            text="↩️ Khôi Phục Bản Sao Lưu Đã Chọn",
            bg=THEME["accent_yellow"],
            fg="#000000",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=10,
            pady=6,
            command=self._restore_selected_backup
        )
        btn_restore.pack(side="left", padx=4)

        btn_create = tk.Button(
            btn_box,
            text="➕ Tạo Bản Sao Lưu Ngay",
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            relief="flat",
            padx=10,
            pady=6,
            command=self._create_manual_backup
        )
        btn_create.pack(side="left", padx=4)

    # --------------------------------------------------------------------------
    # RIGHT PREVIEW MONITOR & ACTIVE LAYERS
    # --------------------------------------------------------------------------
    def _build_preview_monitor(self):
        # Top monitor container
        monitor_container = tk.Frame(self.right_frame, bg=THEME["bg_panel"])
        monitor_container.pack(side="top", fill="both", expand=True)

        # Header of monitor
        top_ctrl = tk.Frame(monitor_container, bg=THEME["bg_panel"])
        top_ctrl.pack(side="top", fill="x", pady=(0, 4))

        tk.Label(
            top_ctrl,
            text="📺 TRÌNH PHÁT ĐA LỚP (NATIVE COMPOSITE MONITOR)",
            bg=THEME["bg_panel"],
            fg=THEME["accent_cyan"],
            font=("Helvetica", 11, "bold")
        ).pack(side="left")

        self.lbl_viewport_info = tk.Label(
            top_ctrl,
            text="1080×1920 (9:16)",
            bg=THEME["bg_card"],
            fg=THEME["accent_green"],
            font=("Menlo", 9),
            padx=6,
            pady=2
        )
        self.lbl_viewport_info.pack(side="right")

        # Preview Canvas (CapCut Player Box)
        self.preview_canvas = tk.Canvas(
            monitor_container,
            bg="#0a0a0c",
            highlightthickness=1,
            highlightbackground=THEME["border"]
        )
        self.preview_canvas.pack(side="top", fill="both", expand=True)
        self.preview_canvas.bind("<Configure>", lambda e: self._render_current_frame())

        # Player Controls Bar
        ctrl_bar = tk.Frame(monitor_container, bg=THEME["bg_panel"], pady=6)
        ctrl_bar.pack(side="top", fill="x")

        # Transport Buttons
        btn_first = tk.Button(ctrl_bar, text="|◀", bg=THEME["bg_card"], fg=THEME["text_main"], relief="flat", width=3, command=self._step_to_start)
        btn_first.pack(side="left", padx=2)

        btn_prev = tk.Button(ctrl_bar, text="◀ 1F", bg=THEME["bg_card"], fg=THEME["text_main"], relief="flat", width=4, command=self._step_prev_frame)
        btn_prev.pack(side="left", padx=2)

        self.btn_play = tk.Button(
            ctrl_bar,
            text="▶ Phát",
            bg=THEME["accent_cyan"],
            fg="#000000",
            font=("Helvetica", 9, "bold"),
            relief="flat",
            width=8,
            command=self._toggle_playback
        )
        self.btn_play.pack(side="left", padx=4)

        btn_next = tk.Button(ctrl_bar, text="1F ▶", bg=THEME["bg_card"], fg=THEME["text_main"], relief="flat", width=4, command=self._step_next_frame)
        btn_next.pack(side="left", padx=2)

        btn_last = tk.Button(ctrl_bar, text="▶|", bg=THEME["bg_card"], fg=THEME["text_main"], relief="flat", width=3, command=self._step_to_end)
        btn_last.pack(side="left", padx=2)

        # Loop checkbox
        self.chk_loop_var = tk.BooleanVar(value=True)
        chk_loop = tk.Checkbutton(
            ctrl_bar,
            text="🔁 Lặp",
            variable=self.chk_loop_var,
            bg=THEME["bg_panel"],
            fg=THEME["text_muted"],
            selectcolor=THEME["bg_card"],
            activebackground=THEME["bg_panel"],
            activeforeground=THEME["text_main"]
        )
        chk_loop.pack(side="left", padx=8)

        # Timecode display
        self.lbl_timecode = tk.Label(
            ctrl_bar,
            text="00:00.000 / 00:00.000 (Frame 0/0)",
            bg=THEME["bg_panel"],
            fg=THEME["accent_cyan"],
            font=("Menlo", 10, "bold")
        )
        self.lbl_timecode.pack(side="right", padx=6)

        # Scrubber Slider
        self.scrub_scale = ttk.Scale(
            monitor_container,
            from_=0.0,
            to=10.0,
            orient="horizontal",
            style="Horizontal.TScale",
            command=self._on_scrub
        )
        self.scrub_scale.pack(side="top", fill="x", pady=2)

        # Active Layers Inspector (Bottom half of right frame)
        layer_box = ttk.LabelFrame(self.right_frame, text="📑 DANH SÁCH LAYER TẠI FRAME HIỆN TẠI", padding=6)
        layer_box.pack(side="bottom", fill="x", pady=(4, 0))

        self.layer_tree = ttk.Treeview(
            layer_box,
            columns=("visible", "track", "name", "scale", "position"),
            show="headings",
            height=5
        )
        self.layer_tree.heading("visible", text="Hiện")
        self.layer_tree.heading("track", text="Track")
        self.layer_tree.heading("name", text="Tên Clip / Asset")
        self.layer_tree.heading("scale", text="Scale")
        self.layer_tree.heading("position", text="Tọa Độ (X, Y)")

        self.layer_tree.column("visible", width=45, anchor="center")
        self.layer_tree.column("track", width=65, anchor="center")
        self.layer_tree.column("name", width=200)
        self.layer_tree.column("scale", width=70, anchor="center")
        self.layer_tree.column("position", width=110, anchor="center")
        self.layer_tree.pack(fill="x", expand=True)
        self.layer_tree.bind("<ButtonRelease-1>", self._on_layer_tree_click)

    # --------------------------------------------------------------------------
    # BOTTOM VISUAL TIMELINE BAR
    # --------------------------------------------------------------------------
    def _build_timeline_bar(self):
        timeline_frame = tk.Frame(self.root, bg=THEME["timeline_track"], height=160, highlightbackground=THEME["border"], highlightthickness=1)
        timeline_frame.pack(side="bottom", fill="x", padx=8, pady=(0, 6))

        # Title bar of timeline
        tl_header = tk.Frame(timeline_frame, bg=THEME["bg_header"], height=24, padx=8)
        tl_header.pack(side="top", fill="x")

        tk.Label(
            tl_header,
            text="🎞️ DÒNG THỜI GIAN ĐA TRACK (VISUAL TIMELINE) - ◆ KIM CƯƠNG KEYFRAME",
            bg=THEME["bg_header"],
            fg=THEME["accent_cyan"],
            font=("Helvetica", 9, "bold")
        ).pack(side="left")

        # Timeline Canvas
        self.timeline_canvas = tk.Canvas(timeline_frame, bg="#14161d", height=136, highlightthickness=0)
        self.timeline_canvas.pack(side="top", fill="both", expand=True)
        self.timeline_canvas.bind("<Configure>", lambda e: self._draw_timeline())
        self.timeline_canvas.bind("<Button-1>", self._on_timeline_click)
        self.timeline_canvas.bind("<B1-Motion>", self._on_timeline_click)

    # --------------------------------------------------------------------------
    # KEYBOARD SHORTCUTS
    # --------------------------------------------------------------------------
    def _bind_keyboard_shortcuts(self):
        self.root.bind("<space>", lambda e: self._toggle_playback())
        self.root.bind("<Left>", lambda e: self._step_prev_frame())
        self.root.bind("<Right>", lambda e: self._step_next_frame())
        self.root.bind("<Home>", lambda e: self._step_to_start())
        self.root.bind("<End>", lambda e: self._step_to_end())

    # --------------------------------------------------------------------------
    # PROJECT LOADING & DISCOVERY
    # --------------------------------------------------------------------------
    def _refresh_projects(self):
        try:
            self.projects_list = self.adapter.list_projects()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể quét danh sách dự án CapCut:\n{e}")
            return

        if not self.projects_list:
            self.proj_combo["values"] = ["Không tìm thấy dự án nào"]
            self.proj_combo.current(0)
            return

        titles = []
        for p in self.projects_list:
            name = p.get("display_name") or p.get("folder_name")
            dur = f"{p.get('duration_seconds', 0):.1f}s"
            titles.append(f"{name} ({dur})")

        self.proj_combo["values"] = titles

        # Default select first or SALE_t11 (1) / switch if available
        default_idx = 0
        for i, p in enumerate(self.projects_list):
            folder = p.get("folder_name", "")
            if "SALE_t11" in folder or "switch" in folder:
                default_idx = i
                break

        self.proj_combo.current(default_idx)
        self._load_project_by_index(default_idx)

    def _browse_custom_dir(self):
        chosen = filedialog.askdirectory(title="Chọn thư mục chứa dự án CapCut")
        if chosen and os.path.exists(chosen):
            self.adapter.set_draft_dir(chosen)
            self._refresh_projects()

    def _on_project_selected(self, event=None):
        idx = self.proj_combo.current()
        if 0 <= idx < len(self.projects_list):
            self._load_project_by_index(idx)

    def _load_project_by_index(self, idx: int):
        proj_meta = self.projects_list[idx]
        folder = proj_meta.get("folder_name")
        self.current_project_folder = folder

        try:
            self.current_project = self.adapter.load_project_details(folder)
        except Exception as e:
            messagebox.showerror("Lỗi Nạp Dự Án", f"Không thể đọc chi tiết dự án {folder}:\n{e}")
            return

        # Update stats
        dur = self.current_project.get("duration_seconds", 0.0)
        fps = self.current_project.get("fps", 30)
        c_w = self.current_project.get("canvas_width", 1080)
        c_h = self.current_project.get("canvas_height", 1920)
        tracks = self.current_project.get("tracks", [])

        self.lbl_duration.config(text=f"⏱️ {dur:.2f}s")
        self.lbl_fps.config(text=f"⚡ {fps} fps")
        self.lbl_tracks.config(text=f"🎞️ {len(tracks)} Tracks")
        self.lbl_viewport_info.config(text=f"{c_w}×{c_h} ({self.current_project.get('canvas_ratio', '9:16')})")

        # Update Scrubber range
        self.scrub_scale.config(to=dur)
        self.current_time_sec = min(self.current_time_sec, dur)

        # Clear render cache
        self.renderer.clear_cache()
        self.layer_visibility.clear()

        # Update Backups Tree
        self._refresh_backup_tree()

        # Render first frame & timeline
        self._render_current_frame()
        self._draw_timeline()

    def _refresh_backup_tree(self):
        self.backup_tree.delete(*self.backup_tree.get_children())
        if not self.current_project:
            return
        backups = self.current_project.get("backups", [])
        self.btn_backup_badge.config(text=f"🛡️ {len(backups)} Bản Sao Lưu")
        for b in backups:
            self.backup_tree.insert("", "end", values=(b.get("time"), b.get("filename")))

    # --------------------------------------------------------------------------
    # TRANSPORT & PLAYBACK CONTROL
    # --------------------------------------------------------------------------
    def _step_to_start(self):
        self.current_time_sec = 0.0
        self.scrub_scale.set(0.0)
        self._render_current_frame()
        self._draw_timeline()

    def _step_to_end(self):
        if not self.current_project:
            return
        dur = self.current_project.get("duration_seconds", 0.0)
        self.current_time_sec = dur
        self.scrub_scale.set(dur)
        self._render_current_frame()
        self._draw_timeline()

    def _step_prev_frame(self):
        if not self.current_project:
            return
        fps = self.current_project.get("fps", 30) or 30
        frame_dt = 1.0 / fps
        self.current_time_sec = max(0.0, self.current_time_sec - frame_dt)
        self.scrub_scale.set(self.current_time_sec)
        self._render_current_frame()
        self._draw_timeline()

    def _step_next_frame(self):
        if not self.current_project:
            return
        dur = self.current_project.get("duration_seconds", 0.0)
        fps = self.current_project.get("fps", 30) or 30
        frame_dt = 1.0 / fps
        self.current_time_sec = min(dur, self.current_time_sec + frame_dt)
        self.scrub_scale.set(self.current_time_sec)
        self._render_current_frame()
        self._draw_timeline()

    def _toggle_playback(self):
        if self.is_playing:
            self.is_playing = False
            self.btn_play.config(text="▶ Phát", bg=THEME["accent_cyan"])
            if self.play_timer_id:
                self.root.after_cancel(self.play_timer_id)
                self.play_timer_id = None
        else:
            self.is_playing = True
            self.btn_play.config(text="⏸ Dừng", bg=THEME["accent_yellow"])
            self._playback_loop()

    def _playback_loop(self):
        if not self.is_playing or not self.current_project:
            return

        dur = self.current_project.get("duration_seconds", 0.0)
        fps = self.current_project.get("fps", 30) or 30
        frame_dt = 1.0 / fps

        self.current_time_sec += frame_dt
        if self.current_time_sec > dur:
            if self.chk_loop_var.get():
                self.current_time_sec = 0.0
            else:
                self.current_time_sec = dur
                self._toggle_playback()
                return

        self.scrub_scale.set(self.current_time_sec)
        self._render_current_frame()
        self._draw_timeline()

        # Schedule next tick (~33ms for 30fps)
        delay_ms = int(1000.0 / fps)
        self.play_timer_id = self.root.after(delay_ms, self._playback_loop)

    def _on_scrub(self, val_str):
        if not self.current_project:
            return
        try:
            self.current_time_sec = float(val_str)
            self._render_current_frame()
            self._draw_timeline()
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # NATIVE MULTI-LAYER PREVIEW RENDERING ENGINE
    # --------------------------------------------------------------------------
    def _render_current_frame(self):
        self.preview_canvas.delete("all")
        if not self.current_project:
            return

        cw = self.preview_canvas.winfo_width()
        ch = self.preview_canvas.winfo_height()
        if cw <= 50:
            cw = 480
        if ch <= 50:
            ch = 560

        # Project aspect ratio
        proj_w = self.current_project.get("canvas_width") or 1080
        proj_h = self.current_project.get("canvas_height") or 1920
        aspect = proj_w / float(proj_h)

        # Fit within canvas with margin
        margin = 16
        avail_w = cw - margin * 2
        avail_h = ch - margin * 2
        if avail_w <= 0 or avail_h <= 0:
            return

        if avail_w / float(avail_h) > aspect:
            vp_h = avail_h
            vp_w = int(vp_h * aspect)
        else:
            vp_w = avail_w
            vp_h = int(vp_w / aspect)

        vx0 = (cw - vp_w) // 2
        vy0 = (ch - vp_h) // 2
        vx1 = vx0 + vp_w
        vy1 = vy0 + vp_h
        center_x = (vx0 + vx1) // 2
        center_y = (vy0 + vy1) // 2

        # Draw viewport background
        self.preview_canvas.create_rectangle(vx0, vy0, vx1, vy1, fill="#050608", outline=THEME["border"], width=2)

        # Collect active layers at current time
        t_sec = self.current_time_sec
        active_layers = []

        tracks = self.current_project.get("tracks", [])
        for track in tracks:
            t_type = track.get("type")
            if t_type != "video":
                continue
            for seg in track.get("segments", []):
                st = seg.get("start_seconds", 0.0)
                du = seg.get("duration_seconds", 0.0)
                et = st + du
                if st <= t_sec <= et:
                    active_layers.append((track.get("index", 0), seg))

        # Sort layers by track index ascending (Track 0 back, higher tracks on top)
        active_layers.sort(key=lambda x: x[0])

        # Active layers tree update
        self.layer_tree.delete(*self.layer_tree.get_children())

        # Render each layer
        for track_idx, seg in active_layers:
            seg_id = seg.get("id")
            # Check visibility
            is_vis = self.layer_visibility.get(seg_id, True)
            eye_symbol = "👁️" if is_vis else "❌"

            # Evaluate Transform and Scale at current time
            offset_us = int((t_sec - seg.get("start_seconds", 0.0)) * 1_000_000)
            kf_dict = {}
            for kf_group in seg.get("raw_common_keyframes", []):
                ptype = kf_group.get("property_type")
                kf_dict[ptype] = kf_group.get("keyframe_list", [])

            # Position X, Y
            clip_prop = seg.get("clip") or {}
            def_tx = clip_prop.get("transform", {}).get("x", 0.0) if clip_prop.get("transform") else 0.0
            def_ty = clip_prop.get("transform", {}).get("y", 0.0) if clip_prop.get("transform") else 0.0
            def_sx = clip_prop.get("scale", {}).get("x", 1.0) if clip_prop.get("scale") else 1.0
            def_sy = clip_prop.get("scale", {}).get("y", 1.0) if clip_prop.get("scale") else 1.0

            cur_tx = self.interpolator.evaluate_property(kf_dict.get("KFTypePositionX", []), offset_us, def_tx)
            cur_ty = self.interpolator.evaluate_property(kf_dict.get("KFTypePositionY", []), offset_us, def_ty)
            cur_sx = self.interpolator.evaluate_property(kf_dict.get("KFTypeScaleX", []), offset_us, def_sx)
            cur_sy = self.interpolator.evaluate_property(kf_dict.get("KFTypeScaleY", []), offset_us, def_sy)

            # Insert into Treeview
            pos_str = f"({cur_tx:+.2f}, {cur_ty:+.2f})"
            scale_str = f"{cur_sx:.2f}x"
            item_id = self.layer_tree.insert(
                "",
                "end",
                values=(eye_symbol, f"V{track_idx}", seg.get("name", "Asset"), scale_str, pos_str)
            )
            # Store seg_id in tree item tags
            self.layer_tree.item(item_id, tags=(seg_id,))

            if not is_vis:
                continue

            # Compute pixel coordinates on canvas
            # In CapCut, x: -1.0 is left edge, +1.0 is right edge; y: +1.0 is top edge, -1.0 is bottom edge
            layer_cx = center_x + cur_tx * (vp_w / 2.0)
            layer_cy = center_y - cur_ty * (vp_h / 2.0)

            # Target display dimensions
            disp_w = max(16, int(vp_w * cur_sx))
            disp_h = max(16, int(vp_h * cur_sy))

            # Fetch scaled frame from local renderer
            fpath = seg.get("file_path", "")
            clip_time_sec = seg.get("source_start_seconds", 0.0) + (t_sec - seg.get("start_seconds", 0.0))
            photo = self.renderer.get_layer_frame(fpath, disp_w, disp_h, clip_time_sec)

            if photo:
                # Draw image on canvas
                self.preview_canvas.create_image(layer_cx, layer_cy, image=photo, anchor="center")
            else:
                # Fallback: draw placeholder rectangle with name
                self.preview_canvas.create_rectangle(
                    layer_cx - disp_w//2, layer_cy - disp_h//2,
                    layer_cx + disp_w//2, layer_cy + disp_h//2,
                    fill="#1e293b", outline=THEME["accent_cyan"], width=1
                )
                self.preview_canvas.create_text(
                    layer_cx, layer_cy,
                    text=seg.get("name", "Asset"),
                    fill="#ffffff",
                    font=("Helvetica", 9)
                )

            # Draw selection bounding box if selected
            if self.selected_layer_id == seg_id:
                self.preview_canvas.create_rectangle(
                    layer_cx - disp_w//2, layer_cy - disp_h//2,
                    layer_cx + disp_w//2, layer_cy + disp_h//2,
                    outline=THEME["accent_cyan"],
                    dash=(4, 4),
                    width=2
                )

        # Viewport HUD Overlay
        dur = self.current_project.get("duration_seconds", 0.0)
        fps = self.current_project.get("fps", 30) or 30
        frame_idx = int(t_sec * fps)
        total_frames = int(dur * fps)

        time_str = f"{int(t_sec//60):02d}:{t_sec%60:06.3f}"
        dur_str = f"{int(dur//60):02d}:{dur%60:06.3f}"
        self.lbl_timecode.config(text=f"{time_str} / {dur_str} (Frame {frame_idx}/{total_frames})")

        # Canvas overlay text
        self.preview_canvas.create_text(
            vx1 - 10, vy1 - 12,
            text=time_str,
            fill=THEME["accent_cyan"],
            font=("Menlo", 10, "bold"),
            anchor="se"
        )
        self.preview_canvas.create_text(
            vx0 + 10, vy1 - 12,
            text=f"{len(active_layers)} Layers Active",
            fill=THEME["text_muted"],
            font=("Helvetica", 9),
            anchor="sw"
        )

    def _on_layer_tree_click(self, event):
        item = self.layer_tree.identify_row(event.y)
        col = self.layer_tree.identify_column(event.x)
        if not item:
            return

        tags = self.layer_tree.item(item, "tags")
        if not tags:
            return
        seg_id = tags[0]

        if col == "#1":  # Clicked 'Visible' column
            cur_vis = self.layer_visibility.get(seg_id, True)
            self.layer_visibility[seg_id] = not cur_vis
            self._render_current_frame()
        else:
            self.selected_layer_id = seg_id
            self._render_current_frame()

    # --------------------------------------------------------------------------
    # VISUAL MULTI-TRACK TIMELINE RENDERING
    # --------------------------------------------------------------------------
    def _draw_timeline(self):
        self.timeline_canvas.delete("all")
        if not self.current_project:
            return

        w = self.timeline_canvas.winfo_width() or 800
        h = self.timeline_canvas.winfo_height() or 136
        dur = self.current_project.get("duration_seconds", 0.0)
        if dur <= 0:
            return

        margin_left = 60
        margin_right = 20
        usable_w = w - margin_left - margin_right

        # Time Ruler
        ruler_h = 24
        self.timeline_canvas.create_rectangle(0, 0, w, ruler_h, fill="#0f1116", outline="")

        # Draw 1-second ticks
        sec_step = 1.0 if dur <= 20 else 2.0
        cur_s = 0.0
        while cur_s <= dur:
            x = margin_left + (cur_s / dur) * usable_w
            self.timeline_canvas.create_line(x, ruler_h - 6, x, ruler_h, fill=THEME["text_muted"])
            self.timeline_canvas.create_text(x + 2, ruler_h - 14, text=f"{int(cur_s)}s", fill=THEME["text_muted"], font=("Helvetica", 8), anchor="w")
            cur_s += sec_step

        # Tracks rows
        tracks = self.current_project.get("tracks", [])
        num_tracks = min(4, len(tracks))
        track_row_h = (h - ruler_h) // max(1, num_tracks)

        for i in range(num_tracks):
            track = tracks[i]
            t_idx = track.get("index", i)
            t_type = track.get("type", "video")
            row_y0 = ruler_h + i * track_row_h
            row_y1 = row_y0 + track_row_h

            # Track background
            bg_color = THEME["timeline_track"] if i % 2 == 0 else "#181a22"
            self.timeline_canvas.create_rectangle(0, row_y0, w, row_y1, fill=bg_color, outline=THEME["border"], width=1)

            # Track Header label
            t_label = f"V{t_idx}" if t_type == "video" else f"A{t_idx}"
            self.timeline_canvas.create_text(24, (row_y0 + row_y1)//2, text=t_label, fill=THEME["accent_cyan"], font=("Helvetica", 9, "bold"))

            # Clips on this track
            for seg in track.get("segments", []):
                st = seg.get("start_seconds", 0.0)
                du = seg.get("duration_seconds", 0.0)
                et = st + du

                x0 = margin_left + (st / dur) * usable_w
                x1 = margin_left + (et / dur) * usable_w
                clip_y0 = row_y0 + 3
                clip_y1 = row_y1 - 3

                fill_col = THEME["clip_video"] if t_type == "video" else THEME["clip_audio"]
                if seg.get("file_path", "").lower().endswith((".png", ".jpg", ".jpeg")):
                    fill_col = THEME["clip_image"]

                # Draw Clip Rectangle
                self.timeline_canvas.create_rectangle(
                    x0, clip_y0, x1, clip_y1,
                    fill=fill_col, outline="#3b82f6", width=1, tags=("clip", seg.get("id", ""))
                )

                # Clip Name
                cname = seg.get("name", "")
                if len(cname) > 14:
                    cname = cname[:12] + ".."
                self.timeline_canvas.create_text(x0 + 4, (clip_y0 + clip_y1)//2, text=cname, fill="#ffffff", font=("Helvetica", 8), anchor="w")

                # Keyframe Diamonds (◆)
                for kf_group in seg.get("raw_common_keyframes", []):
                    for kf in kf_group.get("keyframe_list", []):
                        kf_offset_s = kf.get("time_offset", 0) / 1_000_000.0
                        kf_abs_s = st + kf_offset_s
                        kx = margin_left + (kf_abs_s / dur) * usable_w
                        ky = (clip_y0 + clip_y1) // 2

                        # Draw diamond
                        self.timeline_canvas.create_polygon(
                            kx, ky - 4,
                            kx + 4, ky,
                            kx, ky + 4,
                            kx - 4, ky,
                            fill=THEME["keyframe_diamond"], outline="#000000"
                        )

        # Red Playhead Line
        playhead_x = margin_left + (self.current_time_sec / dur) * usable_w
        self.timeline_canvas.create_line(playhead_x, 0, playhead_x, h, fill=THEME["accent_red"], width=2)
        # Red Playhead Head triangle
        self.timeline_canvas.create_polygon(
            playhead_x - 6, 0,
            playhead_x + 6, 0,
            playhead_x, 10,
            fill=THEME["accent_red"]
        )

    def _on_timeline_click(self, event):
        if not self.current_project:
            return
        w = self.timeline_canvas.winfo_width() or 800
        dur = self.current_project.get("duration_seconds", 0.0)
        if dur <= 0:
            return

        margin_left = 60
        margin_right = 20
        usable_w = w - margin_left - margin_right

        rel_x = max(0, min(usable_w, event.x - margin_left))
        t = (rel_x / float(usable_w)) * dur
        self.current_time_sec = max(0.0, min(dur, t))
        self.scrub_scale.set(self.current_time_sec)
        self._render_current_frame()
        self._draw_timeline()

    # --------------------------------------------------------------------------
    # ACTION IMPLEMENTATIONS
    # --------------------------------------------------------------------------
    def _apply_rhythm_preset(self, preset_code: str):
        if not self.current_project or not self.current_project_folder:
            messagebox.showwarning("Chú ý", "Vui lòng chọn một dự án CapCut trước.")
            return

        folder = self.current_project_folder
        info_file = self.current_project.get("info_file")
        if not os.path.exists(info_file):
            messagebox.showerror("Lỗi", "Không tìm thấy file draft_info.json")
            return

        with open(info_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        scale_start = float(self.spin_scale_start.get() or 1.0)
        scale_peak = float(self.spin_scale_peak.get() or 1.25)
        curve_type = self.rhythm_curve_combo.get().split()[0]

        target_track_choice = self.rhythm_track_combo.get()
        applied_count = 0

        for t_idx, track in enumerate(data.get("tracks", [])):
            if track.get("type") != "video":
                continue
            if "Chỉ Track đang chọn" in target_track_choice and t_idx != 0:
                continue
            if "Track 0" in target_track_choice and t_idx != 0:
                continue
            if "Track 1" in target_track_choice and t_idx != 1:
                continue

            segments = track.get("segments", [])
            for s_idx, seg in enumerate(segments):
                du_us = seg.get("target_timerange", {}).get("duration", 0)
                if du_us <= 0:
                    continue

                new_kfs = []
                if preset_code == "switch_in_out":
                    # Alternate entrance direction
                    direction = "up" if s_idx % 2 == 0 else "down"
                    new_kfs = KeyframeEngine.preset_rhythmic_switch_entrance(
                        du_us, direction=direction, transition_duration_ms=220
                    )
                elif preset_code == "pulse_1s":
                    new_kfs = KeyframeEngine.preset_rhythmic_pulse_step(
                        du_us, interval_seconds=1.0, motion_type="bounce", bounce_scale=scale_peak
                    )
                elif preset_code == "pulse_2s":
                    new_kfs = KeyframeEngine.preset_rhythmic_pulse_step(
                        du_us, interval_seconds=2.0, motion_type="bounce", bounce_scale=scale_peak
                    )
                elif preset_code == "bounce":
                    new_kfs = KeyframeEngine.preset_bounce(
                        du_us, bounce_scale=scale_peak, bounce_count=2
                    )
                elif preset_code == "punch_zoom":
                    new_kfs = KeyframeEngine.preset_punch_zoom(
                        du_us, peak_scale=scale_peak, punch_duration_ms=200
                    )
                elif preset_code == "shake":
                    new_kfs = KeyframeEngine.preset_camera_shake(
                        du_us, intensity=0.03, frequency_hz=10
                    )

                if new_kfs:
                    seg["common_keyframes"] = new_kfs
                    applied_count += 1

        if applied_count > 0:
            self.adapter.save_project_data(folder, data)
            self._load_project_by_index(self.proj_combo.current())
            messagebox.showinfo(
                "Thành Công!",
                f"Đã áp dụng preset '{preset_code}' vào {applied_count} clip!\n"
                f"Bản sao lưu an toàn đã được tự động lưu trong thư mục dự án."
            )
        else:
            messagebox.showwarning("Thông Báo", "Không tìm thấy clip video nào phù hợp để áp dụng.")

    def _save_keyframes_to_capcut(self):
        self._apply_rhythm_preset("pulse_1s")

    def _clear_keyframes_on_track(self):
        if not self.current_project or not self.current_project_folder:
            return
        if not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa tất cả keyframe trên track đã chọn?"):
            return

        folder = self.current_project_folder
        info_file = self.current_project.get("info_file")
        with open(info_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        target_track_choice = self.rhythm_track_combo.get()
        cleared_count = 0
        for t_idx, track in enumerate(data.get("tracks", [])):
            if track.get("type") != "video":
                continue
            if "Track 0" in target_track_choice and t_idx != 0:
                continue
            if "Track 1" in target_track_choice and t_idx != 1:
                continue
            for seg in track.get("segments", []):
                if seg.get("common_keyframes"):
                    seg["common_keyframes"] = []
                    cleared_count += 1

        self.adapter.save_project_data(folder, data)
        self._load_project_by_index(self.proj_combo.current())
        messagebox.showinfo("Đã Xóa", f"Đã xóa keyframe khỏi {cleared_count} clip.")

    def _apply_speed_ramp(self, preset_code: str):
        if not self.current_project or not self.current_project_folder:
            messagebox.showwarning("Chú ý", "Vui lòng chọn một dự án CapCut trước.")
            return

        self._draw_speed_curve_preview(preset_code)

        folder = self.current_project_folder
        info_file = self.current_project.get("info_file")
        with open(info_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        applied = 0
        for track in data.get("tracks", []):
            if track.get("type") != "video":
                continue
            for seg in track.get("segments", []):
                du_us = seg.get("target_timerange", {}).get("duration", 0)
                if preset_code == "hero_ramp":
                    SpeedRampEngine.apply_speed_curve_to_segment(seg, SpeedRampEngine.preset_hero_ramp(du_us))
                    applied += 1
                elif preset_code == "bullet_time":
                    SpeedRampEngine.apply_speed_curve_to_segment(seg, SpeedRampEngine.preset_bullet_time(du_us))
                    applied += 1
                elif preset_code == "flash_in_out":
                    SpeedRampEngine.apply_speed_curve_to_segment(seg, SpeedRampEngine.preset_flash_in_out(du_us))
                    applied += 1
                elif preset_code == "reset":
                    SpeedRampEngine.reset_segment_speed(seg)
                    applied += 1

        if applied > 0:
            self.adapter.save_project_data(folder, data)
            self._load_project_by_index(self.proj_combo.current())
            messagebox.showinfo("Thành Công", f"Đã áp dụng uốn tốc độ '{preset_code}' vào {applied} clip!")

    def _execute_stabilizer(self):
        if not self.current_project or not self.current_project_folder:
            messagebox.showwarning("Chú ý", "Vui lòng chọn một dự án CapCut trước.")
            return

        # Find first video segment with actual video file
        target_video = None
        target_seg = None
        for track in self.current_project.get("tracks", []):
            for seg in track.get("segments", []):
                fp = seg.get("file_path", "")
                if fp.lower().endswith((".mp4", ".mov", ".m4v")):
                    target_video = fp
                    target_seg = seg
                    break
            if target_video:
                break

        if not target_video:
            messagebox.showinfo(
                "Thông Báo",
                "Dự án hiện tại chủ yếu là ảnh PNG/layer đồ họa.\n"
                "Tính năng chống rung khóa mốc áp dụng tốt nhất cho video camera quay thực tế."
            )
            return

        # Run stabilizer engine
        try:
            mode = "dead_lock" if "Khóa Mốc" in self.stab_mode_combo.get() else "smooth"
            zoom_str = self.stab_zoom_combo.get().replace("x", "")
            zoom_val = float(zoom_str)

            engine = StabilizerEngine()
            kfs = engine.stabilize_video_clip(
                target_video,
                target_seg.get("start_seconds", 0.0),
                target_seg.get("duration_seconds", 0.0),
                mode=mode,
                auto_zoom=zoom_val
            )

            # Update draft
            info_file = self.current_project.get("info_file")
            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Find and assign to segment
            for track in data.get("tracks", []):
                for s in track.get("segments", []):
                    if s.get("id") == target_seg.get("id"):
                        s["common_keyframes"] = kfs
                        break

            self.adapter.save_project_data(self.current_project_folder, data)
            self._load_project_by_index(self.proj_combo.current())
            messagebox.showinfo("Thành Công", f"Đã tạo keyframe chống rung khóa mốc (Auto-Zoom {zoom_val}x)!")
        except Exception as e:
            messagebox.showerror("Lỗi Chống Rung", f"Không thể thực thi chống rung:\n{e}")

    # --------------------------------------------------------------------------
    # AI RHYTHM ANALYSIS & SINGLE-FILE FILMSTRIP PNG (USER REQUEST #1 & #2)
    # --------------------------------------------------------------------------
    def _analyze_video_rhythm(self):
        if not self.current_project:
            return
        tracks = self.current_project.get("tracks", [])
        dur = self.current_project.get("duration_seconds", 0.0)

        total_segments = sum(len(t.get("segments", [])) for t in tracks if t.get("type") == "video")
        avg_cut = dur / max(1, total_segments)

        rhythm_type = "Nhịp Đều (Consistent Tempo)"
        if avg_cut < 0.8:
            rhythm_type = "Nhịp Nhanh Dồn Dập (Fast Action / TikTok Beat)"
        elif avg_cut > 2.0:
            rhythm_type = "Nhịp Chậm Điện Ảnh (Cinematic / Commercial)"

        summary = (
            f"📊 KẾT QUẢ PHÂN TÍCH NHỊP TIMELINE:\n"
            f"• Tổng thời lượng: {dur:.2f} giây\n"
            f"• Tổng số phân đoạn (Clips/Cuts): {total_segments}\n"
            f"• Tốc độ chuyển cảnh trung bình: {avg_cut:.2f} giây / clip\n"
            f"• Đánh giá nhịp độ: {rhythm_type}\n"
            f"• Đề xuất Editor: Áp dụng Keyframe In/Out so le 250ms cho các cut nhanh,\n"
            f"  và Speed Ramp (Hero Ramp) cho các đoạn trên 1.5s."
        )
        self.lbl_ai_rhythm_summary.config(text=summary)

    def _generate_single_png_filmstrip(self):
        """
        User Request:
        'chỉ cần tách rồi gộp thành 1 file png tổng, không cần tách như vậy, tách vậy sẽ chiếm dung lượng nhiều'
        Extracts representative key frames and merges them into a SINGLE summary contact-sheet PNG!
        """
        if not self.current_project or not self.current_project_folder:
            return

        proj_path = self.current_project.get("project_path")
        output_png = os.path.join(proj_path, "filmstrip_summary_rhythm.png")

        # Find target video or sample project
        video_src = None
        for track in self.current_project.get("tracks", []):
            for seg in track.get("segments", []):
                fp = seg.get("file_path", "")
                if fp.lower().endswith((".mp4", ".mov", ".m4v")):
                    video_src = fp
                    break
            if video_src:
                break

        if not video_src:
            messagebox.showinfo(
                "Thông Báo",
                "Dự án này là tập hợp các layer PNG đồ họa tĩnh.\n"
                "Tính năng Filmstrip trích xuất chuỗi nhịp hoạt động tối ưu nhất với file video thực tế."
            )
            return

        # Use FFmpeg built-in tile filter to produce 1 single compact PNG
        # Grid: 4 columns x 3 rows = 12 representative rhythm points
        try:
            cmd = [
                "ffmpeg", "-y", "-i", video_src,
                "-vf", "fps=1,scale=240:-1,tile=4x3",
                "-vframes", "1",
                output_png
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if res.returncode == 0 and os.path.exists(output_png):
                size_kb = os.path.getsize(output_png) // 1024
                ans = messagebox.askyesno(
                    "Thành Công!",
                    f"Đã xuất 1 file PNG tổng duy nhất ({size_kb} KB):\n{output_png}\n\n"
                    f"Bạn có muốn mở xem ngay tấm ảnh này không?"
                )
                if ans:
                    if platform.system() == "Darwin":
                        subprocess.run(["open", output_png])
                    elif platform.system() == "Windows":
                        os.startfile(output_png)
            else:
                messagebox.showerror("Lỗi Xuất Filmstrip", f"FFmpeg trả về lỗi:\n{res.stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất file filmstrip tổng:\n{e}")

    # --------------------------------------------------------------------------
    # ROLLBACK & BACKUP ACTIONS
    # --------------------------------------------------------------------------
    def _show_backup_manager(self):
        self.notebook.select(4)  # Switch to Tab 5 (Backups)

    def _create_manual_backup(self):
        if not self.current_project_folder:
            return
        b_path = self.adapter.backup_project(self.current_project_folder, label="manual")
        self._load_project_by_index(self.proj_combo.current())
        messagebox.showinfo("Đã Sao Lưu", f"Đã tạo bản sao lưu thành công:\n{os.path.basename(b_path)}")

    def _restore_selected_backup(self):
        selected = self.backup_tree.selection()
        if not selected:
            messagebox.showwarning("Chú ý", "Vui lòng chọn 1 bản sao lưu trong danh sách để khôi phục.")
            return

        item = self.backup_tree.item(selected[0])
        filename = item["values"][1]

        if not messagebox.askyesno("Xác Nhận Khôi Phục", f"Bạn có chắc muốn khôi phục dự án về phiên bản:\n{filename}?"):
            return

        try:
            self.adapter.restore_backup(self.current_project_folder, filename)
            self._load_project_by_index(self.proj_combo.current())
            messagebox.showinfo("Thành Công", f"Đã khôi phục hoàn tất từ {filename}!")
        except Exception as e:
            messagebox.showerror("Lỗi Khôi Phục", f"Không thể khôi phục:\n{e}")


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
def main():
    root = tk.Tk()
    app = CapCutStudioDesktopApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
