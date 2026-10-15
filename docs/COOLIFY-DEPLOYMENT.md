# Coolify on the home test node — initial private installation

2026-10-15. Operator explicitly requested deployment on the current ctx1 Docker/LXC test environment. Status: PRIVATE_CONTROL_PLANE_RUNNING / FH-0004 TESTING, not completed application deployment or M03 acceptance. Initial administrator email has been requested privately; no identity was invented and login/logout is NOT_TESTED.

## Observed installation

Coolify 4.4.6, PostgreSQL 15-alpine and Redis 7-alpine run as three new dedicated containers. All three health checks PASS at 16:44:23 UTC. `/api/health` and `/login` return 200; four locally served build assets passed. Anonymous `/` and `/register` redirect to `/login`. Headless Chromium at 360/768/1440 rendered the real login page without horizontal overflow; registration redirect passed, mobile screenshot visually inspected. This is UI/readiness evidence, not a successful administrator session.

Application HTTP/realtime/terminal bindings are IPv4 loopback only. Database and Redis have no published host ports. No public Coolify hostname, gateway route, TLS certificate or proxy was created. Existing occupied web ports remain with their prior service. Private access requires an operator-authorized SSH tunnel; do not publish a registration endpoint or open firewall ports to make it reachable.

Instance settings have registration, automatic updates, API access and the unconfigured default SMTP transport disabled. This prevents offering a mail recovery service that has not been configured. Initial administrator is absent; bootstrap is intentionally pending the requested email. Account enrollment, secure password delivery, recovery/MFA setup and actual browser login/logout must be completed before administrative activation is claimed.

No Coolify-to-host key was registered, no existing technical private key was copied into Coolify, and no self-management/server validation was run. Its default localhost record is not a verified deployment target. Coolify controller health does not prove it can deploy an application. Application-only users must not receive its broad native team Admin role.

## Provenance and reviewed changes

Official upstream source tag v4.4.6 resolves to `f55efc859dfcbbf79274c4907b3df89f9767c11d`. Base/production Compose and seeders were reviewed at that revision; the automated install/upgrade scripts were inspected but never executed. Official version metadata advertised 4.4.6 at observation time.

Deployed Coolify image: `coollabsio/coolify@sha256:7c54f42d64c0d20fed4a8f4561df9018a561fecba9931ed3f64a4f3e0d34a3be`. PostgreSQL, Redis, BusyBox setup image and official Coolify helper were also resolved to immutable digests; exact image/resource/config journals remain private. No image remains a mutable `latest` deployment reference.

Reviewed Compose deltas: loopback-only host ports, no legacy inactive realtime service, explicit digest images, ownership labels, unless-stopped restart, local logs bounded to 10 MiB × 3 per service, CPU/RAM/PID limits, and authenticated Redis PONG health check. App budget 1 CPU/1536 MiB/512 PIDs; PostgreSQL 0.5 CPU/512 MiB/256 PIDs; Redis 0.25 CPU/256 MiB/128 PIDs. These initial controller limits do not reserve capacity for future builds/apps.

Only the new `/data/coolify` tree and dedicated network/database/Redis volumes were initialized. Directory setup used a bounded temporary helper because the existing technical account has Docker access but cannot create the standard directory directly. The helper touched only new installation paths; application containers have no Docker socket mount. Temporary Compose helper access to the Docker socket was privileged installation execution, not proof of a restricted runtime boundary. No new account, sudo, SSH trust or permissions on existing paths were granted.

Two initial issues were reconciled: `/data` parent was absent, causing bind setup to fail before any service existed; then application Nginx failed on unavailable IPv6 sockets. The image supports `NGINX_LISTEN_IP_PROTOCOL=ipv4`; adding that persistent environment setting and reconfiguring only the newly installed Coolify app fixed readiness. PostgreSQL/Redis and the original workload were preserved. No host IPv6, sysctl, firewall, Docker daemon, systemd or host Nginx change was made.

## Safety evidence and rollback

Original workload image, running state, start time and restart count matched the preinstall baseline. Protected Oracle reference/project TLS/routes/assets and live inventory release checks PASS both before installation and after readiness. Oracle serving has no dependency on this controller.

Remote private installation journal contains before-state, pinned images, exact newly owned container IDs, compose intent/results, initial environment backup and IPv4 correction backup. No secret, raw confidential log, resource ID or private mapping is included here. These backups are on the same node; they are not an offsite copy. Earlier operator-verified LXC archive predates the new installation and does not prove coverage of new secrets/volumes. Fresh backup coverage and isolated restore testing remain required.

Rollback means inspect the private ownership journal, verify exact current IDs/labels and stop/remove only these newly installed controller containers. Preserve DB/Redis volumes, `/data/coolify` and secret backups; no broad prune, volume deletion, existing workload recreation or shared configuration restoration. No rollback drill was performed because initial administrator/bootstrap and target enrollment are still pending. If interrupted, reconcile markers/resources first; do not blindly repeat initialization or overwrite secrets.

## Remaining concrete work

1. Receive the administrator email privately; generate a unique password and use the reviewed native root-user seeder. Keep credential delivery outside Git/public project; verify user/team ownership and registration rejection, then real login/logout in the browser.
2. Configure and test administrator MFA/recovery and explicit private access. Public exposure requires a concrete separately authorized route/TLS/access-control plan.
3. Prepare a distinct protected Coolify automation credential and exact target/privilege action for review. No host SSH authorized-key or sudo modification is implicitly performed by the controller installation.
4. Validate the deployment target in a controlled maintenance scope only after reviewing possible Docker/proxy changes; deploy/redeploy a small owned demo and verify cleanup and independent-site canaries to satisfy M03.

## Primary references

- [Coolify self-hosted installation](https://coolify.io/docs/start-with-self-hosted): manual deployment and initial account/secrets handling.
- [Pinned upstream production Compose](https://github.com/coollabsio/coolify/blob/f55efc859dfcbbf79274c4907b3df89f9767c11d/docker-compose.prod.yml).
- [serversideup/php FPM-NGINX settings](https://serversideup.net/open-source/docker-php/docs/image-variations/fpm-nginx): supported `NGINX_LISTEN_IP_PROTOCOL=ipv4`.

## Reproducible nonsecret configuration

`deploy/coolify-compose.json` is the exact nonsecret deployed Compose document, verified against the remote prepared artifact SHA256 `75cfc5c64c4982e8e827cd0e8051472fbfae9a15cecf50e3ca5c610f695939b8`. It intentionally contains only variable references for credentials. The private `.env` additionally requires `NGINX_LISTEN_IP_PROTOCOL=ipv4` and `AUTOUPDATE=false`; never commit its generated contents. Three repository regression checks cover private-only published ports, restricted runtime mounts and immutable image/resource/log limits.
