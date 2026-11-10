"""Dựng video dọc 1080x1920: ảnh motion graphics (Pillow) + giọng đọc + phụ đề (FFmpeg)."""
import random
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from image_generator import generate_scene_images
from utils import ASSETS_DIR, OUTPUT_DIR, load_settings, log, media_duration, run_cmd

FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/tahoma.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_BOLD_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/tahomabd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
TYPE_LABEL = {"hook": "BẠN CÓ BIẾT?", "intro": "GIỚI THIỆU", "step": "HƯỚNG DẪN",
              "result": "KẾT QUẢ", "cta": "THEO DÕI NGAY"}


# ---------------------------------------------------------------- helpers
def _find_font(custom: str, candidates: list[str]) -> str:
    fonts_dir = sorted((ASSETS_DIR / "fonts").glob("*.ttf"))
    for p in [custom] + [str(f) for f in fonts_dir] + candidates:
        if p and Path(p).exists():
            return p
    raise RuntimeError("Không tìm thấy font .ttf hỗ trợ tiếng Việt. Hãy chép font vào assets/fonts/")


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _hex(c: str) -> tuple:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _fit_text(draw, text, font_path, max_w, max_h, start=120, min_size=50, spacing=1.2):
    size = start
    while size >= min_size:
        f = _font(font_path, size)
        lines = _wrap(draw, text, f, max_w)
        if len(lines) * size * spacing <= max_h:
            return f, lines
        size -= 6
    f = _font(font_path, min_size)
    return f, _wrap(draw, text, f, max_w)


def _gradient(w, h, c1, c2) -> Image.Image:
    top, bot = Image.new("RGB", (w, h), _hex(c1)), Image.new("RGB", (w, h), _hex(c2))
    mask = Image.linear_gradient("L").resize((w, h))
    return Image.composite(bot, top, mask)


def _background(w, h, colors, rng: random.Random) -> Image.Image:
    bgs = [p for p in (ASSETS_DIR / "backgrounds").glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    if bgs:
        img = Image.open(rng.choice(bgs)).convert("RGB")
        scale = max(w / img.width, h / img.height)
        img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1))
        l, t = (img.width - w) // 2, (img.height - h) // 2
        img = img.crop((l, t, l + w, t + h)).filter(ImageFilter.GaussianBlur(6))
        return Image.blend(img, Image.new("RGB", (w, h), (0, 0, 0)), 0.55)
    img = _gradient(w, h, *colors)
    # Họa tiết vòng tròn mờ trang trí
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for _ in range(7):
        r = rng.randint(120, 420)
        x, y = rng.randint(-100, w + 100), rng.randint(-100, h + 100)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, rng.randint(10, 28)))
    overlay = overlay.filter(ImageFilter.GaussianBlur(30))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def _icon(scene: dict) -> Image.Image | None:
    key = (scene.get("icon") or "").lower().strip()
    icons = list((ASSETS_DIR / "icons").glob("*.png"))
    if not icons:
        return None
    match = [p for p in icons if key and key in p.stem.lower()]
    return Image.open((match or icons)[0]).convert("RGBA") if match else None


# ---------------------------------------------------------------- frames
def _cover(img: Image.Image, w: int, h: int) -> Image.Image:
    scale = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1), Image.LANCZOS)
    l, t = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((l, t, l + w, t + h))


def _vertical_shade(w: int, h: int, top_alpha: int, top_end: int, bot_start: int, bot_alpha: int) -> Image.Image:
    """Lớp tối dần ở trên và dưới để chữ dễ đọc trên ảnh AI."""
    col = Image.new("L", (1, h), 0)
    px = col.load()
    for y in range(h):
        a = 0
        if y < top_end:
            a = int(top_alpha * (1 - y / top_end))
        elif y > bot_start:
            a = int(bot_alpha * (y - bot_start) / (h - bot_start))
        px[0, y] = max(a, 40)
    mask = col.resize((w, h))
    shade = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    shade.putalpha(mask)
    return shade


