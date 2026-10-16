# Multiple app nodes and private configuration — FH-0017

Status: multi-node inventory and authenticated read-only project center are active at `lab.ventureout.cz`. The operator reached the authenticated admin page; live HTTPS checks cover the center route/assets and session revocation. Actual360/768/1440 fixture add/edit/disable and live inventory/center browser QA now PASS, as does exact previous/current immutable PHP release rollback. Production inventory/auth preserved; FH-0017 complete. Full original configuration recovery remains FH-0018. Historical implementation-stage claims below are superseded by state/catalog.json and latest acceptance checkpoint. Architecture extension requested by operator on 2026-10-15; no Coolify/runtime replacement or node operation was added.

## What exists and what remains

| Area | Verified result | Remaining gate |
| --- | --- | --- |
| M00 | Docs/resume/checkpoints/local commits | No automatic push |
| M01 | Oracle audit, reference canary, technical SSH and isolated Docker lifecycle; ctx1 fingerprint independently verified; backup/integrity/schedule operator-verified | Restore, external backup copy, backup-volume inclusion and independent external app checks |
| M02 | Public progress HTTPS page and private PHP multi-node admin live; read-only project center integrated under the same session | Full center visual QA and live rollback drill; separate operations controls remain local prototypes |
| M03 | Docker technical access works; operations-service proposal | Coolify/controller security review and explicitly approved installation/deployment |
| M04–M10 | Roadmap/design only | Routing, snapshots, switching, contact processing, resilience/continuity/release gates |

No overall percentage is claimed. Docker smoke-test success is not a complete infrastructure audit or production-deployment permission.

## Model

One independent Oracle gateway fronts multiple app nodes. Inventory schema v1 stores a single gateway and a list of up to 100 node records, not a single hardcoded counterpart. Future applications reference a node ID; per-host routing/health/fallback selects only that app's node. Loss of one home node must not cause cross-node failover or affect unrelated Oracle sites. Home Coolify remains the planned deployment control plane; the inventory UI is not a Docker-control implementation.

Node fields: stable unique ID, display name, address, SSH port/account, runtime (Docker/Podman/other), declared platform (LXC/VM/physical/unknown), enabled flag, opaque technical identity reference, expected host fingerprint and note. Runtime alternatives are inventory values only; Podman support is NOT implemented. All private address/account mapping is authenticated inventory, never public progress data.

Observed SSH, Docker and fingerprint results include provenance/timestamps and remain distinct from operator-declared platform/runtime. Changing host, port, user, runtime, identity reference or expected fingerprint resets old SSH/runtime evidence to UNKNOWN and fingerprint to NEEDS_TEST. Editing a name/note or enabled flag preserves dated observations. Entering an expected fingerprint does not attest it. Disabling a record changes inventory only; it does not stop containers or implement deployment policy.

## Implementation

- PHP 8.3, no framework, database, external package or JavaScript required. Public code is admin/public/index.php and admin.css; library/CLI are outside its document root.
- Private JSON inventory/auth/session files outside webroot and Git, directory 0700/files 0600. JSON writes are locked and atomic. Revision checks reject stale updates, duplicate IDs are rejected on creation, bounded audit of last 100 configuration mutations commits with inventory. This is a bounded configuration history, not a complete compliance audit or external backup.
- Single initial administrator, no registration or web bootstrap. Argon2id password hash; session ID rotation, strict session mode, Secure/HttpOnly/SameSite=Strict cookie, 30-minute inactivity expiry, POST-only mutation with exact Origin validation. Login uses exact Origin validation without depending on a pre-authentication session cookie; authenticated mutations and logout also require the session-bound CSRF token. Output escaping and no-store/CSP headers remain enabled.
- Login budget: 5 attempts per client IP and 50 total per 10-minute window. Process-local proxy headers are not trusted; source comes from server REMOTE_ADDR. The global limit trades availability for bounded login work; external auth/MFA and wider account management are future work.
- Web code never invokes SSH/shell, reads technical keys, queries Docker, installs software or submits broker jobs. Credential reference is a validated name, not a path. Actual operations still require the separately reviewed broker and privilege/identity gates.

References: [PHP password hashing](https://www.php.net/manual/en/function.password-hash.php), [session security settings](https://www.php.net/manual/en/session.security.ini.php), [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php). Controls are tested locally; these links are not proof of live deployment or complete security assurance.

## Seed and first administrator

ctx1 is prefilled in ignored `.local/admin/inventory.json` as Docker/LXC with the supplied private endpoint/account, opaque identity alias and existing dated SSH/Docker evidence. LXC/OS declarations remain historical; independent fingerprint remains NEEDS_TEST. No private key or its path is stored. This is protected operator working state, not a second public task/roadmap source.

Initial admin is provisioned locally with a unique random credential; app auth file stores its Argon2id hash only. Operator handoff credential is in `.local/operator/initial-admin.json`, mode 0600 beneath private directories, ignored and never served/copied to the web account. It was not printed in tool output or committed. Retrieve only in your private SSH terminal, never paste into chat. Production activation must copy only inventory/auth hashes and establish new private session directory under a dedicated web user; do not copy the plaintext handoff file or use the agent's personal account as PHP runtime.

`admin/manage.php` accepts JSON stdin for CLI-only seed/bootstrap; both refuse overwrite. `scripts/admin-config.py bootstrap --data-dir ... --username ...` offers hidden interactive password entry for a fresh installation; existing local admin must not be overwritten blindly. Existing installations need a separately scoped credential-rotation/recovery procedure. No public password reset endpoint exists yet.

## Verification and rollback

Black-box tests in tests/test_admin.py run PHP only on an ephemeral loopback listener with disposable test state/credentials and explicitly enabled loopback HTTP mode. They exercise authentication, cookie flags/session rotation/logout, CSRF/Origin, denied private paths, multi-node persistence, disabled state, stale-write conflict, duplicate IDs, output escaping, forged observation/key fields, malformed targets, evidence invalidation/preservation, login throttling, bootstrap/seed overwrite refusal and concurrent process locking. Public-export tests remain separate.

Production defaults require configured HTTPS origin; loopback mode must not be set in deployment. No live service, FPM pool, Nginx host, certificate, OS user or home change performed for this feature. Browser/mobile visual review is still unverified if no browser is available. Actual local ctx1 login check is reported separately in checkpoint; private values/credentials never enter test output.

Repository rollback: reviewed revert. Before any later config edit/deployment, take a protected inventory/auth backup; restore under the same lock after maintenance, preserve revision/audit continuity, invalidate sessions after an auth restore. Initial seed/bootstrap refuses overwrite. Exact live activation/rollback scope: docs/ADMIN-ACTIVATION.md. Do not infer production approval from a successful local test.

## Activation update — 2026-10-15

Explicit operator approval was followed by private backup, dedicated unprivileged web account/FPM pool, root-managed frozen application release, lab vhost and dedicated Certbot certificate. Real HTTPS login, ctx1 Docker inventory and logout passed without inventory mutation. Public progress publishes each verified/failed increment. Exact interruptions, checks and recovery are in ADMIN-ACTIVATION.md and checkpoints; journal prevents blind replay. Browser/mobile QA and operational rollback drill remain unperformed. No broker/remote operations implemented.
