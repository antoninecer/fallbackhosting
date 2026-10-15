# 20261015T114223Z-FH-0018-admin-https-failed
- UTC: 2026-10-15T11:42:23Z; Codex; M02/FH-0018 IN_PROGRESS.
- Associated Git revision: 55e23cb329654ef9a3bcbf9a39e02d6749ec1897; uncommitted changes must be inspected before resumption.
- Last verified action/results: HTTPS vhost syntax/reload and protected canaries PASS, but unauthenticated lab app returned FPM 404 because new root-owned release/public directory inherited mode 0700. Exact path inspected; fix only this new release public directory to planned 0755, not shared permissions. HTTPS journal remains started, no done.
- Files changed: state/current.json, this checkpoint and generated public artifact; inspect Git for source/docs changes.
- Infrastructure scope: approved ADMIN-ACTIVATION.md only; actual actions/results above. No home runtime changes.
- Open issues/unverified: independent fingerprint, external application baseline, full dependency/backup coverage, browser QA and certificate-renewal reload validation remain open.
- Next exact step: Correct exact new directory, verify app without reload/reissue, then reconcile HTTPS journal and publish.
- Rollback: approved scoped activation rollback; preserve private journal/data/release/certificate/account. Interrupted phases require reconciliation.
- Required approvals: none within already approved activation/Git-push scope.