def render_scene_layers(scene: dict, total: int, title: str, work: Path, rng: random.Random) -> tuple[Path, Path]:
    """Trả về (nền chuyển động, lớp chữ trong suốt)."""
    cfg = load_settings().get("video", {})
    W, H = cfg.get("width", 1080), cfg.get("height", 1920)
    accent = _hex(cfg.get("accent_color", "#ffd166"))
    fr = _find_font(cfg.get("font_path", ""), FONT_CANDIDATES)
    fb = _find_font(cfg.get("font_bold_path", ""), FONT_BOLD_CANDIDATES)
    colors = rng.choice(cfg.get("theme_colors", [["#0f2027", "#2c5364"]]))

    # ---- Lớp nền
    has_ai = bool(scene.get("image")) and Path(scene["image"]).exists()
    if has_ai:
        bg = _cover(Image.open(scene["image"]).convert("RGB"), W, H).convert("RGBA")
        bg = Image.alpha_composite(bg, _vertical_shade(W, H, 210, 950, 1150, 230))
    else:
        bg = _background(W, H, colors, rng).convert("RGBA")
    bg_path = work / f"bg_{scene['index']:02d}.png"
    bg.convert("RGB").save(bg_path)

    # ---- Lớp chữ (trong suốt)
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    d.text((W // 2, 150), cfg.get("channel_name", "AI Thực Chiến").upper(), font=_font(fb, 46),
           fill=(255, 255, 255, 235), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0, 160))
    bar_w = W - 160
    d.rounded_rectangle((80, 210, 80 + bar_w, 222), 6, fill=(255, 255, 255, 70))
    d.rounded_rectangle((80, 210, 80 + int(bar_w * (scene["index"] + 1) / total), 222), 6, fill=accent)

    label = TYPE_LABEL.get(scene.get("type", "step"), "HƯỚNG DẪN")
    if scene.get("type") == "step" and scene.get("step_no"):
        label = f"BƯỚC {scene['step_no']}"
    label_y = 340 if has_ai else 420
    lf = _font(fb, 52)
    lw = d.textlength(label, font=lf)
    d.rounded_rectangle((W / 2 - lw / 2 - 40, label_y, W / 2 + lw / 2 + 40, label_y + 100), 50, fill=accent)
    d.text((W // 2, label_y + 50), label, font=lf, fill=(20, 20, 30), anchor="mm")

    y_text_top = label_y + 150
    icon = _icon(scene)
    if icon and not has_ai:
        icon.thumbnail((260, 260))
        fg.alpha_composite(icon, ((W - icon.width) // 2, 580))
        y_text_top = 880

    # Có ảnh AI: chữ chính gọn ở phần trên để lộ hình; không có: chữ lớn giữa màn hình
    bottom = 900 if has_ai else 1220
    start = 96 if has_ai else 120
    font, lines = _fit_text(d, scene["on_screen"], fb, W - 160, bottom - y_text_top, start=start)
    lh = int(font.size * 1.2)
    y = y_text_top + (0 if has_ai else (bottom - y_text_top - lh * len(lines)) // 2)
    for line in lines:
        d.text((W // 2, y), line, font=font, fill=(255, 255, 255), anchor="ma",
               stroke_width=4, stroke_fill=(0, 0, 0, 200))
        y += lh

    clean_title = re.sub(r"^(tentative\s+title|title|tiêu đề)\s*:\s*", "", title, flags=re.IGNORECASE).strip(" \"'")
    short = textwrap.shorten(clean_title, 60, placeholder="…")
    d.text((W // 2, H - 110), short, font=_font(fr, 34), fill=(255, 255, 255, 190), anchor="mm",
           stroke_width=1, stroke_fill=(0, 0, 0, 160))
    fg_path = work / f"fg_{scene['index']:02d}.png"
    fg.save(fg_path)

    # Ảnh xem trước (thumbnail)
    Image.alpha_composite(bg, fg).convert("RGB").save(work / f"scene_{scene['index']:02d}.png", quality=95)
    return bg_path, fg_path


def split_subtitles(text: str, max_words: int = 6) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    raw_parts = re.split(r"(?<=[.,!?:;])\s+", text)
    chunks = []
    for part in raw_parts:
        part = part.strip()
        if not part:
            continue
        words = part.split()
        if len(words) <= max_words:
            chunks.append(part)
        else:
            for i in range(0, len(words), max_words):
                group = words[i:i + max_words]
                if group:
                    chunks.append(" ".join(group))
    return chunks or [text]


def render_subtitle(text: str, out: Path) -> Path:
    cfg = load_settings().get("video", {})
    W, H = cfg.get("width", 1080), cfg.get("height", 1920)
    fb = _find_font(cfg.get("font_bold_path", ""), FONT_BOLD_CANDIDATES)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = _font(fb, 56)
    lines = _wrap(d, text, font, W - 240)
    if not lines:
        lines = [text]
    lh = 72
    box_h = lh * len(lines) + 36
    max_line_w = max(d.textlength(line, font=font) for line in lines)
    box_w = min(W - 120, int(max_line_w + 70))
    left = (W - box_w) // 2
    top = 1420

    d.rounded_rectangle((left, top, left + box_w, top + box_h), radius=26, fill=(15, 18, 26, 215),
                        outline=(255, 255, 255, 60), width=2)
    y = top + 18
    for line in lines:
        d.text((W // 2, y), line, font=font, fill=_hex(cfg.get("accent_color", "#ffd166")), anchor="ma",
               stroke_width=3, stroke_fill=(0, 0, 0, 240))
        y += lh
    img.save(out)
    return out


# ---------------------------------------------------------------- ffmpeg
def render_scene_clip(scene: dict, bg_png: Path, fg_png: Path, work: Path) -> Path:
    cfg = load_settings().get("video", {})
    W, H, fps = cfg.get("width", 1080), cfg.get("height", 1920), cfg.get("fps", 30)
    dur = scene["duration"]
    frames = max(1, int(dur * fps))

    subs = split_subtitles(scene["narration"])
    weights = [max(len(s), 1) for s in subs]
    speech = max(dur - 0.3, 0.5)
    t, timings = 0.0, []
    for i, s in enumerate(subs):
        seg = speech * weights[i] / sum(weights)
        png = render_subtitle(s, work / f"sub_{scene['index']:02d}_{i:02d}.png")
        timings.append((png, t, t + seg if i < len(subs) - 1 else dur))
        t += seg

    def still(p):
        return ["-loop", "1", "-framerate", str(fps), "-t", f"{dur:.3f}", "-i", str(p)]

    inputs = still(bg_png) + still(fg_png)
    for png, _, _ in timings:
        inputs += still(png)
    inputs += ["-i", scene["audio"]]

    # Chuyển động camera cho nền: luân phiên zoom vào / zoom ra / lia ngang / lia dọc
    z_in, z_out = f"1+0.15*on/{frames}", f"1.15-0.15*on/{frames}"
    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    moves = [
        (z_in, cx, cy),
        (z_out, cx, cy),
        ("1.15", f"(iw-iw/zoom)*on/{frames}", cy),        # lia trái → phải
        ("1.15", f"(iw-iw/zoom)*(1-on/{frames})", cy),    # lia phải → trái
        ("1.12", cx, f"(ih-ih/zoom)*(1-on/{frames})"),    # lia dưới → trên
    ]
    z, x, y = moves[scene["index"] % len(moves)]
    fc = [f"[0:v]scale={W * 2}:{H * 2},zoompan=z='{z}':x='{x}':y='{y}'"
          f":d={frames}:s={W}x{H}:fps={fps},setsar=1[bg0]",
          # Lớp chữ trượt từ dưới lên + hiện dần
          f"[1:v]format=rgba,fade=t=in:st=0.1:d=0.45:alpha=1[fg]",
          f"[bg0][fg]overlay=x=0:y='max(0,60-(t-0.1)*140)'[bg1]"]
    last = "bg1"
    for i, (_, a, b) in enumerate(timings, start=2):
        fc.append(f"[{last}][{i}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[s{i}]")
        last = f"s{i}"
    fade_out = max(dur - 0.25, 0)
    fc.append(f"[{last}]fade=t=in:st=0:d=0.25,fade=t=out:st={fade_out:.3f}:d=0.25,format=yuv420p[v]")
    audio_idx = len(timings) + 2

    out = work / f"clip_{scene['index']:02d}.mp4"
    run_cmd(["ffmpeg", "-y", "-loglevel", "error", *inputs,
             "-filter_complex", ";".join(fc), "-map", "[v]", "-map", f"{audio_idx}:a",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", str(fps),
             "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
             "-t", f"{dur:.3f}", "-movflags", "+faststart", str(out)])
    return out


def _pick_music(rng: random.Random) -> Path | None:
    files = []
    for p in (ASSETS_DIR / "music").glob("*"):
        if p.suffix.lower() not in (".mp3", ".wav", ".m4a", ".ogg"):
            continue
        try:
            if media_duration(p) < 15:  # bỏ qua file test/giọng nói ngắn, không phải nhạc nền
                log.warning("Bỏ qua %s: quá ngắn để làm nhạc nền", p.name)
                continue
        except Exception:  # noqa: BLE001
            continue
        files.append(p)
    return rng.choice(files) if files else None


def render_video(script: dict) -> dict:
    cfg = load_settings().get("video", {})
    rng = random.Random(script["slug"])
    name = f"{script['topic']['date'][:10]}_{script['slug']}"
    work = OUTPUT_DIR / "images" / name
    work.mkdir(parents=True, exist_ok=True)

    step_no = 0
    for s in script["scenes"]:
        if s.get("type") == "step":
            step_no += 1
            s["step_no"] = step_no

    generate_scene_images(script, work)

    clips = []
    total = len(script["scenes"])
    for s in script["scenes"]:
        log.info("Dựng cảnh %d/%d", s["index"] + 1, total)
        bg, fg = render_scene_layers(s, total, script["title"], work, rng)
        clips.append(render_scene_clip(s, bg, fg, work))

    concat_list = work / "concat.txt"
    concat_list.write_text("\n".join(f"file '{c.as_posix()}'" for c in clips), encoding="utf-8")
    joined = work / "joined.mp4"
    run_cmd(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", concat_list, "-c", "copy", joined])

    final = OUTPUT_DIR / "videos" / f"{name}.mp4"
    music = _pick_music(rng)
    if music:
        vol = cfg.get("background_music_volume", 0.08)
        dur = media_duration(joined)
        log.info("Thêm nhạc nền: %s", music.name)
        run_cmd(["ffmpeg", "-y", "-loglevel", "error", "-i", joined, "-stream_loop", "-1", "-i", music,
                 "-filter_complex",
                 f"[1:a]volume={vol},afade=t=out:st={max(dur - 2, 0):.2f}:d=2[m];"
                 f"[0:a][m]amix=inputs=2:duration=first:dropout_transition=0,"
                 f"loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                 "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                 "-movflags", "+faststart", final])
    else:
        log.info("Không có nhạc trong assets/music – chỉ dùng giọng đọc")
        run_cmd(["ffmpeg", "-y", "-loglevel", "error", "-i", joined, "-c:v", "copy",
                 "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                 "-movflags", "+faststart", final])

    # Ảnh thumbnail = cảnh hook
    thumb = OUTPUT_DIR / "videos" / f"{name}.jpg"
    Image.open(work / "scene_00.png").save(thumb, quality=92)

    for c in clips + [joined]:
        c.unlink(missing_ok=True)
    script["video_path"] = str(final)
    script["thumbnail_path"] = str(thumb)
    script["video_duration"] = round(media_duration(final), 2)
    log.info("Video hoàn thành: %s (%.1fs)", final, script["video_duration"])
    return script


if __name__ == "__main__":
    import sys
    from utils import load_json
    if len(sys.argv) < 2:
        print("Cách dùng: python video_renderer.py output/scripts/<file>.json  (kịch bản đã có audio)")
    else:
        render_video(load_json(Path(sys.argv[1])))

