# Current project state

2026-10-16T08:40:56Z — Public demo and authenticated maintenance are LIVE and actual HTTPS/browser/outage/recovery verified. FH-0026/FH-0025 acceptance PASS; full116 tests PASS. Final automatic ONLINE/no planned window; auth/inventory/unrelated configs unchanged, protected canaries and three Coolify services healthy. See `checkpoints/20261016T084056Z-FH-0026-public-live-pass.md`. Earlier approval-pending/not-deployed paragraphs below are historical and superseded. Generic exporter and controller/database/VM recovery remain open.


2026-10-16 07:22 UTC — FH-0024 TESTING: actual read-only SSH catalog found three static backup archives; all three independently fetched/hash-checked/restored to isolated new directories and scoped repository attestations updated. Nonexecuting selected restore preview passes; malformed/symlink/duplicate/unknown-format/oversize/decompression cases tested. Full116 tests PASS. Controller/database/private-secret/VM restore unsupported, not claimed. Public activation FH-0026 remains the only pending exact-scope operator decision; existing services unchanged. Evidence: `checkpoints/20261016T072248Z-FH-0024-discovery-restore-preview-pass.md`.

2026-10-16 07:10 UTC — FH-0025 minimum composable slice implemented/tested, awaiting exact public activation step. Actual remote demo stop/start, independent Nginx, local assets, three-check recovery, maintenance/scheduled window, remote backup/readback/restore/serving/rollback PASS. Admin maintenance UI/Unix peer control and Prague DST validation pass local/browser360/768/1440; actual unprivileged www-data worker tested. Full113 tests PASS. Verified source f354427; root-owned candidate staged, no shared service/current-release activation yet. Scope/rollback: docs/MINIMUM-STANDBY.md. Generic WordPress export/full database/controller restore remain separate.

Operator follow-up: scheduled maintenance must support start/end, affected apps, advance notice and theme-matched contact-only fallback replacing online ordering. Maintenance overrides automatic healthy-backend routing until the window ends; stable checks gate return, otherwise report overrun. This is specified/planned, not deployed. No notifications sent or actual maintenance window created.

2026-10-16 06:30 UTC — operator clarified primary objective: unified FallbackHosting UI over VPN-connected nodes, automated supported-node preparation and independent minimal static standby for maximum practical public-content availability. Coolify location/count is flexible; a public-host migration is not required for its own sake. Keep current verified ctx1 controller for first end-to-end test. Serving must not depend on controller API/backup availability; per-app checks, local snapshots, manual maintenance and stable recovery are the next functional priority. No live change; see availability contract in `docs/PUBLIC-CONTROLLER-RECOVERY.md`.

2026-10-16 06:25 UTC — operator clarified target: public-IP node hosts FallbackHosting/Coolify management, remote selfhosted nodes host apps and may store discoverable backup repositories. New-install recovery wizard must verify SSH identity/catalog/archive compatibility and preview an explicitly selected restore; controller and app data are distinct. Design in `docs/PUBLIC-CONTROLLER-RECOVERY.md`. Current Coolify remains on ctx1; no live migration/restore. Independent edge/static standby preserved. Next task is fixture-only catalog/discovery/restore planning.

2026-10-16 06:06 UTC — FH-0023 DONE: actual guided installation SUCCEEDED, native owner enrolled, three healthy services, registration disabled. Operator-authorized correction synchronized lab/Coolify to one new compatible 16-character credential in ignored private JSON; actual browser login/logout PASS in both, prior lab credential rejected. Generator now defaults to16 and guarantees all four groups; 102 repository tests PASS. One completed worker operation, readiness withdrawn, no stored queue secrets or unfinished operation. Original workload and protected canaries unchanged. M03 remains IN_PROGRESS for target validation/MFA/recovery/demo deployment. Evidence: `checkpoints/20261016T060607Z-FH-0023-credentials-and-native-login-verified.md`.

2026-10-16 05:59 UTC — FH-0023 TESTING: actual HTTPS browser trial with exact operator-requested credentials reached installation confirmation but was rejected for missing password symbol. Lab login/logout PASS; password fields cleared; private queue independently confirmed zero requests/secrets/results. No installation/account creation attempted; retained data unchanged. Next: operator selects a compatible Coolify password, then inspect worker readiness and retry once. Other safe work remains actionable. Evidence: `checkpoints/20261016T055916Z-FH-0023-exact-credentials-result.md`.

