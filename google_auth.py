"""Google OAuth for Gmail (readonly) + Calendar (readonly).

Supports multiple Gmail accounts. Set GMAIL_ACCOUNTS in .env to a
comma-separated list of addresses, e.g.

    GMAIL_ACCOUNTS=me@gmail.com,work@gmail.com

Each account gets its own cached token file: google_token_<email>.json.
First run for each account opens a browser to sign in to that account.

If GMAIL_ACCOUNTS is empty, falls back to a single default account
cached in google_token.json (legacy behaviour).
"""
import os
import re
import stat
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]
HERE = Path(__file__).parent
DEFAULT_TOKEN_PATH = HERE / "google_token.json"
CREDS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH", "")


def gmail_accounts() -> list[str]:
    """Configured Gmail addresses, or [""] for the legacy single account."""
    raw = os.environ.get("GMAIL_ACCOUNTS", "")
    accounts = [a.strip() for a in raw.split(",") if a.strip()]
    return accounts or [""]


def _token_path(account: str) -> Path:
    """Per-account token file; legacy path when account is empty."""
    if not account:
        return DEFAULT_TOKEN_PATH
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", account)
    return HERE / f"google_token_{safe}.json"


def get_credentials(account: str = "") -> Credentials:
    token_path = _token_path(account)
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json())
        token_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        return creds
    if not CREDS_PATH or not Path(CREDS_PATH).exists():
        raise FileNotFoundError(
            f"GOOGLE_CREDENTIALS_PATH not found: {CREDS_PATH!r}. "
            "Download an OAuth client (Desktop) from console.cloud.google.com."
        )
    flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
    label = account or "your Google account"
    print(f"\n  >>> Sign-in required for: {label}", flush=True)
    print(f"  >>> Opening browser... (if nothing opens, copy the URL printed below)", flush=True)
    # login_hint nudges Google's account picker toward the intended address.
    kwargs = {"login_hint": account, "open_browser": True} if account else {"open_browser": True}
    creds = flow.run_local_server(port=0, **kwargs)
    print(f"  >>> Sign-in complete for: {label}", flush=True)
    token_path.write_text(creds.to_json())
    token_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return creds


def gmail_service(account: str = ""):
    return build("gmail", "v1", credentials=get_credentials(account), cache_discovery=False)


def calendar_service(account: str = ""):
    return build("calendar", "v3", credentials=get_credentials(account), cache_discovery=False)
