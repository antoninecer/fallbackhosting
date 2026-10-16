# FH-0023 exact requested credentials: validation rejection observed

- UTC: 2026-10-16T05:59:16Z. Actual HTTPS Chromium trial used the operator-supplied account details and exact existing private JSON password. Credentials are excluded from this evidence.
- OBSERVED: lab admin login succeeded; Aplikace/server/help/account flow loaded; installation confirmation POST was rejected with the explicit password-composition message requiring a symbol. No credential substitution or validation bypass performed.
- PASS: password fields cleared after rejection, browser displayed no installation history, logout succeeded. Independent private queue inspection found zero request, secret and status files. No remote installation or account creation was attempted.
- Baseline retained-template read-only verification PASS: three intended containers absent, two volumes retained, pinned images cached, unrelated workload unchanged. Protected canaries PASS before trial.
- FH-0023 remains TESTING; actual installation and native Coolify login NOT_TESTED. The existing password is long but does not meet this composition rule; do not describe that alone as evidence of a weak password.
- Next operator choice: select a Coolify password containing a symbol (a proposed suffix can be confirmed without sharing the password itself). Preserve existing lab credentials. Other safe project tasks are not blocked by this account choice.
- Rollback: none needed for rejected input; retained volumes/data, immutable lab release and original credentials unchanged. Inspect bounded-worker readiness before a later trial; reconcile any actual started job before retry.
