# Docker lifecycle test — PASS, cleanup verified

Evidence recorded UTC 2026-10-15T08:35:47Z; agent Codex; task FH-0016, milestone M03; base 0d5e5c5. Completion revision: containing local commit.

Operator first added the target technical account to Docker group, then explicitly requested a retest. Agent changed no permissions. New bounded strict SSH session observed group membership and Docker Engine 29.9.0. Existing known_hosts accepted; independent host fingerprint attestation remains outstanding.

## Acceptance evidence

- Own unique test name: `fallbackhosting-smoke-20261015t083413z-d081cf7059dd3d09`; created container ID `185287c3f72d43744392238d292ea3e53b13a91c98ab7fbc830d62394ffebcd6`.
- Already-local immutable image ID taken from known reference container; image has no declared volumes; no image pulled.
- New container: no network access/ports/mounts/volumes, read-only rootfs, non-root UID/GID 65534, capabilities dropped, no-new-privileges, PIDs 32, memory 32 MiB, CPUs 0.25, restart disabled and no persistent Docker logs.
- Entry point overridden with inert shell printf; expected marker returned, exit code 0. No application service started.
- Cleanup verified ownership label, removed only own container, then exact-name daemon query returned no remaining resource. Rollback exercised successfully; image kept.
- Existing reference container ID/running state/restart count/start time/image unchanged before/after. Existing workload not restarted, recreated or reconfigured.
- Reference production HTTP 200 with verified TLS and home test HTTP 200 before/after. These are bounded endpoint observations, not full application/failover guarantees.

Docker-group membership is a broad technical capability, not a per-user isolation policy. No remote sudo used, no key contents read/copied, no SSH trust/service/firewall/DNS/gateway change. No Coolify install or authorization for further deployments. No service/helper installed. Initial denied diagnostic remains historical evidence in older checkpoints.

Next: independently attest SSH host identity and review protected operations/controller privilege design. Before repeating, confirm prior cleanup/state and obtain scope; never broad prune or remove existing workloads.

Evidence checkpoint: `checkpoints/20261015T083547Z-FH-0016-docker-smoke-pass.md`. No private endpoint or key path exported to public Git.
