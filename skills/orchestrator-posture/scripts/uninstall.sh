#!/usr/bin/env bash
# Remove the orchestrator-posture Stop-hook entry. Idempotent.
# Leaves ~/.claude/state/orchestrator-posture/ in place (the ledger is the run record).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="${ORCHESTRATOR_POSTURE_STATE_DIR:-${HOME}/.claude/state/orchestrator-posture}"
echo "[orchestrator-posture/uninstall] starting"
python3 "${HERE}/_settings_hook.py" remove
echo "[orchestrator-posture/uninstall] done"
echo ""
echo "Notes:"
echo "  - ${STATE_DIR}/ left in place (runs.jsonl is the record)."
echo "  - settings.json hook removal generally requires a NEW Claude Code session."
