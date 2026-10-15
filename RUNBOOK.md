# Runbook — initial operations

## Where and who

- GitHub: `https://github.com/antoninecer/fallbackhosting` (public).
- Reported working copy: `/opt/fallback` on `setonuk`, using non-root account `tonda`.
- Public read-only presentation `project.lab.ventureout.cz` is **live**; protected administrative portal remains planned.
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

Public build: `python3 portal/build.py`, after each validated update of canonical tasks/milestones/state/checkpoint. Output public/ is the only webroot; never expose the repository root. Test with `python3 -m unittest discover -s tests -p test_portal.py -v`. Reviewed deployment/rollback and approval scope: docs/PORTAL-DEPLOYMENT.md. Project publication is complete under operator approval; lab introduction is built locally and awaits separate exact gateway approval. Regeneration updates the live project page without reload; no server-side commands are exposed to visitors.

## First platform server setup

Follow docs/SERVER-ONBOARDING.md. Operator may review/copy scripts/inspect-node.sh and run it on ctx1 for bounded read-only evidence. No key, user, sudo, SSH or Docker changes are implied. Unknown host-key/account state stops remote connection; never guess credentials or use disabled host-key checking. Coolify connection validation can mutate/restart Docker, so it requires a separate approved plan.
