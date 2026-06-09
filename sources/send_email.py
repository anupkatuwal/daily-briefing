import base64
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote
from googleapiclient.discovery import build
from .google_auth import get_creds

BTN = (
    "display:inline-block;padding:5px 12px;border-radius:4px;font-size:12px;"
    "text-decoration:none;font-weight:600;margin-right:6px;"
)
BTN_PRIMARY = BTN + "background:#1a1a2e;color:#fff;"
BTN_REPLY   = BTN + "background:#2e7d32;color:#fff;"
BTN_DELETE  = BTN + "background:#c62828;color:#fff;"


def _extract_email_addr(from_field: str) -> str:
    m = re.search(r"<(.+?)>", from_field)
    return m.group(1) if m else from_field.strip()


def _extract_sender_name(from_field: str) -> str:
    m = re.match(r'^"?([^"<]+)"?\s*<', from_field)
    if m:
        return m.group(1).strip()
    m = re.search(r"<(.+?)>", from_field)
    return m.group(1) if m else from_field


def _gmail_url(message_id: str) -> str:
    return f"https://mail.google.com/mail/u/0/#inbox/{message_id}"


def _reply_url(from_field: str, subject: str) -> str:
    addr = _extract_email_addr(from_field)
    subj = quote(f"Re: {subject}")
    return f"mailto:{addr}?subject={subj}"


def _email_cards_html(emails: list[dict]) -> str:
    if not emails:
        return "<p style='color:#666;'>No unread emails.</p>"
    cards = []
    for i, e in enumerate(emails, 1):
        name = _extract_sender_name(e["from"])
        gmail = _gmail_url(e["id"])
        reply = _reply_url(e["from"], e["subject"])
        snippet = e["snippet"][:160] + ("…" if len(e["snippet"]) > 160 else "")
        cards.append(f"""
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:14px 16px;margin:8px 0;">
  <div style="font-size:11px;color:#aaa;margin-bottom:2px;">EMAIL #{i}</div>
  <div style="font-size:13px;color:#555;margin-bottom:2px;">{name}</div>
  <div style="font-weight:600;margin-bottom:6px;">{e['subject']}</div>
  <div style="font-size:13px;color:#444;margin-bottom:10px;">{snippet}</div>
  <a href="{gmail}" style="{BTN_PRIMARY}">View in Gmail</a>
  <a href="{reply}" style="{BTN_REPLY}">Reply</a>
  <a href="{gmail}" style="{BTN_DELETE}">Delete</a>
</div>""")
    return "\n".join(cards)


def _news_cards_html(news: list[dict]) -> str:
    if not news:
        return "<p style='color:#666;'>No news available.</p>"
    cards = []
    for a in news:
        summary = a["summary"][:600] + ("…" if len(a["summary"]) > 600 else "")
        cards.append(f"""
<div style="border-left:3px solid #1a1a2e;padding:12px 16px;margin:10px 0;background:#fafafa;border-radius:0 6px 6px 0;">
  <div style="font-weight:700;font-size:15px;margin-bottom:4px;">
    <a href="{a['link']}" style="color:#1a1a2e;text-decoration:none;">{a['title']}</a>
  </div>
  <div style="font-size:11px;color:#888;margin-bottom:8px;">{a['source']}</div>
  <div style="font-size:13px;color:#333;line-height:1.6;">{summary}</div>
  <a href="{a['link']}" style="font-size:12px;color:#1a1a2e;font-weight:600;margin-top:8px;display:inline-block;">
    Read more &rarr;
  </a>
</div>""")
    return "\n".join(cards)


def _md_to_html(text: str) -> str:
    lines = text.split("\n")
    html_lines = []
    in_list = False
    for line in lines:
        if re.match(r"^\*\*[^*]+\*\*$", line.strip()):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            heading = re.sub(r"\*\*(.+?)\*\*", r"\1", line.strip())
            html_lines.append(
                f'<h3 style="color:#1a1a2e;margin-top:28px;margin-bottom:8px;'
                f'border-bottom:1px solid #eee;padding-bottom:6px;">{heading}</h3>'
            )
        elif re.match(r"^[-\d][\.\s]", line.strip()):
            if not in_list:
                html_lines.append('<ul style="padding-left:20px;margin:4px 0;">')
                in_list = True
            item = re.sub(r"^[-\d]+[.\s]+", "", line.strip())
            item = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item)
            item = re.sub(r"\[(\w+)\]", r'<span style="font-size:11px;background:#eee;'
                          r'padding:1px 5px;border-radius:3px;font-weight:700;">\1</span>', item)
            html_lines.append(f"<li style='margin:6px 0;'>{item}</li>")
        elif line.strip() == "":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<br>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            para = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            html_lines.append(f"<p style='margin:4px 0;'>{para}</p>")
    if in_list:
        html_lines.append("</ul>")
    return "\n".join(html_lines)


def send_briefing(briefing_text: str, emails: list[dict], news: list[dict], to: str) -> None:
    creds = get_creds()
    service = build("gmail", "v1", credentials=creds)

    today = datetime.now().strftime("%A, %B %d, %Y")
    subject = f"Daily Briefing — {today}"

    email_cards = _email_cards_html(emails)
    news_cards = _news_cards_html(news)

    html_body = f"""<html>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
             max-width:700px;margin:0 auto;padding:24px;color:#222;line-height:1.6;">
  <h2 style="color:#1a1a2e;border-bottom:3px solid #1a1a2e;padding-bottom:12px;">
    Daily Briefing &mdash; {today}
  </h2>

  {_md_to_html(briefing_text)}

  <h3 style="color:#1a1a2e;margin-top:28px;margin-bottom:8px;
             border-bottom:1px solid #eee;padding-bottom:6px;">
    Email Quick Actions
  </h3>
  <div style="background:#f0f4ff;border-radius:8px;padding:12px 16px;margin-bottom:12px;font-size:13px;">
    <strong>Reply to this email</strong> with instructions and Claude will act on them. Examples:<br>
    &bull; <em>Reply to email 2 saying: Thanks, I'll confirm by Friday</em><br>
    &bull; <em>Delete email 3</em><br>
    &bull; <em>Reply to the GitHub email saying: Will fix this today</em>
  </div>
  {email_cards}

  <h3 style="color:#1a1a2e;margin-top:28px;margin-bottom:8px;
             border-bottom:1px solid #eee;padding-bottom:6px;">
    Full News
  </h3>
  {news_cards}

  <p style="margin-top:36px;color:#aaa;font-size:11px;border-top:1px solid #eee;padding-top:12px;">
    Generated by Daily Briefing &middot; Powered by Claude
  </p>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "me"
    msg["To"] = to
    msg.attach(MIMEText(briefing_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"Emailed to {to}")
