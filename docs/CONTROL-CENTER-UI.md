# Read-only control center — local prototype

The FH-0007 artifact is a repository-local static prototype, not a deployed or authenticated service. The existing public project page and live lab inventory administration remain separate. No home, Docker, Tailscale, database, external asset, CDN or runtime GitHub dependency is needed to render it. Source links intentionally open the public Git repository when clicked; evidence files are not copied into the artifact.

## Build and boundary

Run `python3 center/build.py`. Output is restricted to `.local/control-center/`: content-addressed immutable releases and atomic `current` symlink. Each release contains exactly index.html, center.css, center.js, resume.txt and a SHA-256 manifest. Attempts to target public/ or another location outside repository .local are refused. Failed validation/build keeps the last selected release. Existing release bytes are checked before reuse. Build output and screenshots stay ignored, outside every configured public webroot.

No authentication is implemented by this static prototype. Do not expose its local test server externally or copy the artifact into the public presentation. FH-0008 must define and verify authentication for every route, stylesheet, script, resume file and manifest, including direct-file requests, before activation. This artifact does not implement SSH, Docker or deployment actions and does not grant access to any technical key or private inventory.

## Modules

- Overview: current canonical task, status and dated checkpoint; explicit saved-state notice.
- Tasks: mobile cards, filter, acceptance, owner, scope, dependencies, rollback and evidence links; keyboard-operated details.
- Milestones: acceptance criteria and evidence, preserving the canonical records.
- Incidents: classified cause provenance and empty-state notice; no invented incident-free claim.
- Health: historical versus observed result, expiry and UNKNOWN/STALE behavior; no green current-health claim from historical PASS.
- Agent: explicitly dated catalog activity snapshot, not inferred process liveness or heartbeat.
- Procedures: three reviewed summaries and source links, no raw runbook or private connection configuration copied.
- Resume: required readings, actual snapshot/checkpoint/task IDs and safety boundaries; copy, manual selection fallback and plain-text download. No action is executed.

Canonical UTC remains in machine/resume metadata; human-facing timestamps display Europe/Prague. The prototype validates catalog/current-task consistency, rejects unknown references and escapes text and textarea content. Only selected current-state fields are used; raw summary, warnings, SSH transport, operational mapping and private data are excluded. Public progress remains its own reviewed projection and does not export the prototype modules.

## Reproducible verification

`python3 -m unittest discover -s tests -v` covers local export, injection, missing/stale data, resume context, public-output denial, atomic failure preservation and immutable release tampering, in addition to existing catalog/admin/public tests.

Optional browser check with independent Playwright/Chromium: `python3 scripts/check-center-browser.py`. It creates only an ephemeral 127.0.0.1 listener serving the exact generated release, tests 360/768/1440, eight modules, five filters, keyboard focus/details, clipboard/download and long Czech text, then stops its listener in finally. Screenshots/report are saved under ignored .local/qa. No credentials are used. Clipboard automation requires browser support; the application offers a manual selection and download fallback.

Current temporary tooling uses `/tmp/fallback-browser-venv`, `/tmp/fallback-browser-cache` and shared libraries extracted into `/tmp/fallback-browser-libs`. No system packages were installed. These are not production dependencies and may disappear after reboot/cleanup. Browser evidence is headless Chromium, not physical-device or multi-engine certification. Exact timestamps/results are in checkpoints.

## Rollback

Repository changes: reviewed Git revert. Local artifact: atomically select a previously verified release under .local/control-center/releases and verify its manifest; do not change production links. Build-failure retention is tested. Operational deployment/rollback is separate FH-0008 work and remains unperformed by this UI task.
