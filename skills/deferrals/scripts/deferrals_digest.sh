#!/usr/bin/env bash
# SessionStart hook: one-line digest from the canonical deferrals CLI.
# Matcher stays startup|clear in settings.json. Silent and fail-open.

INPUT=$(cat 2>/dev/null)
CWD=$(jq -r '.cwd // empty' <<<"$INPUT" 2>/dev/null)
[[ -n "$CWD" ]] || CWD=$(pwd 2>/dev/null)
[[ -n "$CWD" ]] || exit 0

GIT_DIR=$(git -C "$CWD" rev-parse --git-common-dir 2>/dev/null)
if [[ -n "$GIT_DIR" ]]; then
  case "$GIT_DIR" in
    /*) ;;
    *) GIT_DIR="$CWD/$GIT_DIR" ;;
  esac
  # `--git-common-dir` is relative from any non-root cwd (`../.git`), so dirname alone
  # leaves a `..` in the path and yields a bogus key. Normalize before slugifying.
  PROJECT_ROOT=$(cd "$(dirname "$GIT_DIR")" 2>/dev/null && pwd -P) || PROJECT_ROOT="$CWD"
else
  PROJECT_ROOT="$CWD"
fi
[[ -n "$PROJECT_ROOT" ]] || PROJECT_ROOT="$CWD"

PROJECT_KEY=$(printf '%s' "$PROJECT_ROOT" | tr '/ ' '--')
CLI="${HOME}/.claude/skills/deferrals/scripts/deferrals.py"
[[ -f "$CLI" ]] || exit 0

DATA_ROOT="${DEFERRALS_ROOT:-${HOME}/.claude/deferrals}"
LINE=$(python3 "$CLI" \
  --root "$DATA_ROOT" \
  --project-key "$PROJECT_KEY" \
  digest 2>/dev/null) || exit 0

[[ -n "$LINE" ]] || exit 0

# --- Watermark: parallel-session dedup + rate-limited tend nudge (D3/W5) ---------
# Hidden file, so the index classifier never treats it as a project index. Locking
# uses fcntl via python3 (already a hard dependency here) — macOS ships no flock(1).
# Every failure path falls through to printing: the watermark may suppress a
# duplicate, but it must never swallow a first-of-its-kind line.
python3 - "$DATA_ROOT" "$PROJECT_KEY" "${DEFERRALS_DEDUP_SECONDS:-90}" "${DEFERRALS_NUDGE_SECONDS:-1209600}" <<'PY' 2>/dev/null
import fcntl, json, os, sys, time
root, key, dedup, nudge_after = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
wm = os.path.join(os.path.expanduser(root), ".digest-watermark.json")
os.makedirs(os.path.dirname(wm), exist_ok=True)
now = int(time.time())
with open(wm + ".lock", "w") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        state = json.load(open(wm))
        if not isinstance(state, dict):
            raise ValueError
    except Exception:
        state = {}
    surfaced = state.get("surfaced") if isinstance(state.get("surfaced"), dict) else {}
    last_seen = surfaced.get(key, 0) if isinstance(surfaced.get(key), int) else 0
    last_nudged = state.get("nudged", 0) if isinstance(state.get("nudged"), int) else 0
    if now - last_seen < dedup:
        sys.exit(4)                       # another session just surfaced this project
    nudge = now - last_nudged >= nudge_after
    surfaced[key] = now
    state["surfaced"] = surfaced
    if nudge:
        state["nudged"] = now
    tmp = wm + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(state, fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, wm)
    sys.exit(5 if nudge else 0)
PY
case $? in
  4) exit 0 ;;                                     # deduped — silent by design
  5) LINE="$LINE · consider \`/deferrals tend\`" ;; # nudge window elapsed
esac

printf '%s\n' "$LINE"
exit 0
