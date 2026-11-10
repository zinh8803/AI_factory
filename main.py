"""AI Video Factory – chạy toàn bộ pipeline tạo 1 video/ngày.

Cách dùng:
    python main.py                       # tự nghiên cứu chủ đề và tạo video
    python main.py --topic "Tiêu đề"     # chỉ định chủ đề thủ công
    python main.py --script output/scripts/xxx.json   # dựng lại từ kịch bản có sẵn
"""
import argparse
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path

from quality_checker import check_quality
from research import pick_topic, save_topic_history
from script_generator import build_description, generate_script
from utils import DATA_DIR, OUTPUT_DIR, load_json, log, save_json, slugify
from video_renderer import render_video
from voice_generator import generate_voices


def preflight() -> None:
    import requests
    from utils import load_settings
    missing = [t for t in ("ffmpeg", "ffprobe") if not shutil.which(t)]
    if missing:
        raise RuntimeError(f"Thiếu {missing}. Cài FFmpeg và thêm vào PATH.")
    url = load_settings().get("ollama", {}).get("url", "http://localhost:11434")
    try:
        requests.get(url, timeout=5)
    except Exception:
        raise RuntimeError(f"Ollama chưa chạy tại {url}. Mở Ollama rồi thử lại.")


def manual_topic(title: str) -> dict:
    return {"topic": title, "title": title, "reason": "Chủ đề thủ công", "target_audience": "Người Việt",
            "hook": "", "affiliate_opportunity": "", "source_urls": [], "confidence": 100,
            "date": datetime.now().isoformat(timespec="seconds")}


def publish_to_pending(script: dict, report: dict) -> Path:
    name = Path(script["video_path"]).stem
    folder = OUTPUT_DIR / "pending" / name
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(script["video_path"], folder / "video.mp4")
    shutil.copy2(script["thumbnail_path"], folder / "thumbnail.jpg")
    (folder / "title.txt").write_text(script["title"], encoding="utf-8")
    (folder / "description.txt").write_text(script["full_description"], encoding="utf-8")
    (folder / "script.txt").write_text(
        "\n\n".join(f"[{s['type']}] {s['narration']}" for s in script["scenes"]), encoding="utf-8")
    save_json(folder / "report.json", report)
    checklist = [
        f"# Review: {script['title']}", "",
        f"- Trạng thái tự động: {'ĐẠT' if report['passed'] else 'CẦN XEM LẠI'}",
        f"- Thời lượng: {script.get('video_duration')}s",
        f"- Điểm nội dung AI: {report['content_review'].get('score')}",
        f"- Lỗi kỹ thuật: {', '.join(report['technical_issues']) or 'không'}",
        f"- Góp ý: {'; '.join(map(str, report['content_review'].get('issues', []))) or 'không'}", "",
        "## Checklist trước khi đăng",
        "- [ ] Xem hết video, giọng đọc rõ, phụ đề khớp",
        "- [ ] Thông tin/tính năng/giá đã kiểm tra nguồn chính thức",
        "- [ ] Nhạc nền và hình ảnh có giấy phép hợp lệ",
        "- [ ] Link Affiliate đúng và có dòng công khai hoa hồng",
        "- [ ] Bật nhãn nội dung AI trên TikTok/YouTube khi cần",
        "- [ ] Đăng YouTube Shorts / TikTok / Facebook Reels",
    ]
    (folder / "REVIEW.md").write_text("\n".join(checklist), encoding="utf-8")
    return folder


def record_published(script: dict, folder: Path, report: dict) -> None:
    path = DATA_DIR / "published_history.json"
    hist = load_json(path, []) or []
    hist.append({"date": script["topic"]["date"], "title": script["title"], "folder": str(folder),
                 "duration": script.get("video_duration"), "passed": report["passed"],
                 "affiliate": (script.get("affiliate") or {}).get("name", ""),
                 "views": None, "affiliate_clicks": None, "signups": None, "commission": None})
    save_json(path, hist)


def run(topic_title: str | None = None, script_path: str | None = None) -> int:
    start = datetime.now()
    log.info("=" * 60)
    log.info("AI VIDEO FACTORY – bắt đầu %s", start.strftime("%Y-%m-%d %H:%M"))
    preflight()

    if script_path:
        script = load_json(Path(script_path))
        script.setdefault("slug", slugify(script["title"]))
        script["full_description"] = script.get("full_description") or build_description(script)
    else:
        topic = manual_topic(topic_title) if topic_title else pick_topic()
        script = generate_script(topic)

    script = generate_voices(script)
    script = render_video(script)
    report = check_quality(script)
    folder = publish_to_pending(script, report)

    if not script_path:
        save_topic_history(script["topic"])
    record_published(script, folder, report)
    save_json(Path(script.get("script_path") or folder / "script.json"), script)

    log.info("Hoàn tất trong %s. Video chờ duyệt tại: %s", datetime.now() - start, folder)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="AI Video Factory")
    ap.add_argument("--topic", help="Chỉ định chủ đề thay vì để AI nghiên cứu")
    ap.add_argument("--script", help="Dựng video từ file kịch bản JSON có sẵn")
    args = ap.parse_args()
    try:
        return run(args.topic, args.script)
    except Exception as ex:  # noqa: BLE001
        log.error("Pipeline thất bại: %s\n%s", ex, traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())

