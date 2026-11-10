"""Tiện ích dùng chung: đường dẫn, cấu hình, log, gọi Ollama, đọc/ghi JSON."""
import json
import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "config"
PROMPTS_DIR = ROOT / "prompts"
ASSETS_DIR = ROOT / "assets"
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
LOGS_DIR = ROOT / "logs"

for d in [
    DATA_DIR / "trends", OUTPUT_DIR / "scripts", OUTPUT_DIR / "audio",
    OUTPUT_DIR / "images", OUTPUT_DIR / "videos", OUTPUT_DIR / "pending", LOGS_DIR,
    ASSETS_DIR / "backgrounds", ASSETS_DIR / "fonts", ASSETS_DIR / "music", ASSETS_DIR / "icons",
]:
    d.mkdir(parents=True, exist_ok=True)


def setup_logger(name: str = "factory") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(LOGS_DIR / f"{datetime.now():%Y-%m-%d}.log", encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


log = setup_logger()


def load_json(path: Path, default=None):
    try:
        text = Path(path).read_text(encoding="utf-8-sig").strip()
        return json.loads(text) if text else default
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: Path, data) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_settings() -> dict:
    return load_json(CONFIG_DIR / "settings.json", {}) or {}


def load_prompt(name: str, fallback: str = "") -> str:
    p = PROMPTS_DIR / name
    if p.exists():
        text = p.read_text(encoding="utf-8-sig").strip()
        if text:
            return text
    return fallback


def extract_json(text: str):
    """Lấy JSON đầu tiên trong câu trả lời của LLM."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start = text.find(open_c)
        end = text.rfind(close_c)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Không đọc được JSON từ LLM:\n{text[:500]}")


def ask_ollama(prompt: str, as_json: bool = True, system: str | None = None, retries: int = 2):
    cfg = load_settings().get("ollama", {})
    url = cfg.get("url", "http://localhost:11434").rstrip("/") + "/api/generate"
    payload = {
        "model": cfg.get("model", "qwen2.5:3b"),
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": cfg.get("temperature", 0.7), "num_ctx": 8192},
    }
    if system:
        payload["system"] = system
    if as_json:
        payload["format"] = "json"
    last_err = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=cfg.get("timeout", 600))
            r.raise_for_status()
            text = r.json().get("response", "")
            return extract_json(text) if as_json else text
        except Exception as e:  # noqa: BLE001
            last_err = e
            log.warning("Ollama lỗi (lần %d): %s", attempt + 1, e)
    raise RuntimeError(f"Không gọi được Ollama: {last_err}")


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    log.debug("RUN %s", " ".join(map(str, cmd)))
    res = subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if check and res.returncode != 0:
        raise RuntimeError(f"Lệnh lỗi ({res.returncode}): {' '.join(map(str, cmd))}\n{res.stderr[-2000:]}")
    return res


def media_duration(path: Path) -> float:
    res = run_cmd(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                   "-of", "default=noprint_wrappers=1:nokey=1", str(path)])
    return float(res.stdout.strip() or 0)


def slugify(text: str, max_len: int = 50) -> str:
    import unicodedata
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len].strip("-") or "video"

