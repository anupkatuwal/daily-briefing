"""Sample data for --dry-run."""

SAMPLE_EMAILS = [
    {"source": "gmail", "from": "Chase Bank <no-reply@chase.com>", "subject": "Your statement is ready",
     "date": "today", "snippet": "Your November statement is now available. Minimum payment $245 due Dec 12."},
    {"source": "gmail", "from": "Prof. Martinez <martinez@uni.edu>", "subject": "CS401 final project deadline",
     "date": "today", "snippet": "Reminder: final project submission due Friday by 11:59pm. Late submissions lose 10%."},
    {"source": "gmail", "from": "Upwork <noreply@upwork.com>", "subject": "New invitation: Python automation gig",
     "date": "today", "snippet": "A client invited you to apply for a $2k Python scraping project. Respond within 48 hours."},
    {"source": "gmail", "from": "Mom <mom@example.com>", "subject": "Dinner Sunday?",
     "date": "today", "snippet": "Are you free Sunday for dinner? Let me know."},
    {"source": "outlook", "from": "Sarah Chen <sarah@acmecorp.com>", "subject": "URGENT: Q4 report review needed today",
     "date": "today", "snippet": "Need your sign-off on the Q4 report before EOD. Blocking the board pack."},
    {"source": "outlook", "from": "GitHub <noreply@github.com>", "subject": "Security alert: dependabot",
     "date": "today", "snippet": "A vulnerable dependency was detected in your repo daily-briefing."},
]

SAMPLE_CALENDAR = [
    {"title": "Standup", "start": "2026-06-06T09:30:00", "end": "2026-06-06T09:45:00", "location": "Zoom", "description": ""},
    {"title": "CS401 lecture", "start": "2026-06-06T11:00:00", "end": "2026-06-06T12:30:00", "location": "Hall B", "description": ""},
    {"title": "Client call — Acme", "start": "2026-06-06T15:00:00", "end": "2026-06-06T15:30:00", "location": "Google Meet", "description": "Discuss Q4 report"},
]

SAMPLE_NEWS = [
    {"title": "Markets rally on Fed signal", "link": "https://example.com/1", "summary": "Stocks rose after the Fed hinted at a pause.", "source": "Sample News"},
    {"title": "Major tech acquisition announced", "link": "https://example.com/2", "summary": "BigCo to acquire StartupX for $4B.", "source": "Sample News"},
    {"title": "Storm warning issued for east coast", "link": "https://example.com/3", "summary": "Heavy rain expected through weekend.", "source": "Sample News"},
    {"title": "New AI model released", "link": "https://example.com/4", "summary": "Lab unveils next-gen model with longer context.", "source": "Sample News"},
    {"title": "Election results in", "link": "https://example.com/5", "summary": "Local elections concluded with surprise upsets.", "source": "Sample News"},
]
