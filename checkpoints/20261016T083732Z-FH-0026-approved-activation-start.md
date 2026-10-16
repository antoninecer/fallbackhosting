# FH-0026 approved public demo activation

- UTC 2026-10-16T08:37:32Z. Operator explicitly approved the presented exact activation and subsequent deployments in that application scope. No repeated approval needed for this scope; unrelated infrastructure remains protected.
- OBSERVED: clean Git dbac738 synchronized with origin/main. Read-only frozen candidate/unchanged vhost/admin/auth/inventory checks, Nginx/PHP syntax and protected health canaries PASS. Frozen source22cec4bc5d29460a0f5d8d6f72cccd28ac4df888 retained.
- Intended result: public HTTPS /demo/ with independent local standby, authenticated maintenance controls, real least-privilege systemd worker/socket. Acceptance includes TLS/assets/auth, manual and scheduled maintenance, owned-container outage, stable recovery and unchanged protected services.
- Exact approved targets/actions: lab vhost /demo/ locations only; /var/www/fallback-standby-demo and /var/lib/fallback-standby-demo; fallback-standby-demo.socket/service installation/start; frozen PHP release activation; syntax-tested graceful Nginx/PHP-FPM reloads. No DNS/cert/VPN/firewall/disk/other-vhost changes.
- Rollback: guarded scripts/activate-minimum-standby.py with exact private backup journal; restore previous lab vhost/admin pointer and stop only new units, preserve data. Never blindly replay partial activation.
- Next: apply guarded helper once, then actual public acceptance; activation is IN_PROGRESS, not DONE.
