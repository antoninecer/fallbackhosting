# 20261015T204510Z-FH-0017-login-fix-live-pass
- UTC: 2026-10-15T20:45:10Z; Codex; M02/FH-0017 TESTING.
- User impact: repeated 403 after entering the existing admin credentials. The earlier direct login checks had not reproduced the user's browser request behavior.
- Change: release `f285d8ab5400c9364f4008c6c06db035ebe0f26e` is active at `/var/www/fallback-admin/current`. Unauthenticated login now relies on strict exact-Origin validation; session-bound CSRF remains required for authenticated mutations and logout.
- Deployment action: after verifying `php-fpm8.3 -t`, active service state, and protected canaries, performed one graceful reload of `php8.3-fpm` to load the new release. No Nginx/PHP-FPM configuration, DNS, inventory, credentials, or unrelated service was changed.
- Acceptance evidence: live HTTPS login without retaining the pre-auth session cookie PASS; authenticated session rotation PASS; `ctx1` visible PASS; logout PASS; private inventory hash unchanged PASS; `scripts/activate-admin.py verify` PASS for protected canaries, TLS, reference/project assets, lab route/CSS/private-path denials.
- Browser limitation: browser automation could not launch because the host lacks `libatk-1.0.so.0`; no OS package was installed. Operator Chrome/Safari confirmation remains pending, so browser QA is NOT_PERFORMED and FH-0017 remains TESTING.
- Rollback: restore `current` to `/var/www/fallback-admin/releases/21c050b36e8ddd4cd3d7ec5e87a727f556348e9b`; gracefully reload PHP-FPM only if needed to clear cached code. Retain private data and both releases.
- Next: operator may use the existing credentials at `https://lab.ventureout.cz/`; if the browser still fails, record the exact message and time. Continue other unblocked project work.
