"""Exercise the real HTTP API and FFmpeg extraction without user projects."""
import json
import subprocess
import tempfile
import threading
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image
import server
from core.capcut_adapter import CapCutAdapter

with tempfile.TemporaryDirectory() as tmp:
    server.adapter = CapCutAdapter(tmp)
    httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.CapCutAPIHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{httpd.server_port}"
    try:
        with urllib.request.urlopen(base + "/") as response:
            assert b"masterPreviewCanvas" in response.read()
        with urllib.request.urlopen(base + "/api/projects") as response:
            assert json.load(response)["projects"] == []
        for width, height in ((640, 360), (360, 640), (360, 360)):
            video = Path(tmp) / f"{width}x{height}.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                f"color=c=blue:s={width}x{height}:d=0.2",
                "-pix_fmt", "yuv420p", str(video)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            query = urllib.parse.urlencode({"path": str(video), "t": 0, "w": 160, "h": 90})
            with urllib.request.urlopen(base + "/api/media_frame?" + query) as response:
                frame = Image.open(BytesIO(response.read()))
                assert abs(frame.width / frame.height - width / height) < 0.02, frame.size
        webp = Path(tmp) / "sample.webp"
        Image.new("RGB", (16, 16), "red").save(webp)
        query = urllib.parse.urlencode({"path": str(webp)})
        with urllib.request.urlopen(base + "/api/media_frame?" + query) as response:
            assert response.headers.get_content_type() == "image/webp"
        print("Web/API smoke checks passed.")
    finally:
        httpd.shutdown()
        httpd.server_close()
