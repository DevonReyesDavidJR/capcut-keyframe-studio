#!/usr/bin/env bash
# ==============================================================================
# Script đóng gói CapCut Keyframe Studio Pro thành file .dmg cho macOS
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "======================================================="
echo "🍏 Đang đóng gói CapCut Keyframe Studio Pro thành DMG..."
echo "======================================================="

# 1. Tạo Icon nếu chưa có
if [ ! -f "AppIcon.icns" ]; then
    echo "🎨 Đang tạo biểu tượng AppIcon.icns..."
    python3 -c "
import os, subprocess
from PIL import Image, ImageDraw

iconset_dir = 'AppIcon.iconset'
os.makedirs(iconset_dir, exist_ok=True)
master = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
draw = ImageDraw.Draw(master)
r = 220
x0, y0, x1, y1 = 64, 64, 960, 960
draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill='#11141c', outline='#00f2fe', width=16)
draw.rounded_rectangle([x0+24, y0+24, x1-24, y1-24], radius=r-20, fill='#181c28')
top_h = 280
draw.rounded_rectangle([x0+24, y0+24, x1-24, y0+top_h], radius=r-20, fill='#202636')
for i in range(x0+20, x1-20, 160):
    draw.polygon([(i, y0+24), (i+80, y0+24), (i+40, y0+top_h), (i-40, y0+top_h)], fill='#00f2fe')
cx, cy = 512, 600
diamond_r = 170
draw.polygon([(cx, cy-diamond_r-20), (cx+diamond_r+20, cy), (cx, cy+diamond_r+20), (cx-diamond_r-20, cy)], fill='#004455')
draw.polygon([(cx, cy-diamond_r), (cx+diamond_r, cy), (cx, cy+diamond_r), (cx-diamond_r, cy)], fill='#00f2fe', outline='#ffffff', width=10)
draw.polygon([(cx, cy-diamond_r//2), (cx+diamond_r//2, cy), (cx, cy+diamond_r//2), (cx-diamond_r//2, cy)], fill='#ffffff')

sizes = [
    ('icon_16x16.png', 16), ('icon_16x16@2x.png', 32),
    ('icon_32x32.png', 32), ('icon_32x32@2x.png', 64),
    ('icon_128x128.png', 128), ('icon_128x128@2x.png', 256),
    ('icon_256x256.png', 256), ('icon_256x256@2x.png', 512),
    ('icon_512x512.png', 512), ('icon_512x512@2x.png', 1024)
]
for fname, sz in sizes:
    master.resize((sz, sz), Image.Resampling.LANCZOS).save(os.path.join(iconset_dir, fname))
subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', 'AppIcon.icns'], check=True)
"
fi

# 2. Build .app Bundle bằng PyInstaller
echo "📦 Đang biên dịch Mach-O app bundle..."
export PYINSTALLER_CONFIG_DIR="$DIR/.pyinstaller_cache"
pyinstaller --noconfirm --windowed \
  --workpath "$DIR/build" \
  --distpath "$DIR/dist" \
  --name "CapCut Keyframe Studio" \
  --icon "AppIcon.icns" \
  --add-data "core:core" \
  --add-data "web:web" \
  --hidden-import "PIL" \
  --hidden-import "PIL.Image" \
  --hidden-import "PIL.ImageTk" \
  --hidden-import "tkinter" \
  --hidden-import "tkinter.ttk" \
  --hidden-import "tkinter.messagebox" \
  --hidden-import "tkinter.filedialog" \
  --osx-bundle-identifier "com.capcut.keyframestudio" \
  desktop_app.py

# 3. Chuẩn bị thư mục staging
echo "📂 Đang chuẩn bị gói cài đặt DMG..."
rm -rf dmg_staging
mkdir -p dmg_staging
cp -R "dist/CapCut Keyframe Studio.app" "dmg_staging/"
ln -s /Applications "dmg_staging/Applications"

cat << 'EOF' > dmg_staging/HUONG_DAN_CAI_DAT.txt
🎬 CAPCUT KEYFRAME STUDIO PRO
==============================
HƯỚNG DẪN CÀI ĐẶT:
1. Kéo thả biểu tượng 'CapCut Keyframe Studio' vào thư mục 'Applications' bên cạnh.
2. Mở ứng dụng từ Launchpad hoặc Spotlight (nhấn Cmd + Space -> gõ CapCut Keyframe Studio).
3. Tận hưởng bộ công cụ tự động hóa Keyframe & Speed Ramp số 1 cho CapCut!

* Lưu ý: Nếu macOS hiển thị thông báo ứng dụng từ nhà phát triển chưa được xác minh,
  vào Cài đặt hệ thống (System Settings) -> Quyền riêng tư & Bảo mật (Privacy & Security) -> Chọn 'Vẫn mở' (Open Anyway).
EOF

# 4. Tạo DMG
echo "💿 Đang tạo file ảnh đĩa DMG..."
rm -f "CapCut-Keyframe-Studio-Pro.dmg"
hdiutil create -volname "CapCut Keyframe Studio Pro" \
  -srcfolder "dmg_staging" \
  -ov -format UDZO \
  "CapCut-Keyframe-Studio-Pro.dmg"

# 5. Dọn dẹp
rm -rf dmg_staging

echo "======================================================="
echo "✅ HOÀN TẤT ĐÓNG GÓI DMG!"
echo "📁 Đường dẫn file DMG: $DIR/CapCut-Keyframe-Studio-Pro.dmg"
echo "======================================================="
