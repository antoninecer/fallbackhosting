# Security and access boundaries

The GitHub repository is **PUBLIC**. Assume every committed file may be indexed and mirrored.

Do not commit:

- SSH private keys, API tokens, passwords, `.env` files, cookies or credentials.
- Complete host inventories, nonpublic IP addresses, Tailscale authorization details, internal topology maps, customer data or raw confidential logs.
- Live application database dumps, WordPress config/secrets or unpublished snapshots with private data.

Use protected secret storage outside the repository; grant access per service with least privilege. Keep the project portal authenticated and do not expose Coolify setup/administrator registration to the public internet before ownership is claimed.

No agent receives unattended root privileges or the ability to modify existing Oracle production sites. All infra changes must be explicitly scoped and approved, with rollback and before/after availability verification.

Web snapshot builder may export only allowlisted public pages with no authentication context. Strip dynamic forms and third-party trackers as required; review licenses and privacy when mirroring assets. Emergency mail forms must validate inputs, protect against abuse, use fixed recipients and avoid data loss.

Monitor and document shared gateway availability: one lab failure must not impact independent sites. Protect the control plane using network and identity controls in addition to app-level login.

## Technical transport key boundary

Operator-provisioned SSH identity remains private to its technical account; do not copy, print, import into web/Codex, forward its agent socket or publish private connection mapping. A process may use the existing identity for an explicitly authorized fixed operation without exporting key material. Current agent unrestricted sudo and Docker-group membership mean filesystem-only separation is not an enforced boundary against that execution account; no claim of full isolation is valid until a separately approved constrained-agent plan is implemented/tested. Proposed service: docs/SSH-OPERATIONS-SERVICE.md. Operator has since granted remote Docker-group membership and an explicitly requested lifecycle test passed; agent made no permission changes. Docker-group access is broad, not a per-project restricted capability. Remote sudo absence remains operator-reported, and additional grants require explicit approval. Independent host fingerprint verification is mandatory before unattended operations.

## Private inventory administration

Server endpoint/account mapping and initial bootstrap credential are restricted local data excluded by /.local/ ignore rule and never served/exported. Web stores no SSH key or key path; opaque identity references are metadata only. Local admin supports Argon2id auth, protected sessions/CSRF/Origin, bounded login attempts, escaped display and revision-checked atomic inventory/audit updates. This does not enforce separation from root-capable Codex and is not a full security review. Planned production runtime uses a dedicated unprivileged web user/pool, reviewed non-web-writable release, private state and no key/broker/Docker/sudo rights. Exact activation approval and canaries remain mandatory; no public registration or web bootstrap.
