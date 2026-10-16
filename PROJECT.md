# Project charter — FallbackHosting

## Purpose

Operator placement clarification (2026-10-16): target management/Coolify control plane resides on the public-IP node; remote selfhosted Linux nodes run applications and may store cataloged backups. A fresh installation should discover available recovery points over verified SSH and prepare a selected restore. Independent public-edge standby copies remain local and serviceable without the remote node or controller. Current Coolify still runs on ctx1; migration and recovery implementation are pending. See `docs/PUBLIC-CONTROLLER-RECOVERY.md`.

A self-hosted platform to deploy and manage web applications using a graphical interface and Git/Docker, with an optional **independent, versioned STANDBY experience** when a primary app or its dependencies are unavailable.

This is an internal development platform for the owner and authorized collaborators (including Aleš), **not** a public shared hosting company or a guaranteed high-availability application platform.

## Main user flows

1. Create a project, choose source (Git, container image, Compose/template), assign a domain under `*.lab.ventureout.cz`, and deploy.
2. Choose fallback policy on creation: `STATIC_SNAPSHOT`, `CONTACT_ONLY`, `MAINTENANCE`, or `DISABLED`.
3. Preview, validate and publish an immutable standby release independently on Oracle.
4. Automatically enter standby when *that specific application's* health policy warrants it, or force standby with recorded operator action.
5. Return to online only after repeated healthy checks; guard against flapping.
6. Consult `project.lab.ventureout.cz` for verified status, roadmap, tasks, incidents, runbooks, logs (redacted) and AI resume checkpoints.

## Non-goals in MVP

- Multi-tenant public hosting, billing and resource resale.
- Guaranteed continuity of interactive workflows or database transactions when primary app is offline.
- Blind recursive copying of private, authenticated or dynamic pages.
- Replacing the working Oracle Nginx and existing production applications.
- Giving an AI agent or a collaborator unrestricted root access to Oracle/PVE.

## MVP acceptance

- A new demo app is deployed and routed through the wildcard domain with working TLS.
- Its standby preview and versioned copy are stored on Oracle.
- A controlled backend outage shows a correctly labeled, safe standby version and **does not interrupt** reference non-lab sites.
- Existing online app routes recover automatically after a stable health period.
- Dynamic actions in standby are disabled or routed to a separate approved emergency contact service.
- Milestones, incidents and the last verified agent checkpoint are accessible on an independently hosted protected project dashboard.
- A new agent can resume from repository state without relying on chat history.

## Administrator server inventory

One public gateway can front multiple authorized application nodes. Administrator configures counterpart name/address/SSH account/runtime/platform and opaque identity reference; private SSH keys remain in separate technical custody. Project applications later bind to a selected node. Declared platform and historical/observed health are distinct. Initial server inventory UI does not grant SSH/Docker rights or perform remote operations. This extends the original single-home-node example without changing independent standby semantics or public-hosting non-goals.

## Accepted modular-provider direction — 2026-10-15

Operator approved the application security design and provider portability: reuse Coolify/Docker for apps, Proxmox native API or libvirt/QEMU/KVM for VM lifecycle and backups. Docker on plain Linux requires neither Proxmox nor VM provisioning. Current LXC remains the demo; VM isolation is selected per trust boundary. docs/MODULAR-PROVIDERS.md records boundaries, local planning tests and pending operational gates. No hypervisor/deployer replacement, Coolify installation/location change or live migration performed; independent Oracle standby remains mandatory.
