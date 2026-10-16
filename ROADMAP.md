# Roadmap and acceptance gates

2026-10-16 update: operator requested an in-app guided Coolify installation instead of manual initial installation. Prior owned containers removed, data retained; FH-0023 implements a scoped wizard/help/account flow and one-shot worker. M03 remains IN_PROGRESS until actual guided deployment, account login and demo deployment gates are evidenced.

FH-0023 follow-up at 05:50 UTC: guide is live and real HTTPS browser/availability/auth/canary checks passed; status TESTING. One bounded trial worker was observed ready, with no permanent system service. Actual install/account validation awaits operator-supplied form details; no completion claimed from mocked tests or an armed worker.

Status codes: `PLANNED`, `IN_PROGRESS`, `NEEDS_TEST`, `BLOCKED`, `DONE`.

FH-0024 first recovery increment at2026-10-16 07:22 UTC: actual three-copy SSH discovery, independent static restore drills and safe nonexecuting preview verified;116 tests PASS. M08 is IN_PROGRESS for this bounded work, not completed full-server disaster recovery. Exact public demo activation remains separately pending under FH-0026.

FH-0025 minimum slice at 2026-10-16 07:10 UTC: actual remote-demo/independent-Nginx outage and static rollback verified,113 tests PASS, maintenance UI and unprivileged worker locally tested, backup/readback/isolated restore gates publication. Public `/demo/` activation and production control acceptance remain pending; M05 is IN_PROGRESS rather than complete from a one-page prototype.

2026-10-16 06:30 clarification supersedes mandatory public Coolify placement: unified FallbackHosting control and independent public-content availability take priority. Coolify instances are replaceable deployment adapters; reuse existing controller for first complete VPN/backend-outage/standby/maintenance/recovery demonstration. First implement/test a repository-local standby vertical slice; SSH backup discovery remains a separate READY task. No live edge reconfiguration or controller migration performed.

Operator-directed placement/recovery clarification 2026-10-16: central management/Coolify target is the public-IP node, applications and optional cataloged backups on remote selfhosted nodes. Fresh-install SSH backup discovery and selected restore are planned; existing ctx1 controller remains unchanged. See `docs/PUBLIC-CONTROLLER-RECOVERY.md`; repository-local recovery planning proceeds independently of later exact migration approval.

2026-10-16 06:06 UTC: FH-0023 bounded guided prototype DONE after actual installation, administrator enrollment, final compatible16-character credential synchronization and real browser login/logout in lab/Coolify. All102 tests and production canaries PASS. M03 remains IN_PROGRESS: target enrollment, MFA/recovery and demo deployment are not completed by a working controller.

2026-10-16 05:59 UTC: actual guided account submission rejected the exact requested password because it lacks a symbol. No installation request or secret was queued. FH-0023 remains TESTING and M03 IN_PROGRESS; select a compatible Coolify password before another trial. Existing lab login works; no credential replacement performed.

<!-- Table generated from state/catalog.json; edit catalog then run python3 scripts/project-data.py sync. -->

| ID | Milestone | Current status | Gate for DONE |
| --- | --- | --- | --- |
| M00 | Foundation and Git state | DONE | Docs and checkpoint locally committed; fresh-session resume works; remote verification tracked separately |
| M01 | Verified inventory and safety baselines | NEEDS_TEST | Evidence of live state; protected reference endpoint baseline; backup/rollback plans |
| M02 | Independent Project Control Center | IN_PROGRESS | Protected portal survives home-node outage; tasks/incidents/checkpoints visible |
| M03 | Central Coolify controller and remote application nodes | IN_PROGRESS | Authorized admin can deploy/redeploy one example app without changing edge config |
| M04 | Wildcard routing and TLS | PLANNED | Multiple test hostnames route correctly; TLS renew plan; existing hosts pass canary |
| M05 | Versioned Fallback Builder | IN_PROGRESS | Safe exported HTML/assets; preview; immutable release; atomic publish; rollback |
| M06 | Standby Gateway + recovery | IN_PROGRESS | Per-app failover, hysteresis, manual force/restore, no cross-app outage |
| M07 | Emergency Contact | PLANNED | Independently hosted contact mechanism passes abuse/delivery tests |
| M08 | Resilience and recovery tests | IN_PROGRESS | One app, Docker, LXC, Tailscale outage tests; existing Quantum unaffected |
| M09 | Durable AI continuity | PLANNED | Checkpoint + automatic project UI ingestion; controlled restart after interruption |
| M10 | v1 release | PLANNED | Backup/restore, security review, docs and repeatable install tests |

