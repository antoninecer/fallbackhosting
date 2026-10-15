# Current project state

Updated 2026-10-15T08:03:33Z, Codex. Observations are point-in-time, not live monitoring.

## Milestones

- M00 DONE, locally committed. No automatic push authorized.
- M01 NEEDS_TEST: initial read-only audit; complete home inventory, external application baseline, dependency/backups and failure testing incomplete.
- M02 IN_PROGRESS: https://project.lab.ventureout.cz/ is LIVE as sanitized public progress presentation; protected administrative center remains planned. FH-0009 TESTING pending browser/mobile/filter QA. Operator said the page looks good, but device sizes and interaction coverage were not specified.
- M03 PLANNED: operator requested next-phase server onboarding. Design and bounded inventory script prepared; no Coolify, remote account/key setup or home changes performed.

## Verified runtime changes

Operator approved the exact project-domain deployment and existing Certbot use. Dedicated vhost/symlink, Certbot webroot certificate and two nginx -t gated reloads completed. Certificate expires 2027-01-13. Private backup and config hash manifest: /var/backups/fallbackhosting-project-20261015 (outside Git/webroot). All 22 pre-existing regular Nginx config hashes unchanged. Existing protocol-options warnings predate changes.

HTTPS page/CSS/JS, correct domain TLS, CSP, redirect and six source/unknown-path denials passed. Reference Quantum route/TLS/two static assets passed before/after; six other root probes matched prior status/type/final URL, including pre-existing 404/502. Home test HTTP remained 200. No DNS/firewall/SSH/Tailscale/home/container/app changes. No push.

Certbot renewal webroot and active timer observed; renewal dry-run and future successful renewal not tested. No project per-certificate deploy/renew hook and zero global deploy-hook files found: automatic Nginx certificate reload after renewal remains unconfigured/unverified (FH-0012); no hook/timer changed. First immediate probe after asynchronous reload saw old certificate; subsequent full checks passed without another reload. External web tool could not fetch site; successful ACME validation provides external challenge evidence, not full external application verification. No fault injection performed.

## Lab entry and platform design

lab.ventureout.cz is intended actual platform; local introductory page/templates built, not activated. Exact lab gateway approval pending in docs/LAB-DEPLOYMENT.md. Future workflow: admin creates invited users/projects/subdomains; users manage assigned home-node applications and configure standby contacts. See docs/PLATFORM-WORKFLOW.md.

Target ctx1 is historically LXC 102 / Rocky Linux 9.8 / Docker. SSH identity, account, port and keys unverified. No Proxmox access assumed. EFI GRUB warning remains historical and unresolved; review before any PVE reboot.

## Next exact step

FH-0011: obtain existing ctx1 SSH account/port/access information without credentials, or operator-run sanitized inventory from scripts/inspect-node.sh. Before any account/key/known-host or runtime change, prepare exact least-privilege plan and obtain scoped approval. Coolify validation is mutating; do not run under audit permission. Lab activation separately awaits exact approval. Broader FH-0006 schema and private portal work remain queued.

Evidence: latest checkpoints, docs/PORTAL-DEPLOYMENT.md, docs/SERVER-ONBOARDING.md, docs/M01-AUDIT.md. Associated revision is the containing commit; inspect Git before resuming.
