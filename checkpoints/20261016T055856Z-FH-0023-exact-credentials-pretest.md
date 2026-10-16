# FH-0023 exact requested credentials browser trial

- UTC: 2026-10-16T05:58:56Z. Operator explicitly requests a trial with their supplied email and the existing private JSON password. Neither credential is included here.
- Scope: authenticated live lab installation wizard; enter exact requested credentials and confirm once. No password substitution, native-policy bypass, infrastructure configuration or volume deletion.
- Acceptance: observe actual browser response; verify whether a job was queued; report account/install success only with actual evidence. If rejected, retain TESTING and document the precise validation requirement.
- Baseline: protected reference/project/lab canaries PASS; remote retained-template preflight PASS (three intended containers absent, two volumes retained, pinned images cached, unrelated workload unchanged). Existing private password lacks a symbol; rejection is expected before dispatch.
- Rollback: rejected input should enqueue nothing and clear password fields. If unexpectedly accepted, inspect the single bounded worker and reconcile actual remote state before any retry. Preserve all retained data and audit records.
