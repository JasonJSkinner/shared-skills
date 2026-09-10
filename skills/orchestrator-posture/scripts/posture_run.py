#!/usr/bin/env python3
"""orchestrator-posture v0.4 instrumentation — a descriptive recorder.

Verbs: start · note · accept · ledger · review · check   (`--help` on each).

Design constraints this file must keep:
  * Missing evidence produces `unknown`, NEVER zero.
  * brief_bytes / return_bytes / wake_ups are three separate fields and are never summed.
  * `ledger` is observational: it NEVER executes a manifest check command.
  * Estimates are recorded before dispatch, append-only, in <RUN_DIR>/.posture/events.jsonl.
  * Coverage is reported alongside accuracy; unmatched launches are counted.
  * `review` states counts and recurrence only — no causal claim.

Stream/transcript parsing follows the pilot parser's verified behavior: group assistant
records by `message.id`, dedupe
tool blocks by block id, classify Bash commands as mutating vs reading, and match codex
lanes only when `codex` sits in command position (or the writeback wrapper is named).

Two record shapes are handled:
  * `claude -p --output-format stream-json` (the pilot's `claude.stream.jsonl`):
    lead records have `parent_tool_use_id is None`.
  * Claude Code session transcripts (`~/.claude/projects/<enc>/<uuid>.jsonl`):
    lead records have `isSidechain` falsey.
"""
import argparse
import datetime
import fcntl
import glob as globmod
import hashlib
import itertools
import json
import tempfile
import os
import re
import sys
import time

STATE_DIR = os.path.expanduser("~/.claude/state/orchestrator-posture")
RUNS_JSONL = os.path.join(STATE_DIR, "runs.jsonl")
INVEST_DIR = os.path.join(STATE_DIR, "investigations")
STANCE_VERSION_DEFAULT = "0.4"

# Bounds for one ledger invocation.
MAX_BYTES_DEFAULT = 4_000_000
MAX_SECONDS_DEFAULT = 10.0
DEBOUNCE_SECONDS = 60
SENTINEL_MAX_AGE_SECONDS = 24 * 3600
COMPLETE_MAX_AGE_SECONDS = 3600          # a completed run's sentinel retires within the hour
# B4: ONE deadline covers every step of a Stop collection — timestamp resolution,
# stream scan, manifest read, wrong-path walk, hashing, event reads, ledger rewrite.
# _settings_hook.py declares a 15 s hook timeout; 8 s leaves margin for process start.
STOP_DEADLINE_SECONDS = 8.0
WALK_MAX_DEPTH = 3                       # wrong-path diagnostic walk, bounded
WALK_MAX_ENTRIES = 2000
LAUNCH_LOG_CAP = 500                     # per-run launch timestamps kept for matching
SESSION_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")   # S15: one path component
ID_MEMO_CAP = 20000          # dedup memo size before oldest ids are dropped

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
DISPATCH_TOOLS = {"Agent", "Task", "Workflow"}

# `codex` must sit in command position to count as a lane launch.
CODEX_RE = re.compile(
    r"(?:^|[;&|(]|\bnohup\s+)\s*codex\s+(?:-{1,2}[\w-]+(?:[= ]\S+)?\s+)*exec\b"
    r"|codex-writeback-lane\.sh", re.M)
# Edit/Write counts miss Bash mutations, so classify common write commands too.
BASH_WRITE_RE = re.compile(
    r">>?\s*(?!/dev/null)[\w./~$-]|\bsed\s+-i\b|\btee\b|\bcp\s|\bmv\s|\brm\s|"
    r"\bmkdir\b|\btouch\b|\bpatch\s|\bapply_patch\b|\bgit\s+(?:apply|checkout|mv|rm)\b")
CODEX_MODEL_RE = re.compile(r"-m\s+([\w.\-]+)")
# The codex write-back guard's rejection marker, as it appears in a lane launch log /
# tool result, for example "FAIL ... out-of-scope writes (1)".
# Require the guard's own failure SHAPE — the parenthesised count it prints
# ("out-of-scope writes (3):"). A bare mention of the phrase is prose ABOUT the guard,
# and this skill's own status paragraph contains one, so the loose form self-triggers.
WRITEBACK_REJECT_RE = re.compile(r"out-of-scope writes\s*\(\d+\)", re.I)
# A lane failure visible in the transcript itself: an errored tool result, a non-zero
# exit line, or the write-back guard's FAIL block. Lead-declared "it failed" is not this.
LANE_FAILURE_RE = re.compile(
    r"\bFAIL\b|exit(?:ed)?\s+(?:code\s+)?[1-9]\d*\b|non-zero exit|"
    r"\bTraceback \(most recent call last\)", re.I)

MANUAL_FAILURE_CODES = {
    "cap-gate-abort", "usage-fetch-failure", "trivial-write-delegated",
    "routing-md-on-bounded-task", "absorbed-lane-without-estimate",
    "same-model-verifier", "instrumentation-incomplete",
}

DISCLAIMER = ("Descriptive only: observed counts, lead-declared values and outcomes. "
              "No causal claim is made or implied; recurrence names what to investigate, "
              "not what to prescribe.")


# --------------------------------------------------------------------------- helpers
COLLECTOR_LOG = os.path.join(STATE_DIR, "collector.log")
COLLECTOR_LOG_LINES = 200
BUDGET = {"deadline": None, "timed_out": False}


def log_collector(msg):
    """Item 12: exceptions are recorded, never swallowed. Bounded to the last 200 lines.
    The hook contract is untouched — nothing reaches stdout and the exit code stays 0."""
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        line = "{} {}\n".format(now_iso(), msg)
        old = []
        if os.path.exists(COLLECTOR_LOG):
            with open(COLLECTOR_LOG, errors="replace") as fh:
                old = fh.readlines()
        with open(COLLECTOR_LOG, "w") as fh:
            fh.writelines((old + [line])[-COLLECTOR_LOG_LINES:])
    except OSError:
        pass


def budget_start(seconds):
    """Arm the shared collection deadline (None disables it)."""
    BUDGET["deadline"] = (time.time() + seconds) if seconds else None
    BUDGET["timed_out"] = False


def over_budget():
    d = BUDGET["deadline"]
    if d is not None and time.time() > d:
        BUDGET["timed_out"] = True
        return True
    return False


def tag(value, evidence):
    """Every ledger field carries its evidence tag: observed|proxy|manual|unknown."""
    assert evidence in ("observed", "proxy", "manual", "unknown")
    return {"value": value, "evidence": evidence}


def unknown():
    return tag(None, "unknown")


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def valid_session(session_id):
    """A session id becomes a filename; it must be exactly one safe path component."""
    return bool(session_id and SESSION_ID_RE.match(str(session_id)))


def sentinel_path(session_id):
    if not valid_session(session_id):
        raise ValueError("unsafe session id: {!r}".format(session_id))
    return os.path.join(STATE_DIR, "sentinel-{}.json".format(session_id))


def read_json(path, default=None):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "{}.{}.tmp".format(path, os.getpid())
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=2)
    os.replace(tmp, path)


def events_path(run_dir):
    return os.path.join(run_dir, ".posture", "events.jsonl")


def current_run_id(run_dir):
    cur = read_json(os.path.join(run_dir, ".posture", "current_run.json")) or {}
    return cur.get("run_id")


