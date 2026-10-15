# Architecture (draft; verify before implementation)

```text
Internet / DNS lab + *.lab
             |
             v
Oracle gateway: existing Nginx / TLS / independent project portal + standby copies
      |                                 |
      | lab traffic only                +--> local versioned static standby
      v
Tailscale encrypted path
      v
Home PVE -> unprivileged Rocky Linux LXC -> Docker -> Coolify / Traefik -> Apps
```

## Trust and failure boundaries

1. **Oracle is the stable shared edge.** Existing Nginx sites including Quantum Random must remain independent. Lab uses separate config and logs. Do not modify other virtual hosts.
2. **Home node is not a prerequisite to the Oracle edge.** No DNS resolver dependency on the home node for Nginx startup. Use an appropriate addressing/resolution strategy that keeps config validation and reload working during a home outage.
3. **Routing is per hostname / registered app.** An unrecognized host must not accidentally expose another application; default deny or controlled landing page.
4. **Coolify is only an application/deployment control plane.** The project center and standby-serving components reside independently of it.
5. **Secure administration.** Coolify and project operations are authenticated and private by default; only approved public application endpoints become publicly reachable.
6. **Zero trusted writes during fallback.** Snapshot copies cannot execute PHP or post to an unavailable backend; transactional actions need an independent audited service or a notice.
7. **Resource budgets.** Constrain application CPU/memory, storage and logs; avoid one app exhausting the shared host.

## Availability semantics

- `ONLINE`: required app probes healthy, traffic to primary.
- `DEGRADED`: partial failure/limited functionality, policy-specific behavior.
- `STANDBY`: approved static release or notice served locally on Oracle.
- `RECOVERY`: repeated checks passed; controlled switch to ONLINE.

Separate **per-application** state from **gateway/node** state. An HTTP response with status 200 may still represent an application failure; health checks need meaningful paths and where applicable dependency checks. Use hysteresis and bounded timeouts.

## TLS and DNS

- Operator reports DNS A records for `lab` and `*.lab` pointing to the Oracle edge; verify authoritatively when needed.
- Wildcard TLS requires ACME DNS-01; avoid assuming HTTP-01 supports wildcard issuance. Certificate issuance/renewal must be isolated from existing TLS on Oracle.
- TLS terminates at Oracle, then a Tailscale-protected hop to the home router. Configure forwarded headers and trusted proxies explicitly to avoid redirect loops.

## Static standby release safety

- Build from approved public routes or app-native static export; exclude auth, cookies, private resources, account/cart/checkout endpoints and sensitive data.
- Assets may be optimized (e.g., WebP / AVIF) with visual QA. Verify links, responsive views and that all public resources are local to the snapshot or approved external dependencies.
- Publish only after checks, using versioned releases and atomic pointer updates. Keep known-good rollback.
- Contact or mail gateway must be hosted on Oracle (or another independently reachable provider), with recipient allowlisting, anti-spam, rate limits, audit and queueing.

## Operational implementation notes

No actual Coolify installation, wildcard Nginx routing, fallback engine, wildcard TLS or Project Control Center is confirmed deployed yet. Follow `STATE.md` for last observed facts; recheck in runtime before changing anything.

## Public progress presentation (operator request, 2026-10-15)

Add a sanitized read-only static presentation, separate from the authenticated project administration center. Build-time canonical Markdown/JSON projection exports reviewed labels/statuses and checkpoint identity/time only. Nginx serves three local files; no PHP, database, Docker, Tailscale or home runtime dependency. This does not weaken authentication requirements for administrative modules or expose runbooks/inventory. Project-domain activation was explicitly approved and completed with evidence in checkpoints and docs/PORTAL-DEPLOYMENT.md. Lab entry is prepared separately and not yet activated.

## Platform first-run setup

Operator clarified admin-provisioned users/projects/subdomains and per-user app management with safe per-app standby contacts. See docs/PLATFORM-WORKFLOW.md and docs/SERVER-ONBOARDING.md. No public admin setup, raw Docker API or general shell is exposed. Key custody belongs to the approved deployment controller; an audit key and controller automation key are distinct. Any change to the original planned home Coolify placement or broad privileges requires explicit architecture review.

## Isolated SSH operations boundary — proposed, not deployed

Operator-provisioned Oracle-to-home technical SSH was independently exercised by agent at 2026-10-15T08:25:31Z with strict existing host trust; independent fingerprint attestation is still required. Proposed local operations service owns key access, accepts only authorized structured allowlisted jobs over a private Unix socket, and starts with read-only identity/uptime actions. Private mapping, trust and service code cannot be writable by web/agent callers. This proposal grants no target privileges. Operator separately granted technical-user Docker-group access; diagnostic lifecycle test passed, while broad-access/tenant isolation still needs review. Current agent unrestricted sudo and possible Docker privilege path prevent a claim of enforced key isolation; exact constrained-agent plan needs human review. Proposal and acceptance/rollback: docs/SSH-OPERATIONS-SERVICE.md. This is a review proposal complementing the planned home Coolify deployment; gateway/static serving has no dependency on broker or home availability.

## One gateway, multiple application nodes — operator-requested extension

The original home node is now the first member of a node list: a single independent Oracle public gateway can front multiple authorized home Docker nodes. Other runtime values are inventory declarations only, without implemented drivers. The private PHP inventory UI is prepared locally on Oracle; deployment control remains planned on home infrastructure via Coolify and separately reviewed technical broker. Per-app target node IDs must drive routing/health/fallback; one node outage must not alter other node routes or Oracle static serving. No public administrative setup, shared key exposure or automatic runtime action is added. User requested this extension; implementation and outstanding activation/security gates documented for review in docs/MULTI-NODE-ADMIN.md. No existing operational architecture changed by local metadata/UI preparation.