2026-10-16 05:50 UTC — FH-0023 TESTING: guided installer live in Aplikace. Actual HTTPS browser login/server/help/account form PASS, 360/768/1440 no overflow, worker availability gates submit, center/CSS/logout/unauth denial PASS; inventory hash unchanged and protected canaries PASS. Immutable root-owned release `10eb26c37ddbc9e1fdb078b946893f6a08d08eb4`; one syntax-checked graceful FPM reload, no config change. A bounded one-attempt operator-started worker was observed READY; no system service. Coolify remains removed/data retained until operator submits account details in the wizard. Actual installation/native login NOT_TESTED. Evidence: `checkpoints/20261016T055011Z-FH-0023-wizard-live-ready.md`.

2026-10-16 05:47 UTC — FH-0023 predeployment: 100/100 tests and Chromium fixture at 360/768/1440 PASS; latest real retained-template precheck, protected canaries and privileged FPM syntax check PASS. Prior immutable release recorded. Next scoped action is lab UI release switch and one bounded one-attempt worker; no new system service/public Coolify route. Actual account details/install remain pending in the application. Evidence: `checkpoints/20261016T054729Z-FH-0023-wizard-predeploy.md`.

2026-10-16 05:45 UTC — FH-0023: wizard, private request/secret spool and scoped one-shot worker implemented locally. HTTP/worker tests, three fixed remote-driver tests and disposable Chromium 360/768/1440 flow PASS. Real retained-template precheck PASS without installing services. No live UI release/worker yet; operator will enter account details in the authenticated wizard. Evidence: `checkpoints/20261016T054536Z-FH-0023-wizard-local-verified.md`.

2026-10-16 05:40 UTC — FH-0023: operator requested removal of existing Coolify and a guided application-based installation trial. Three exact owned containers removed; both volumes/private data retained; unrelated workload and protected canaries unchanged. Current work: authenticated wizard/help/account request and a fixed-template one-shot worker. No new installation or system service yet; see `checkpoints/20261016T054027Z-FH-0023-coolify-removed.md`.

Updated 2026-10-15T16:47:01Z, Codex. Observations are point-in-time, not live monitoring.

## Milestones

- M00 DONE, locally committed. Git push explicitly authorized by operator.
- M01 NEEDS_TEST, partially verified: Oracle, SSH, Docker lifecycle/cleanup and home OS/resources/Compose observed. Independent SSH identity and operator-attested backup/integrity are verified; external application, remaining dependency coverage, restore/offsite evidence remain open. Controlled failure tests belong to M08.
- M02 IN_PROGRESS: https://project.lab.ventureout.cz/ is LIVE as sanitized public progress presentation; private server-inventory admin LIVE at https://lab.ventureout.cz/, ctx1 seeded and real HTTPS admin login/list/logout verified; broader center modules remain planned. FH-0009 browser QA now passed in headless Chromium at 360/768/1440, including screenshot inspection, keyboard scrolling and all filters; see follow-up checkpoint.
- M03 IN_PROGRESS: private Coolify 4.4.6 controller installed on home test node; three services healthy, loopback UI/browser/canaries verified. Initial admin email/bootstrap, real login and validated application deployment target remain pending. No remote account/key/SSH/daemon changes.

2026-10-15 20:45 UTC: FH-0017 login failure fixed in the deployed PHP release. The unauthenticated login request now requires an exact same-origin `Origin` and no longer depends on the pre-auth session cookie; authenticated mutations and logout retain session-bound CSRF. After one graceful PHP-FPM reload, live HTTPS login with the pre-auth cookie omitted, session rotation, ctx1 display, logout, and unchanged inventory hash all PASS. Protected canaries and TLS/reference/project checks PASS. The source release is `f285d8ab5400c9364f4008c6c06db035ebe0f26e`. Actual Chrome/Safari operator confirmation is still pending; browser automation could not launch because `libatk-1.0.so.0` is unavailable, so browser QA is NOT_PERFORMED. FH-0017 remains TESTING. Evidence: `checkpoints/20261015T204510Z-FH-0017-login-fix-live-pass.md`.

