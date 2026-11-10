1. Kiến trúc hệ thống
Daily AI Video Factory
AI Topic Research

Tìm xu hướng, chọn chủ đề, kiểm tra độ hữu ích


Script Generator

Viết hook, kịch bản, CTA, mô tả, hashtag


Media Generator

Ảnh minh họa, giọng đọc, nhạc nền hợp lệ


Video Renderer

Ghép cảnh, phụ đề, hiệu ứng, xuất MP4 9:16


Human Review

Cậu chủ kiểm tra nội dung và bản quyền


Publish & Monetize

YouTube · TikTok · Facebook · Affiliate


2. Chủ đề kênh: để AI tự nghiên cứu và lựa chọn
Không nên để AI chọn chủ đề hoàn toàn ngẫu nhiên. Mình đề xuất định hướng kênh là AI thực chiến cho người Việt. Trong định hướng này, AI tự chọn chủ đề mỗi ngày dựa trên:
- Xu hướng tìm kiếm và vấn đề người dùng đang quan tâm.
- Công cụ AI mới hoặc tính năng hữu ích.
- Khả năng làm video ngắn dễ hiểu.
- Khả năng dẫn đến một sản phẩm Affiliate phù hợp.
- Tránh trùng lặp với những video đã đăng.
Ví dụ các nhóm chủ đề:
Nhóm	Ví dụ
Công cụ AI	AI tạo ảnh, video, giọng đọc
AI cho công việc	Tóm tắt tài liệu, Excel, viết email
AI cho lập trình	Code assistant, tạo website
AI cho kiếm tiền	Làm nội dung, sản phẩm số, tự động hóa
Website hữu ích	Công cụ miễn phí, nền tảng online

Tỷ lệ nội dung khởi đầu: 70% hướng dẫn hữu ích, 20% review/so sánh, 10% nội dung có mục đích giới thiệu Affiliate. Không nên biến mọi video thành quảng cáo.
3. Bộ công cụ miễn phí
Đây là stack mình chọn để không phụ thuộc vào API trả phí.










Ollama – bộ não AI
Chạy trên máy tính
- Chạy mô hình ngôn ngữ ngay trên Windows.
- Tự nghiên cứu, chọn chủ đề, viết kịch bản.
- Không cần API key.
Mô hình khởi đầu: qwen2.5:3b.

Tải Ollama cho Windows · 
Ollama English Documentation+1














KorvaTTS – giọng đọc tiếng Việt
- Chạy hoàn toàn trên máy tính.
- Có giọng nam và nữ.
- Không cần GPU hoặc API.
- Mã nguồn và model công bố giấy phép Apache 2.0.
KorvaTTS trên PyPI · 
PyPI














FFmpeg – dựng video
- Ghép hình, âm thanh, phụ đề.
- Xuất MP4 1080 × 1920.
- Chạy bằng dòng lệnh, phù hợp tự động hóa.
Trang tải FFmpeg · 
ffmpeg.org














Python – điều phối hệ thống
- Lấy dữ liệu xu hướng.
- Gọi Ollama.
- Gọi KorvaTTS.
- Điều khiển FFmpeg.
- Tạo thư mục video và báo cáo.
Tải Python · 
Python 3.12.16 documentation














Google Trends – nghiên cứu chủ đề
- Theo dõi tìm kiếm đang tăng.
- Chọn khu vực Việt Nam.
- Có thể xuất dữ liệu qua RSS.
Google Trends – Trending Now · 
Trends Help




Lưu ý về video: hệ thống ban đầu sẽ tạo video dạng motion graphics: hình nền, chữ động, biểu tượng, ảnh minh họa và giọng đọc AI. Đây là cách khả thi để chạy miễn phí trên máy tính. Chưa nên cài mô hình text-to-video nặng như Wan ngay từ đầu vì cần phần cứng và dung lượng lớn hơn.

4. Cài đặt từng bước trên Windows 11
Mình đề xuất đặt dự án tại:
C:\AI-Video-Factory


