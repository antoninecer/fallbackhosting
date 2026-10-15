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
| FH-0009 | M02 | TESTING | Codex | Live HTTPS/page/assets/isolation/canaries passed; browser/mobile/filter QA pending; evidence in latest live checkpoint |
| FH-0010 | M02 | READY | Operator + Codex | Separate lab platform entry page/templates prepared; validate locally, obtain exact gateway approval, then live HTTPS/canary checks; no fake login or home changes |
| FH-0011 | M03 | BLOCKED | Operator + Codex | Onboarding design and read-only inventory script prepared; existing SSH account/port/access unknown. Next obtain operator evidence, then exact account/key/privilege proposal; no installation |
| FH-0012 | M02 | READY | Operator + Codex | Dedicated webroot renewal recorded, but no per-cert/global deploy hook observed. Prepare exact nginx syntax-test/reload hook and renewal-test proposal; scoped approval required before changes |

FH-0006 may prepare a local prototype against the documented proposal while design approval is pending; publication remains blocked. The original Session 001 scope ended at design; the subsequent operator request adds the public presentation under FH-0009.

## Scope, dependencies, rollback and evidence

FH-0001: repository only; Bash/Git/Python available; rollback via reviewed revert. Validation and timestamps in latest checkpoint. Remote main observed at initial base commit; no push performed.
FH-0002/0003: read-only; existing tools/network only; no runtime rollback needed. Evidence/unknowns: docs/M01-AUDIT.md. Failed sandbox startup is a tooling limitation, not a production incident.
FH-0005: documentation only; architecture constraints and audit are dependencies; rollback via revert. No approval or deployed portal claimed.
FH-0006: repository only; acceptance includes canonical-state migration preserving IDs, explicit schema, validation, allowlisted export and meaningful negative tests. Rollback via revert; no secret/runtime configuration.

No new confirmed production incident. Historical EFI warning remains an uncertainty requiring operator review before any PVE reboot.

## FH-0009 — public presentation

Operator requested a simple public project presentation after Session 001 design. Operator subsequently approved exact project-domain Nginx/TLS activation; it is live and verified, with visual QA pending. Lab domain needs a separate exact target approval. This is separate from the authenticated administrative center. Dependencies: Python stdlib and existing Nginx/certbot; no PHP runtime needed. Rollback: reviewed Git revert; production rollback in docs/PORTAL-DEPLOYMENT.md. Current output is a snapshot, not live monitoring. FH-0006 remains a broader canonical schema/export task, not completed by this limited public view.

## FH-0010 — platform entry

Scope: lab.ventureout.cz introductory page explaining future admin-provisioned workspaces; actual account/runtime implementation remains M03 and future security work. Dependencies: reviewed static source and dedicated gateway approval. Rollback: new lab host only, per docs/LAB-DEPLOYMENT.md. Acceptance: truthful static copy, no login/forms/admin execution, HTTPS/assets/isolation and unchanged production canaries after activation. Owner: operator + Codex.

## FH-0011 — server onboarding design

User requested first-run server identification and SSH setup as next phase. Design: docs/SERVER-ONBOARDING.md. Intended result: verified node identity/resources and explicit private connection settings, separate read-only probe from approved deployment setup. Current blocker: existing SSH account and key access unconfirmed. Dependencies: operator existing console/access and supported OS/Docker evidence. Rollback: documentation revert; no runtime changes made. Acceptance for design: fields, fingerprint verification, key custody, privilege risks and read-only inspection procedure documented. Runtime acceptance later requires actual node evidence and approved access provisioning; do not mark DONE now. Official current Coolify documentation reviewed; validation can restart Docker and is outside read-only scope.

## FH-0012 — certificate renewal completion

Read-only inspection found no project per-certificate deploy/renew hook and zero global deploy-hook files. Successful future Certbot renewal alone does not prove Nginx will load the renewed certificate. Intended next result: reviewed project-specific syntax-test/reload hook and controlled renewal-test plan, with backups, exact authorization and protected-site canaries. No hook/timer changed and no staging renewal test run. Dependencies: existing Certbot timer and approved maintenance scope; rollback restore only project renewal configuration backup. Do not claim automatic end-to-end renewal tested.
