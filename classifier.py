"""Send everything to Gemini in one prompt, get structured JSON back."""
import json
import os
import re
import sys
import time

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Override with the GEMINI_MODEL env var if Google renames or retires this one.
# The extras below are tried in order if a model is rejected or overloaded, so
# neither a model rename nor a demand spike silently kills the morning briefing.
MODEL = os.environ.get("GEMINI_MODEL") or "gemini-3.6-flash"
FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-2.5-flash"]

# Attempts per model before moving to the next one, and the backoff between them.
ATTEMPTS_PER_MODEL = 3
BACKOFF_SECONDS = [5, 15]


def _is_retryable(err: Exception) -> bool:
    """Transient server-side problems: worth waiting and asking again."""
    text = str(err)
    return any(
        marker in text
        for marker in ("503", "UNAVAILABLE", "high demand", "overloaded",
                       "429", "RESOURCE_EXHAUSTED", "500", "INTERNAL")
    )


def _is_missing_model(err: Exception) -> bool:
    """This model id does not exist for us: no point retrying it."""
    text = str(err)
    return "NOT_FOUND" in text or "404" in text or "not found" in text.lower()

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
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    payload = {
        "emails": emails,
        "calendar": calendar,
        "news": news,
    }

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM,
        response_mime_type="application/json",
        max_output_tokens=8192,
        temperature=0.2,
    )
    contents = "Here is today's raw data. Produce the JSON.\n\n" + json.dumps(payload, indent=2)

    last_error = None
    for model in [MODEL, *(m for m in FALLBACK_MODELS if m != MODEL)]:
        for attempt in range(ATTEMPTS_PER_MODEL):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
            except Exception as e:
                last_error = e
                if _is_missing_model(e):
                    print(f"[warn] model {model} unavailable, trying next", file=sys.stderr)
                    break
                if _is_retryable(e) and attempt < ATTEMPTS_PER_MODEL - 1:
                    wait = BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)]
                    print(f"[warn] {model} busy ({e}); retrying in {wait}s", file=sys.stderr)
                    time.sleep(wait)
                    continue
                if _is_retryable(e):
                    print(f"[warn] {model} still busy, trying next model", file=sys.stderr)
                    break
                raise
            else:
                if model != MODEL:
                    print(f"[warn] fell back to model {model}", file=sys.stderr)
                return _parse(resp.text)

    raise RuntimeError(f"No usable Gemini model. Last error: {last_error}")


def _parse(text: str) -> dict:
    text = (text or "").strip()
    # Strip code fences if the model added them anyway
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)
