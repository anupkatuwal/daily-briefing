# Daily Briefing — Project Guide

A personal daily briefing that reads your inboxes + calendar + news, summarizes
with Claude, and emails you a styled briefing every morning. Runs entirely on
GitHub Actions (no local machine needed).

## Architecture

| File | Role |
|------|------|
| `briefing.py` | Entry point. Orchestrates fetch → classify → render → email. |
| `sources.py` | Fetches Gmail, Outlook/Hotmail, Google Calendar, Google News RSS. |
| `classifier.py` | Sends everything to Claude, gets structured JSON back. |
| `google_auth.py` | Google OAuth (Gmail + Calendar), read-only scopes. |
| `ms_auth.py` | Microsoft Graph auth (Outlook/Hotmail), read-only scopes. |
| `send_email.py` | Renders the briefing as a styled HTML email via Gmail SMTP. |
| `.github/workflows/daily_briefing.yml` | Runs the briefing at 08:30 Nepal time daily. |
| `.github/workflows/keepalive.yml` | Weekly commit so GitHub never disables the schedule. |
| `.github/workflows/security_audit.yml` | Weekly CVE scan + compile check. |
| `.github/dependabot.yml` | Auto-opens PRs for dependency + Action updates. |

## Schedule & delivery

- **Runs:** 08:30 AM Nepal time (cron `45 2 * * *` UTC).
- **From:** katuwalanup@gmail.com (Gmail SMTP, app password).
- **To:** anup.katuwal2025@outlook.com (`BRIEFING_TO_EMAIL` secret).

## Accounts covered

- Gmail: katuwalanup@gmail.com, akatuwal1@cougars.ccis.edu, anup.202854@ncit.edu.np
- Microsoft: katuwalanup@hotmail.com, anup.katuwal2025@outlook.com

## Secrets (GitHub → Settings → Secrets → Actions)

`ANTHROPIC_API_KEY`, `GMAIL_ACCOUNTS`, `MS_CLIENT_ID`, `MS_ACCOUNTS`,
`GMAIL_SMTP_USER`, `GMAIL_SMTP_PASSWORD`, `BRIEFING_TO_EMAIL`,
`GOOGLE_TOKEN_*` (per Gmail account, base64), `MS_TOKEN_CACHE_*` (per MS account, base64).

## Security model

- All inbox OAuth scopes are **read-only** — the app cannot send/delete your mail.
- Tokens are gitignored and written with `600` (owner-only) permissions.
- No secrets are committed; verify with `git log -p | grep -i token`.
- SMTP uses TLS (port 465).

## The 60-day rule (already handled)

GitHub disables scheduled workflows after 60 days of no repo activity. The
`keepalive.yml` workflow makes a tiny commit every Monday, which resets that
timer indefinitely. Do not delete it.

---

## Maintenance prompt (paste into Claude Code periodically)

> Run a full health check on this daily-briefing project:
> 1. Run `pip-audit --desc` and report any vulnerable dependencies, separating
>    real app-runtime risks from build-only tooling (pip, setuptools).
> 2. Run `python -m compileall -q .` to confirm everything still compiles.
> 3. Check that all model IDs in `classifier.py` are current and supported.
> 4. Review any open Dependabot PRs — for each, summarize what changed and
>    whether it's safe to merge (breaking changes, changelog highlights).
> 5. Check the last 5 GitHub Actions runs of `daily_briefing.yml` for silent
>    failures (especially `[warn]` lines that don't fail the job — email send,
>    per-account auth, expired tokens).
> 6. Confirm `keepalive.yml` ran within the last 14 days.
> 7. Flag anything that could break soon: deprecated APIs, expiring tokens,
>    Python version EOL, RSS feeds returning empty.
> Fix what's safe to fix automatically, and list anything that needs my input.

## Common tasks

- **Add a news category:** edit `NEWS_FEEDS` in `sources.py`.
- **Change send time:** edit the cron in `daily_briefing.yml` (UTC = NPT − 5:45).
- **Change recipient:** update the `BRIEFING_TO_EMAIL` GitHub secret.
- **Re-auth an account (token expired):** run locally, sign in, then re-upload
  the refreshed `google_token_*.json` / `ms_token_cache_*.json` as a base64 secret.
- **Test now:** `gh workflow run daily_briefing.yml` then `gh run watch <id>`.
