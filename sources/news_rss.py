import os
import re
import feedparser
from dotenv import load_dotenv

load_dotenv()


def fetch_news(max_per_feed: int = 8) -> list[dict]:
    urls = [u.strip() for u in os.environ.get("NEWS_RSS_FEEDS", "").split(",") if u.strip()]
    articles = []
    for url in urls:
        feed = feedparser.parse(url)
        source = feed.feed.get("title", url)
        for entry in feed.entries[:max_per_feed]:
            # Prefer full content over summary when available
            content = ""
            if entry.get("content"):
                content = entry["content"][0].get("value", "")
            if not content:
                content = entry.get("summary", "") or ""
            # Strip HTML tags from content
            content = re.sub(r"<[^>]+>", " ", content).strip()
            content = re.sub(r"\s+", " ", content)
            articles.append(
                {
                    "source": source,
                    "title": entry.get("title", ""),
                    "summary": content[:800],
                    "link": entry.get("link", ""),
                }
            )
    return articles
