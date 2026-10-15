# Current verified project state

> Snapshot of **historically reported** results from the operator; it is **not live monitoring**. Re-verify on each new session before writing to servers. Last audit by an agent: **NOT PERFORMED**.

## Git

- Public repo: `antoninecer/fallbackhosting`.
- Intended working directory: `/opt/fallback` on Oracle `setonuk`, under the operator's non-root account.
- SSH authentication to GitHub previously succeeded; initial clone on `main` was empty (`No commits yet`).
- M00 documents and first push still need to be performed and verified.

## Historically observed components

| Component | Previous observation | Current confidence |
| --- | --- | --- |
| Public Oracle gateway | Ubuntu server with existing Nginx and several non-lab production vhosts | HISTORICAL, verify |
| Reference production application | Quantum Random accessible via existing Oracle Nginx/PHP | HISTORICAL, verify before each gateway change |
| Home hypervisor | Proxmox VE 8.4.21 and `lxc-pve 6.0.0-2` observed after update | HISTORICAL, verify |
| Home `ctx1` | Unprivileged LXC 102 with Rocky Linux 9.8 and Docker | HISTORICAL, verify |
| Home lab Docker | `hello-world` succeeded; `nginx-test` returned 200 over Tailscale | HISTORICAL, verify |
| Home Tailscale | Oracle-to-home ping and HTTP succeeded | HISTORICAL, verify |
| DNS | Operator configured `lab` and `*.lab` A records to Oracle gateway | HISTORICAL, verify |
| Desired LXC resources | 3 vCPU and 8 GiB RAM requested; not conclusively verified | UNKNOWN |
| Coolify / Traefik | Not confirmed installed | PLANNED |
| Independent fallback and project portal | Not implemented/confirmed | PLANNED |

## Outstanding operational concern

Before any **Proxmox host reboot**, review the previously observed EFI GRUB removable bootloader warning. Do not assume it was resolved by upgrading `lxc-pve`.

## Active next step

M00: make and push the first documentation/agent-policy commit, then verify remote Git state. Next M01: read-only inventory and protection baseline. No product deployment authorization is implied.
