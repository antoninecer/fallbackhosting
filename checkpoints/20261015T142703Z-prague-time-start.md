# Prague display time — start
- UTC: 2026-10-15T14:26:46+00:00; pre-change checkpoint.
- Intended result: all human-facing project progress times display Europe/Prague, including DST; canonical UTC remains unchanged.
- Scope: portal renderer, tests and documentation/state; no host timezone or service changes.
- Acceptance: summer/winter conversion, UTC datetime attributes preserved, live HTTPS output verified.
- Dependencies: Python zoneinfo and system timezone database.
- Rollback: reviewed Git revert and rebuild public page.