def append_event(run_dir, ev):
    """Append-only. Estimates recorded here are never rewritten (Astra §2)."""
    path = events_path(run_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ev.setdefault("at", now_iso())
    if "run_id" not in ev:
        rid = current_run_id(run_dir)
        if rid:
            ev["run_id"] = rid
    with open(path, "a") as fh:
        fh.write(json.dumps(ev, sort_keys=True) + "\n")
    return path


EVENT_PARSE_ERRORS = {"n": 0}


def read_events(run_dir, run_id=None):
    """Events for ONE run. A reused run dir accumulates earlier runs' events; those are
    ignored rather than folded in (they would inflate this run's notes and accepts).

    A malformed line is COUNTED, never silently skipped: a dropped `accept` turns its
    deliverable into `unchecked`, which on a complete run becomes an observed
    lost-deliverable that feeds recurrence. The count downgrades the deliverable tags to
    proxy and raises instrumentation-incomplete, which makes the run ineligible."""
    EVENT_PARSE_ERRORS["n"] = 0
    out = []
    try:
        with open(events_path(run_dir), errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        ev = json.loads(line)
                    except ValueError:
                        EVENT_PARSE_ERRORS["n"] += 1
                        continue
                    if run_id and ev.get("run_id") and ev["run_id"] != run_id:
                        continue                      # out-of-run: an earlier run here
                    out.append(ev)
                if over_budget():
                    break
    except OSError:
        pass
    return out


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def new_run_id(session_id):
    return "{}-{}".format(time.strftime("%Y%m%dT%H%M%S"), str(session_id)[:8])


# ------------------------------------------------------------------- stream scanning
def blank_counters():
    return {
        "assistant_messages": 0,
        "dispatch_subagent": 0,
        "dispatch_codex_lane": 0,
        "brief_bytes": 0,
        "return_bytes": 0,
        "wake_ups": 0,
        "lead_edit_write": 0,
        "lead_bash_mutations": 0,
        "writeback_rejected": 0,
        "unreturned_launches": 0,
        "records": 0,
        "parse_errors": 0,
        "dispatch_models": [],
        "launches": [],              # B2: {"ts", "kind"} per observed launch, in order
        "lane_failures": [],         # item 10: transcript-observed failures, {"ts"}
        "scan_stopped_early": False, # item 5: deadline cut the scan short
        "truncation_resets": 0,      # S5: transcript shrank under us
    }


def blank_cursor():
    return {"offset": 0, "seen_msg_ids": [], "seen_block_ids": [], "open_dispatch_ids": []}


RECOGNIZED_TYPES = {"assistant", "user", "system", "result", "summary", "attachment",
                    "file-history-snapshot", "queue-operation", "atis-latch",
                    "last-prompt", "mode", "permission-mode", "ai-title", "custom-title",
                    "agent-name", "file-history-delta"}


def transcript_shape(path, probe_bytes=262144):
    """Item 4: is this a Claude Code transcript at all?

    A readable file of the wrong shape (a Codex rollout, a log, someone's notes) must not
    yield a confident 0 for every count. Probe the head for records carrying a recognized
    `type`; none found -> "unsupported", and the caller blanks every derived field.
    """
    try:
        with open(path, "rb") as fh:
            blob = fh.read(probe_bytes)
    except OSError:
        return "unreadable"
    cut = blob.rfind(b"\n")
    text = blob[:cut + 1].decode("utf-8", errors="replace") if cut >= 0 else \
        blob.decode("utf-8", errors="replace")
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict) and rec.get("type") in RECOGNIZED_TYPES:
            return "ok"
    return "unsupported"


def _is_lead(rec):
    if rec.get("parent_tool_use_id") is not None:
        return False
    return not rec.get("isSidechain")


def _is_wakeup(rec):
    """Task-notification user record (proxy for a lead wake-up).

    Field-based, per reference_cc_transcript_human_turn_discriminator: a string-content
    user record is NOT a human turn. A task notification is promptSource=system with
    isMeta falsey, or (legacy, field absent) starts with the literal tag.
    """
    if rec.get("type") != "user":
        return False
    msg = rec.get("message") or {}
    content = msg.get("content") if isinstance(msg, dict) else None
    if not isinstance(content, str):
        return False
    if rec.get("isMeta") or rec.get("isCompactSummary") or rec.get("isSidechain"):
        return False
    ps = rec.get("promptSource")
    if ps is not None:
        return ps == "system"
    return content.startswith("<task-notification>")


def _memo_add(lst, seen, value):
    if value in seen:
        return False
    seen.add(value)
    lst.append(value)
    if len(lst) > ID_MEMO_CAP:
        dropped = lst[:-ID_MEMO_CAP]
        del lst[:-ID_MEMO_CAP]
        for d in dropped:
            seen.discard(d)
    return True


def _rec_time(rec):
    ts = rec.get("timestamp")
    if not isinstance(ts, str):
        return None
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def resolve_start_offset(path, started_at):
    """Byte offset of the first record at/after `started_at`. Read-only, one pass.

    This is what scopes a ledger to ITS OWN RUN. A session transcript accumulates
    everything the session ever did, including branches discarded by /rewind, so an
    unscoped collector reports the whole file's history as the run's own work.

    Scoping is by BYTE OFFSET ONLY: records written before the run began are excluded,
    which covers pre-run history and any pre-run rewind. Records from a branch abandoned
    by a rewind DURING the run stay counted — deciding liveness needs a full-file
    parentUuid walk from the live leaf, which cannot be done incrementally, so it is not
    attempted. Returns (offset, evidence) where evidence is "observed" when a timestamped
    boundary was found and "unknown" when the file carries no usable timestamps.
    """
    try:
        cutoff = datetime.datetime.fromisoformat(started_at)
    except (TypeError, ValueError):
        return 0, "unknown"
    pos, saw_ts = 0, False
    try:
        with open(path, "rb") as fh:
            for raw in fh:
                if over_budget():
                    return 0, "unknown"
                try:
                    rec = json.loads(raw.decode("utf-8", errors="replace"))
                except ValueError:
                    pos += len(raw)
                    continue
                t = _rec_time(rec)
                if t is not None:
                    saw_ts = True
                    if t >= cutoff:
                        return pos, "observed"
                pos += len(raw)
    except OSError:
        return 0, "unknown"
    # every record predates the run: start at end-of-file
    return (pos, "observed") if saw_ts else (0, "unknown")


def _log_launch(counters, rec, kind):
    """B2: keep each launch's timestamp so notes can be matched by order AND time."""
    if len(counters["launches"]) < LAUNCH_LOG_CAP:
        t = _rec_time(rec)
        counters["launches"].append({"ts": t.isoformat() if t else None, "kind": kind})


def scan_stream(path, counters, cursor, max_bytes=MAX_BYTES_DEFAULT,
                max_seconds=MAX_SECONDS_DEFAULT):
    """Advance `counters`/`cursor` over new bytes of `path`. Read-only, bounded.

    Only whole lines are consumed; a truncated final line stays unread and the offset
    stops before it, so the next invocation picks it up (idempotent by offset).
    Returns the number of bytes consumed this call.
    """
    if not os.path.exists(path):
        return 0
    size = os.path.getsize(path)
    start = cursor.get("offset", 0)
    if start > size:
        # The transcript shrank: our offset is meaningless and so are the counters
        # accumulated against it. Reset BOTH and record that we did (build_ledger
        # downgrades the affected fields to proxy).
        resets = counters.get("truncation_resets", 0) + 1
        cursor.clear(); cursor.update(blank_cursor())
        counters.clear(); counters.update(blank_counters())
        counters["truncation_resets"] = resets
        start = 0
    if start >= size:
        return 0

    seen_msgs = set(cursor["seen_msg_ids"])
    seen_blocks = set(cursor["seen_block_ids"])
    open_ids = set(cursor["open_dispatch_ids"])
    deadline = time.time() + max_seconds
    consumed = 0

    with open(path, "rb") as fh:
        fh.seek(start)
        buf = fh.read(max_bytes)
    cut = buf.rfind(b"\n")
    if cut < 0:
        if start + len(buf) >= size or over_budget():
            return 0            # genuine truncated tail (or out of budget): leave it
        # One line is longer than the byte cap. Reading only `max_bytes` would stall
        # the collector forever with no signal, so consume exactly that one line.
        with open(path, "rb") as fh:
            fh.seek(start)
            buf = fh.readline()
        if not buf.endswith(b"\n"):
            return 0
        cut = len(buf) - 1
    body = buf[:cut + 1]
    text = body.decode("utf-8", errors="replace")

    for line in text.split("\n"):
        if time.time() > deadline or over_budget():
            counters["scan_stopped_early"] = True
            break
        consumed += len(line.encode("utf-8", errors="replace")) + 1
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            counters["parse_errors"] += 1
            continue
        counters["records"] += 1
        if _is_wakeup(rec):
            counters["wake_ups"] += 1
        if not _is_lead(rec):
            continue
        msg = rec.get("message") or {}
        if not isinstance(msg, dict):
            continue
        blocks = [b for b in (msg.get("content") or []) if isinstance(b, dict)]

        if rec.get("type") == "user":
            for b in blocks:
                if b.get("type") != "tool_result":
                    continue
                content = b.get("content")
                blob = content if isinstance(content, str) else json.dumps(content)
                text_len = len(blob.encode("utf-8", errors="replace"))   # S9: bytes
                if isinstance(content, str) and WRITEBACK_REJECT_RE.search(content):
                    counters["writeback_rejected"] += 1
                # item 10: a lane failure is only "observed" when the TRANSCRIPT shows it
                if (b.get("is_error") or (isinstance(content, str)
                        and LANE_FAILURE_RE.search(content))) \
                        and len(counters["lane_failures"]) < LAUNCH_LOG_CAP:
                    t = _rec_time(rec)
                    counters["lane_failures"].append(
                        {"ts": t.isoformat() if t else None})
                if b.get("tool_use_id") in open_ids:
                    counters["return_bytes"] += text_len
                    open_ids.discard(b.get("tool_use_id"))
            continue

        if rec.get("type") != "assistant":
            continue
        mid = msg.get("id")
        # Several assistant RECORDS share one message.id, each carrying one content
        # block. Count the message once, but still walk
        # every record's blocks — block-id dedup is what prevents double counting.
        if not mid or _memo_add(cursor["seen_msg_ids"], seen_msgs, mid):
            counters["assistant_messages"] += 1
        for b in blocks:
            if b.get("type") != "tool_use":
                continue
            bid = b.get("id")
            if bid and not _memo_add(cursor["seen_block_ids"], seen_blocks, bid):
                continue
            name = b.get("name")
            inp = b.get("input") or {}
            if name in EDIT_TOOLS:
                counters["lead_edit_write"] += 1
            elif name in DISPATCH_TOOLS:
                counters["dispatch_subagent"] += 1
                counters["brief_bytes"] += len(
                    str(inp.get("prompt", "")).encode("utf-8", errors="replace"))
                _log_launch(counters, rec, "subagent")
                counters["dispatch_models"].append(
                    str(inp.get("subagent_type") or inp.get("agent") or name))
                if bid:
                    open_ids.add(bid)
                    cursor["open_dispatch_ids"] = sorted(open_ids)
            elif name == "Bash":
                cmd = str(inp.get("command", ""))
                if BASH_WRITE_RE.search(cmd):
                    counters["lead_bash_mutations"] += 1
                if CODEX_RE.search(cmd):
                    counters["dispatch_codex_lane"] += 1
                    _log_launch(counters, rec, "codex_lane")
                    mm = CODEX_MODEL_RE.search(cmd)
                    counters["dispatch_models"].append(mm.group(1) if mm else "codex")
                    if bid:
                        open_ids.add(bid)

    cursor["open_dispatch_ids"] = sorted(open_ids)
    counters["unreturned_launches"] = len(open_ids)
    cursor["offset"] = start + min(consumed, len(body))
    return consumed


# ------------------------------------------------------------------------- manifest
MANIFEST_PATH_RE = re.compile(r"`([^`]+)`")
MANIFEST_CHECK_RE = re.compile(r"check:\s*`?([^`\n]+)`?", re.I)
MANIFEST_BASELINE_RE = re.compile(r"baseline-sha256:\s*([0-9a-f]{64})", re.I)


def _parse_bullet_manifest(lines, unparsed):
    """- `path/to/thing` — check: `cmd`  [baseline-sha256: <hex>]"""
    items = []
    for line in lines:
        if not re.match(r"\s*[-*]\s+", line):
            continue
        m = MANIFEST_PATH_RE.search(line)
        if not m:
            unparsed.append(line.strip()[:120])     # item 11: reported, not dropped
            continue
        chk = MANIFEST_CHECK_RE.search(line)
        base = MANIFEST_BASELINE_RE.search(line)
        items.append({"path": m.group(1).strip(),
                      "check": chk.group(1).strip() if chk else None,
                      "baseline_sha256": base.group(1).lower() if base else None})
    return items


def _parse_table_manifest(lines, unparsed):
    """| # | deliverable | required path | check command |  — column-addressed.

    The path column is found from the HEADER, not by looking for backticks: in real
    manifests the path cell is bare and the CHECK cell is the backticked one, so a
    "first backticked token wins" rule reads the check command as the path.
    """
    rows = [ln.strip() for ln in lines if ln.strip().startswith("|")]
    if len(rows) < 3:
        unparsed.extend(r[:120] for r in rows)
        return []
    header = [c.strip().lower() for c in rows[0].strip("|").split("|")]
    pi = next((i for i, h in enumerate(header) if "path" in h), None)
    if pi is None:
        pi = next((i for i, h in enumerate(header)
                   if "deliverable" in h or "artifact" in h or "file" in h), None)
    if pi is None:
        unparsed.extend(r[:120] for r in rows[2:])  # no path column: nothing is parseable
        return []
    ci = next((i for i, h in enumerate(header) if "check" in h), None)
    items = []
    for row in rows[2:]:                       # row 1 is the |---| separator
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) <= pi:
            unparsed.append(row[:120])
            continue
        cell = cells[pi]
        m = MANIFEST_PATH_RE.search(cell)      # unwrap backticks when present
        if m:
            cell = m.group(1).strip()
        if not cell or not cell.strip("-: "):
            unparsed.append(row[:120])
            continue
        chk = cells[ci] if ci is not None and len(cells) > ci else None
        base = MANIFEST_BASELINE_RE.search(row)
        # one cell may name several paths ("a.md, b.md") — but a brace set's commas
        # belong to the set, so only comma-split when no brace group is present
        parts = [cell] if "{" in cell else cell.split(",")
        for p in [x.strip() for x in parts if x.strip()]:
            items.append({"path": p, "check": chk.strip("` ") if chk else None,
                          "baseline_sha256": base.group(1).lower() if base else None})
    return items


