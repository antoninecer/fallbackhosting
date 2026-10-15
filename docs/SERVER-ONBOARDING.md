# Server onboarding — design and first safe step

2026-10-15, operator requested this as part of first platform setup. Status: onboarding design; operator has since provisioned technical SSH transport. Agent performed the explicitly requested identity/uptime and Docker access diagnostics; no account/key/permission/service changes or Coolify installation performed by agent.

## Intended node

The operator's intended deployment target is ctx1, historically LXC 102 on home Proxmox, Rocky Linux 9.8 with Docker/Compose. Those identity/OS/resource claims need live verification. Home test HTTP was rechecked successfully from Oracle. Operator-provisioned technical SSH accounts/key now work: agent hostname, effective-user and uptime probes passed at 2026-10-15T08:25:31Z under existing strict host trust. Independent fingerprint attestation still pending. Proxmox access is not required or authorized for this step.

The deployment control plane remains planned on home infrastructure per ARCHITECTURE.md. Oracle independently hosts the gateway, snapshots and project progress page. Do not conflate an agent's audit key on Oracle with the eventual deployment controller's automation key: choose the controller location and approved privilege model before creating or distributing keys. There is no Coolify service confirmed on either node.

## First-run administrator workflow (planned UI)

1. Secure first administrator and authentication before any public setup screen.
2. Add server: friendly name, intended role (build/deploy/both), operator-declared type (LXC/VM/bare metal), address, SSH port, dedicated username, selected secret-key reference. These connection details are authenticated private inventory, never public progress-page data.
3. Display/copy public key, with explicit operator authorization to add it for the dedicated server account. Generate private key only in an approved protected secret store outside Git/webroot; never send it in chat, logs or browser downloads. Do not use shared personal keys. Plan revocation/rotation and backups.
4. Verify server SSH host-key fingerprint using an independently trusted console/operator source, then pin it. Do not auto-trust ssh-keyscan output or disable StrictHostKeyChecking. Unknown/changed fingerprint stops connection.
5. Explicit read-only connection test first: OS/release, architecture, virtualization, CPU/RAM/disk, Docker/Compose versions and permissions, service state. Record observed UTC, method and UNKNOWN values separately from declared metadata.
6. Show compatibility, planned operations, privilege implications, affected existing containers and rollback. Only after scoped approval run software setup, proxy start or Docker operations. A UI button labeled validation must not conceal installation/restarts.
7. Mark ready for deployment only after actual authorized tests. User accounts later receive project roles, not server shell access or access to the infrastructure key.

## Verified documentation implications

Official docs reviewed 2026-10-15:

- [Coolify Add Server](https://coolify.io/docs/core/infrastructure/servers/add-server): SSH key authorization and server connection fields; its server validation can install Docker, restart Docker and start a proxy. It is NOT a read-only audit and must not be run under read-only approval.
- [Coolify Non-root User](https://coolify.io/docs/core/infrastructure/servers/non-root-user): non-root support is described as experimental and still requires unrestricted passwordless sudo. A non-root username does not establish least privilege. This needs explicit architecture/security review and exact operator approval; do not configure it automatically.
- [Coolify self-hosted prerequisites](https://coolify.io/docs/start-with-self-hosted): Rocky is listed; published minimum is 2 CPU cores, 2 GB RAM, 10 GB free disk for Coolify itself, with extra capacity for applications/builds. This does not prove compatibility of the specific nested LXC or workload capacity.
- [Docker Linux post-installation](https://docs.docker.com/engine/install/linux-postinstall/): Docker group membership grants root-level privileges. Do not propose it as a restricted inspection account.

No change to the planned Coolify architecture is made here. If the required privilege model conflicts with project least-privilege constraints, document alternatives and request human architecture review before installation. No root SSH enablement, firewall changes or service restarts are authorized by this design.

## Current access evidence and next gate

Technical accounts and key access already exist per operator, with subsequent agent transport verification. Exact private connection details remain in operator custody; no additional credentials should be sent in chat or Git. Operator subsequently granted Docker-group membership and agent verified an isolated lifecycle test; no rights changed by agent. Destination sudo absence remains operator-reported. Do not grant more rights, recreate accounts/keys, or run installation. Independent console fingerprint comparison is the next gate.

`scripts/inspect-node.sh` is intended to be copied/reviewed and run locally on ctx1 by the operator. It reads only selected OS/resources/version/service values, does not list apps/containers or read configs/secrets, and marks denied Docker access UNKNOWN. It was syntax-checked in the repository, not executed on ctx1. Return only sanitized results through a private operator channel if needed.

Next exact gate: independently compare the actual negotiated host-key fingerprint using trusted target console evidence, then review docs/SSH-OPERATIONS-SERVICE.md. No guessed usernames or new SSH methods used. Current agent unrestricted sudo means actual key isolation is not yet enforced; do not claim a separate Unix account alone protects the key from this agent. No permissions changed.

## Earlier Docker diagnostic — historical denial

Operator requested a disposable Docker create/delete probe. Agent confirmed /usr/bin/docker exists but daemon query returned socket permission denied (exit 1); therefore no resource was created or deleted. Current daemon version/health remains UNKNOWN. This is an observed permission blocker; do not re-run as root, add Docker-group membership or grant sudo without exact operator approval. Any constrained test helper is a proposal only in docs/SSH-OPERATIONS-SERVICE.md.

## Current Docker diagnostic — success after operator grant

Operator added technical account to Docker group, then requested retest. Fresh SSH session observed membership and Docker Engine 29.9.0. Isolated creation/start/exit-0/removal and absence passed; pre-existing reference unchanged and HTTP pre/post canaries passed. Evidence: docs/DOCKER-SMOKE-TEST.md. Earlier denial is superseded; independent fingerprint, node OS/resource inventory and least-privilege/controller review remain pending.
