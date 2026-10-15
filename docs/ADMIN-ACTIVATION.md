# lab admin activation — approved activation, journaled execution

This supersedes the static-only lab activation proposal for the operator's requested server administration. Existing project.lab.ventureout.cz progress site remains separate. All preparation is complete locally; Operator explicitly approved this exact scope and Git push; no further approval is pending for these actions. No shared config, account, PHP service or certificate changed yet.

## Requested exact scope

1. New dedicated system user/group `fallback-web`, home `/var/lib/fallback-web`, nologin shell, no sudo or Docker-group membership. If already present, stop and reconcile rather than repurpose.
2. Root-managed versioned application release `/var/www/fallback-admin/releases/<approved-commit>/` with `public/index.php`, admin.css and private-source lib.php, current symlink `/var/www/fallback-admin/current`. Only reviewed source from that commit; files/parents not writable by web user. This does not enforce isolation against the still root-capable Codex account; FH-0015 remains open.
3. Private runtime `/var/lib/fallback-web/admin/`, owner fallback-web, directory 0700/files 0600. Copy only prepared inventory.json and auth.json (password hash), create private sessions directory. Do not copy plaintext initial credential, technical SSH identity or key paths. No database migration.
4. New FPM pool `/etc/php/8.3/fpm/pool.d/fallback-admin.conf` from deploy/fallback-admin-pool.conf, socket `/run/php/fallback-admin.sock`; existing pools unchanged. Two on-demand workers, 128 MiB PHP memory each and 15-second request limit are proposed initial caps, not measured guarantees. `php-fpm8.3 -t` before one graceful `systemctl reload php8.3-fpm`; shared service means canaries before/after are mandatory.
5. New `/etc/nginx/sites-available/lab.ventureout.cz` plus matching enabled symlink. First deploy/lab-http.conf for existing ACME webroot `/opt/fallback/lab-public`; then deploy/admin-lab-https.conf for the app. No existing vhost edits. Two syntax-gated `systemctl reload nginx` operations. No restarts.
6. Dedicated `lab.ventureout.cz` certificate via existing Certbot webroot account/timer: `certbot certonly --webroot -w /opt/fallback/lab-public -d lab.ventureout.cz --cert-name lab.ventureout.cz --non-interactive`. No existing certificate or wildcard replacement. Inspect renewal settings afterward; actual renewal/reload validation remains a separate maintenance task, not implied here.
7. Private prechange backup `/var/backups/fallbackhosting-admin-20261015/` (0700), including exact existing Nginx/PHP configuration and a protected copy of prepared app data. Never copy backups into public webroot/Git or print contents. Verify archive readability; record old file hashes privately.

No DNS/firewall/routing/SSH/Tailscale/PVE/home Docker or service-key changes, no account permission increase on ctx1, no installation/upgrades of packages. Git push was separately authorized.

## Ordered activation and stop conditions

- Reconcile actual target paths, existing user/group and listeners. Check DNS A/AAAA externally, reference/project route/TLS/assets and other protected canaries; record pre-existing failures separately. Confirm dedicated certificate does not already exist before requesting issuance. Verify free space and backup/archive integrity.
- Review/lint the exact approved application commit and pool/vhost templates. Verify auth exists and protected inventory contains intended ctx1; do not log private configuration/password/hash. Operator retrieves initial credential only in their private terminal. No public registration/setup allowed.
- Create only the new web account/release/private runtime/pool; copy reviewed code and just inventory/auth data with exact intended ownership/modes. Never bulk chmod/chown existing app directories. No runtime account access to technical key, Docker socket, broker or sudo.
- Test FPM configuration, reload once, wait for new socket, verify owner/group and unrelated PHP/reference canaries. Stop and roll back new pool if reference regresses. No new public admin until backend can fail closed and its administrator already exists.
- Install only the new HTTP challenge vhost, nginx -t, approved reload. Verify challenge path and protected canaries. Issue dedicated Certbot cert, then install exact HTTPS template, nginx -t, second approved reload. Allow bounded readiness retry for asynchronous reload; never disable TLS verification.
- Verify valid lab TLS, correct unauthenticated login and no internal server data, CSS MIME, exact HTTP redirect, source/auth/inventory/CLI/private paths 404. Privately test real admin login/logout and ctx1 inventory. Do not print credentials or actual private HTML; do not mutate actual configuration merely to smoke test it. Test forms against disposable test data before deployment.
- Repeat production/project route/TLS/assets and baseline comparisons; verify pre-existing shared config files unchanged. Record UTC, release revision, ownership and actual verification. Browser/mobile review (360/768/1440) remains required; do not claim it if tooling unavailable. Broker/home outage tests require separate controlled scope, not part of this activation.

The app has no remote actions; per-server fields are stored configuration, not a completed connection test or authorization for arbitrary host access. Certificate reload hooks, backups/restore drills, admin credential rotation and first-run operator UX remain explicit follow-up work.

## Scoped rollback

If syntax fails, do not reload. Preserve failure evidence privately. Disable only the newly created lab symlink by moving it to this backup directory; test Nginx and reload only if it was activated. Existing project site and other virtual hosts remain enabled. Move only the new FPM pool to backup, test FPM and gracefully reload after its Nginx use is disabled; never overwrite all shared config from backup. Keep dedicated certificate and private inventory/auth data for reconciliation, do not delete automatically. For a later app-only rollback atomically select the prior reviewed release and recheck auth/inventory compatibility; no data migration is present. Keep new service user unused until operator approves cleanup; no automatic user deletion. Recheck protected canaries and record checkpoint after rollback.

No approval is inferred from preparation or elapsed time. All targets/actions above need the operator's exact scope confirmation before execution.

## Repeatable execution from Git

Application source is frozen at 21c050b36e8ddd4cd3d7ec5e87a727f556348e9b. The tracked script reads those Git blobs, never a mutable working-tree app/template. Review script before running as root. Run each command separately and record checkpoint/evidence before continuing:

```bash
cd /opt/fallback
sudo -n python3 scripts/activate-admin.py prepare
sudo -n python3 scripts/activate-admin.py http
sudo -n python3 scripts/activate-admin.py certificate
sudo -n python3 scripts/activate-admin.py https
sudo -n python3 scripts/activate-admin.py verify
```

The fixed private backup directory stores verified backup archive, existing-config hashes and per-phase started/done timestamps. A phase is never blindly replayed: started without done means UNKNOWN; inspect actual files, services and certificate first. On a fresh server execute phases in order. On this server use verify for repeatable read-only verification. Do not delete markers to force a replay. A later release uses an explicitly reviewed release-update procedure, not this first-install tool.

Recovery within the approved scope: `sudo -n python3 scripts/activate-admin.py rollback`. It disables only the newly created lab vhost/pool, syntax-tests before graceful reload, retains all data, account, release and certificate, and checks unchanged pre-existing configs and protected canaries. Failure during rollback requires reconciliation rather than rerun. No complete shared-config restore is automatic.
