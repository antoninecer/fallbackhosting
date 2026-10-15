# Protected control-center integration — reviewable proposal, not activated

The local prototype now has a same-session PHP delivery adapter. This proposal narrows deployment to an application release update of the existing lab administration. Existing public project host, Nginx/PHP configuration, certificate, users/groups, private inventory/auth, SSH and home runtime remain unchanged. The adapter is locally tested; no production release has been switched for this feature. Local browser integration also reproduced a pre-existing login bug in the frozen source: no-referrer caused Origin: null for form POST and strict validation rejected it. The reviewed new source uses Referrer-Policy: same-origin so same-origin forms preserve Origin while cross-origin referrers remain suppressed. CSRF and exact-origin checks are unchanged. Live frozen source was verified to still contain the old header; this correction is not yet active.

## Exact target and behavior

Entry: `https://lab.ventureout.cz/?center=index.html`. Existing administrator logs in at `/`, then opens “Řídicí centrum”. Back link returns to server administration for logout. Every HTML, CSS, JS, TXT and manifest request goes through existing `/` PHP front controller and the same session/origin/HTTPS validation. No new public registration, credential, cookie namespace, password reset or technical-user access.

The closed query allowlist is index.html, center.css, center.js, resume.txt, manifest.json. Unauthenticated access returns 401 for every file. Logout and 30-minute inactivity expiration revoke all file access. Only GET/HEAD are accepted; unknown/array/traversal names return 404, other methods 405. Responses use no-store, nosniff and existing frame/CSP controls; resume is a plain-text attachment. Asset hashes and bounded sizes are verified before serving, and missing/corrupt/oversized/symlinked artifacts fail closed with 503. No inventory read is needed to serve the center after authentication.

The artifact is selected at build time with `python3 center/build.py --delivery admin-query`. It references `/?center=...` for all protected local assets. Static development mode remains separately labeled local-only and does not imply authentication. `FH_CENTER_ARTIFACT` exists only for disposable loopback tests; production uses the fixed release sibling `center-artifact/`, so no FPM pool environment change is needed.

## Exact release layout

New immutable directory under `/var/www/fallback-admin/releases/<reviewed-full-commit>-center/`:

- public/index.php and public/admin.css from the reviewed commit;
- lib.php and center.php from that same reviewed commit, outside public/;
- center-artifact/index.html, center.css, center.js, resume.txt and manifest.json from the reviewed validated catalog, generated in admin-query mode.

The current root-managed symlink remains `/var/www/fallback-admin/current`. All new release directories 0755 and files 0644, root-owned and non-writable by fallback-web; generated output is copied only from an exact verified build, never from mutable public/. Private `/var/lib/fallback-web/admin/` stays intact. No bootstrap, seed, credential rotation, database migration or private-state overwrite. Root-managed ownership and parent modes must be verified; PHP also refuses writable artifact directory/files outside explicitly enabled loopback test mode.

Before activation, freeze and record the full source commit, artifact SHA-256 manifest/digest, total byte size (maximum 2 MiB), previous current link and protected private backup path in a checkpoint. Use Git blobs or an archive of that exact commit, not the working tree. The implementation completion checkpoint identifies the local source revision; the activation checkpoint must name the exact reviewed release/artifact. No release switch is performed by build.py.

## Ordered activation checks for a later explicitly scoped operation

