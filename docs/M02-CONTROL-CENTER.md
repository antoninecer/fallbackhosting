# M02 — Project Control Center proposal

Status: PLANNED, pending operator design review. No deployment or implementation authorized in Session 001.
Target: https://project.lab.ventureout.cz. Oracle-local, independent of home, Docker, Tailscale and Coolify. Existing architecture is preserved.

## First implementation

Generate a static HTML/CSS/minimal JavaScript portal from a validated, explicitly allowlisted repository export. Serve immutable versioned releases directly through an isolated Oracle Nginx virtual host after separate approval. No application daemon or database required for this read-only MVP. A build failure leaves the last valid release active. No remote resources, CDN, web fonts, home API calls or runtime GitHub dependency.

Require HTTPS and edge authentication on every page, asset, export and resume download before first publication. Proposed MVP: dedicated HTTP Basic authentication over TLS with strong operator-managed credentials outside Git and least-privilege file access; operator must choose/approve identity and initial-account provisioning. Do not publish unauthenticated setup routes. Shared-host configuration and certificate work require a separate exact approval. No deployment secrets in generated assets.

Repository is authoritative. Extend state/current.json with versioned validated references to canonical structured milestone/task/incident/inventory records under state/; render human-readable summaries from those records when implemented. Existing Markdown descriptions and evidence remain linked context. Migration must reconcile every existing task and preserve IDs; do not establish two independently editable task databases. This session does not introduce a competing store.

## Data contract

- Milestone: ID, description, acceptance criteria, dependencies, status, owner, evidence references, completion UTC and Git revision.
- Task: ID, milestone, goal/scope, owner, dependencies, acceptance, rollback, evidence, status, timestamps. Lifecycle BACKLOG → READY → IN_PROGRESS → TESTING → DONE; BLOCKED may interrupt work, returns through READY after resolution. DONE requires verified evidence and commit. Milestone PLANNED/NEEDS_TEST remains distinct from task lifecycle.
- Incident: ID, UTC, severity, affected component, symptoms, sanitized diagnostics, suspected/verified cause, resolution, retest, status. Unknown cause stays UNKNOWN.
- Inventory/health: component, dependency, provenance OBSERVED/HISTORICAL/PLANNED/UNKNOWN, observed UTC, method, expiry and evidence; missing or expired observations display UNKNOWN/STALE.
- Agent: identity, task, last operation, completed/outstanding work, blockers, tests, next safe action, checkpoint and commit, heartbeat UTC and session-ended flag. Only explicit recent heartbeat means recently observed activity; never infer execution from IN_PROGRESS. Proposed heartbeat expiry 5 minutes, configurable; absent heartbeat UNKNOWN, expired STALE, ended STOPPED. Static portal cannot prove current process liveness.

## Responsive modules

Dashboard shows current milestone, latest completed/active/blocked tasks, incidents, dated health, checkpoint and next action. Avoid percentage until a calculation is defined; optional later percentage = verified DONE milestones / total included milestones, explicitly labeled unweighted milestone completion, not effort.

Milestones and tasks use desktop tables with mobile cards at 360 px, visible acceptance and evidence. Incidents distinguish suspected and verified causes. Inventory separates historical records from observations. Runbooks are authenticated and sanitized; detailed connection/admin procedures stay in a separate private operator store, never copied from public Git into a public route.

Agent activity shows timestamp freshness and associated revision. Resume Project offers latest verified checkpoint and a downloadable/copyable continuation prompt containing required reading, actual recorded state, next task, safety boundaries and requirement to reverify. It never executes shell commands, starts agents, stores credentials or promises credit-reset automation.

## Implementation slices and tests

1. FH-0006: reconcile schema and canonical records; implement validator and allowlisted exporter with no dependencies beyond approved local tooling. Test malformed JSON, missing references/evidence, invalid transitions, secrets/private-field exclusion and stale observations. Validate generated links and HTML escaping against untrusted task text.
2. FH-0007: responsive read-only UI with all modules, accessible navigation, keyboard use, clear UTC labels and empty/error states. Test 360/768/1440 px, long Czech text, script injection, missing data and stale heartbeat.
3. FH-0008: prepare exact deployment plan with artifact digest, size budget, dedicated release directory, read-only serving identity, auth provisioning, TLS scope, backup targets and resource budget. Review before any live action.
4. Approved deployment only: syntax test, authentication denial for all assets/exports, successful authenticated navigation, TLS and asset checks, unrelated production baseline before/after, atomic publish and rollback to prior artifact.
5. Separately approved controlled home outage test: portal and existing standby assets remain accessible without Docker/Tailscale/home; reference production canary passes. M02 cannot be DONE before this evidence.

## Rollback and permissions

Local implementation changes use reviewed Git revert; generated artifacts are reproducible. Deployment proposal must identify exact previous Nginx files and release pointer, secure backups and approved narrow reload. Failed generation must never overwrite active release. Authentication failure blocks publication. DNS, certificate issuance/replacement, service configuration, installation and reload are outside current authorization.

Later authenticated editing needs a separately reviewed service, authorization, CSRF protection, audit trail, concurrency control and backup; do not add writes or shell execution to the static MVP.
