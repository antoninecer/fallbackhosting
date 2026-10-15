# Coolify deployment preflight
- UTC: 2026-10-15T16:33:31.490163+00:00.
- Operator explicitly requested Coolify deployment; intended target existing ctx1 test Docker/LXC, never Oracle.
- First scope: read-only resources, occupied ports, existing workloads, official Compose/start/bootstrap review. No shell installer execution or host/service/SSH change.
- Acceptance before install: capacity, collision-free private-only UI, preserved workload baseline, pinned reviewed configuration, private credentials/bootstrap and scoped rollback.
- Rollback before mutation: none; deployment plan/checkpoint required before any containers created.
