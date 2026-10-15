# lab.ventureout.cz — exact activation proposal

Status: historical static-only proposal, not deployed. Superseded for the requested private admin by docs/ADMIN-ACTIVATION.md; do not execute this older static procedure as the admin deployment. User clarified this is the actual future platform address; project.lab.ventureout.cz remains progress reporting. Initial publication is a truthful static introduction, not an admin panel or deployment interface. Full workflow: docs/PLATFORM-WORKFLOW.md.

## Exact targets/actions requiring approval

- Create `/etc/nginx/sites-available/lab.ventureout.cz` and symlink `/etc/nginx/sites-enabled/lab.ventureout.cz`; use deploy/lab-http.conf, then deploy/lab-https.conf.
- Dedicated Certbot webroot certificate for `lab.ventureout.cz`, under `/etc/letsencrypt/live/lab.ventureout.cz/` with its own renewal/archive records. Existing account and timer, no wildcard or other certificate replacement.
- Private backup `/var/backups/fallbackhosting-lab-20261015/` before gateway work.
- Two `nginx -t` gated `systemctl reload nginx` operations, plus scoped rollback if needed. No restart.
- Serve only generated `/opt/fallback/lab-public/index.html` and style.css. Build via `python3 portal/build.py` as repository owner. No database, PHP service, new listener port, login or Docker management exposed.

This approval does not permit other vhost edits, DNS/firewall/SSH/Tailscale/home changes, deployment platform installation, or Git push. Shared Nginx reload is the operational risk. Backup, baseline/canary and new-host-only rollback follow the already-used project deployment procedure.

## Commands (not yet executed; root only after approval)

First confirm external DNS A/AAAA and target absence (including broken symlinks), rerun local tests/build, record reference/project assets/TLS and unrelated root baseline. Stop on unexpected state.

```bash
test ! -e /etc/nginx/sites-available/lab.ventureout.cz
test ! -L /etc/nginx/sites-available/lab.ventureout.cz
test ! -e /etc/nginx/sites-enabled/lab.ventureout.cz
test ! -L /etc/nginx/sites-enabled/lab.ventureout.cz
test ! -e /var/backups/fallbackhosting-lab-20261015
install -d -m 700 /var/backups/fallbackhosting-lab-20261015
tar -czf /var/backups/fallbackhosting-lab-20261015/nginx-before.tgz -C /etc nginx
tar -tzf /var/backups/fallbackhosting-lab-20261015/nginx-before.tgz > /dev/null
nginx -t
install -m 644 /opt/fallback/deploy/lab-http.conf /etc/nginx/sites-available/lab.ventureout.cz
ln -s /etc/nginx/sites-available/lab.ventureout.cz /etc/nginx/sites-enabled/lab.ventureout.cz
nginx -t
systemctl reload nginx
```

Verify protected reference and project endpoints plus HTTP ACME path before Certbot. External web-tool preflight was unavailable for the project deployment; successful ACME validation is independent external challenge evidence. If the challenge fails locally, stop before issuance.

```bash
certbot certonly --webroot -w /opt/fallback/lab-public -d lab.ventureout.cz --cert-name lab.ventureout.cz --non-interactive
install -m 644 /opt/fallback/deploy/lab-https.conf /etc/nginx/sites-available/lab.ventureout.cz
nginx -t
systemctl reload nginx
```

Allow the asynchronous reload transition to settle before checking HTTPS; use bounded readiness retries, never disable TLS verification. Check page and CSS 200, valid domain certificate, expected content/CSP, HTTP→HTTPS redirect, source/admin/PHP paths 404, no forms, and correct link to project. Recheck protected route/TLS/assets, project and other baseline statuses. Inspect dedicated renewal webroot and timer; no automatic renewal dry-run. Browser/mobile review and home-failure tests must be accurately recorded as unverified if unavailable.

## Rollback

Move only the newly created lab symlink and configuration into this lab backup directory; run nginx -t then reload. Before first successful reload, remove the proposed host from enabled config by these same moves without unnecessary reload. Do not restore the entire shared backup over concurrent changes. Leave dedicated certificate unused; no automatic certificate deletion. Recheck both project and production reference. Record evidence and checkpoint before marking task complete.
