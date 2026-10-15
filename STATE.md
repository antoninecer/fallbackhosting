# Current project state

Updated 2026-10-15T14:24:49Z, Codex. Observations are point-in-time, not live monitoring.

## Milestones

- M00 DONE, locally committed. Git push explicitly authorized by operator.
- M01 NEEDS_TEST, partially verified: Oracle, SSH, Docker lifecycle/cleanup and home OS/resources/Compose observed. Independent SSH identity, external application baseline and dependency/backup coverage remain open. Controlled failure tests belong to M08.
- M02 IN_PROGRESS: https://project.lab.ventureout.cz/ is LIVE as sanitized public progress presentation; private server-inventory admin LIVE at https://lab.ventureout.cz/, ctx1 seeded and real HTTPS admin login/list/logout verified; broader center modules remain planned. FH-0009 browser QA now passed in headless Chromium at 360/768/1440, including screenshot inspection, keyboard scrolling and all filters; see follow-up checkpoint.
- M03 PLANNED: operator requested next-phase server onboarding. Design and bounded inventory script prepared; technical SSH access provisioned/tested by operator and subsequently verified by agent. No Coolify or agent-performed remote account/key/permission changes.

## Verified runtime changes

Operator approved the exact project-domain deployment and existing Certbot use. Dedicated vhost/symlink, Certbot webroot certificate and two nginx -t gated reloads completed. Certificate expires 2027-01-13. Private backup and config hash manifest: /var/backups/fallbackhosting-project-20261015 (outside Git/webroot). All 22 pre-existing regular Nginx config hashes unchanged. Existing protocol-options warnings predate changes.

HTTPS page/CSS/JS, correct domain TLS, CSP, redirect and six source/unknown-path denials passed. Reference Quantum route/TLS/two static assets passed before/after; six other root probes matched prior status/type/final URL, including pre-existing 404/502. Home test HTTP remained 200. During gateway activation no DNS/firewall/SSH/Tailscale/home/container/app changes were made. Subsequent authorized Docker diagnostic created/removed only its temporary container as recorded below. No push.

Certbot renewal webroot and active timer observed; renewal dry-run and future successful renewal not tested. No project per-certificate deploy/renew hook and zero global deploy-hook files found: automatic Nginx certificate reload after renewal remains unconfigured/unverified (FH-0012); no hook/timer changed. First immediate probe after asynchronous reload saw old certificate; subsequent full checks passed without another reload. External web tool could not fetch site; successful ACME validation provides external challenge evidence, not full external application verification. No fault injection performed.

## Lab entry and platform design

lab.ventureout.cz now hosts the authenticated multi-node PHP inventory app; it does not yet execute remote Docker operations. New dedicated web-account/FPM/vhost deployment scope in docs/ADMIN-ACTIVATION.md supersedes static-only lab proposal. Future workflow: admin creates invited users/projects/subdomains; users manage assigned home-node applications and configure standby contacts. See docs/PLATFORM-WORKFLOW.md.

Target ctx1 remains historically LXC 102 / Rocky Linux 9.8; OS/resources now observed via tracked read-only inventory at 2026-10-15T11:36:16Z: Rocky 9.8, LXC, x86_64, 3 CPUs, 8 GiB RAM, Compose v5.6.0. SSH probes passed at 08:25:31Z. Earlier Docker denial is historical: operator subsequently added the technical account to Docker group. In a new strict SSH session agent observed membership and Docker Engine 29.9.0, then created/started/deleted one isolated owned container successfully. Evidence recorded 2026-10-15T08:35:47Z; docs/DOCKER-SMOKE-TEST.md and checkpoint checkpoints/20261015T083547Z-FH-0016-docker-smoke-pass.md. Exit 0, exact cleanup/absence verified; known reference container ID/running/start time/restart count/image unchanged. Existing image reused, no pull, network/ports/mounts/volumes, no existing workload modified. Agent granted no rights; operator did. Remote sudo remains absent per prior operator report and not independently tested.

Independent SSH fingerprint remains NEEDS_TEST. Broker/service not installed. Docker-group access is broad and does not establish per-project authorization or isolation from a root-capable agent. Key used only through owner process; never read/copied/exported. Private connection mapping/key path remain outside public Git; private server inventory now exists in ignored .local/admin/inventory.json (no technical key path or key mapping). No Proxmox access assumed; historical EFI warning still unresolved.

## Next exact step

FH-0006 and FH-0007 local data/UI implementation DONE with tests, browser evidence and concrete completion revisions in the canonical catalog. Prepare the exact protected-center deployment/authentication proposal separately; no production center deployment performed. Public progress remains live and separate. FH-0018 admin visual/operational rollback QA, independent SSH identity, backup/dependency coverage and constrained remote operations boundary remain open.

Evidence: latest checkpoints, docs/PORTAL-DEPLOYMENT.md, docs/SERVER-ONBOARDING.md, docs/M01-AUDIT.md. Associated revision is the containing commit; inspect Git before resuming.

## Evidence provenance

