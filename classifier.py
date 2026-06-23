"""Send everything to Claude in one prompt, get structured JSON back."""
import json
import os
import re

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"

SYSTEM = """You are a personal daily-briefing assistant. You receive raw email, calendar, and news data and produce a single JSON object that powers a Markdown briefing.

Output ONLY valid JSON. No prose, no markdown fences. Schema:

{
  "emails": [
    {
      "from": str,
      "subject": str,
      "source": "gmail" | "outlook",
      "account": str,   // the receiving inbox, copied verbatim from the input email's "account" field
      "category": "URGENT" | "Finance" | "College/Academic" | "Work/Freelance" | "Personal" | "Promotions",
      "importance": 1-5,
      "action_items": [ {"task": str, "deadline": str_or_empty} ],
      "decisions_needed": [ str ],
      "one_line": str
    }
  ],
  "calendar_summary": str,
  "news_by_category": {
    "Top Headlines": [ str ],
    "US": [ str ],
    "World": [ str ],
    "Nepal": [ str ],
    "Technology": [ str ],
    "Entertainment": [ str ]
  },
  "top_priorities": [ str ]   // 3-6 items, anything due today or marked URGENT
}

Rules:
- Always copy the "account" field from each input email into your output unchanged, so the reader knows which inbox (Gmail address / Outlook / Hotmail) received it.
- Skip Promotions entirely (do not include them in the emails array).
- importance 5 = act today; 1 = FYI.
- action_items.deadline empty string if none.
- top_priorities are short imperative phrases like "Pay Chase by Dec 12" or "Review Q4 report (Sarah)".
- news_by_category: group the input news by its "category" field. For each category give 3-4 tight one-line summaries (no links, no source names). Keep the same category keys as the input. Drop a category only if it has no news.
"""


def classify(emails: list[dict], calendar: list[dict], news: list[dict]) -> dict:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    payload = {
        "emails": emails,
        "calendar": calendar,
        "news": news,
    }

    msg = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": "Here is today's raw data. Produce the JSON.\n\n" + json.dumps(payload, indent=2),
        }],
    )
    text = msg.content[0].text.strip()
    # Strip code fences if the model added them anyway
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)