Milestones may be reprioritized only after updating the architecture decision and explaining consequences. Use Git commits/PRs and evidence, not optimistic progress claims.

Session 001 evidence: docs/M01-AUDIT.md and checkpoints. M00 local acceptance supersedes automatic push under explicit operator instructions. M02 is now IN_PROGRESS: public presentation live, private portal and failure tests still pending.

Transport follow-up: M03 remains PLANNED, preparation only. Technical SSH probes passed; following operator Docker-group grant, isolated Docker lifecycle/cleanup passed (FH-0016). Independent SSH fingerprint and enforceable agent/key boundary remain open (FH-0011, FH-0013–0015); no deployment milestone completed by transport checks.

FH-0017: private multi-node server configuration under M02 is active; ctx1 Docker record and initial admin are present. A browser-reported login 403 was fixed and live HTTPS tested, including a request without the pre-auth cookie; operator confirmed reaching the authenticated administration page. Session rotation, ctx1 display and logout passed. A stale ctx1 note was corrected while preserving the verified identity observation. Wider browser QA remains pending. M02 remains IN_PROGRESS and M03 deployment still PLANNED; this does not close audit/fingerprint/Coolify gates.

Current reconciliation: existing lab inventory HTTPS is already live; only the new center/form-fix release activation is BLOCKED_BY_OPERATOR (FH-0019). Independent ctx1 ED25519 identity is now VERIFIED from trusted-console attestation and client comparison (FH-0014). M01 remains NEEDS_TEST for backup/dependency/external application coverage. Operator prioritizes read-only audit, local broker/admin fixtures, then controlled owned Docker exercises on ctx1; no production service changes authorized by this reconciliation.

Latest task update 2026-10-15 20:55 UTC: center 503 fixed by activating the authenticated read-only artifact in immutable release `5b57a1e7886cf0976f948dc46da845c66c704d11`. Server-side auth/assets/logout, anonymous denial, inventory preservation and canaries PASS. Operator visual review and live rollback drill remain NOT_TESTED, so FH-0019 is TESTING. Current work moves to read-only FH-0002 dependency/backup coverage.

Further evidence: operator-attested 2026-10-15 node backup and zstd integrity VERIFIED, monthly schedule reported; restore NOT TESTED/offsite copy NOT DOCUMENTED. Controlled owned ctx1 lifecycle and cleanup passed; M03 remains PLANNED for actual Coolify deployment, not closed by broker fixtures or diagnostics.

## Scoped dependency follow-up — 2026-10-15T15:46:48Z

See docs/DEPENDENCY-AUDIT.md: selected project static and admin PHP dependencies are local; one home Docker bind mount observed, archive inclusion UNKNOWN. Operator backup/integrity VERIFIED; restore NOT TESTED/offsite NOT DOCUMENTED. FH-0002 TESTING, M01 NEEDS_TEST; no infrastructure changes.

## Accepted modular-provider direction — 2026-10-15

Operator approved the application security design and provider portability: reuse Coolify/Docker for apps, Proxmox native API or libvirt/QEMU/KVM for VM lifecycle and backups. Docker on plain Linux requires neither Proxmox nor VM provisioning. Current LXC remains the demo; VM isolation is selected per trust boundary. docs/MODULAR-PROVIDERS.md records boundaries, local planning tests and pending operational gates. No hypervisor/deployer replacement, Coolify installation/location change or live migration performed; independent Oracle standby remains mandatory.

Coolify initial controller installation: three healthy private services and real login-page browser QA verified; administrator bootstrap and app deploy/redeploy still pending. M03 IN_PROGRESS, never DONE from controller health alone. See docs/COOLIFY-DEPLOYMENT.md.
