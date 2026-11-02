"""Tk update window. All network/disk work runs off the Tk thread."""
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk
import urllib.error
import webbrowser

from core import updater
from core.version import APP_VERSION

class UpdateDialog(tk.Toplevel):
    def __init__(self, parent, theme, font):
        super().__init__(parent)
        self.theme = theme
        self.configure(bg=theme["bg_panel"])
        self.title("Cập nhật Keyframe Studio")
        self.geometry("520x460")
        self.resizable(False, False)
        self.transient(parent)
        self.events = queue.Queue()
        self.cancelled = threading.Event()
        self.phase = "idle"
        self.update_info = None
        self.installer = None
        tk.Label(self, text="Cập nhật ứng dụng", bg=theme["bg_panel"], fg=theme["text_main"],
                 font=(font, 17, "bold")).pack(anchor="w", padx=24, pady=(24, 6))
        tk.Label(self, text="Phiên bản hiện tại: " + APP_VERSION, bg=theme["bg_panel"],
                 fg=theme["text_muted"], font=(font, 11)).pack(anchor="w", padx=24)
        self.preview = tk.BooleanVar(value="-preview." in APP_VERSION)
        self.preview_control = tk.Checkbutton(self, text="Nhận cả bản thử nghiệm", variable=self.preview,
            command=self.check, bg=theme["bg_panel"], fg=theme["text_sub"],
            activebackground=theme["bg_panel"], activeforeground=theme["text_main"],
            selectcolor=theme["bg_card"], font=(font, 10))
        self.preview_control.pack(anchor="w", padx=20, pady=(12, 8))
        self.status = tk.Label(self, text="", bg=theme["bg_panel"], fg=theme["text_main"],
                               wraplength=470, justify="left", font=(font, 11))
        self.status.pack(anchor="w", padx=24, pady=(0, 10))
        style = ttk.Style(self)
        style.configure("Update.Horizontal.TProgressbar",
            troughcolor=theme["bg_card"], background=theme["accent_cyan"],
            bordercolor=theme["bg_panel"], lightcolor=theme["accent_cyan"],
            darkcolor=theme["accent_cyan"], borderwidth=0, thickness=6)
        style.configure("Update.TButton", background=theme["accent_cyan"], foreground="#102033",
            bordercolor=theme["accent_cyan"], lightcolor=theme["accent_cyan"],
            darkcolor=theme["accent_cyan"], padding=10)
        style.map("Update.TButton", background=[("active", "#a3ceff"), ("disabled", theme["bg_card"])],
                  foreground=[("disabled", theme["text_muted"])])
        self.progress = ttk.Progressbar(self, maximum=100, style="Update.Horizontal.TProgressbar")
        self.progress.pack(fill="x", padx=24, pady=(0, 12))
        self.notes = tk.Text(self, height=7, wrap="word", relief="flat", borderwidth=0, highlightthickness=0,
            bg=theme["bg_card"], fg=theme["text_sub"], padx=12, pady=10, font=(font, 10))
        self.notes.pack(fill="both", expand=True, padx=24)
        self.notes.configure(state="disabled")
        self.action = ttk.Button(self, text="Kiểm tra cập nhật", command=self.check, style="Update.TButton")
        self.action.pack(fill="x", padx=24, pady=14)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(50, self.check)
        self.after(80, self.poll)

    def close(self):
        if self.phase == "install":
            return
        self.cancelled.set()
        self.destroy()

    def busy(self, phase, text):
        self.phase = phase
        self.status.configure(text=text)
        self.action.configure(state="disabled")
        self.preview_control.configure(state="disabled")

    def worker(self, operation, kind):
        def run():
            try:
                self.events.put((kind, operation()))
            except Exception as error:
                self.events.put(("error", error))
        threading.Thread(target=run, daemon=True).start()

    def check(self):
        if self.phase in ("check", "download", "install"):
            return
        self.installer = None
        self.busy("check", "Đang kiểm tra phiên bản trên GitHub…")
        self.progress.pack(fill="x", padx=24, pady=(0, 12), before=self.notes)
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        include = self.preview.get()
        self.worker(lambda: updater.find_update(include_preview=include), "checked")

    def download(self):
        self.busy("download", "Đang tải bộ cài từ GitHub…")
        self.progress.pack(fill="x", padx=24, pady=(0, 12), before=self.notes)
        self.progress.configure(mode="determinate", value=0)
        self.worker(lambda: updater.download(self.update_info,
                    progress=lambda value: self.events.put(("progress", value)),
                    cancelled=self.cancelled.is_set), "downloaded")

    def install(self):
        self.busy("install", "Đang chuẩn bị cài đặt. App sẽ đóng và tự mở lại sau khi cập nhật.")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.worker(lambda: updater.launch_installer(self.installer), "installed")

    def poll(self):
        if not self.winfo_exists():
            return
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "progress":
                    self.progress.configure(value=value)
                    continue
                self.progress.stop()
                self.preview_control.configure(state="normal")
                self.action.configure(state="normal")
                self.phase = "idle"
                if kind == "checked":
                    self.progress.pack_forget()
                    self.update_info = value
                    if not value:
                        self.status.configure(text="Bạn đang dùng phiên bản mới nhất có bộ cài phù hợp.")
                        self.action.configure(text="Kiểm tra lại", command=self.check)
                        continue
                    self.status.configure(text="Đã có phiên bản " + value["version"])
                    self.notes.configure(state="normal")
                    self.notes.delete("1.0", "end")
                    self.notes.insert("1.0", value["notes"][:12000])
                    self.notes.configure(state="disabled")
                    if getattr(sys, "frozen", False):
                        self.action.configure(text="Tải bản cập nhật", command=self.download)
                    else:
                        self.status.configure(text="Đã có bản " + value["version"] + ". Bản chạy từ source cần cài bản đóng gói để cập nhật trong app.")
                        self.action.configure(text="Mở trang tải về", command=lambda: webbrowser.open(self.update_info["url"]))
                elif kind == "downloaded":
                    self.installer = value
                    self.progress.configure(mode="determinate", value=100)
                    self.status.configure(text="Đã tải và kiểm tra bộ cài. Nhấn bên dưới để đóng app, cài bản mới và mở lại.")
                    self.action.configure(text="Cài và mở lại", command=self.install)
                elif kind == "installed":
                    self.master.destroy()
                    return
                elif kind == "error":
                    if isinstance(value, urllib.error.HTTPError) and value.code in (403, 429):
                        message = "GitHub đang giới hạn lượt kiểm tra. Vui lòng thử lại sau."
                    else:
                        message = str(value)
                    self.status.configure(text="Không thể cập nhật: " + message)
                    self.action.configure(text="Thử lại", command=self.check)
        except queue.Empty:
            pass
        self.after(80, self.poll)