Operator report: technical SSH setup, initially absent destination sudo/Docker permissions, then explicit Docker-group grant and requested retest; operator action time not supplied. Agent verified effective group/API access and complete test cleanup afterward. Agent observation: three transport probes at 2026-10-15T08:25:31Z and read-only local sudo capability check this turn. Neither successful SSH nor cached host trust proves independent host identity. Broker design is PROPOSED only: docs/SSH-OPERATIONS-SERVICE.md. Public exports retain only reviewed task labels/statuses and checkpoint metadata.

## Multi-node admin local verification

Thirteen tests PASS (eight PHP admin HTTP/concurrency tests, five public-export tests), PHP syntax checks PASS, actual seeded admin loopback login/list(ctx1 Docker/LXC/prior timestamps)/logout PASS without inventory mutation. Temporary test servers stopped. No screenshots/browser visual QA available; no live pool/vhost/cert/account changes. Private JSON 0700/0600, initial credential securely generated and not printed, auth uses Argon2id hash. Inventory one gateway/multiple nodes is a reviewable extension of existing home-node pattern, not a replacement for Coolify or fallback architecture. Docs: MULTI-NODE-ADMIN.md and ADMIN-ACTIVATION.md.

## Approved lab activation in progress

Operator explicitly approved exact ADMIN-ACTIVATION.md scope and Git push. Tooling/progress committed and pushed as a0f67d9. Prepare phase PASS at 11:38:31Z: private verified backup, dedicated unprivileged account/release/data/FPM pool and graceful reload; pre-existing shared config hashes unchanged. HTTP challenge vhost activated after exact-path recovery from restrictive-directory-mode failure; HTTP challenge/canaries PASS. Dedicated lab certificate issued, expires 2027-01-13. Post-certificate canary found separate Quantum API HTTP 429 versus earlier 200; cards32.php remains 200/TLS valid. HTTPS activation paused pending canary reconciliation. Do not issue certificate again; certificate.started without done is a post-check interruption, not an issuance failure.

After every meaningful result publish reviewed public event + checkpoint via scripts/record-progress.py and verify public HTTPS before next phase. Public page now includes dated completed steps/errors, not just generic task status. No additional operator approval required within approved activation scope.

## Live lab follow-up

The approved HTTPS vhost is active and lab.ventureout.cz serves authenticated inventory. Release public-directory umask defect corrected only at exact new path, no further reload required; frozen code intact. Real HTTPS login, session rotation/security flags, ctx1 Docker list and logout PASS; actual inventory unchanged. Private runtime 0700/files0600, dedicated fallback-web has only its own group; root-managed release/public0755. Repeated probes hit unrelated API 429 again; final full canary/config/app verification subsequently PASS after cooldown. This is not a Docker management service: broker and deployment actions remain planned. Initial credential remains in private operator handoff, never published.

Latest verified result supersedes activation-in-progress observations above: all prepare/http/certificate/https journal phases now have done evidence; final canaries and unchanged shared config hashes PASS after cooldown. Backend activation and real admin login complete. FH-0018 remains TESTING for browser/mobile review and operational rollback drill; neither is claimed performed. No home outage independence test performed.

## Follow-up documentation reconciliation

Fresh HTTPS auth/session rotation/ctx1/logout PASS without inventory mutation; 14 local tests PASS. Browser tooling unavailable; no visual QA or rollback drill claimed. Earlier activation-in-progress paragraphs are historical and superseded by the live result. No operational configuration changed in this follow-up.

## Prague display time

Project page event/checkpoint/generation times now display Europe/Prague with automatic CET/CEST. Eight portal tests and live HTTPS conversion check PASS; canonical UTC and host settings unchanged. See latest checkpoint for verification UTC.

## FH-0006 canonical catalog

Repository data implementation validated: 11 milestones/18 tasks preserved in state/catalog.json, Markdown tables generated, public export fail-closed on invalid records/drift. All 28 repository tests PASS, including privacy, references, transitions, stale/unknown health and heartbeat, and last-valid-page retention. See latest checkpoint for timestamp and completion revision. No protected-center deployment, remote action or service change. Small demo containers requested by operator for later deployment; no image selected yet.

## Public history and browser follow-up

Operator-requested bounded history is live. Headless Chromium at 360/768/1440 PASS: keyboard scrolling, five filters, no page overflow/errors, 40 extra rows cause 0 px section movement. All three screenshots inspected; private report path in checkpoint. Admin visual QA and operational rollback remain separate and unperformed. No system package/service changes; browser tooling isolated under /tmp.

## FH-0007 local control-center UI

Local-only read-only center built with eight modules, immutable artifact/manifest and atomic current pointer. All 36 repository tests and loopback Chromium 360/768/1440 filters/keyboard/clipboard/download/long-text checks PASS; screenshots reviewed. No authentication/deployment is claimed. Public blocker explanations now show actual missing evidence; superseded FH-0005 local design wait moved to READY under operator approval. FH-0008 deployment remains separate.

## Authenticated center adapter and browser discrepancy

41 repository tests and disposable Chromium 360/768/1440 login/asset/copy/download/logout checks PASS. Local query adapter and deployment proposal prepared; no live release switch. Frozen live source still sends no-referrer, which reproduced Origin:null form rejection in local Chromium; same-origin correction tested locally. Earlier direct-HTTP auth checks did not prove browser form behavior. Current operator priorities: read-only M01, mock-only Docker broker and local admin integration; pending new activation must not stall safe engineering.
