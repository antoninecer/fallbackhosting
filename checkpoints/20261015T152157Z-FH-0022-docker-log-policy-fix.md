# 20261015T152157Z-FH-0022-docker-log-policy-fix
- UTC: 2026-10-15T15:21:57Z; Codex; M02/FH-0022 IN_PROGRESS.
- Associated Git revision: 1c0bc6592b489d04a43803d0a1d834036b84a539; uncommitted changes must be inspected before resumption.
- Last verified action/results: Private own-operation diagnostic established Docker local log driver rejects compression with max-file=1. Changed only new-container max-file option to 2 while retaining 1 MiB per file and all isolation/resource limits. Every prior own resource absence and unchanged original baseline verified. No daemon/security/host changes.
- Files changed: state/current.json, this checkpoint and generated public artifact; inspect Git for source/docs changes.
- Scope: repository state/checkpoint/public static projection; any operational action requires its separately recorded exact authorization. No home runtime changes in this recorded stage.
- Open issues/unverified: independent fingerprint, external application baseline, full dependency/backup coverage, browser QA and certificate-renewal reload validation remain open.
- Next exact step: Run one reconciled owned lifecycle with corrected bounded container log policy and verify exact cleanup plus protected canaries.
- Rollback: reviewed Git revert and public rebuild for repository work; operational activation rollback remains documented separately in docs/ADMIN-ACTIVATION.md.
- Required approvals: none within already approved activation/Git-push scope.
