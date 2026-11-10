"""Tạo ảnh minh họa AI cho từng cảnh qua Pollinations.ai (miễn phí, không cần API key).

Lưu ý bản quyền: kiểm tra điều khoản sử dụng hiện hành của Pollinations trước khi kiếm tiền.
"""
import hashlib
import time
from pathlib import Path
from urllib.parse import quote

import requests

from utils import load_settings, log

STYLE_SUFFIX = ("cinematic lighting, vibrant colors, highly detailed, modern tech aesthetic, "
                "vertical composition, no text, no letters, no watermark")


def _cfg() -> dict:
    return load_settings().get("images", {})


def build_prompt(scene: dict, script: dict) -> str:
    base = (scene.get("image_prompt") or "").strip()
    if not base:
        topic = script.get("topic", {}).get("topic") or script.get("title", "")
        base = f"illustration about {topic}, {scene.get('on_screen', '')}"
    style = _cfg().get("style", STYLE_SUFFIX)
    return f"{base}, {style}"


_last_request = 0.0


def _wait_rate_limit(interval: float) -> None:
    global _last_request
    wait = _last_request + interval - time.time()
    if wait > 0:
        log.info("Chờ %.0fs theo giới hạn miễn phí của Pollinations...", wait)
        time.sleep(wait)
    _last_request = time.time()


def generate_image(prompt: str, out: Path, seed: int) -> Path | None:
    cfg = _cfg()
    vcfg = load_settings().get("video", {})
    w, h = vcfg.get("width", 1080), vcfg.get("height", 1920)
    key = (cfg.get("api_key") or "").strip()
    # Không có key: bản miễn phí giới hạn 1 ảnh / 45 giây / IP
    interval = 2 if key else float(cfg.get("free_interval_seconds", 47))
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    params = f"?width={w}&height={h}&seed={seed}&nologo=true"
    if cfg.get("model"):
        params += f"&model={cfg['model']}"
    url = f"https://image.pollinations.ai/prompt/{quote(prompt[:900])}{params}"
    for attempt in range(cfg.get("retries", 3)):
        _wait_rate_limit(interval)
        try:
            r = requests.get(url, headers=headers, timeout=cfg.get("timeout", 180))
            ctype = r.headers.get("content-type", "")
            if r.status_code == 200 and ctype.startswith("image") and len(r.content) > 10_000:
                out.write_bytes(r.content)
                return out
            log.warning("Pollinations trả về %s: %s", r.status_code, r.text[:200])
        except Exception as ex:  # noqa: BLE001
            log.warning("Tạo ảnh lỗi (lần %d): %s", attempt + 1, ex)
    return None


def generate_scene_images(script: dict, work: Path) -> None:
    if not _cfg().get("enabled", True):
        return
    for s in script["scenes"]:
        out = work / f"ai_{s['index']:02d}.jpg"
        if out.exists() and out.stat().st_size > 10_000:
            s["image"] = str(out)
            continue
        prompt = build_prompt(s, script)
        seed = int(hashlib.md5(f"{script['slug']}{s['index']}".encode()).hexdigest()[:8], 16) % 2_000_000_000
        log.info("Tạo ảnh AI cảnh %d: %s", s["index"], prompt[:80])
        if generate_image(prompt, out, seed):
            s["image"] = str(out)
        else:
            log.warning("Không tạo được ảnh cảnh %d – dùng nền mặc định", s["index"])
