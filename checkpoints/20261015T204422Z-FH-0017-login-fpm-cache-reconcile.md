# 20261015T204422Z-FH-0017-login-fpm-cache-reconcile
- UTC: 2026-10-15T20:44:22Z; Codex; M02/FH-0017 TESTING.
- Source revision: f285d8ab5400c9364f4008c6c06db035ebe0f26e; PHP release symlink points to this immutable release.
- Reconciliation: the new implementation is installed, but live no-pre-auth-cookie login still returned 403 after the documented PHP realpath cache TTL. This is consistent with PHP-FPM OPcache retaining the prior script; root cause is not yet proven.
- Before the next action: `php-fpm8.3 -t` PASS; service `php8.3-fpm` ACTIVE; `scripts/activate-admin.py verify` PASS (protected canaries, TLS, reference/project assets, existing lab route/CSS/private-path denials and old release integrity).
- Intended next action: one graceful `systemctl reload php8.3-fpm` to clear stale code cache and load the already-installed release. No pool/config edit, Nginx change, credential/inventory mutation, or restart.
- Acceptance: live login without the pre-auth cookie passes; session rotates, ctx1 is displayed, logout works, inventory hash unchanged; protected canaries and lab TLS pass afterward.
- Rollback: restore `current` symlink to `/var/www/fallback-admin/releases/21c050b36e8ddd4cd3d7ec5e87a727f556348e9b`; a further graceful FPM reload only if needed to clear the cached code; retain data and both releases.
