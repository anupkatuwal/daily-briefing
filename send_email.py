"""Send the daily briefing as an HTML email via Gmail SMTP."""
import html as _html
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()


def send_briefing(markdown_text: str, date_str: str) -> None:
    smtp_user = os.environ.get("GMAIL_SMTP_USER", "")
    smtp_password = os.environ.get("GMAIL_SMTP_PASSWORD", "")
    to_email = os.environ.get("BRIEFING_TO_EMAIL", smtp_user)

    if not smtp_user or not smtp_password:
        print("[skip] GMAIL_SMTP_USER / GMAIL_SMTP_PASSWORD not set — skipping email")
        return

    try:
        import markdown as md
        html_body = md.markdown(markdown_text, extensions=["tables", "fenced_code"])
    except ImportError:
        html_body = "<pre>" + _html.escape(markdown_text) + "</pre>"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Daily Briefing — {date_str}"
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(markdown_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(smtp_user, smtp_password)
        smtp.sendmail(smtp_user, to_email, msg.as_string())

    print(f"✓ Email sent to {to_email}")
