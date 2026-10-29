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
2. **📱 Trình Phát Xem Trước Đa Lớp & Timeline CapCut Trực Quan (Multi-Layer Viewer & Timeline)**:
   - **Màn hình Preview Đa Lớp (Composite Preview Monitor)**: Xem toàn bộ các layer video, ảnh phủ, mask, sticker chồng lên nhau tại bất kỳ khung hình nào theo đúng trục thứ tự hiển thị của CapCut.
   - **Tắt/Bật Mắt Ẩn Hiện Lớp (👁️ Layer Visibility)**: Dễ dàng ẩn hoặc hiện từng track để soi riêng chuyển động của layer đó hoặc xem tổng thể cả video.
   - **Phím tắt chuẩn Editor**: Bấm phím **Space** để Phát/Tạm dừng, phím **◀ / ▶** để lùi/tới từng frame (30fps/60fps) siêu mượt.
   - **Timeline Đa Lớp Trực Quan (CapCut Multi-Track Timeline)**:
     - Xếp chồng các track V0, V1, V2, V4... và audio A10, A14... theo trục thời gian thực.
     - Hiển thị ảnh thumbnail thu nhỏ của từng clip trực tiếp trên thanh timeline.
     - Hiển thị trực quan các điểm mốc **Keyframe Diamonds (Điểm kim cương `◆`)** ngay trên thanh clip để nhận biết ngay đoạn nào có chuyển động.
     - Thanh kim Playhead đỏ quét đồng bộ theo thời gian thực khi play hoặc kéo chuột.
     - Thanh trượt Zoom timeline và nút `Khớp (Fit)` để quan sát toàn bộ dự án 12s hoặc zoom sâu vào từng frame.

3. **🤖 Trợ Lý AI Soi & Check Khung Hình (AI Frame Inspector)**:
   - **Màn hình mô phỏng chuyển động từng Frame (9:16 Preview Player)**: Xem thử chuyển động trực quan từng frame `[◀ Lùi 1 Frame]`, `[▶ Phát thử 30fps]`, `[Tới 1 Frame ▶]` hoặc kéo thanh scrubber mà không cần xuất video hay mở lại CapCut.
   - **Chấm điểm độ mượt AI (Smoothness Score 0-100)**: Tự động tính toán đạo hàm vận tốc và gia tốc giữa các frame, phát hiện điểm gắt, giật hình hoặc đảo chiều đột ngột.
   - **Soi lệch nhịp âm thanh (Beat Sync Check)**: Đối chiếu frame đỉnh chuyển động với frame âm thanh, cảnh báo nếu chuyển động chạm đích sớm hoặc muộn so với tiếng bass/kick.
   - **✨ AI Auto-Tune (1-Click Fix)**: Tự động nắn mượt và loại bỏ các vi điểm giật cục bằng đường cong toán học chuẩn xác.
   - **🎞️ Xuất 1 Ảnh Ghép Từng Frame (Filmstrip PNG Tổng Hợp)**: Không tạo hàng trăm file ảnh lẻ gây nặng máy; tự động trích xuất và ghép toàn bộ frame nhịp vào **DUY NHẤT 1 file PNG tổng** dạng lưới (5x2, 6x3...) dung lượng siêu nhẹ (~200KB) để mở lên là nhìn thấu toàn bộ nhịp điệu chuyển động.
3. **🎵 Auto Keyframe Theo Beat Nhạc (Beat & Bass Sync)**:
   - Tự động phân tích beat/bass từ chính Audio Track trong project hoặc theo nhịp BPM cố định.
   - Tự động sinh keyframe **Bass Bounce** (Nảy nhịp), **Bass Shake** (Rung nhịp), hoặc **Bass Flash** (Chớp mờ) chính xác từng mili-giây.

4. **⚡ Speed Ramping Master (Uốn Tốc Độ & Đồng Bộ Nhịp Chuẩn Điện Ảnh)**:
   - **Hero Curve**: Tua nhanh $5\text{x} \rightarrow$ Rớt Slow-Motion $0.4\text{x}$ đúng khoảnh khắc đắt giá $\rightarrow$ Tua nhanh $5\text{x}$ thoát cảnh (chuẩn MV/trailer).
   - **Bullet Time (Ma Trận)**: Tốc độ chuẩn $1\text{x} \rightarrow$ Khựng siêu chậm $0.2\text{x}$ ở điểm nhấn $\rightarrow$ Bật lại bình thường.
   - **Flash In / Flash Out**: Lao cực nhanh vào hoặc vút nhanh thoát cảnh.
   - **Beat-Synced Speed Ramp**: Tự động giảm tốc độ cực chậm ở đúng từng nốt beat/bass và tua nhanh ở khoảng giữa 2 beat.
   - **Sao chép hàng loạt & Tự tính thời lượng**: Áp dụng đường cong tốc độ cho 20 clip cùng lúc, tự động tính toán lại thời lượng hiển thị (`target_timerange`) để timeline không bao giờ bị xô lệch hay hở khoảng trống.