def read_manifest(run_dir):
    """Parse <RUN_DIR>/DELIVERABLES.md. Check commands are RECORDED, never executed.

    Both forms are accepted — bullet lines and a pipe table with path/check columns.
    Returns (items, unparsed_rows); items is None when the file is absent and [] when it
    is present but yields nothing — the caller must distinguish those (an empty parse is
    an instrumentation failure, never an "observed" zero). Item 11: a row that looks like
    a deliverable but yields no path is REPORTED in `unparsed`, never silently dropped.
    """
    path = os.path.join(run_dir, "DELIVERABLES.md")
    if not os.path.exists(path):
        return None, []
    lines = open(path, errors="replace").read().splitlines()
    unparsed = []
    items = _parse_bullet_manifest(lines, unparsed) + _parse_table_manifest(lines, unparsed)
    return items, unparsed


def _expand(spec, run_dir):
    """Path spec -> (hits, specs, is_glob). Handles ~, one level of {a,b}, and globs.

    S10: a brace set expands to several REQUIRED members, so the caller checks that
    every member exists rather than treating one hit as satisfaction.
    """
    spec = os.path.expanduser(spec)
    if not os.path.isabs(spec):
        spec = os.path.join(run_dir, spec)
    m = re.search(r"\{([^{}]*,[^{}]*)\}", spec)
    specs = ([spec[:m.start()] + alt + spec[m.end():] for alt in m.group(1).split(",")]
             if m else [spec])
    is_glob = any(ch in spec for ch in "*?[")
    # A brace member is satisfied by its own existence (or, if it is itself a glob
    # pattern, by matching >= 1 file). `unmet` names the members nothing satisfied.
    hits, unmet = [], []
    for one in specs:
        got = globmod.glob(one) if any(ch in one for ch in "*?[") else \
            ([one] if os.path.exists(one) else [])
        hits.extend(got)
        if not got:
            unmet.append(one)
    return hits, specs, is_glob, unmet


def classify_deliverables(run_dir, manifest, events, run_id=None):
    """Two independent axes, never merged.

    FILESYSTEM AXIS (observed — these are facts this process established by looking):
      present | missing | wrong_path | unchanged
    ACCEPTANCE AXIS (what the lead said about them):
      `unchecked` counts existing deliverables with NO accept event — an observed
      absence. The accept RESULTS themselves are lead self-report and leave here in
      `lead_declared`, which the caller tags `manual`. A passing accept never promotes
      anything into `present`: this recorder does not run the check command, so it
      cannot corroborate the claim, and folding the claim into an `observed` bucket is
      precisely the "looks objective" failure it exists to prevent.

    Accepts bind to a manifest entry by EXACT path (raw string, or after ~/brace/glob
    expansion). Basename matching is deliberately absent — it silently binds
    `a/report.md` to `b/report.md`. `_find_by_basename` survives only as the wrong-path
    DIAGNOSTIC, which reports a suspicion, not an acceptance.

    OUT OF SCOPE: reconciling the manifest against the run's stored objective (does the
    manifest list the deliverables the objective actually required?). That needs natural
    language judgement and stays a manual review item — see `review`.

    Returns (buckets, lead_declared, unmatched_accepts).
    """
    accepts = [e for e in events if e.get("kind") == "accept"
               and not (run_id and e.get("run_id") and e["run_id"] != run_id)]
    used = set()
    buckets = {"present": [], "missing": [], "wrong_path": [], "unchanged": [],
               "unchecked": []}
    lead_declared = {"pass": [], "fail": [], "unchanged": []}
    partial = False
    for item in manifest:
        if over_budget():
            partial = True       # item 5: never leave observed buckets half-filled
            break
        p = item["path"]
        hits, specs, is_glob, unmet = _expand(p, run_dir)
        expanded = set(specs) | set(hits)
        evs = [e for e in accepts
               if str(e.get("deliverable")) == p
               or os.path.expanduser(str(e.get("deliverable"))) in expanded]
        for e in evs:
            used.add(id(e))
        result = evs[-1].get("result") if evs else None
        if result in ("pass", "fail", "unchanged"):
            # item 2: EVERY accept result is lead self-report and stays here. The
            # observed `unchanged` bucket comes only from the baseline sha comparison.
            lead_declared[result].append(p)

        # item 11: EVERY brace member must be satisfied, glob members included.
        missing_members = unmet if len(specs) > 1 else []
        if not hits or missing_members:
            # S10: a brace set is satisfied only when every member exists.
            alt = _find_by_basename(run_dir, os.path.basename(specs[0]), specs[0])
            buckets["wrong_path" if (not hits and alt) else "missing"].append(
                p if not missing_members else "{} (missing: {})".format(
                    p, ", ".join(os.path.basename(x) for x in missing_members)))
            continue
        if item["baseline_sha256"] and os.path.isfile(hits[0]) and \
                sha256_file(hits[0]) == item["baseline_sha256"]:
            buckets["unchanged"].append(p)          # filesystem fact, not a claim
        else:
            buckets["present"].append(p)
        if not evs:
            buckets["unchecked"].append(p)      # exists, nobody checked it
    unmatched = [str(e.get("deliverable")) for e in accepts if id(e) not in used]
    return buckets, lead_declared, unmatched, partial


def _find_by_basename(run_dir, base, skip):
    """Wrong-path DIAGNOSTIC only — bounded walk (B4): depth <= 3, <= 2000 entries."""
    root_depth = os.path.abspath(run_dir).rstrip(os.sep).count(os.sep)
    seen = 0
    for root, dirs, files in os.walk(run_dir):
        if over_budget():
            return None
        if os.path.abspath(root).rstrip(os.sep).count(os.sep) - root_depth >= WALK_MAX_DEPTH:
            dirs[:] = []
        else:
            dirs[:] = [d for d in dirs if d not in (".git", ".posture", "node_modules")]
        seen += len(files) + len(dirs)
        if seen > WALK_MAX_ENTRIES:
            return None
        if base in files:
            cand = os.path.join(root, base)
            if os.path.abspath(cand) != os.path.abspath(skip):
                return cand
    return None


# --------------------------------------------------------------------------- ledger
def _parse_iso(v):
    try:
        return datetime.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _match_notes_to_launches(delegating, launches):
    """B2: a note matches the FIRST unmatched launch at/after the note's own timestamp.

    Order and time, not a count: `min(notes, launches)` claimed coverage for a note
    written after the launch it supposedly preceded, which is exactly the hindsight
    editing the pre-dispatch rule exists to prevent. A note with no later launch is
    reported as an unmatched NOTE; a launch no note precedes stays an unmatched LAUNCH.
    Dedupe by decision id first — a later `--actual` on the same id is not a new note.
    """
    first_by_id, ordered = {}, []
    for n in sorted(delegating, key=lambda x: str(x.get("at") or "")):
        did = n.get("id")
        if did and did in first_by_id:
            continue
        if did:
            first_by_id[did] = n
        ordered.append(n)
    used = [False] * len(launches)
    matched, unmatched_notes = 0, []
    for n in ordered:
        nt = _parse_iso(n.get("at"))
        hit = None
        for i, lch in enumerate(launches):
            if used[i]:
                continue
            lt = _parse_iso(lch.get("ts"))
            # item 3: a note with no usable timestamp never auto-matches — order alone
            # cannot show it preceded the launch, which is the whole point.
            if nt is not None and lt is not None and lt >= nt:
                hit = i
                break
        if hit is None:
            unmatched_notes.append(n.get("id"))
        else:
            used[hit] = True
            matched += 1
    return matched, unmatched_notes


