#!/usr/bin/env bash
# Install the deferrals SessionStart digest. Idempotent and settings-safe.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SRC="${SCRIPT_DIR}/deferrals_digest.sh"
HOOK_TARGET="${HOME}/.claude/hooks/deferrals_digest.sh"
CLI="${HOME}/.claude/skills/deferrals/scripts/deferrals.py"
SETTINGS="${HOME}/.claude/settings.json"
HOOK_COMMAND="bash ~/.claude/hooks/deferrals_digest.sh"
FINGERPRINT="deferrals_digest.sh"

ok()  { printf "  [installed] %s\n" "$1"; }
sk()  { printf "  [skip]      %s\n" "$1"; }
err() { printf "  [error]     %s\n" "$1" >&2; }

echo "[deferrals/install] starting"

command -v jq >/dev/null 2>&1 || { err "jq is required but not on PATH"; exit 1; }
command -v python3 >/dev/null 2>&1 || { err "python3 is required but not on PATH"; exit 1; }
[[ -f "$HOOK_SRC" ]] || { err "missing $HOOK_SRC"; exit 1; }
[[ -f "$CLI" ]] || { err "missing deployed CLI: $CLI"; exit 1; }
python3 "$CLI" --help 2>/dev/null | grep -qw digest ||
  { err "deployed CLI lacks required digest verb: $CLI"; exit 1; }

mkdir -p "$(dirname "$HOOK_TARGET")"
if [[ -f "$HOOK_TARGET" ]] && cmp -s "$HOOK_SRC" "$HOOK_TARGET"; then
  sk "hook script up-to-date: $HOOK_TARGET"
else
  cp "$HOOK_SRC" "$HOOK_TARGET"
  chmod +x "$HOOK_TARGET"
  ok "hook script copied: $HOOK_TARGET"
fi

mkdir -p "$(dirname "$SETTINGS")"
if [[ ! -f "$SETTINGS" ]]; then
  printf '{}\n' >"$SETTINGS"
  ok "created settings file: $SETTINGS"
fi

if jq -e --arg cmd "$HOOK_COMMAND" '
  [(.hooks.SessionStart // [])[]?
    | select((.matcher // "") == "startup|clear")
    | .hooks[]?
    | select(.type == "command" and .command == $cmd and .timeout == 5)]
  | length == 1
' "$SETTINGS" >/dev/null; then
  sk "SessionStart startup|clear hook already registered: $SETTINGS"
else
  tmp=$(mktemp "${SETTINGS}.tmp.XXXXXX")
  jq --arg cmd "$HOOK_COMMAND" --arg fp "$FINGERPRINT" '
    .hooks = (.hooks // {}) |
    .hooks.SessionStart = (
      [(.hooks.SessionStart // [])[]
        | .hooks = [(.hooks // [])[]
            | select(((.command // "") | contains($fp)) | not)]
        | select((.hooks | length) > 0)]
      + [{
          "matcher": "startup|clear",
          "hooks": [{
            "type": "command",
            "command": $cmd,
            "timeout": 5
          }]
        }]
    )
  ' "$SETTINGS" >"$tmp"
  mv "$tmp" "$SETTINGS"
  ok "registered SessionStart startup|clear hook in: $SETTINGS"
fi

echo "[deferrals/install] done"
