#!/usr/bin/env bash
# Operator-run on the intended app node. Read-only, bounded, no sudo or secrets.
set -u
printf 'UTC: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
printf '\nOS\n'
awk '/^(PRETTY_NAME|VERSION_ID)=/ {print}' /etc/os-release
uname -sm
printf '\nVIRTUALIZATION\n'
systemd-detect-virt || true
printf '\nRESOURCES\n'
nproc
free -m
df -h /
printf '\nDOCKER SERVICE\n'
systemctl is-active docker || true
printf '\nDOCKER / COMPOSE (denied access remains UNKNOWN)\n'
if command -v docker >/dev/null && command -v timeout >/dev/null; then
  timeout 10 docker version --format 'Client={{.Client.Version}} Server={{if .Server}}{{.Server.Version}}{{else}}UNKNOWN{{end}}' 2>/dev/null || printf 'Docker version/access UNKNOWN\n'
  timeout 10 docker info --format 'OS={{.OSType}} Arch={{.Architecture}} CPUs={{.NCPU}} MemoryBytes={{.MemTotal}}' 2>/dev/null || printf 'Docker daemon info UNKNOWN\n'
  timeout 10 docker compose version 2>/dev/null || printf 'Compose UNKNOWN\n'
else
  printf 'Docker or timeout unavailable: UNKNOWN\n'
fi
