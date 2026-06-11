import os
import sys
from pathlib import Path
from googleapiclient.discovery import build
from .google_auth import get_creds, PROJECT_ROOT

# Hard cap to keep Claude prompt size reasonable; covers virtually all real inboxes
MAX_EMAILS = 200


def gmail_accounts() -> list[dict]:
    """Accounts to aggregate, from GMAIL_ACCOUNTS env var.

    Format: comma-separated "Name:path/to/token.json" pairs, e.g.
      GMAIL_ACCOUNTS=Primary:token.json,Secondary:tokens/token_secondary.json
    Defaults to the single primary account (token.json).
    """
    raw = os.environ.get("GMAIL_ACCOUNTS", "").strip()
    if not raw:
        return [{"name": "Primary", "token_path": "token.json"}]
    accounts = []
    for entry in raw.split(","):
        name, _, token_path = entry.strip().partition(":")
        if name and token_path:
            accounts.append({"name": name, "token_path": token_path})
    return accounts


def fetch_unread_emails(service, account_name: str, token_path: str,
                        max_results: int = MAX_EMAILS) -> list[dict]:
    """Fetch unread emails from a Gmail service instance."""
    messages = []
    page_token = None
    query = "is:unread (in:inbox OR in:important)"

    while len(messages) < max_results:
        kwargs = {"userId": "me", "q": query, "maxResults": min(500, max_results - len(messages))}
        if page_token:
            kwargs["pageToken"] = page_token
        result = service.users().messages().list(**kwargs).execute()
        messages.extend(result.get("messages", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    emails = []
    for msg in messages:
        detail = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["Subject", "From", "Date", "Message-ID"],
        ).execute()
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        emails.append(
            {
                "id": msg["id"],
                "thread_id": detail.get("threadId", msg["id"]),
                "message_id": headers.get("Message-ID", ""),
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "snippet": detail.get("snippet", ""),
                "account": account_name,
                "token_path": token_path,
            }
        )
    return emails


def fetch_emails() -> list[dict]:
    """Aggregate unread emails across all configured Gmail accounts.

    An account whose token is missing or broken is skipped with a warning so
    one bad account can't kill the whole briefing.
    """
    emails = []
    for acct in gmail_accounts():
        token_path = Path(acct["token_path"])
        resolved = token_path if token_path.is_absolute() else PROJECT_ROOT / token_path
        if not resolved.exists():
            print(f"[warn] {acct['name']}: token not found at {acct['token_path']}, skipping",
                  file=sys.stderr)
            continue
        try:
            creds = get_creds(acct["token_path"])
            service = build("gmail", "v1", credentials=creds)
            batch = fetch_unread_emails(service, acct["name"], acct["token_path"])
            print(f"  {acct['name']}: {len(batch)} email(s)")
            emails.extend(batch)
        except Exception as e:
            print(f"[warn] {acct['name']}: fetch failed ({e}), skipping", file=sys.stderr)
    return emails
