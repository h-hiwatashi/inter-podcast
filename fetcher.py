import json
import feedparser
from datetime import datetime
from config import RSS_FEED_URL, PROCESSED_URLS_FILE, MAX_ARTICLES_PER_EPISODE


def load_processed_urls() -> set:
    try:
        with open(PROCESSED_URLS_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def fetch_new_articles() -> list[dict]:
    processed = load_processed_urls()
    feed = feedparser.parse(RSS_FEED_URL)

    new_articles = []
    for entry in feed.entries:
        url = entry.get("link", "")
        if not url or url in processed:
            continue

        summary = entry.get("summary", "") or entry.get("content", [{}])[0].get("value", "")
        # Strip basic HTML tags from summary
        import re
        summary = re.sub(r"<[^>]+>", " ", summary).strip()

        new_articles.append({
            "title": entry.get("title", ""),
            "summary": summary[:2000],
            "url": url,
            "published": entry.get("published", datetime.utcnow().isoformat()),
        })

        if len(new_articles) >= MAX_ARTICLES_PER_EPISODE:
            break

    return new_articles