Bước 1 – Cài Python
Tải Python 3.12 tại:
Python Windows DownloadKhi cài đặt:
- Chọn Add Python to PATH.
- Chọn Install Now.
Mở PowerShell và kiểm tra:
py -3.12 --version
pip --version


Nếu có phiên bản Python và pip là được.
Bước 2 – Cài Ollama
Tải và cài đặt:
Ollama WindowsMở PowerShell:
ollama --version


Tải mô hình:
ollama pull qwen2.5:3b


Chạy thử:
ollama run qwen2.5:3b


Nhập:
Hãy đề xuất 5 chủ đề video AI hữu ích cho người Việt.
Mỗi chủ đề cần có tiêu đề và lý do người xem quan tâm.


Nếu AI trả lời được thì phần xử lý nội dung đã hoạt động.

Ollama chạy API nội bộ tại:
http://localhost:11434


Python có thể gọi API này để yêu cầu AI tạo nội dung. 
Ollama English Documentation+1

Khuyến nghị máy có RAM 16 GB để trải nghiệm dễ chịu hơn. Máy yếu vẫn có thể thử mô hình nhỏ nhưng tốc độ sẽ phụ thuộc cấu hình.Bước 3 – Cài FFmpeg
Truy cập:
FFmpeg DownloadChọn bản Windows build từ Gyan.dev.

Sau khi tải và giải nén, ví dụ:
C:\ffmpeg\bin\ffmpeg.exe


Thêm C:\ffmpeg\bin vào Environment Variables → Path.

Kiểm tra:
ffmpeg -version


Nếu hiện thông tin phiên bản FFmpeg là thành công.
Bước 4 – Tạo Python project
Chạy lần lượt:
mkdir C:\AI-Video-Factory
cd C:\AI-Video-Factory

py -3.12 -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip


Nếu PowerShell không cho chạy activate:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1


Cài thư viện:
pip install requests feedparser pillow korvatts python-dotenv


Chúng ta sử dụng:
Thư viện	Nhiệm vụ
requests	Gọi API Ollama
feedparser	Đọc RSS xu hướng
pillow	Tạo hình ảnh và chữ
korvatts	Chuyển văn bản thành giọng đọc
python-dotenv	Quản lý cấu hình

Bước 5 – Kiểm tra giọng đọc tiếng Việt
Trong PowerShell:
korvatts voices


Thử tạo một file âm thanh:
korvatts synth "Xin chào, đây là video AI đầu tiên của chúng ta." -v khanh_vy -o hello.wav


Nếu tạo được hello.wav, hệ thống đã có giọng đọc tiếng Việt.

KorvaTTS hỗ trợ chạy CPU và tự tải model cùng giọng đọc trong lần đầu sử dụng. 
PyPI

Bước 6 – Thiết lập nguồn nghiên cứu xu hướng
Mở:
Google Trends Trending NowThiết lập:
- Khu vực: Việt Nam.
- Khoảng thời gian: 7 ngày.
- Chọn nhóm chủ đề liên quan công nghệ và AI.
- Xuất RSS hoặc dữ liệu xu hướng.
Google Trends hỗ trợ xuất RSS và cập nhật xu hướng trung bình khoảng 10 phút/lần. 
Trends Help


Ta sẽ dùng RSS làm nguồn ý tưởng đầu vào, sau đó AI phân tích xem chủ đề nào có thể phát triển thành video.

Không lấy mọi từ khóa đang hot để làm video. AI cần ưu tiên chủ đề thực sự phù hợp với kênh.

