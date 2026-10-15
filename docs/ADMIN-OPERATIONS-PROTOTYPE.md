# Local PHP / isolated operations integration

FH-0021 prepares an actual PHP-to-Unix-socket client and a read-only operations page against the fixture broker. Nothing is installed, exposed through a production route or connected to SSH. The existing live inventory remains on its frozen release; signing roots/private keys are never read by PHP.

## Components and representation

- `admin/operations-client.php`: trusted backend-configured Unix path and signed structured request; no shell/process execution, command strings or caller-selected remote destination. <=16 KiB request/response, 2-second connect and absolute 20-second overall I/O deadline, partial-frame handling and generic errors without socket/token/raw internals. PHP empty-object normalization preserves signed empty params across JSON roundtrip.
- `admin/operations-view.php`: scoped application/node bindings, full registered container ID and last observed state/time, requested actions, QUEUED/RUNNING/SUCCEEDED/FAILED/UNKNOWN outcomes, errors and selected audit. It marks current availability unverified and saved state historical; bindings alone never imply a currently connected server. Prague display time, escaped text, empty/error states and mobile job cards.
- `admin/operations.css`: bounded scrollable audit and responsive desktop table/mobile cards.
- `operations/core.py` read views: signed inspect-scoped access to one application; at most 16 recent job/audit rows to remain inside framing bounds. Logs, policy, authorities, capabilities, private endpoints and credentials are absent from view output.

No operation is executed from this web prototype. The fixture CLI client exercises real framed PHP/broker messages and the inert Docker driver. Web mutation controllers/worker dispatch and independently trusted identity/approval issuance remain future activation prerequisites. The cleanup policy is implemented in core fixtures: stop separately, then remove only a registered ownership-checked full ID with one-use approval; no prune/volumes/unrelated resources.

## Tests

`python3 -m unittest discover -s tests -p test_php_operations.py -v`: real PHP subprocess + private Unix socket + SO_PEERCRED broker + fake driver. Tests cover all lifecycle/read paths, exact confirmed removal, unrelated-resource preservation, inability to mint identity/approval or change project, oversized/broken frames without internal leakage, view schema rejection, escaping and empty state.

`python3 scripts/check-operations-browser.py` with optional isolated Playwright/Chromium: generates only ignored .local/qa files, starts/stops a loopback static artifact server and tests 360/768/1440. Two independently scoped fixture applications/nodes show actual captured transient RUNNING and UNKNOWN jobs, errors and audit; the running fixture finishes after capture. The saved page never promises it remains running. Only generated HTML/CSS is served; no tokens, SQLite or fixture authority files are in that webroot.

Raw fixture state and screenshots are not Git/public dashboard data. Full-suite results and timestamps are in checkpoints. This tests headless Chromium and a local mock transport, not production RBAC deployment or physical devices. Rollback is a reviewed source revert; temporary sockets/listeners/state are removed by fixture teardown. No production or infrastructure rollback occurred or is claimed.
