# Availability-first clarification

- UTC 2026-10-16T06:30:02Z. Operator prioritizes unified FallbackHosting control, VPN-reachable nodes and independent minimalist standby over a fixed Coolify placement/count. Earlier mandatory central-Coolify placement must be relaxed; public FallbackHosting edge remains.
- Scope: documentation and canonical next engineering priorities only. Acceptance: separate network/control/serving/backup roles, no controller requirement per request, per-app failure/maintenance/recovery policy, self-contained local standby and exact current implementation limits. No VPN/service/migration/proxy/DNS changes.
- Git clean/synchronized at f8a19de. Last observed canaries are historical 06:25–06:27 documentation-stage probes; no new monitoring implied.
- Rollback: repository revert/public projection rebuild only.
