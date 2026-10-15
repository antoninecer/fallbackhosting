# Coolify initial directory preparation stopped safely
- UTC: 2026-10-15T16:39:05.755625+00:00.
- Initial helper exited 125 before mounts because /data parent absent. Read-only reconciliation: no /data, no Coolify data tree, zero new service containers, no prepared marker. New secret backup/journal exist privately.
- Next scoped correction: Docker bind-volume syntax may create only the missing /data parent; helper creates new /data/coolify tree, never modifies existing data. Resume reuses saved secrets/config and checks absence before mutation. No blind rerun.
- Existing production configuration, SSH and workloads unchanged. Prior install-scope checkpoint remains governing rollback.
