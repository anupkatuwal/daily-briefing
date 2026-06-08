import os
import feedparser
from dotenv import load_dotenv

load_dotenv()


def fetch_news(max_per_feed: int = 5) -> list[dict]:
    urls = [u.strip() for u in os.environ.get("NEWS_RSS_FEEDS", "").split(",") if u.strip()]
    articles = []
    for url in urls:
        feed = feedparser.parse(url)
        source = feed.feed.get("title", url)
        for entry in feed.entries[:max_per_feed]:
            articles.append(
                {
                    "source": source,
                    "title": entry.get("title", ""),
                    "summary": (entry.get("summary", "") or "")[:300],
                    "link": entry.get("link", ""),
                }
            )
    return articles
