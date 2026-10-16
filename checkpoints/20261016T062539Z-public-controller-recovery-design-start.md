# Operator-directed public controller and SSH backup discovery

- UTC 2026-10-16T06:25:39Z. Operator explicitly selects the public-IP node for the management control plane and a remote selfhosted node as an allowed backup repository, discoverable during new installation over SSH.
- Scope: reconcile and record target architecture, recovery contract and next repository-local engineering task. No controller migration, Docker installation on Oracle, restore, DNS, Nginx or service change.
- Acceptance: distinguish accepted target from current ctx1 controller; keep independent gateway/static standby serving; specify backup discovery/verification/selection and separate controller/application recovery requirements. Validate canonical project state and sanitized public update.
- Baseline: Git clean/synchronized at 24cb13a; last verified health/account evidence in 20261016T060607Z checkpoint is historical, not a fresh heartbeat. Current service probes will be read-only.
- Rollback: repository revert and public projection rebuild only. Existing running services, data, accounts and backups remain unchanged.
