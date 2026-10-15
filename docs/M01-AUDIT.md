# M01 — read-only audit, Session 001

Verification window: 2026-10-15T07:06:50Z through 2026-10-15T07:12:54Z. Agent: Codex. Base revision: 3b5ea7b.
No infrastructure changes, installations, restarts, new access or fault injection.
This is a sanitized point-in-time inventory, not live monitoring or a complete private inventory.

## OBSERVED

| Area | Evidence / result |
| --- | --- |
| Oracle OS | uname -sm, /etc/os-release: Linux aarch64, Ubuntu 24.04.5 LTS |
| Resources | nproc: 2; free -m: 11925 MiB RAM, 5152 MiB available, no swap at sample |
| Disk | df -h / /opt/fallback: root 192G, 44G used, 149G available, 23% used |
| Services | systemctl is-active: nginx, tailscaled, docker, php8.3-fpm, mysql, redis-server and certbot.timer active; php8.1-fpm and mariadb inactive |
| Public listeners | ss -ltnH: wildcard HTTP/HTTPS and SSH listeners; additional wildcard listeners require private ownership/exposure review. Listening is not proof of internet reachability |
| Nginx structure | /etc/nginx has sites-enabled, sites-available, conf.d, snippets, modules directories; enabled symlinks include reference host and default. Included-file contents and all vhosts NOT audited |
| Application locations | Bounded top-level directory inspection found multiple application directories under /opt and /var/www/html. Names and private topology intentionally omitted; no application files read |
| TLS management | /etc/letsencrypt and renewal directory exist; certbot timer active with scheduled next run. Renewal success, full certificate coverage and permissions UNKNOWN |
| Reference baseline | curl safe GET: HTTP 200, TLS verification result 0, approximately 0.075 s from Oracle |
| Reference route/assets | Python urllib: final URL unchanged, 3842 HTML bytes; both discovered same-origin stylesheet/script returned HTTP 200 with CSS/JavaScript content types |
| Home reachability | curl safe GET of operator-provided home test URL: HTTP 200, approximately 0.072 s. Existing network path works at this instant; actual container identity and resource configuration not proven |
| Repository | clean main initially; resume succeeds; git ls-remote confirms remote main equals full local base revision 3b5ea7bc2d8c9fe11e45f6d8fca3f1230df86d58 |

## UNKNOWN / historical only

PVE version, LXC identity/OS/resources, Docker workloads on home, Coolify/Traefik deployment, DNS records, full Nginx include graph, firewall/OCI ingress, certificate renewal success and backups are UNVERIFIED. No SSH to PVE/ctx1 attempted; no new access created. Earlier PVE/LXC/Docker results remain historical. EFI GRUB warning remains historical and unresolved in this audit.

Full Quantum Random behavior, external-vantage availability and all application assets are unverified. No forms, writes or application actions were executed. Independence under home-node outage is NOT proven; no outage test authorized. Docker active on Oracle does not establish any FallbackHosting deployment.

## Risks and next steps

- Shared production host: active existing services and multiple app directories require exact isolation and resource limits before any deployment.
- Additional wildcard listeners need operator-led private exposure/ownership review; no vulnerability or external exposure inferred.
- No swap observed; assess capacity with representative measurements before allocating portal resources.
- Get independent external reference canary evidence; review authorized sanitized Nginx dependency/backup evidence before gateway changes.
- Obtain scoped home inventory access if required; do not infer host state from HTTP alone.
- Inspect DNS read-only before public deployment; no DNS changes.

## Canary and rollback policy

Use bounded GET with TLS verification to reference URL, assert expected route/content and selected static assets. Failure includes network/TLS error, unexpected redirect/content, non-200 or missing asset; HTTP 200 alone is insufficient. Dynamic behavior needs a separate safe test environment. Repeat baseline immediately before and after any future risk-bearing gateway work, including an independent vantage point. Retain measurements, not raw confidential responses.

This audit changed no runtime state; runtime rollback is unnecessary. Documentation rollback: reviewed Git revert. Future deployments require exact backup targets, tested restoration, nginx syntax check, unrelated-site canary, explicit scoped approval and narrow reload. These procedures have not been executed or validated as operational recovery.

M01 remains NEEDS_TEST: external baseline, dependency analysis and operational backup/rollback verification are outstanding.

## Correction — public presentation follow-up

2026-10-15: initial sites-enabled command enumerated only symbolic links. Subsequent read-only enumeration found regular vhost files as well. The original two-name list is incomplete and must not be used as production coverage. Existing site names/roots are intentionally not exported to the public presentation. No configuration was changed.

## Deployment baseline follow-up — 2026-10-15

