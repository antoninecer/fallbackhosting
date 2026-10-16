# Web-managed incremental application migration — accepted scope

Operator clarification, 2026-10-16. Target for the first supported end-to-end demonstration: 2026-10-17 (Europe/Prague). This is a delivery target, not evidence of implemented functionality. The independent public gateway and existing unrelated production remain.

## User result

An operator such as Aleš manages source VPS nodes and destination home Linux nodes through FallbackHosting's authenticated web console. The console lists applications, their own hostnames, source/current/destination nodes, database/file dependencies, migration progress, backup/standby evidence and rollback options. Coolify is an internal deployment adapter; its installer is not the application dashboard.

Register both existing VPS and destination home server. Move applications one at a time while all other applications continue running. On the selected target MySQL service, each application receives a distinct database and separate account with access only to that application's database. A shared database server is a separately owned dependency, never an app-owned disposable container.

Every published application owns an entire hostname, initially <application>.lab.ventureout.cz, and all its paths. No application prefix under lab.ventureout.cz is part of the product model. The current /demo/ proof is a legacy test route to migrate, not the target routing model. Wildcard DNS does not establish wildcard TLS: observed DNS resolves arbitrary lab names, but only dedicated lab/project certificates were found. Hostname enrollment must validate routing and provision/test the required certificate before publication.

## First supported workflow

### Production source and capacity-aware destination — operator clarification

The operator has an additional server already running production Docker workloads. Register it as an existing production source, distinct from a fresh destination. Source discovery must not install Docker/Coolify/monitoring agents, initialize the node, restart/recreate containers, stop writers or change configuration. Initial access instructions must distinguish reusing existing access from provisioning a fresh target; do not apply the fresh-node administrative bootstrap blindly to production. This is an accepted requirement, not a claim that the source discovery UI/adapter is deployed.

Discover bounded selected metadata: containers including stopped applications, Compose/project grouping when available, image IDs/digests and architecture, mounts/volumes/bind paths, ports, restart/health state, configured CPU/RAM/PID limits, filesystem capacity/free space and inodes on actual Docker/data/export filesystems. Discover database/shared-service ownership and required configuration privately. Never publish raw Docker inspect output: environments, labels, command arguments and mounts can contain secrets. Missing Compose files, external storage and shared dependencies are explicit unknowns.

For each candidate destination, measure current workloads, architecture/runtime compatibility, CPU/RAM capacity and available resources, storage capacity/inodes on the actual target filesystems and existing reservations. Account for selected application data, database restore, staging archives, image extraction, rollback retention and safety headroom; do not equate the free space of /var with capacity of every volume. Avoid double-counting shared images/data; show uncertain size estimates. The gateway's independent standby role does not make it an application migration target.

Show instantaneous utilization, configured limits and observed historical peaks as separate values, with timestamps, units, sample interval/window and provenance. Docker current stats do not establish a historical maximum, a resource limit or a guarantee of future demand. Read existing telemetry when available; absent history stays UNKNOWN. A bounded approved sampling period can establish an observed peak for its window, never an all-time maximum. Shared database and host overhead contribute to sizing; missing limits do not mean zero usage.

Recommend a destination from measured candidates, with a human-readable explanation of compatibility, usable disk/RAM/CPU headroom, reservations and uncertainties. No destination is selected as safe from stale or missing critical measurements. If no candidate fits, show the unmet requirements rather than initiating a transfer. The operator reviews the concrete app, source and destination before any copy/restore.

Transfer means application files/configuration plus a consistent database-native backup and required image references/portable images, not copying a running Docker data directory or archiving a live shared MySQL volume. Archives and secrets travel/stay privately, with integrity/readback checks. Start only an isolated copy, suppress duplicated workers/cron/mail/payment side effects and use a test hostname. Source cutover/write freeze and source deletion remain separate explicit operations under the workflow below.

Acceptance: discovery makes no production changes; source inventory and metrics distinguish facts/unknowns; target recommendation accounts for existing workloads and real storage paths; insufficient/unknown capacity blocks unattended transfer; selected app restores with verified data while source and unrelated apps continue serving. The additional production source's identity/access and its actual apps, size and historical peaks are currently UNKNOWN.

