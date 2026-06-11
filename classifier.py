import os
from datetime import datetime
import anthropic
from dotenv import load_dotenv

load_dotenv()


def generate_briefing(emails: list[dict], events: list[dict], news: list[dict]) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    email_block = "\n".join(
        f"- Account: {e.get('account', 'Primary')}\n  From: {e['from']}\n"
        f"  Subject: {e['subject']}\n  Preview: {e['snippet']}"
        for e in emails
    ) or "No unread emails."

    event_block = "\n".join(
        f"- {e['title']} at {e['start']}" + (f" ({e['location']})" if e["location"] else "")
        for e in events
    ) or "No events today."

    news_block = "\n".join(
        f"- [{e['source']}] {e['title']}\n  Content: {e['summary']}" for e in news
    ) or "No news available."

    today = datetime.now().strftime("%A, %B %d, %Y")
    prompt = f"""You are an executive assistant preparing a daily briefing for {today}.

## Unread Emails ({len(emails)} total)
{email_block}

## Calendar Events Today
{event_block}

## News Articles
{news_block}

Write a briefing in exactly this format:

**Good Morning Summary**
2-3 sentences covering the overall shape of the day: inbox load, schedule, and top news theme.

**Email Triage**
List every email. For each: one line with sender name, subject, one-sentence summary, and label it [URGENT], [REPLY NEEDED], [FYI], or [MARKETING].

**Today's Schedule**
List events with times. If none, say so.

**News Digest**
For each news story write: a bold headline, then 3-4 sentences explaining what happened, why it matters, and any key context. Cover all stories provided.

**Action Items**
Numbered list of concrete next steps based on emails and calendar only."""

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