5. **🎯 Chống Rung Khóa Điểm Mốc (Point-Lock Stabilizer & Auto-Zoom Crop Protection)**:
   - **Khóa Trục Cố Định (Dead-Lock 100%)**: Khóa cứng điểm mốc đứng im phăng phắc tại 1 vị trí cố định trên màn hình bất kể máy quay bị rung lắc hay người cầm máy di chuyển.
   - **Khử Rung Mượt (Smooth Damping)**: Lọc sạch các rung giật cao tần của tay cầm, nhưng vẫn giữ lại chuyển động lia máy (pan/tilt) tự nhiên, mượt mà.
   - **Điểm Mốc Nhận Diện Linh Hoạt**:
     - 🎯 *Tâm Giữa (Center 50%, 50%)*: Khóa trung tâm khung hình.
     - 👤 *Mặt / Đầu (Face 50%, 30%)*: Giữ khuôn mặt nhân vật luôn đứng yên 1 vị trí (rất thịnh hành trên TikTok/Reels).
     - 👕 *Ngực Áo / Logo / Sản Phẩm (Chest 50%, 55%)*: Khóa áo hoặc sản phẩm cố định khi đổi trang phục, đổi đồ liên tục (outfit switch).
     - 🖱️ *Tùy Chọn Tọa Độ*: Click trực tiếp lên màn hình mô phỏng để ghim điểm mốc vào bất kỳ vật thể nào.
   - **Tự Động Phóng To Giữ Cảnh Trong Khung Hình (Auto-Zoom)**: Khi di chuyển bù rung, mép khung hình sẽ bị thụt vào. Thuật toán tự động đo độ lệch cực đại $\Delta X, \Delta Y$ để tính toán tỷ lệ phóng to (`KFTypeScaleX`) vừa vặn tuyệt đối, **triệt tiêu 100% hiện tượng hở viền đen**.

6. **📋 Sao Chép Hàng Loạt (Batch Keyframing)**:
   - Copy keyframe từ 1 clip mẫu và áp dụng tức thì cho 10 - 50 clip khác trên timeline.
   - Hỗ trợ chế độ **Co giãn tỷ lệ (Stretch to fit)** để tự khớp độ dài từng clip nhận.

7. **📈 Làm Mượt Easing (Curve Smoother)**:
   - Chuyển đổi mọi keyframe gãy góc (`Line`) thành đường cong Bezier mềm mại `FreeCurveInOut`.

8. **🛡️ An Toàn Tuyệt Đối (Auto Backup & Rollback)**:
   - Tự động sao lưu bản dự phòng `.bak` trước mọi thao tác chỉnh sửa.
   - Tính năng 1-click Khôi phục (Restore) giúp đưa project về nguyên trạng bất kỳ lúc nào.

---

## 🖥️ Giao Diện Ứng Dụng (Native Desktop & Web)

Ứng dụng chạy **trực tiếp dưới dạng Desktop App độc lập trên máy tính** (Native Desktop GUI) sử dụng Python Tkinter chuẩn:
- **Tốc độ kết xuất tức thì (Zero-Latency)**: Đọc và hiển thị composite trực tiếp từ ổ cứng, đạt tốc độ 250+ FPS, không còn tình trạng lag hay "Đang nạp..." như trên web browser.
- **Trình Phát Đa Lớp (Composite Monitor)**: Hiển thị chân thực tất cả các layer (video, ảnh PNG trong suốt, text) xếp chồng tại bất kỳ thời điểm nào.
- **Thanh Timeline Đa Track**: Hiển thị vạch đỏ Playhead, các block clip phân màu, và **viên kim cương Keyframe (`◆`)** trực quan.
- **Chế độ Web Server dự phòng**: Nếu cần chạy qua trình duyệt, chỉ cần thêm cờ `python3 run.py --web`.

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng (Quick Start)

Tool sử dụng **100% Python Standard Library**, **không cần cài đặt thư viện rườm rà (Zero Pip Dependencies)**.

### 1. Tải dự án về máy
```bash
git clone https://github.com/DevonReyesDavidJR/capcut-keyframe-studio.git
cd capcut-keyframe-studio
```

### 2. Khởi động công cụ (Native Desktop GUI)

#### 👉 Trên macOS:
Chỉ cần nhấp đúp vào file `run_mac.sh` hoặc chạy trong Terminal:
```bash
./run_mac.sh
```

#### 👉 Trên Windows:
Nhấp đúp chuột vào file `run_win.bat` hoặc mở Command Prompt:
```cmd
run_win.bat
```

Ứng dụng Desktop CapCut Keyframe Studio Pro sẽ lập tức xuất hiện ngay trên màn hình máy tính của bạn!

*(Tùy chọn: Để chạy qua giao diện Web Browser, dùng lệnh `python3 run.py --web`)*.

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
├── desktop_app.py             # Ứng dụng Desktop Studio Native GUI (Tkinter 100% Native)
├── core/
│   ├── capcut_adapter.py      # Quản lý đường dẫn, đọc/ghi và sao lưu draft CapCut
│   ├── keyframe_engine.py     # Bộ sinh toán học keyframe, bezier curves, presets
│   ├── audio_analyzer.py      # Phân tích năng lượng âm thanh & bắt beat/bass
│   ├── frame_ai_inspector.py  # Soi từng frame, vận tốc, gia tốc, auto-tune
│   ├── filmstrip_generator.py # Xuất 1 ảnh PNG tổng hợp dạng lưới (Contact sheet)
│   ├── speed_ramp_engine.py   # Uốn tốc độ Curve speed, Hero, Bullet, Beat-sync
│   └── stabilizer_engine.py   # Chống rung khóa điểm mốc, auto-zoom crop viền
├── web/
│   ├── index.html             # Giao diện Web (Chế độ dự phòng --web)
│   ├── style.css              # Hệ thống màu sắc, layout, canvas preview
│   └── app.js                 # Logic tương tác, vẽ đồ thị & gọi API
├── server.py                  # REST API Server dự phòng (Python standard library)
├── run.py                     # Launcher khởi động Native Desktop GUI (hoặc --web)
├── run_mac.sh                 # Script 1-click cho Mac
├── run_win.bat                # Script 1-click cho Windows
└── README.md                  # Tài liệu hướng dẫn
```

---

## 📜 Giấy Phép (License)

Dự án được phát hành theo giấy phép [MIT License](LICENSE).
Tự do sử dụng, chỉnh sửa và phân phối cho mục đích cá nhân lẫn thương mại.
