"""Tạo giọng đọc tiếng Việt cho từng cảnh bằng KorvaTTS (CLI)."""
import shutil
import sys
from pathlib import Path

from utils import OUTPUT_DIR, load_settings, log, media_duration, run_cmd


def _korvatts_cmd() -> str:
    cmd = load_settings().get("tts", {}).get("command", "korvatts")
    # Ưu tiên bản trong venv đang chạy
    venv_exe = Path(sys.executable).parent / ("korvatts.exe" if sys.platform == "win32" else "korvatts")
    if venv_exe.exists():
        return str(venv_exe)
    found = shutil.which(cmd)
    if not found:
        raise RuntimeError("Không tìm thấy KorvaTTS. Chạy: pip install korvatts")
    return found


def synth(text: str, out_wav: Path, voice: str) -> Path:
    run_cmd([_korvatts_cmd(), "synth", text, "-v", voice, "-o", str(out_wav)])
    if not out_wav.exists() or out_wav.stat().st_size < 1000:
        raise RuntimeError(f"KorvaTTS không tạo được file {out_wav}")
    return out_wav


def generate_voices(script: dict) -> dict:
    tts = load_settings().get("tts", {})
    voice = tts.get("voice", "khanh_vy")
    pause = float(tts.get("pause_between_scenes", 0.35))
    out_dir = OUTPUT_DIR / "audio" / f"{script['topic']['date'][:10]}_{script['slug']}"
    out_dir.mkdir(parents=True, exist_ok=True)

    for s in script["scenes"]:
        raw = out_dir / f"scene_{s['index']:02d}_raw.wav"
        wav = out_dir / f"scene_{s['index']:02d}.wav"
        log.info("TTS cảnh %d: %s", s["index"], s["narration"][:60])
        synth(s["narration"], raw, voice)
        # Chuẩn hóa 44.1kHz stereo + thêm khoảng lặng cuối cảnh
        run_cmd(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                 "-af", f"apad=pad_dur={pause}", "-ar", "44100", "-ac", "2", wav])
        raw.unlink(missing_ok=True)
        s["audio"] = str(wav)
        s["duration"] = round(media_duration(wav), 3)

    total = sum(s["duration"] for s in script["scenes"])
    script["audio_dir"] = str(out_dir)
    script["voice_duration"] = round(total, 2)
    log.info("Tổng thời lượng giọng đọc: %.1fs", total)
    return script


if __name__ == "__main__":
    out = OUTPUT_DIR / "audio" / "test.wav"
    synth("Xin chào, đây là video AI đầu tiên của chúng ta.", out,
          load_settings().get("tts", {}).get("voice", "khanh_vy"))
    print(out, media_duration(out))