2026-10-15 20:49 UTC: Operator confirmed reaching the authenticated administration page. Fixed a contradictory ctx1 note through the authenticated form; only the note and its audited inventory revision changed, while the independently verified fingerprint status/timestamp remained intact. The web account could not open the root-owned inventory lock, so ownership of that exact 0600 lock file was corrected to `fallback-web:fallback-web`; no other runtime file/config/service changed. Nine admin tests and protected HTTPS/reference/project canaries PASS. FH-0017 remains TESTING for wider browser QA. Resume M01/FH-0002 with read-only backup/dependency coverage audit. Evidence: `checkpoints/20261015T204932Z-FH-0017-ctx1-description-reconciled.md`.

2026-10-15 20:51 UTC: Operator then reported HTTP 503 at the authenticated center URL. The active PHP release is missing `center-artifact/`, so the existing handler correctly fails closed; no production switch has occurred. Treating the exact error report as a request to fix this route, FH-0019 is now IN_PROGRESS. Prepare only an immutable release adding the read-only artifact, preserving existing authentication and inventory; no Nginx/PHP-FPM/service/network changes. Evidence/scope/rollback: `checkpoints/20261015T205108Z-FH-0019-center-activation-start.md`.

2026-10-15 20:52 UTC: Local candidate release passed all 88 tests; exact source/artifact manifest verifier PASS; PHP syntax and FPM configuration checks PASS; protected HTTPS/reference/project canaries PASS. Candidate is built from commit `9ccca4b2a07c528cb7387ddbf3a052d53f2f82ea`, with 72,573 bytes of verified content; prior release still active and private inventory baseline captured. Deployment not yet performed. Evidence: `checkpoints/20261015T205239Z-FH-0019-center-candidate-pass.md`.

2026-10-15 20:53 UTC: Final activation precheck completed. Exact previous release and private inventory baseline are recorded. The new candidate will be built from the committed state; only the admin release symlink may change. A single graceful PHP-FPM reload is allowed only if cache behavior prevents the new artifact path from loading, after syntax and canary checks. See `checkpoints/20261015T205357Z-FH-0019-center-release-ready.md`.

2026-10-15 20:55 UTC: FH-0019 center release is live at commit `5b57a1e7886cf0976f948dc46da845c66c704d11`. Exact source/artifact verification, root ownership/modes, authenticated HTTPS center and all five assets PASS; anonymous/post-logout access denied; traversal rejected; inventory unchanged; canaries PASS after one graceful PHP-FPM reload. Operator visual confirmation and rollback drill remain untested; status TESTING. Next current task FH-0002: read-only dependency/backup coverage audit. Evidence: `checkpoints/20261015T205503Z-FH-0019-center-live-pass.md`.

2026-10-15 20:56 UTC: Updated RUNBOOK and MULTI-NODE-ADMIN to distinguish the deployed session-protected read-only center from the local unauthenticated prototype and Docker operations fixtures. No runtime changes. Next safe work remains FH-0002 read-only dependency/backup-coverage evidence; restore, external copy and volume inclusion are still unverified.

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

## Independent ctx1 identity VERIFIED

Trusted-console operator attestation privately matched existing ED25519 client trust and strict pinned-algorithm SSH. Both prepared/live private inventory updated with VERIFIED provenance and private backups; no host/trust/service/network changes. Earlier missing-fingerprint paragraphs are historical and superseded. Complete backup/dependency and independent external app evidence remain open; broker runtime privilege isolation remains separate.

## Local broker v1 validation

FH-0020: eight fixture actions, OS-peer plus signed-principal/project scope, separate one-use write approvals, durable registry/jobs/audit, timeout UNKNOWN/no repeat, bounded Unix framing and historical admin view implemented. All 57 repository tests/16 broker tests PASS. No real driver, service or protected issuer activated. Independent external web fetch remained unavailable; M01 external app and backup/dependency coverage remain open. User permits owned controlled ctx1 Docker exercises; no unrelated workload changes permitted by that exercise scope.

## ctx1 backup/integrity VERIFIED by operator

Operator confirms successful 2026-10-15 LXC backup and zstd -t, monthly schedule set. Backup and integrity VERIFIED (operator attestation); restore NOT TESTED, external copy NOT DOCUMENTED. Exact execution UTC/archive path not supplied. Canonical record in state/current.json backup_verification and FH-0002 evidence. Remaining audit work continues; no agent restore or infrastructure change.

## Controlled ctx1 Docker exercise PASS

