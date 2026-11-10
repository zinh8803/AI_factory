# 🎬 AI Video Factory

Hệ thống tự động hóa sản xuất video ngắn dạng dọc (9:16 - 1080×1920) cho **YouTube Shorts, TikTok và Facebook Reels** với chi phí công cụ **0 đồng**.

Hệ thống tích hợp AI từ nghiên cứu xu hướng, biên kịch, thu âm giọng đọc tiếng Việt, vẽ ảnh nền nghệ thuật AI, dựng video chuyển động với phụ đề capsule hiện đại và quản lý qua giao diện Web Dashboard trực quan.

---

## ✨ Tính năng nổi bật

- **🔍 Tự động nghiên cứu xu hướng:** Quét RSS Google Trends Việt Nam hàng ngày để chọn chủ đề thực chiến phù hợp nhất (tránh trùng lặp trong 60 ngày).
- **🧠 Biên kịch kịch bản AI:** Sử dụng LLM chạy offline qua Ollama (`qwen2.5:3b`) chia kịch bản thành các phân cảnh ngắn 60–75s với hook lôi cuốn, CTA, mô tả và hashtag.
- **🎙️ Giọng đọc tiếng Việt (KorvaTTS):** Chuyển văn bản thành giọng nói tiếng Việt tự nhiên hoàn toàn miễn phí, chạy offline trên CPU.
- **🎨 Ảnh nền nghệ thuật AI (Pollinations):** Tự động tạo ảnh minh họa bối cảnh sắc nét cho từng phân cảnh qua Pollinations.ai.
- **🎞️ Dựng video chuyển động (FFmpeg):** Hiệu ứng camera Ken Burns đa dạng (zoom-in, zoom-out, pan ngang, lia dọc), lớp chữ tiêu đề trượt mượt mà.
- **💬 Phụ đề kiểu Capsule hiện đại:** Cắt câu ngắn 4–6 từ/cụm, bo góc ôm sát chữ tương phản cao, phong cách TikTok/Reels thịnh hành.
- **🖥️ Web Studio Dashboard:** Giao diện điều khiển 1-click, thanh tiến trình loading trực quan, console terminal xem log thời gian thực và kho video tích hợp trình phát.
- **💰 Tiếp thị liên kết (Affiliate):** Tự động tích hợp giới thiệu sản phẩm khi có chủ đề phù hợp và kèm tuyên bố minh bạch hoa hồng.

---

## 🛠️ Yêu cầu hệ thống (Prerequisites)

Trước khi chạy dự án, hãy đảm bảo máy tính của bạn đã cài đặt các công cụ sau:

