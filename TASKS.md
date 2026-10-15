# Tasks

Task lifecycle: BACKLOG → READY → IN_PROGRESS → TESTING → DONE; BLOCKED requires reason and next safe step. Legacy PLANNED maps to BACKLOG for tasks only. Milestone statuses remain defined in ROADMAP.md.

<!-- Table generated from state/catalog.json; edit catalog then run python3 scripts/project-data.py sync. -->

| ID | Milestone | Status | Owner | Acceptance / next step |
| --- | --- | --- | --- | --- |
| FH-0001 | M00 | DONE | Codex | Required docs, valid state, working resume, checkpoint and local commit; Session 001 validation checkpoint is evidence |
| FH-0002 | M01 | READY | Operator + Codex | Operator attests successful 2026-10-15 LXC backup and zstd -t integrity VERIFIED, monthly schedule configured. Restore NOT TESTED, external copy NOT DOCUMENTED. Continue dependency coverage; do not claim full M01 complete. |
| FH-0003 | M01 | BLOCKED | Operator + Codex | Oracle route/TLS/two assets passed; independent external vantage and safe dynamic test evidence missing; obtain external baseline |
| FH-0004 | M03 | BACKLOG | Operator + Codex | Coolify requirements/security/backup plan and explicit installation approval; do not install |
| FH-0005 | M02 | TESTING | Operator + Codex | Local authenticated center adapter and exact release proposal prepared; 41 tests and disposable browser 360/768/1440 PASS. Production activation remains a separate operator decision; source header compatibility fix is not deployed. |
| FH-0006 | M02 | DONE | Codex | Canonical catalog and generated Markdown tables implemented; 28 repository tests, reference/evidence/revision/privacy/staleness checks passed. Evidence: docs/PROJECT-DATA.md and FH-0006 checkpoints. |
| FH-0007 | M02 | DONE | Codex | Local-only eight-module read-only prototype implemented; 36 repository tests and Chromium 360/768/1440 keyboard/filter/copy/download/long-text checks PASS. Deployment/authentication remains separate FH-0008 scope. |
| FH-0008 | M02 | BACKLOG | Operator + Codex | Depends FH-0005/FH-0007; exact isolated deployment/rollback proposal and approval before runtime changes |
| FH-0009 | M02 | DONE | Codex | Live HTTPS/isolation checks previously passed; Chromium 360/768/1440 screenshots, keyboard history scrolling and all five filters now PASS. History growth does not move later content; see browser checkpoint. |
| FH-0010 | M02 | READY | Operator + Codex | Historical static entry proposal superseded by live authenticated admin FH-0017/FH-0018; reconcile any future entry work with that deployment |
| FH-0011 | M03 | BLOCKED | Operator + Codex | SSH identity, node OS/resources/Compose and isolated Docker lifecycle verified; constrained operations boundary/Coolify installation remain separate gates. |
| FH-0012 | M02 | READY | Operator + Codex | Dedicated webroot renewal recorded, but no per-cert/global deploy hook observed. Prepare exact nginx syntax-test/reload hook and renewal-test proposal; scoped approval required before changes |
| FH-0013 | M03 | TESTING | Codex + Operator | Isolated SSH service proposal documented; operator review pending; no service deployed or operational permissions granted |
| FH-0014 | M01 | DONE | Operator + Codex | Independent trusted-console ED25519 attestation supplied by operator, matched existing client trust and strict pinned-algorithm probe; private prepared/live identity VERIFIED with audit and backup. No trust or infrastructure change. |
| FH-0015 | M03 | TESTING | Operator + Codex | Concrete separate constrained-runner/issuer/code/policy/key-custody/recovery proposal prepared; current unrestricted sudo/Docker path re-observed. Operator review and real negative tests required; no enforcement or permission change claimed. |
| FH-0016 | M03 | DONE | Codex | New-session Docker access, isolated create/start/exit-0/remove and absence, unchanged reference, pre/post endpoint checks passed; evidence docs/DOCKER-SMOKE-TEST.md and lifecycle checkpoint; containing local commit required |
| FH-0017 | M02 | TESTING | Codex + Operator | Multi-node PHP admin, private ctx1 Docker seed and secured local admin ready; 13 tests and actual local login passed. Activation complete under FH-0018; browser QA pending; docs/MULTI-NODE-ADMIN.md |
| FH-0018 | M02 | TESTING | Codex | Existing lab inventory HTTPS live. Prior direct-HTTP auth passed; local browser test found no-referrer/Origin compatibility issue in matching frozen source. Same-origin fix tested locally, not deployed. Live browser QA/rollback remain open. |
| FH-0019 | M02 | BLOCKED_BY_OPERATOR | Codex + Operator | Approve exact new reviewed lab application release switch and rollback; no Nginx/PHP-FPM/cert/DNS/firewall change. Existing inventory deployment is already live. |
| FH-0020 | M03 | DONE | Codex | Fixture-only v1 implements eight managed actions and scoped Unix views; all 57 repository/16 broker tests PASS. Real driver/issuer/host sandbox/service activation remain separate gates. |
| FH-0021 | M02 | DONE | Codex | Local PHP/Unix client and read-only app/node/dated-container/jobs/results/errors/audit prototype verified: 62 tests and Chromium 360/768/1440 PASS. No live route/service or web mutation controller activated. |
| FH-0022 | M03 | DONE | Codex | Authorized real ctx1 one-owned-container create/start/inspect/log/restart/stop/remove/absence PASS, original baseline unchanged, protected canaries PASS. Earlier bounded-log configuration failure corrected only for new test container; no service changes. |

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