def build_ledger(sentinel, counters, events, manifest, unparsed=None):
    """Assemble one runs.jsonl record. Every field carries an evidence tag."""
    failures = []
    run_dir = sentinel.get("run_dir") or ""
    scope = sentinel.get("scope") or {"mode": "unscoped", "evidence": "unknown"}
    # A transcript covers the whole SESSION. Anything counted from it is only "observed"
    # for this run once the run's start boundary is established; otherwise the counts
    # include pre-run history and are a proxy at best.
    scoped = "observed" if scope.get("evidence") == "observed" else "proxy"
    if scoped != "observed":
        failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                         "detail": "run start boundary not established ({}); transcript "
                                   "counts include pre-run history".format(scope.get("mode"))})

    # B3: no readable transcript means NO transcript-derived value — not a zero wearing
    # an evidence tag. `tscoped` is the tag those fields carry; `tval` blanks them.
    tstate = sentinel.get("transcript_state", "ok")
    complete = bool(sentinel.get("complete", False))
    if tstate != "ok":
        failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                         "detail": "transcript {}; every transcript-derived field is "
                                   "unknown".format(tstate)})
    if counters.get("parse_errors"):
        scoped = "proxy"           # item 5: unparsed records mean records went uncounted
        failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                         "detail": "{} unparsable transcript record(s); counts omit "
                                   "them".format(counters["parse_errors"])})
    if counters.get("scan_stopped_early") or BUDGET.get("timed_out"):
        scoped = "proxy"           # item 5: a partial scan cannot be an observed count
    if counters.get("truncation_resets"):
        scoped = "proxy"
        failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                         "detail": "transcript shrank mid-run ({} reset(s)); counts "
                                   "restart from the reset and are a proxy".format(
                                       counters["truncation_resets"])})
    if BUDGET.get("timed_out"):
        failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                         "detail": "collection hit its deadline; this line is partial"})

    def tval(value, evidence):
        """A transcript-derived field: unknown when the transcript could not be read."""
        return unknown() if tstate != "ok" else tag(value, evidence)

    notes = [e for e in events if e.get("kind") == "note"]
    # item 3: a note with no --estimate is not a precommitted estimate; it cannot be
    # matched to a launch and must not inflate coverage.
    delegating = [n for n in notes if n.get("route") in ("subagent", "suborch")
                  and n.get("estimate") is not None]
    routed = [n for n in notes if n.get("route") in ("subagent", "suborch")]
    lane_briefs = [n for n in notes if n.get("brief_bytes") is not None]
    observed_launches = counters["dispatch_subagent"] + counters["dispatch_codex_lane"]

    # --- estimates: precommitted, append-only; coverage reported beside accuracy.
    est_by_id, actual_by_id = {}, {}
    for n in notes:
        did = n.get("id")
        if did and n.get("estimate") is not None and did not in est_by_id:
            est_by_id[did] = {"estimate": n["estimate"], "unit": n.get("unit", "tokens")}
        if did and n.get("actual") is not None:
            actual_by_id[did] = n["actual"]
    accuracy = [{"id": k, "estimate": v["estimate"], "unit": v["unit"],
                 "actual": actual_by_id[k]} for k, v in sorted(est_by_id.items())
                if k in actual_by_id]
    matched, unmatched_note_ids = _match_notes_to_launches(
        delegating, counters.get("launches") or [])
    unmatched_launches = max(0, observed_launches - matched)
    # item 3: coverage is an order-and-time heuristic over lead-written notes -> proxy,
    # never observed; with no estimate-bearing notes there is nothing to cover.
    coverage = (tag(round(matched / observed_launches, 3), "proxy")
                if (observed_launches and delegating) else unknown())
    if delegating and not matched and observed_launches:
        failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                         "detail": "{} delegating note(s) matched no launch at or after "
                                   "their own timestamps".format(len(delegating))})

    # --- deliverables
    lead_declared = {"pass": [], "fail": [], "unchanged": []}
    ev_errs = EVENT_PARSE_ERRORS["n"]
    ev_tag = "proxy" if ev_errs else None      # None = keep the computed tag
    if ev_errs:
        failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                         "detail": "{} unparsable event record(s); an accept may have "
                                   "been dropped".format(ev_errs)})
    if unparsed:
        failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                         "detail": "{} manifest row(s) named no parseable path".format(
                             len(unparsed))})
    if manifest is None:
        deliverables = unknown()
        failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                         "detail": "no DELIVERABLES.md in run dir"})
    elif not manifest:
        # A manifest that parses to nothing must NOT read as an observed empty result —
        # that is the "looks objective, says nothing" failure this recorder exists to
        # avoid. Unknown plus a named instrumentation failure.
        deliverables = unknown()
        failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                         "detail": "DELIVERABLES.md present but parsed to 0 entries "
                                   "(neither bullet nor path/check table form matched)"})
    else:
        buckets, lead_declared, unmatched_accepts, partial = classify_deliverables(
            run_dir, manifest, events, sentinel.get("run_id"))
        # item 5: a partial classification is not an observed result.
        deliverables = tag({k: len(v) for k, v in buckets.items()},
                           "proxy" if (partial or BUDGET.get("timed_out") or ev_errs)
                           else "observed")
        if partial:
            failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                             "detail": "deliverable classification stopped at the "
                                       "deadline; buckets are partial"})
        deliverables["paths"] = buckets
        deliverables["unparsed"] = unparsed or []
        deliverables["axes"] = ("present/missing/wrong_path/unchanged are filesystem "
                                "facts; unchecked counts existing deliverables with no "
                                "accept event. Accept RESULTS live in lead_declared.")
        for d in unmatched_accepts:
            failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                             "detail": "accept names {!r}, absent from the manifest".format(d)})
        # S7: an intermediate Stop is a checkpoint, not the end of the run — a
        # deliverable that has not landed yet is not lost. Record the buckets always;
        # raise lost-deliverable only once the run is declared complete.
        if complete:
            # item 3: a failure is only as good as the classification it came from.
            dtag = deliverables["evidence"]
            for kind in ("missing", "wrong_path", "unchanged", "unchecked"):
                for p in buckets[kind]:
                    failures.append({"code": "lost-deliverable",
                                     "sub_kind": kind.replace("_", "-"),
                                     "evidence": dtag, "detail": p})
        if complete and not any(e.get("kind") == "accept" for e in events):
            failures.append({"code": "acceptance-check-omitted",
                             "evidence": deliverables["evidence"],
                             "detail": "manifest present, zero accept events"})

    if observed_launches and not notes:
        failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                         "detail": "{} launches observed, 0 note events".format(observed_launches)})
    if routed and not observed_launches:
        # The inverse gap, and the one a late `start` produces: decisions were recorded
        # but no launch falls inside the measurement window. Reported, never back-dated.
        failures.append({"code": "instrumentation-incomplete", "evidence": "observed",
                         "detail": "{} delegating note(s) but 0 launches inside the run "
                                   "window — `start` likely ran after the dispatch"
                                   .format(len(routed))})
    if counters["writeback_rejected"]:
        failures.append({"code": "writeback-rejected", "evidence": "observed",
                         "detail": "{} rejection marker(s) in tool results".format(
                             counters["writeback_rejected"])})

    # --- same-model-verifier: only when BOTH identities were logged.
    builders = {n.get("model") for n in notes if n.get("role") == "builder" and n.get("model")}
    for n in notes:
        if n.get("role") == "verifier" and n.get("model") and n["model"] in builders:
            failures.append({"code": "same-model-verifier", "evidence": "manual",
                             "detail": "verifier model {} also logged as builder".format(n["model"])})

    # --- absorbed-lane-without-estimate: ALWAYS manual in v0.4. The lane IDENTITY is
    #     lead-supplied and cannot be corroborated from a tool_result, so no chain of
    #     transcript evidence can promote this to observed. Kept as an owner-judgment
    #     signal only. (`counters["lane_failures"]` still records transcript-visible
    #     failures; nothing derives an evidence tag from them.)
    for n in notes:
        lane = n.get("repairs")
        if not lane:
            continue
        nt = _parse_iso(n.get("at"))
        prior = [m for m in notes if m.get("lane_id") == lane
                 and m.get("estimate") is not None
                 and (nt is None or (_parse_iso(m.get("at")) or nt) <= nt)]
        if not prior:
            failures.append({
                "code": "absorbed-lane-without-estimate", "evidence": "manual",
                "detail": "repair of lane {} with no prior estimate (lane identity is "
                          "lead-declared; owner judgment)".format(lane)})

    for ev in events:
        if ev.get("kind") == "note" and ev.get("failure"):
            failures.append({"code": ev["failure"], "evidence": "manual",
                             "detail": ev.get("detail") or ev.get("summary") or ""})

    for err in sentinel.get("collector_errors", []):
        failures.append({"code": "collector-error", "evidence": "observed", "detail": err})

    return {
        "run_id": sentinel.get("run_id"),
        "session_id": sentinel.get("session_id"),
        "run_dir": run_dir,
        "started_at": sentinel.get("started_at"),
        "collected_at": now_iso(),
        "complete": sentinel.get("complete", False),
        "stance_version": tag(sentinel.get("stance_version"), "manual"),
        "objective_summary": tag(sentinel.get("objective_summary"), "manual")
        if sentinel.get("objective_summary") else unknown(),
        "objective_sha256": tag(sentinel.get("objective_sha256"), "manual")
        if sentinel.get("objective_sha256") else unknown(),
        "delegations": {
            "subagent": tval(counters["dispatch_subagent"], scoped),
            "codex_lane": tval(counters["dispatch_codex_lane"], scoped),
            # a sub-orchestrator is not identifiable from a launch alone (Astra §1)
            "suborch": tag(sum(1 for n in notes if n.get("route") == "suborch"), "manual")
            if notes else unknown(),
            "direct_decisions": tag(sum(1 for n in notes if n.get("route") == "direct"), "manual")
            if notes else unknown(),
        },
        # THREE separate transport measurements. Never summed with each other, and
        # never with lane_briefs below — unlike units, unlike evidence classes (Astra §1).
        "brief_bytes": tval(counters["brief_bytes"], scoped),
        # B3: bytes for launches still outstanding have not been seen, so a total with
        # unreturned launches is a floor, not a measurement — tagged proxy, with the
        # outstanding count beside it.
        "return_bytes": tval(counters["return_bytes"],
                             "proxy" if counters["unreturned_launches"] else scoped),
        "unreturned_launches": tval(counters["unreturned_launches"], scoped),
        "wake_ups": tval(counters["wake_ups"], "proxy"),
        # codex lanes leave only a Bash pointer in the stream, so their brief size is
        # captured by `note --brief-file` AT LAUNCH TIME and stays lead-declared.
        "lane_briefs": tag({"count": len(lane_briefs),
                            "bytes": sum(n["brief_bytes"] for n in lane_briefs),
                            "lanes": [{"lane_id": n.get("lane_id"), "model": n.get("model"),
                                       "bytes": n["brief_bytes"],
                                       "sha256": n.get("brief_sha256")}
                                      for n in lane_briefs]}, "manual")
        if lane_briefs else unknown(),
        "lead_direct_edits": {
            "edit_write_tools": tval(counters["lead_edit_write"], scoped),
            "bash_mutations": tval(counters["lead_bash_mutations"], "proxy"),
        },
        "estimates": {
            "declared": tag(len(est_by_id), "manual"),
            "delegating_notes": tag(len(delegating), "manual"),
            "delegation_notes_without_estimate": tag(len(routed) - len(delegating), "manual"),
            "observed_launches": tval(observed_launches, scoped),
            "matched": tval(matched, "proxy"),
            # item 2: derived from note matching, not read off the transcript.
            "unmatched_launches": tval(unmatched_launches, "proxy"),
            "unmatched_notes": tag(unmatched_note_ids, "manual"),
            "coverage": coverage if tstate == "ok" else unknown(),
            "accuracy": tag(accuracy, "manual") if accuracy else unknown(),
        },
        "deliverables": deliverables,
        "lead_declared": tag(lead_declared, ev_tag or "manual") if manifest else unknown(),
        "failures": failures,
        "scope": scope,
        "collector": {
            "records_read": counters["records"],
            "parse_errors": counters["parse_errors"],
            "truncation_resets": counters.get("truncation_resets", 0),
            "transcript_state": tstate,
            "timed_out": bool(BUDGET.get("timed_out")),
            "transcript_offset": sentinel.get("cursor", {}).get("offset"),
        },
    }


