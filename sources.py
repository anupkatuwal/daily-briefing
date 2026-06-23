"""Fetch raw data from Gmail, Outlook, Calendar, RSS."""
import os
import base64
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr

import feedparser
import requests
from dotenv import load_dotenv

load_dotenv()


# ---------- Gmail ----------

def _fetch_gmail_one(account: str, max_results: int) -> list[dict]:
    """Last 24h of unread, non-promotional emails for a single account."""
    from google_auth import gmail_service
    svc = gmail_service(account)
    # Identify the inbox so multi-account briefings show which one each mail came from.
    label = account or svc.users().getProfile(userId="me").execute().get("emailAddress", "gmail")
    # Gmail's category filters skip Promotions and Social (newsletters mostly live there)
    query = "is:unread newer_than:1d -category:promotions -category:social"
    resp = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    out = []
    for m in resp.get("messages", []):
        msg = svc.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
        out.append({
            "source": "gmail",
            "account": label,
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
        })
    return out


def fetch_gmail(max_results: int = 50) -> list[dict]:
    """Last 24h of unread, non-promotional emails across all configured accounts."""
    from google_auth import gmail_accounts
    accounts = gmail_accounts()
    print(f"  Gmail accounts configured: {accounts}", flush=True)
    out = []
    for account in accounts:
        print(f"  Authenticating {account or 'default Gmail'}...", flush=True)
        try:
            msgs = _fetch_gmail_one(account, max_results)
            print(f"  {len(msgs)} emails from {account or 'default Gmail'}", flush=True)
            out.extend(msgs)
        except Exception as e:
            print(f"  [warn] gmail {account or 'default'} failed: {e}", flush=True)
    return out


# ---------- Outlook / Microsoft Graph ----------

def _fetch_outlook_one(account: str, max_results: int) -> list[dict]:
    from ms_auth import get_access_token
    token = get_access_token(account)
    since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    url = "https://graph.microsoft.com/v1.0/me/messages"
    params = {
        "$filter": f"isRead eq false and receivedDateTime ge {since}",
        "$select": "from,subject,receivedDateTime,bodyPreview",
        "$top": str(max_results),
        "$orderby": "receivedDateTime desc",
    }
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=30)
    r.raise_for_status()
    label = account or "outlook"
    out = []
    for m in r.json().get("value", []):
        sender = m.get("from", {}).get("emailAddress", {})
        out.append({
            "source": "outlook",
            "account": label,
            "from": f"{sender.get('name','')} <{sender.get('address','')}>".strip(),
            "subject": m.get("subject", "(no subject)"),
            "date": m.get("receivedDateTime", ""),
            "snippet": m.get("bodyPreview", "")[:300],
        })
    return out


def fetch_outlook(max_results: int = 50) -> list[dict]:
    """Last 24h of unread emails across all configured Microsoft accounts."""
    from ms_auth import ms_accounts
    out = []
    for account in ms_accounts():
        try:
            out.extend(_fetch_outlook_one(account, max_results))
        except Exception as e:
            print(f"[warn] outlook {account or 'default'} failed: {e}")
    return out


# ---------- Google Calendar ----------

def fetch_calendar() -> list[dict]:
    """Today's events, using the first configured Gmail account's credentials."""
    from google_auth import calendar_service, gmail_accounts
    primary = gmail_accounts()[0]
    svc = calendar_service(primary)
    now = datetime.now().astimezone()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    resp = svc.events().list(
        calendarId="primary",
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    out = []
    for e in resp.get("items", []):
        s = e["start"].get("dateTime") or e["start"].get("date", "")
        en = e["end"].get("dateTime") or e["end"].get("date", "")
        out.append({
            "title": e.get("summary", "(no title)"),
            "start": s,
            "end": en,
            "location": e.get("location", ""),
            "description": (e.get("description") or "")[:300],
        })
    return out


# ---------- RSS ----------

def fetch_news(top_n: int = 5) -> list[dict]:
    feeds = [f.strip() for f in os.environ.get("NEWS_RSS_FEEDS", "").split(",") if f.strip()]
    items: list[dict] = []
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:top_n]:
                items.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": (entry.get("summary", "") or "")[:300],
                    "source": parsed.feed.get("title", url),
                })
        except Exception as e:
            print(f"[warn] feed failed {url}: {e}")
    # Interleave so we get variety, then cap
    return items[:top_n * 2]
