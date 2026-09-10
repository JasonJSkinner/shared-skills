#!/usr/bin/env python3
"""Register / deregister / report the orchestrator-posture Stop hook in settings.json.

Shared by install.sh, status.sh and uninstall.sh (the /decisions trio shape, with the
settings edit done by JSON parse+dump instead of jq — stdlib only).

Byte-safety: `json.dumps(obj, indent=2, ensure_ascii=False) + "\\n"` is verified to
round-trip this settings.json exactly, so an install+uninstall pair leaves the file
byte-identical to the pre-install backup.
"""
import json
import os
import shlex
import shutil
import sys

SETTINGS = os.path.expanduser(os.environ.get(
    "ORCHESTRATOR_POSTURE_SETTINGS", "~/.claude/settings.json"))
STATE_DIR = os.path.expanduser(os.environ.get(
    "ORCHESTRATOR_POSTURE_STATE_DIR", "~/.claude/state/orchestrator-posture"))
BACKUP = os.path.join(STATE_DIR, "settings.json.pre-install.bak")
SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posture_run.py")
COMMAND = "python3 {} ledger --hook".format(shlex.quote(SCRIPT))
FINGERPRINT = "posture_run.py ledger --hook"
# The collector's own deadline (posture_run.STOP_DEADLINE_SECONDS = 8 s) sits inside
# this, so it always writes a partial line and exits 0 before the harness would kill it.
HOOK_TIMEOUT_SECONDS = 15


def load():
    with open(SETTINGS) as fh:
        return json.load(fh)


def dump(obj):
    tmp = SETTINGS + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, SETTINGS)


def registered(obj):
    for entry in (obj.get("hooks", {}).get("Stop") or []):
        for h in (entry.get("hooks") or []):
            if FINGERPRINT in (h.get("command") or ""):
                return True
    return False


def cmd_add():
    if not os.path.exists(SETTINGS):
        print("  [error]     no settings.json at {}".format(SETTINGS), file=sys.stderr)
        return 1
    if not os.path.exists(SCRIPT):
        print("  [error]     missing {}".format(SCRIPT), file=sys.stderr)
        return 1
    obj = load()
    if registered(obj):
        print("  [skip]      Stop hook already registered in {}".format(SETTINGS))
        return 0
    os.makedirs(STATE_DIR, exist_ok=True)
    shutil.copy2(SETTINGS, BACKUP)
    print("  [installed] pre-install backup: {}".format(BACKUP))
    obj.setdefault("hooks", {}).setdefault("Stop", []).append(
        {"matcher": "*", "hooks": [{"type": "command", "command": COMMAND,
                                    "timeout": HOOK_TIMEOUT_SECONDS}]})
    dump(obj)
    print("  [installed] Stop hook registered: {}".format(COMMAND))
    return 0


def cmd_remove():
    if not os.path.exists(SETTINGS):
        print("  [warn]      no settings.json at {}".format(SETTINGS))
        return 0
    obj = load()
    if not registered(obj):
        print("  [skip]      Stop hook not present in {}".format(SETTINGS))
        return 0
    stop = []
    for entry in (obj.get("hooks", {}).get("Stop") or []):
        entry = dict(entry)
        entry["hooks"] = [h for h in (entry.get("hooks") or [])
                          if FINGERPRINT not in (h.get("command") or "")]
        if entry["hooks"]:
            stop.append(entry)
    if stop:
        obj["hooks"]["Stop"] = stop
    else:
        obj["hooks"].pop("Stop", None)
    dump(obj)
    print("  [removed]   Stop hook entry from {}".format(SETTINGS))
    if os.path.exists(BACKUP):
        same = open(BACKUP).read() == open(SETTINGS).read()
        print("  [{}] settings.json {} the pre-install backup".format(
            "ok      " if same else "warn    ",
            "is byte-identical to" if same else "DIFFERS from"))
    return 0


def cmd_status():
    print("  [{}] settings.json Stop hook: {}".format(
        "yes" if os.path.exists(SETTINGS) and registered(load()) else "no ", COMMAND))
    print("  [{}] collector script: {}".format(
        "yes" if os.path.exists(SCRIPT) else "no ", SCRIPT))
    print("  [{}] state dir: {}".format(
        "yes" if os.path.isdir(STATE_DIR) else "no ", STATE_DIR))
    sentinels = sorted(f for f in os.listdir(STATE_DIR)
                       if f.startswith("sentinel-")) if os.path.isdir(STATE_DIR) else []
    print("")
    print("  live sentinels ({}):".format(len(sentinels)))
    for s in sentinels:
        print("    - {}".format(s))
    if not sentinels:
        print("    (none — the hook returns immediately for every session)")
    runs = os.path.join(STATE_DIR, "runs.jsonl")
    n = sum(1 for _ in open(runs)) if os.path.exists(runs) else 0
    print("  runs.jsonl: {} line(s){}".format(n, "" if n else " (absent)"))
    return 0


if __name__ == "__main__":
    sys.exit({"add": cmd_add, "remove": cmd_remove,
              "status": cmd_status}[sys.argv[1]]())
