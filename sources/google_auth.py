import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
]

TOKEN_PATH = Path(__file__).parent.parent / "token.json"


def get_creds() -> Credentials:
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif TOKEN_PATH.exists():
            # Token exists but scopes changed — delete and re-auth interactively
            raise RuntimeError(
                "Token scopes changed. Run 'python3 briefing.py' in a terminal once to re-authorize."
            )
        else:
            # No token at all — must be run interactively
            import sys
            if not sys.stdout.isatty():
                raise RuntimeError(
                    "No OAuth token found. Run 'python3 briefing.py' in a terminal once to authorize."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                os.environ["GOOGLE_CREDENTIALS_PATH"], SCOPES
            )
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds
