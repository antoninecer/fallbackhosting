# Offline release verifier start
- UTC: 2026-10-15T15:47:37.303011+00:00; FH-0005 TESTING.
- Intended result: read-only exact Git-source and artifact manifest verification of a staged new admin release; reject symlinks, extra files, corruption and unsafe permissions.
- Scope: repository tool and temporary isolated fixtures only. No live release read/write, switch, service or credentials.
- Acceptance: correct fixture passes; mismatched source/artifact and unsafe structure fail; no activation functionality.
- Rollback: repository revert. Production readiness additionally requires ownership, PHP behavior, canaries and separately approved rollout.