User requested first-run server identification and SSH setup as next phase. Design: docs/SERVER-ONBOARDING.md. Intended result: verified node identity/resources and explicit private connection settings, separate read-only probe from approved deployment setup. Operator has now provisioned technical access. Agent verified hostname, effective user and uptime over strict existing SSH trust at 2026-10-15T08:25:31Z. Current blockers: independent fingerprint attestation and approved service/agent privilege boundary; software/resources still unverified. Previous Docker denial is superseded: operator granted Docker-group membership, fresh-session agent lifecycle test passed and cleanup was verified. Remote sudo absence remains operator-reported. Agent granted no rights. Dependencies: operator existing console/access and supported OS/Docker evidence. Rollback: documentation revert; owned test container cleanup was exercised, no existing workloads changed. Acceptance for design: fields, fingerprint verification, key custody, privilege risks and read-only inspection procedure documented. Runtime acceptance later requires actual node evidence and approved access provisioning; do not mark DONE now. Official current Coolify documentation reviewed; validation can restart Docker and is outside read-only scope.

## FH-0012 — certificate renewal completion

Read-only inspection found no project per-certificate deploy/renew hook and zero global deploy-hook files. Successful future Certbot renewal alone does not prove Nginx will load the renewed certificate. Intended next result: reviewed project-specific syntax-test/reload hook and controlled renewal-test plan, with backups, exact authorization and protected-site canaries. No hook/timer changed and no staging renewal test run. Dependencies: existing Certbot timer and approved maintenance scope; rollback restore only project renewal configuration backup. Do not claim automatic end-to-end renewal tested.

## FH-0013 — isolated operations-service proposal

Intended result: reviewable design keeping private key outside web/Codex access. Scope: docs/SSH-OPERATIONS-SERVICE.md and existing state only. Dependencies: verified transport, independently attested host identity and enforceable local privilege boundary. Acceptance: allowlisted read-only actions, caller/project authorization, protected key/code/policy, bounded jobs, interruption UNKNOWN handling, no automatic privilege escalation, explicit deployment tests/approval/rollback. Design drafted; runtime tests not run. Rollback: reviewed documentation revert; no installed service to roll back. Operator review pending, so TESTING rather than deployed/DONE.

## FH-0014 — independent SSH host identity

