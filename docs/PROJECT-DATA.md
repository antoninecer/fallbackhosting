# Canonical project data — schema v1

`state/catalog.json` is the sole editable source for milestone/task table records. `TASKS.md` and `ROADMAP.md` retain explanatory prose and evidence context; their tables are generated projections, never a second editable database. `state/current.json` remains the current-session/checkpoint/public-event pointer, not a task store. The existing public presentation now validates the catalog before rendering. The protected control-center UI is future work.

## Local workflow

1. Edit the catalog record, including a dated evidence-backed task transition when changing status.
2. Run `python3 scripts/project-data.py sync` to regenerate only the two Markdown tables. Existing prose remains intact.
3. Run `python3 scripts/project-data.py check` and `python3 -m unittest discover -s tests -v`.
4. Record the verified stage/checkpoint/public event, inspect the diff and commit/push under operator authorization.

Public generation fails closed on invalid catalog or table drift before replacing the page. Rollback: revert the reviewed change, synchronize tables and rebuild the known-good public page. No service reload or host configuration change is needed. The catalog is public repository data: private connection inventory, key references, credentials and raw logs remain outside it.

## Contract and migration

The executable strict schema is `portal/model.py::validate`; unsupported versions and unknown keys are rejected. Top-level keys: schema_version, milestones, tasks, incidents, observations, agent. Migration preserved all M00–M10 and FH-0001–FH-0018 IDs and previous statuses, apart from the explicitly evidenced FH-0006 READY → IN_PROGRESS transition. Existing task history before migration is not reconstructed or invented. Dependencies migrate only explicit existing task gates; missing relationships are not guessed.

Milestones: id, title, status, owner, acceptance, dependencies, evidence, completed_at_utc, completion_revision. Tasks add milestone, scope, rollback and history. Status transitions use BACKLOG → READY → IN_PROGRESS → TESTING → DONE; BLOCKED returns through READY. TESTING may return to IN_PROGRESS. DONE cannot silently reopen. Each history step contains from/to/utc/evidence, is chronological and must end at the recorded current status. Completed records require existing repository evidence, an explicit UTC completion timestamp and full commit hash; the check command also verifies that commit exists locally. The check command compares task status/history against the committed catalog to reject erased history, silent state changes, removed IDs and altered committed completion evidence. Commit existence and evidence-file existence do not independently certify the claim's truth: review remains required.

Task/milestone references must exist, be unique and remain acyclic. Evidence references must be existing `docs/*.md` or `checkpoints/*.md` files contained in the repository; absolute paths, traversal and escaping symlinks are rejected. Table fields must be bounded nonempty single-line strings without pipe delimiters. Public labels remain separately reviewed fixed mappings in `portal/build.py`; catalog owners, acceptance, scope, rollback, incident text, observations and raw checkpoint contents are not exported by the public page.

Incidents: id, utc, severity, component, symptoms, cause, cause_provenance, resolution, status, evidence. Cause provenance explicitly distinguishes UNKNOWN/SUSPECTED/VERIFIED. Empty initial list means no incident records migrated, not a claim of incident-free infrastructure. No raw logs or connection maps belong in these fields.

Observations: id, component, dependencies, provenance, status, observed_at_utc, expires_at_utc, method, evidence. Provenance is OBSERVED/HISTORICAL/PLANNED/UNKNOWN; result is PASS/FAIL/UNKNOWN. `observation_state` returns UNKNOWN without both an actual observation and a declared expiry, for historical/planned data, or for future observations; expired results are STALE. An expiry is policy and must be explicitly chosen rather than fabricated during migration. The initial gateway result is historical with no expiry and therefore projects as UNKNOWN for current health.

Agent: identity, task_id, heartbeat_utc, session_ended, checkpoint, revision. No heartbeat is synthesized from task status or build time. Missing/future heartbeat means UNKNOWN; age of five minutes or more is STALE; explicit ended session means STOPPED. RECENT only means a recent recorded heartbeat, never proof a process is executing. Initial heartbeat is null. Checkpoint/revision are a dated catalog snapshot, not an automatically maintained liveness feed.

UTC stays canonical; human-facing public timestamps use Europe/Prague. No new full catalog JSON or operational export is served publicly. Existing three-file public asset boundary is preserved.

## Validation evidence

Tests cover malformed/duplicate-key JSON, duplicate IDs, missing/self/cyclic dependencies, missing completion evidence/revision/time, illegal task transitions, private/unknown fields, traversal, stale/future/missing observations and heartbeat, public text exclusion, Markdown drift, HTML escaping and preservation of the last valid page on build failure. Actual test counts/timestamps and containing commits are recorded in checkpoints, not assumed here.
