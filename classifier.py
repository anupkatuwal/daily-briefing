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
      "category": "URGENT" | "Finance" | "College/Academic" | "Work/Freelance" | "Personal" | "Promotions",
      "importance": 1-5,
      "action_items": [ {"task": str, "deadline": str_or_empty} ],
      "decisions_needed": [ str ],
      "one_line": str
    }
  ],
  "calendar_summary": str,
  "news_bullets": [ str, str, str, str, str ],
  "top_priorities": [ str ]   // 3-6 items, anything due today or marked URGENT
}

Rules:
- Skip Promotions entirely (do not include them in the emails array).
- importance 5 = act today; 1 = FYI.
- action_items.deadline empty string if none.
- top_priorities are short imperative phrases like "Pay Chase by Dec 12" or "Review Q4 report (Sarah)".
- news_bullets: tight one-line summaries (no links). Prioritize Nepal and US stories first, then world.
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
