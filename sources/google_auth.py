import os
import sys
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

PROJECT_ROOT = Path(__file__).parent.parent
TOKEN_PATH = PROJECT_ROOT / "token.json"


def get_creds(token_path: Path | str = TOKEN_PATH) -> Credentials:
    """Return credentials for one Google account, cached at token_path."""
    token_path = Path(token_path)
    if not token_path.is_absolute():
        token_path = PROJECT_ROOT / token_path
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif token_path.exists():
            # Token exists but scopes changed — delete and re-auth interactively
            raise RuntimeError(
                f"Token scopes changed for {token_path.name}. "
                f"Run 'python3 -m sources.google_auth {token_path}' once to re-authorize."
            )
        else:
            # No token at all — must be run interactively
            if not sys.stdout.isatty():
                raise RuntimeError(
                    f"No OAuth token at {token_path}. "
                    f"Run 'python3 -m sources.google_auth {token_path}' once to authorize."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                os.environ["GOOGLE_CREDENTIALS_PATH"], SCOPES
            )
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())
    return creds


if __name__ == "__main__":
    # Authorize an account interactively: python3 -m sources.google_auth tokens/token_secondary.json
    path = sys.argv[1] if len(sys.argv) > 1 else str(TOKEN_PATH)
    get_creds(path)
    print(f"Token saved to {path}")
