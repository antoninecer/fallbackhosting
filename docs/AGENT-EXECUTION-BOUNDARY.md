# FH-0015 — constrained execution and key custody proposal

Status: REVIEW PROPOSAL ONLY, not enforced or deployed. Read-only check at 2026-10-15T15:34:07Z reconfirmed current execution account has unrestricted passwordless sudo and Docker-group membership. Proposed constrained identity does not exist. No real key was read/tested; no account/group/sudo/SSH/systemd configuration changed.

## Required decision and intended result

Authorize a separate agent execution identity and external tool runner that cannot obtain host-root or switch into credential-bearing accounts, while preserving the operator's current recovery access. This is not a request to remove the operator's privileges or lock down the current session in place. Exact activation must identify accounts, runner/service configuration, protected directories, approved peer UIDs and recovery procedure before applying anything.

A root-capable agent session cannot be made unable to access a service user's key by file modes alone. Running one subprocess through sudo -u while the tool server remains root-capable is also insufficient. The process that executes every agent-generated command and its external tools must actually run under the constrained identity and expose no alternate root/SSH/Docker administrative capability. This must be configured outside agent-editable instructions/workspace. Current full-access session is not that boundary.

## Proposed roles

| Role | Intended capability | Explicit exclusions |
| --- | --- | --- |
| Operator's existing recovery login | Manual reviewed maintenance and recovery | Do not modify/remove automatically |
| New fallback-codex execution identity | Agent tools, own workspace, local tests and read-only approved status | No sudo rule, Docker/admin groups/socket, credential-account switching, host mounts, privileged tool connector |
| Existing fallback-web runtime | Private authenticated app, signed bounded operation submission | No SSH key/agent, signing root, Docker socket, policy/service-code writes or user/group administration |
| Existing technical fallback-agent service identity | Fixed reviewed broker release, private job store/socket and existing SSH identity | No root/sudo on gateway; no caller-selected key/host/config or arbitrary SSH command API |
| Separate trusted identity/approval issuer | Authenticate principal/project and issue short-lived approval bound to exact request | No signing API callable merely on an unauthenticated user/role claim from PHP; no key in PHP/agent workspace |

Names other than existing roles are proposed only and must be reconciled against actual accounts before creation. Do not repurpose an existing identity on collision. Current remote technical Docker-group access is root-equivalent on the test node; registry/labels provide application policy, not protection from a compromised daemon/host administrator. A separately reviewed fixed remote helper/forced-command or controller boundary is required before claiming narrow target capability. No target grant or authorized_keys change is included here.

## Protected code, policy and runtime

Proposed broker release under `/usr/local/lib/fallback-operations/releases/<reviewed-commit>/`, root-owned and non-writable by agent/web/service caller; a reviewed pointer selects code. Never execute credential-bearing broker from /opt/fallback. Private policy/trust roots under `/etc/fallback-operations/`, runtime/state under `/var/lib/fallback-operations/` and `/run/fallback-operations/`, with least-privilege modes and explicit socket peer mapping. Existing key location remains private/unchanged and is represented only by a protected opaque binding.

Service Python and dependencies must be installed into a protected environment, use isolated import/search behavior and exclude agent-writable cwd/PYTHONPATH/user packages. A systemd sandbox alone does not defeat a root-capable host caller. Review NoNewPrivileges, empty capabilities, read-only system view, private temp, minimal environment and bounded address families, but test every required key/trust/job/network access before claiming they work. No unit is installed by this proposal.

Policy must bind approved node/app/project IDs independently of web-editable server inventory. Web saving a hostname or identity reference must not authorize a new SSH target. The service resolves existing protected bindings; fixed driver inputs have no shell/Compose/host-path/options channel. Disable agent forwarding, user SSH config inheritance, TTY and forwarding; pin the independently attested host identity without learning replacement keys.

The fixture HMAC authorities are not deployed credentials. Real issuer custody, rotation and a verification-only signature protocol must be reviewed before production; prefer vetted asymmetric verification so callers never receive a signing root. Do not implement custom cryptography or generate production trust roots in the agent workspace. Broker/key compromise remains a different trust boundary from compromised web/agent callers.

## Staged activation plan for later exact authorization

1. Preserve an independent operator recovery session/console and record current access without exporting raw policy or keys. Define who can reverse only the newly added controls.
2. Create/reconcile the proposed new constrained execution identity and separate owned workspace. Grant only repository/test needs; no sudo or Docker membership. Do not remove current operator rights.
3. Configure the actual external command/tool runner for this identity. Verify effective UID/groups and available connectors for every execution path; do not rely on prompts or project markdown as enforcement.
4. Install only reviewed root-managed broker code/policy/issuer and private data/socket permissions, in a separately authorized maintenance scope with backups and canaries. Keep service inactive initially. Do not expose a public broker port or make static serving depend on it.
5. Run negative tests under the real constrained runner and web identity with canary material before accessing any real credential-bearing resource. Verify ordinary operator recovery separately.
6. Only after the boundary, identity/approval issuance and target helper are evidenced, authorize a limited read-only broker activation; compare independent project/reference health before/after. Managed writes require their exact approval scope and reconciliation/rollback policy.

## Acceptance and negative tests

- Restricted agent/web cannot sudo, become technical/root user, use local Docker socket, change groups, edit broker release/policy/trust roots or read issuer material. Verify enforcement with a nonsecret canary using the same ownership/mode/layout; never print a real private key to demonstrate denial.
- Agent tools cannot escape through privileged connectors, root Docker, host mounts, mutable imported Python, delegated service commands or agent-writable production code.
- Unauthorized socket UID, forged principal/project, changed payload, stale/reused approval, unknown app/host/key/action and arbitrary command parameters are denied before any remote dispatch. Existing local tests cover logical protocol checks; they do not certify host privilege enforcement.
- An approved read-only known target check succeeds with independently verified trust. Node/broker loss leaves local static gateway/project assets and unrelated reference sites reachable; controlled outage test needs its own safe scope.
- Operator recovery still works independently; deployment/negative-test evidence has UTC, identity, exact release and rollback. Until then enforced key isolation is NOT ESTABLISHED and broker production activation is NO-GO.

## Narrow recovery and rollback

Stop/disable only a newly approved broker if needed, preserving job/UNKNOWN records and retaining private data for reconciliation. Revert only new runner/account/group/policy controls using private prechange evidence from the operator recovery context; do not revoke the existing technical identity, replace host trust or remove the operator login automatically. Retain the old operator session until recovery is verified. Never restore all shared host configuration wholesale. If constrained-runner checks fail, continue repository engineering in the existing environment without claiming the key boundary is enforced; do not activate the broker.
