import os
from datetime import datetime
import anthropic
from dotenv import load_dotenv

load_dotenv()


def generate_briefing(emails: list[dict], events: list[dict], news: list[dict]) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    email_block = "\n".join(
        f"- From: {e['from']}\n  Subject: {e['subject']}\n  Preview: {e['snippet']}"
        for e in emails
    ) or "No emails today."

    event_block = "\n".join(
        f"- {e['title']} at {e['start']}" + (f" ({e['location']})" if e["location"] else "")
        for e in events
    ) or "No events today."

    news_block = "\n".join(
        f"- [{e['source']}] {e['title']}: {e['summary']}" for e in news
    ) or "No news available."

    today = datetime.now().strftime("%A, %B %d, %Y")
    prompt = f"""You are an executive assistant preparing a daily briefing for {today}.

## Unread Emails — Inbox & Important ({len(emails)} total)
{email_block}

## Calendar Events Today
{event_block}

## Top News Headlines
{news_block}

Write a daily briefing in this exact format:

**Good Morning Summary**
2-3 sentence overview of the day.

**All Unread Emails**
List every email with: sender, subject, and one-line summary of the snippet.
Group them: first Urgent/Needs Reply, then FYI/Informational, then Promotions/Marketing.

**Today's Schedule**
List events with times in order.

**News Digest**
3-5 bullet points of the most important stories.

**Action Items**
Concrete next steps based on emails and calendar."""

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