Approved project presentation deployment repeated protected route/TLS/asset checks and sampled six other unrelated root URLs before/after. A pre-existing root probe returned 502, two returned 404; all sampled status/content-type/final-URL values were unchanged by deployment. Underlying application causes remain UNKNOWN and were not investigated or modified in this scope. This is a measured baseline, not a claim all production workflows are healthy. Full external app verification remains incomplete because web fetch tool was unavailable.

## Technical SSH evidence — 2026-10-15T08:25:31Z

After operator provisioning and explicit test authorization, agent performed bounded hostname/effective-user/uptime probes via existing technical Oracle identity: all exited 0 and identity values matched expected target/account. No private key contents accessed/copied, no account/permission/trust changes. StrictHostKeyChecking=yes and UpdateHostKeys=no used. Independent source fingerprint remains NEEDS_TEST, not proven by these probes. Remote absence of sudo/Docker permissions is operator-reported, not independently queried. OS/resources and Docker management remain unverified. Current local unrestricted sudo was observed, so file separation does not enforce exclusion of Codex from key-owner privileges.

Explicit subsequent Docker probe: CLI found at standard path, daemon-version query failed with socket permission denial. No resource create/delete test occurred and no remote sudo was used. This does not establish daemon health/version or existing workload inventory; no permission changed. See latest Docker-denied checkpoint for evidence-recorded UTC.

## Docker permission retest — supersedes earlier denial

Operator added target Docker-group membership and requested retest. Agent observed fresh-session group membership, Docker Engine 29.9.0, and successful isolated create/start/exit-0/remove with verified absence. Existing reference state and endpoint canaries unchanged. Agent changed no rights. Evidence recorded 2026-10-15T08:35:47Z; docs/DOCKER-SMOKE-TEST.md. This establishes tested lifecycle capability, not host identity, OS/resources, per-user isolation or Coolify readiness.

## Home inventory follow-up — 2026-10-15T11:36:16Z

OBSERVED through existing strict technical SSH, running tracked scripts/inspect-node.sh via stdin, exit 0: Rocky Linux 9.8, Linux x86_64, LXC virtualization, 3 CPUs, 8192 MiB RAM (8069 available), 2048 MiB swap (unused), root filesystem 98G/1.3G used/92G available. Docker service active; client/server 29.9.0; daemon reports 3 CPUs and 8589934592 memory bytes; Compose v5.6.0. No writes, installs, permission changes or workload mutations. PVE host version/container numeric ID remain historical, not inspected.

M01 is **partially verified**, not an untested infrastructure. Remaining audit gates: independent SSH identity attestation, external application canary, dependency and backup/rollback coverage. Controlled outage tests belong to M08; they do not need to be performed merely to close M01. Public wording now distinguishes partial verification from no evidence.

## Read-only refresh — 2026-10-15T15:01:59Z

Strict existing technical SSH PASS; Rocky 9.8/LXC/x86_64/3 CPUs/8 GiB RAM/2 GiB swap, Docker 29.9.0 and Compose 5.6.0 re-observed. Selected Docker/Tailscale/sshd active; firewalld inactive is a service observation only, not exposure proof. One running container by count. Oracle protected route/TLS/assets and frozen lab integrity verify PASS. No mutation. Independent fingerprint still requires trusted-console evidence; full backup/dependency and independent external app checks remain open. Latest checkpoint provides provenance; no private mapping exported.

## Independent identity verification — supersedes earlier missing-attestation gate

Operator supplied trusted hypervisor-console ED25519 attestation and explicitly approved VERIFIED status. Agent matched it privately against the existing client trust record and completed strict pinned-algorithm read-only SSH. Both private ctx1 inventory records updated with provenance, comparison timestamp, lock/revision/audit and private backups; fingerprint/endpoint are excluded from Git. Operator execution time was not supplied. M01 still needs full backup/dependency and independent external application coverage.

## Backup and integrity — operator attestation for 2026-10-15

Administrator confirms successful ctx1 LXC backup and successful zstd -t integrity test, with monthly automatic backup configured. Record backup/integrity VERIFIED with OPERATOR_ATTESTED provenance; agent did not execute these checks. Exact execution time and archive location were not supplied. Recoverability remains NOT TESTED and external copy NOT DOCUMENTED. This supersedes blanket missing-backup evidence, not remaining dependency/external application gates or restore/offsite verification.

## Scoped dependency follow-up — 2026-10-15T15:46:48Z

See docs/DEPENDENCY-AUDIT.md: selected project static and admin PHP dependencies are local; one home Docker bind mount observed, archive inclusion UNKNOWN. Operator backup/integrity VERIFIED; restore NOT TESTED/offsite NOT DOCUMENTED. FH-0002 TESTING, M01 NEEDS_TEST; no infrastructure changes.