At 2026-10-15T15:21:58Z–15:22:05Z, one owned limited container create/start/inspect/log/restart/stop/remove/absence passed; original reference unchanged. Protected canaries and frozen lab integrity PASS afterward. Initial attempts exposed incompatible local-log compression/max-file=1; corrected only new-container max-file to 2, keeping all isolation. Every prior test resource cleanup verified. No daemon/service/host changes; no live broker.

## Local PHP operations integration

PHP-to-Unix peer broker fixture roundtrip implements scoped lifecycle/read requests and a selected read-only app/node/container/jobs/errors/audit page. Browser 360/768/1440 PASS, screenshots inspected, actual transient RUNNING and timeout UNKNOWN snapshots explicitly historical. No production route, signing authority or SSH transport installed; existing lab frozen release unchanged. See docs/ADMIN-OPERATIONS-PROTOTYPE.md and latest checkpoint for exact validation.

## Constrained execution proposal

FH-0015 TESTING: docs/AGENT-EXECUTION-BOUNDARY.md prepared with external runner identity, protected code/policy/issuer/trust roots, preserved operator recovery and negative canary tests. Read-only current sudo/Docker membership reconfirmed at 15:34:07Z; key isolation still NOT ESTABLISHED. No key read, account/group/sudo/SSH/service change. Proposal review does not block other local engineering.

## Certificate reload proposal

FH-0012 TESTING: own two-certificate hook/proposal and five injected callback tests prepared, all 67 repository tests PASS. Root-managed future install/reconfigure/timeout/canary/served-leaf/rollback plan documented. Nothing installed or renewed/reloaded; automatic end-to-end renewal remains unconfigured/unverified.

## Scoped dependency follow-up — 2026-10-15T15:46:48Z

See docs/DEPENDENCY-AUDIT.md: selected project static and admin PHP dependencies are local; one home Docker bind mount observed, archive inclusion UNKNOWN. Operator backup/integrity VERIFIED; restore NOT TESTED/offsite NOT DOCUMENTED. FH-0002 TESTING, M01 NEEDS_TEST; no infrastructure changes.

## Offline release verification — 2026-10-15T15:48:50.738818+00:00

FH-0005 TESTING: exact Git/artifact/mode verifier implemented, four isolated tests PASS. No real new release staged/verified or activated. Runtime readiness/rollback remain untested; FH-0019 BLOCKED_BY_OPERATOR.

## Application access proposal — 2026-10-15T16:02:56.884737+00:00

FH-0015 TESTING: docs/APPLICATION-ACCESS-SECURITY.md records researched role/identity/revocation/isolation proposal and exact operator decisions. VM trust boundaries are proposed architecture review only. No MFA/RBAC/VM deployment or enforced key-isolation claim; current broker approvals retained. Public project reports sanitized decisions, not private recovery data. Local engineering remains actionable.

## Modular existing-tool integration — 2026-10-15T16:23:17Z

Operator accepted app security design and requested portability to ordinary Linux KVM. FH-0004 TESTING: offline provider planner and five tests implemented; full suite 76 PASS. Coolify/Docker app layer is independent of Proxmox/libvirt hypervisor layer; actual adapters NOT_IMPLEMENTED. Coolify team Admin is too broad for app-only delegation; no native role access granted. Current LXC unchanged; VM/backup workers are future explicit operations, not activated. General role/isolation approval no longer pending; exact installation/credential/host scope still required.

## Local application policy — 2026-10-15T16:26:03Z

FH-0015 TESTING: accepted scoped role rules, separate logs grant, strong authentication/step-up and current-policy/session rechecks implemented locally; eight new tests and full 84-test suite PASS. No real IdP, durable role store, broker admission interlock, PHP wiring or runtime privilege isolation claimed. docs/APPLICATION-POLICY-PROTOTYPE.md records exact gaps; infrastructure unchanged.

## Coolify private readiness — 2026-10-15T16:47:01Z

Operator-requested ctx1 installation is running privately with all three services healthy. docs/COOLIFY-DEPLOYMENT.md records exact deltas, initial directory/IPv6 failures and safe reconciliation, private backups, browser/canary evidence and scoped rollback. FH-0004 TESTING, M03 IN_PROGRESS; initial administrator absent pending requested private email. Registration/updates/API/default SMTP disabled; no public route or automation credential/target configured. No application deployment or full milestone completion claimed.
