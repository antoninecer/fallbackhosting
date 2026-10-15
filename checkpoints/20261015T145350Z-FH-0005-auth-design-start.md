# Protected center authentication design
- UTC: 2026-10-15T14:53:50Z; FH-0005 IN_PROGRESS.
- Scope: concrete repository-only integration/deployment proposal using existing lab admin session and query-routed allowlisted artifacts; no operational modification.
- Dependencies: local data/UI tasks DONE; existing lab entry is frozen root-managed release, exact Nginx routes allow only /, /index.php, /admin.css.
- Intended result: reviewable plan protecting every center asset and resume file, preserving existing inventory/auth and independent public presentation.
- Acceptance: fixed paths/allowlist, least privilege, bounded sizes, session/logout/timeout behavior, artifact hashes, exact release/rollback/canaries and explicit activation gates; no public center files.
- Rollback: reviewed documentation revert. Runtime remains unchanged.
