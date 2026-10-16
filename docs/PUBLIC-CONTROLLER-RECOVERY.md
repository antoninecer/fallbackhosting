# Public control plane and SSH-discovered recovery

Operator-directed target architecture, 2026-10-16. This supersedes the preferred home-node controller placement; it does not authorize an unreviewed live migration.

## Placement and independence

The public-IP node hosts the FallbackHosting administration/control plane and the intended central Coolify controller. Remote physical/VM/Docker-capable LXC Linux nodes host application workloads. One controller manages multiple nodes. Public IP placement does not imply anonymously accessible administration.

The existing Oracle gateway remains the independent public edge. Its current Nginx sites, approved static standby releases and public project presentation must continue serving without Docker, Coolify, the remote application node or the SSH recovery service. Running a Docker-based controller on the same public machine must not turn Docker into a dependency of static serving. Resource/storage limits and narrow service/config boundaries are required in the migration plan.

OBSERVED current state: Coolify still runs privately on ctx1; public-node controller placement is a target, not a completed deployment. No live placement changes are made by this document.

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
