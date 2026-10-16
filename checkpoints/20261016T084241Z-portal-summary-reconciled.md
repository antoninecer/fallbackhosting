# Public summary reconciled after actual deployment

- UTC 2026-10-16T08:42:41Z. Replaced stale public overview claims about unavailable automatic fallback/local-only controls with reviewed bounded actual public-demo/maintenance/recovery results. Last-recorded-step label no longer implies the completed deployment is still executing. No runtime/service/config change.
- Existing eight public export tests PASS in0.338s; actual HTTPS overview checked for current wording and absence of both stale claims. Public export stays three local files with no private-state/log/credential export.
- FH-0025/FH-0026 DONE; deployment acceptance remains checkpoints/20261016T084056Z-FH-0026-public-live-pass.md. Live source22cec4b, automatic ONLINE/no scheduled window at last check. Existing private backup/journal preserved; never repeat apply against installed targets. Full live activation rollback not exercised. Generic application publication UI and full controller/database recovery remain next separate engineering. Operator approval persists within established application scope.
- Rollback of this wording only: source revert then public rebuild; no Nginx/PHP reload needed.