1. Reconcile Git, live current link and root-owned frozen source, account/pool/vhost and private runtime modes. Obtain fresh reference route/TLS/assets and project/admin baselines. Existing rate-limit responses are recorded, never reconfigured or accepted as a successful app baseline.
2. Create a new private root-only backup directory `/var/backups/fallbackhosting-center-<UTC>/` with exact current-link/release manifest and a protected inventory/auth backup for recovery; verify readability privately. Never put backups or confidential hashes/logs on public routes.
3. Build and validate the exact reviewed source offline, run all repository tests and local authenticated browser checks; verify artifact hashes/size. Prepare only the new root-managed release, checking all five artifact hashes and code hashes and fallback-web read-only access. Do not copy test credentials or loopback flags.
4. Atomically replace only `/var/www/fallback-admin/current` with the new release. No Nginx or PHP reload/restart is included in this proposed application-only switch. Poll bounded readiness; verify actual served release/content and auth, not only HTTP 200. PHP realpath/opcache caching may delay recognition: if the verified release is not observed within the chosen bounded maintenance window, restore the prior pointer and stop. A service reload would require a separately recorded exact action/canary scope.
5. Test anonymous direct requests for all five assets, valid current admin login, center navigation, all protected MIME/hash headers, clipboard/download, logout and direct-file denial. Use credentials privately in memory; no credentials/raw HTML/private inventory output. Ensure inventory/auth bytes unchanged. Test expiry/malformed/corrupt/method cases only in disposable local environment, not by damaging a live artifact.
6. Recheck reference/project/admin route/TLS/assets and unrelated shared config hashes. Verify old CSS/private/source paths remain appropriately isolated and center-artifact/ has no direct web route. The existing admin CSS remains the intentionally public login stylesheet; center assets do not.
7. Publish reviewed public event/checkpoint and commit/push verified evidence. Keep any runtime uncertainty NEEDS_TEST. The old activation script verifies the original frozen source and must not be blindly reused to assert a new release is valid; a reviewed new-release verifier is an explicit remaining prerequisite.

## Rollback

Retain the exact original current symlink/release. If any center or existing-admin acceptance fails, atomically restore only that prior link, then verify actual old application behavior, original admin login/logout/inventory, public progress and protected production canaries. No private-state rollback is needed because this update makes no inventory/auth migration. Do not delete either release, private data, certificate or account. If runtime caches prevent verification of rollback, record UNKNOWN and use a separately authorized narrow FPM recovery plan; never restart the host or blindly rerun first-install tooling.

## Verified locally and remaining gates

Unit/HTTP tests cover all asset session gates, logout, expiry, direct paths, methods, HEAD, MIME/cache, corruption/missing/oversize/symlink failures and unchanged disposable inventory. Browser integration uses only disposable PHP data and account, at 360/768/1440, and checks actual form login, protected CSS/JS/TXT/manifest delivery, clipboard/download and post-logout denials. Source code is reviewable in admin/center.php and admin/public/index.php.

Remaining before production: full source/artifact freeze, dedicated new-release verifier, fresh shared-production baseline, exact activation checkpoint, production identity/permission checks and actual rollout/rollback evidence. This design does not close M02 home-outage independence tests or remote SSH/agent privilege gates. No production activation is claimed by this document.

## Offline staged-release verification

Implemented read-only prerequisite: `scripts/verify-center-release.py`. Run against an immutable staged release with `--revision <full-reviewed-commit>` and `--artifact-manifest-sha256 <separately-reviewed-sha256-of-manifest.json>`. For production staging also require `--require-root-owned`. The separately retained digest must come from the reviewed local build, not be discovered from the target being checked.

The verifier compares all four PHP/CSS source files against Git, requires the exact artifact/file set, validates pinned manifest and every bounded artifact hash, requires authenticated asset URLs, rejects symlink paths and nonordinary files, and checks exact 0755/0644 modes. Root ownership is explicitly NOT_CHECKED without the flag. No copying, switch, network request, credential handling, reload or restart exists in this tool. Use only with a quiescent operator-controlled immutable directory; this is not a defense against a concurrent privileged writer.

Four isolated fixture tests pass, including corruption, unwanted files, symlinks, modes, missing files and incorrect revision/manifest pins. No actual new production release has been staged or verified. Runtime PHP syntax/behavior, web-user access, authentication, TLS/canaries, readiness and rollback remain separate acceptance steps. This tool replaces only the missing offline content-verification prerequisite; it does not replace the future live release verifier.
