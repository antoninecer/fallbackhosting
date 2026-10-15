# 20261015T205239Z-FH-0019-center-candidate-pass
- UTC: 2026-10-15T20:52:39Z; M02/FH-0019 IN_PROGRESS.
- Exact request: operator reported 503 at `https://lab.ventureout.cz/?center=index.html` after reaching authenticated admin.
- Cause: active PHP release `f285d8ab5400c9364f4008c6c06db035ebe0f26e` lacks `center-artifact/`; existing handler therefore correctly fails closed.
- Candidate source: exact commit `9ccca4b2a07c528cb7387ddbf3a052d53f2f82ea`; `center/build.py --delivery admin-query`; candidate content size 72,573 bytes; manifest SHA-256 `58c8e4d58023f604b18c0e9ae96c11a13dfc8a8e4c30437dc6d451abfaffe307`.
- Validation: repository test suite 88/88 PASS; catalog check PASS; exact pinned-source/artifact verifier PASS; PHP syntax checks PASS; privileged `php-fpm8.3 -t` PASS; `scripts/activate-admin.py verify` PASS (protected canaries, TLS, reference/project assets, lab route/CSS/private-path denials and current-release integrity).
- Baseline: current symlink still resolves to prior release above; private inventory revision 3 SHA-256 baseline saved mode 0600 under ignored `.local/center-predeploy-private.json`. Candidate built under ignored `.local/`; no production files changed.
- Exact next action: install a new root-owned 0755/0644 immutable release and atomically switch only `/var/www/fallback-admin/current`; test the authenticated route and all five assets, unauthenticated denials, session revocation on logout, unchanged inventory hash and canaries.
- Rollback: atomically restore the prior symlink. Retain both releases and private data; no reload.
