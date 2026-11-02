#!/usr/bin/env python3
"""
CapCut Keyframe Studio Pro - Launcher
====================================
Launches the 100% Native Desktop Studio Application directly on macOS and Windows.
No web browser or localhost server required.

Usage:
  python3 run.py        -> Starts Native Desktop App (Recommended)
  python3 run.py --web  -> Starts Web Server fallback on http://localhost:8765
"""

import os
import sys

def main():
    # Finder-launched apps do not inherit a shell's Homebrew PATH.
    extra_paths = [p for p in ("/opt/homebrew/bin", "/usr/local/bin") if os.path.isdir(p)]
    os.environ["PATH"] = os.pathsep.join(extra_paths + [os.environ.get("PATH", "")])

    if "--self-test" in sys.argv:
        from pathlib import Path
        import tkinter as tk
        import desktop_app
        import server
        root = tk.Tk()
        root.withdraw()
        desktop_app.CapCutAdapter.list_projects = lambda self: []
        app = desktop_app.CapCutStudioDesktopApp(root)
        root.update_idletasks()
        assert app.preview_canvas.winfo_exists()
        assert (Path(server.BASE_DIR) / "web" / "index.html").is_file()
        root.destroy()
        return

    if "--web" in sys.argv:
        import time
        import webbrowser
        import threading
        from server import run_server

        PORT = 8765
        URL = f"http://localhost:{PORT}"

        def open_browser():
            time.sleep(1.2)
            print(f"\n=======================================================")
            print(f"🎬 CapCut Keyframe Studio Pro (Web Mode) is running!")
            print(f"🌐 Access Web UI at: {URL}")
            print(f"💡 Press Ctrl+C in this terminal to stop.")
            print(f"=======================================================\n")
            try:
                webbrowser.open(URL)
            except Exception:
                pass

        print(f"Starting CapCut Keyframe Studio Pro Web Server on port {PORT}...")
        threading.Thread(target=open_browser, daemon=True).start()
        try:
            run_server(PORT)
        except KeyboardInterrupt:
            print("\nTool stopped. Goodbye!")
            sys.exit(0)
    else:
        print("=======================================================")
        print("🎬 Khởi động CapCut Keyframe Studio Pro (Native Desktop)...")
        print("⚡ Chạy trực tiếp trên máy - Không qua trình duyệt web")
        print("=======================================================")
        from desktop_app import main as run_desktop
        run_desktop()

if __name__ == "__main__":
    main()
