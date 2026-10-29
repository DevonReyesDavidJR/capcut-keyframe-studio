# 🎬 CapCut Keyframe Studio Pro

> **Tool tự động hóa & tối ưu hóa Keyframe chuyên nghiệp cho CapCut Desktop** (chạy mượt mà trên cả **macOS** và **Windows**).

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-brightgreen)
![CapCut](https://img.shields.io/badge/CapCut-Desktop%20Compatible-00f2fe)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## 🌟 Giới Thiệu (Overview)

Việc đặt từng điểm keyframe trên CapCut theo cách thủ công (để tạo zoom giật theo beat, rung lắc điện ảnh, đường cong easing) thường tốn rất nhiều thời gian và khó đạt độ mượt mà như mong muốn.

**CapCut Keyframe Studio Pro** là giải pháp hoàn chỉnh giúp can thiệp trực tiếp và an toàn vào cấu trúc `draft_info.json` của CapCut Desktop, mang lại những tính năng mà CapCut chưa hỗ trợ sẵn:

1. **⚡ Presets Chuyển Động Chuyên Biệt Cho Rhythmic Switch & Beat:**
   - **Switch In (Vút Vào Đàn Hồi)**: Đối tượng/sản phẩm bay vút vào từ dưới lên (hoặc từ trên/trái/phải) với gia tốc Ease-out và độ nảy nhẹ (overshoot), sau đó đứng yên chuẩn xác ở vị trí mong muốn (như trong các clip đổi trang phục, đổi sản phẩm Halloween edit).
   - **Switch Out (Vút Xuống Rời Khung)**: Lao nhanh ra khỏi màn hình ở cuối phân đoạn nhịp.
   - **Rhythmic Step (Nhịp Đều 1s / 2s / 0.8s)**: Tự động lặp lại nấc giật hoặc nảy nhịp theo chu kỳ thời gian cố định mà không cần chỉnh tay từng đoạn.
   - **Smooth Zoom In / Out**: Phóng to/thu nhỏ mượt mà với đường cong Bezier (`FreeCurveInOut`).
   - **Camera Shake**: Rung lắc máy quay giật nảy phong cách Hip-hop / Điện ảnh với tần số và biên độ tùy chỉnh.
   - **Slow Pan (Ken Burns)**: Trôi nhẹ khung hình cho b-roll và ảnh tĩnh.
   - **Elastic Bounce**: Hiệu ứng nảy đàn hồi (overshoot) cực kỳ sinh động cho clip/sticker/text.
   - **Whip Pan**: Gạt chuyển cảnh tốc độ cao sang trái/phải/lên/xuống.
   - **Breathing Pulse**: Nhịp thở/đập tuần hoàn êm ái.
   - **Fade Opacity**: Làm mờ dần / Hiện dần clip.
2. **🎵 Auto Keyframe Theo Beat Nhạc (Beat & Bass Sync)**:
   - Tự động phân tích beat/bass từ chính Audio Track trong project hoặc theo nhịp BPM cố định.
   - Tự động sinh keyframe **Bass Bounce** (Nảy nhịp), **Bass Shake** (Rung nhịp), hoặc **Bass Flash** (Chớp mờ) chính xác từng mili-giây.
3. **📋 Sao Chép Hàng Loạt (Batch Keyframing)**:
   - Copy keyframe từ 1 clip mẫu và áp dụng tức thì cho 10 - 50 clip khác trên timeline.
   - Hỗ trợ chế độ **Co giãn tỷ lệ (Stretch to fit)** để tự khớp độ dài từng clip nhận.
4. **📈 Làm Mượt Easing (Curve Smoother)**:
   - Chuyển đổi mọi keyframe gãy góc (`Line`) thành đường cong Bezier mềm mại `FreeCurveInOut`.
5. **🛡️ An Toàn Tuyệt Đối (Auto Backup & Rollback)**:
   - Tự động sao lưu bản dự phòng `.bak` trước mọi thao tác chỉnh sửa.
   - Tính năng 1-click Khôi phục (Restore) giúp đưa project về nguyên trạng bất kỳ lúc nào.

---

## 🖥️ Giao Diện Ứng Dụng (Web UI)

Ứng dụng chạy trực tiếp trên trình duyệt máy tính của bạn với giao diện tối (Dark Editor Theme) hiện đại, trực quan:
- Tự động quét và hiển thị tất cả các project CapCut gần nhất kèm ảnh bìa thumbnail.
- Khám phá toàn bộ Video Tracks, Audio Tracks và từng Segment trong timeline.
- Canvas trực quan hiển thị đường cong chuyển động (Curve Visualizer) thời gian thực khi kéo thanh trượt.

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng (Quick Start)

Tool sử dụng **100% Python Standard Library**, **không cần cài đặt thư viện rườm rà**.

### 1. Tải dự án về máy
```bash
git clone https://github.com/DevonReyesDavidJR/capcut-keyframe-studio.git
cd capcut-keyframe-studio
```

### 2. Khởi động công cụ

#### 👉 Trên macOS:
Chỉ cần nhấp đúp vào file `run_mac.sh` hoặc chạy terminal:
```bash
./run_mac.sh
```

#### 👉 Trên Windows:
Nhấp đúp chuột vào file `run_win.bat` hoặc mở Command Prompt:
```cmd
run_win.bat
```

Trình duyệt sẽ tự động mở địa chỉ `http://localhost:8765`.

---

## 📖 Quy Trình Sử Dụng Chuẩn

1. **Lưu hoặc đóng dự án trong CapCut** trước khi thao tác trên tool để tránh xung đột file.
2. Trên giao diện tool, chọn dự án ở cột bên trái.
3. Tích chọn các clip cần chèn keyframe ở phần Timeline Tracks.
4. Chọn Preset mong muốn hoặc chuyển sang tab **Auto Beat / Nhịp Nhạc**.
5. Nhấn **Áp Dụng Vào Các Clip Đã Chọn**.
6. Mở lại CapCut và thưởng thức thành quả! 🎉

---

## 🛠️ Cấu Trúc Dự Án (Architecture)

```
capcut-keyframe-studio/
├── core/
│   ├── capcut_adapter.py    # Quản lý đường dẫn, đọc/ghi và sao lưu draft CapCut
│   ├── keyframe_engine.py   # Bộ sinh toán học keyframe, bezier curves, presets
│   └── audio_analyzer.py    # Phân tích năng lượng âm thanh & bắt beat/bass
├── web/
│   ├── index.html           # Giao diện Dark theme chuyên nghiệp
│   ├── style.css            # Hệ thống màu sắc, layout, canvas preview
│   └── app.js               # Logic tương tác, vẽ đồ thị & gọi API
├── server.py                # REST API Server siêu nhẹ (Python standard library)
├── run.py                   # Launcher tự động mở trình duyệt
├── run_mac.sh               # Script 1-click cho Mac
├── run_win.bat              # Script 1-click cho Windows
└── README.md                # Tài liệu hướng dẫn
```

---

## 📜 Giấy Phép (License)

Dự án được phát hành theo giấy phép [MIT License](LICENSE).
Tự do sử dụng, chỉnh sửa và phân phối cho mục đích cá nhân lẫn thương mại.
