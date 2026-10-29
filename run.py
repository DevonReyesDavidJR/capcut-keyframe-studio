#!/usr/bin/env python3
"""
CapCut Keyframe Studio Pro - Launcher
Starts local server and opens browser interface automatically.
"""

import os
import sys
import time
import webbrowser
import threading
from server import run_server

PORT = 8765
URL = f"http://localhost:{PORT}"

def open_browser():
    time.sleep(1.2)
    print(f"\n=======================================================")
    print(f"🎬 CapCut Keyframe Studio Pro is running!")
    print(f"🌐 Access Web UI at: {URL}")
    print(f"💡 Press Ctrl+C in this terminal to stop the tool.")
    print(f"=======================================================\n")
    try:
        webbrowser.open(URL)
    except Exception:
        pass

def main():
    print(f"Starting CapCut Keyframe Studio Pro on port {PORT}...")
    threading.Thread(target=open_browser, daemon=True).start()
    try:
        run_server(PORT)
    except KeyboardInterrupt:
        print("\nTool stopped. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()

