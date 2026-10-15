# 20261015T204932Z-FH-0017-ctx1-description-reconciled
- UTC: 2026-10-15T20:49:32Z; Codex; M02/FH-0017 TESTING.
- Operator confirmed reaching the authenticated administration page, confirming login succeeded in their browser.
- Live private inventory initially had revision 2 and a PASS fingerprint observation at 2026-10-15T15:08:23Z, but its description incorrectly said independent SSH fingerprint verification was missing.
- First validated-form save returned 503 and made no inventory change. Inspection found the exact `inventory.lock` owned by root (mode 0600), preventing the web account from opening it. Changed only that lock file to owner/group `fallback-web:fallback-web`, mode 0600; no service/config/release change.
- Authenticated HTTPS form edit then changed only ctx1 description. Inventory revision is 3; audit records `server.update`; fingerprint status and timestamp remain PASS / 2026-10-15T15:08:23Z. Updated description states LXC/OS are historical and SSH identity was independently verified via the administrator's Proxmox console. No fingerprint value or private endpoint was published.
- Verification: authenticated form confirms stale message absent and identity observation retained; logout request sent; all 9 admin tests PASS; `scripts/activate-admin.py verify` PASS for protected canaries, TLS, reference/project assets, lab route/CSS/private-path denials and release integrity.
- Rollback: restore only prior description through authenticated form (creating a new audit revision); do not revert lock ownership because root ownership prevents intended admin writes. No other runtime data changed.
- Next safe task: resume M01/FH-0002 read-only dependency and backup coverage audit. No backup schedule, infrastructure or service changes.
