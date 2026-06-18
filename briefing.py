import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from sources.gmail import fetch_emails
from sources.calender_events import fetch_events
from sources.news_rss import fetch_news
from sources.send_email import send_briefing
from classifier import generate_briefing


def run():
    print("Fetching emails...")
    emails = fetch_emails()
    print(f"  {len(emails)} email(s) today")

    print("Fetching calendar events...")
    events = fetch_events()
    print(f"  {len(events)} event(s) today")

    print("Fetching news...")
    news = fetch_news()
    print(f"  {len(news)} article(s) fetched")

    print("\nGenerating briefing with Claude...\n")
    briefing = generate_briefing(emails, events, news)

    separator = "=" * 60
    print(separator)
    print(briefing)
    print(separator)

    os.makedirs("output", exist_ok=True)
    output_path = f"output/briefing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_path, "w") as f:
        f.write(briefing)
    print(f"Saved to {output_path}")

    recipient = os.environ.get("RECIPIENT_EMAIL")
    if not recipient:
        raise RuntimeError("RECIPIENT_EMAIL environment variable is required")
    send_briefing(briefing, emails, news, recipient)


if __name__ == "__main__":
    run()
