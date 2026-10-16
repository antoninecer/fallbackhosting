# FH-0025 remote demo and independent backup verified

- UTC 2026-10-16T06:45:19Z. One newly owned ctx1 demo built from cached pinned BusyBox; nonroot/read-only/cap-drop/no-new-privileges, bounded CPU/memory/PIDs/logs, tailnet-only HTTP binding, no volume/image pull. Original container ID/image/running/start/restart baseline unchanged.
- Initial dispatch failed before any mutation because payload binding was missing. Read-only reconciliation proved demo journal/container absent; corrected fixed binding and then deployed once. No blind retry of a partially created resource.
- Actual export from remote demo PASS. Source JPEG 1,019,267 bytes; optimized responsive-size WebP 22,376 bytes. Theme retained, forms replaced by local contact notice. Atomic current pointer and manifest verified.
- Isolated Nginx syntax PASS and actual HTTP ONLINE200 observed. Nginx runs only on loopback in an operator-owned isolated prefix, not the shared production service.
- Snapshot backup 24,899 bytes copied over strict existing SSH to a new0700 owned remote repository. Stored checksum independently verified; readback rehashed; restored into a new isolated local directory and all snapshot file hashes PASS. This verifies STATIC_DEMO_RELEASE_ONLY, not controller/application-database/VM recovery. No USB/disk mount or backup container needed for this bounded copy.
- Next: actual demo stop/start outage/maintenance/browser checks, then prepare exact narrow public-route activation artifact and authenticated control integration. No public dynamic route or production proxy edit yet.
