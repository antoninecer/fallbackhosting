# Tasks (human-readable backlog)

Tasks are never silently treated as DONE. Each entry needs verification, evidence, and an updated checkpoint.

## Active

### FH-0001 — First public repo foundation [IN_PROGRESS]

- **Milestone:** M00
- **Owner:** Operator + assisted AI
- **Goal:** Add startup documentation, binding agent rules, roadmap, state, tasks and resume scripts.
- **Before doing:** Review staged files for credentials/private topology; the GitHub repository is public.
- **Acceptance:** `git status` clean after commit and successful push to `main`; remote files visible.
- **Safe rollback:** revert documentation commit with reviewed commit; never rewrite Git history.
- **Last verified evidence:** Empty Git repo cloned; SSH authentication previously succeeded. First push not yet verified.
- **Next action:** Extract starter kit into the repo, inspect, stage, commit and push.

## Ready after M00

### FH-0002 — Read-only inventory [PLANNED]

- **Milestone:** M01
- **Goal:** Verify actual host, LXC, Docker, Tailscale, Nginx, DNS and storage state without changing services.
- **Acceptance:** Signed/dated sanitized inventory and a list of unknowns, with secrets stored outside Git.

### FH-0003 — Protected production canary [PLANNED]

- **Milestone:** M01
- **Goal:** Measure Quantum Random availability from Oracle and externally before Lab proxy work.
- **Acceptance:** Safe read-only probe and explicit error criteria; no credentials in Git.

### FH-0004 — Deployment-control design [PLANNED]

- **Milestone:** M03
- **Goal:** Confirm Coolify requirements in nested unprivileged LXC, security separation and backup.
- **Acceptance:** Tested plan, operator approval prior to installation, and rollback.

### FH-0005 — Project center design [PLANNED]

- **Milestone:** M02
- **Goal:** Define minimal authenticated portal on Oracle backed by Git/task state.
- **Acceptance:** UI scope and privacy model approved, no dependence on home availability.

## Incident registry

No FallbackHosting incident is currently recorded. Prior host issues described in `STATE.md` are historical context, **not unresolved incidents unless independently confirmed**.
