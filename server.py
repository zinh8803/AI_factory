"""FastAPI Backend cho AI Video Factory.

Cung cấp API điều khiển tạo video, stream logs theo thời gian thực (SSE),
quản lý kho video đã xuất bản và phục vụ giao diện Web Frontend.
"""
import asyncio
import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from main import manual_topic, publish_to_pending, record_published
from quality_checker import check_quality
from research import pick_topic, save_topic_history
from script_generator import build_description, generate_script
from utils import DATA_DIR, LOGS_DIR, OUTPUT_DIR, load_json, save_json, slugify
from video_renderer import render_video
from voice_generator import generate_voices

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
WEB_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Video Factory", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------- State Management
class JobState:
    def __init__(self):
        self.lock = threading.Lock()
        self.is_running = False
        self.current_step = "idle"
        self.step_message = "Hệ thống sẵn sàng"
        self.progress = 0
        self.error: Optional[str] = None
        self.logs: list[dict] = []
        self.current_video_folder: Optional[str] = None
        self.start_time: Optional[float] = None

    def add_log(self, text: str, level: str = "INFO"):
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": text.strip()
        }
        with self.lock:
            self.logs.append(entry)
            if len(self.logs) > 600:
                self.logs.pop(0)

    def set_step(self, step: str, message: str, progress: int):
        with self.lock:
            self.current_step = step
            self.step_message = message
            self.progress = progress
        self.add_log(f"[{step.upper()}] {message}", "INFO")

    def to_dict(self):
        with self.lock:
            elapsed = int(time.time() - self.start_time) if self.start_time and self.is_running else 0
            return {
                "is_running": self.is_running,
                "current_step": self.current_step,
                "step_message": self.step_message,
                "progress": self.progress,
                "error": self.error,
                "current_video_folder": self.current_video_folder,
                "elapsed_seconds": elapsed,
            }


job_state = JobState()


# Hook vào logger của factory để đẩy log vào frontend
class WebLogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            job_state.add_log(msg, record.levelname)
        except Exception:
            pass


root_logger = logging.getLogger()
web_handler = WebLogHandler()
web_handler.setFormatter(logging.Formatter("%(message)s"))
root_logger.addHandler(web_handler)


# ---------------------------------------------------------------- Pipeline Worker
def run_pipeline_thread(custom_topic: Optional[str]):

    job_state.is_running = True
    job_state.error = None
    job_state.start_time = time.time()
    job_state.current_video_folder = None
    job_state.set_step("starting", "Đang khởi động hệ thống...", 5)

    try:
        # Bước 1: Nghiên cứu chủ đề
        if custom_topic and custom_topic.strip():
            job_state.set_step("research", f"Dùng chủ đề: {custom_topic.strip()}", 15)
            topic = manual_topic(custom_topic.strip())
        else:
            job_state.set_step("research", "Đang quét Google Trends VN & phân tích bằng AI...", 15)
            topic = pick_topic()

        # Bước 2: Tạo kịch bản
        job_state.set_step("script", f"AI đang viết kịch bản: {topic['title']}", 30)
        script = generate_script(topic)

        # Bước 3: Tạo giọng đọc
        job_state.set_step("voice", f"KorvaTTS đang thu âm {len(script['scenes'])} phân cảnh...", 45)
        script = generate_voices(script)

        # Bước 4: Tạo ảnh & Dựng video
        job_state.set_step("render", "Đang tạo ảnh AI và ghép video 9:16 (FFmpeg)...", 65)
        script = render_video(script)

        # Bước 5: Kiểm tra chất lượng
        job_state.set_step("quality", "Đang kiểm tra chất lượng kỹ thuật và nội dung...", 85)
        report = check_quality(script)

        # Bước 6: Lưu kho pending
        job_state.set_step("saving", "Đang đóng gói video và xuất bản vào kho...", 95)
        folder = publish_to_pending(script, report)
        save_topic_history(script["topic"])
        record_published(script, folder, report)
        save_json(Path(script.get("script_path") or folder / "script.json"), script)

        job_state.current_video_folder = str(folder)
        job_state.set_step("done", f"Hoàn tất! Video đã sẵn sàng: {script['title']}", 100)
    except Exception as e:
        job_state.error = str(e)
        job_state.set_step("error", f"Lỗi: {e}", job_state.progress)
        job_state.add_log(f"LỖI: {e}", "ERROR")
    finally:
        job_state.is_running = False


