# 20261015T145812Z-FH-0005-center-auth-retest
- UTC: 2026-10-15T14:58:12Z; Codex; M02/FH-0005 IN_PROGRESS.
- Associated Git revision: 3b8da0fd51e10b1e27deea009121b82b34fc8a44; uncommitted changes must be inspected before resumption.
- Last verified action/results: Four disposable PHP HTTP integration tests PASS (all assets session-gated, logout/expiry revoked, HEAD/method/path/oversize/corruption/symlink cases denied). First local real-browser login returned CSRF/Origin denial; debugging only sanitized header-presence/match categories. Live frozen admin release untouched.
- Files changed: state/current.json, this checkpoint and generated public artifact; inspect Git for source/docs changes.
- Scope: repository state/checkpoint/public static projection; any operational action requires its separately recorded exact authorization. No home runtime changes in this recorded stage.
- Open issues/unverified: independent fingerprint, external application baseline, full dependency/backup coverage, browser QA and certificate-renewal reload validation remain open.
- Next exact step: Identify actual local-browser form-origin/session behavior; retain production HTTPS/CSRF policy and rerun browser auth tests.
- Rollback: reviewed Git revert and public rebuild for repository work; operational activation rollback remains documented separately in docs/ADMIN-ACTIVATION.md.
- Required approvals: none within already approved activation/Git-push scope.
