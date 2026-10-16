# Guided Coolify installation — FH-0023

The operator requested removal of the manually installed controller and a trial through the authenticated lab application. This first template reinstalls the already prepared Coolify 4.4.6 stack on ctx1, using its retained data/volumes and cached immutable images. It is not a general image/Compose runner or a fresh-server installer. The prior controller had no users; account creation refuses a nonempty user table.

2026-10-16 actual trial: exactly one authenticated HTTPS browser request completed SUCCEEDED, all three services healthy, native owner created and registration disabled; native browser login/logout also passed. The operator-authorized credential correction subsequently synchronized lab and Coolify to a generated 16-character password with all four required groups, stored only in the ignored operator JSON. Never replay the installation/bootstrap against this now-enrolled instance. Broader deployment-target enrollment and demo deployment remain separate M03 gates.

## Operator flow

In `lab.ventureout.cz`, open **Aplikace**, select the verified Docker node, read the template explanation and fill the initial administrator email, password and password confirmation. The wizard explains three services, resource limits, retained data, separate Coolify credentials and private access. It displays worker availability and requires an explicit installation checkbox. It never requests an SSH key or command. A missing worker rejects submission before saving credentials.

Passwords must contain lowercase and uppercase letters, a digit and a symbol, without spaces (12–128 characters accepted). The operator generator `scripts/generate-admin-credential.py` defaults to 16 random characters and guarantees all four groups before writing a new private file. The initial incompatible generated password was replaced, not silently modified by the installer.

After submission, the status page refreshes every five seconds. It displays only fixed stages/outcomes and timestamps. Success requires healthy services, creation of the native admin with a matching password hash, disabled registration and an unchanged unrelated workload. Native browser login is a further acceptance check; health alone is not that check. No public Coolify URL is created by this feature.

## Technical boundary

- PHP authenticates the existing admin and enforces exact Origin plus session CSRF for both plan and submit. Plans bind the node and inventory revision; changed configuration requires a new plan. Only the fixed template is available. Caller command/image/path/host fields are rejected.
- The private 0700 request directory contains 0600 structured requests and a separate short-lived 0600 account-secret file. Email/password never enter request history, status files, public exports or logs. The worker deletes the secret on completion or rejection; expired/unprocessed requests need operator cleanup under the same private boundary. No credentials are stored in the draft session.
- A root-managed policy fixes the technical endpoint/account, node, actor and template hash independently of browser configuration. PHP never holds SSH keys or signing roots. The worker accepts one operator-authorized attempt per invocation, uses strict existing ED25519 host trust and fixed argument arrays, and sends only encoded data over SSH stdin. No caller-selected shell, image, mount or environment option is accepted.
- The worker pins queue directory descriptors to prevent directory/symlink substitution, rejects symlinks/hardlinks/unsafe modes, duplicate fields, excessive sizes, stale requests and wrong scopes. Root-owned attempted/started/done markers prevent replay. Interrupted dispatch blocks further worker invocation pending reconciliation. Timeouts and incomplete verification become UNKNOWN and are never retried automatically.
- The remote fixed payload checks the exact retained Compose checksum, expected service set, pinned images, private-only bindings, retained volume labels and pre/post unrelated workload baseline. It uses the reviewed native RootUserSeeder with credentials passed only through process environment. Existing users are never overwritten. No broad cleanup, volume deletion or host Docker/SSH/network changes are exposed.

This is a bounded trial worker, not a new system service. The existing agent's broad sudo and destination Docker-group access still do not establish tenant/key privilege isolation. Do not describe this as the fully hardened general broker from FH-0013/FH-0015.

## Starting the scoped trial

Install only verified committed worker/source files into the immutable root-owned app release. Keep a 0600 root-owned policy and 0700 ledger outside PHP's open_basedir. The policy contains queue/ledger paths, allowed node/actor, independently captured host/user/port, template checksum, web UID/GID and the immutable remote source path; never commit the policy. The request directory is 0700 owned by the web account.

Run as the authorized operator, using the exact private policy path:

```text
python3 <immutable-release>/installer/install_worker.py --policy <root-private-policy> --wait-seconds 1800
```

One invocation waits at most 30 minutes for one request; it then exits after that attempt. Readiness is withdrawn before dispatch and on exit. The wizard rejects a new submission when the heartbeat is stale or unavailable. A persistent service is separate future work and must not be silently installed.

## Checks and rollback

Tests cover authenticated HTTP/Origin/CSRF/verified-node gates, stale plans, unknown command/image fields, credential mismatch/private storage/nonexport, one-shot/replay/expiry, input file attacks, timeout/partial failure and fixed remote bootstrap. `scripts/check-install-browser.py` exercises a disposable PHP instance and inert worker at 360/768/1440 with no real SSH/Docker changes. Screenshots contain only fixtures and remain ignored/private.

Before app release switch, preserve its exact predecessor and verify production canaries. Rollback restores only that symlink, preserves inventory/requests/ledger/data, withdraws worker readiness and rechecks canaries; graceful PHP-FPM reload is used only when needed to clear the release path cache. After a dispatched install, reconcile exact current container IDs and account status before any rollback/retry. Retained volumes/data must never be deleted by a generic uninstall.
