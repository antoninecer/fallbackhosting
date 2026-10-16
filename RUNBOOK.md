# Runbook — initial operations

## Where and who

- GitHub: `https://github.com/antoninecer/fallbackhosting` (public).
- Reported working copy: `/opt/fallback` on `setonuk`, using non-root account `tonda`.
- Public read-only presentation `project.lab.ventureout.cz` is **live**; authenticated server-inventory administration and the read-only project control center are live at `lab.ventureout.cz`. Docker operations remain a local fixture prototype.
- Keep sensitive connection details (IP inventory, credentials, SSH private keys, tokens) in an access-controlled operator secret store **outside Git**.

## Starting a Codex/agent session

```bash
cd /opt/fallback
git status --short --branch
git log -5 --oneline || true
./scripts/resume.sh
```

Agent opening instruction:

> Read AGENTS.md first, then PROJECT.md, ARCHITECTURE.md, ROADMAP.md, STATE.md, TASKS.md, SECURITY.md and the latest checkpoint. Inspect Git and verify any live system claim before changing anything. Work on exactly one approved task. Keep existing Oracle production vhosts independent and operational. Record a checkpoint before and after changes; never mark DONE without evidence.

## Safe commits

```bash
git status --short
git diff --check
git diff --cached --stat
# Review full staged diff for private or secret material.
git diff --cached
git commit -m 'docs: initialize FallbackHosting foundation'
# Push only after explicit operator authorization; no automatic push.
```

## When agent credits run out

The last successfully committed checkpoint remains durable. When access is restored, begin with the opening instruction and `./scripts/resume.sh`; verify the last task before continuing. **Do not** leave unsupervised privileged maintenance jobs running merely to simulate automatic resumption.

## Pre-change protections (for later gateway work)

1. Record current reference application HTTP/TLS baseline and timestamps.
2. Back up the exact files to be edited; verify available rollback.
3. Validate proposed Nginx config (`nginx -t`) before any approved reload.
4. Use only a narrowly scoped, approved config change; do not alter unrelated virtual hosts.
5. Recheck reference service from an independent vantage point after change.
6. If anything is uncertain or a baseline fails, stop and escalate before proceeding.

## Recovery rule

A standby snapshot is not a backup of databases. During standby: disable logins, writes, checkout and DB-backed operations; offer approved static content and independent contact only. Returning online requires a stable health verification period.

## Public project presentation

Public build: `python3 portal/build.py`, after each validated update of canonical tasks/milestones/state/checkpoint. Output public/ is the only webroot; never expose the repository root. Test with `python3 -m unittest discover -s tests -p test_portal.py -v`. Reviewed deployment/rollback and approval scope: docs/PORTAL-DEPLOYMENT.md. Project publication is complete under operator approval; the lab domain now serves the approved authenticated inventory administration. The local static lab introduction is a historical artifact, not the live lab app. Regeneration updates the live project page without reload; no server-side commands are exposed to visitors.

## First platform server setup

Follow docs/SERVER-ONBOARDING.md. Operator may review/copy scripts/inspect-node.sh and run it on ctx1 for bounded read-only evidence. No key, user, sudo, SSH or Docker changes are implied. Unknown host-key/account state stops remote connection; never guess credentials or use disabled host-key checking. Coolify connection validation can mutate/restart Docker, so it requires a separate approved plan.

## Technical SSH status and safe continuation

Operator provisioned the technical transport; agent hostname/effective-user/uptime probes passed at 2026-10-15T08:25:31Z using existing technical identity via its owner process, no key copying. Reuse private operator inventory; exact endpoint/key location are intentionally omitted from this public runbook. Do not recreate keys/accounts or resolve denial with new sudo/Docker rights. Existing StrictHostKeyChecking success is not independent fingerprint proof.

For FH-0014 the operator uses existing trusted ctx1 console to fingerprint the actual negotiated public SSH host key and compares privately with the configured client's trusted entry, recording source/time/verifier/match. Procedure: docs/SSH-OPERATIONS-SERVICE.md. Do not accept new keys, remove known_hosts records, or obtain the sole attestation over the same unverified connection.

