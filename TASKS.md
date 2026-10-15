# Tasks

Task lifecycle: BACKLOG → READY → IN_PROGRESS → TESTING → DONE; BLOCKED requires reason and next safe step. Legacy PLANNED maps to BACKLOG for tasks only. Milestone statuses remain defined in ROADMAP.md.

| ID | Milestone | Status | Owner | Acceptance / next step |
| --- | --- | --- | --- | --- |
| FH-0001 | M00 | DONE | Codex | Required docs, valid state, working resume, checkpoint and local commit; Session 001 validation checkpoint is evidence |
| FH-0002 | M01 | BLOCKED | Operator + Codex | Initial sanitized audit delivered; full scoped home inventory, dependency and backup evidence still unavailable; obtain authorized evidence |
| FH-0003 | M01 | BLOCKED | Operator + Codex | Oracle route/TLS/two assets passed; independent external vantage and safe dynamic test evidence missing; obtain external baseline |
| FH-0004 | M03 | BACKLOG | Operator + Codex | Coolify requirements/security/backup plan and explicit installation approval; do not install |
| FH-0005 | M02 | BLOCKED | Operator + Codex | Proposal in docs/M02-CONTROL-CENTER.md; operator UI/privacy/auth design approval pending |
| FH-0006 | M02 | READY | Codex | Next: repository-only schema/export implementation after mandatory initialization; validate references, evidence, sanitization and stale states; no deployment |
| FH-0007 | M02 | BACKLOG | Codex | Depends FH-0006; responsive accessible UI, all modules and mobile verification |
| FH-0008 | M02 | BACKLOG | Operator + Codex | Depends FH-0005/FH-0007; exact isolated deployment/rollback proposal and approval before runtime changes |

FH-0006 may prepare a local prototype against the documented proposal while design approval is pending; publication remains blocked. Session 001 scope ends at design.

## Scope, dependencies, rollback and evidence

FH-0001: repository only; Bash/Git/Python available; rollback via reviewed revert. Validation and timestamps in latest checkpoint. Remote main observed at initial base commit; no push performed.
FH-0002/0003: read-only; existing tools/network only; no runtime rollback needed. Evidence/unknowns: docs/M01-AUDIT.md. Failed sandbox startup is a tooling limitation, not a production incident.
FH-0005: documentation only; architecture constraints and audit are dependencies; rollback via revert. No approval or deployed portal claimed.
FH-0006: repository only; acceptance includes canonical-state migration preserving IDs, explicit schema, validation, allowlisted export and meaningful negative tests. Rollback via revert; no secret/runtime configuration.

No new confirmed production incident. Historical EFI warning remains an uncertainty requiring operator review before any PVE reboot.
