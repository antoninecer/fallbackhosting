# Current project state

Updated 2026-10-15T08:32:51Z, Codex. Observations are point-in-time, not live monitoring.

## Milestones

- M00 DONE, locally committed. No automatic push authorized.
- M01 NEEDS_TEST: initial read-only audit; complete home inventory, external application baseline, dependency/backups and failure testing incomplete.
- M02 IN_PROGRESS: https://project.lab.ventureout.cz/ is LIVE as sanitized public progress presentation; protected administrative center remains planned. FH-0009 TESTING pending browser/mobile/filter QA. Operator said the page looks good, but device sizes and interaction coverage were not specified.
- M03 PLANNED: operator requested next-phase server onboarding. Design and bounded inventory script prepared; technical SSH access provisioned/tested by operator and subsequently verified by agent. No Coolify or agent-performed remote account/key/permission changes.

## Verified runtime changes

Operator approved the exact project-domain deployment and existing Certbot use. Dedicated vhost/symlink, Certbot webroot certificate and two nginx -t gated reloads completed. Certificate expires 2027-01-13. Private backup and config hash manifest: /var/backups/fallbackhosting-project-20261015 (outside Git/webroot). All 22 pre-existing regular Nginx config hashes unchanged. Existing protocol-options warnings predate changes.

HTTPS page/CSS/JS, correct domain TLS, CSP, redirect and six source/unknown-path denials passed. Reference Quantum route/TLS/two static assets passed before/after; six other root probes matched prior status/type/final URL, including pre-existing 404/502. Home test HTTP remained 200. No DNS/firewall/SSH/Tailscale/home/container/app changes. No push.

Certbot renewal webroot and active timer observed; renewal dry-run and future successful renewal not tested. No project per-certificate deploy/renew hook and zero global deploy-hook files found: automatic Nginx certificate reload after renewal remains unconfigured/unverified (FH-0012); no hook/timer changed. First immediate probe after asynchronous reload saw old certificate; subsequent full checks passed without another reload. External web tool could not fetch site; successful ACME validation provides external challenge evidence, not full external application verification. No fault injection performed.

## Lab entry and platform design

lab.ventureout.cz is intended actual platform; local introductory page/templates built, not activated. Exact lab gateway approval pending in docs/LAB-DEPLOYMENT.md. Future workflow: admin creates invited users/projects/subdomains; users manage assigned home-node applications and configure standby contacts. See docs/PLATFORM-WORKFLOW.md.

Target ctx1 is historically LXC 102 / Rocky Linux 9.8 / Docker; actual OS/resources and Docker management remain unverified. Existing technical accounts/key-based SSH were reported operational by operator, then three bounded agent SSH probes passed at 2026-10-15T08:25:31Z: hostname, effective user and uptime. Strict existing host trust passed; independently sourced fingerprint remains NEEDS_TEST (FH-0014). Destination has no sudo/Docker permissions per operator. Agent subsequently found Docker CLI but its daemon-version query was denied at the standard socket (exit 1); no container could be created and no cleanup was needed. Docker daemon version/health remains UNKNOWN. Sudo privilege absence was not independently tested. No rights changed. Private key remains owned/used by technical account; Codex did not read/copy/export it. Private address, exact key path and connection mapping are intentionally not in public Git; operator private inventory storage location remains UNKNOWN and must be supplied securely on future resume. No Proxmox access assumed. EFI GRUB warning remains historical and unresolved; review before any PVE reboot.

## Next exact step

FH-0014: obtain independently sourced host fingerprint through the trusted ctx1 console and compare with existing client trust privately; no automatic known_hosts changes. Review FH-0013 service proposal and FH-0015 agent isolation plan before activation. Existing agent account has unrestricted passwordless sudo and Docker-group membership; filesystem-only key separation does not enforce exclusion from Codex. No restriction, service or permission change made. Explicit Docker create/delete diagnostic was blocked at daemon-access prerequisite, with zero resources created. Review a constrained smoke-test helper separately; remote sudo/Docker grants remain forbidden without explicit approval. Coolify validation is mutating; do not run under audit permission. Lab activation separately awaits exact approval. Broader FH-0006 schema and private portal work remain queued.

Evidence: latest checkpoints, docs/PORTAL-DEPLOYMENT.md, docs/SERVER-ONBOARDING.md, docs/M01-AUDIT.md. Associated revision is the containing commit; inspect Git before resuming.

## Evidence provenance

Operator report: technical SSH setup and absent destination sudo/Docker permissions; exact operator test UTC not supplied. Agent observation: three transport probes at 2026-10-15T08:25:31Z and read-only local sudo capability check this turn. Neither successful SSH nor cached host trust proves independent host identity. Broker design is PROPOSED only: docs/SSH-OPERATIONS-SERVICE.md. Public exports retain only reviewed task labels/statuses and checkpoint metadata.
