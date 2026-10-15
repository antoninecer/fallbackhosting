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
