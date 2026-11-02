"""Regression coverage for source transforms, alpha and real preset actions."""
import copy
import json
import tempfile
from pathlib import Path
from PIL import Image
from core.capcut_adapter import CapCutAdapter
from desktop_app import PILMediaCompositor, CapCutStudioDesktopApp

class Field:
    def __init__(self, value): self.value = value
    def get(self): return self.value
    def current(self): return 0

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp)
    draft = path / "sample"
    draft.mkdir()
    asset = path / "source.png"
    Image.new("RGBA", (100, 100), (255, 0, 0, 255)).save(asset)
    original = {
        "name": "Regression", "duration": 2000000, "fps": 30,
        "canvas_config": {"width": 100, "height": 100},
        "materials": {"videos": [{"id": "media", "path": str(asset)}]},
        "tracks": [{"type": "video", "segments": [{
            "id": "segment", "material_id": "media",
            "target_timerange": {"start": 0, "duration": 2000000},
            "clip": {"scale": {"x": 0.5, "y": 0.5},
                     "transform": {"x": 0.5, "y": 0}, "alpha": 0.5},
        }]}],
    }
    info = draft / "draft_info.json"
    info.write_text(json.dumps(original))
    adapter = CapCutAdapter(tmp)
    project = adapter.load_project_details("sample")
    seg = project["tracks"][0]["segments"][0]
    assert seg["clip"] == original["tracks"][0]["segments"][0]["clip"]
    image, _ = PILMediaCompositor().composite_scene([(0, seg)], 0, cw=100, ch=100)
    assert image.getpixel((75, 50))[0] > 100
    assert image.getpixel((10, 50))[0] < 30
    animated = copy.deepcopy(seg)
    animated["clip"] = {}
    animated["raw_common_keyframes"] = [{
        "property_type": "KFTypeScaleX", "keyframe_list": [{"time_offset": 0, "values": [0.5]}]
    }]
    image, _ = PILMediaCompositor().composite_scene([(0, animated)], 0, cw=100, ch=100)
    assert image.getpixel((50, 10))[0] < 30, "Uniform scale must affect both axes"

    import desktop_app
    desktop_app.messagebox.showinfo = lambda *a: None
    desktop_app.messagebox.showwarning = lambda *a: None
    desktop_app.messagebox.askyesno = lambda *a: True
    app = CapCutStudioDesktopApp.__new__(CapCutStudioDesktopApp)
    app.adapter = adapter
    app.current_project_folder = "sample"
    app.selected_segments = set()
    app.spin_scale_peak = Field("1.25")
    app.spin_scale_start = Field("1.0")
    app.rhythm_track_combo = Field("Tất cả Video Track")
    app.rhythm_curve_combo = Field("FreeCurveInOut (Mượt)")
    app.proj_combo = Field("")
    app._load_project_by_index = lambda idx: None
    for preset in ("switch_in_out", "pulse_1s", "pulse_2s", "bounce", "punch_zoom", "shake"):
        info.write_text(json.dumps(original))
        app.current_project = adapter.load_project_details("sample")
        app._apply_rhythm_preset(preset)
        result = json.loads(info.read_text())
        assert result["tracks"][0]["segments"][0]["common_keyframes"], preset
    assert list(draft.glob("*.bak-*"))
    app._draw_speed_curve_preview = lambda preset: None
    for preset in ("hero_ramp", "bullet_time", "flash_in_out", "beat_sync", "reset"):
        fixture = copy.deepcopy(original)
        fixture["tracks"][0]["segments"][0]["source_timerange"] = {"start": 100000, "duration": 2000000}
        info.write_text(json.dumps(fixture))
        app.current_project = adapter.load_project_details("sample")
        app._apply_speed_ramp(preset)
        result = json.loads(info.read_text())
        segment = result["tracks"][0]["segments"][0]
        assert segment["speed"] > 0
        assert abs(segment["target_timerange"]["duration"] - 2000000 / segment["speed"]) <= 1
        if preset != "reset":
            assert segment["extra_material_refs"][-1] in {s["id"] for s in result["materials"]["speeds"]}


    # Hand-drawn motion path: smoothed, spans the whole clip, ends where the stroke ends
    from core.keyframe_engine import KeyframeEngine
    stroke = [(-0.6 + i * 0.02, 0.3 * (i % 7) / 7, i * 0.03) for i in range(60)]
    groups = KeyframeEngine.generate_motion_path_keyframes(stroke, 2000000, fps=30, center=(0, 0))
    by_type = {g["property_type"]: g["keyframe_list"] for g in groups}
    xs = by_type["KFTypePositionX"]
    assert xs[0]["time_offset"] == 0 and xs[-1]["time_offset"] == 2000000
    assert all(a["time_offset"] < b["time_offset"] for a, b in zip(xs, xs[1:]))
    try:
        KeyframeEngine.generate_motion_path_keyframes([(0, 0, 0), (0, 0, 0.1)], 2000000)
        raise AssertionError("A zero-length stroke must be rejected")
    except ValueError:
        pass

    # CapCut 9.x keeps a timeline copy that must receive the same edits
    timeline = draft / "Timelines" / "tl-main"
    timeline.mkdir(parents=True)
    mirrored = dict(original, id="tl-main")
    info.write_text(json.dumps(mirrored))
    (timeline / "draft_info.json").write_text(json.dumps(mirrored))
    app.current_project = adapter.load_project_details("sample")
    app._apply_rhythm_preset("bounce")
    assert json.loads((timeline / "draft_info.json").read_text())["tracks"][0]["segments"][0]["common_keyframes"]

print("Transform, alpha, uniform scale, preset, motion path and timeline mirror checks passed.")
