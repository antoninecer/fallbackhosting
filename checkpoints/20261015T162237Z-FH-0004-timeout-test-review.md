# Existing timeout test reliability review
- UTC: 2026-10-15T16:22:37.495699+00:00.
- Full suite first found unsynchronized generated TASKS table; synchronized, then rerun found existing timeout test elapsed 0.233s vs brittle 0.15s threshold.
- Intended correction: use an explicitly blocked fixture worker and prove caller returns UNKNOWN while driver is still unfinished, with generous outer bound and deterministic cleanup. No broker behavior or timeout policy changes.
- Acceptance: strengthened event-driven test and full suite pass; record failures honestly.
- Rollback: reviewed test-only revert.