5. Cấu trúc project hoàn chỉnh
Sau khi cài xong, tạo cấu trúc như sau:
C:\AI-Video-Factory
│
├── .venv/
│
├── config/
│   ├── settings.json
│   └── affiliate.json
│
├── prompts/
│   ├── topic_research.txt
│   ├── script_writer.txt
│   └── quality_checker.txt
│
├── assets/
│   ├── backgrounds/
│   ├── fonts/
│   ├── music/
│   └── icons/
│
├── data/
│   ├── trends/
│   ├── topics_history.json
│   └── published_history.json
│
├── output/
│   ├── scripts/
│   ├── audio/
│   ├── images/
│   ├── videos/
│   └── pending/
│
├── logs/
│
├── research.py
├── script_generator.py
├── voice_generator.py
├── video_renderer.py
├── quality_checker.py
└── main.py


Chức năng từng module
Module	Công việc
research.py	Thu thập xu hướng, chọn chủ đề
script_generator.py	Tạo kịch bản và chia cảnh
voice_generator.py	Tạo giọng đọc
video_renderer.py	Tạo ảnh động, ghép video
quality_checker.py	Kiểm tra độ dài, âm thanh, nội dung
main.py	Chạy toàn bộ pipeline

Đây là kiến trúc project đích; các file Python cần được triển khai thêm mới có thể chạy tự động.
6. Thiết kế AI tự nghiên cứu và chọn chủ đề
Đây là prompt cốt lõi mình đề xuất đặt trong prompts/topic_research.txt:

Bạn là chuyên gia nghiên cứu nội dung video ngắn cho thị trường Việt Nam.

MỤC TIÊU:
Chọn một chủ đề tốt nhất để sản xuất một video mỗi ngày.

ĐỊNH HƯỚNG KÊNH:
- AI và công nghệ thực chiến.
- Công cụ AI miễn phí.
- Ứng dụng AI trong công việc.
- AI hỗ trợ lập trình và làm website.
- Tự động hóa công việc.
- Công cụ hữu ích cho người Việt.

DỮ LIỆU ĐẦU VÀO:
- Xu hướng tìm kiếm từ Google Trends.
- Các chủ đề đã đăng trước đó.
- Danh sách công cụ có thể giới thiệu Affiliate.

NGUYÊN TẮC:
1. Ưu tiên vấn đề người xem thực sự cần giải quyết.
2. Không chọn chủ đề trùng với video gần đây.
3. Không tự bịa số liệu hoặc tính năng sản phẩm.
4. Phải có nguồn tham khảo để kiểm chứng.
5. Ưu tiên chủ đề có khả năng tạo chuyển đổi Affiliate tự nhiên.
6. Không chọn chủ đề chỉ vì đang viral nếu không phù hợp kênh.

ĐẦU RA JSON:
{
  "topic": "",
  "title": "",
  "reason": "",
  "target_audience": "",
  "hook": "",
  "affiliate_opportunity": "",
  "source_urls": [],
  "confidence": 0
}

Chỉ chọn một chủ đề tốt nhất.
Nếu không đủ dữ liệu đáng tin cậy, hãy báo không đủ dữ liệu.



Điểm quan trọng: Ollama không tự biết những gì đang xảy ra hôm nay. Python phải đưa dữ liệu xu hướng và nguồn tham khảo vào prompt để AI phân tích. Với thông tin về giá, tính năng hay chính sách sản phẩm, cần kiểm tra lại nguồn chính thức.

7. Quy chuẩn sản xuất một video mỗi ngày
Mình chọn video dài khoảng 60–75 giây để có đủ thời gian hướng dẫn và giải thích.
Mẫu cấu trúc video 70 giây
1. 0–5 giây: Hook
   
   Đặt câu hỏi hoặc nêu một vấn đề gây chú ý.
   
   Ví dụ: “Bạn có biết AI có thể biến một đoạn văn thành giọng đọc tiếng Việt không?”
2. 5–20 giây: Giới thiệu
   
   Nêu công cụ và vấn đề mà nó giải quyết.
3. 20–50 giây: Hướng dẫn
   
   Hiển thị giao diện, tính năng và ví dụ cụ thể.
4. 50–65 giây: Kết quả
   
   Cho xem kết quả hoặc so sánh trước và sau.
