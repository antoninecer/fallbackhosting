# FallbackHosting

**Self-hosted deployment platform with resilient, independently hosted standby pages.**

Status: **M00 / Foundation – in progress**. This repository is a project foundation, **not a deployed product**.

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
