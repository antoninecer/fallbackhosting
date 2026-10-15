# 20261015T164305Z-FH-0004-coolify-ipv4-reconcile
- UTC: 2026-10-15T16:43:05Z; Codex; M03/FH-0004 IN_PROGRESS.
- Associated Git revision: f7fc93f6b596ef230abf99c50d441d68c46740ed; uncommitted changes must be inspected before resumption.
- Last verified action/results: Compose wait returned nonzero: new DB/Redis healthy, Coolify unhealthy. Sanitized error confirms app-container Nginx IPv6 socket errno97 unsupported. New owned container IDs journaled; no existing workload or host IPv6 configuration altered. Investigate supported IPv4-only image setting before scoped own-app correction.
- Files changed: state/current.json, this checkpoint and generated public artifact; inspect Git for source/docs changes.
- Scope: repository state/checkpoint/public static projection; any operational action requires its separately recorded exact authorization. No home runtime changes in this recorded stage.
- Open issues/unverified: external application baseline, complete dependency/backup coverage, production-release QA and certificate-renewal reload validation remain open. Independent fingerprint is VERIFIED; restore NOT TESTED and external backup copy NOT DOCUMENTED.
- Next exact step: Apply reviewed persistent IPv4-only setting to new Coolify only; preserve new DB volumes and secrets, recheck health and protected workloads. No global IPv6/network/firewall change.
- Rollback: reviewed Git revert and public rebuild for repository work; operational activation rollback remains documented separately in docs/ADMIN-ACTIVATION.md.
- Required approvals: none within already approved activation/Git-push scope.
