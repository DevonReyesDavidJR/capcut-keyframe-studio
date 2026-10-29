#!/usr/bin/env bash
# CapCut Keyframe Studio Pro - macOS / Linux Launcher

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "======================================================="
echo "🎬 Khởi động CapCut Keyframe Studio Pro (macOS)..."
echo "======================================================="

# Prefer python3
if command -v python3 &>/dev/null; then
    python3 run.py
elif command -v python &>/dev/null; then
    python run.py
else
    echo "❌ Lỗi: Không tìm thấy Python 3 trên máy của bạn. Vui lòng cài đặt Python 3."
    exit 1
fi
