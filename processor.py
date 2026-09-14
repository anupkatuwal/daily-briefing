import json
import os
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

from sources.gmail import fetch_emails
from sources.gmail_actions import (
    find_briefing_replies,
    send_reply,
    trash_message,
    mark_read,
    send_confirmation,
)


def parse_instruction(client: genai.Client, instruction: str, emails: list[dict]) -> list[dict]:
    email_list = "\n".join(
        f"{i + 1}. [{e.get('account', 'Primary')}] From: {e['from']}  |  Subject: {e['subject']}"
        for i, e in enumerate(emails)
    )
    prompt = f"""The user has these unread emails (numbered):
{email_list}

The user sent this instruction:
\"\"\"{instruction}\"\"\"

Parse every action the user wants. Return ONLY a JSON array, no explanation:
[
  {{
    "type": "reply" | "delete" | "unknown",
    "email_number": <1-based integer matching the list above, or null>,
    "message": "<exact reply text if type is reply, else null>"
  }}
]

Match by email number, sender name, or subject keywords. If you cannot identify a target, set type to "unknown"."""

    response = client.models.generate_content(
        model=os.environ.get("GEMINI_MODEL") or "gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=2048,
            response_mime_type="application/json",
        ),
    )
    text = (response.text or "").strip()
    # Extract JSON array even if wrapped in markdown
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return []


def process():
    replies = find_briefing_replies()
    if not replies:
        print("No new instructions.")
        return

    emails = fetch_emails()
    if not emails:
        print("No emails to act on.")
        return

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    for reply in replies:
        print(f"Processing instruction: {reply['body'][:80]}")
        actions = parse_instruction(client, reply["body"], emails)
        confirmations = []

        for action in actions:
            idx = action.get("email_number")
            if not idx or not (1 <= idx <= len(emails)):
                confirmations.append(f"Could not identify target email for: {action}")
                continue

            target = emails[idx - 1]

            if action["type"] == "reply":
                msg = action.get("message") or ""
                if msg:
                    send_reply(target, msg)
                    confirmations.append(
                        f"Replied to email #{idx} ({target['subject']}) with:\n\"{msg}\""
                    )
                else:
                    confirmations.append(f"No reply message found for email #{idx}.")

            elif action["type"] == "delete":
                trash_message(target["id"], target.get("token_path"))
                confirmations.append(f"Deleted email #{idx}: {target['subject']}")

            else:
                confirmations.append(f"Unknown action for email #{idx}.")

        if confirmations:
            send_confirmation(reply["id"], "\n\n".join(confirmations))

        mark_read(reply["id"])


if __name__ == "__main__":
    process()
