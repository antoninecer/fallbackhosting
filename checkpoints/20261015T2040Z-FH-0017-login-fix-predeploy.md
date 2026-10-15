# 20261015T2040Z-FH-0017-login-fix-predeploy
- UTC: 2026-10-15T20:40Z; Codex; M02/FH-0017 TESTING.
- Source revision: 5914381 (`fix: allow origin-validated admin login without pre-session cookie`).
- Validation: all 88 repository unit tests pass; PHP syntax check passes; focused regression proves a login POST without the prior session cookie succeeds only with exact configured Origin, while wrong Origin is denied. Existing post-login mutation/logout CSRF tests pass.
- Pre-deployment point-in-time check: `sudo -n python3 scripts/activate-admin.py verify` passed protected canaries, TLS, reference/project assets, lab login route/CSS/private-path denials and frozen prior release integrity.
- Intended deployment: install only the committed PHP admin files into a new root-owned immutable release and atomically switch `/var/www/fallback-admin/current`. No Nginx, PHP-FPM, DNS, firewall, credential, or inventory changes; no service reload.
- Expected previous release for rollback: `/var/www/fallback-admin/releases/21c050b36e8ddd4cd3d7ec5e87a727f556348e9b`.
- Acceptance after switch: current symlink points to the new commit release; live credential login/session rotation/ctx1 display/logout passes; private inventory hash unchanged; protected canaries and TLS remain healthy.
- Rollback: atomically restore the current symlink to the previous immutable release above; retain new release and all data for investigation. No reload required.
- Browser limitation: local headless Chromium cannot start because the host lacks `libatk-1.0.so.0`; no actual Chrome/Safari test is claimed.