Before any unattended broker, review and approve its exact deployment and the agent privilege boundary. Current unrestricted agent sudo defeats simple account/file isolation. No service is installed. Operator separately added target Docker-group membership and authorized an isolated test; its verified cleanup is recorded in docs/DOCKER-SMOKE-TEST.md. No general deployment permission follows. Proposed jobs are fixed read-only actions; public presentation never submits them.

## Private server administration (live HTTPS)

See docs/MULTI-NODE-ADMIN.md and ADMIN-ACTIVATION.md. Source admin/public is sole app document root; never serve admin/, .local/ or repo root. Actual ctx1 inventory/auth are private local working data, not Git/export. Existing bootstrap/seed refuse overwrite: reconcile files first on resume. Initial unique credential is available only to operator in ignored .local/operator/initial-admin.json; retrieve in own private SSH terminal, never paste credentials into chat or command output captured by agent. Application auth JSON contains hash only. Approved isolated web user/pool/vhost activation is now complete; use no SSH/Docker privileges for web runtime. Local tests use disposable data and short-lived loopback listeners, not live services. Back up private inventory/auth before future mutation, preserve lock/revision/audit and do not overwrite after interruption.

## Mandatory public progress after each stage

After each meaningful completed or failed stage, write checkpoint and canonical state, append a reviewed public_events ID/UTC in state/current.json, run `python3 portal/build.py`, and verify the new event over HTTPS on project.lab.ventureout.cz before beginning another stage. Public labels are fixed reviewed mappings in portal/build.py; never export raw checkpoint text, credentials or inventory. Saved timestamps are evidence, not agent heartbeat. Commit/push verified increments under existing operator authorization.

Project progress displays human-readable times in Europe/Prague (CET/CEST, including daylight saving). Canonical state, checkpoint IDs and HTML datetime attributes retain UTC. No host timezone change is required.

## Canonical project records

Edit milestone/task records only in state/catalog.json, then run `python3 scripts/project-data.py sync` and `python3 scripts/project-data.py check`. The two Markdown tables are generated and the public build rejects drift. Contract, evidence requirements and rollback: docs/PROJECT-DATA.md. Public labels still require explicit review in portal/build.py.

For the first application deployment, the operator requests small demo Docker applications selected by the agent. Prefer a simple stateless web demo; choose the concrete image/version and resource limits when preparing the deployment plan. No image selected or deployed by this note.

Public browser QA is reproducible with scripts/check-public-browser.py using an independently installed Playwright/Chromium. It visits only the public page, tests widths 360/768/1440, scroll/focus, filters and stable section position; screenshots/reports go to ignored .local/qa. Temporary tooling is not a production dependency and is not guaranteed to survive cleanup/reboot.

## Protected project control center

The read-only center is active only behind the admin session at `https://lab.ventureout.cz/?center=index.html`; HTML, CSS, JS, resume and manifest are delivered through the same authenticated query route. Its release is root-owned and immutable. Public progress and private inventory remain separate. `python3 center/build.py` defaults to an unauthenticated local static prototype under ignored `.local/control-center`; never publish that output. The reviewed production artifact uses `--delivery admin-query`, is tested in an authenticated fixture, and must be included only in the pinned release flow. Local tests: docs/CONTROL-CENTER-UI.md and scripts/check-center-auth-browser.py.

## Local operations integration

Contract/limitations: docs/OPERATIONS-PROTOTYPE.md and docs/ADMIN-OPERATIONS-PROTOTYPE.md. PHP client uses bounded Unix frames and externally issued scoped capabilities, never a key/shell/SSH API. No production operation route or service is installed. Optional scripts/check-operations-browser.py serves only its generated private fixture page on loopback and stops afterward. Completed ctx1 exercise/cleanup evidence is separate in docs/CONTROLLED-DOCKER-EXERCISE.md.

## Initial private Coolify controller

The initial Coolify containers were removed at operator request on 2026-10-16 for the FH-0023 guided installation trial; data/volumes and pinned recovery material are retained. Follow docs/COOLIFY-DEPLOYMENT.md and the private journal before any retry. Initial account details will be entered in the authenticated wizard. No self-management key or validated deployment target exists. Never open public registration, reuse the audit key or recreate unrelated containers. Exact nonsecret template is deploy/coolify-compose.json; environment/secrets stay private.
