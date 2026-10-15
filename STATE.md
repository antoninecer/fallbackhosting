# Current project state

Updated 2026-10-15T07:12:54Z, Session 001 / Codex. Point-in-time observations, not live monitoring.

- M00 DONE with locally committed evidence; original push requirement superseded by explicit no-auto-push instruction.
- M01 NEEDS_TEST: initial read-only audit delivered; external canary, complete dependency/backup evidence and home inventory unresolved.
- M02 PLANNED: concrete proposal delivered, operator review pending; no portal deployed.
- Git initial main clean at 3b5ea7b; remote main independently matched via git ls-remote during audit. Session changes are local only. See git log for final evidence commit.
- No infrastructure changes, outage tests, installations, production reloads or DNS changes.

## Evidence and uncertainty

See docs/M01-AUDIT.md for methods, timestamp window, protected-services baseline, inventory and risks. Reference HTTP/TLS/route/two assets and home test HTTP passed from Oracle. Full application functionality and home-failure independence remain UNKNOWN. Home PVE/LXC versions/resources remain historical/unverified. Docker active on Oracle is observed, not evidence of Coolify installation.

Historical EFI GRUB warning is not confirmed resolved; operator review required before PVE reboot. No uptime guarantee or fallback readiness claimed.

## Next exact task

FH-0006: after mandatory initialization, checkpoint and implement repository-only canonical schema validator and sanitized portal exporter against docs/M02-CONTROL-CENTER.md. Do not deploy. Review pending design with operator; any live change requires exact scope approval. Resume shows latest checkpoint and state/current.json. No automatic push or credit-reset resumption.
