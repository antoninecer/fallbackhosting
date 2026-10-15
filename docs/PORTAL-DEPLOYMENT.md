# Public project presentation — deployment proposal

Status: local build and HTTP checks PASS; production activation awaits exact operator approval and privileged execution. Task FH-0009, M02. No infrastructure commands below have been executed by this task.

## Scope and benefit

Publish https://project.lab.ventureout.cz as a public static progress presentation. No PHP, database, application service, Docker or home dependency. No administration, raw state download, operational inventory or shell execution is exposed. The protected future control center remains separate. The operator requested this public projection on 2026-10-15.

Exact live targets:

- New `/etc/nginx/sites-available/project.lab.ventureout.cz` and matching symlink `/etc/nginx/sites-enabled/project.lab.ventureout.cz` only.
- New dedicated certificate `/etc/letsencrypt/live/project.lab.ventureout.cz/`, its Certbot archive and renewal configuration; use existing ACME account if available. No wildcard certificate or replacement of existing certificates.
- Backup `/var/backups/fallbackhosting-project-20261015/` outside public repository.
- Two syntax-checked `systemctl reload nginx` operations: HTTP ACME host, then HTTPS host. Never restart Nginx.
- Webroot `/opt/fallback/public/` serves only generated index.html, style.css and app.js. Existing generic Certbot renewal timer must cover the new webroot certificate; do not install or change timers.

No DNS, firewall, SSH, Tailscale, existing app/vhost or home changes. Current `tonda` account lacks the required write/read permissions. Run privileged steps through the operator's authorized root session; do not bypass with sudo without explicit operator authorization for these exact commands.

## Preconditions / risks

DNS A resolves to expected gateway; target HTTPS currently fails hostname verification. Check A and AAAA externally before issuance; stale IPv6 must be resolved by the operator, never changed automatically. Confirm HTTP challenge is reachable publicly. Shared Nginx reload is the principal risk; ACME may fail or rate-limit. No reload if syntax/canary fails. Check all unrelated sites the operator identifies; the Quantum reference canary alone is not proof of every production workflow.

The initial audit's symlink-only vhost list was incomplete; regular files also exist. Do not use it as an exhaustive change inventory.

## Proposed activation commands (approval required)

In the repository as its normal owner:

```bash
cd /opt/fallback
python3 -m unittest discover -s tests -p 'test_portal.py' -v
python3 portal/build.py
```

In an authorized root session, execute one stage at a time and inspect every result. Stop on any failure. `test ! -e` and `test ! -L` must both succeed before creating the vhost; an existing path requires reconciliation, not overwrite.

```bash
test ! -e /etc/nginx/sites-available/project.lab.ventureout.cz
test ! -L /etc/nginx/sites-available/project.lab.ventureout.cz
test ! -e /etc/nginx/sites-enabled/project.lab.ventureout.cz
test ! -L /etc/nginx/sites-enabled/project.lab.ventureout.cz
test ! -e /var/backups/fallbackhosting-project-20261015
install -d -m 700 /var/backups/fallbackhosting-project-20261015
tar -czf /var/backups/fallbackhosting-project-20261015/nginx-before.tgz -C /etc nginx
nginx -t
curl --fail --silent --show-error --connect-timeout 5 --max-time 15 -o /dev/null https://dashboard.api.ventureout.cz/cards32.php
install -m 644 /opt/fallback/deploy/project-http.conf /etc/nginx/sites-available/project.lab.ventureout.cz
ln -s /etc/nginx/sites-available/project.lab.ventureout.cz /etc/nginx/sites-enabled/project.lab.ventureout.cz
nginx -t
systemctl reload nginx
```

Before ACME, recheck protected reference TLS/route/assets and verify a temporary public challenge file via an independent external vantage; use a nonsecret token in the webroot ACME subdirectory and remove only that exact owned test file afterward. Failure blocks certificate issuance. Then, with an existing ACME account selected (or operator-managed account registration if absent):

```bash
certbot certonly --webroot -w /opt/fallback/public -d project.lab.ventureout.cz --cert-name project.lab.ventureout.cz
install -m 644 /opt/fallback/deploy/project-https.conf /etc/nginx/sites-available/project.lab.ventureout.cz
nginx -t
systemctl reload nginx
```

Do not use Certbot's automatic Nginx editor. Review Certbot output and generated renewal settings. Account email/credentials never enter Git. Existing timer observation does not establish successful renewal; separately approve and schedule any ACME staging renewal test.

## Verification and acceptance

```bash
curl --fail --silent --show-error --connect-timeout 5 --max-time 15 -I https://project.lab.ventureout.cz/
curl --fail --silent --show-error --connect-timeout 5 --max-time 15 -I https://project.lab.ventureout.cz/style.css
curl --fail --silent --show-error --connect-timeout 5 --max-time 15 -I https://project.lab.ventureout.cz/app.js
curl --silent --show-error --connect-timeout 5 --max-time 15 -I http://project.lab.ventureout.cz/
curl --silent --show-error --connect-timeout 5 --max-time 15 -I https://project.lab.ventureout.cz/state/current.json
curl --silent --show-error --connect-timeout 5 --max-time 15 -I https://project.lab.ventureout.cz/.git/config
curl --fail --silent --show-error --connect-timeout 5 --max-time 15 -o /dev/null https://dashboard.api.ventureout.cz/cards32.php
```

Assert HTTPS page/assets 200 with valid hostname/TLS and correct content types, HTTP redirect only to this HTTPS hostname, raw source routes 404, CSP header present and no external dependencies. Confirm expected page title/marker and generated checkpoint matches canonical state. Repeat reference route and its same-origin assets checks; test other identified protected vhosts as agreed. Record actual timestamps/results. Browser QA at 360/768/1440 px and task filtering remains required; no browser tool was available during local build. Infrastructure-failure independence is designed but not fault-tested.

## Rollback (same scoped approval)

If proposed config fails `nginx -t`, do not reload. For a failure before first reload, move only the newly created vhost and symlink into the backup directory and re-test. After either reload, rollback:

```bash
mv /etc/nginx/sites-enabled/project.lab.ventureout.cz /var/backups/fallbackhosting-project-20261015/disabled-project-symlink
mv /etc/nginx/sites-available/project.lab.ventureout.cz /var/backups/fallbackhosting-project-20261015/disabled-project.conf
nginx -t
systemctl reload nginx
```

Recheck protected production canary. Do not restore the entire Nginx backup over unrelated concurrent changes; inspect exact differences. Keep the newly issued certificate unused; do not delete certificates or revoke automatically. No fallback live app state or databases were altered. Local source rollback is a reviewed Git revert. No automatic push.

## Keeping the page current

After each verified stage, update canonical TASKS.md, ROADMAP.md, state/current.json and checkpoint first, then run `python3 portal/build.py` as repository owner. This copies no operational document bodies and opens no ports. New task IDs require reviewed public labels in portal/build.py; unknown statuses/references fail the build and preserve the previous page. The artifact is ignored in Git and rebuilt from committed sources. Serving is read-only; build changes are deliberate operator/agent actions, not a cron job or public request.

Static explanatory copy in portal/build.py must also be reviewed as capabilities change. This presentation is not the full canonical schema migration (FH-0006). Build timestamp and checkpoint timestamp are explicit; no agent heartbeat or live health is claimed.
