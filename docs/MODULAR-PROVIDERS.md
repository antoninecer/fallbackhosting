# Modular infrastructure and reuse of existing systems

2026-10-15. Operator accepted the application-access design and requested Docker/VM/backup modularity including ordinary Linux with KVM. This records the accepted direction, not approval of unspecified infrastructure commands. FH-0004 TESTING; provider planning exists locally, real adapters NOT_IMPLEMENTED.

## Separate responsibilities

| Layer | Reused existing system | Responsibility | Current state |
| --- | --- | --- | --- |
| Application deployment | Coolify with Docker Engine/Compose | Application builds/deployments and runtime management | Planned integration; Coolify not installed or validated by this work |
| Virtualization on Proxmox | Proxmox native API and backup system | Explicitly authorized VM lifecycle and backup jobs | Future adapter, not contacted |
| Virtualization on ordinary Linux | libvirt API with QEMU/KVM | Same platform-level VM workflow using native host capabilities | Future adapter, not installed/contacted |
| App data backup | Existing backup tool selected after storage/consistency audit | DB-native export plus approved data backup/retention/offsite policy | Tool selection and coverage remain pending |
| Identity and authorization | Maintained identity/WebAuthn components + scoped platform policy | Personal accounts, application membership, revocation and operation authorization | Accepted security design, not deployed |
| Standby and public project | Independent Oracle static serving | Versioned safe standby/public progress without home control plane | Existing public progress live; broader standby planned |

We are not building a replacement hypervisor or deployment product. A narrow platform integration coordinates existing products and enforces project/operation boundaries. Docker runtime, deployment control plane and hypervisor are different entities. Metadata saying “VM” does not grant host API access.

## Supported topology directions

- Current demonstration: Proxmox → LXC → Docker. Keep existing workloads; this change does not create/migrate/restart anything.
- Stronger isolation: Proxmox → QEMU/KVM VM → Docker, with VM per trust boundary or sensitive application.
- Portable alternative: ordinary Linux → libvirt/QEMU/KVM VM → Docker.
- Simple trusted deployment: ordinary Linux → Docker; no hypervisor provider required.

The same application workflow addresses a registered Docker application node regardless of its substrate. Provisioning a new VM is a separate administrator workflow targeting a registered virtualization host. It must never attempt nested virtualization inside the existing LXC simply because Docker is there. Native KVM capability, installed libvirt, versions, quotas and storage/network availability must be verified independently on a candidate host.

## Backups and recovery

VM creation, a VM snapshot, a durable backup and a standby website are distinct operations. A backup VM can be provisioned from an approved template to host an existing backup service, but a VM on the same hardware/storage is not an external copy. An isolated temporary VM may be used for restore testing; it starts without production network identity, credentials or publication. Never overwrite a registered production resource during validation.

Proxmox uses native backup semantics. A libvirt integration should use the supported backup API where compatible; it must check host versions and storage features rather than silently emulate it with arbitrary shell or copy a live disk file. Guest/application consistency, all disks/volumes/bind mounts, metadata and required secrets recovery must be assessed. Provider job completion, archive integrity, external copy and successful application restore are separate dated records. Current operator-attested LXC backup/integrity remain VERIFIED; restore NOT_TESTED and external copy NOT_DOCUMENTED.

A VM-level backup does not automatically cover external application storage or guarantee database consistency. Database-native backup and restore validation may still be required. No snapshot/backup procedure is executed by this work.

## Local provider contract and security

`operations/planning.py` implements an OFFLINE_PLAN_ONLY selector for trusted target inventory. `application_node/coolify-docker` offers deployment planning. `virtualization_host/proxmox` and `virtualization_host/libvirt-kvm` offer VM provisioning/backup/restore planning. The output always states driver NOT_IMPLEMENTED and execution_allowed=false. It is not an authorization decision, worker, remote API or existing PHP integration.

The request has only action, target and opaque resource ID. Provider choice comes from trusted policy, never the caller. Unknown providers, duplicate targets, unsupported operations and cross-layer requests fail closed; there is no automatic fallback to another host/provider. Future adapters expose explicit capability/version checks and bounded typed requests/results, protected credential references, idempotent jobs, ownership registry and UNKNOWN reconciliation. No user-supplied XML, command, Compose, URI, storage path or root credentials.

Hypervisor credentials must be separate from Docker and identity credentials. Application managers never receive hypervisor permissions. Avoid global administrator API tokens; prove a restricted identity can access only the approved resource set, or refuse integration when the backend cannot enforce the required boundary. Existing exact broker write approval remains mandatory; planning grants nothing.

Coolify is an existing deployment component, not proof of least-privilege execution. Its documented non-root mode still has root-equivalent sudo. It must be treated as a privileged controller in an isolated management boundary, without PVE access. The operator's 2026-10-16 clarification selects the public-IP node for the controller; `docs/PUBLIC-CONTROLLER-RECOVERY.md` supersedes the earlier preference against shared-edge placement. Exact deployment still requires a reviewed resource/isolation/migration plan protecting existing sites and keeping static serving independent of Docker. Mapping application roles to actual upstream API scopes and preventing confused-deputy access require negative tests before delegation. No claims of rootless-Coolify compatibility are made.

## Acceptance and next steps

Five local planning tests PASS: Docker without hypervisor, explicit Proxmox/libvirt selection, wrong-layer/unknown target/provider injection rejection, isolated restore gates and invalid inventory. These are logical fixture checks, not hypervisor/backup/deployment validation.

Next: implement and test the accepted application role and revocation policy locally; then verify a chosen existing deployment product's API scope against it. Real driver selection/installation comes after bounded read-only host capability evidence and a concrete reviewed action/target/rollback. No PVE/libvirt endpoint or credential is currently needed from the operator for local work. No changes to existing production Nginx, PHP, certificates, routing or DNS.

Rollback: reviewed repository revert and public projection rebuild; no resources or operational config were created here. Existing broker and live inventory formats are unchanged.

## Primary sources checked 2026-10-15

- [Coolify model](https://coolify.io/docs/core/what-is-coolify): existing Docker deployment control plane.
- [Coolify non-root account](https://coolify.io/docs/core/infrastructure/servers/non-root-user): still requires unrestricted sudo; isolation must not be assumed from username.
- [libvirt QEMU/KVM driver](https://libvirt.org/drvqemu.html): native hypervisor integration on Linux.
- [libvirt backup API guidance](https://libvirt.org/kbase/live_full_disk_backup.html): supported backup path and version-dependent behavior.
- [Proxmox backup guide](https://github.com/proxmox/pve-docs/blob/master/vzdump.adoc): existing VM/LXC backup system and backup destinations.

The adapter boundaries, role policy and topology choices are project design decisions; these sources do not certify our implementation.

## Existing-product authorization fit

Official [Coolify team roles](https://coolify.io/docs/core/team/roles-and-permissions) were checked: team Admin/Owner combine deploy/operate with deletion and terminal capabilities; Member is broadly read-only. Those native roles must not be presented as our narrower per-application manager. Do not enroll an application-only manager as a Coolify team Admin to make deployment work. Keep upstream administration restricted to trusted operators and mediate narrowly scoped app requests, with verified current resource ownership. Whether the chosen API credential and deployment architecture can enforce the accepted boundary remains NEEDS_TEST; no compatibility or security certification is implied.
