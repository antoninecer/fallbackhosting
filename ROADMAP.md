# Roadmap and acceptance gates

Status codes: `PLANNED`, `IN_PROGRESS`, `NEEDS_TEST`, `BLOCKED`, `DONE`.

| ID | Milestone | Initial status | Gate for DONE |
| --- | --- | --- | --- |
| M00 | Foundation and Git state | IN_PROGRESS | Docs and checkpoint committed/pushed; fresh-session resume works |
| M01 | Verified inventory and safety baselines | PLANNED | Evidence of live state; protected reference endpoint baseline; backup/rollback plans |
| M02 | Independent Project Control Center | PLANNED | Protected portal survives home-node outage; tasks/incidents/checkpoints visible |
| M03 | Coolify deployment on home node | PLANNED | Authorized admin can deploy/redeploy one example app without changing edge config |
| M04 | Wildcard routing and TLS | PLANNED | Multiple test hostnames route correctly; TLS renew plan; existing hosts pass canary |
| M05 | Versioned Fallback Builder | PLANNED | Safe exported HTML/assets; preview; immutable release; atomic publish; rollback |
| M06 | Standby Gateway + recovery | PLANNED | Per-app failover, hysteresis, manual force/restore, no cross-app outage |
| M07 | Emergency Contact | PLANNED | Independently hosted contact mechanism passes abuse/delivery tests |
| M08 | Resilience and recovery tests | PLANNED | One app, Docker, LXC, Tailscale outage tests; existing Quantum unaffected |
| M09 | Durable AI continuity | PLANNED | Checkpoint + automatic project UI ingestion; controlled restart after interruption |
| M10 | v1 release | PLANNED | Backup/restore, security review, docs and repeatable install tests |

Milestones may be reprioritized only after updating the architecture decision and explaining consequences. Use Git commits/PRs and evidence, not optimistic progress claims.
