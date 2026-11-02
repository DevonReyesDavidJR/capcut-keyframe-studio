"""Render a deterministic sample project in the real native app and capture it."""
import base64
import json
import os
import subprocess
import tempfile
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageDraw, ImageGrab
import desktop_app

tmp = tempfile.TemporaryDirectory()
directory = Path(tmp.name)
background = Image.new("RGBA", (540, 960), "#e7dfd2")
draw = ImageDraw.Draw(background)
draw.rectangle((0, 0, 540, 180), fill="#b6c9c3")
draw.text((42, 70), "STUDIO / NOVEMBER", fill="#253c3c", stroke_width=1)
draw.rounded_rectangle((60, 250, 480, 700), radius=30, fill="#d2b8a2")
draw.ellipse((160, 330, 380, 550), fill="#f3ece0")
draw.text((180, 590), "PRODUCT", fill="#283c3c")
background.save(directory / "background.png")
Image.new("RGBA", (100, 100), "#9b6753").save(directory / "detail.png")
tracks = []
for i in range(20):
    seg = {
        "id": str(i), "name": "Background.png" if i == 0 else f"Product detail {i:02}.png",
        "file_path": str(directory / ("background.png" if i == 0 else "detail.png")),
        "start_seconds": 0, "duration_seconds": 8, "end_seconds": 8,
        "clip": {} if i == 0 else {
            "scale": {"x": 0.05, "y": 0.05},
            "transform": {"x": (i % 5 - 2) * 0.18, "y": (i // 5 - 2) * 0.18},
        },
        "raw_common_keyframes": [],
    }
    tracks.append({"index": i, "type": "video", "segments": [seg]})
desktop_app.CapCutStudioDesktopApp._refresh_projects = lambda self: None
root = tk.Tk()
app = desktop_app.CapCutStudioDesktopApp(root)
root.geometry(f"{min(1440, root.winfo_screenwidth())}x{min(940, root.winfo_screenheight() - 90)}+0+25")
def callback_error(*args):
    import traceback
    traceback.print_exception(*args)
    os._exit(1)
root.report_callback_exception = callback_error
subprocess.run(["defaults", "write", "com.apple.dock", "autohide", "-bool", "true"], check=True)
subprocess.run(["killall", "Dock"], check=False)
app.proj_combo["values"] = ["Product campaign / 20 layers"]
app.proj_combo.current(0)
app.current_project = {
    "canvas_width": 1080, "canvas_height": 1920, "fps": 60,
    "duration_seconds": 8, "tracks": tracks,
}
app.lbl_tracks.config(text="20 tracks")
app.lbl_duration.config(text="8.00s")
app.lbl_fps.config(text="60 FPS")
app.scrubber.set_duration(8)
root.update()
app._render_current_frame()
app._draw_timeline()
root.lift()
root.update()
output = Path("dist")
output.mkdir(exist_ok=True)
def capture():
    root.update_idletasks()
    shot = ImageGrab.grab()
    shot.save(output / "Desktop-Preview.png")
    payload = {"content": base64.b64encode((output / "Desktop-Preview.png").read_bytes()).decode(), "encoding": "utf-8"}
    result = subprocess.run(
        ["gh", "api", "repos/" + os.environ["GITHUB_REPOSITORY"] + "/git/blobs", "--input", "-"],
        input=json.dumps(payload), text=True, capture_output=True, check=True,
    )
    print("VISUAL_BLOB_SHA=" + json.loads(result.stdout)["sha"], flush=True)
    if not app.layers_expanded:
        app._toggle_layer_inspector()
    root.update()
    app._render_current_frame()
    root.update()
    ImageGrab.grab().save(output / "Desktop-Layers.png")
    app.timeline_canvas.yview_moveto(1)
    assert app.timeline_canvas.yview()[0] > 0, "All 20 tracks must be reachable"
    app.layer_tree.yview_moveto(1)
    assert app.layer_tree.yview()[0] > 0, "All layers must be reachable"
    from core import updater
    import sys
    sys.frozen = True
    updater.find_update = lambda **kwargs: {
        "version": "0.2.0-preview.4",
        "notes": "Bản cập nhật mới\n\n• Cải thiện trình xem video\n• Sửa lỗi và tối ưu hiệu năng",
        "url": "https://github.com/DevonReyesDavidJR/capcut-keyframe-studio/releases",
    }
    app._show_updates()
    root.after(700, capture_update)

def capture_update():
    shot = ImageGrab.grab()
    shot.save(output / "Desktop-Update.png")
    payload = {"content": base64.b64encode((output / "Desktop-Update.png").read_bytes()).decode(), "encoding": "utf-8"}
    result = subprocess.run(
        ["gh", "api", "repos/" + os.environ["GITHUB_REPOSITORY"] + "/git/blobs", "--input", "-"],
        input=json.dumps(payload), text=True, capture_output=True, check=True,
    )
    print("UPDATE_VISUAL_BLOB_SHA=" + json.loads(result.stdout)["sha"], flush=True)
    assert app._update_dialog.action.cget("text") == "Tải bản cập nhật"
    root.destroy()
root.after(1800, capture)
root.mainloop()
tmp.cleanup()
