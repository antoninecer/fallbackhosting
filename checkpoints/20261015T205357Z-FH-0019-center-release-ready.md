# 20261015T205357Z-FH-0019-center-release-ready
- UTC: 2026-10-15T20:53:57Z; M02/FH-0019 IN_PROGRESS.
- Cause confirmed: existing active release has no center artifact, resulting in the existing handler's generic 503. Center delivery is already session-gated; no public/static route will be added.
- Candidate readiness: 88/88 repository tests PASS; center artifact source pin and manifest verification PASS; generated assets fit limits and use only `/?center=` delivery; the local-only prototype banner is removed. PHP source syntax PASS; privileged PHP-FPM config test PASS; protected canaries/TLS/reference/project checks PASS.
- Existing current release: `/var/www/fallback-admin/releases/f285d8ab5400c9364f4008c6c06db035ebe0f26e`.
- Private inventory baseline (revision 3 and SHA-256) saved in mode-0600 ignored file `.local/center-predeploy-private.json`; do not publish its contents.
- Planned exact action: build from the committed candidate state, install one root-owned immutable release under `/var/www/fallback-admin/releases/<full-commit>`, verify its exact files/modes/manifest, atomically replace only `current`, then test protected route/assets, unauthenticated denial, logout revocation, inventory hash and canaries.
- If the prior-code cache prevents loading the new center path, one graceful `systemctl reload php8.3-fpm` may be used only after `php-fpm8.3 -t` and protected pre-canaries pass; post-canaries are mandatory. No config changes.
- Rollback on any failed check: restore `current` to the exact previous release above; retain both releases/data; graceful FPM reload only if needed to discard cached new code; recheck protected canaries.
- No production release switch has occurred yet.
