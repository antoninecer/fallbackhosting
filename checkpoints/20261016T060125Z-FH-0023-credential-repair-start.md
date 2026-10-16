# FH-0023 operator-authorized credential repair and guided installation

- UTC 2026-10-16T06:01:25Z. Operator explicitly requests correcting the credential problem and generating a new password.
- Scope: rotate existing lab administrator password and ignored operator JSON; use the same newly generated compatible password for the requested Coolify administrator, then execute one actual guided trial. No secret values or personal account details in tracked evidence.
- Acceptance: new credential has all four required character categories, actual browser lab login succeeds, old lab password fails, guided job completes, actual native Coolify login succeeds, registration disabled and unrelated workload/canaries remain healthy. Otherwise record actual partial state without replay.
- Baseline: Git clean at 048cfdf; protected production/project/lab TLS/assets/access canaries PASS. Prior exact-credential trial queued zero requests/secrets/results; no remote installation dispatched.
- Rollback: private backups of auth/credential files before rotation; atomically write validated hash and private credential JSON preserving ownership/modes. Preserve original inventory and all retained Coolify volumes/data. For dispatched installation inspect ledger/markers/container identity before any retry or removal; no automatic repeat. No Nginx/DNS/firewall/system-service change.