1. **Python 3.12** (hoặc 3.10+):
   - Tải tại: [python.org](https://www.python.org/downloads/)
   - *Lưu ý:* Tích chọn **"Add Python to PATH"** khi cài đặt.

2. **FFmpeg:**
   - Tải bản build cho Windows tại: [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)
   - Giải nén và thêm thư mục `bin` (chứa `ffmpeg.exe` và `ffprobe.exe`) vào biến môi trường **System PATH**.
   - Kiểm tra bằng lệnh: `ffmpeg -version`

3. **Ollama:**
   - Tải và cài đặt: [ollama.com](https://ollama.com/)
   - Mở terminal và tải model Qwen 2.5:
     ```bash
     ollama pull qwen2.5:3b
     ```
   - Đảm bảo ứng dụng Ollama đang chạy trên máy tính (`http://localhost:11434`).

---

## 🚀 Hướng dẫn cài đặt sau khi Clone

### Bước 1: Mở thư mục dự án
Mở terminal (PowerShell hoặc Command Prompt) tại thư mục dự án:
```powershell
cd AI-Video-Factory
```

### Bước 2: Tạo và kích hoạt môi trường ảo Python
```powershell
# Tạo môi trường ảo .venv
python -m venv .venv

# Kích hoạt môi trường ảo trên Windows PowerShell
.\.venv\Scripts\Activate.ps1

# (Nếu gặp lỗi ExecutionPolicy trên PowerShell, hãy chạy lệnh sau rồi kích hoạt lại):
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Bước 3: Cài đặt các thư viện phụ thuộc
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🎮 Cách sử dụng

### Cách 1: Khởi động 1-Click bằng file `.bat` (Khuyên dùng)
Nhấp đúp chuột vào file:
```
run_app.bat
```
File script sẽ tự động kiểm tra Ollama, kích hoạt môi trường và mở Web Dashboard trên trình duyệt tại địa chỉ: **`http://localhost:8000`**.

Tại giao diện Web:
1. Nhập chủ đề bạn muốn làm video (hoặc để trống để AI tự quét Google Trends).
2. Bấm nút **"🚀 Tạo Video Ngay"**.
3. Theo dõi tiến trình qua thanh loading và live log terminal.
4. Video sau khi tạo xong sẽ hiển thị ngay trong danh sách **Kho Video** để bạn xem trước, tải về hoặc sao chép mô tả/hashtag.

---

### Cách 2: Chạy Web Dashboard bằng dòng lệnh
```powershell
.\.venv\Scripts\Activate.ps1
python server.py
```
Sau đó truy cập trình duyệt tại: **`http://localhost:8000`**

---

### Cách 3: Chạy trực tiếp qua dòng lệnh (CLI - không cần Web)

- **Tự động quét xu hướng và tạo video:**
  ```powershell
  python main.py
  ```

- **Tạo video theo chủ đề chỉ định sẵn:**
  ```powershell
  python main.py --topic "3 cách dùng AI để tiết kiệm thời gian mỗi ngày"
  ```

- **Dựng lại video từ kịch bản JSON có sẵn:**
  ```powershell
  python main.py --script output/scripts/ten_file_kich_ban.json
  ```

Video hoàn thiện sẽ được lưu tại thư mục:
`output/pending/<tên-video>/` bao gồm:
- `video.mp4`: Video hoàn chỉnh độ phân giải 1080×1920.
- `thumbnail.jpg`: Ảnh thu nhỏ đại diện.
- `title.txt` & `description.txt`: Tiêu đề, mô tả và hashtags tối ưu SEO.
- `REVIEW.md`: Báo cáo đánh giá chất lượng và checklist trước khi đăng.

---

## ⚙️ Cấu hình tùy biến

Tất cả các cấu hình được quản lý trong thư mục `config/`:

- **`config/settings.json`**:
  - `ollama`: Địa chỉ Ollama và model sử dụng (`qwen2.5:3b`).
  - `tts`: Giọng đọc KorvaTTS (`khanh_vy`, `nam_nguyen`,...).
  - `video`: Kích thước (1080x1920), FPS, màu chủ đạo (`accent_color`), âm lượng nhạc nền.
  - `images`: Cấu hình tạo ảnh AI (`enabled`, `timeout`, `style`).
- **`config/affiliate.json`**:
  - Danh sách sản phẩm tiếp thị liên kết (Tên, link affiliate, nhóm ngành).
- **Thư viện tài nguyên `assets/`**:
  - `assets/music/`: Chép file nhạc nền không bản quyền (`.mp3`, `.wav`) vào đây.
  - `assets/backgrounds/`: Chép ảnh nền tùy chọn (nếu có).
  - `assets/fonts/`: Chép font chữ TrueType (`.ttf`) hỗ trợ tiếng Việt nếu muốn đổi font.

---

## 📂 Cấu trúc thư mục dự án

```text
AI-Video-Factory/
├── .venv/                      # Môi trường ảo Python
├── assets/                     # Tài nguyên nhạc, font, hình nền
│   ├── backgrounds/
│   ├── fonts/
│   ├── icons/
│   └── music/
├── config/                     # Cấu hình hệ thống & affiliate
│   ├── settings.json
│   └── affiliate.json
├── data/                       # Dữ liệu xu hướng & lịch sử video
│   ├── trends/
│   ├── topics_history.json
│   └── published_history.json
├── logs/                       # Nhật ký hoạt động theo ngày
├── output/                     # Thành phẩm xuất ra
│   ├── audio/                  # File giọng đọc từng cảnh
│   ├── images/                 # Ảnh nền AI & khung hình dựng
│   ├── scripts/                # Kịch bản JSON
│   ├── videos/                 # Video MP4 xuất bản
│   └── pending/                # Thư mục gói video chờ duyệt
├── prompts/                    # System prompts cho Ollama
│   ├── topic_research.txt
│   ├── script_writer.txt
│   └── quality_checker.txt
├── web/                        # Giao diện Web Dashboard
│   └── index.html
├── .gitignore
├── requirements.txt
├── run_app.bat                 # Script chạy nhanh trên Windows
├── server.py                   # FastAPI backend & SSE stream logs
├── main.py                     # Pipeline điều phối CLI chính
├── research.py                 # Quét Google Trends & chọn chủ đề
├── script_generator.py         # AI viết kịch bản phân cảnh
├── voice_generator.py          # KorvaTTS tạo âm thanh
├── image_generator.py          # Tạo ảnh minh họa AI Pollinations
├── video_renderer.py           # Dựng video FFmpeg & phụ đề
├── quality_checker.py          # Kiểm định chất lượng video
└── utils.py                    # Tiện ích chung & gọi Ollama
```

---

## 📄 Bản quyền & Trách nhiệm nội dung

- Dự án sử dụng các công cụ mã nguồn mở: Python, FFmpeg, Ollama, KorvaTTS và Pillow.
- Khi đăng tải video lên các nền tảng mạng xã hội (YouTube, TikTok, Facebook), hãy lưu ý bật nhãn **"Nội dung do AI tạo"** (AI-generated content) theo đúng chính sách hiện hành của từng nền tảng.

