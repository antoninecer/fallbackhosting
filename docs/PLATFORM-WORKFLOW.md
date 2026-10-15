# Platform workflow — operator clarification, 2026-10-15

Status: planned, not implemented. This refines the existing mission; no home Docker, authentication or database changes made.

## Domain responsibilities

- lab.ventureout.cz: actual platform entry, later authenticated admin and project workspaces.
- project.lab.ventureout.cz: public sanitized development progress presentation; no administrative capabilities.
- Approved app subdomains: registered app traffic and that app's independently stored standby content.

## Administrator and user journey

1. Administrator creates an invited user account, project and approved subdomain. No public self-registration. Reserve infrastructure names (including project); validate domain ownership, normalized hostname and uniqueness.
2. User signs in and sees only assigned projects. Server-side authorization must cover every read, deployment, logs, secrets, build, preview and fallback publication. Hiding buttons is not access control.
3. User chooses source/template and deploys within the assigned resource budget on the home LXC. Docker access is mediated by a restricted deployment control plane. Do not expose Docker socket/API or unrestricted host SSH to users or the browser. No new remote connectivity method is authorized by this design.
4. User configures standby mode, public message, telephone and e-mail, then previews and explicitly publishes a validated release. Store private account/configuration outside public artifacts and public Git.
5. Per-app health policy selects ONLINE or STANDBY. Health must detect required dependencies, including database-dependent app failure; HTTP 200 alone is insufficient. Keep manual force/restore and stable recovery thresholds in the planned gateway design.

## Standby behavior

Prominent notice, e.g. “Web je dočasně v režimu pouze pro čtení. Přihlášení a práce s objednávkami nejsou dostupné. Kontaktujte nás telefonicky nebo e-mailem. Děkujeme za pochopení.” Contact values are supplied and approved per project; never invent them.

Database-dependent logins, orders, carts, checkout, edits and all other writes are disabled. Do not collect credentials or accept data that cannot be processed. Replace affected links/forms with an explanatory safe page/contact notice; forbid active form submission from the snapshot. Do not expose private order/account pages as static exports. Show only approved public content.

Telephone and mailto links can provide direct client-side contact without a backend; validate and escape values. An eventual contact submission form requires separately hosted independent processing, recipient allowlist, anti-abuse and explicit configuration under M07. No functionality is implied by an unconfigured contact field.

Gateway serves versioned standby releases on Oracle independently of Docker/Tailscale/Coolify/home; per-app failure must not affect unrelated sites. Snapshots are not database backups. Switching/recovery and failure independence need controlled tests and approval.

## Implementation gates

1. Public entry page (FH-0010): truthful planned-capability presentation, no forms or pretend login. Separate exact gateway approval.
2. Security/data design before live administration: first admin securely provisioned, invite/reset process, password hashing, session security, CSRF, rate limits, audit, per-project RBAC, secrets storage and backup/restore. Credentials never in Git or page source.
3. M03: verify supported deployment platform/remote-LXC arrangement and least-privilege user isolation; explicit installation/remote-operation scope approval. Reuse Coolify where suitable; no unreviewed custom Docker control daemon.
4. M04: registered domain/TLS routing. M05: safe fallback editor/export/preview and immutable publication. M06: dependency-aware health switching/recovery. M07: independent contacts if configured. M08: controlled failures and cross-project/production-isolation tests.

The static landing is not completion of these gates. PVE/LXC live versions/resources remain unverified; home HTTP reachability does not establish Docker management access.