5. 65–75 giây: CTA
   
   Kêu gọi theo dõi, xem link công cụ trong mô tả nếu phù hợp.

Ví dụ video đầu tiên








flowvideo.ai


Tiêu đề: 3 cách dùng AI để tiết kiệm thời gian mỗi ngày

Kịch bản mẫu:

“Bạn đang mất quá nhiều thời gian cho những công việc lặp lại?

Có một số công cụ AI có thể giúp bạn xử lý chúng nhanh hơn.

Đầu tiên, dùng AI để tóm tắt tài liệu dài.

Thứ hai, chuyển văn bản thành giọng đọc để làm nội dung.

Thứ ba, dùng AI để tạo bản nháp email và nội dung công việc.

Tuy nhiên, hãy luôn kiểm tra lại kết quả trước khi sử dụng.

Theo dõi kênh để khám phá thêm những công cụ AI hữu ích nhé!”
Nội dung hướng dẫn, chưa phải quảng cáo

Về hình ảnh, mình khuyên:
- 60%: quay màn hình sản phẩm thật bằng OBS.
- 25%: chữ động và infographic do Python tạo.
- 15%: hình minh họa tự thiết kế hoặc stock có giấy phép phù hợp.
Cách này vừa tự động hóa được vừa tạo ra nội dung có giá trị riêng, thay vì chỉ ghép ảnh AI và giọng đọc.

8. Cơ chế kiếm tiền Affiliate
Mình muốn hệ thống có thể tự gợi ý sản phẩm để giới thiệu, nhưng chỉ đưa link vào khi sản phẩm thực sự liên quan đến video.

Tạo file config/affiliate.json:
{
  "products": [
    {
      "name": "AI Tool A",
      "category": "AI",
      "affiliate_url": "YOUR_AFFILIATE_LINK",
      "commission": "Kiểm tra theo chương trình",
      "active": true
    },
    {
      "name": "Hosting B",
      "category": "Hosting",
      "affiliate_url": "YOUR_AFFILIATE_LINK",
      "commission": "Kiểm tra theo chương trình",
      "active": true
    }
  ]
}


Đây là dữ liệu mẫu, không phải link Affiliate thật.

AI sẽ đánh giá:
- Công cụ có giải quyết vấn đề trong video không?
- Có thể hướng dẫn dùng thật không?
- Có link giới thiệu hợp lệ không?
- Người xem có lý do để đăng ký không?
Nếu không phù hợp, video không cần chèn quảng cáo.
Theo dõi hiệu quả
Tạo Google Sheets với các cột:
Ngày	Chủ đề	Lượt xem	Click Affiliate	Đăng ký	Hoa hồng
Ngày 1	AI tạo giọng đọc				
Ngày 2	AI viết email				
Ngày 3	AI tạo ảnh				

Nên sử dụng link theo dõi riêng cho từng video nếu chương trình Affiliate hỗ trợ. Luôn công khai rằng link có thể mang lại hoa hồng.

9. Đăng video lên ba nền tảng
Nền tảng	Cách triển khai ban đầu
YouTube Shorts	Đăng MP4, tiêu đề và mô tả có link Affiliate
TikTok	Đăng video, bật nhãn AI khi thuộc trường hợp phải công khai
Facebook Reels	Đăng video gốc, mô tả và link phù hợp











YouTube

YouTube Studio










TikTok

TikTok










Facebook

Facebook

Mình khuyên giai đoạn đầu đăng thủ công sau khi xem trước video. Sau này có thể làm module upload YouTube qua YouTube Data API; API có phương thức tải video và đặt tiêu đề, mô tả, trạng thái xuất bản. 
Google for Developers+1


Với TikTok, nếu video chứa hình ảnh, âm thanh hoặc cảnh chân thực được tạo đáng kể bằng AI thì cần thực hiện công khai theo chính sách của nền tảng. 
Hỗ Trợ TikTok


