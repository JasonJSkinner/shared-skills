#!/usr/bin/env bash
# Report the install state of the orchestrator-posture collector. Read-only.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[orchestrator-posture/status]"
echo ""
python3 "${HERE}/_settings_hook.py" status
