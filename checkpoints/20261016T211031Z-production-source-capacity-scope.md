# Production source discovery and capacity-aware destination selection

- UTC 2026-10-16T21:10:31Z. Operator clarified a further server already runs production Docker. This is a source to inspect/export, not a fresh initialization target. Its endpoint/account/independently attested host identity have not been supplied or verified; no production source contact or data copy claimed.
- Intended result: bounded authenticated read-only source discovery, dependency-aware app selection and evidenced destination recommendation including storage and CPU/RAM history/limits. Transfer is a subsequent app-scoped, consistent backup and isolated restore; original production preserved.
- Scope now: record acceptance in docs/WEB-MIGRATION-MVP.md and canonical FH-0029. Finish already-activated FH-0031 live SSH/browser acceptance independently. Production inventory/export/placement remain IN_PROGRESS, not deployed.
- Dependencies: actual source access and host identity, readable Docker metadata, app/database ownership, available telemetry and candidate destination measurements. Missing facts remain UNKNOWN. Existing runtime must not be initialized/installed/restarted during source discovery.
- Rollback: documentation revert for this increment; existing onboarding activation has its own exact private journal. No production runtime changes authorized by a read-only connection test.

## Validated increment

- 2026-10-16T21:11:19Z: new onboarding units and immutable PHP release831a239 activated using journaled helper; exact private rollback journal retained. Live real HTTPS authenticated Chromium360/768/1440 first-access/key/layout PASS; actual strict SSH inspection via unprivileged systemd service returned READY, Rocky9.8 and Docker absent. Explicit initialization unchecked; no prepare action submitted. Existing center, standby, demo, public project and logout denial PASS. Root readback confirms READY/docker_ready=false. Independent protected canaries and release checks PASS. Private browser evidence remains ignored under .local/qa/onboarding-live.
- Full126 repository tests and disposable complete initialization fixture previously PASS; real initialization remains untested and FH-0031 stays TESTING.
- Source workflow accepted/documented, not implemented or exercised against production. FH-0032 records missing actual source identity/access so public waiting count no longer implies all inputs are available. No raw inventory, credentials or archives exported.
