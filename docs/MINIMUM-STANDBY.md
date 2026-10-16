# Minimum composable standby slice — FH-0025

## Verified scope

One explicitly reviewed public demo page, stylesheet and JPEG are exported from the owned remote demo. The HTML adapter removes active markup/forms and replaces unsupported links/ordering with a local contact section. CSS with external/active dependencies, redirects and cookie-bearing responses are rejected. ImageMagick creates a stripped <=800×500 WebP. This is an intentionally bounded first adapter, not a general WordPress crawler, login export or complete backup system.

Independent Nginx serves live HTTP via the existing tailnet and intercepts backend errors to the already-built local version. Manual/scheduled maintenance closes access to the backend before a POST can reach it. Standby returns HTTP503 with Retry-After/no-store/noindex and an explicit notice, never false order success. Assets stay local. A separate unprivileged gate checks the actual app marker and requires three successes before reopening; health failure after a maintenance window is OVERRUN. No request calls Coolify or PHP to serve the public copy.

The first demo uses a fixed small owned BusyBox image/container with no persistent volume; it is not a WordPress deployment or real ordering system. Current operator-only demo driver is not a web command API. Actual test-stop/start preserves all earlier remote containers.

## Reusable pieces

- `standby/snapshot.py`: bounded export, sanitization, installed ImageMagick, immutable manifest and atomic current pointer.
- `standby/gateway.py`: reviewed Nginx locations, independent health gate, persisted manual/windows policy and stable recovery.
- `standby/backup.py`: portable tar+manifest, bounded strict isolated extraction, checksums and no overwrite.
- `operations/standby_backup.py` / `standby/transport.py`: explicit operator-only fixed SSH repository adapter. A normal private directory is sufficient; no root Docker socket or new backup daemon is required. Later a specifically approved mounted USB path can be another repository provider.
- `standby/recovery.py` / `scripts/discover-standby-backups.py`: bounded read-only catalog discovery and a selected isolated restore preview, with format/integrity/provenance distinctions. No automatic publish or controller/database restore is implied.
- `standby/control.py`: maintenance/status/window control over the existing bounded peer-authenticated Unix protocol, with revision checks and bounded audit. No SSH/Docker/commands or arbitrary origins are accepted from the web.
- `admin/standby.php`: existing administrator/session/Origin/CSRF boundary, Prague-time conversion including DST ambiguity rejection, manual/automatic buttons, one scheduled interval, announcement preview and clearly dated health/backup evidence.

The PHP socket client and framing are reused from the operations prototype. New applications/export/backup/proxy providers should add an adapter/configuration, keeping public serving independent; arbitrary unreviewed images/scripts are not an adapter interface.

## Operator tools

`scripts/standby.py` supports export, verified publish/rollback, backup, isolated restore, isolated Nginx config, bounded health watch and manual maintenance. `scripts/standby-remote-backup.py` requires an explicit execute flag, verified inventory identity, and copies/readbacks/restores one owned static archive. Credentials are never argv/output. Examples use approved private configuration only; never expose source origins/inventory/policies through public status.

CLI export is still an operator step; the first UI controls maintenance/scheduling and shows the last verified release/backup. General app onboarding, generic crawling, customer messaging delivery, cross-version controller/database/VM recovery and a redundant second public edge are separate increments.

`scripts/publish-standby.py` composes export, remote archive upload, independent readback, bounded isolated restore and only then atomic publication. Failed backup leaves the last published release untouched. Discovery verified three actual owned copies without using Coolify; each was fetched and independently restored again before recording the exact static-scope restore attestation. Catalog provenance is pinned-SSH repository trust, not a signed archive or proof that a compromised repository is trustworthy. Bootstrapping private/controller secrets requires a separately reviewed authenticated/encrypted format and independently recoverable identity/key material.

## Public activation — deployed and verified 2026-10-16

Live public URL `https://lab.ventureout.cz/demo/`; authenticated controls `https://lab.ventureout.cz/?standby=1`. Existing TLS/DNS are reused, no wildcard/certificate change. Scope is exactly:

1. Add only the generated `/demo/`, its local asset location and an internal standby location to `/etc/nginx/sites-available/lab.ventureout.cz`; preserve both existing hosts/root/PHP routes. Candidate is built against the observed file hash and syntax-checked in a complete shadow configuration.
2. Create only new public-static tree `/var/www/fallback-standby-demo/` and protected service tree `/var/lib/fallback-standby-demo/`. Static release copied from the verified, remote-backed artifact, root-owned immutable code/policy separate from writable runtime.
3. Install exactly `fallback-standby-demo.socket` and `fallback-standby-demo.service` under `/etc/systemd/system/`, register/start/enable only those new units. Socket is private to the existing web account; service runs as existing unprivileged www-data with a strict filesystem/resource sandbox and no SSH keys. It only probes a fixed app and changes its own demo gate.
4. Stage/verify a new immutable lab PHP release with maintenance page/client, switch the existing current pointer and perform one syntax-tested graceful PHP-FPM reload for cache reconciliation, as in the earlier approved release flow.
5. Back up the exact original vhost and previous release pointer, verify unrelated reference/project/admin/Coolify health; nginx syntax test; one narrow Nginx reload; actual TLS/browser/dynamic controls/denial/outage/recovery checks after activation.

Operator explicitly approved this exact prepared scope and further deployments within the application scope. Activation completed; real HTTPS browser360/768/1440, auth/CSRF/Origin, manual/scheduled maintenance, remote-demo outage, worker independence and stable recovery all PASS. Root-owned frozen source22cec4b is active. Full116 tests and protected canaries PASS; auth/inventory and unrelated configs unchanged. This supersedes earlier prepared/not-applied records. AGENTS.md exact-target restrictions remain for new unrelated infrastructure changes. No DNS/firewall/VPN/disk changes or host/container recreation are needed for this candidate.

Rollback: stop only these new units, disable their startup; restore only the exact backed-up lab vhost/current pointer; syntax-test and narrowly reload affected services with canaries. Keep snapshots, archives, private policy/journal and remote demo for reconciliation. Do not restore unrelated gateway configuration, delete volumes, prune or blindly repeat a partial activation.


Acceptance evidence: `checkpoints/20261016T084056Z-FH-0026-public-live-pass.md`. Actual shared live activation rollback has not been exercised; the private original-vhost/current-pointer backup and guarded rollback are retained. Static snapshot restore and atomic publication rollback were tested.
