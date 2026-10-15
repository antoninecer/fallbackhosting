# Isolated SSH operations service — proposal for review

Status: PROPOSED / NOT IMPLEMENTED / NOT DEPLOYED. M03, FH-0013.
No account, permission, SSH trust, systemd or Docker change is made by this document.

## Evidence and scope

The operator reported existing technical accounts and a working key-based Oracle-to-home connection. At 2026-10-15T08:25:31Z Codex independently completed three explicitly authorized SSH probes: hostname, effective username and uptime. All exited 0 and the identity outputs matched the operator's intended node/account. Existing host trust was accepted with StrictHostKeyChecking=yes; UpdateHostKeys=no prevented learning additional keys. This is verified transport, not independent host fingerprint attestation, Docker management or deployment readiness.

Initially the operator reported no destination sudo/Docker rights; the first daemon probe was denied. Operator subsequently granted Docker-group membership, and a fresh-session agent lifecycle/cleanup test passed (docs/DOCKER-SMOKE-TEST.md). No permission changed by Codex. Remote sudo absence remains reported, not independently tested. Ordinary agent-user access to the private key is reported denied; no key contents were read, copied or exported. Endpoint, exact key path and account mapping stay in operator-controlled private inventory, not public Git. Its durable storage location has not been verified; subsequent sessions must obtain it through the approved operator channel, not guess credentials.

## Proposed boundary

```text
Authenticated private backend -> local bounded job API -> operations service
                                                       -> existing SSH identity
                                                       -> approved home-node commands

Public progress/static standby -> Oracle-local files (no dependency on service)
```

Proposed service name: `fallback-operations`. Run as the existing technical Oracle account, without root, sudo or Docker membership. Only that process account and the operator's protected administrative context may access its SSH identity. Web and agent users receive no identity file, key API, forwarded SSH agent, reusable signed challenge or general SSH proxy. The private backend submits action IDs, never private-key bytes or command strings.

CRITICAL prerequisite: current agent execution account has unrestricted passwordless sudo, independently observed via sudo -n -l this turn. It can run as the technical account, as the authorized test demonstrated. Oracle-side Docker-group membership was also observed; rootful Docker access can be another privilege path and must be assessed before claiming isolation. A separate Unix user/systemd sandbox alone cannot protect against a root-capable caller. Therefore do not claim the key is inaccessible to Codex under present privileges. Before deploying, approve a dedicated constrained agent execution boundary without general sudo, root-equivalent Docker/socket access, privileged service-user switching or ability to edit service code/policy. Changing existing operator privileges is outside this task and requires its own reviewed recovery plan and exact approval.

This complements the planned home-hosted Coolify control plane; it does not replace it with a custom public Docker manager or move Coolify to Oracle. Initial service operations are read-only. Any eventual integration with Coolify and its broader privilege requirements needs an architectural/security review.

## Small initial contract

Unix-domain socket, not a public HTTP port. Protect socket ownership/mode and check peer credentials against a private caller allowlist. An OS peer identifies the backend process, not the human user: additionally verify independently trusted authenticated principal/project authorization. Never accept a client-supplied username or role as proof. Public static presentation has no socket access.

Request fields: schema version, unique request ID, approved node ID, action enum, narrowly typed parameters and authorization reference. Initially allow only the three fixed actions `node.hostname`, `node.user`, `node.uptime`, with no caller arguments. Node ID resolves through protected server-side configuration to a single approved endpoint/account/key/trust record. Reject unknown fields/actions, client hostnames, paths, SSH options, environment variables and raw commands. Store private configuration outside Git/webroot.

Return bounded structured results: job ID, state, observed UTC, sanitized selected values, exit status and stable error code. Raw stderr, credentials, key paths, process environment and unrestricted remote output must not be exported. Authentication/authorization failure denies before opening SSH. Start with one worker, one in-flight job per node, at most 16 queued jobs, 5-second connect and 15-second execution budgets, 8 KiB output limit; these are proposed limits, not measured capacity. Reject overload; website reads never wait for the home node.

Future write/deploy actions remain disabled. Enabling any requires exact operator authorization for action, node, project/resource, reviewed payload digest, expiry and one-use approval ID from a separate trusted approval authority. A compromised web process must not mint that approval. A sudo/Docker failure is denial, never a reason to auto-grant privileges or retry as root. Do not pass arbitrary Compose, mount paths or privileged-container options through this initial API.

## SSH execution and host identity

Invoke SSH with a fixed local argument vector, no local shell and only constant approved remote commands. Keep -F /dev/null, selected identity, BatchMode=yes, IdentitiesOnly=yes, IdentityAgent=none, StrictHostKeyChecking=yes and UpdateHostKeys=no; disable agent/port forwarding and TTY. Use an explicitly pinned private known_hosts file. Caller input cannot select config, destination, key or options. The remote login shell remains involved in SSH command execution, so no untrusted text may enter that command.

Independent fingerprint gate (FH-0014): operator uses the existing trusted ctx1 console to run `ssh-keygen -l -E sha256 -f /etc/ssh/ssh_host_ed25519_key.pub`. This reads only the public host key. Compare algorithm and full SHA256 fingerprint against the connection's configured trusted entry using the technical account, through an approved private channel. Record trusted source, comparison UTC, verifier and match result privately. If another algorithm is actually negotiated, verify that specific public host key too; do not infer it from an unrelated key. Mismatch or unknown identity blocks service activation. Do not delete/relearn trust entries automatically. Network keyscan or a fingerprint obtained solely over this same SSH connection is not independent proof.

