# Scoped dependency audit — 2026-10-15

Read-only observations at 15:44:11–15:46:11 UTC. This is a bounded configuration/source classification, not a complete topology or outage proof. Private raw evidence stays outside Git/public export.

| Component | OBSERVED | Remaining evidence |
| --- | --- | --- |
| Public project page | Local static roots exist; no backend or resolver directive in its selected vhost | Full include graph and controlled outage acceptance remain untested |
| Existing inventory admin | Local roots and Unix PHP upstreams; dedicated pool and private local JSON/sessions; bounded source scan found no shell, remote-client or DB-driver calls | Scan is not proof against every indirect dependency; new operations/center release is not activated |
| Protected reference | Selected matching vhost declares a local Unix backend | Dynamic application source dependencies UNKNOWN; independent external baseline incomplete |
| Home Docker | Strict identity-verified SSH; one container running, one bind mount, one published binding | Bind source contents and LXC archive inclusion UNKNOWN; no values, paths or addresses exported |
| LXC backup | Operator attests successful backup dated 2026-10-15 and successful `zstd -t`; both VERIFIED; monthly scheduling reported configured | Exact execution UTC/archive location not supplied; restore NOT TESTED; external copy NOT DOCUMENTED |

A valid compressed archive does not demonstrate application consistency, inclusion of bind-mounted data, or successful restoration. Do not infer inclusion merely because a container is inside the backed-up LXC. Next read-only evidence should be a sanitized archive/config inclusion report; no restore, backup scheduling or PVE changes performed here.

The selected Oracle configuration provides evidence of local serving dependencies. Home-outage independence is still a future M08 controlled test, not a result of this scan. M01 remains NEEDS_TEST. No production configuration, permissions, workloads or volumes changed. Rollback: reviewed documentation revert only.
