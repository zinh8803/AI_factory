"""Thu thập xu hướng Google Trends (RSS) và để AI chọn chủ đề tốt nhất trong ngày."""
from datetime import datetime, timedelta

import feedparser
import requests

from utils import (CONFIG_DIR, DATA_DIR, ask_ollama, load_json, load_prompt,
                   load_settings, log, save_json)

HISTORY_FILE = DATA_DIR / "topics_history.json"

DEFAULT_PROMPT = """Bạn là chuyên gia nghiên cứu nội dung video ngắn cho thị trường Việt Nam.
Chọn một chủ đề tốt nhất về AI và công nghệ thực chiến cho người Việt để làm một video ngắn hôm nay.
ĐẦU RA JSON: {"topic":"","title":"","reason":"","target_audience":"","hook":"","affiliate_opportunity":"","source_urls":[],"confidence":0}"""

# Chủ đề dự phòng khi không có xu hướng phù hợp / AI không đủ dữ liệu
EVERGREEN_TOPICS = [
    "3 cách dùng AI để tiết kiệm thời gian mỗi ngày",
    "Dùng AI tóm tắt tài liệu dài trong 1 phút",
    "Chuyển văn bản thành giọng đọc tiếng Việt miễn phí",
    "Dùng AI viết email công việc chuyên nghiệp",
    "AI hỗ trợ làm Excel nhanh hơn",
    "Tạo website đơn giản với trợ lý AI",
    "Chạy AI miễn phí ngay trên máy tính với Ollama",
    "Cách viết prompt hiệu quả cho người mới",
    "Dùng AI lên kế hoạch học tập và làm việc",
    "Tự động hóa công việc lặp lại bằng AI",
]


def fetch_trends() -> list[dict]:
    cfg = load_settings().get("trends", {})
    items: list[dict] = []
    for url in cfg.get("rss_urls", []):
        try:
            resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            feed = feedparser.parse(resp.content)
            for e in feed.entries:
                news = []
                for key in ("ht_news_item_title", "ht_news_item_url"):
                    if key in e:
                        news.append(e[key])
                items.append({
                    "keyword": e.get("title", ""),
                    "traffic": e.get("ht_approx_traffic", ""),
                    "link": e.get("ht_news_item_url") or e.get("link", ""),
                    "news_title": e.get("ht_news_item_title", ""),
                })
        except Exception as ex:  # noqa: BLE001
            log.warning("Không đọc được RSS %s: %s", url, ex)
    items = items[: cfg.get("max_items", 25)]
    save_json(DATA_DIR / "trends" / f"{datetime.now():%Y-%m-%d}.json", items)
    log.info("Đã thu thập %d xu hướng", len(items))
    return items


def recent_topics() -> list[dict]:
    history = load_json(HISTORY_FILE, []) or []
    days = load_settings().get("history_days_no_repeat", 60)
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    return [h for h in history if h.get("date", "") >= cutoff]


def active_affiliates() -> list[dict]:
    data = load_json(CONFIG_DIR / "affiliate.json", {}) or {}
    return [p for p in data.get("products", []) if p.get("active")]


def pick_topic() -> dict:
    trends = fetch_trends()
    recent = recent_topics()
    affiliates = active_affiliates()

    base = load_prompt("topic_research.txt", DEFAULT_PROMPT)
    trend_text = "\n".join(
        f"- {t['keyword']} (lượt tìm: {t['traffic']}) | tin: {t['news_title']} | {t['link']}"
        for t in trends) or "(Không có dữ liệu xu hướng hôm nay)"
    recent_text = "\n".join(f"- {h['title']}" for h in recent[-30:]) or "(Chưa có)"
    aff_text = "\n".join(f"- {p['name']} ({p['category']})" for p in affiliates) or "(Không có)"
    evergreen = "\n".join(f"- {t}" for t in EVERGREEN_TOPICS)

    prompt = f"""{base}

=== XU HƯỚNG GOOGLE TRENDS VIỆT NAM HÔM NAY ===
{trend_text}

=== CHỦ ĐỀ ĐÃ ĐĂNG GẦN ĐÂY (KHÔNG ĐƯỢC TRÙNG) ===
{recent_text}

=== SẢN PHẨM AFFILIATE CÓ THỂ GIỚI THIỆU ===
{aff_text}

=== CHỦ ĐỀ BỀN VỮNG (dùng nếu xu hướng không phù hợp kênh) ===
{evergreen}

Hôm nay là {datetime.now():%d/%m/%Y}. Trả lời DUY NHẤT một object JSON đúng định dạng, viết tiếng Việt có dấu.
"confidence" là số từ 0 đến 100. "affiliate_opportunity" ghi tên sản phẩm phù hợp hoặc "" nếu không phù hợp."""

    try:
        topic = ask_ollama(prompt)
        if not isinstance(topic, dict) or not topic.get("title"):
            raise ValueError("AI không trả về tiêu đề")
    except Exception as ex:  # noqa: BLE001
        log.warning("AI không chọn được chủ đề (%s) – dùng chủ đề dự phòng", ex)
        used = {h["title"] for h in recent}
        title = next((t for t in EVERGREEN_TOPICS if t not in used), EVERGREEN_TOPICS[0])
        topic = {"topic": title, "title": title, "reason": "Chủ đề bền vững dự phòng",
                 "target_audience": "Người đi làm, sinh viên Việt Nam", "hook": "",
                 "affiliate_opportunity": "", "source_urls": [], "confidence": 50}

    topic.setdefault("topic", topic["title"])
    topic.setdefault("source_urls", [])
    topic["date"] = datetime.now().isoformat(timespec="seconds")
    log.info("Chủ đề được chọn: %s (confidence=%s)", topic["title"], topic.get("confidence"))
    return topic


def save_topic_history(topic: dict) -> None:
    history = load_json(HISTORY_FILE, []) or []
    history.append({"date": topic["date"], "title": topic["title"], "topic": topic.get("topic", "")})
    save_json(HISTORY_FILE, history)


if __name__ == "__main__":
    import json
    print(json.dumps(pick_topic(), ensure_ascii=False, indent=2))

