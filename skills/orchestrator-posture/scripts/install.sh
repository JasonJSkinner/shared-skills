#!/usr/bin/env bash
# Install the orchestrator-posture Stop-hook collector. Idempotent.
#
# Touches:
#   ~/.claude/state/orchestrator-posture/   (sentinels, runs.jsonl, investigations/)
#   ~/.claude/state/orchestrator-posture/settings.json.pre-install.bak
#   ~/.claude/settings.json                 (adds ONE Stop hook entry)
#
# The hook returns immediately (exit 0, no output) for any session with no sentinel,
# so installing it costs nothing until a run calls `posture_run.py start`.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="${ORCHESTRATOR_POSTURE_STATE_DIR:-${HOME}/.claude/state/orchestrator-posture}"
echo "[orchestrator-posture/install] starting"
command -v python3 >/dev/null 2>&1 || { echo "  [error]     python3 required" >&2; exit 1; }
mkdir -p "${STATE_DIR}/investigations"
echo "  [installed] state dir: ${STATE_DIR}"
python3 "${HERE}/_settings_hook.py" add
echo "[orchestrator-posture/install] done"
echo ""
echo "Notes:"
echo "  - settings.json hook registration generally requires a NEW Claude Code session."
echo "  - Verify with scripts/status.sh; revert with scripts/uninstall.sh."
