# New Coolify IPv4 correction scope
- UTC: 2026-10-15T16:43:34.778308+00:00.
- Image entrypoint supports NGINX_LISTEN_IP_PROTOCOL, documented by upstream serversideup/php. New app Nginx failed binding IPv6 socket errno97; DB/Redis healthy.
- Within requested initial Coolify deployment: preserve old environment and exact own container ID; add NGINX_LISTEN_IP_PROTOCOL=ipv4 only to new Coolify environment, reconfigure only newly installed app service with --no-deps. No existing predeployment workload recreation, DB recreation, SSH/sysctl/firewall/Nginx host configuration change.
- Acceptance: all three services healthy, own app real HTTP/assets, private binding and unchanged baseline. If correction fails, preserve evidence/data and stop scoped app rather than modifying host IPv6.
- Rollback: stop exact newly registered Coolify app, retain DB/Redis/volumes/secrets and prior config; never delete data or affect original workload.
