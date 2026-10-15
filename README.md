# FallbackHosting

**Self-hosted deployment platform with resilient, independently hosted standby pages.**

Status: **M00 complete; M01 audit needs further verification; M02 public project presentation live; platform in preparation**. This repository is a project foundation, **not a deployed product**.

## Vision

Deploy WordPress, PHP, Node.js and other container-based applications through a web UI. Publish them under `*.lab.ventureout.cz`. If a primary backend becomes unavailable, serve an explicitly marked standby snapshot or contact page from an **independent Oracle gateway**. An outage at the home app node must not interrupt unrelated services on the gateway.

## Components (planned)

- **Application control plane:** Coolify for Git/Docker deployments on the home app node.
- **Routing:** Existing Nginx on Oracle (stable shared public edge); an internal Coolify/Traefik router on the home node.
- **Fallback:** a standalone builder, versioned snapshots and a gateway serving standby content independently of the home node.
- **Project center:** `project.lab.ventureout.cz`, hosted independently of the home node, for tasks, milestones, incidents, runbooks and agent checkpoints.

## What is known to work (from previous operator checks)

- Public gateway reaches the home test container over Tailscale; an HTTP request returned the expected HTML page.
- Docker in an unprivileged Rocky Linux 9.8 LXC successfully ran `hello-world` after the Proxmox `lxc-pve` update.
- A Docker Nginx test web served HTTP 200 from the home node.
- The intended DNS records for `lab` and `*.lab` were configured; re-check before public deployments.

These facts are **historical observations**. They are not live monitoring. See `STATE.md` and verify before acting.

## Start or resume work

1. Read `AGENTS.md`, `PROJECT.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `STATE.md`, `TASKS.md`, and `SECURITY.md`.
2. Run `./scripts/resume.sh` (read-only) and inspect Git working tree.
3. Confirm the real runtime state; never infer success from a stale document.
4. Select exactly one unblocked task; record a checkpoint before changes.
5. Perform a small reversible change, test it, update task and checkpoint, then commit.

> Never commit credentials, private network inventories, SSH private keys, secrets, full internal logs or customer data. The GitHub repository is public.

## First implementation milestones

M00 docs + Git → M01 inventory/baselines → M02 independent project portal → M03 deployment platform → M04 wildcard routing & TLS → M05 snapshot builder → M06 standby routing → M07 emergency contacts → M08 failure tests → M09 agent continuity → M10 release.

This roadmap is a plan, **not a record of completed deliveries**.

Session 001 audit: [M01](docs/M01-AUDIT.md). Portal proposal: [M02](docs/M02-CONTROL-CENTER.md). Current next task: `state/current.json` and latest checkpoint. Approved public progress presentation is live; application platform is not deployed.

Public progress presentation source is in `portal/`; build with `python3 portal/build.py`. Project presentation: https://project.lab.ventureout.cz/ (verified HTTPS). See [deployment evidence/procedure](docs/PORTAL-DEPLOYMENT.md). This public view is distinct from protected administration.

Authenticated server inventory is live at https://lab.ventureout.cz/ under explicitly approved isolated Oracle deployment. [User workflow](docs/PLATFORM-WORKFLOW.md) and [server onboarding](docs/SERVER-ONBOARDING.md) document the next phase. `python3 portal/build.py` rebuilds project and lab static artifacts; they contain no administrative access.

Technical SSH transport to the home node was operator-provisioned and subsequently checked by agent with three read-only probes. Independent host identity and enforced key/agent isolation remain open. [Operations service proposal](docs/SSH-OPERATIONS-SERVICE.md) records the next gates; no broker deployed. Operator subsequently granted Docker-group access; the isolated lifecycle test and cleanup passed (FH-0016).

Private multi-node PHP administration source: `admin/`. ctx1 is prefilled only in ignored private local inventory; initial admin securely provisioned and real HTTPS login/list/logout tested. [Feature/status review](docs/MULTI-NODE-ADMIN.md), [exact activation scope](docs/ADMIN-ACTIVATION.md). No remote operations/technical-key access from web. Run local checks with `python3 -m unittest discover -s tests -v`.
