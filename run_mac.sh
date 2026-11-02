#!/usr/bin/env bash
# CapCut Keyframe Studio Pro - macOS / Linux Launcher

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "======================================================="
echo "🎬 Khởi động CapCut Keyframe Studio Pro (macOS)..."
echo "======================================================="

# Prefer python3
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo "❌ Lỗi: Không tìm thấy Python 3 trên máy của bạn. Vui lòng cài đặt Python 3."
    exit 1
fi

# Desktop mode needs Pillow; install it on first run if missing
if ! "$PY" -c "import PIL" &>/dev/null; then
    echo "📦 Đang cài đặt thư viện cần thiết (Pillow)..."
    "$PY" -m pip install --user -r requirements.txt || echo "⚠️ Không cài được Pillow, sẽ chạy ở chế độ Web."
fi

"$PY" run.py

