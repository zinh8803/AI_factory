"""Kiểm tra chất lượng: kỹ thuật (thời lượng, độ phân giải, âm thanh) + nội dung (AI review)."""
import json

from utils import ask_ollama, load_prompt, load_settings, log, run_cmd


def probe(path: str) -> dict:
    res = run_cmd(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    return json.loads(res.stdout)


def check_technical(script: dict) -> list[str]:
    cfg = load_settings().get("video", {})
    issues = []
    info = probe(script["video_path"])
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"].get("duration", 0))
    if not v:
        issues.append("Không có luồng video")
    elif (v["width"], v["height"]) != (cfg.get("width", 1080), cfg.get("height", 1920)):
        issues.append(f"Sai độ phân giải: {v['width']}x{v['height']}")
    if not a:
        issues.append("Không có âm thanh")
    if dur < cfg.get("min_duration", 45):
        issues.append(f"Video quá ngắn: {dur:.1f}s")
    if dur > cfg.get("max_duration", 90):
        issues.append(f"Video quá dài: {dur:.1f}s")

    # Phát hiện âm thanh im lặng/quá nhỏ
    res = run_cmd(["ffmpeg", "-i", script["video_path"], "-af", "volumedetect", "-vn", "-f", "null", "-"],
                  check=False)
    for line in res.stderr.splitlines():
        if "mean_volume" in line:
            mean = float(line.split(":")[1].replace("dB", "").strip())
            if mean < -40:
                issues.append(f"Âm lượng quá nhỏ ({mean} dB)")
    return issues


def check_content(script: dict) -> dict:
    base = load_prompt("quality_checker.txt")
    body = "\n".join(f"[{s['type']}] {s['narration']}" for s in script["scenes"])
    prompt = f"{base}\n\n=== TIÊU ĐỀ ===\n{script['title']}\n\n=== KỊCH BẢN ===\n{body}\n\n" \
             f"=== MÔ TẢ ===\n{script['full_description']}\n\nTrả lời DUY NHẤT JSON."
    try:
        r = ask_ollama(prompt, retries=1)
        r["score"] = int(float(r.get("score", 0)))
        return r
    except Exception as ex:  # noqa: BLE001
        log.warning("AI review lỗi: %s", ex)
        return {"score": 0, "passed": False, "issues": [f"Không chạy được AI review: {ex}"], "suggestions": []}


def check_quality(script: dict) -> dict:
    tech = check_technical(script)
    content = check_content(script)
    passed = not tech and content.get("score", 0) >= 70
    report = {"passed": passed, "technical_issues": tech, "content_review": content,
              "duration": script.get("video_duration")}
    log.info("Kiểm tra chất lượng: %s | kỹ thuật=%s | điểm nội dung=%s",
             "ĐẠT" if passed else "CẦN XEM LẠI", tech or "OK", content.get("score"))
    return report

