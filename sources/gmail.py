from googleapiclient.discovery import build
from .google_auth import get_creds

# Hard cap to keep Claude prompt size reasonable; covers virtually all real inboxes
MAX_EMAILS = 200


def fetch_emails() -> list[dict]:
    creds = get_creds()
    service = build("gmail", "v1", credentials=creds)

    messages = []
    page_token = None
    query = "is:unread (in:inbox OR in:important)"

    while len(messages) < MAX_EMAILS:
        kwargs = {"userId": "me", "q": query, "maxResults": min(500, MAX_EMAILS - len(messages))}
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
            metadataHeaders=["Subject", "From", "Date"],
        ).execute()
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        emails.append(
            {
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "snippet": detail.get("snippet", ""),
            }
        )
    return emails
