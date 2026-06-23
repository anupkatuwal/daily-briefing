from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from .google_auth import get_creds


def fetch_events() -> list[dict]:
    creds = get_creds()
    service = build("calendar", "v3", credentials=creds)

    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    result = service.events().list(
        calendarId="primary",
        timeMin=day_start.isoformat(),
        timeMax=day_end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for item in result.get("items", []):
        start = item.get("start", {})
        events.append(
            {
                "title": item.get("summary", "Untitled"),
                "start": start.get("dateTime", start.get("date", "")),
                "location": item.get("location", ""),
                "description": (item.get("description", "") or "")[:200],
            }
        )
    return events
