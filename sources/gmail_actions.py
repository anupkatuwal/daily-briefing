import base64
import re
from datetime import datetime
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from .google_auth import get_creds


def _service(token_path=None):
    # Default (no token_path) is the primary account, which sends/receives the briefing
    creds = get_creds(token_path) if token_path else get_creds()
    return build("gmail", "v1", credentials=creds)


def find_briefing_replies() -> list[dict]:
    """Find unread replies to today's briefing email sent by the user."""
    svc = _service()
    today = datetime.now().strftime("%Y/%m/%d")
    result = svc.users().messages().list(
        userId="me",
        q=f'subject:"Re: Daily Briefing" is:unread after:{today}',
        maxResults=10,
    ).execute()

    replies = []
    for msg in result.get("messages", []):
        detail = svc.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        body = _extract_plain_text(detail)
        if body:
            replies.append({"id": msg["id"], "body": body})
    return replies


def _extract_plain_text(message: dict) -> str:
    """Pull plain text from a Gmail message, stripping quoted reply lines."""
    def walk(part):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        for sub in part.get("parts", []):
            result = walk(sub)
            if result:
                return result
        return ""

    raw = walk(message.get("payload", {}))
    # Drop quoted lines (>) and Gmail footer separators
    lines = [l for l in raw.splitlines() if not l.startswith(">") and not l.startswith("On ")]
    return "\n".join(lines).strip()


def send_reply(target: dict, reply_text: str) -> None:
    """Send a reply to a specific email on behalf of the account that received it."""
    svc = _service(target.get("token_path"))
    addr = _addr(target["from"])
    subject = target["subject"]
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    msg = MIMEText(reply_text)
    msg["To"] = addr
    msg["Subject"] = subject
    if target.get("message_id"):
        msg["In-Reply-To"] = target["message_id"]
        msg["References"] = target["message_id"]

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    svc.users().messages().send(
        userId="me",
        body={"raw": raw, "threadId": target["thread_id"]},
    ).execute()
    print(f"Replied to {addr}")


def trash_message(message_id: str, token_path=None) -> None:
    _service(token_path).users().messages().trash(userId="me", id=message_id).execute()
    print(f"Trashed {message_id}")


def mark_read(message_id: str) -> None:
    _service().users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def send_confirmation(thread_id: str, text: str) -> None:
    """Send a confirmation reply in the same briefing thread."""
    svc = _service()
    msg = MIMEText(f"Done!\n\n{text}\n\n— Daily Briefing Assistant")
    msg["To"] = "me"
    msg["Subject"] = "Re: Daily Briefing — action completed"
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    svc.users().messages().send(
        userId="me", body={"raw": raw, "threadId": thread_id}
    ).execute()


def _addr(from_field: str) -> str:
    m = re.search(r"<(.+?)>", from_field)
    return m.group(1) if m else from_field.strip()
