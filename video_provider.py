"""Module tìm kiếm và tải Video chuyển động (Footage) tự động:
1. Mixkit Video: Hoàn toàn miễn phí, KHÔNG CẦN API KEY, chất lượng Full HD 1080p.
2. Pixabay Video API: Miễn phí, lấy key tức thì tại pixabay.com/api/docs/
3. Pexels Video API: Dự phòng khi có key.
"""
import random
import re
from pathlib import Path
from urllib.parse import quote

import requests

from utils import load_settings, log, media_duration, run_cmd

MIXKIT_CATEGORIES = {
    "coding": ["code", "coding", "program", "developer", "software", "python", "javascript", "algorithm", "it"],
    "robot": ["robot", "robotics", "android", "cyborg", "automation", "future", "futuristic"],
    "computer": ["computer", "screen", "monitor", "matrix", "display", "hardware", "server"],
    "typing": ["typing", "keyboard", "email", "writing", "chatgpt", "chat", "text"],
    "laptop": ["laptop", "notebook", "macbook"],
    "office": ["office", "meeting", "work", "job", "business", "presentation", "report"],
    "technology": ["technology", "tech", "digital", "ai", "artificial", "intelligence", "cloud", "network"]
}

_mixkit_cache: dict[str, list[str]] = {}


def _cfg() -> dict:
    return load_settings().get("video_source", {})


def determine_best_topic(scene: dict, script: dict) -> str:
    """Xác định danh mục video phù hợp nhất từ kịch bản."""
    text = " ".join([
        str(scene.get("video_keywords", "")),
        str(scene.get("image_prompt", "")),
        str(scene.get("on_screen", "")),
        str(script.get("title", "")),
        str(script.get("topic", {}).get("topic", ""))
    ]).lower()

    for category, keywords in MIXKIT_CATEGORIES.items():
        if any(kw in text for kw in keywords):
            return category
    return "technology"


def fetch_mixkit_video_urls(category: str) -> list[str]:
    """Lấy danh sách video MP4 trực tiếp từ Mixkit theo danh mục (Không cần API key)."""
    if category in _mixkit_cache and _mixkit_cache[category]:
        return _mixkit_cache[category]

    url = f"https://mixkit.co/free-stock-video/{category}/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            # Tìm tất cả link video mp4 HD 1080p hoặc 720p
            matches = list(set(re.findall(r"https://assets\.mixkit\.co/videos/\d+/\d+-(?:1080|720)\.mp4", r.text)))
            if matches:
                _mixkit_cache[category] = matches
                return matches
    except Exception as ex:  # noqa: BLE001
        log.warning("Không thể lấy video từ Mixkit (%s): %s", category, ex)

    # Dự phòng sang danh mục technology
    if category != "technology":
        return fetch_mixkit_video_urls("technology")
    return []


def search_pixabay_video(query: str, api_key: str) -> str | None:
    """Tìm video từ Pixabay Video API (nếu người dùng có key)."""
    if not api_key:
        return None
    url = f"https://pixabay.com/api/videos/?key={api_key}&q={quote(query)}&video_type=film&per_page=5"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            hits = r.json().get("hits", [])
            for h in hits:
                vids = h.get("videos", {})
                for q in ("large", "medium", "small"):
                    if q in vids and vids[q].get("url"):
                        return vids[q]["url"]
    except Exception as ex:  # noqa: BLE001
        log.warning("Lỗi tìm Pixabay video: %s", ex)
    return None


def download_and_conform_video(video_url: str, target_dur: float, out_path: Path) -> Path | None:
    """Tải video và cắt/loop/crop chuẩn 1080x1920 9:16 bằng FFmpeg."""
    tmp_raw = out_path.with_name(f"raw_{out_path.name}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(video_url, headers=headers, stream=True, timeout=60)
        if r.status_code != 200:
            return None
        with open(tmp_raw, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)

        dur = media_duration(tmp_raw)
        loop_times = int(target_dur // dur) + 1 if dur < target_dur else 1

        cfg = load_settings().get("video", {})
        W, H, fps = cfg.get("width", 1080), cfg.get("height", 1920), cfg.get("fps", 30)

        cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        if loop_times > 1:
            cmd += ["-stream_loop", str(loop_times)]
        cmd += [
            "-i", str(tmp_raw),
            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1",
            "-t", f"{target_dur:.3f}",
            "-r", str(fps),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-an",
            str(out_path)
        ]
        run_cmd(cmd)
        return out_path if out_path.exists() and out_path.stat().st_size > 10_000 else None
    except Exception as ex:  # noqa: BLE001
        log.warning("Lỗi xử lý video footage: %s", ex)
        return None
    finally:
        tmp_raw.unlink(missing_ok=True)


def fetch_scene_videos(script: dict, work: Path) -> bool:
    """Tìm và chuẩn bị video chuyển động cho tất cả phân cảnh."""
    cfg = _cfg()
    pixabay_key = (cfg.get("pixabay_api_key") or "").strip()
    success_count = 0

    log.info("Đang tự động tìm kiếm video chuyển động Full HD...")

    for s in script["scenes"]:
        out = work / f"stock_{s['index']:02d}.mp4"
        if out.exists() and out.stat().st_size > 50_000:
            s["video_clip"] = str(out)
            success_count += 1
            continue

        topic = determine_best_topic(s, script)
        video_url = None

        # 1. Thử qua Pixabay nếu có key
        if pixabay_key:
            video_url = search_pixabay_video(topic, pixabay_key)

        # 2. Mặc định dùng Mixkit (100% Miễn phí, KHÔNG CẦN KEY)
        if not video_url:
            urls = fetch_mixkit_video_urls(topic)
            if urls:
                # Chọn video theo thứ tự cảnh để mỗi cảnh là một clip khác nhau
                video_url = urls[s["index"] % len(urls)]

        if video_url:
            log.info("Tải video chuyển động cho cảnh %d (chủ đề: %s)...", s["index"], topic)
            res = download_and_conform_video(video_url, s["duration"], out)
            if res:
                s["video_clip"] = str(res)
                success_count += 1
                log.info("✓ Cảnh %d đã có video chuyển động!", s["index"])
            else:
                log.warning("Không tải được video cho cảnh %d", s["index"])
        else:
            log.warning("Không tìm thấy video chuyển động cho cảnh %d", s["index"])

    return success_count > 0
