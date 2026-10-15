# Current project state

Updated 2026-10-15T09:04:58Z, Codex. Observations are point-in-time, not live monitoring.

## Milestones

- M00 DONE, locally committed. No automatic push authorized.
- M01 NEEDS_TEST: initial read-only audit; complete home inventory, external application baseline, dependency/backups and failure testing incomplete.
- M02 IN_PROGRESS: https://project.lab.ventureout.cz/ is LIVE as sanitized public progress presentation; private server-inventory admin locally implemented/tested with ctx1 seed and secured initial admin, not publicly deployed; broader center modules remain planned. FH-0009 TESTING pending browser/mobile/filter QA. Operator said the page looks good, but device sizes and interaction coverage were not specified.
- M03 PLANNED: operator requested next-phase server onboarding. Design and bounded inventory script prepared; technical SSH access provisioned/tested by operator and subsequently verified by agent. No Coolify or agent-performed remote account/key/permission changes.

## Verified runtime changes

Operator approved the exact project-domain deployment and existing Certbot use. Dedicated vhost/symlink, Certbot webroot certificate and two nginx -t gated reloads completed. Certificate expires 2027-01-13. Private backup and config hash manifest: /var/backups/fallbackhosting-project-20261015 (outside Git/webroot). All 22 pre-existing regular Nginx config hashes unchanged. Existing protocol-options warnings predate changes.

HTTPS page/CSS/JS, correct domain TLS, CSP, redirect and six source/unknown-path denials passed. Reference Quantum route/TLS/two static assets passed before/after; six other root probes matched prior status/type/final URL, including pre-existing 404/502. Home test HTTP remained 200. During gateway activation no DNS/firewall/SSH/Tailscale/home/container/app changes were made. Subsequent authorized Docker diagnostic created/removed only its temporary container as recorded below. No push.

Certbot renewal webroot and active timer observed; renewal dry-run and future successful renewal not tested. No project per-certificate deploy/renew hook and zero global deploy-hook files found: automatic Nginx certificate reload after renewal remains unconfigured/unverified (FH-0012); no hook/timer changed. First immediate probe after asynchronous reload saw old certificate; subsequent full checks passed without another reload. External web tool could not fetch site; successful ACME validation provides external challenge evidence, not full external application verification. No fault injection performed.

## Lab entry and platform design

lab.ventureout.cz is intended actual platform; authenticated multi-node PHP inventory app now prepared locally, not activated. New dedicated web-account/FPM/vhost deployment scope in docs/ADMIN-ACTIVATION.md supersedes static-only lab proposal. Future workflow: admin creates invited users/projects/subdomains; users manage assigned home-node applications and configure standby contacts. See docs/PLATFORM-WORKFLOW.md.

Target ctx1 remains historically LXC 102 / Rocky Linux 9.8; actual OS/resources still need verification. SSH probes passed at 08:25:31Z. Earlier Docker denial is historical: operator subsequently added the technical account to Docker group. In a new strict SSH session agent observed membership and Docker Engine 29.9.0, then created/started/deleted one isolated owned container successfully. Evidence recorded 2026-10-15T08:35:47Z; docs/DOCKER-SMOKE-TEST.md and checkpoint checkpoints/20261015T083547Z-FH-0016-docker-smoke-pass.md. Exit 0, exact cleanup/absence verified; known reference container ID/running/start time/restart count/image unchanged. Existing image reused, no pull, network/ports/mounts/volumes, no existing workload modified. Agent granted no rights; operator did. Remote sudo remains absent per prior operator report and not independently tested.

Independent SSH fingerprint remains NEEDS_TEST. Broker/service not installed. Docker-group access is broad and does not establish per-project authorization or isolation from a root-capable agent. Key used only through owner process; never read/copied/exported. Private connection mapping/key path remain outside public Git; private server inventory now exists in ignored .local/admin/inventory.json (no technical key path or key mapping). No Proxmox access assumed; historical EFI warning still unresolved.

## Next exact step

FH-0017: review and approve exact admin activation scope in docs/ADMIN-ACTIVATION.md, then secure isolated runtime, verify HTTPS/auth/private config and protected-site canaries. Local PHP admin and ctx1 config are ready; initial unique admin credential is private, not in chat/Git/webroot. No active public admin yet. Independent fingerprint (FH-0014), full node inventory, broker/agent privilege boundary and Coolify remain separate gates; saving node metadata performs no remote action.

Evidence: latest checkpoints, docs/PORTAL-DEPLOYMENT.md, docs/SERVER-ONBOARDING.md, docs/M01-AUDIT.md. Associated revision is the containing commit; inspect Git before resuming.

## Evidence provenance

Operator report: technical SSH setup, initially absent destination sudo/Docker permissions, then explicit Docker-group grant and requested retest; operator action time not supplied. Agent verified effective group/API access and complete test cleanup afterward. Agent observation: three transport probes at 2026-10-15T08:25:31Z and read-only local sudo capability check this turn. Neither successful SSH nor cached host trust proves independent host identity. Broker design is PROPOSED only: docs/SSH-OPERATIONS-SERVICE.md. Public exports retain only reviewed task labels/statuses and checkpoint metadata.

## Multi-node admin local verification

Thirteen tests PASS (eight PHP admin HTTP/concurrency tests, five public-export tests), PHP syntax checks PASS, actual seeded admin loopback login/list(ctx1 Docker/LXC/prior timestamps)/logout PASS without inventory mutation. Temporary test servers stopped. No screenshots/browser visual QA available; no live pool/vhost/cert/account changes. Private JSON 0700/0600, initial credential securely generated and not printed, auth uses Argon2id hash. Inventory one gateway/multiple nodes is a reviewable extension of existing home-node pattern, not a replacement for Coolify or fallback architecture. Docs: MULTI-NODE-ADMIN.md and ADMIN-ACTIVATION.md.
