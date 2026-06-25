# Daily Briefing

Sends a daily briefing email at **10:00 AM Nepal Time (04:15 UTC)** with unread Gmail
across one or more accounts, today's calendar, and news headlines, summarized by Claude.
Runs on GitHub Actions ([.github/workflows/daily-briefing.yml](.github/workflows/daily-briefing.yml));
replies to the briefing are processed every 30 minutes by
[process_replies.yml](.github/workflows/process_replies.yml).

## Scheduling

GitHub fires scheduled workflows late (hours, on this repo), so the briefing is queued
early at 01:45 UTC and a wait step holds the run until exactly 04:15 UTC
(= 10:00 AM Nepal Time, UTC+5:45) before sending.

## Setup

1. `python3 -m venv venv && ./venv/bin/pip install -r requirements.txt`
2. Copy a Google OAuth client (Desktop type) JSON and set `GOOGLE_CREDENTIALS_PATH` in `.env`.
3. Set `ANTHROPIC_API_KEY`, `RECIPIENT_EMAIL`, and `NEWS_RSS_FEEDS` in `.env`.
4. Authorize the primary account (opens a browser):

   ```bash
   python3 -m sources.google_auth tokens/token_primary.json
   ```

5. Run manually: `python3 briefing.py`

## Multiple Gmail accounts

Unread email is aggregated across every account listed in `GMAIL_ACCOUNTS`
(comma-separated `Name:token_path` pairs). Each email in the briefing is tagged with
the account it came from, and reply/delete actions are routed back to that account.

To add an account:

1. Run the OAuth flow for the new account (sign in as that account in the browser;
   it must be a test user on the OAuth app):

   ```bash
   python3 -m sources.google_auth tokens/token_<accountname>.json
   ```

2. Save the token as `tokens/token_<accountname>.json` (the command above does this).
3. Add the entry to `GMAIL_ACCOUNTS` in `.env`:

   ```bash
   GMAIL_ACCOUNTS=Primary:tokens/token_primary.json,Work:tokens/token_work.json
   ```

Accounts whose token file is missing or broken are skipped with a warning, so one bad
account never blocks the briefing. `tokens/` is gitignored — never commit token files.

### On GitHub Actions

The workflows rebuild tokens from repository secrets:

| Secret | Written to |
|---|---|
| `GOOGLE_TOKEN_JSON` | `tokens/token_primary.json` |
| `GOOGLE_TOKEN_SECONDARY_JSON` (optional) | `tokens/token_secondary.json` |

To add the secondary account in CI, paste the contents of its local token file into the
`GOOGLE_TOKEN_SECONDARY_JSON` secret. For more than two accounts, add another secret
write step and extend the `GMAIL_ACCOUNTS` env var in both workflow files.

## 🔗 Portfolio

Featured on my portfolio: **[https://anup-katuwal.com.np/projects/daily-briefing](https://anup-katuwal.com.np/projects/daily-briefing)**  
More of my work → [anup-katuwal.com.np](https://anup-katuwal.com.np)
