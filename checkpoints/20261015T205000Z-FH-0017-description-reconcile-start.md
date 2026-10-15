# FH-0017 ctx1 description reconciliation — start
- UTC: 2026-10-15T20:50:00Z; M02/FH-0017 TESTING.
- Observed inconsistency: authenticated live page reports server identity `Ověřeno · 2026-10-15T15:08:23Z`, while the same ctx1 card description says independent SSH fingerprint verification is missing.
- Read-only check of `/var/lib/fallback-web/admin/inventory.json` confirmed revision 2, fingerprint observation status PASS at 2026-10-15T15:08:23Z, and stale description. No endpoint/account/fingerprint value was emitted.
- Intended exact action: update only ctx1 description through the authenticated admin form to state that LXC/OS are historical and the identity was independently verified; preserve endpoint, credentials, runtime, fingerprint observation and all other records.
- Acceptance: inventory revision/audit records one metadata edit; all ctx1 observations and endpoint/config fields remain identical; authenticated HTTPS page no longer claims fingerprint is missing; logout works; tests/canaries remain PASS.
- Rollback: restore only original description through authenticated edit (which records a new revision/audit event); no raw file replacement or infrastructure changes.