# ---------------------------------------------------------------- API Endpoints
class GenerateRequest(BaseModel):
    topic: Optional[str] = None


@app.post("/api/generate")
def api_generate(req: GenerateRequest):
    if job_state.is_running:
        raise HTTPException(status_code=400, detail="Một tác vụ tạo video khác đang chạy!")
    t = threading.Thread(target=run_pipeline_thread, args=(req.topic,), daemon=True)
    t.start()
    return {"status": "started", "topic": req.topic or "auto"}


@app.get("/api/status")
def api_status():
    return job_state.to_dict()


@app.get("/api/logs")
def api_logs(since: int = 0):
    with job_state.lock:
        return job_state.logs[since:]


@app.get("/api/logs/stream")
async def api_logs_stream():
    """Server-Sent Events (SSE) để stream logs liên tục về Frontend."""
    async def event_generator():
        last_idx = 0
        while True:
            with job_state.lock:
                current_logs = list(job_state.logs)
                status_dict = job_state.to_dict()

            if last_idx < len(current_logs):
                new_items = current_logs[last_idx:]
                last_idx = len(current_logs)
                payload = {
                    "status": status_dict,
                    "logs": new_items
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'status': status_dict, 'logs': []}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.8)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/videos")
def api_list_videos():
    """Quét toàn bộ video có trong output/pending."""
    pending_dir = OUTPUT_DIR / "pending"
    results = []
    if not pending_dir.exists():
        return results

    folders = sorted([d for d in pending_dir.iterdir() if d.is_dir()],
                     key=lambda d: d.stat().st_mtime, reverse=True)

    for f in folders:
        video_file = f / "video.mp4"
        thumb_file = f / "thumbnail.jpg"
        report_file = f / "report.json"
        desc_file = f / "description.txt"
        title_file = f / "title.txt"
        script_file = f / "script.txt"
        review_file = f / "REVIEW.md"

        if not video_file.exists():
            continue

        title = title_file.read_text(encoding="utf-8").strip() if title_file.exists() else f.name
        desc = desc_file.read_text(encoding="utf-8").strip() if desc_file.exists() else ""
        script_text = script_file.read_text(encoding="utf-8").strip() if script_file.exists() else ""
        review_text = review_file.read_text(encoding="utf-8").strip() if review_file.exists() else ""
        report = load_json(report_file, {}) if report_file.exists() else {}

        stat = video_file.stat()
        created_dt = datetime.fromtimestamp(stat.st_mtime)

        results.append({
            "folder_name": f.name,
            "folder_path": str(f),
            "title": title,
            "description": desc,
            "script": script_text,
            "review": review_text,
            "report": report,
            "passed": report.get("passed", True),
            "duration": report.get("duration", 0),
            "created_at": created_dt.strftime("%d/%m/%Y %H:%M"),
            "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
            "video_url": f"/api/media/{f.name}/video.mp4",
            "thumb_url": f"/api/media/{f.name}/thumbnail.jpg" if thumb_file.exists() else None,
        })

    return results


@app.get("/api/media/{folder}/{filename}")
def api_get_media(folder: str, filename: str):
    file_path = OUTPUT_DIR / "pending" / folder / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File không tồn tại")
    return FileResponse(file_path)


@app.post("/api/open-folder")
def api_open_folder(data: dict):
    folder = data.get("folder")
    if folder and Path(folder).exists() and sys.platform == "win32":
        subprocess.run(["explorer", str(folder)])
        return {"status": "opened"}
    return {"status": "failed"}


# Phục vụ Frontend HTML
@app.get("/")
def serve_index():
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Frontend đang được xây dựng...</h1>")
    return FileResponse(index_file)


app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
