# Roadmap and acceptance gates

Status codes: `PLANNED`, `IN_PROGRESS`, `NEEDS_TEST`, `BLOCKED`, `DONE`.

| ID | Milestone | Current status | Gate for DONE |
| --- | --- | --- | --- |
| M00 | Foundation and Git state | DONE | Docs and checkpoint locally committed; fresh-session resume works; remote verification tracked separately |
| M01 | Verified inventory and safety baselines | NEEDS_TEST | Evidence of live state; protected reference endpoint baseline; backup/rollback plans |
| M02 | Independent Project Control Center | IN_PROGRESS | Protected portal survives home-node outage; tasks/incidents/checkpoints visible |
| M03 | Coolify deployment on home node | PLANNED | Authorized admin can deploy/redeploy one example app without changing edge config |
| M04 | Wildcard routing and TLS | PLANNED | Multiple test hostnames route correctly; TLS renew plan; existing hosts pass canary |
| M05 | Versioned Fallback Builder | PLANNED | Safe exported HTML/assets; preview; immutable release; atomic publish; rollback |
| M06 | Standby Gateway + recovery | PLANNED | Per-app failover, hysteresis, manual force/restore, no cross-app outage |
| M07 | Emergency Contact | PLANNED | Independently hosted contact mechanism passes abuse/delivery tests |
| M08 | Resilience and recovery tests | PLANNED | One app, Docker, LXC, Tailscale outage tests; existing Quantum unaffected |
| M09 | Durable AI continuity | PLANNED | Checkpoint + automatic project UI ingestion; controlled restart after interruption |
| M10 | v1 release | PLANNED | Backup/restore, security review, docs and repeatable install tests |

Milestones may be reprioritized only after updating the architecture decision and explaining consequences. Use Git commits/PRs and evidence, not optimistic progress claims.

Session 001 evidence: docs/M01-AUDIT.md and checkpoints. M00 local acceptance supersedes automatic push under explicit operator instructions. M02 is now IN_PROGRESS: public presentation live, private portal and failure tests still pending.

Transport follow-up: M03 remains PLANNED, preparation only. Technical SSH probes passed; following operator Docker-group grant, isolated Docker lifecycle/cleanup passed (FH-0016). Independent SSH fingerprint and enforceable agent/key boundary remain open (FH-0011, FH-0013–0015); no deployment milestone completed by transport checks.

FH-0017: private multi-node server configuration under M02 is locally implemented/tested; ctx1 Docker record and initial admin prepared. Exact isolated lab activation and browser checks pending. M02 remains IN_PROGRESS and M03 deployment still PLANNED; local configuration does not close audit/fingerprint/Coolify gates.