def upsert_run_line(record):
    """One line per run_id; an update rewrites that run's line in place.

    Rewrite-of-one-line semantics (not append-per-collection) keeps runs.jsonl at one
    row per run so `review` never double-counts a run across Stop-hook invocations.
    """
    os.makedirs(STATE_DIR, exist_ok=True)
    # S5: two Stop hooks (or a hook and a manual call) can land together. Hold an
    # exclusive lock on a sidecar for the whole read-modify-replace so neither loses.
    lockfh = open(RUNS_JSONL + ".lock", "a+")
    got = False
    while True:
        try:
            fcntl.flock(lockfh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            got = True
            break
        except OSError:
            if over_budget() or BUDGET["deadline"] is None:
                break
            time.sleep(0.05)
    if not got:
        # item 5: write NOTHING rather than a torn line. The caller records the miss.
        lockfh.close()
        log_collector("lock timeout on runs.jsonl; no line written for {}".format(
            record.get("run_id")))
        return False
    lines, replaced = [], False
    if os.path.exists(RUNS_JSONL):
        with open(RUNS_JSONL, errors="replace") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    lines.append(line)
                    continue
                if obj.get("run_id") == record["run_id"]:
                    lines.append(json.dumps(record, sort_keys=True))
                    replaced = True
                else:
                    lines.append(line)
    if not replaced:
        lines.append(json.dumps(record, sort_keys=True))
    tmp = "{}.{}.tmp".format(RUNS_JSONL, os.getpid())      # S5: per-process temp name
    with open(tmp, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    os.replace(tmp, RUNS_JSONL)
    try:
        fcntl.flock(lockfh, fcntl.LOCK_UN)
    finally:
        lockfh.close()
    return True


def read_runs():
    out = []
    if not os.path.exists(RUNS_JSONL):
        return out
    with open(RUNS_JSONL, errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    return out


# ---------------------------------------------------------------------------- verbs
def cmd_start(a):
    session = a.session or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session:
        # item 4: a sentinel is keyed by session. Defaulting to "nosession" silently
        # merged every un-sessioned run into one bucket — under Codex, where the env var
        # does not exist, that was every run.
        print("posture: --session is required (no $CLAUDE_CODE_SESSION_ID in this "
              "environment); pass the session/run identifier explicitly", file=sys.stderr)
        return 2
    if not valid_session(session):                  # S15: it becomes a filename
        print("posture: refusing unsafe session id {!r} (want {})".format(
            session, SESSION_ID_RE.pattern), file=sys.stderr)
        return 2
    run_dir = os.path.abspath(os.path.expanduser(a.run_dir))
    objective = a.objective
    if a.objective_file:
        objective = open(os.path.expanduser(a.objective_file), errors="replace").read()
    sent = {
        "run_id": a.run_id or new_run_id(session),
        "session_id": session,
        "run_dir": run_dir,
        "stance_version": a.stance_version,
        # the ORIGINAL objective text, preserved for later manifest reconciliation
        "objective": objective,
        "objective_sha256": hashlib.sha256((objective or "").encode()).hexdigest()
        if objective else None,
        "objective_summary": (objective or "").strip().splitlines()[0][:200]
        if objective else None,
        "transcript_path": os.path.expanduser(a.transcript) if a.transcript else None,
        "started_at": now_iso(),
        "last_activity": now_iso(),
        "last_collect_at": None,
        "complete": False,
        "cursor": blank_cursor(),
        "counters": blank_counters(),
        "collector_errors": [],
    }
    # Scope the run NOW: everything already in the transcript is pre-run history.
    tp = sent["transcript_path"]
    if tp and os.path.exists(tp):
        sent["cursor"]["offset"] = os.path.getsize(tp)
        sent["scope"] = {"mode": "offset-at-start", "start_offset": sent["cursor"]["offset"],
                         "evidence": "observed"}
    else:
        sent["scope"] = {"mode": "deferred", "start_offset": None, "evidence": "unknown"}
    os.makedirs(run_dir, exist_ok=True)
    write_json(sentinel_path(session), sent)
    append_event(run_dir, {"kind": "start", "run_id": sent["run_id"],
                           "session_id": session, "stance_version": a.stance_version})
    # S5: note/accept read this to stamp themselves, so a reused run dir keeps runs apart
    write_json(os.path.join(run_dir, ".posture", "current_run.json"),
               {"run_id": sent["run_id"], "session_id": session})
    print("posture: run {} started (session {}, run-dir {})".format(
        sent["run_id"], session, run_dir))
    return 0


def _touch_sentinel(session):
    p = sentinel_path(session) if valid_session(session) else None
    if p and os.path.exists(p):
        s = read_json(p)
        if s:
            s["last_activity"] = now_iso()
            write_json(p, s)


def cmd_note(a):
    run_dir = os.path.abspath(os.path.expanduser(a.run_dir))
    ev = {"kind": "note", "id": a.id, "route": a.route, "summary": a.summary,
          "estimate": a.estimate, "actual": a.actual, "unit": a.unit,
          "model": a.model, "role": a.role, "lane_id": a.lane_id,
          "repairs": a.repairs, "failure": a.failure, "detail": a.detail}
    if a.brief_file:
        bf = os.path.expanduser(a.brief_file)
        # Captured at LAUNCH time: reading the brief at Stop risks measuring a later
        # revision, and a Bash pointer is not the brief (Astra §1).
        ev["brief_bytes"] = os.path.getsize(bf)
        ev["brief_sha256"] = sha256_file(bf)
        ev["brief_path"] = os.path.abspath(bf)
    if a.failure and a.failure not in MANUAL_FAILURE_CODES:
        print("posture: unknown --failure code {!r} (allowed: {})".format(
            a.failure, ", ".join(sorted(MANUAL_FAILURE_CODES))), file=sys.stderr)
        return 2
    append_event(run_dir, {k: v for k, v in ev.items() if v is not None})
    _touch_sentinel(a.session or os.environ.get("CLAUDE_CODE_SESSION_ID"))
    if a.verbose:
        print("posture: noted {} ({})".format(a.id, a.route))
    return 0


def cmd_accept(a):
    run_dir = os.path.abspath(os.path.expanduser(a.run_dir))
    ev = {"kind": "accept", "deliverable": a.deliverable, "result": a.result,
          "check": a.check, "evidence": a.evidence, "lane_id": a.lane_id}
    append_event(run_dir, {k: v for k, v in ev.items() if v is not None})
    _touch_sentinel(a.session or os.environ.get("CLAUDE_CODE_SESSION_ID"))
    if a.verbose:
        print("posture: accept {} = {}".format(a.deliverable, a.result))
    return 0


def sweep_sentinels():
    """Item 8: retirement is checked for EVERY session on every collector invocation —
    an idle session never runs the collector again, so its own sentinel would never
    retire. Open runs go at 24 h, completed ones at the next invocation past 1 h."""
    try:
        names = os.listdir(STATE_DIR)
    except OSError:
        return
    now = time.time()
    for name in names:
        if not (name.startswith("sentinel-") and name.endswith(".json")):
            continue
        p = os.path.join(STATE_DIR, name)
        try:
            age = now - os.path.getmtime(p)
            done = bool((read_json(p) or {}).get("complete"))
            if age > (COMPLETE_MAX_AGE_SECONDS if done else SENTINEL_MAX_AGE_SECONDS):
                os.remove(p)
        except OSError:
            continue


def cmd_ledger(a):
    """Stop-hook collector. Bounded, silent, observational, idempotent.

    NEVER executes a manifest check command; existence is established by inspection.
    """
    session, transcript, stop_active = a.session, a.transcript, False
    if a.hook:
        a.verbose = False                           # the hook path is silent, always
        try:
            payload = json.loads(sys.stdin.read() or "{}")
        except ValueError:
            return 0
        session = session or payload.get("session_id")
        transcript = transcript or payload.get("transcript_path")
        stop_active = bool(payload.get("stop_hook_active"))
    session = session or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not valid_session(session):                  # S15
        return 0
    # B4: arm ONE deadline for everything that follows.
    budget_start(STOP_DEADLINE_SECONDS if a.hook else None)
    sweep_sentinels()
    sp = sentinel_path(session)
    sent = read_json(sp)
    if not sent:
        return 0                                    # no sentinel: not an instrumented run
    if a.hook and stop_active:
        return 0                                    # already re-entered; do nothing

    # age-out: an idle sentinel is retired rather than collected forever
    try:
        age = time.time() - os.path.getmtime(sp)
    except OSError:
        age = 0
    # S6: a completed run stops collecting (sweep_sentinels above handles retirement).
    if sent.get("complete") and not a.complete:
        return 0                                    # no-op: sentinel mtime untouched

    if a.hook and sent.get("last_collect_at"):
        try:
            last = datetime.datetime.fromisoformat(sent["last_collect_at"]).timestamp()
            if time.time() - last < DEBOUNCE_SECONDS:
                return 0                            # debounced
        except ValueError:
            pass

    # item 7: the Stop hook is the only caller that knows the transcript path. Persist
    # it so a later manual `ledger --complete` (no hook payload) can still find it.
    if transcript and not sent.get("transcript_path"):
        sent["transcript_path"] = os.path.expanduser(transcript)
    transcript = transcript or sent.get("transcript_path")
    # B3: classify the transcript BEFORE counting anything. "missing"/"unreadable"/
    # "none" all mean the transcript-derived fields have no value — not a zero.
    tpath = os.path.expanduser(transcript) if transcript else None
    if not tpath:
        sent["transcript_state"] = "none"
    elif not os.path.exists(tpath):
        sent["transcript_state"] = "missing"
    elif not os.access(tpath, os.R_OK):
        sent["transcript_state"] = "unreadable"
    else:
        sent["transcript_state"] = transcript_shape(tpath)      # ok | unsupported
    # Scope resolution: a run that could not scope itself at `start` (transcript unknown
    # then) resolves its boundary from the first record at/after started_at. Without
    # this, the collector reports the whole transcript — pre-rewind branches and all
    # earlier work in the session — as this run's own activity.
    if "scope" not in sent:
        # Sentinel predates run-scoping: its counters cover the whole transcript, so
        # they are not this run's. Discard them and recollect from the boundary.
        sent["counters"], sent["cursor"] = blank_counters(), blank_cursor()
    scope = sent.get("scope") or {"mode": "deferred", "start_offset": None,
                                  "evidence": "unknown"}
    if scope.get("start_offset") is None and sent["transcript_state"] == "ok":
        off, ev = resolve_start_offset(tpath, sent.get("started_at"))
        scope = {"mode": "offset-resolved-by-timestamp", "start_offset": off,
                 "evidence": ev}
        if (sent.get("cursor") or {}).get("offset", 0) < off:
            sent.setdefault("cursor", blank_cursor())["offset"] = off
    sent["scope"] = scope
    counters = sent.get("counters") or blank_counters()
    for k, v in blank_counters().items():           # forward-compatible field adds
        counters.setdefault(k, v)
    cursor = sent.get("cursor") or blank_cursor()
    consumed, reached_eof = 0, True
    try:
        if sent["transcript_state"] == "ok":
            # item 6: `--complete` must see the whole run, so loop the capped scan until
            # it drains. Under --hook the shared deadline still bounds it; a manual call
            # has no deadline and runs to EOF.
            while True:
                got = scan_stream(tpath, counters, cursor, a.max_bytes, a.max_seconds)
                consumed += got
                if not got or not a.complete:
                    break
                if over_budget():
                    break
            if a.complete:
                reached_eof = cursor.get("offset", 0) >= os.path.getsize(tpath)
    except Exception as exc:                        # collector never raises into the hook
        msg = "{}: {}".format(type(exc).__name__, exc)
        sent.setdefault("collector_errors", []).append(msg)
        log_collector("scan error for {}: {}".format(sent.get("run_id"), msg))
        reached_eof = False

    sent["counters"], sent["cursor"] = counters, cursor
    completion_pending = bool(a.complete and not reached_eof)
    sent["completion_pending"] = completion_pending
    if consumed or a.complete or not sent.get("last_collect_at"):
        sent["last_collect_at"] = now_iso()

    run_dir = sent.get("run_dir") or ""
    manifest, unparsed = read_manifest(run_dir)
    record = build_ledger(dict(sent, complete=bool(sent.get("complete")) or
                               (a.complete and reached_eof)),
                          counters, read_events(run_dir, sent.get("run_id")),
                          manifest, unparsed)
    if completion_pending:
        record["failures"].append(
            {"code": "instrumentation-incomplete", "evidence": "observed",
             "detail": "--complete could not scan to EOF; run NOT marked complete "
                       "(completion_pending)"})
        record["completion_pending"] = True
    prev = {r["run_id"]: r for r in read_runs()}.get(record["run_id"])
    if prev:
        # keep the line byte-stable when nothing observable changed
        a_cmp = dict(prev); b_cmp = dict(record)
        a_cmp.pop("collected_at", None); b_cmp.pop("collected_at", None)
        if a_cmp == b_cmp:
            record["collected_at"] = prev["collected_at"]
    written = upsert_run_line(record)
    if not written:
        # item 5: no line written -> nothing is persisted, and the sentinel keeps its
        # previous state so the next collection retries cleanly.
        log_collector("no ledger line written for {} (lock timeout)".format(
            record.get("run_id")))
        return 0
    # item 6: complete is persisted only AFTER the line lands.
    if a.complete and reached_eof:
        sent["complete"] = True
    prior = read_json(sp)
    if prior != sent:                               # item 8: no-op collections do not
        write_json(sp, sent)                        # touch the sentinel (or its mtime)
    if a.verbose:
        print(json.dumps(record, indent=2, sort_keys=True))
    return 0


# ---------------------------------------------------------------------------- review
def _fail_codes(run, evidence=None):
    return sorted({f["code"] for f in run.get("failures", [])
                   if evidence is None or f.get("evidence") == evidence})


def _eligible(run):
    """Item 1: what SKILL.md promises. A run feeds recurrence only when it finished,
    its instrumentation held, and its collection was not cut short. Anything else is a
    partial observation and cannot supply either a hit or a counterexample."""
    return (bool(run.get("complete"))
            and "instrumentation-incomplete" not in _fail_codes(run)
            and not (run.get("collector") or {}).get("timed_out"))


def cmd_review(a):
    runs = read_runs()[-a.limit:]
    out = ["orchestrator-posture ledger — {} run(s)".format(len(runs)), DISCLAIMER, ""]
    if not runs:
        out.append("(no runs recorded)")
        print("\n".join(out))
        return 0
    out.append("| run | stance | sub/lane | brief B | ret B | wake | edits | deliv m/p | failures |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    body_cap = 40 - len(out) - 8            # reserve lines for the recurrence section
    for r in runs[-max(body_cap, 1):]:
        d = r.get("deliverables") or {}
        dv = d.get("value") if isinstance(d, dict) else None
        deliv = "?" if not isinstance(dv, dict) else "{}/{}".format(
            dv.get("missing", 0) + dv.get("wrong_path", 0), dv.get("present", 0))
        out.append("| {}{} | {} | {}/{} | {} | {} | {} | {} | {} | {} |".format(
            "" if _eligible(r) else "inel ",
            (r.get("run_id") or "?")[-15:], _v(r.get("stance_version")),
            _v(r["delegations"]["subagent"]), _v(r["delegations"]["codex_lane"]),
            _v(r.get("brief_bytes")), _v(r.get("return_bytes")), _v(r.get("wake_ups")),
            _v(r.get("lead_direct_edits", {}).get("edit_write_tools")),
            deliv, ", ".join(_fail_codes(r)) or "—"))

    elig = [r for r in runs if _eligible(r)]
    eligible = len(elig)
    counts, soft = {}, {}
    for r in elig:
        # item 4: only an OBSERVED failure can drive recurrence. Manual and proxy
        # findings are owner judgment and are listed, never counted or investigated.
        for c in _fail_codes(r, "observed"):
            counts.setdefault(c, []).append(r.get("run_id"))
        for c in _fail_codes(r):
            if c not in _fail_codes(r, "observed"):
                soft.setdefault(c, []).append(r.get("run_id"))
    out.append("")
    out.append("Recurrence over {} eligible of {} listed run(s), observed failures only "
               "(eligible = complete, no instrumentation-incomplete, not timed out; "
               "`inel` rows are listed but never counted):".format(eligible, len(runs)))
    recurring = []
    for code, ids in sorted(counts.items(), key=lambda kv: -len(kv[1]))[:5]:
        counter = [r.get("run_id") for r in elig if code not in _fail_codes(r, "observed")]
        out.append("  {}: {}/{} runs; counterexamples: {}".format(
            code, len(ids), eligible,
            ", ".join(x[-15:] for x in counter[:3]) or "none"))
        if len(ids) >= a.min_runs:
            recurring.append((code, ids, counter))
    if not counts:
        out.append("  (none)")
    if soft:
        out.append("  manual/proxy (owner judgment, never counted): " + ", ".join(
            "{} x{}".format(c, len(v)) for c, v in sorted(soft.items())))

    if a.stage_investigation and recurring:
        path = stage_investigation(recurring, eligible)
        out.append("")
        out.append("Staged for OWNER ratification (not applied): {}".format(path))
    print("\n".join(out[:40]))
    return 0


def _v(field):
    if not isinstance(field, dict):
        return "?"
    return "?" if field.get("evidence") == "unknown" else str(field.get("value"))


INVESTIGATION_TMPL = """# INVESTIGATION draft — {date}

{disclaimer}

Status: DRAFT. A stance edit requires OWNER ratification; nothing here is applied.

## Recurrence ({eligible} eligible runs)

| failure code | distinct affected runs | counterexample runs |
|---|---|---|
{rows}

## What a review lane must establish before any stance edit is proposed

1. Whether the affected runs share a cause other than the stance (task mix, model,
   instrumentation coverage, harness layout).
2. Why the counterexample runs did not hit the code under the same stance.
3. Whether the evidence for each occurrence is observed, proxy or lead-declared
   (see the `evidence` tag on each ledger failure entry).

## Read-only review lane (run by the owner or the conductor; this script never runs it)

```bash
codex exec --sandbox read-only \\
  "Read {runs_jsonl} and this draft at {self_path}. For each recurring failure code,
   state what the ledger evidence does and does not establish, list the confounders,
   and propose AT MOST one candidate stance.md edit with the counterexamples that
   would falsify it. Make no causal claim. Output a review only; change no files."
```
"""


def stage_investigation(recurring, eligible):
    os.makedirs(INVEST_DIR, exist_ok=True)
    date = time.strftime("%Y-%m-%d")
    path = os.path.join(INVEST_DIR, "INVESTIGATION-{}.md".format(date))
    rows = "\n".join("| {} | {} | {} |".format(
        code, len(ids), ", ".join(c[-15:] for c in counter[:3]) or "none")
        for code, ids, counter in recurring)
    with open(path, "w") as fh:
        fh.write(INVESTIGATION_TMPL.format(
            date=date, disclaimer=DISCLAIMER, eligible=eligible, rows=rows,
            runs_jsonl=RUNS_JSONL, self_path=path))
    return path


# ----------------------------------------------------------------------------- check
FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
PILOT_ROOT_DEFAULT = ""


def _scan_fresh(path):
    c, cur = blank_counters(), blank_cursor()
    scan_stream(path, c, cur)
    return c, cur


def cmd_check(a):
    failures, ran = [], 0
    syn_ran = man_ran = led_ran = rev_ran = 0

    # 1) synthetic fixtures
    syn = os.path.join(FIXTURES, "synthetic")
    for name in sorted(os.listdir(syn)) if os.path.isdir(syn) else []:
        if not name.endswith(".jsonl"):
            continue
        stream = os.path.join(syn, name)
        exp = read_json(stream[:-6] + ".expected.json") or {}
        ran += 1; syn_ran += 1
        if exp.get("scope_started_at"):
            # run-scoping regression: only records at/after the run's start may count
            off, ev = resolve_start_offset(stream, exp["scope_started_at"])
            counters, cursor = blank_counters(), blank_cursor()
            cursor["offset"] = off
            scan_stream(stream, counters, cursor)
            if ev != "observed":
                failures.append("synthetic/{}: start boundary not resolvable "
                                "(evidence {})".format(name, ev))
            if off <= 0:
                failures.append("synthetic/{}: start offset resolved to {} — the whole "
                                "transcript would be counted".format(name, off))
        else:
            counters, cursor = _scan_fresh(stream)
        for k, want in (exp.get("expect") or {}).items():
            got = counters.get(k)
            if got != want:
                failures.append("synthetic/{}: {} expected {!r}, got {!r}".format(
                    name, k, want, got))
        if exp.get("expect_transcript_shape"):
            got_shape = transcript_shape(stream)
            if got_shape != exp["expect_transcript_shape"]:
                failures.append("synthetic/{}: transcript_shape expected {!r}, got {!r}"
                                .format(name, exp["expect_transcript_shape"], got_shape))
        if exp.get("partial_tail"):
            if cursor["offset"] >= os.path.getsize(stream):
                failures.append("synthetic/{}: expected offset < file size (truncated "
                                "final line must stay unread), got {}".format(
                                    name, cursor["offset"]))
        for dotted, want in (exp.get("expect_ledger") or {}).items():
            budget_start(None)
            rec = build_ledger({"run_id": "fx", "run_dir": syn, "stance_version": "0.4",
                                "scope": {"mode": "offset-at-start", "evidence": "observed"}},
                               counters, [], None, [])
            got = rec
            for part in dotted.split("."):
                got = (got or {}).get(part) if isinstance(got, dict) else None
            if got != want:
                failures.append("synthetic/{}: ledger {} expected {!r}, got {!r}".format(
                    name, dotted, want, got))
        if exp.get("rescan_delta_zero"):
            before = dict(counters)
            scan_stream(stream, counters, cursor)
            if {k: v for k, v in counters.items() if k != "dispatch_models"} != \
               {k: v for k, v in before.items() if k != "dispatch_models"}:
                failures.append("synthetic/{}: re-scan changed counters (not idempotent)"
                                .format(name))

    # 2) ledger fixtures: a synthetic sentinel + counters + events + files on disk,
    #    asserted with dotted paths against the assembled runs.jsonl record. This is
    #    where evidence TAGS are pinned, not just counts.
    led = os.path.join(FIXTURES, "ledger")
    for name in sorted(os.listdir(led)) if os.path.isdir(led) else []:
        if not name.endswith(".json"):
            continue
        fx = read_json(os.path.join(led, name)) or {}
        ran += 1; led_ran += 1
        with tempfile.TemporaryDirectory(prefix="posture-check-") as rd:
            for rel, body in (fx.get("files") or {}).items():
                full = os.path.join(rd, rel)
                os.makedirs(os.path.dirname(full), exist_ok=True)
                open(full, "w").write(body)
            if fx.get("manifest_md") is not None:
                open(os.path.join(rd, "DELIVERABLES.md"), "w").write(fx["manifest_md"])
            counters = blank_counters()
            counters.update(fx.get("counters") or {})
            sentinel = {"run_id": "fx", "run_dir": rd, "stance_version": "0.4",
                        "scope": {"mode": "offset-at-start", "evidence": "observed"}}
            sentinel.update(fx.get("sentinel") or {})
            # a fixture may arm an already-expired deadline to exercise the partial paths
            budget_start(fx.get("budget_seconds"))
            mf, unp = read_manifest(rd)
            if fx.get("events_jsonl") is not None:
                # exercise the real reader (and its parse-error counter), not a list
                os.makedirs(os.path.join(rd, ".posture"), exist_ok=True)
                with open(events_path(rd), "w") as fh:
                    fh.write(fx["events_jsonl"])
                evs = read_events(rd)
            else:
                EVENT_PARSE_ERRORS["n"] = 0
                evs = fx.get("events") or []
            rec = build_ledger(sentinel, counters, evs, mf, unp)
            if fx.get("expect_eligible") is not None and _eligible(rec) != fx["expect_eligible"]:
                failures.append("ledger/{}: eligible expected {}, got {}".format(
                    name, fx["expect_eligible"], _eligible(rec)))
            for dotted, want in (fx.get("expect") or {}).items():
                got = rec
                for part in dotted.split("."):
                    got = (got or {}).get(part) if isinstance(got, dict) else None
                if got != want:
                    failures.append("ledger/{}: {} expected {!r}, got {!r}".format(
                        name, dotted, want, got))
            for code in fx.get("expect_failure_codes") or []:
                hits = [f for f in rec["failures"] if f["code"] == code]
                if not hits:
                    failures.append("ledger/{}: expected failure {!r}, got {}".format(
                        name, code, sorted({f["code"] for f in rec["failures"]}) or "none"))
                elif fx.get("expect_failure_evidence", {}).get(code) and \
                        hits[0]["evidence"] != fx["expect_failure_evidence"][code]:
                    failures.append("ledger/{}: failure {} evidence expected {!r}, got {!r}"
                                    .format(name, code, fx["expect_failure_evidence"][code],
                                            hits[0]["evidence"]))
            for code in fx.get("expect_no_failure_codes") or []:
                if any(f["code"] == code for f in rec["failures"]):
                    failures.append("ledger/{}: failure {!r} present but must not be"
                                    .format(name, code))

    # 3) manifest-form fixtures (bullet, pipe table, and a manifest that parses to zero)
    man = os.path.join(FIXTURES, "manifests")
    for name in sorted(os.listdir(man)) if os.path.isdir(man) else []:
        if not name.endswith(".md"):
            continue
        exp = read_json(os.path.join(man, name[:-3] + ".expected.json")) or {}
        ran += 1; man_ran += 1
        tmpctx = tempfile.TemporaryDirectory(prefix="posture-check-")
        tmpdir = tmpctx.name
        with open(os.path.join(tmpdir, "DELIVERABLES.md"), "w") as fh:
            fh.write(open(os.path.join(man, name), errors="replace").read())
        items, unparsed_rows = read_manifest(tmpdir)
        if exp.get("expect_entries") is not None and len(items) != exp["expect_entries"]:
            failures.append("manifest/{}: expected {} entries, parsed {}".format(
                name, exp["expect_entries"], len(items)))
        paths = [i["path"] for i in items]
        for want in exp.get("expect_paths_contain") or []:
            if want not in paths:
                failures.append("manifest/{}: path {!r} not parsed".format(name, want))
        bad = exp.get("expect_no_path_starting")
        if bad and any(p.startswith(bad) for p in paths):
            failures.append("manifest/{}: a check command was parsed as a path "
                            "(starts with {!r})".format(name, bad))
        # the empty-manifest case must reach `unknown` + instrumentation-incomplete
        budget_start(None)
        rec = build_ledger({"run_id": "fx", "run_dir": tmpdir, "stance_version": "0.4",
                            "complete": True,
                            "scope": {"mode": "offset-at-start", "evidence": "observed"}},
                           blank_counters(), [], items, unparsed_rows)
        want_ev = exp.get("expect_deliverables_evidence")
        if want_ev and rec["deliverables"]["evidence"] != want_ev:
            failures.append("manifest/{}: deliverables evidence expected {!r}, got {!r}"
                            .format(name, want_ev, rec["deliverables"]["evidence"]))
        want_fail = exp.get("expect_failure_code")
        if want_fail and want_fail not in {f["code"] for f in rec["failures"]}:
            failures.append("manifest/{}: expected failure {!r}, got {}".format(
                name, want_fail, sorted({f["code"] for f in rec["failures"]}) or "none"))
        tmpctx.cleanup()

    # 3b) review-eligibility fixtures: a list of prebuilt run records -> the recurrence
    #     section, asserting which runs feed it.
    rev = os.path.join(FIXTURES, "review")
    for name in sorted(os.listdir(rev)) if os.path.isdir(rev) else []:
        if not name.endswith(".json"):
            continue
        fx = read_json(os.path.join(rev, name)) or {}
        ran += 1; rev_ran += 1
        got = sorted(r["run_id"] for r in fx["runs"] if _eligible(r))
        want = sorted(fx.get("expect_eligible") or [])
        if got != want:
            failures.append("review/{}: eligible runs expected {}, got {}".format(
                name, want, got))
        if fx.get("expect_recurrence_codes") is not None:
            # item 4: recurrence is fed by OBSERVED failures of eligible runs only
            rec = sorted({c for r in fx["runs"] if _eligible(r)
                          for c in _fail_codes(r, "observed")})
            if rec != sorted(fx["expect_recurrence_codes"]):
                failures.append("review/{}: recurrence codes expected {}, got {}".format(
                    name, sorted(fx["expect_recurrence_codes"]), rec))

    # 4) pilot regression streams
    pilot = read_json(os.path.join(FIXTURES, "pilot.json")) or {}
    root = os.path.expanduser(a.pilot_root or pilot.get("root") or PILOT_ROOT_DEFAULT)
    pilot_ran, pilot_skipped = 0, []
    for rel, spec in sorted((pilot.get("runs") or {}).items()):
        stream = os.path.join(root, rel, "claude.stream.jsonl")
        if not os.path.exists(stream):
            pilot_skipped.append(rel)
            continue
        pilot_ran += 1
        ran += 1
        counters, _ = _scan_fresh(stream)
        for k, want in (spec.get("expect") or {}).items():
            got = counters.get(k)
            if got != want:
                failures.append("pilot/{}: {} expected {!r}, got {!r}".format(
                    rel, k, want, got))
        label = spec.get("deliverable_label")
        dp = spec.get("deliverable_path")
        if label in ("delivered", "lost") and dp:
            exists = os.path.exists(os.path.join(root, rel, dp))
            if (label == "delivered") != exists:
                failures.append("pilot/{}: label {} contradicts inspection of {} "
                                "(exists={})".format(rel, label, dp, exists))

    print("posture check: {} fixture(s) — {} synthetic stream(s), {} ledger case(s), "
          "{} manifest form(s), {} review case(s), {} pilot stream(s){}".format(
        ran, syn_ran, led_ran, man_ran, rev_ran, pilot_ran,
        "; skipped (stream absent): " + ", ".join(pilot_skipped) if pilot_skipped else ""))
    expected_pilot = len(pilot.get("runs") or {})
    if pilot_ran < expected_pilot and not a.allow_missing_pilot:
        failures.append("pilot corpus incomplete: {} of {} streams found under {} "
                        "(pass --allow-missing-pilot to accept a short corpus)".format(
                            pilot_ran, expected_pilot, root))
    unknown_labels = [k for k, v in (pilot.get("runs") or {}).items()
                      if v.get("deliverable_label") == "unknown"]
    if unknown_labels:
        print("  labels not established (recorded as unknown): " + ", ".join(sorted(unknown_labels)))
    if failures:
        print("\nFAIL ({} mismatch(es)):".format(len(failures)))
        for f in failures:
            print("  - " + f)
        return 1
    print("  all expectations matched")
    return 0


# ------------------------------------------------------------------------------ cli
def build_parser():
    p = argparse.ArgumentParser(
        prog="posture_run.py",
        description="orchestrator-posture v0.4 instrumentation (descriptive recorder).")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("start", help="open a run: write the sentinel + preserve the objective")
    s.add_argument("--run-dir", required=True)
    s.add_argument("--session", help="session id (default $CLAUDE_CODE_SESSION_ID)")
    s.add_argument("--run-id")
    s.add_argument("--objective", help="original objective text")
    s.add_argument("--objective-file", help="file holding the original objective text")
    s.add_argument("--stance-version", default=STANCE_VERSION_DEFAULT)
    s.add_argument("--transcript", help="transcript path to collect from (else the hook supplies it)")
    s.set_defaults(fn=cmd_start)

    n = sub.add_parser("note", help="record ONE delegation decision BEFORE dispatch (append-only)")
    n.add_argument("--run-dir", required=True)
    n.add_argument("--id", required=True, help="decision id, reused to attach --actual later")
    n.add_argument("--route", choices=["direct", "subagent", "suborch"], required=True)
    n.add_argument("--estimate", type=int, help="pre-dispatch context-cost estimate")
    n.add_argument("--actual", type=int, help="observed cost for an earlier --id (append-only)")
    n.add_argument("--unit", default="tokens")
    n.add_argument("--summary")
    n.add_argument("--model", help="resolved model identity")
    n.add_argument("--role", choices=["builder", "verifier"])
    n.add_argument("--lane-id", help="codex lane id")
    n.add_argument("--brief-file", help="brief file — bytes+sha256 captured NOW, at launch time")
    n.add_argument("--repairs", help="lane id this direct decision repairs")
    n.add_argument("--failure", help="manual failure code: " + ", ".join(sorted(MANUAL_FAILURE_CODES)))
    n.add_argument("--detail")
    n.add_argument("--session")
    n.add_argument("--verbose", action="store_true")
    n.set_defaults(fn=cmd_note)

    c = sub.add_parser("accept", help="record a deliverable's check result at the delivery gate")
    c.add_argument("--run-dir", required=True)
    c.add_argument("--deliverable", required=True, help="path exactly as written in DELIVERABLES.md")
    c.add_argument("--result", choices=["pass", "fail", "unchanged"], required=True)
    c.add_argument("--check", help="the check command that was run (recorded, not re-run)")
    c.add_argument("--evidence")
    c.add_argument("--lane-id")
    c.add_argument("--session")
    c.add_argument("--verbose", action="store_true")
    c.set_defaults(fn=cmd_accept)

    l = sub.add_parser("ledger", help="collect one run line (bounded, silent, idempotent)")
    l.add_argument("--hook", action="store_true", help="read Stop-hook JSON from stdin")
    l.add_argument("--session")
    l.add_argument("--transcript", help="override the transcript/stream to read")
    l.add_argument("--complete", action="store_true", help="mark the run complete")
    l.add_argument("--max-bytes", type=int, default=MAX_BYTES_DEFAULT)
    l.add_argument("--max-seconds", type=float, default=MAX_SECONDS_DEFAULT)
    l.add_argument("--verbose", action="store_true", help="print the run record (default: silent)")
    l.set_defaults(fn=cmd_ledger)

    r = sub.add_parser("review", help="render a capped cross-run table (no causal claims)")
    r.add_argument("--limit", type=int, default=20)
    r.add_argument("--min-runs", type=int, default=3,
                   help="distinct affected runs before an INVESTIGATION draft is eligible")
    r.add_argument("--stage-investigation", action="store_true",
                   help="write a STAGED investigation draft for owner ratification")
    r.set_defaults(fn=cmd_review)

    k = sub.add_parser("check", help="self-test against labeled fixtures; non-zero on mismatch")
    k.add_argument("--pilot-root", help="override the pilot runs/ root")
    k.add_argument("--allow-missing-pilot", action="store_true",
                   help="do not fail when fewer pilot streams are present than labeled")
    k.set_defaults(fn=cmd_check)
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    if getattr(a, "hook", False):
        # Verified against 1194 recorded stop_hook_summary records in this project's
        # transcripts: a Stop hook that exits 0 with no output leaves hasOutput=false,
        # hookErrors=[] and hookAdditionalContext=[] — no next-turn surface. The error
        # path is unobserved in that corpus, so the collector never lets one happen:
        # every exception is swallowed and the exit code is always 0.
        try:
            a.fn(a)
        except Exception as exc:            # item 7: recorded, not silently discarded
            log_collector("unhandled {} in hook: {}".format(type(exc).__name__, exc))
        return 0
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