Transport probes passed using existing known_hosts with StrictHostKeyChecking=yes, UpdateHostKeys=no; this is not independent identity verification. Operator must obtain the negotiated host-key algorithm/SHA256 fingerprint through the existing trusted target console and compare privately against the client trust entry; record source, UTC, verifier and match without raw private inventory in Git. Expected fingerprint is UNKNOWN; no trust entry changed. Acceptance: independent match and recorded provenance before service activation. Dependencies: trusted operator console and exact private connection inventory. Rollback: none for comparison; any later pin change needs backup and exact approval. This task is BLOCKED on external evidence, not failed SSH.

## FH-0015 — enforce agent/key separation

Current agent account has unrestricted passwordless sudo (AGENT_OBSERVED) and Docker-group membership; key file separation alone is not sufficient. Intended result: reviewed constrained execution plan without sudo/service-user switching, editable credential-bearing service code, or root-equivalent Docker paths, with preserved operator recovery access. No privilege changes made. Acceptance: operator approves exact scope and later negative tests demonstrate key/service/policy isolation. Dependencies: deployment policy and actual Docker privilege assessment. Rollback: separately approved restoration plan for only changed agent boundary; never lock out operator. Do not grant remote sudo/Docker rights to resolve this task.

### FH-0011 previous Docker probe result — historical, superseded by FH-0016

On explicit operator request, agent found /usr/bin/docker but daemon-version query exited 1 with socket permission denial. No resource was created; cleanup was unnecessary. At that time the account could not use the standard Docker API. Operator later granted access and FH-0016 passed; this old denial is not the current state. No remote sudo was attempted. Before repeating a create/delete test, review the strictly scoped helper proposal in docs/SSH-OPERATIONS-SERVICE.md and obtain exact privilege/installation approval; no broad Docker-group or sudo-docker grant. Evidence recorded 2026-10-15T08:31:28Z in checkpoint.

## FH-0016 — isolated Docker lifecycle verified

Operator granted Docker-group membership and requested retest. Scope: one unique own resource using existing immutable image, no ports/mounts/network or image pull; inert command run, exact removal, absence and unchanged existing reference verified. Acceptance passed with recorded UTC 2026-10-15T08:35:47Z and evidence in docs/DOCKER-SMOKE-TEST.md. Rollback exercised by own-container removal. Dependencies: existing technical SSH trust and image; independent identity remains a separate unresolved gate. No permission granted by agent. Completion revision: containing local commit. This is not Coolify deployment or cross-project isolation verification.

## FH-0017 — multi-node counterpart administration

Operator requests one public VPS with multiple application nodes and ctx1 prefilled as Docker. Scope: PHP auth/config UI, private local inventory/bootstrap, no remote actions or deployment installation. Acceptance: authenticated list/add/edit/disable, multiple distinct IDs, declared runtime/platform separate from dated observations, changed target invalidates old results, locked atomic updates/conflicts, no key fields or private export, safe initial admin and ctx1 seed. Initial thirteen tests plus actual seeded loopback login/list/logout passed; activation and real HTTPS auth subsequently passed under FH-0018. Browser QA remains outstanding, so TESTING. Dependencies: existing PHP 8.3/Argon2id/session support, protected local state and explicit production plan. Evidence: latest FH-0017 checkpoint and docs/MULTI-NODE-ADMIN.md. Rollback: reviewed source revert; back up private state before edits and never overwrite seed/auth; exact new-pool/vhost rollback in docs/ADMIN-ACTIVATION.md. No runtime/account/remote grant implied.

## 2026-10-15 follow-up verification

FH-0018: real HTTPS admin login/session rotation/ctx1/logout rechecked successfully; private inventory unchanged. All 14 local tests passed. No browser tooling available; visual/mobile QA and live rollback drill remain unperformed. Deployment is not marked DONE. Historical static lab-entry instructions are superseded by the deployed authenticated app.

FH-0009 display follow-up: Europe/Prague timestamps implemented; eight portal tests including summer/winter/DST and UTC preservation PASS, live HTTPS display verified. Browser/mobile/filter QA remains pending. Rollback: reviewed Git revert and public rebuild.
