#!/usr/bin/env python3
"""
CapCut Keyframe Studio Pro - Native Desktop Edition (V2 Refined)
==============================================================
A professional, modern, dark-themed native desktop studio for CapCut project editing.
Built with Python 3 + Tkinter + PIL (Pillow) with custom vector-rendered controls.

Key Highlights:
- Pixel-Perfect Multi-Layer Viewport with strict 9:16/16:9 canvas clipping (No off-screen leaks!)
- Realistic Studio Phone Mockup Monitor with aspect ratio preservation and sub-pixel rotation
- Custom Vector UI Controls (Rounded Buttons, Smooth Scrubber, Pill Toggles, no ugly OS buttons)
- 1-Click Rhythmic Keyframe Presets (Switch In/Out, 1s Pulse, Bounce, Punch Zoom, Shake)
- Speed Ramping Master (Hero Ramp, Bullet Time, Flash, Beat-Sync)
- Point-Lock Keyframe Stabilizer (Dead-Lock 100% & Smooth Damping with Auto-Zoom)
- AI Rhythm Analysis & Single-File Filmstrip PNG Generator
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
import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk

# Base path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.capcut_adapter import CapCutAdapter
from core.keyframe_engine import KeyframeEngine
from core.speed_ramp_engine import SpeedRampEngine
from core.stabilizer_engine import StabilizerEngine

# ==============================================================================
# PROFESSIONAL CAPCUT DARK PALETTE
# ==============================================================================
THEME = {
    "bg_app": "#0e1015",         # Deep obsidian app background
    "bg_panel": "#14161e",       # Sidebar and panel containers
    "bg_card": "#1c1f2b",        # Cards and operation boxes
    "bg_card_hover": "#252938",  # Card hover state
    "bg_header": "#101218",      # Top header bar
    "bg_input": "#252936",       # Combobox / Input field bg
    "border": "#282d3c",         # Subtle dividers
    "border_highlight": "#383f54",
    "accent_cyan": "#00f2fe",    # CapCut Neon Cyan
    "accent_blue": "#3b82f6",    # Action Blue
    "accent_sky": "#38bdf8",     # Highlight Sky
    "accent_green": "#10b981",   # Success Emerald
    "accent_yellow": "#f59e0b",  # Warning Amber
    "accent_red": "#ef4444",     # Delete Ruby Red
    "accent_purple": "#8b5cf6",  # Special Purple
    "text_main": "#ffffff",      # Crisp White
    "text_sub": "#cbd5e1",       # Subdued White
    "text_muted": "#848d9f",     # Dim Gray
    "timeline_bg": "#12141c",    # Timeline canvas
    "timeline_track": "#181a24", # Track row
    "clip_video": "#2563eb",     # Video clip rectangle
    "clip_image": "#7c3aed",     # Image clip rectangle
    "clip_audio": "#059669",     # Audio clip rectangle
    "keyframe_diamond": "#facc15"# Keyframe diamond
}

FONT_FAMILY = "Helvetica"
if platform.system() == "Darwin":
    FONT_FAMILY = "SF Pro Display"


# ==============================================================================
# CUSTOM VECTOR CONTROLS (ROUNDED BUTTONS, SCRUBBERS, PILLS)
# ==============================================================================
class RoundedButton(tk.Canvas):
    """Modern vector rounded button with smooth hover & active animations."""

    def __init__(
        self,
        parent,
        text: str = "",
        width: int = 100,
        height: int = 34,
        radius: int = 12,
        bg_color: str = THEME["bg_card"],
        hover_color: str = THEME["bg_card_hover"],
        text_color: str = THEME["text_main"],
        font: Tuple[str, int, str] = (FONT_FAMILY, 10, "bold"),
        command=None,
        variant: str = "default",
        **kwargs
    ):
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = THEME["bg_panel"]

        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            cursor="pointinghand" if platform.system() == "Darwin" else "hand2",
            **kwargs
        )
        self.btn_text = text
        self.w = width
        self.h = height
        self.r = min(radius, height // 2)
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = font
        self.command = command
        self.variant = variant
        self.is_hovered = False

        if variant == "primary":
            self.bg_color = THEME["accent_cyan"]
            self.hover_color = "#38ef7d"
            self.text_color = "#000000"
        elif variant == "danger":
            self.bg_color = "#3d1417"
            self.hover_color = THEME["accent_red"]
            self.text_color = "#f87171"
        elif variant == "action":
            self.bg_color = "#1e293b"
            self.hover_color = THEME["accent_blue"]
            self.text_color = "#ffffff"

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

        self._draw()

    def set_text(self, text: str, variant: Optional[str] = None):
        self.btn_text = text
        if variant:
            self.variant = variant
            if variant == "primary":
                self.bg_color = THEME["accent_cyan"]
                self.text_color = "#000000"
            elif variant == "warning":
                self.bg_color = THEME["accent_yellow"]
                self.text_color = "#000000"
        self._draw()

    def _draw(self):
        self.delete("all")
        color = self.hover_color if self.is_hovered else self.bg_color
        x0, y0, x1, y1 = 1, 1, self.w - 1, self.h - 1
        r = self.r

        # Draw rounded rectangle arcs & polygons
        self.create_arc(x0, y0, x0 + 2*r, y0 + 2*r, start=90, extent=90, fill=color, outline="")
        self.create_arc(x1 - 2*r, y0, x1, y0 + 2*r, start=0, extent=90, fill=color, outline="")
        self.create_arc(x0, y1 - 2*r, x0 + 2*r, y1, start=180, extent=90, fill=color, outline="")
        self.create_arc(x1 - 2*r, y1 - 2*r, x1, y1, start=270, extent=90, fill=color, outline="")
        self.create_rectangle(x0 + r, y0, x1 - r, y1, fill=color, outline="")
        self.create_rectangle(x0, y0 + r, x1, y1 - r, fill=color, outline="")

        # Draw subtle border if not primary
        if self.variant != "primary":
            border_col = THEME["accent_cyan"] if self.is_hovered else THEME["border"]
            self.create_arc(x0, y0, x0 + 2*r, y0 + 2*r, start=90, extent=90, fill="", outline=border_col, width=1)
            self.create_arc(x1 - 2*r, y0, x1, y0 + 2*r, start=0, extent=90, fill="", outline=border_col, width=1)
            self.create_arc(x0, y1 - 2*r, x0 + 2*r, y1, start=180, extent=90, fill="", outline=border_col, width=1)
            self.create_arc(x1 - 2*r, y1 - 2*r, x1, y1, start=270, extent=90, fill="", outline=border_col, width=1)
            self.create_line(x0 + r, y0, x1 - r, y0, fill=border_col, width=1)
            self.create_line(x0 + r, y1, x1 - r, y1, fill=border_col, width=1)
            self.create_line(x0, y0 + r, x0, y1 - r, fill=border_col, width=1)
            self.create_line(x1, y0 + r, x1, y1 - r, fill=border_col, width=1)

        # Center Text
        txt_col = "#000000" if (self.variant == "primary" or (self.is_hovered and self.variant == "danger")) else self.text_color
        self.create_text(self.w / 2, self.h / 2, text=self.btn_text, fill=txt_col, font=self.font)

    def _on_enter(self, e):
        self.is_hovered = True
        self._draw()

    def _on_leave(self, e):
        self.is_hovered = False
        self._draw()

    def _on_click(self, e):
        if self.command:
            self.command()


class ModernScrubber(tk.Canvas):
    """Custom vector-drawn smooth time scrubber with glowing thumb & progress."""

    def __init__(self, parent, width: int = 400, height: int = 24, on_seek=None, **kwargs):
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = THEME["bg_panel"]

        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            cursor="pointinghand" if platform.system() == "Darwin" else "hand2",
            **kwargs
        )
        self.on_seek = on_seek
        self.duration = 10.0
        self.current_time = 0.0
        self.is_dragging = False

        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Button-1>", self._on_mouse)
        self.bind("<B1-Motion>", self._on_mouse)
        self.bind("<ButtonRelease-1>", self._on_release)

    def set_duration(self, dur: float):
        self.duration = max(0.001, dur)
        self._draw()

    def set_time(self, t: float):
        self.current_time = max(0.0, min(self.duration, t))
        self._draw()

    def _on_mouse(self, event):
        self.is_dragging = True
        w = self.winfo_width()
        margin = 10
        usable_w = w - margin * 2
        rel_x = max(0, min(usable_w, event.x - margin))
        self.current_time = (rel_x / usable_w) * self.duration
        self._draw()
        if self.on_seek:
            self.on_seek(self.current_time)

    def _on_release(self, event):
        self.is_dragging = False
        if self.on_seek:
            self.on_seek(self.current_time)

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 20:
            return

        margin = 10
        usable_w = w - margin * 2
        track_y = h / 2
        track_h = 6

        # Track background
        self.create_line(margin, track_y, w - margin, track_y, fill="#232734", width=track_h, capstyle="round")

        # Progress fill
        ratio = max(0.0, min(1.0, self.current_time / self.duration))
        prog_x = margin + ratio * usable_w
        if prog_x > margin:
            self.create_line(margin, track_y, prog_x, track_y, fill=THEME["accent_cyan"], width=track_h, capstyle="round")

        # Glowing thumb handle
        thumb_r = 7 if self.is_dragging else 6
        # Outer glow
        self.create_oval(
            prog_x - thumb_r - 2, track_y - thumb_r - 2,
            prog_x + thumb_r + 2, track_y + thumb_r + 2,
            fill="#005577", outline=""
        )
        # Main cyan thumb
        self.create_oval(
            prog_x - thumb_r, track_y - thumb_r,
            prog_x + thumb_r, track_y + thumb_r,
            fill=THEME["accent_cyan"], outline="#ffffff", width=1.5
        )


# ==============================================================================
# KEYFRAME INTERPOLATION ENGINE
# ==============================================================================
class KeyframeInterpolator:
    """Evaluates position, scale, rotation, and opacity at time T."""

    @staticmethod
    def evaluate_property(keyframe_list: List[Dict[str, Any]], offset_us: int, default_val: float) -> float:
        if not keyframe_list:
            return default_val
        if len(keyframe_list) == 1:
            vals = keyframe_list[0].get("values", [default_val])
            return float(vals[0]) if vals else default_val

        sorted_kfs = sorted(keyframe_list, key=lambda k: k.get("time_offset", 0))

        if offset_us <= sorted_kfs[0].get("time_offset", 0):
            return float(sorted_kfs[0].get("values", [default_val])[0])
        if offset_us >= sorted_kfs[-1].get("time_offset", 0):
            return float(sorted_kfs[-1].get("values", [default_val])[0])

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
                return v1 + ratio * (v2 - v1)

        return default_val


# ==============================================================================
# HIGH-FIDELITY PIL MULTI-LAYER COMPOSITOR (ZERO LEAKING / BUFFER CLIPPED)
# ==============================================================================
class PILMediaCompositor:
    """
    Renders multi-layer CapCut frames with 100% strict viewport buffer clipping.
    Every layer is rendered strictly inside (cw, ch); off-screen items are naturally clipped.
    """

    def __init__(self):
        self.image_cache: Dict[str, Image.Image] = {}
        self.video_frame_cache: Dict[str, Image.Image] = {}
        self.composite_cache: Dict[str, Image.Image] = {}
        self.lock = threading.Lock()

    def clear_cache(self):
        with self.lock:
            self.image_cache.clear()
            self.video_frame_cache.clear()
            self.composite_cache.clear()

    def _load_image(self, file_path: str) -> Optional[Image.Image]:
        if not file_path or not os.path.exists(file_path):
            return None
        with self.lock:
            if file_path in self.image_cache:
                return self.image_cache[file_path]
        try:
            img = Image.open(file_path).convert("RGBA")
            with self.lock:
                if len(self.image_cache) < 60:
                    self.image_cache[file_path] = img
            return img
        except Exception:
            return None

    def _extract_video_frame(self, file_path: str, time_sec: float) -> Optional[Image.Image]:
        time_key = f"{file_path}_{round(time_sec, 2):.2f}"
        with self.lock:
            if time_key in self.video_frame_cache:
                return self.video_frame_cache[time_key]

        try:
            cmd = [
                "ffmpeg", "-ss", f"{max(0.0, time_sec):.3f}",
                "-i", file_path,
                "-vframes", "1",
                "-strict", "-1",
                "-f", "image2pipe", "-vcodec", "png", "pipe:1"
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
            if res.returncode == 0 and res.stdout:
                img = Image.open(io.BytesIO(res.stdout)).convert("RGBA")
                with self.lock:
                    if len(self.video_frame_cache) < 80:
                        self.video_frame_cache[time_key] = img
                return img
        except Exception:
            pass
        return None

    def composite_scene(
        self,
        active_layers: List[Tuple[int, Dict[str, Any]]],
        t_sec: float,
        cw: int = 360,
        ch: int = 640,
        layer_visibility: Optional[Dict[str, bool]] = None,
        selected_layer_id: Optional[str] = None
    ) -> Tuple[Image.Image, List[Dict[str, Any]]]:
        """
        Composites active layers into a strict (cw, ch) PIL RGBA image.
        Returns: (composited_PIL_image, layer_hud_metadata)
        """
        # Strict (cw, ch) buffer: anything with X > 1.0 or X < -1.0 is naturally clipped!
        comp = Image.new("RGBA", (cw, ch), (15, 17, 24, 255))
        interpolator = KeyframeInterpolator()
        layers_meta = []

        # Sort layers by track ascending (Track 0 back, higher tracks on top)
        sorted_layers = sorted(active_layers, key=lambda x: x[0])

        for track_idx, seg in sorted_layers:
            seg_id = seg.get("id", "")
            fpath = seg.get("file_path", "")
            is_vis = layer_visibility.get(seg_id, True) if layer_visibility else True

            # Evaluate keyframes at current time
            st_s = seg.get("start_seconds", 0.0)
            offset_us = int((t_sec - st_s) * 1_000_000)

            clip_prop = seg.get("clip") or {}
            def_tx = clip_prop.get("transform", {}).get("x", 0.0) if clip_prop.get("transform") else 0.0
            def_ty = clip_prop.get("transform", {}).get("y", 0.0) if clip_prop.get("transform") else 0.0
            def_sx = clip_prop.get("scale", {}).get("x", 1.0) if clip_prop.get("scale") else 1.0
            def_sy = clip_prop.get("scale", {}).get("y", 1.0) if clip_prop.get("scale") else 1.0
            def_rot = clip_prop.get("rotation", 0.0)

            kf_dict = {}
            for kf_group in seg.get("raw_common_keyframes", []):
                ptype = kf_group.get("property_type")
                kf_dict[ptype] = kf_group.get("keyframe_list", [])

            cur_tx = interpolator.evaluate_property(kf_dict.get("KFTypePositionX", []), offset_us, def_tx)
            cur_ty = interpolator.evaluate_property(kf_dict.get("KFTypePositionY", []), offset_us, def_ty)
            cur_sx = interpolator.evaluate_property(kf_dict.get("KFTypeScaleX", []), offset_us, def_sx)
            cur_sy = interpolator.evaluate_property(kf_dict.get("KFTypeScaleY", []), offset_us, def_sy)
            cur_rot = interpolator.evaluate_property(kf_dict.get("KFTypeRotation", []), offset_us, def_rot)

            is_in_viewport = (-1.1 <= cur_tx <= 1.1) and (-1.1 <= cur_ty <= 1.1)

            layers_meta.append({
                "id": seg_id,
                "track": f"V{track_idx}",
                "name": seg.get("name", "Asset"),
                "visible": is_vis,
                "scale": f"{cur_sx:.2f}x",
                "pos": f"({cur_tx:+.2f}, {cur_ty:+.2f})",
                "in_viewport": is_in_viewport
            })

            if not is_vis or not fpath or not os.path.exists(fpath):
                continue

            # Load source image or extract video frame
            is_video = fpath.lower().endswith((".mp4", ".mov", ".m4v", ".avi", ".webm"))
            src_img = None
            if is_video:
                src_time = seg.get("source_start_seconds", 0.0) + (t_sec - st_s) * (seg.get("speed", 1.0) or 1.0)
                src_img = self._extract_video_frame(fpath, src_time)
            else:
                src_img = self._load_image(fpath)

            if not src_img:
                continue

            # Accurate Base Size calculation maintaining material aspect ratio
            iw, ih = src_img.size
            if iw <= 0 or ih <= 0:
                continue
            img_aspect = iw / float(ih)
            canvas_aspect = cw / float(ch)

            if img_aspect > canvas_aspect:
                base_w = cw
                base_h = int(cw / img_aspect)
            else:
                base_h = ch
                base_w = int(ch * img_aspect)

            target_w = max(2, int(base_w * cur_sx))
            target_h = max(2, int(base_h * cur_sy))

            # Resize layer image
            resized = src_img.resize((target_w, target_h), Image.Resampling.BILINEAR)

            # Apply sub-pixel rotation if needed
            if cur_rot != 0.0:
                resized = resized.rotate(-cur_rot, expand=True, resample=Image.Resampling.BILINEAR)
                rw, rh = resized.size
            else:
                rw, rh = target_w, target_h

            # CapCut coordinate mapping:
            # cur_tx: 0.0 = center, +1.0 = right edge (+cw/2), -1.0 = left edge (-cw/2)
            # cur_ty: 0.0 = center, +1.0 = top edge (+ch/2), -1.0 = bottom edge (-ch/2)
            pos_x = int((cw / 2.0) + cur_tx * (cw / 2.0) - (rw / 2.0))
            pos_y = int((ch / 2.0) - cur_ty * (ch / 2.0) - (rh / 2.0))

            # Alpha Composite onto the strict (cw, ch) phone buffer!
            comp.paste(resized, (pos_x, pos_y), resized)

        return comp, layers_meta


# ==============================================================================
# MAIN REFINED DESKTOP STUDIO APPLICATION
# ==============================================================================
class CapCutStudioDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🎬 CapCut Keyframe Studio Pro - Desktop Edition")
        self.root.geometry("1480x940")
        self.root.minsize(1160, 720)
        self.root.configure(bg=THEME["bg_app"])

        # Core Engines
        self.adapter = CapCutAdapter()
        self.compositor = PILMediaCompositor()

        # State
        self.projects_list: List[Dict[str, Any]] = []
        self.current_project_folder: Optional[str] = None
        self.current_project: Optional[Dict[str, Any]] = None
        self.current_time_sec: float = 0.0
        self.is_playing: bool = False
        self.loop_playback: bool = True
        self.play_timer_id = None
        self.selected_layer_id: Optional[str] = None
        self.layer_visibility: Dict[str, bool] = {}

        # Viewport display buffer
        self.current_photo_image: Optional[ImageTk.PhotoImage] = None
        self.vp_width = 360
        self.vp_height = 640

        # Build UI
        self._setup_ttk_styles()
        self._build_header_bar()
        self._build_main_split()
        self._build_timeline_bar()
        self._bind_keyboard_shortcuts()

        # Load projects
        self._refresh_projects()

    # --------------------------------------------------------------------------
    # TTK STYLES
    # --------------------------------------------------------------------------
    def _setup_ttk_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=THEME["bg_panel"], foreground=THEME["text_main"], font=(FONT_FAMILY, 10))
        style.configure("TFrame", background=THEME["bg_panel"])
        style.configure("Card.TFrame", background=THEME["bg_card"])

        # Notebook tabs
        style.configure("TNotebook", background=THEME["bg_app"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=THEME["bg_card"],
            foreground=THEME["text_muted"],
            padding=[16, 9],
            font=(FONT_FAMILY, 10, "bold")
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", THEME["bg_panel"])],
            foreground=[("selected", THEME["accent_cyan"])]
        )

        # Combobox
        style.configure(
            "TCombobox",
            fieldbackground=THEME["bg_input"],
            background=THEME["bg_card"],
            foreground=THEME["text_main"],
            arrowcolor=THEME["accent_cyan"],
            relief="flat"
        )

        # Treeview (Active Layers)
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
            background="#181a24",
            foreground=THEME["accent_cyan"],
            font=(FONT_FAMILY, 9, "bold"),
            relief="flat"
        )
        style.map("Treeview", background=[("selected", "#1e3a8a")], foreground=[("selected", "#ffffff")])

    # --------------------------------------------------------------------------
    # HEADER BAR
    # --------------------------------------------------------------------------
    def _build_header_bar(self):
        header = tk.Frame(self.root, bg=THEME["bg_header"], height=58, padx=18, pady=10)
        header.pack(side="top", fill="x")

        # Brand Title
        brand_box = tk.Frame(header, bg=THEME["bg_header"])
        brand_box.pack(side="left")

        lbl_logo = tk.Label(
            brand_box,
            text="🎬 CAPCUT KEYFRAME STUDIO",
            bg=THEME["bg_header"],
            fg=THEME["accent_cyan"],
            font=(FONT_FAMILY, 13, "bold")
        )
        lbl_logo.pack(side="left")

        lbl_pro = tk.Label(
            brand_box,
            text=" PRO ",
            bg=THEME["accent_cyan"],
            fg="#000000",
            font=(FONT_FAMILY, 9, "bold")
        )
        lbl_pro.pack(side="left", padx=6)

        # Project Selector
        proj_box = tk.Frame(header, bg=THEME["bg_header"], padx=24)
        proj_box.pack(side="left", fill="x", expand=True)

        tk.Label(proj_box, text="Dự án:", bg=THEME["bg_header"], fg=THEME["text_muted"], font=(FONT_FAMILY, 10)).pack(side="left", padx=4)
        self.proj_combo = ttk.Combobox(proj_box, state="readonly", width=34)
        self.proj_combo.pack(side="left", padx=4)
        self.proj_combo.bind("<<ComboboxSelected>>", self._on_project_selected)

        btn_browse = RoundedButton(proj_box, text="📂 Thư Mục...", width=95, height=28, command=self._browse_custom_dir)
        btn_browse.pack(side="left", padx=4)

        btn_refresh = RoundedButton(proj_box, text="🔄 Làm Mới", width=85, height=28, command=self._refresh_projects)
        btn_refresh.pack(side="left", padx=4)

        # Project Meta Badges
        self.meta_frame = tk.Frame(header, bg=THEME["bg_header"])
        self.meta_frame.pack(side="right")

        self.lbl_duration = tk.Label(self.meta_frame, text="⏱️ 00.00s", bg=THEME["bg_card"], fg=THEME["text_main"], font=(FONT_FAMILY, 9, "bold"), padx=10, pady=4)
        self.lbl_duration.pack(side="left", padx=3)

        self.lbl_fps = tk.Label(self.meta_frame, text="⚡ 60 FPS", bg=THEME["bg_card"], fg=THEME["accent_green"], font=(FONT_FAMILY, 9, "bold"), padx=10, pady=4)
        self.lbl_fps.pack(side="left", padx=3)

        self.lbl_tracks = tk.Label(self.meta_frame, text="🎞️ 0 Tracks", bg=THEME["bg_card"], fg=THEME["text_sub"], font=(FONT_FAMILY, 9), padx=10, pady=4)
        self.lbl_tracks.pack(side="left", padx=3)

        self.btn_backups = RoundedButton(self.meta_frame, text="🛡️ Sao Lưu", width=85, height=26, variant="warning", command=self._show_backup_tab)
        self.btn_backups.pack(side="left", padx=4)

    # --------------------------------------------------------------------------
    # MAIN SPLIT CONTAINER
    # --------------------------------------------------------------------------
    def _build_main_split(self):
        self.split_pane = tk.PanedWindow(self.root, orient="horizontal", bg=THEME["bg_app"], sashwidth=4, sashrelief="flat")
        self.split_pane.pack(side="top", fill="both", expand=True, padx=8, pady=4)

        # Left Operations Panel
        self.left_panel = tk.Frame(self.split_pane, bg=THEME["bg_panel"], padx=6, pady=6)
        self.split_pane.add(self.left_panel, minsize=480, width=540)

        # Right Studio Monitor Panel
        self.right_panel = tk.Frame(self.split_pane, bg=THEME["bg_panel"], padx=6, pady=6)
        self.split_pane.add(self.right_panel, minsize=520)

        self._build_operations_tabs()
        self._build_studio_monitor()

    # --------------------------------------------------------------------------
    # LEFT OPERATIONS TABS
    # --------------------------------------------------------------------------
    def _build_operations_tabs(self):
        self.notebook = ttk.Notebook(self.left_panel)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Keyframe Motion Rhythms
        tab_rhythm = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab_rhythm, text="⚡ Nhịp Chuyển Động")
        self._build_tab_rhythm(tab_rhythm)

        # Tab 2: Speed Ramping Master
        tab_speed = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab_speed, text="🏎️ Speed Ramp")
        self._build_tab_speed(tab_speed)

        # Tab 3: Stabilizer Point-Lock
        tab_stab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab_stab, text="🎯 Chống Rung Khóa Mốc")
        self._build_tab_stabilizer(tab_stab)

        # Tab 4: AI Rhythm & Filmstrip (Single PNG)
        tab_ai = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab_ai, text="🤖 AI Nhịp & Filmstrip")
        self._build_tab_ai_inspector(tab_ai)

        # Tab 5: Backups & Rollback
        tab_backup = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab_backup, text="🛡️ Bản Sao Lưu")
        self._build_tab_backups(tab_backup)

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
        group_1click = tk.LabelFrame(inner, text="⚡ 1-CLICK PRESETS CHUYỂN ĐỘNG THEO NHỊP", bg=THEME["bg_panel"], fg=THEME["accent_cyan"], font=(FONT_FAMILY, 10, "bold"), padx=10, pady=8)
        group_1click.pack(fill="x", pady=4)

        presets = [
            ("🔁 Đảo Nhịp In / Out (Switch Clip)", "switch_in_out", "So le nhịp vào/ra giữa các clip liên tiếp (chuẩn Halloween/Sale)"),
            ("⏱️ Nhịp Đều 1 Giây (1s Pulse)", "pulse_1s", "Chu kỳ phóng to thu nhỏ mỗi 1.0 giây theo nhịp TVC"),
            ("⏱️ Nhịp Dài 2 Giây (2s Slow Push)", "pulse_2s", "Đẩy từ từ khung hình mỗi 2.0 giây"),
            ("💥 Giật Nảy Đàn Hồi (Elastic Bounce)", "bounce", "Hiệu ứng nảy lò xo overshoot cực nảy ở đầu clip"),
            ("🔍 Punch-In Zoom (Giật Phóng Nhanh)", "punch_zoom", "Giật phóng cận cảnh 1.35x rồi thu về 1.0x"),
            ("🌊 Lắc Rung Nhẹ (Subtle Shake)", "shake", "Hiệu ứng rung cầm tay tự nhiên sống động")
        ]

        for title, preset_code, desc in presets:
            card = tk.Frame(group_1click, bg=THEME["bg_card"], padx=10, pady=8, highlightbackground=THEME["border"], highlightthickness=1)
            card.pack(fill="x", pady=3)

            top = tk.Frame(card, bg=THEME["bg_card"])
            top.pack(fill="x")
            tk.Label(top, text=title, bg=THEME["bg_card"], fg=THEME["accent_cyan"], font=(FONT_FAMILY, 10, "bold")).pack(side="left")

            btn_apply = RoundedButton(
                top,
                text="Áp Dụng",
                width=76,
                height=26,
                variant="primary",
                command=lambda p=preset_code: self._apply_rhythm_preset(p)
            )
            btn_apply.pack(side="right")

            tk.Label(card, text=desc, bg=THEME["bg_card"], fg=THEME["text_muted"], font=(FONT_FAMILY, 9), anchor="w").pack(fill="x", pady=(2, 0))

        # Target Options
        group_opt = tk.LabelFrame(inner, text="⚙️ PHẠM VI ÁP DỤNG", bg=THEME["bg_panel"], fg=THEME["accent_cyan"], font=(FONT_FAMILY, 10, "bold"), padx=10, pady=8)
        group_opt.pack(fill="x", pady=6)

        row1 = tk.Frame(group_opt, bg=THEME["bg_panel"])
        row1.pack(fill="x", pady=4)
        tk.Label(row1, text="Áp dụng cho Track:", bg=THEME["bg_panel"], fg=THEME["text_main"]).pack(side="left", padx=4)
        self.rhythm_track_combo = ttk.Combobox(row1, state="readonly", width=20)
        self.rhythm_track_combo["values"] = ["Tất cả Video Track", "Chỉ Track 0 (Chính)", "Chỉ Track 1 (Overlay 1)"]
        self.rhythm_track_combo.current(0)
        self.rhythm_track_combo.pack(side="left", padx=4)

        row2 = tk.Frame(group_opt, bg=THEME["bg_panel"])
        row2.pack(fill="x", pady=4)
        tk.Label(row2, text="Đường cong Bezier:", bg=THEME["bg_panel"], fg=THEME["text_main"]).pack(side="left", padx=4)
        self.rhythm_curve_combo = ttk.Combobox(row2, state="readonly", width=20)
        self.rhythm_curve_combo["values"] = ["FreeCurveInOut (Mượt)", "FreeCurveIn", "FreeCurveOut", "Line"]
        self.rhythm_curve_combo.current(0)
        self.rhythm_curve_combo.pack(side="left", padx=4)

        # Scale Spinboxes
        row3 = tk.Frame(group_opt, bg=THEME["bg_panel"])
        row3.pack(fill="x", pady=4)
        tk.Label(row3, text="Scale Bắt đầu:", bg=THEME["bg_panel"], fg=THEME["text_muted"]).pack(side="left", padx=4)
        self.spin_scale_start = ttk.Spinbox(row3, from_=0.5, to=3.0, increment=0.05, width=6)
        self.spin_scale_start.set(1.0)
        self.spin_scale_start.pack(side="left", padx=4)

        tk.Label(row3, text="Scale Đỉnh:", bg=THEME["bg_panel"], fg=THEME["text_muted"]).pack(side="left", padx=10)
        self.spin_scale_peak = ttk.Spinbox(row3, from_=0.5, to=3.0, increment=0.05, width=6)
        self.spin_scale_peak.set(1.25)
        self.spin_scale_peak.pack(side="left", padx=4)

        # Action Buttons
        btn_box = tk.Frame(inner, bg=THEME["bg_panel"])
        btn_box.pack(fill="x", pady=10)

        btn_save = RoundedButton(
            btn_box,
            text="🚀 GHI KEYFRAME VÀO CAPCUT (TỰ ĐỘNG SAO LƯU)",
            width=380,
            height=38,
            variant="primary",
            command=lambda: self._apply_rhythm_preset("pulse_1s")
        )
        btn_save.pack(fill="x", pady=4)

        btn_clear = RoundedButton(
            btn_box,
            text="🧼 Xóa Toàn Bộ Keyframe Trên Track Đã Chọn",
            width=380,
            height=32,
            variant="danger",
            command=self._clear_keyframes_on_track
        )
        btn_clear.pack(fill="x", pady=4)

    def _build_tab_speed(self, parent):
        group_presets = tk.LabelFrame(parent, text="🏎️ CÁC MẪU UỐN TỐC ĐỘ (SPEED CURVE PRESETS)", bg=THEME["bg_panel"], fg=THEME["accent_cyan"], font=(FONT_FAMILY, 10, "bold"), padx=10, pady=8)
        group_presets.pack(fill="x", pady=6)

        speed_presets = [
            ("🌟 Hero Ramp", "hero_ramp", "Nhanh 2.5x -> Chậm 0.3x đỉnh điểm -> Nhanh 3.0x"),
            ("⏱️ Bullet-Time Slowmo", "bullet_time", "1.0x -> 0.15x siêu chậm giữa hành động -> 1.0x"),
            ("⚡ Flash-In / Flash-Out", "flash_in_out", "4.0x vút nhanh vào -> 1.0x -> 4.0x vút ra"),
            ("🥁 Beat-Synced Speed", "beat_sync", "Uốn nhịp tốc độ dồn dập theo nhịp 0.5s"),
            ("🔄 Reset 1.0x Bình Thường", "reset", "Đưa clip trở về tốc độ gốc 1.0x không uốn")
        ]

        for title, code, desc in speed_presets:
            card = tk.Frame(group_presets, bg=THEME["bg_card"], padx=10, pady=8, highlightbackground=THEME["border"], highlightthickness=1)
            card.pack(fill="x", pady=3)

            top = tk.Frame(card, bg=THEME["bg_card"])
            top.pack(fill="x")
            tk.Label(top, text=title, bg=THEME["bg_card"], fg=THEME["accent_cyan"], font=(FONT_FAMILY, 10, "bold")).pack(side="left")

            btn = RoundedButton(
                top,
                text="Áp Dụng",
                width=76,
                height=26,
                variant="primary",
                command=lambda c=code: self._apply_speed_ramp(c)
            )
            btn.pack(side="right")
            tk.Label(card, text=desc, bg=THEME["bg_card"], fg=THEME["text_muted"], font=(FONT_FAMILY, 9)).pack(anchor="w")

        # Curve Visualizer
        group_viz = tk.LabelFrame(parent, text="📈 BIỂU ĐỒ ĐƯỜNG CONG TỐC ĐỘ", bg=THEME["bg_panel"], fg=THEME["accent_cyan"], font=(FONT_FAMILY, 10, "bold"), padx=10, pady=8)
        group_viz.pack(fill="both", expand=True, pady=6)

        self.speed_canvas = tk.Canvas(group_viz, bg="#0d0e14", height=130, highlightthickness=0)
        self.speed_canvas.pack(fill="both", expand=True, pady=4)
        self._draw_speed_curve_preview("hero_ramp")

    def _draw_speed_curve_preview(self, preset_code: str):
        self.speed_canvas.delete("all")
        w = self.speed_canvas.winfo_width() or 400
        h = self.speed_canvas.winfo_height() or 130
        mid_y = h * 0.6

        self.speed_canvas.create_line(20, mid_y, w - 20, mid_y, fill=THEME["border"], dash=(4, 4))
        self.speed_canvas.create_text(w - 15, mid_y, text="1.0x", fill=THEME["text_muted"], font=(FONT_FAMILY, 8), anchor="w")

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

    def _build_tab_stabilizer(self, parent):
        info_box = tk.Frame(parent, bg=THEME["bg_card"], padx=12, pady=10, highlightbackground=THEME["border"], highlightthickness=1)
        info_box.pack(fill="x", pady=6)

        tk.Label(info_box, text="🎯 CHỐNG RUNG KHÓA TRỤC CỐ ĐỊNH (POINT-LOCK)", bg=THEME["bg_card"], fg=THEME["accent_cyan"], font=(FONT_FAMILY, 10, "bold")).pack(anchor="w")
        msg = (
            "Khóa mốc tại 1 điểm cố định (logo, mắt, mặt sản phẩm) và giữ trục tọa độ\n"
            "để loại bỏ rung lắc hoàn toàn. Tự động phóng to (Auto-Zoom 1.05x - 1.25x)\n"
            "và bù trừ keyframe chuyển động để cảnh quay luôn nằm trong khung hình chính."
        )
        tk.Label(info_box, text=msg, bg=THEME["bg_card"], fg=THEME["text_muted"], font=(FONT_FAMILY, 9), justify="left").pack(anchor="w", pady=4)

        group_opt = tk.LabelFrame(parent, text="⚙️ THÔNG SỐ CHỐNG RUNG", bg=THEME["bg_panel"], fg=THEME["accent_cyan"], font=(FONT_FAMILY, 10, "bold"), padx=10, pady=8)
        group_opt.pack(fill="x", pady=6)

        row1 = tk.Frame(group_opt, bg=THEME["bg_panel"])
        row1.pack(fill="x", pady=4)
        tk.Label(row1, text="Chế độ chống rung:", bg=THEME["bg_panel"], fg=THEME["text_main"]).pack(side="left", padx=4)
        self.stab_mode_combo = ttk.Combobox(row1, state="readonly", width=22)
        self.stab_mode_combo["values"] = ["Khóa Mốc Tuyệt Đối (Dead-Lock)", "Giảm Rung Mượt (Smooth Damping)"]
        self.stab_mode_combo.current(0)
        self.stab_mode_combo.pack(side="left", padx=4)

        row2 = tk.Frame(group_opt, bg=THEME["bg_panel"])
        row2.pack(fill="x", pady=4)
        tk.Label(row2, text="Auto-Zoom bảo vệ viền:", bg=THEME["bg_panel"], fg=THEME["text_main"]).pack(side="left", padx=4)
        self.stab_zoom_combo = ttk.Combobox(row2, state="readonly", width=10)
        self.stab_zoom_combo["values"] = ["1.05x", "1.10x", "1.15x", "1.20x", "1.25x"]
        self.stab_zoom_combo.current(1)
        self.stab_zoom_combo.pack(side="left", padx=4)

        btn_stab = RoundedButton(
            parent,
            text="🎯 PHÂN TÍCH & TẠO KEYFRAME CHỐNG RUNG KHÓA MỐC",
            width=380,
            height=38,
            variant="primary",
            command=self._execute_stabilizer
        )
        btn_stab.pack(fill="x", pady=12)

    def _build_tab_ai_inspector(self, parent):
        info_box = tk.Frame(parent, bg=THEME["bg_card"], padx=12, pady=10, highlightbackground=THEME["border"], highlightthickness=1)
        info_box.pack(fill="x", pady=6)

        tk.Label(info_box, text="🤖 AI PHÂN TÍCH NHỊP & XUẤT FILMSTRIP TỔNG", bg=THEME["bg_card"], fg=THEME["accent_cyan"], font=(FONT_FAMILY, 10, "bold")).pack(anchor="w")
        tk.Label(
            info_box,
            text="Tách các frame đại diện của video và gộp thành 1 tấm ảnh PNG tổng\nđể review nhịp cắt nhanh, không tốn dung lượng ổ cứng.",
            bg=THEME["bg_card"],
            fg=THEME["text_muted"],
            font=(FONT_FAMILY, 9),
            justify="left"
        ).pack(anchor="w", pady=4)

        self.ai_stats_card = tk.Frame(parent, bg=THEME["bg_card"], padx=10, pady=8)
        self.ai_stats_card.pack(fill="x", pady=6)
        self.lbl_ai_rhythm_summary = tk.Label(
            self.ai_stats_card,
            text="Chưa phân tích. Nhấn nút bên dưới để quét nhịp timeline.",
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            font=(FONT_FAMILY, 9),
            justify="left"
        )
        self.lbl_ai_rhythm_summary.pack(anchor="w")

        btn_inspect = RoundedButton(
            parent,
            text="🔍 PHÂN TÍCH NHỊP VIDEO TIMELINE",
            width=380,
            height=34,
            variant="action",
            command=self._analyze_video_rhythm
        )
        btn_inspect.pack(fill="x", pady=4)

        btn_filmstrip = RoundedButton(
            parent,
            text="🖼️ XUẤT FILMSTRIP TỔNG (1 FILE PNG DUY NHẤT)",
            width=380,
            height=38,
            variant="primary",
            command=self._generate_single_png_filmstrip
        )
        btn_filmstrip.pack(fill="x", pady=4)

    def _build_tab_backups(self, parent):
        tk.Label(parent, text="🛡️ LỊCH SỬ BẢN SAO LƯU DỰ ÁN (AN TOÀN TUYỆT ĐỐI)", bg=THEME["bg_panel"], fg=THEME["accent_cyan"], font=(FONT_FAMILY, 10, "bold")).pack(anchor="w", pady=4)

        self.backup_tree = ttk.Treeview(parent, columns=("time", "filename"), show="headings", height=8)
        self.backup_tree.heading("time", text="Thời Gian Sao Lưu")
        self.backup_tree.heading("filename", text="Tên File Bản Sao")
        self.backup_tree.column("time", width=150)
        self.backup_tree.column("filename", width=250)
        self.backup_tree.pack(fill="both", expand=True, pady=6)

        btn_box = tk.Frame(parent, bg=THEME["bg_panel"])
        btn_box.pack(fill="x", pady=6)

        btn_restore = RoundedButton(btn_box, text="↩️ Khôi Phục Bản Này", width=160, height=32, variant="primary", command=self._restore_selected_backup)
        btn_restore.pack(side="left", padx=4)

        btn_create = RoundedButton(btn_box, text="➕ Tạo Bản Sao Mới", width=140, height=32, command=self._create_manual_backup)
        btn_create.pack(side="left", padx=4)

    # --------------------------------------------------------------------------
    # RIGHT STUDIO MONITOR & ACTIVE LAYERS INSPECTOR
    # --------------------------------------------------------------------------
    def _build_studio_monitor(self):
        # Header of monitor
        top_ctrl = tk.Frame(self.right_panel, bg=THEME["bg_panel"])
        top_ctrl.pack(side="top", fill="x", pady=(0, 4))

        tk.Label(
            top_ctrl,
            text="📺 TRÌNH PHÁT ĐA LỚP (STUDIO COMPOSITE MONITOR)",
            bg=THEME["bg_panel"],
            fg=THEME["accent_cyan"],
            font=(FONT_FAMILY, 11, "bold")
        ).pack(side="left")

        self.lbl_viewport_info = tk.Label(
            top_ctrl,
            text="1080×1920 (9:16)",
            bg=THEME["bg_card"],
            fg=THEME["accent_green"],
            font=(FONT_FAMILY, 9, "bold"),
            padx=8,
            pady=2
        )
        self.lbl_viewport_info.pack(side="right")

        # Phone Bezel Mockup Container (Zero-leakage Canvas)
        bezel_frame = tk.Frame(self.right_panel, bg="#08090d", highlightbackground="#222634", highlightthickness=1)
        bezel_frame.pack(side="top", fill="both", expand=True, padx=4, pady=2)

        self.preview_canvas = tk.Canvas(
            bezel_frame,
            bg="#08090d",
            highlightthickness=0
        )
        self.preview_canvas.pack(fill="both", expand=True)
        self.preview_canvas.bind("<Configure>", lambda e: self._render_current_frame())

        # Transport Controls Bar
        ctrl_bar = tk.Frame(self.right_panel, bg=THEME["bg_panel"], pady=4)
        ctrl_bar.pack(side="top", fill="x")

        # Custom Vector Transport Buttons
        btn_first = RoundedButton(ctrl_bar, text="⏮", width=42, height=30, command=self._step_to_start)
        btn_first.pack(side="left", padx=2)

        btn_prev = RoundedButton(ctrl_bar, text="◀ 1F", width=52, height=30, command=self._step_prev_frame)
        btn_prev.pack(side="left", padx=2)

        self.btn_play = RoundedButton(ctrl_bar, text="▶ PHÁT", width=90, height=30, variant="primary", command=self._toggle_playback)
        self.btn_play.pack(side="left", padx=4)

        btn_next = RoundedButton(ctrl_bar, text="1F ▶", width=52, height=30, command=self._step_next_frame)
        btn_next.pack(side="left", padx=2)

        btn_last = RoundedButton(ctrl_bar, text="⏭", width=42, height=30, command=self._step_to_end)
        btn_last.pack(side="left", padx=2)

        self.btn_loop = RoundedButton(ctrl_bar, text="🔁 Lặp: BẬT", width=85, height=30, command=self._toggle_loop)
        self.btn_loop.pack(side="left", padx=4)

        # Timecode badge
        self.lbl_timecode = tk.Label(
            ctrl_bar,
            text="00:00.000 / 00:00.000 (Frame 0 / 0)",
            bg=THEME["bg_card"],
            fg=THEME["accent_cyan"],
            font=("Menlo", 9, "bold"),
            padx=10,
            pady=4
        )
        self.lbl_timecode.pack(side="right", padx=4)

        # Custom Vector Scrubber
        self.scrubber = ModernScrubber(self.right_panel, height=22, on_seek=self._on_scrubber_seek)
        self.scrubber.pack(side="top", fill="x", pady=2)

        # Active Layers Table Inspector (Bottom of right panel)
        layer_box = tk.LabelFrame(self.right_panel, text="📑 DANH SÁCH LAYER TẠI FRAME HIỆN TẠI (CLICK [👁️] ĐỂ ẨN/HIỆN)", bg=THEME["bg_panel"], fg=THEME["accent_cyan"], font=(FONT_FAMILY, 9, "bold"), padx=6, pady=4)
        layer_box.pack(side="bottom", fill="x", pady=(4, 0))

        self.layer_tree = ttk.Treeview(
            layer_box,
            columns=("visible", "track", "name", "scale", "position", "status"),
            show="headings",
            height=4
        )
        self.layer_tree.heading("visible", text="Hiện")
        self.layer_tree.heading("track", text="Track")
        self.layer_tree.heading("name", text="Tên Clip / Asset")
        self.layer_tree.heading("scale", text="Scale")
        self.layer_tree.heading("position", text="Tọa Độ (X, Y)")
        self.layer_tree.heading("status", text="Trạng Thái Khung Hình")

        self.layer_tree.column("visible", width=42, anchor="center")
        self.layer_tree.column("track", width=60, anchor="center")
        self.layer_tree.column("name", width=180)
        self.layer_tree.column("scale", width=65, anchor="center")
        self.layer_tree.column("position", width=105, anchor="center")
        self.layer_tree.column("status", width=130, anchor="center")
        self.layer_tree.pack(fill="x", expand=True)
        self.layer_tree.bind("<ButtonRelease-1>", self._on_layer_tree_click)

    # --------------------------------------------------------------------------
    # BOTTOM VISUAL TIMELINE BAR
    # --------------------------------------------------------------------------
    def _build_timeline_bar(self):
        timeline_frame = tk.Frame(self.root, bg=THEME["timeline_bg"], height=150, highlightbackground=THEME["border"], highlightthickness=1)
        timeline_frame.pack(side="bottom", fill="x", padx=8, pady=(0, 6))

        tl_header = tk.Frame(timeline_frame, bg=THEME["bg_header"], height=22, padx=8)
        tl_header.pack(side="top", fill="x")

        tk.Label(
            tl_header,
            text="🎞️ DÒNG THỜI GIAN ĐA TRACK (VISUAL TIMELINE) - ◆ KIM CƯƠNG KEYFRAME",
            bg=THEME["bg_header"],
            fg=THEME["accent_cyan"],
            font=(FONT_FAMILY, 9, "bold")
        ).pack(side="left")

        self.timeline_canvas = tk.Canvas(timeline_frame, bg=THEME["timeline_bg"], height=128, highlightthickness=0)
        self.timeline_canvas.pack(side="top", fill="both", expand=True)
        self.timeline_canvas.bind("<Configure>", lambda e: self._draw_timeline())
        self.timeline_canvas.bind("<Button-1>", self._on_timeline_click)
        self.timeline_canvas.bind("<B1-Motion>", self._on_timeline_click)

    def _bind_keyboard_shortcuts(self):
        self.root.bind("<space>", lambda e: self._toggle_playback())
        self.root.bind("<Left>", lambda e: self._step_prev_frame())
        self.root.bind("<Right>", lambda e: self._step_next_frame())
        self.root.bind("<Home>", lambda e: self._step_to_start())
        self.root.bind("<End>", lambda e: self._step_to_end())

    # --------------------------------------------------------------------------
    # PROJECT LOADING
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

        dur = self.current_project.get("duration_seconds", 0.0)
        fps = self.current_project.get("fps", 30) or 30
        c_w = self.current_project.get("canvas_width", 1080)
        c_h = self.current_project.get("canvas_height", 1920)
        tracks = self.current_project.get("tracks", [])

        self.lbl_duration.config(text=f"⏱️ {dur:.2f}s")
        self.lbl_fps.config(text=f"⚡ {fps} FPS")
        self.lbl_tracks.config(text=f"🎞️ {len(tracks)} Tracks")
        self.lbl_viewport_info.config(text=f"{c_w}×{c_h} ({self.current_project.get('canvas_ratio', '9:16')})")

        self.scrubber.set_duration(dur)
        self.current_time_sec = min(self.current_time_sec, dur)

        self.compositor.clear_cache()
        self.layer_visibility.clear()
        self._refresh_backup_tree()

        self._render_current_frame()
        self._draw_timeline()

    def _refresh_backup_tree(self):
        self.backup_tree.delete(*self.backup_tree.get_children())
        if not self.current_project:
            return
        backups = self.current_project.get("backups", [])
        self.btn_backups.set_text(f"🛡️ {len(backups)} Bản")
        for b in backups:
            self.backup_tree.insert("", "end", values=(b.get("time"), b.get("filename")))

    # --------------------------------------------------------------------------
    # TRANSPORT & PLAYBACK
    # --------------------------------------------------------------------------
    def _step_to_start(self):
        self.current_time_sec = 0.0
        self.scrubber.set_time(0.0)
        self._render_current_frame()
        self._draw_timeline()

    def _step_to_end(self):
        if not self.current_project:
            return
        dur = self.current_project.get("duration_seconds", 0.0)
        self.current_time_sec = dur
        self.scrubber.set_time(dur)
        self._render_current_frame()
        self._draw_timeline()

    def _step_prev_frame(self):
        if not self.current_project:
            return
        fps = self.current_project.get("fps", 30) or 30
        self.current_time_sec = max(0.0, self.current_time_sec - (1.0 / fps))
        self.scrubber.set_time(self.current_time_sec)
        self._render_current_frame()
        self._draw_timeline()

    def _step_next_frame(self):
        if not self.current_project:
            return
        dur = self.current_project.get("duration_seconds", 0.0)
        fps = self.current_project.get("fps", 30) or 30
        self.current_time_sec = min(dur, self.current_time_sec + (1.0 / fps))
        self.scrubber.set_time(self.current_time_sec)
        self._render_current_frame()
        self._draw_timeline()

    def _toggle_loop(self):
        self.loop_playback = not self.loop_playback
        txt = "🔁 Lặp: BẬT" if self.loop_playback else "🔁 Lặp: TẮT"
        self.btn_loop.set_text(txt)

    def _toggle_playback(self):
        if self.is_playing:
            self.is_playing = False
            self.btn_play.set_text("▶ PHÁT", variant="primary")
            if self.play_timer_id:
                self.root.after_cancel(self.play_timer_id)
                self.play_timer_id = None
        else:
            self.is_playing = True
            self.btn_play.set_text("⏸ DỪNG", variant="warning")
            self._playback_loop()

    def _playback_loop(self):
        if not self.is_playing or not self.current_project:
            return

        dur = self.current_project.get("duration_seconds", 0.0)
        fps = self.current_project.get("fps", 30) or 30
        dt = 1.0 / fps

        self.current_time_sec += dt
        if self.current_time_sec > dur:
            if self.loop_playback:
                self.current_time_sec = 0.0
            else:
                self.current_time_sec = dur
                self._toggle_playback()
                return

        self.scrubber.set_time(self.current_time_sec)
        self._render_current_frame()
        self._draw_timeline()

        delay_ms = int(1000.0 / fps)
        self.play_timer_id = self.root.after(delay_ms, self._playback_loop)

    def _on_scrubber_seek(self, t: float):
        self.current_time_sec = t
        self._render_current_frame()
        self._draw_timeline()

    # --------------------------------------------------------------------------
    # PIXEL-PERFECT MULTI-LAYER VIEWPORT RENDERING (CLIPPED BUFFER)
    # --------------------------------------------------------------------------
    def _render_current_frame(self):
        self.preview_canvas.delete("all")
        if not self.current_project:
            return

        cw = self.preview_canvas.winfo_width()
        ch = self.preview_canvas.winfo_height()
        if cw <= 50:
            cw = 500
        if ch <= 50:
            ch = 560

        proj_w = self.current_project.get("canvas_width") or 1080
        proj_h = self.current_project.get("canvas_height") or 1920
        aspect = proj_w / float(proj_h)

        # Fit phone screen within canvas
        pad = 20
        avail_w = cw - pad * 2
        avail_h = ch - pad * 2
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

        # Collect active layers at current time
        t_sec = self.current_time_sec
        active_layers = []
        tracks = self.current_project.get("tracks", [])
        for track in tracks:
            if track.get("type") != "video":
                continue
            for seg in track.get("segments", []):
                st = seg.get("start_seconds", 0.0)
                du = seg.get("duration_seconds", 0.0)
                if st <= t_sec <= st + du:
                    active_layers.append((track.get("index", 0), seg))

        # Composite scene onto strict (vp_w, vp_h) buffer via PIL
        comp_img, layers_meta = self.compositor.composite_scene(
            active_layers,
            t_sec,
            cw=vp_w,
            ch=vp_h,
            layer_visibility=self.layer_visibility,
            selected_layer_id=self.selected_layer_id
        )

        # Convert to PhotoImage and render onto canvas
        self.current_photo_image = ImageTk.PhotoImage(comp_img)

        # Draw phone bezel / drop shadow
        self.preview_canvas.create_rectangle(vx0 - 2, vy0 - 2, vx1 + 2, vy1 + 2, fill="#1c1f2b", outline=THEME["border"], width=1)
        # Draw strictly clipped composite image
        self.preview_canvas.create_image(vx0, vy0, image=self.current_photo_image, anchor="nw")
        # Draw screen outline border
        self.preview_canvas.create_rectangle(vx0, vy0, vx1, vy1, outline="#33384a", width=1)

        # Update Active Layers Treeview
        self.layer_tree.delete(*self.layer_tree.get_children())
        for meta in layers_meta:
            eye_sym = "👁️" if meta["visible"] else "🚫"
            status_txt = "🟢 Trong Khung" if meta["in_viewport"] else "⚪ Ngoài Khung"
            item_id = self.layer_tree.insert(
                "",
                "end",
                values=(eye_sym, meta["track"], meta["name"], meta["scale"], meta["pos"], status_txt)
            )
            self.layer_tree.item(item_id, tags=(meta["id"],))

        # Viewport HUD Overlay (inside screen bounds)
        dur = self.current_project.get("duration_seconds", 0.0)
        fps = self.current_project.get("fps", 30) or 30
        frame_idx = int(t_sec * fps)
        total_frames = int(dur * fps)

        time_str = f"{int(t_sec//60):02d}:{t_sec%60:06.3f}"
        dur_str = f"{int(dur//60):02d}:{dur%60:06.3f}"
        self.lbl_timecode.config(text=f"{time_str} / {dur_str} (Frame {frame_idx} / {total_frames})")

        # Bottom-right timecode pill inside viewport
        tc_w = 75
        tc_h = 18
        self.preview_canvas.create_rectangle(vx1 - tc_w - 6, vy1 - tc_h - 6, vx1 - 6, vy1 - 6, fill="#0a0c10", outline="#222634")
        self.preview_canvas.create_text(vx1 - 10, vy1 - 15, text=time_str, fill=THEME["accent_cyan"], font=("Menlo", 9, "bold"), anchor="e")

        # Bottom-left layers active badge inside viewport
        self.preview_canvas.create_text(vx0 + 10, vy1 - 15, text=f"{len(active_layers)} Layers", fill=THEME["text_muted"], font=(FONT_FAMILY, 8, "bold"), anchor="w")

    def _on_layer_tree_click(self, event):
        item = self.layer_tree.identify_row(event.y)
        col = self.layer_tree.identify_column(event.x)
        if not item:
            return
        tags = self.layer_tree.item(item, "tags")
        if not tags:
            return
        seg_id = tags[0]

        if col == "#1":  # Toggle visibility
            cur_vis = self.layer_visibility.get(seg_id, True)
            self.layer_visibility[seg_id] = not cur_vis
            self._render_current_frame()
        else:
            self.selected_layer_id = seg_id
            self._render_current_frame()

    # --------------------------------------------------------------------------
    # VISUAL MULTI-TRACK TIMELINE
    # --------------------------------------------------------------------------
    def _draw_timeline(self):
        self.timeline_canvas.delete("all")
        if not self.current_project:
            return

        w = self.timeline_canvas.winfo_width() or 800
        h = self.timeline_canvas.winfo_height() or 128
        dur = self.current_project.get("duration_seconds", 0.0)
        if dur <= 0:
            return

        margin_left = 60
        margin_right = 20
        usable_w = w - margin_left - margin_right

        # Time Ruler
        ruler_h = 22
        self.timeline_canvas.create_rectangle(0, 0, w, ruler_h, fill="#0c0e14", outline="")

        sec_step = 1.0 if dur <= 20 else 2.0
        cur_s = 0.0
        while cur_s <= dur:
            x = margin_left + (cur_s / dur) * usable_w
            self.timeline_canvas.create_line(x, ruler_h - 5, x, ruler_h, fill="#3b4256")
            self.timeline_canvas.create_text(x + 2, ruler_h - 12, text=f"{int(cur_s)}s", fill=THEME["text_muted"], font=(FONT_FAMILY, 8), anchor="w")
            cur_s += sec_step

        # Track rows
        tracks = self.current_project.get("tracks", [])
        num_tracks = min(4, len(tracks))
        track_row_h = (h - ruler_h) // max(1, num_tracks)

        for i in range(num_tracks):
            track = tracks[i]
            t_idx = track.get("index", i)
            t_type = track.get("type", "video")
            row_y0 = ruler_h + i * track_row_h
            row_y1 = row_y0 + track_row_h

            bg_color = THEME["timeline_track"] if i % 2 == 0 else "#151720"
            self.timeline_canvas.create_rectangle(0, row_y0, w, row_y1, fill=bg_color, outline=THEME["border"], width=1)

            t_label = f"V{t_idx}" if t_type == "video" else f"A{t_idx}"
            self.timeline_canvas.create_text(24, (row_y0 + row_y1)//2, text=t_label, fill=THEME["accent_cyan"], font=(FONT_FAMILY, 9, "bold"))

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

                self.timeline_canvas.create_rectangle(
                    x0, clip_y0, x1, clip_y1,
                    fill=fill_col, outline="#3b82f6", width=1
                )

                cname = seg.get("name", "")
                if len(cname) > 14:
                    cname = cname[:12] + ".."
                self.timeline_canvas.create_text(x0 + 4, (clip_y0 + clip_y1)//2, text=cname, fill="#ffffff", font=(FONT_FAMILY, 8), anchor="w")

                # Keyframe Diamonds
                for kf_group in seg.get("raw_common_keyframes", []):
                    for kf in kf_group.get("keyframe_list", []):
                        kf_offset_s = kf.get("time_offset", 0) / 1_000_000.0
                        kf_abs_s = st + kf_offset_s
                        kx = margin_left + (kf_abs_s / dur) * usable_w
                        ky = (clip_y0 + clip_y1) // 2

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
        self.timeline_canvas.create_polygon(
            playhead_x - 5, 0,
            playhead_x + 5, 0,
            playhead_x, 8,
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
        self.scrubber.set_time(self.current_time_sec)
        self._render_current_frame()
        self._draw_timeline()

    # --------------------------------------------------------------------------
    # ACTIONS: RHYTHM PRESETS, SPEED, STABILIZER, FILMSTRIP
    # --------------------------------------------------------------------------
    def _apply_rhythm_preset(self, preset_code: str):
        if not self.current_project or not self.current_project_folder:
            messagebox.showwarning("Chú ý", "Vui lòng chọn một dự án CapCut trước.")
            return

        folder = self.current_project_folder
        info_file = self.current_project.get("info_file")
        with open(info_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        scale_peak = float(self.spin_scale_peak.get() or 1.25)
        target_choice = self.rhythm_track_combo.get()
        applied_count = 0

        for t_idx, track in enumerate(data.get("tracks", [])):
            if track.get("type") != "video":
                continue
            if "Track 0" in target_choice and t_idx != 0:
                continue
            if "Track 1" in target_choice and t_idx != 1:
                continue

            for s_idx, seg in enumerate(track.get("segments", [])):
                du_us = seg.get("target_timerange", {}).get("duration", 0)
                if du_us <= 0:
                    continue

                new_kfs = []
                if preset_code == "switch_in_out":
                    direction = "up" if s_idx % 2 == 0 else "down"
                    new_kfs = KeyframeEngine.preset_rhythmic_switch_entrance(du_us, direction=direction, transition_duration_ms=220)
                elif preset_code == "pulse_1s":
                    new_kfs = KeyframeEngine.preset_rhythmic_pulse_step(du_us, interval_seconds=1.0, motion_type="bounce", bounce_scale=scale_peak)
                elif preset_code == "pulse_2s":
                    new_kfs = KeyframeEngine.preset_rhythmic_pulse_step(du_us, interval_seconds=2.0, motion_type="bounce", bounce_scale=scale_peak)
                elif preset_code == "bounce":
                    new_kfs = KeyframeEngine.preset_bounce(du_us, bounce_scale=scale_peak, bounce_count=2)
                elif preset_code == "punch_zoom":
                    new_kfs = KeyframeEngine.preset_punch_zoom(du_us, peak_scale=scale_peak, punch_duration_ms=200)
                elif preset_code == "shake":
                    new_kfs = KeyframeEngine.preset_camera_shake(du_us, intensity=0.03, frequency_hz=10)

                if new_kfs:
                    seg["common_keyframes"] = new_kfs
                    applied_count += 1

        if applied_count > 0:
            self.adapter.save_project_data(folder, data)
            self._load_project_by_index(self.proj_combo.current())
            messagebox.showinfo("Thành Công", f"Đã áp dụng preset '{preset_code}' vào {applied_count} clip!\nBản sao lưu đã được tự động lưu an toàn.")
        else:
            messagebox.showwarning("Thông Báo", "Không tìm thấy clip video nào phù hợp để áp dụng.")

    def _clear_keyframes_on_track(self):
        if not self.current_project or not self.current_project_folder:
            return
        if not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa tất cả keyframe trên track đã chọn?"):
            return

        folder = self.current_project_folder
        info_file = self.current_project.get("info_file")
        with open(info_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        target_choice = self.rhythm_track_combo.get()
        cleared = 0
        for t_idx, track in enumerate(data.get("tracks", [])):
            if track.get("type") != "video":
                continue
            if "Track 0" in target_choice and t_idx != 0:
                continue
            if "Track 1" in target_choice and t_idx != 1:
                continue
            for seg in track.get("segments", []):
                if seg.get("common_keyframes"):
                    seg["common_keyframes"] = []
                    cleared += 1

        self.adapter.save_project_data(folder, data)
        self._load_project_by_index(self.proj_combo.current())
        messagebox.showinfo("Đã Xóa", f"Đã xóa keyframe khỏi {cleared} clip.")

    def _apply_speed_ramp(self, preset_code: str):
        if not self.current_project or not self.current_project_folder:
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
            return

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
            messagebox.showinfo("Thông Báo", "Dự án hiện tại là đồ họa/ảnh PNG.\nTính năng chống rung khóa mốc áp dụng tốt nhất cho video quay thực tế.")
            return

        try:
            mode = "dead_lock" if "Khóa Mốc" in self.stab_mode_combo.get() else "smooth"
            zoom_val = float(self.stab_zoom_combo.get().replace("x", ""))

            engine = StabilizerEngine()
            kfs = engine.stabilize_video_clip(
                target_video,
                target_seg.get("start_seconds", 0.0),
                target_seg.get("duration_seconds", 0.0),
                mode=mode,
                auto_zoom=zoom_val
            )

            info_file = self.current_project.get("info_file")
            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for track in data.get("tracks", []):
                for s in track.get("segments", []):
                    if s.get("id") == target_seg.get("id"):
                        s["common_keyframes"] = kfs
                        break

            self.adapter.save_project_data(self.current_project_folder, data)
            self._load_project_by_index(self.proj_combo.current())
            messagebox.showinfo("Thành Công", f"Đã tạo keyframe chống rung khóa mốc (Auto-Zoom {zoom_val}x)!")
        except Exception as e:
            messagebox.showerror("Lỗi Chống Rung", f"Không thể thực thi:\n{e}")

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
            f"• Đề xuất Editor: Áp dụng Keyframe In/Out so le 220ms cho các cut nhanh,\n"
            f"  và Speed Ramp (Hero Ramp) cho các đoạn trên 1.5s."
        )
        self.lbl_ai_rhythm_summary.config(text=summary)

    def _generate_single_png_filmstrip(self):
        """Generates 1 single contact sheet PNG representing the timeline rhythm."""
        if not self.current_project or not self.current_project_folder:
            return

        proj_path = self.current_project.get("project_path")
        output_png = os.path.join(proj_path, "filmstrip_summary_rhythm.png")

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
            messagebox.showinfo("Thông Báo", "Dự án hiện tại là tập hợp các layer PNG.\nTính năng Filmstrip trích xuất chuỗi nhịp tối ưu nhất với file video thực tế.")
            return

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
                    f"Đã xuất 1 file PNG tổng duy nhất ({size_kb} KB):\n{output_png}\n\nBạn có muốn mở xem ngay tấm ảnh này không?"
                )
                if ans:
                    if platform.system() == "Darwin":
                        subprocess.run(["open", output_png])
                    elif platform.system() == "Windows":
                        os.startfile(output_png)
            else:
                messagebox.showerror("Lỗi Xuất Filmstrip", "FFmpeg không thể trích xuất filmstrip.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất file filmstrip tổng:\n{e}")

    def _show_backup_tab(self):
        self.notebook.select(4)

    def _create_manual_backup(self):
        if not self.current_project_folder:
            return
        b_path = self.adapter.backup_project(self.current_project_folder, label="manual")
        self._load_project_by_index(self.proj_combo.current())
        messagebox.showinfo("Đã Sao Lưu", f"Đã tạo bản sao lưu an toàn:\n{os.path.basename(b_path)}")

    def _restore_selected_backup(self):
        selected = self.backup_tree.selection()
        if not selected:
            messagebox.showwarning("Chú ý", "Vui lòng chọn 1 bản sao lưu trong danh sách.")
            return

        item = self.backup_tree.item(selected[0])
        filename = item["values"][1]

        if not messagebox.askyesno("Xác Nhận", f"Bạn có chắc muốn khôi phục về bản sao lưu:\n{filename}?"):
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