1. Connect/register two nodes, verify identity, reachability, supported OS/runtime and capacity. Initial enrollment may require one operator bootstrap action; normal ongoing management uses the web console.
2. Discover supported applications on the source using a bounded read-only adapter. Select an application and show its containers/Compose identity, image/template, volumes, database and shared dependencies. Unknown/unreadable dependencies block migration explicitly.
3. Select destination, dedicated production/test hostnames and an existing or newly provisioned shared target MySQL instance. Prepare only the selected app, with unique target database/account and private credential custody.
4. Create a consistent app-scoped native DB backup plus required file/configuration backup; verify readback and restore into an isolated destination. Do not copy the whole shared MySQL data directory or other apps' databases.
5. Start the destination on its test hostname. Verify meaningful app reads and bounded test writes, persistence and cross-database access denial. Source production continues serving.
6. Export only approved public routes into a self-contained passive static mini-site. Remove login/order/write operations; preserve useful content/theme/contact. Independently back up, preview and publish it on the public edge before cutover.
7. Announce a maintenance window, stop source writes, perform/verify the final DB/file synchronization, then switch the production hostname. Source and target must not accept divergent writes. Record the precise recovery point.
8. Observe stable destination health including DB-dependent actions, and exercise automatic/manual standby. Static serving survives loss of either source or target, VPN, deployment controller and backup repository.
9. Keep the old installation or explicitly remove only that app's source resources after accepted migration and verified retained backup. Source cleanup is a separate confirmation naming the application and server. Never remove shared MySQL or shared volumes while another app depends on them.
10. A VPS becomes eligible for retirement only when application/dependency inventory is empty and backups/recovery are verified. No automatic provider cancellation or whole-server deletion.

Rollback must account for data written after cutover. Switching back to an old stale database is not a safe rollback. The console must either preserve the write freeze until acceptance or complete verified reverse synchronization before returning writers to the old source. Interrupted/unknown operations are reconciled, never silently replayed.

## Tomorrow acceptance — real, bounded demonstration

- Two actually reachable registered nodes, one supported Docker+MySQL application plus a second app proving shared-service isolation; no invented source VPS access.
- Web-driven source/app/target/hostname selection and visible durable operation/result states. No requirement to type Docker, SQL, SSH or Nginx commands for normal migration.
- Verified distinct DB accounts, cross-DB denial, app-scoped backup/restore with meaningful data, file persistence and unrelated-app preservation.
- Isolated test hostname before cutover; app production hostname serves at root with verified HTTPS/assets/routes and safe dynamic action.
- Actual independent static fallback, controlled target outage, stable recovery and tested app-level rollback with documented write consistency.
- Optional exact-app source cleanup tested only on owned disposable fixtures, with shared MySQL and the second app preserved.
- UI recognizes completed Coolify installation and does not request another first account. Dashboard distinguishes deployed/read-only-observed/planned/unknown.

A planning mock, a green progress label, a controller login or a generic 200 is not this acceptance. Unsupported applications are identified honestly. General arbitrary-Compose migration, every MySQL/MariaDB version, multiuser delegated authorization and full hypervisor/controller disaster recovery are not implied by the first adapter.

## Observed prerequisites and current limits

ctx1 and the new test VM are now registered. The new VM's console-attested SSH identity, actual login, Rocky Linux 9.8, two CPUs, approximately 3.6 GiB RAM and available storage were verified; Docker is absent and initialization has not been requested. A further production Docker source is operator-reported, but no verified source access/application inventory has been supplied. Its resources, applications and historical load remain UNKNOWN.

Existing verified components: authenticated inventory/control center; owned stateless cafe demo; independent local static standby; manual/scheduled maintenance; authenticated backup-gated snapshot preview/publication/rollback; static archive discovery/readback/restore. General app import/migration, shared-MySQL lifecycle integration and production app subdomain enrollment remain implementation work.

Immediate work: correct application dashboard/completed-install UX, add hostname/source/target/dependency model, implement a bounded migration adapter with consistent durable jobs, then validate against the second VM and a selected real source. Keys/passwords/raw inventory stay out of public Git and progress exports.
