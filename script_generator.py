"""Tạo kịch bản chia cảnh, mô tả, hashtag và chèn Affiliate (nếu phù hợp)."""
import re

from research import active_affiliates
from utils import OUTPUT_DIR, ask_ollama, load_prompt, load_settings, log, save_json, slugify

MIN_SCENES, MAX_SCENES = 5, 12


def _clean_narration(text: str) -> str:
    text = re.sub(r"[*#_`~>\[\]{}|<]", "", str(text))
    text = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", "", text)  # emoji
    return re.sub(r"\s+", " ", text).strip()


def _match_affiliate(topic: dict) -> dict | None:
    opp = (topic.get("affiliate_opportunity") or "").lower()
    if not opp:
        return None
    for p in active_affiliates():
        url = p.get("affiliate_url", "")
        if p["name"].lower() in opp and url and not url.startswith("YOUR_"):
            return p
    return None


def generate_script(topic: dict) -> dict:
    affiliate = _match_affiliate(topic)
    base = load_prompt("script_writer.txt")
    prompt = f"""{base}

=== CHỦ ĐỀ ===
Tiêu đề gợi ý: {topic['title']}
Chủ đề: {topic.get('topic', '')}
Đối tượng: {topic.get('target_audience', '')}
Hook gợi ý: {topic.get('hook', '')}
Lý do chọn: {topic.get('reason', '')}
Nguồn tham khảo: {', '.join(topic.get('source_urls', [])) or 'không có'}
Sản phẩm Affiliate phù hợp: {affiliate['name'] if affiliate else 'KHÔNG CÓ – không nhắc tới link hay sản phẩm'}

Trả lời DUY NHẤT một object JSON, tiếng Việt có dấu."""

    script = None
    for attempt in range(3):
        try:
            data = ask_ollama(prompt)
            scenes = [s for s in data.get("scenes", []) if isinstance(s, dict) and s.get("narration")]
            if len(scenes) < MIN_SCENES:
                raise ValueError(f"Chỉ có {len(scenes)} cảnh")
            data["scenes"] = scenes[:MAX_SCENES]
            script = data
            break
        except Exception as ex:  # noqa: BLE001
            log.warning("Tạo kịch bản lỗi (lần %d): %s", attempt + 1, ex)
    if script is None:
        raise RuntimeError("Không tạo được kịch bản hợp lệ")

    for i, s in enumerate(script["scenes"]):
        s["index"] = i
        s["narration"] = _clean_narration(s["narration"])
        s["on_screen"] = _clean_narration(s.get("on_screen") or s["narration"][:60])
        s.setdefault("type", "step")

    title = (script.get("title") or topic["title"]).strip()
    title = re.sub(r"^(tentative\s+title|title|tiêu đề)\s*:\s*", "", title, flags=re.IGNORECASE)
    script["title"] = title.strip(" \"'")[:100]
    tags = script.get("hashtags") or []
    tags = [t if str(t).startswith("#") else f"#{t}" for t in tags]
    for t in ["#AI", "#AIThucChien", "#Shorts"]:
        if t not in tags:
            tags.append(t)
    script["hashtags"] = [re.sub(r"\s+", "", t) for t in tags][:10]
    script["topic"] = topic
    script["affiliate"] = affiliate
    script["slug"] = slugify(script["title"])
    script["full_description"] = build_description(script)

    path = OUTPUT_DIR / "scripts" / f"{topic['date'][:10]}_{script['slug']}.json"
    save_json(path, script)
    script["script_path"] = str(path)
    log.info("Kịch bản: %s (%d cảnh) -> %s", script["title"], len(script["scenes"]), path.name)
    return script


def build_description(script: dict) -> str:
    settings = load_settings()
    lines = [script["title"], "", script.get("description", "").strip()]
    aff = script.get("affiliate")
    if aff:
        lines += ["", f"👉 {aff['name']}: {aff['affiliate_url']}", "",
                  settings.get("affiliate", {}).get("disclosure", "")]
    srcs = script["topic"].get("source_urls") or []
    if srcs:
        lines += ["", "Nguồn tham khảo:"] + [f"- {u}" for u in srcs]
    lines += ["", "Nội dung có sử dụng giọng đọc và hình ảnh tạo bởi AI.", "",
              " ".join(script["hashtags"])]
    return "\n".join(lines).strip()


if __name__ == "__main__":
    from research import pick_topic
    print(generate_script(pick_topic())["full_description"])

