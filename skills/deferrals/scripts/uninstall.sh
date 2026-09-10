#!/usr/bin/env bash
# Remove only the deferrals digest hook and its settings entry.

set -euo pipefail

HOOK_TARGET="${HOME}/.claude/hooks/deferrals_digest.sh"
SETTINGS="${HOME}/.claude/settings.json"
FINGERPRINT="deferrals_digest.sh"

ok()  { printf "  [removed] %s\n" "$1"; }
sk()  { printf "  [skip]    %s\n" "$1"; }
err() { printf "  [error]   %s\n" "$1" >&2; }

echo "[deferrals/uninstall] starting"

command -v jq >/dev/null 2>&1 || { err "jq is required but not on PATH"; exit 1; }

if [[ -f "$SETTINGS" ]] && jq -e --arg fp "$FINGERPRINT" '
  [(.hooks.SessionStart // [])[]? | .hooks[]?
    | select((.command // "") | contains($fp))]
  | length > 0
' "$SETTINGS" >/dev/null; then
  tmp=$(mktemp "${SETTINGS}.tmp.XXXXXX")
  jq --arg fp "$FINGERPRINT" '
    .hooks.SessionStart = [
      (.hooks.SessionStart // [])[]
      | .hooks = [(.hooks // [])[]
          | select(((.command // "") | contains($fp)) | not)]
      | select((.hooks | length) > 0)
    ]
    | if (.hooks.SessionStart | length) == 0
      then del(.hooks.SessionStart)
      else .
      end
    | if (.hooks | length) == 0 then del(.hooks) else . end
  ' "$SETTINGS" >"$tmp"
  mv "$tmp" "$SETTINGS"
  ok "digest SessionStart entry from: $SETTINGS"
else
  sk "digest SessionStart entry not present: $SETTINGS"
fi

if [[ -f "$HOOK_TARGET" ]]; then
  rm -f "$HOOK_TARGET"
  ok "hook script: $HOOK_TARGET"
else
  sk "hook script not present: $HOOK_TARGET"
fi

echo "[deferrals/uninstall] done"
