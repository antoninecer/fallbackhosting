# Server onboarding — design and first safe step

2026-10-15, operator requested this as part of first platform setup. Status: design only; no ctx1 account/key/SSH/service changes or Coolify installation performed.

## Intended node

The operator's intended deployment target is ctx1, historically LXC 102 on home Proxmox, Rocky Linux 9.8 with Docker/Compose. Those identity/OS/resource claims need live verification. Only the historical home test HTTP endpoint was rechecked successfully from Oracle. No SSH account or usable key has been confirmed. Proxmox access is not required or authorized for this step.

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

## Needed from operator now

Confirm whether a dedicated SSH account already exists, its username/SSH port and whether Oracle already has authorized key access. Do not send passwords/private keys or complete confidential inventory. If no account exists, first use the existing ctx1 console to run the bounded read-only inventory below; do not create an account, install software or grant sudo/Docker membership yet.

`scripts/inspect-node.sh` is intended to be copied/reviewed and run locally on ctx1 by the operator. It reads only selected OS/resources/version/service values, does not list apps/containers or read configs/secrets, and marks denied Docker access UNKNOWN. It was syntax-checked in the repository, not executed on ctx1. Return only sanitized results through a private operator channel if needed.

Next exact gate: inspect actual ctx1 state and approve an exact account/key/known-host provisioning plan with rollback. No remote login attempts using guessed usernames and no new SSH methods have been made.