Cảnh báo về kiếm tiền: YouTube không cấm nội dung AI, nhưng có thể từ chối kiếm tiền đối với nội dung hàng loạt, lặp lại, ít giá trị hoặc thiếu tính nguyên bản. Vì vậy mỗi video phải có hướng dẫn, nhận xét hoặc thông tin thực sự khác biệt. 
YouTube Help


10. Tự động chạy mỗi ngày bằng Windows Task Scheduler
Sau khi hoàn thành các module Python, ta sẽ thiết lập:
- Mỗi ngày lúc 08:00: nghiên cứu chủ đề.
- 08:05: tạo kịch bản.
- 08:10: tạo giọng đọc.
- 08:15: dựng video.
- 08:30: kiểm tra và xuất bản nháp vào output/pending.
Mở Windows Task Scheduler:
1. Nhấn Win + R.
2. Gõ taskschd.msc.
3. Chọn Create Basic Task.
4. Đặt tên AI Video Factory.
5. Chọn Daily.
6. Chọn thời gian 08:00.
7. Chọn Start a Program.
Điền:

Program/script
C:\AI-Video-Factory\.venv\Scripts\python.exe


Add arguments
main.py


Start in
C:\AI-Video-Factory


Lưu ý: máy tính phải bật, không ngủ và Ollama phải hoạt động. Nếu chạy không thành công, kiểm tra log trước khi cho chạy tự động mỗi ngày.

11. Kế hoạch triển khai trong 7 ngày
Ngày	Công việc	Kết quả
1	Cài Python, Ollama, FFmpeg	Môi trường chạy được
2	Cài KorvaTTS, thử giọng đọc	File WAV tiếng Việt
3	Xây dựng research.py	Chọn được chủ đề
4	Xây dựng script_generator.py	Kịch bản JSON
5	Xây dựng video_renderer.py	Video MP4 đầu tiên
6	Kiểm tra, thêm Affiliate	Video hoàn chỉnh
7	Thiết lập Task Scheduler	Chạy tự động mỗi ngày

Mục tiêu tháng đầu:
- 30 chủ đề được nghiên cứu.
- 30 video được sản xuất.
- Đăng cả ba nền tảng.
- Thử 5–10 video có nội dung Affiliate phù hợp.
- Theo dõi lượt xem, lượt click và chuyển đổi.
Không đặt mục tiêu doanh thu chắc chắn trong tháng đầu. Trước hết phải chứng minh được quy trình sản xuất và tìm ra nội dung có người xem.

12. Những gì chúng ta sẽ xây dựng
AI Video Factory – MVP
Mục tiêu: 0 đồng chi phí phần mềm
Tiến độ triển khai
0/12



[ ] Cài Python 3.12 và tạo virtual environment
[ ] Cài Ollama và mô hình Qwen 2.5 3B
[ ] Cài FFmpeg
[ ] Cài KorvaTTS và kiểm tra giọng đọc
[ ] Tạo bộ khung project Python
[ ] Tích hợp Google Trends RSS
[ ] Tích hợp AI chọn chủ đề và viết kịch bản
[ ] Tích hợp tạo giọng đọc
[ ] Tạo video dọc tự động
[ ] Tạo báo cáo và lịch chạy mỗi ngày
[ ] Thêm Affiliate và theo dõi chuyển đổi
[ ] Kiểm tra video trước khi đăng
Đặt lại tiến độ
Đề xuất của mình: đừng cài tất cả và cố làm một hệ thống hoàn chỉnh ngay. Hãy làm theo thứ tự: cài Ollama → tạo giọng đọc KorvaTTS → xuất video đầu tiên → mới tích hợp nghiên cứu tự động.

Bước tiếp theo mình có thể viết trọn bộ source code Python cho project AI-Video-Factory, gồm các file main.py, research.py, script_generator.py, voice_generator.py, video_renderer.py và quality_checker.py để cậu chủ copy vào Windows 11 và chạy thử.

Nếu muốn duy trì thêm một nguồn ý tưởng độc lập mỗi ngày: