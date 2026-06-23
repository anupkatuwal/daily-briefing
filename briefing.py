"""Daily briefing — entry point.

Usage:
  python briefing.py              # live
  python briefing.py --dry-run    # sample data, still hits Claude
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def safe(fn, label: str, default):
    try:
        return fn()
    except Exception as e:
        print(f"[warn] {label} failed: {e}", file=sys.stderr)
        return default


def fmt_calendar(cal: list[dict]) -> str:
    if not cal:
        return "_No events today._"
    lines = []
    for e in cal:
        start = e.get("start", "")
        # Trim ISO to HH:MM
        t = start[11:16] if "T" in start else "all-day"
        loc = f" — _{e['location']}_" if e.get("location") else ""
        lines.append(f"- **{t}** {e.get('title','(untitled)')}{loc}")
    return "\n".join(lines)


def fmt_emails(emails: list[dict], category: str) -> str:
    rows = [e for e in emails if e.get("category") == category]
    if not rows:
        return "_Nothing._"
    rows.sort(key=lambda e: -e.get("importance", 0))
    out = []
    for e in rows:
        stars = "★" * e.get("importance", 1)
        line = f"- **{e.get('subject','(no subject)')}** — _{e.get('from','')}_ {stars}\n  {e.get('one_line','')}"
        for ai in e.get("action_items", []) or []:
            dl = f" _(due {ai['deadline']})_" if ai.get("deadline") else ""
            line += f"\n  - ☐ {ai['task']}{dl}"
        out.append(line)
    return "\n".join(out)


def fmt_priorities(p: list[str]) -> str:
    if not p:
        return "_Nothing urgent._"
    return "\n".join(f"- {item}" for item in p)


def fmt_news(bullets: list[str]) -> str:
    if not bullets:
        return "_No headlines._"
    return "\n".join(f"- {b}" for b in bullets)


def build_markdown(result: dict, date_str: str) -> str:
    emails = result.get("emails", [])
    cal_summary = result.get("calendar_summary", "")
    other = [e for e in emails if e.get("category") not in {
        "URGENT", "Finance", "College/Academic", "Work/Freelance", "Promotions"
    }]
    other_md = "_Nothing._" if not other else "\n".join(
        f"- _{e.get('from','')}_ — {e.get('subject','')}" for e in other
    )
    cal_summary_md = f"\n_{cal_summary}_" if cal_summary else ""

    return f"""# Daily Briefing — {date_str}

## 🔴 TODAY'S PRIORITY
{fmt_priorities(result.get("top_priorities", []))}

## 📅 CALENDAR
{result.get("_calendar_md", "_(no calendar)_")}
{cal_summary_md}

## 💰 FINANCE
{fmt_emails(emails, "Finance")}

## 🎓 COLLEGE
{fmt_emails(emails, "College/Academic")}

## 💼 WORK / FREELANCE
{fmt_emails(emails, "Work/Freelance")}

## 📰 NEWS
{fmt_news(result.get("news_bullets", []))}

## 📥 EVERYTHING ELSE
{other_md}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="use sample data instead of live APIs")
    args = ap.parse_args()

    if args.dry_run:
        from sample_data import SAMPLE_EMAILS, SAMPLE_CALENDAR, SAMPLE_NEWS
        emails, calendar, news = SAMPLE_EMAILS, SAMPLE_CALENDAR, SAMPLE_NEWS
    else:
        from sources import fetch_gmail, fetch_outlook, fetch_calendar, fetch_news
        print("Fetching Gmail...")
        gmail = safe(fetch_gmail, "gmail", [])
        print(f"  {len(gmail)} emails")
        print("Fetching Outlook...")
        outlook = safe(fetch_outlook, "outlook", [])
        print(f"  {len(outlook)} emails")
        print("Fetching Calendar...")
        calendar = safe(fetch_calendar, "calendar", [])
        print(f"  {len(calendar)} events")
        print("Fetching News...")
        news = safe(fetch_news, "news", [])
        print(f"  {len(news)} headlines")
        emails = gmail + outlook

    print("Classifying with Claude...")
    from classifier import classify
    result = classify(emails, calendar, news)

    # Build calendar markdown from raw events (model gives a freeform summary too)
    result["_calendar_md"] = fmt_calendar(calendar)

    date_str = datetime.now().strftime("%Y-%m-%d")
    out_path = Path(__file__).parent / "output" / f"briefing_{date_str}.md"
    out_path.parent.mkdir(exist_ok=True)
    briefing_md = build_markdown(result, date_str)
    out_path.write_text(briefing_md)
    print(f"\n✓ Wrote {out_path}")

    from send_email import send_briefing
    try:
        send_briefing(briefing_md, date_str)
    except Exception as e:
        print(f"[warn] email failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
