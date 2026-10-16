# Public control plane and SSH-discovered recovery

Operator-directed target architecture, 2026-10-16. Subsequent clarification prioritizes availability and one FallbackHosting UI over a fixed Coolify placement/count. This supersedes the mandatory public Coolify placement below; no live migration is implied.

## Placement and independence

The public-IP node hosts the FallbackHosting administration/control plane and independent public serving edge. Remote physical/VM/Docker-capable LXC Linux nodes host application workloads. Coolify is a deployment adapter behind FallbackHosting: it can run centrally or remotely; multiple instances are allowed when there is an explicit operational benefit, rather than required per node. Prefer reusing the current verified instance for the first complete availability test. Public IP placement does not imply anonymously accessible administration.

The existing Oracle gateway remains the independent public edge. Its current Nginx sites, approved static standby releases and public project presentation must continue serving without Docker, Coolify, the remote application node or the SSH recovery service. Running a Docker-based controller on the same public machine must not turn Docker into a dependency of static serving. Resource/storage limits and narrow service/config boundaries are required in the migration plan.

OBSERVED current state: Coolify still runs privately on ctx1. Its final placement is an implementation choice subordinate to availability, access isolation and simple operation; no public-node migration is required merely to satisfy this architecture. No live placement changes are made by this document.

## Availability contract

The user-facing entry point is FallbackHosting: node enrollment over a supported VPN, controlled software preparation, application/domain assignment, snapshot preview/publication, maintenance, dated health and backup/recovery operations. Tailscale is the initial transport; deployment and recovery adapters must not hardcode the physical/VM/LXC topology.

Healthy requests use the edge proxy and the selected application's reachable backend. Requests must not call a Coolify API, PHP management session or backup repository before being served. A failed controller alone does not mean an application is unavailable. Monitoring evaluates each actual app separately; a backend/app/VPN failure selects that app's already-published local static release. Manual maintenance can select it before work begins. Recovery needs repeated healthy app checks and bounded retry behavior, not rapid oscillation.

Fallback snapshots are built and validated before an outage, with local HTML/styles/fonts/optimized responsive images and no dependency on the original site to render essential content. Database-backed interactions are replaced by theme-matched unavailability content or an explicitly independent service. Snapshot build failure retains the last good published release. Resource limits and retained releases prevent builders/backups from exhausting the public serving edge.

Failure acceptance matrix: loss of app, one remote node, VPN, Coolify controller or builder must not break unrelated apps or local standby; controller loss must preserve healthy serving. Manual maintenance and stable recovery must be tested. Serving a static standby preserves public content, not database transactions. A single public edge remains a host/provider failure point; independent second-edge/static replication is a later resilience extension, not already-proven high availability.

## Planned maintenance windows

Operator additionally requests scheduled maintenance announcements: choose affected apps (or an explicit platform-wide set), start/end with timezone, notice and theme-matched contact-only standby. Display times in Europe/Prague and store canonical UTC instants; validate daylight-saving ambiguity. Show the published fallback preview and disabled dynamic routes before confirming a window. Contact details remain locally available; an interactive form is available only through a separately independent configured service.

At the start, select the already-validated standby release even if the backend remains healthy. Automatic health checks must not cancel active scheduled/manual maintenance. Block checkout/login/search/write routes consistently so a stale open form cannot bypass the maintenance page into the backend. Define explicitly how already-running requests are drained; never promise transaction preservation from the static mode.

At the planned end, resume only after actual application/dependency checks satisfy the stable-recovery policy. Otherwise retain standby and flag an overrun; allow extension, cancellation or explicit finish, with audit. Announced completion time must not imply successful recovery when health checks fail. Persist confirmed windows on the independent edge so a restart/controller/VPN outage does not erase the schedule; test overlapping windows and cross-app isolation.

Provide a previewable announcement for the operator to share, with affected sites, timezone, expected window and limited available functions. Automated email/messaging delivery is a separate explicitly configured feature; no messages have been sent. Historical/live status must distinguish PLANNED_MAINTENANCE, ACTIVE_MAINTENANCE, OVERRUN and RECOVERY rather than reporting a planned event as an incident.

## Recovery user flow

1. A fresh FallbackHosting installation offers New setup or Restore existing installation.
2. Operator provides the backup server SSH endpoint and a separately held technical identity. Independently verify host identity; private keys remain outside PHP/webroot. Discovery uses read-only permissions to explicitly selected backup roots, not arbitrary host-wide shell searches.
3. Discover a versioned backup catalog. Display backup kind, creation time, format/version, size, declared contents and last verified integrity/restore evidence. A catalog is untrusted input: bounded parsing, safe paths, no commands or executable restore hooks supplied by the repository.
4. Verify actual archive existence, completeness, checksums and trusted provenance/authenticity. Do not execute manifests or restore merely because a file exists. Encrypted backups additionally require separately recoverable decryption material; an SSH key alone does not decrypt them.
5. Operator selects a recovery point and exact target. Present what will be replaced. Stage/validate first and restore into an isolated destination where possible; a live overwrite needs explicit scope and rollback.
6. Recover controller configuration, inventory, application/domain mappings and required private secrets with original protection. Recover Coolify database and matching encryption/configuration material together. Application databases and persistent files are separate recovery components and must not be inferred from the controller backup.
7. Check application-specific health and restored data before promotion; keep static standby available. A discovered backup is FOUND, a checksum check establishes INTEGRITY_VERIFIED, and recoverability becomes RESTORE_TESTED only after an evidenced restore test.

## Backup locations and failure cases

A remote selfhosted node is an allowed backup location for public-controller recovery. Backups should be structured/cataloged so a replacement public node can discover them without needing the lost controller database. The bootstrap SSH identity, host verification and encryption recovery material must be obtainable independently of that database.

Static standby releases remain locally on the public edge for immediate outage serving; archival copies can also be stored remotely. If the only backup node is unavailable, recovery from it is unavailable until it returns. If the same node holds applications and their only backups, loss of that node can lose both; track an independent copy separately rather than labeling that arrangement resilient.

This is not a claim of automatic cross-version recovery, support for arbitrary Linux distributions or existing Coolify backup formats. Format/version compatibility, archive extraction safeguards, ownership/secret restoration, retention and actual restore drills require implementation and evidence.

## Next engineering increment

Implement a repository-local backup-catalog/discovery and restore-plan prototype using fixtures: reject malformed/missing/unsafe archives and incompatible versions; distinguish evidence levels; produce a concrete restore preview without any network execution or live writes. Separately prepare public-controller resource/dependency/canary/migration/rollback plan before proposing exact operational changes. No runtime migration or restore approval is requested by this planning step.
