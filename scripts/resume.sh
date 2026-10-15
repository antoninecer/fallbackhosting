#!/usr/bin/env bash
# Read-only orientation aid. Deliberately makes no server changes.
set -euo pipefail
cd "$(dirname "$0")/.."
printf '=== FALLBACKHOSTING RESUME ===\n'
printf '%s\n' "UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
printf '\n=== GIT ===\n'
git status --short --branch
printf '\n=== RECENT COMMITS ===\n'
git log -5 --format='%h %cs %s' 2>/dev/null || true
printf '\n=== LAST CHECKPOINT ===\n'
last="$(find checkpoints -maxdepth 1 -type f -name '20*.md' | LC_ALL=C sort | tail -1)"
if [[ -n "$last" ]]; then cat "$last"; else echo 'No operational checkpoints yet.'; fi
printf '\n=== READ NEXT ===\n'
printf '%s\n' 'AGENTS.md STATE.md TASKS.md ROADMAP.md RUNBOOK.md'
printf '\n=== NO COMMANDS WERE EXECUTED ON LIVE SERVICES ===\n'