Reference: [OpenSSH client configuration](https://man.openbsd.org/ssh_config), [ssh-keygen](https://man.openbsd.org/ssh-keygen). These describe the trust/identity controls, not proof that this proposed service exists.

## Service isolation and job continuity

Deploy only a reviewed release into an operator-managed location that web/agent accounts cannot edit. Never run privileged/credential-bearing service code directly from the agent-writable checkout; policy, endpoint mapping, approval trust roots and known_hosts must also be protected against caller edits. Use a dedicated private runtime/state directory, restricted socket and minimal environment; no inherited SSH_AUTH_SOCK, caller PATH or user SSH configuration.

Proposed systemd hardening to validate on the actual host: NoNewPrivileges, restrictive umask, read-only system view with only dedicated state/runtime writable, private temporary directory, empty capability set and constrained address families. Do not copy a service unit into /etc/systemd or claim the sandbox effective until tested with key/trust file access and network behavior. No new Nginx or Tailscale service dependency; stopping the broker or losing home connectivity must leave static portal/standby and unrelated sites serving.

Persist an intent record before dispatch. Job states: QUEUED → RUNNING → SUCCEEDED/FAILED/UNKNOWN. On timeout, lost connection or service restart after dispatch, record UNKNOWN unless outcome is established; killing local SSH does not prove remote work stopped. Deduplicate request IDs durably; never blindly repeat a future mutating action after interruption. Reconcile by querying safe known state and obtaining renewed approval when appropriate. Audit records use principal/project/action/result and UTC with bounded sanitized output; private audit retention and storage budget must be set before deployment.

## Acceptance, approvals and rollback

Repository implementation may follow after design review. Start with a fake transport and tests for unauthorized peer/principal/project, unknown actions/fields, argument injection, alternate key/host selection, stale/replayed approval, host-key mismatch, queue/output/time bounds and crash/UNKNOWN handling. Verify neither key paths/bytes nor arbitrary remote data appear in responses/logs/public export.

Before real activation separately authorize exact service release/path, existing service-user usage, socket callers, policy/state directories and host-trust configuration. Confirm constrained agent/web identities cannot read the key, switch to its owner, edit service/policy or acquire host-root via Docker/sudo. Test trusted fingerprint match then an authorized read-only probe. No target sudo/Docker grant is part of this gate. Future deployment privileges remain a separate explicit decision.

Record production and public-portal baselines before/after activation. Controlled broker/home outages and security tests need approved safe scope. Failure isolation, runtime sandboxing and RBAC are currently UNTESTED.

Deployment rollback proposal: stop/disable only the new broker through its approved service controls, retain job records and deny new submissions; reconcile RUNNING/UNKNOWN jobs before restart. Restore only its previous reviewed release/config/socket policy. Do not revoke the existing SSH key, change target rights, restart home services or alter shared gateway configs automatically. Static serving continues independently. Documentation rollback is a reviewed Git revert and rebuild of the sanitized public presentation. No deployment commands run now.

## Earlier Docker smoke-test denial — historical helper alternative

A subsequent explicitly authorized diagnostic found the remote Docker CLI, but daemon query was denied at its standard socket. No disposable resource was created and there was nothing to clean up. The initial broker must remain read-only; no change to its operation allowlist or account permissions is made here.

If the operator wants to authorize only a create/delete smoke test before a full deployment privilege decision, prepare a separate root-owned, reviewed helper proposal with one fixed entry point and no user arguments. A narrowly scoped sudoers rule could permit only that exact helper for the technical account; this is a FUTURE PRIVILEGE GRANT requiring exact approval, not something configured now. The helper code/config and parent directories must not be writable by web/agent/remote technical users. Do not allow generic sudo docker or Docker-group membership as a restricted capability.

Proposed helper behavior: use an operator-approved already-local immutable image ID; no pull, no start/exec, no mounts, ports, network or arbitrary container specification. Generate a unique test name and ownership label inside the trusted helper; create a stopped container, verify its ID/label, remove only that exact owned container and verify absence. Lock concurrent calls and persist owned resource ID before cleanup; if interrupted, reconcile only that ID, never broad prune or guessed names. Deny if approved image absent. Any failed cleanup records remaining ID privately and blocks success. Output only sanitized creation/deletion results. This tests metadata create/delete, not running applications or full Coolify privileges.

Exact helper path/content, allowed image, sudoers rule, approval enforcement, backups and rollback are not yet selected/approved. Do not install a helper, edit sudoers or repeat the Docker operation as another remote user under current authorization. Full deployment privileges remain a distinct architectural review.

## Current transport capability after operator change

Operator separately granted broad Docker-group access and authorized a new diagnostic; create/start/exit-0/remove/absence passed without remote sudo. No helper/broker was installed. Earlier denied probe and helper proposal are historical context/possible restricted alternative, not current access blockers. Broker API remains read-only by design until separately reviewed; broad technical credentials are not authorization for arbitrary project operations or isolation proof. Account/group reduction or remote forced-command restriction would need exact approval and operator recovery plan.
