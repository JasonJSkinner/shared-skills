#!/usr/bin/env bash
# Report deferrals SessionStart digest state. Read-only.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SRC="${SCRIPT_DIR}/deferrals_digest.sh"
HOOK_TARGET="${HOME}/.claude/hooks/deferrals_digest.sh"
CLI="${HOME}/.claude/skills/deferrals/scripts/deferrals.py"
SETTINGS="${HOME}/.claude/settings.json"
HOOK_COMMAND="bash ~/.claude/hooks/deferrals_digest.sh"
FINGERPRINT="deferrals_digest.sh"

yes()  { printf "  [yes] %s\n" "$1"; }
no()   { printf "  [no ] %s\n" "$1"; }
warn() { printf "  [?  ] %s\n" "$1"; }

echo "[deferrals/status]"

if [[ -f "$CLI" ]]; then
  if python3 "$CLI" --help 2>/dev/null | grep -qw digest; then
    yes "deployed CLI has digest verb: $CLI"
  else
    no "deployed CLI lacks digest verb: $CLI"
  fi
else
  no "deployed CLI missing: $CLI"
fi

if [[ -f "$HOOK_TARGET" ]]; then
  if [[ -f "$HOOK_SRC" ]] && cmp -s "$HOOK_SRC" "$HOOK_TARGET"; then
    yes "hook installed and matches draft: $HOOK_TARGET"
  else
    warn "hook installed but differs from draft: $HOOK_TARGET"
  fi
  [[ -x "$HOOK_TARGET" ]] || warn "hook is not executable: $HOOK_TARGET"
else
  no "hook missing: $HOOK_TARGET"
fi

if [[ -f "$SETTINGS" ]]; then
  exact=$(jq --arg cmd "$HOOK_COMMAND" '
    [(.hooks.SessionStart // [])[]?
      | select((.matcher // "") == "startup|clear")
      | .hooks[]?
      | select(.type == "command" and .command == $cmd and .timeout == 5)]
    | length
  ' "$SETTINGS" 2>/dev/null)
  any=$(jq --arg fp "$FINGERPRINT" '
    [(.hooks.SessionStart // [])[]? | .hooks[]?
      | select((.command // "") | contains($fp))]
    | length
  ' "$SETTINGS" 2>/dev/null)
  if [[ "$exact" == "1" && "$any" == "1" ]]; then
    yes "one startup|clear hook registered with timeout 5: $SETTINGS"
  elif [[ "${any:-0}" -gt 0 ]] 2>/dev/null; then
    warn "digest hook registration exists but is not canonical: $SETTINGS"
  else
    no "digest hook not registered: $SETTINGS"
  fi
else
  no "settings file missing: $SETTINGS"
fi
