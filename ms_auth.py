"""Microsoft Graph auth via MSAL device code flow.

Supports multiple Microsoft accounts (work, school, personal Outlook/Hotmail).

Set MS_ACCOUNTS in .env:
    MS_ACCOUNTS=work@company.com,me@outlook.com,me@hotmail.com

Each account gets its own token cache: ms_token_cache_<email>.json.
First run for each account prints a URL + code to paste in browser.
Subsequent runs refresh silently from the cached token.

IMPORTANT: For personal Outlook/Hotmail accounts your Azure app registration
must support "Personal Microsoft accounts". Set MS_TENANT_ID=common and update
the Supported account types in portal.azure.com (see README for steps).
"""
import os
import re
import sys
import json
import atexit
from pathlib import Path

import msal
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get("MS_CLIENT_ID")
TENANT_ID = os.environ.get("MS_TENANT_ID", "common")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["Mail.Read", "Calendars.Read", "User.Read"]
HERE = Path(__file__).parent


def ms_accounts() -> list[str]:
    """Configured Microsoft account emails, or [""] for the legacy single account."""
    raw = os.environ.get("MS_ACCOUNTS", "")
    accounts = [a.strip() for a in raw.split(",") if a.strip()]
    return accounts or [""]


def _cache_path(account: str) -> Path:
    if not account:
        return HERE / "ms_token_cache.json"
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", account)
    return HERE / f"ms_token_cache_{safe}.json"


def _load_cache(account: str) -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    path = _cache_path(account)
    if path.exists():
        cache.deserialize(path.read_text())
    atexit.register(lambda: path.write_text(cache.serialize()) if cache.has_state_changed else None)
    return cache


def get_access_token(account: str = "") -> str:
    if not CLIENT_ID:
        raise RuntimeError("MS_CLIENT_ID not set in .env — register an app at portal.azure.com first.")

    cache = _load_cache(account)
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)

    # Try silent refresh — filter to the specific account when one is given.
    cached_accounts = app.get_accounts(username=account if account else None)
    if cached_accounts:
        result = app.acquire_token_silent(SCOPES, account=cached_accounts[0])
        if result and "access_token" in result:
            return result["access_token"]

    # Device code flow — login_hint is not supported by all MSAL versions, omit it.
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"Failed to start device flow: {json.dumps(flow, indent=2)}")

    label = account or "Microsoft account"
    print(f"\n[Outlook] Sign in for {label}:")
    print(flow["message"] + "\n", flush=True)

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise RuntimeError(f"Auth failed for {label}: {result.get('error_description', result)}")
    return result["access_token"]


if __name__ == "__main__":
    for acct in ms_accounts():
        token = get_access_token(acct)
        print(f"OK — {acct or 'default'} token len={len(token)}")
