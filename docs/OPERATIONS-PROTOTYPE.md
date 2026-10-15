# Isolated Docker operations core — local fixture v1

This is repository code and an inert driver, not an installed service, SSH transport or live Docker controller. It complements the planned home Coolify deployment and does not replace it. Static public progress/standby do not import or depend on the broker. No system unit, listener, key mapping or runtime privilege change is installed.

## Contract and trust

`operations/core.py` exposes a strict version-1 request with request_id, node, project, app, action, params, authorization and approval. Exact keys and bounded IDs only; unknown commands, hostnames, paths, environment and Docker options are rejected. Actions: list, inspect, bounded logs, start, stop, restart, deploy and remove. List is scoped to the authorized application, not discovery of arbitrary node containers. Deploy creates a managed stopped container from a trusted template; starting is an explicitly approved second operation.

An OS Unix peer UID is combined with a short-lived signed principal/project/node/action capability and root-controlled policy. A client-supplied role/username is never proof of identity. The prototype uses separate HMAC signing roots for the trusted identity authority and operator approval authority; fixture helpers issue tokens only in tests. PHP must receive no signing root and cannot mint write approvals. A real independently trusted identity/approval issuer, protected policy storage and least-privilege runtime are prerequisites to activation; the local tests do not establish those host boundaries.

Every write additionally requires a distinct, at-most-five-minute operator approval binding principal, full canonical request digest and one-use nonce. Digest covers request ID, node/project/app, action and parameters. Approval is consumed transactionally with durable intent before dispatch. Removal needs the exact registered full container ID as confirmation and requires a previously stopped container. No force removal, volumes, prune, shell/exec/Compose payload or bulk operation is exposed.

## Managed ownership and resource limits

An application must be bound to its node/project by trusted policy. A resource must be in the broker's durable registry and its actual full ID and four ownership labels must match. Labels alone do not confer ownership. Every mutation rechecks ownership before dispatch; a post-dispatch mismatch becomes UNKNOWN, not a confirmed safe failure. Unrelated fixture containers remain untouched.

Deploy templates require image@sha256 digest from server policy. The broker supplies fixed network=none, no mounts/ports, nonroot UID/GID, read-only filesystem, all capabilities dropped, no-new-privileges, 64 MiB memory, quarter CPU and 64 PIDs. These are fixture request fields, not proof a production driver enforces them. A future driver must reject images with implicit unsafe volumes and enforce bounded logging/no unexpected runtime options before activation.

## Continuity and bounds

SQLite records intents, one-use approvals, owned IDs, outcomes and selected audit metadata. Authentication tokens, approval tokens, keys, raw stderr and raw logs are not persisted. Repeated request ID with the same authorized request returns recorded state without dispatch; a different payload conflicts. Dispatched/queued jobs become UNKNOWN after an explicit single-owner broker restart; no command is replayed. An exclusive process lease prevents another broker instance from resetting active work.

At most 16 pending jobs globally, one in-flight per node and four driver workers. Calls have bounded caller wait budgets of 5 seconds for inspection and 15 seconds for an operation; an expired call may still finish in its daemon thread/remote system. UNKNOWN blocks further writes on that node until separately reviewed reconciliation. This v1 deliberately has no automatic UNKNOWN-clearing operation. At 1,000 durable jobs it refuses new jobs rather than deleting replay protection; audit is capped to 1,000 metadata rows. A deployment must define safe archival/retention and storage permissions/quotas.

Logs have explicit tail<=100 and byte<=4096 bounds. Selected output is truncated/redacted and returned only to the authorized private caller, never the public view or durable job/audit. Pattern redaction is not a guarantee logs contain no customer data; production log authorization/privacy policy and streaming bounds remain required. Duplicate log request returns a logs-available marker rather than persisting/replaying content.

## Unix protocol and admin projection

`operations/protocol.py` handles one length-prefixed <=16 KiB JSON request on an already accepted Unix socket; it obtains SO_PEERCRED itself and sets a 2-second frame budget. It cannot trust a peer UID from JSON. It never installs a socket or service. Tests use disposable socketpairs. Responses are bounded and expose stable error codes, not internal exceptions.

Read envelopes kind=view or job_status require the same scoped identity capability with inspect permission. View includes scoped jobs/progress/results/error metadata, selected audit and a dated last-observed container state. It explicitly returns current_health UNKNOWN and historical/unknown provenance, never calls a saved result live monitoring. No policy, token, endpoint, key or raw log is in the projection.

## Verification and activation gates

Run `python3 -m unittest discover -s tests -p test_operations.py -v`. Tests exercise all eight actions, unrelated-resource preservation, principal/peer/project isolation, command/option injection, replay/expiry, full-ID remove confirmation, ownership checks, actual timeout bounds, UNKNOWN/restart behavior, durable deduplication, bounded nonpersisted logs, Unix peer framing and scoped historical views. `operations/fixtures.py` cannot execute Docker, SSH or a shell.

Independent ctx1 ED25519 identity is now verified by trusted-console attestation plus client comparison; this does not establish constrained agent/key isolation. Real service activation still requires exact release/user/socket/policy/state/trust roots, a reviewed bounded remote driver/issuer, negative privilege tests, baseline health and rollback. Operator separately permits owned small Docker exercises on ctx1; that is not activation of this broker. Repository rollback is reviewed Git revert; fixture state is disposable. No operational rollback is claimed by unit tests.
