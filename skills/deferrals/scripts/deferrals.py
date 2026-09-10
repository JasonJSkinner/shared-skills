#!/usr/bin/env python3
"""Deterministic v0.4 deferrals storage commands. Python stdlib only."""

import argparse
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
import tempfile


SCHEMA = "<!-- deferrals-schema: 0.4 -->"
ID_RE = re.compile(r"^ddf_[0-9a-f]{8}$")
RECORD_RE = re.compile(
    r"^- \[([ x-])\] \*\*(ddf_[0-9a-f]{8})\*\* — ([^\r\n]+)",
    re.MULTILINE,
)
SECTION_RE = re.compile(r"^## ([^\r\n]+)", re.MULTILINE)
AXES = ("impact", "opportunity", "confidence", "autonomy")
# Fields another verb owns; repair-body refuses to change any of them.
MANAGED = AXES + (
    "status", "threads", "created", "updated", "lane", "priority",
    "archive-generation", "record-hash", "companion", "not-before",
    "window-closes", "archived-at", "archive", "inactive_reason",
    "reactivate_when",
)
DERIVED = {
    "active": ("Active", " "),
    "inactive": ("Inactive", " "),
    "resolved": ("Terminal Tombstones", "x"),
    "closed": ("Terminal Tombstones", "-"),
}
LEGACY = {
    ("Open", " "): "active",
    ("Resolved", "x"): "resolved",
    ("Abandoned", "-"): "closed",
}


class DeferralError(Exception):
    pass


@dataclass
class Record:
    start: int
    end: int
    text: str
    section: str
    glyph: str
    ticket_id: str
    title: str


def read_exact(path):
    return path.read_bytes().decode("utf-8") if path.exists() else ""


def newline(text):
    return "\r\n" if "\r\n" in text else "\n"


def parse_records(text):
    starts = list(RECORD_RE.finditer(text))
    sections = list(SECTION_RE.finditer(text))
    records = []
    for index, match in enumerate(starts):
        following = [len(text)]
        if index + 1 < len(starts):
            following.append(starts[index + 1].start())
        following.extend(section.start() for section in sections if section.start() > match.start())
        end = min(following)
        section = ""
        for heading in sections:
            if heading.start() < match.start():
                section = heading.group(1)
            else:
                break
        records.append(Record(
            match.start(),
            end,
            text[match.start():end],
            section,
            match.group(1),
            match.group(2),
            match.group(3),
        ))
    return records


def get_field(record, key):
    exact = re.search(rf"^  - {re.escape(key)}:\s*([^\r\n]*)", record, re.MULTILINE)
    if exact:
        return exact.group(1).strip()
    embedded = re.search(rf"(?:^  - |\| ){re.escape(key)}:\s*([^|\r\n]+)", record, re.MULTILINE)
    return embedded.group(1).strip() if embedded else None


def set_field(record, key, value):
    pattern = re.compile(rf"^  - {re.escape(key)}:[^\r\n]*(?:\r?\n|$)", re.MULTILINE)
    line = f"  - {key}: {value}{newline(record)}"
    if pattern.search(record):
        return pattern.sub(line, record, count=1)
    split = record.find(newline(record))
    if split < 0:
        return record + newline(record) + line
    split += len(newline(record))
    return record[:split] + line + record[split:]


def set_metadata(record, key, value):
    """Write a single-value `key` without disturbing keys packed onto the same line.

    v0.3 records pack metadata onto one line ("  - lane: H | priority: important",
    "  - threads: t | created: d | lane: L"). set_field replaces whole lines, so
    writing one packed key through it silently deletes its siblings. Not for rating
    axes — those carry a paired `rated:` value and are written whole by set_rating.
    """
    dedicated = re.search(rf"^  - {re.escape(key)}:[ \t]*", record, re.MULTILINE)
    packed = re.search(rf"^  - [^\r\n]*\|[ \t]*{re.escape(key)}:[ \t]*", record, re.MULTILINE)
    match = dedicated or packed
    if not match:
        return set_field(record, key, value)
    rest = record[match.end():]
    stop = min(index for index in (rest.find("|"), rest.find("\n"), len(rest)) if index >= 0)
    old = rest[:stop]
    return record[:match.end()] + value + old[len(old.rstrip()):] + record[match.end() + stop:]


def set_title(record, title):
    return re.sub(
        r"^(- \[[ x-]\] \*\*ddf_[0-9a-f]{8}\*\* — )[^\r\n]*",
        lambda match: match.group(1) + title,
        record,
        count=1,
    )


def append_body(record, text):
    nl = newline(record)
    return finalize_record(record.rstrip("\r\n") + nl + "  - " + text.replace("\n", nl + "    "))


def remove_field(record, key):
    return re.sub(
        rf"^  - {re.escape(key)}:[^\r\n]*(?:\r?\n|$)",
        "",
        record,
        count=1,
        flags=re.MULTILINE,
    )


def append_event(record, key, payload):
    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    split = record.find(newline(record)) + len(newline(record))
    return record[:split] + f"  - {key}: {line}{newline(record)}" + record[split:]


def set_glyph(record, glyph):
    return re.sub(r"^- \[[ x-]\]", f"- [{glyph}]", record, count=1)


def finalize_record(record):
    nl = newline(record)
    return record.rstrip("\r\n") + nl + nl


def unhashed(record):
    return re.sub(
        r"^  - record-hash:[^\r\n]*(?:\r?\n|$)",
        "",
        record,
        count=1,
        flags=re.MULTILINE,
    )


def set_record_hash(record):
    base = unhashed(record)
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return set_field(base, "record-hash", f"sha256:{digest}")


def hash_valid(record):
    stored = get_field(record, "record-hash")
    if not stored or not stored.startswith("sha256:"):
        return None
    actual = hashlib.sha256(unhashed(record).encode("utf-8")).hexdigest()
    return stored == f"sha256:{actual}"


def record_status(record):
    explicit = get_field(record.text, "status")
    if explicit:
        return explicit
    return LEGACY.get((record.section, record.glyph))


def generation(record):
    value = get_field(record.text, "archive-generation")
    try:
        return int(value) if value is not None else 0
    except ValueError:
        return -1


def record_threads(record):
    value = get_field(record.text, "threads") or ""
    return [part.strip() for part in value.split(",") if part.strip()]


def add_thread(record, thread):
    match = re.search(r"(threads:\s*)([^|\r\n]+)", record)
    if match:
        threads = [part.strip() for part in match.group(2).split(",") if part.strip()]
        if thread in threads:
            return record
        value = ", ".join(threads + [thread])
        return record[:match.start(2)] + value + record[match.end(2):]
    return set_field(record, "threads", thread)


def set_rating(record, axis, value, rated):
    line = f"{value} | rated: {rated}"
    return set_field(record, axis, line)


def rating_dates(record):
    found = {}
    for axis in AXES:
        match = re.search(
            rf"^  - {axis}:\s*([1-5])\s*\|\s*rated:\s*(\d{{4}}-\d{{2}}-\d{{2}})",
            record,
            re.MULTILINE,
        )
        if match:
            found[axis] = match.group(2)
    legacy = re.search(
        r"impact:\s*([1-5])\s*·\s*opportunity:\s*([1-5])"
        r"(?:\s*\([^,\r\n]+,\s*(\d{4}-\d{2}-\d{2})\))?",
        record,
    )
    if legacy and legacy.group(3):
        found.setdefault("impact", legacy.group(3))
        found.setdefault("opportunity", legacy.group(3))
    return found


def ratings_stale(record):
    updated = get_field(record, "updated")
    dates = rating_dates(record)
    return bool(updated and any(updated > rated for rated in dates.values()))


def replace_record(text, old, new):
    return text[:old.start] + new + text[old.end:]


def remove_record(text, old):
    return text[:old.start] + text[old.end:]


def insert_record(text, section, record):
    nl = newline(text)
    record = finalize_record(record)
    heading = re.search(rf"^## {re.escape(section)}\s*$", text, re.MULTILINE)
    if not heading:
        text = text.rstrip("\r\n") + nl + nl + f"## {section}" + nl
        heading = re.search(rf"^## {re.escape(section)}\s*$", text, re.MULTILINE)
    next_heading = SECTION_RE.search(text, heading.end())
    position = next_heading.start() if next_heading else len(text)
    before = text[:position].rstrip("\r\n") + nl + nl
    after = text[position:].lstrip("\r\n")
    return before + record + after


def move_record(text, old, section, new):
    return insert_record(remove_record(text, old), section, new)


def new_document(key, archive=False):
    if archive:
        return f"# Deferrals Archive — {key}\n{SCHEMA}\n\n## Terminal Records\n"
    return (
        f"# Deferrals — {key}\n{SCHEMA}\n\n"
        "## Active\n\n## Inactive\n\n## Terminal Tombstones\n"
    )


def is_index(path):
    name = path.name
    if path.parent == path or name.startswith(".") or not path.is_file():
        return False
    if name == "global.md":
        return True
    return name.startswith("-") and name.endswith(".md") and not name.endswith(".archive.md")


def index_paths(root):
    return sorted(path for path in root.iterdir() if is_index(path)) if root.exists() else []


def key_from_path(path):
    return path.name[:-3]


def find_record(text, query):
    query = query if query.startswith("ddf_") else f"ddf_{query}"
    matches = [record for record in parse_records(text) if record.ticket_id.startswith(query)]
    if not matches:
        raise DeferralError(f"ticket not found: {query}")
    if len(matches) > 1:
        raise DeferralError(f"ambiguous ticket prefix: {query}")
    return matches[0]


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(text.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
        directory = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def durable_unlink(path):
    path.unlink()
    directory = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


class Project:
    def __init__(self, root, key):
        self.root = Path(root).expanduser()
        self.key = key
        self.active = self.root / f"{key}.md"
        self.archive = self.root / f"{key}.archive.md"

    @property
    def lock_path(self):
        return Path(str(self.active.resolve(strict=False)) + ".lock")

    @contextmanager
    def lock(self):
        self.root.mkdir(parents=True, exist_ok=True)
        lock_path = self.lock_path
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def validate_target(record):
    valid = hash_valid(record.text)
    if valid is not True:
        raise DeferralError(f"{record.ticket_id}: direct-edit drift; run doctor")


def make_tombstone(source, status, archive_name, archived_at, archive_generation):
    glyph = DERIVED[status][1]
    lines = [
        f"- [{glyph}] **{source.ticket_id}** — {source.title}",
        f"  - status: {status}",
        f"  - archived-at: {archived_at}",
        f"  - archive: {archive_name}",
        f"  - archive-generation: {archive_generation}",
    ]
    companion = get_field(source.text, "companion")
    if companion:
        lines.append(f"  - companion: {companion}")
    return set_record_hash(finalize_record("\n".join(lines)))


def archive_record(text, key, record):
    document = text or new_document(key, archive=True)
    existing = [item for item in parse_records(document) if item.ticket_id == RECORD_RE.match(record).group(2)]
    if existing:
        return replace_record(document, existing[0], record)
    return insert_record(document, "Terminal Records", record)


def validate_companion(name, ticket_id):
    if Path(name).name != name or not name.startswith(ticket_id + "-"):
        raise DeferralError("companion must be a root-relative basename matching the ticket ID")


def command_add(args):
    project = Project(args.root, args.project_key)
    ticket_id = args.ticket_id or f"ddf_{secrets.token_hex(4)}"
    if not ID_RE.fullmatch(ticket_id):
        raise DeferralError("--id must match ddf_<8 lowercase hex>")
    if args.companion:
        validate_companion(args.companion, ticket_id)
    with project.lock():
        text = read_exact(project.active)
        if text and SCHEMA not in text:
            raise DeferralError("legacy index requires migrate --apply before mutation")
        text = text or new_document(project.key)
        if any(record.ticket_id == ticket_id for record in parse_records(text)):
            raise DeferralError(f"duplicate ID: {ticket_id}")
        today = args.date or date.today().isoformat()
        lines = [
            f"- [ ] **{ticket_id}** — {args.title}",
            "  - status: active",
            f"  - threads: {args.thread}",
            f"  - created: {today} by {args.actor or args.thread}",
            f"  - updated: {today}",
            f"  - lane: {args.lane}",
            f"  - priority: {args.priority}",
            "  - archive-generation: 0",
        ]
        if args.companion:
            lines.append(f"  - companion: {args.companion}")
        if args.body:
            body = args.body.replace("\n", "\n    ")
            lines.append(f"  - **Background:** {body}")
        record = set_record_hash(finalize_record("\n".join(lines)))
        atomic_write(project.active, insert_record(text, "Active", record))
    print(ticket_id)
    return 0


def command_claim(args):
    project = Project(args.root, args.project_key)
    with project.lock():
        text = read_exact(project.active)
        record = find_record(text, args.ticket)
        validate_target(record)
        status = record_status(record)
        if status not in ("active", "inactive"):
            raise DeferralError(f"expected active or inactive, found {status}")
        changed = add_thread(record.text, args.thread)
        if changed == record.text:
            print(f"{record.ticket_id}: already claimed")
            return 0
        changed = set_record_hash(changed)
        atomic_write(project.active, replace_record(text, record, changed))
    print(f"{record.ticket_id}: claimed")
    return 0


def command_rate(args):
    values = {axis: getattr(args, axis) for axis in AXES if getattr(args, axis) is not None}
    if not values:
        raise DeferralError("rate requires at least one axis")
    project = Project(args.root, args.project_key)
    with project.lock():
        text = read_exact(project.active)
        record = find_record(text, args.ticket)
        validate_target(record)
        if record_status(record) not in ("active", "inactive"):
            raise DeferralError("rate requires an active or inactive ticket")
        changed = record.text
        for axis, value in values.items():
            if not 1 <= value <= 5:
                raise DeferralError(f"{axis} must be 1..5")
            changed = set_rating(changed, axis, value, args.date or date.today().isoformat())
        changed = set_record_hash(changed)
        atomic_write(project.active, replace_record(text, record, changed))
    print(f"{record.ticket_id}: rated")
    return 0


def command_edit(args):
    # Spec §3: title, body, companion and window metadata are material changes — they
    # bump `updated` and therefore stale ratings. lane/priority are operational, not
    # material, so editing them leaves rating freshness alone.
    material = {
        "companion": args.companion,
        "not-before": args.not_before,
        "window-closes": args.window_closes,
    }
    operational = {"lane": args.lane, "priority": args.priority}
    touched = [args.title, args.append_body] + list(material.values()) + list(operational.values())
    if all(value is None for value in touched):
        raise DeferralError("edit requires at least one field")
    project = Project(args.root, args.project_key)
    with project.lock():
        text = read_exact(project.active)
        record = find_record(text, args.ticket)
        validate_target(record)
        status = record_status(record)
        if status not in ("active", "inactive"):
            raise DeferralError(
                f"expected active or inactive, found {status}; "
                "edit never rewrites terminal history — reopen first"
            )
        if args.companion is not None:
            validate_companion(args.companion, record.ticket_id)
        changed = record.text
        if args.title is not None:
            changed = set_title(changed, args.title)
        for key, value in {**material, **operational}.items():
            if value is not None:
                changed = set_metadata(changed, key, value)
        if args.append_body is not None:
            changed = append_body(changed, args.append_body)
        if changed == record.text:
            print(f"{record.ticket_id}: no change")
            return 0
        if any(
            value is not None
            for value in list(material.values()) + [args.title, args.append_body]
        ):
            changed = set_metadata(changed, "updated", args.date or date.today().isoformat())
        changed = set_record_hash(changed)
        atomic_write(project.active, replace_record(text, record, changed))
    print(f"{record.ticket_id}: edited")
    return 0


def body_only(before, after):
    """True when a rewrite left the title line and every MANAGED field untouched."""
    head = RECORD_RE.match(after)
    if not head or head.group(0) != RECORD_RE.match(before).group(0):
        return False
    before_records = parse_records(before)
    after_records = parse_records(after)
    if (
        len(before_records) != 1
        or len(after_records) != 1
        or before_records[0].text != before
        or after_records[0].text != after
    ):
        return False

    def values(record, key):
        return [
            value.strip()
            for value in re.findall(
                rf"(?:^  - |\| ){re.escape(key)}:\s*([^|\r\n]*)",
                record,
                re.MULTILINE,
            )
        ]

    return all(values(before, key) == values(after, key) for key in MANAGED)


def command_repair_body(args):
    # `edit --append-body` is append-only by design, so a defect already in the body
    # (e.g. a duplicated "**Background:**" prefix) was previously fixable only by a
    # hand edit, which breaks record-hash. This replaces one exact, unambiguous
    # substring inside the same lock/atomic transaction `edit` uses, then re-seals the
    # hash. Body bytes only: the title and every field another verb owns are refused.
    project = Project(args.root, args.project_key)
    with project.lock():
        text = read_exact(project.active)
        record = find_record(text, args.ticket)
        validate_target(record)
        status = record_status(record)
        if status not in ("active", "inactive"):
            raise DeferralError(
                f"expected active or inactive, found {status}; "
                "repair-body never rewrites terminal history — reopen first"
            )
        matches = record.text.count(args.old)
        if matches != 1:
            raise DeferralError(
                f"--old matched {matches} times in {record.ticket_id}; "
                "exactly one match is required — extend --old until it is unique"
            )
        changed = record.text.replace(args.old, args.new)
        if changed == record.text:
            print(f"{record.ticket_id}: no change")
            return 0
        if not body_only(record.text, changed):
            raise DeferralError(
                "repair-body changes body bytes only; the title and managed metadata "
                "belong to edit, rate, claim, and transition"
            )
        changed = set_metadata(changed, "updated", args.date or date.today().isoformat())
        changed = set_record_hash(changed)
        atomic_write(project.active, replace_record(text, record, changed))
    print(f"{record.ticket_id}: body repaired")
    return 0


def command_transition(args):
    project = Project(args.root, args.project_key)
    targets = {
        "activate": "active",
        "deactivate": "inactive",
        "resolve": "resolved",
        "close": "closed",
        "reopen": "active",
    }
    target = targets[args.action]
    with project.lock():
        active_text = read_exact(project.active)
        record = find_record(active_text, args.ticket)
        validate_target(record)
        current = record_status(record)
        if current == target:
            print(f"{record.ticket_id}: already {target}")
            return 0
        allowed = {
            ("active", "deactivate"),
            ("active", "resolve"),
            ("active", "close"),
            ("inactive", "activate"),
            ("resolved", "reopen"),
            ("closed", "reopen"),
        }
        if (current, args.action) not in allowed:
            if current == "inactive" and args.action in ("resolve", "close"):
                guidance = "activate first"
            elif current in ("resolved", "closed"):
                guidance = "use reopen"
            else:
                guidance = f"expected a valid transition from {current}"
            expected = {
                "activate": "inactive",
                "deactivate": "active",
                "resolve": "active",
                "close": "active",
                "reopen": "resolved or closed",
            }[args.action]
            raise DeferralError(f"expected {expected}, found {current}; {guidance}")
        today = args.date or date.today().isoformat()
        if args.action in ("resolve", "close") and not args.actor:
            raise DeferralError(f"{args.action} requires --actor")
        if args.action == "reopen" and (not args.actor or not args.reason):
            raise DeferralError("reopen requires --actor and non-empty --reason")

        if args.action in ("deactivate", "activate"):
            changed = set_field(record.text, "status", target)
            changed = set_field(changed, "updated", today)
            changed = set_glyph(changed, DERIVED[target][1])
            if args.action == "deactivate":
                if args.inactive_reason:
                    changed = set_field(changed, "inactive_reason", args.inactive_reason)
                if args.reactivate_when:
                    changed = set_field(changed, "reactivate_when", args.reactivate_when)
            else:
                changed = remove_field(remove_field(changed, "inactive_reason"), "reactivate_when")
            changed = set_record_hash(changed)
            active_text = move_record(active_text, record, DERIVED[target][0], changed)
            atomic_write(project.active, active_text)
            print(f"{record.ticket_id}: {target}")
            return 0

        archive_text = read_exact(project.archive)
        if args.action in ("resolve", "close"):
            next_generation = generation(record) + 1
            changed = set_field(record.text, "status", target)
            changed = set_field(changed, "updated", today)
            changed = set_field(changed, "archive-generation", str(next_generation))
            changed = set_glyph(changed, DERIVED[target][1])
            changed = append_event(changed, "terminal-event", {
                "actor": args.actor,
                "date": today,
                "generation": next_generation,
                "reason": args.reason or "",
                "status": target,
            })
            changed = set_record_hash(finalize_record(changed))
            archive_text = archive_record(archive_text, project.key, changed)
            atomic_write(project.archive, archive_text)
            if os.environ.get("DEFERRALS_FAIL_AFTER_ARCHIVE") == "1":
                os._exit(86)
            tombstone = make_tombstone(record, target, project.archive.name, today, next_generation)
            active_text = move_record(active_text, record, "Terminal Tombstones", tombstone)
            atomic_write(project.active, active_text)
            print(f"{record.ticket_id}: {target}")
            return 0

        archived = find_record(archive_text, record.ticket_id)
        if generation(archived) != generation(record):
            raise DeferralError("archive generation mismatch; run doctor")
        changed = set_field(archived.text, "status", "active")
        changed = set_field(changed, "updated", today)
        changed = set_glyph(changed, " ")
        changed = append_event(changed, "reopen-event", {
            "actor": args.actor,
            "date": today,
            "generation": generation(record),
            "reason": args.reason,
        })
        changed = set_record_hash(finalize_record(changed))
        active_text = move_record(active_text, record, "Active", changed)
        atomic_write(project.active, active_text)
    print(f"{record.ticket_id}: active")
    return 0


def render_record(record, key):
    stale_ratings = rating_dates(record.text) and (
        ratings_stale(record.text) or hash_valid(record.text) is False
    )
    stale = " · ratings stale" if stale_ratings else ""
    return f"{key}: {record.ticket_id} [{record_status(record)}] {record.title}{stale}"


def thread_matches(record, thread):
    return not thread or thread in record_threads(record)


def command_list(args):
    root = Path(args.root).expanduser()
    paths = index_paths(root)
    include = {"active", "inactive"} if args.inactive else {"active"}
    if args.all_projects:
        for path in paths:
            key = key_from_path(path)
            for record in parse_records(read_exact(path)):
                if record_status(record) in include and thread_matches(record, args.thread):
                    print(render_record(record, key))
        return 0

    shown_paths = [root / f"{args.project_key}.md"]
    global_path = root / "global.md"
    if global_path not in shown_paths:
        shown_paths.append(global_path)
    for path in shown_paths:
        if not path.exists():
            continue
        key = key_from_path(path)
        for record in parse_records(read_exact(path)):
            if record_status(record) in include and thread_matches(record, args.thread):
                print(render_record(record, key))

    elsewhere = set()
    for path in paths:
        if path in shown_paths:
            continue
        for record in parse_records(read_exact(path)):
            if record_status(record) == "active" and thread_matches(record, args.thread):
                elsewhere.add(record.ticket_id)
    if elsewhere:
        print(f"{len(elsewhere)} active elsewhere")
    return 0


def command_digest(args):
    # One-line SessionStart projection: active count (project + global) + top
    # actionable item (blocking first, then important, oldest created within
    # class) + active-elsewhere count. Silent (exit 0, no output) when empty.
    root = Path(args.root).expanduser()
    project_path = root / f"{args.project_key}.md"
    global_path = root / "global.md"
    shown_paths = [project_path]
    if global_path != project_path:
        shown_paths.append(global_path)
    records = []
    for path in shown_paths:
        if not path.exists():
            continue
        for record in parse_records(read_exact(path)):
            if record_status(record) == "active":
                records.append(record)
    if not records:
        return 0

    def rank(record):
        priority = (get_field(record.text, "priority") or "normal").strip()
        klass = {"blocking": 0, "important": 1}.get(priority, 2)
        created = (get_field(record.text, "created") or "9999-99-99")
        created = created.split(" by ")[0].strip()
        return (klass, created, record.ticket_id)

    top = min(records, key=rank)
    top_priority = (get_field(top.text, "priority") or "normal").strip()
    elsewhere = set()
    for path in index_paths(root):
        if path in shown_paths:
            continue
        for record in parse_records(read_exact(path)):
            if record_status(record) == "active":
                elsewhere.add(record.ticket_id)
    line = (
        f"Deferrals: {len(records)} active · top: {top.ticket_id}"
        f" [{top_priority}] {top.title}"
    )
    if elsewhere:
        line += f" · {len(elsewhere)} active elsewhere"
    print(line)
    return 0


def expected_legacy_status(record):
    return LEGACY.get((record.section, record.glyph))


def transform_legacy_record(record, status, migrated_on):
    changed = record.text
    changed = set_field(changed, "status", status)
    terminal = status in ("resolved", "closed")
    changed = set_field(changed, "archive-generation", "1" if terminal else "0")
    changed = set_glyph(changed, DERIVED[status][1])
    if terminal:
        changed = append_event(changed, "terminal-event", {
            "actor": "migration",
            "date": migrated_on,
            "generation": 1,
            "reason": "legacy status migration",
            "status": status,
        })
    return set_record_hash(finalize_record(changed))


def migration_plan(root):
    changes = {}
    mappings = []
    blockers = []
    summaries = []
    seen = {}
    migrated_on = date.today().isoformat()
    companion_ids = {}
    if root.exists():
        for path in root.iterdir():
            match = re.match(r"^(ddf_[0-9a-f]{8})-.+\.md$", path.name)
            if match:
                companion_ids.setdefault(match.group(1), []).append(path.name)
    for ticket_id, names in companion_ids.items():
        if len(names) > 1:
            blockers.append(f"{ticket_id}: companion collision: {', '.join(sorted(names))}")

    for path in index_paths(root):
        source = read_exact(path)
        if SCHEMA not in source:
            continue
        for record in parse_records(source):
            if record.ticket_id in seen:
                blockers.append(
                    f"duplicate ID {record.ticket_id}: {seen[record.ticket_id]} and {path.name}"
                )
            else:
                seen[record.ticket_id] = path.name

    for path in index_paths(root):
        source = read_exact(path)
        if SCHEMA in source:
            continue
        records = parse_records(source)
        matched_starts = {record.start for record in records}
        for malformed in re.finditer(r"^- \[", source, re.MULTILINE):
            if malformed.start() not in matched_starts:
                line = source.count("\n", 0, malformed.start()) + 1
                blockers.append(f"{path.name}:{line}: malformed record boundary")
        active = new_document(key_from_path(path))
        archive = new_document(key_from_path(path), archive=True)
        archive_count = 0
        for record in records:
            status = expected_legacy_status(record)
            if not status:
                blockers.append(
                    f"{path.name}:{record.ticket_id}: glyph/section conflict "
                    f"[{record.glyph}] under {record.section}"
                )
                continue
            explicit = get_field(record.text, "status")
            if explicit and explicit != status:
                blockers.append(
                    f"{path.name}:{record.ticket_id}: status/glyph/section conflict"
                )
                continue
            if record.ticket_id in seen:
                blockers.append(
                    f"duplicate ID {record.ticket_id}: {seen[record.ticket_id]} and {path.name}"
                )
                continue
            seen[record.ticket_id] = path.name
            companion = get_field(record.text, "companion")
            if companion and (
                Path(companion).name != companion
                or not companion.startswith(record.ticket_id + "-")
                or not (root / companion).is_file()
            ):
                blockers.append(
                    f"{path.name}:{record.ticket_id}: companion mismatch: {companion}"
                )
            for axis in AXES:
                values = re.findall(
                    rf"(?:^  - |\| ){axis}:\s*(\d+)",
                    record.text,
                    re.MULTILINE,
                )
                if len(set(values)) > 1:
                    blockers.append(
                        f"{path.name}:{record.ticket_id}: conflicting {axis} ratings"
                    )
                for value in values:
                    if not 1 <= int(value) <= 5:
                        blockers.append(f"{path.name}:{record.ticket_id}: invalid {axis}={value}")
            transformed = transform_legacy_record(record, status, migrated_on)
            if status in ("active", "inactive"):
                active = insert_record(active, DERIVED[status][0], transformed)
            else:
                archive = insert_record(archive, "Terminal Records", transformed)
                transformed_record = parse_records(transformed)[0]
                tombstone = make_tombstone(
                    transformed_record,
                    status,
                    f"{key_from_path(path)}.archive.md",
                    migrated_on,
                    1,
                )
                active = insert_record(active, "Terminal Tombstones", tombstone)
                archive_count += 1
            mappings.append({"id": record.ticket_id, "status": status, "source": path.name})
        changes[path] = active
        if archive_count:
            changes[root / f"{key_from_path(path)}.archive.md"] = archive
        summaries.append(f"{path.name}: would migrate {len(records)} records")
    return changes, mappings, blockers, summaries


def command_migrate(args):
    root = Path(args.root).expanduser()
    changes, mappings, blockers, summaries = migration_plan(root)
    for summary in summaries:
        print(summary)
    if blockers:
        for blocker in blockers:
            print(blocker, file=sys.stderr)
        return 2
    if args.check:
        if not changes:
            print("already v0.4")
        return 0
    if not changes:
        print("already v0.4")
        return 0

    projects = set()
    for path in changes:
        if path.name.endswith(".archive.md"):
            projects.add(path.name[:-len(".archive.md")])
        elif is_index(path):
            projects.add(key_from_path(path))
    with ExitStack() as stack:
        for key in sorted(projects):
            stack.enter_context(Project(root, key).lock())
        changes, mappings, blockers, summaries = migration_plan(root)
        if blockers:
            for blocker in blockers:
                print(blocker, file=sys.stderr)
            return 2
        if not changes:
            print("already v0.4")
            return 0
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup_root = root / ".migration-backups" / stamp
        backup_root.mkdir(parents=True)
        manifest = {"schema": "deferrals-migration-v0.4", "files": [], "mappings": mappings}
        for path, postimage in sorted(changes.items(), key=lambda item: str(item[0])):
            if path.exists():
                backup = backup_root / path.name
                atomic_write(backup, read_exact(path))
                prehash = hashlib.sha256(path.read_bytes()).hexdigest()
                backup_name = backup.name
            else:
                prehash = None
                backup_name = None
            manifest["files"].append({
                "path": path.name,
                "preimage_sha256": prehash,
                "backup": backup_name,
                "postimage_sha256": hashlib.sha256(postimage.encode("utf-8")).hexdigest(),
            })
        atomic_write(
            backup_root / "manifest.json",
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        )
        for path, postimage in sorted(
            changes.items(),
            key=lambda item: (not item[0].name.endswith(".archive.md"), item[0].name),
        ):
            atomic_write(path, postimage)
    print(f"migrated {len(mappings)} records")
    return 0


def rating_issues(text):
    # Legacy embedded forms are read-only history that a canonical `  - axis:` line
    # supersedes (spec §3), so only canonical duplicates count as conflicts; an
    # out-of-range value is corrupt in any form.
    found = []
    for axis in AXES:
        for value in re.findall(rf"(?:^  - |\| ){axis}:\s*(\d+)", text, re.MULTILINE):
            if not 1 <= int(value) <= 5:
                found.append(f"invalid {axis}={value}")
        if len(re.findall(rf"^  - {axis}:", text, re.MULTILINE)) > 1:
            found.append(f"duplicate {axis} ratings")
    return found


def file_issues(path, source, records):
    found = []
    if source.count(SCHEMA) > 1:
        found.append(f"{path.name}: mixed schema markers")
    elif source.strip() and SCHEMA not in source:
        found.append(f"{path.name}: legacy schema marker; run migrate --check")
    starts = {record.start for record in records}
    for malformed in re.finditer(r"^- \[", source, re.MULTILINE):
        if malformed.start() not in starts:
            line = source.count("\n", 0, malformed.start()) + 1
            found.append(f"{path.name}:{line}: malformed record boundary")
    return found


def record_issues(path, record, root, tombstone):
    # Spec §3: new records require these; a tombstone (spec §5) carries the pointer
    # set instead. lane/priority are non-state operational metadata a migrated record
    # may omit — those are counted separately, not reported as defects.
    required = (
        ("status", "archived-at", "archive", "archive-generation", "record-hash")
        if tombstone
        else ("status", "threads", "created", "archive-generation", "record-hash")
    )
    found = []
    missing = [key for key in required if get_field(record.text, key) is None]
    if missing:
        found.append(f"{path.name}:{record.ticket_id}: missing required field: {', '.join(missing)}")
    found.extend(f"{path.name}:{record.ticket_id}: {issue}" for issue in rating_issues(record.text))
    companion = get_field(record.text, "companion")
    if companion:
        if Path(companion).name != companion or not companion.startswith(record.ticket_id + "-"):
            found.append(f"{path.name}:{record.ticket_id}: companion mismatch: {companion}")
        elif not (root / companion).is_file():
            found.append(f"{path.name}:{record.ticket_id}: missing companion: {companion}")
    return found


def diagnostics(root):
    issues = []
    owners = {}
    archive_owners = {}
    declared_companions = set()
    archive_by_key = {}
    index_records = []
    omissions = 0
    for path in index_paths(root):
        key = key_from_path(path)
        source = read_exact(path)
        records = parse_records(source)
        issues.extend(file_issues(path, source, records))
        index_records.extend((key, path, record) for record in records)
        archive_path = root / f"{key}.archive.md"
        archive_source = read_exact(archive_path)
        archive_records = parse_records(archive_source)
        if archive_source:
            issues.extend(file_issues(archive_path, archive_source, archive_records))
        archive_by_key[key] = {}
        for archived in archive_records:
            archive_owners.setdefault(archived.ticket_id, []).append(archive_path.name)
            archive_by_key[key].setdefault(archived.ticket_id, archived)
            valid = hash_valid(archived.text)
            if valid is False:
                issues.append(f"{archive_path.name}:{archived.ticket_id}: direct-edit drift")
            elif valid is None and SCHEMA in archive_source:
                issues.append(f"{archive_path.name}:{archived.ticket_id}: missing record hash")
            status = record_status(archived)
            if status not in ("resolved", "closed"):
                issues.append(f"{archive_path.name}:{archived.ticket_id}: invalid archive status")
            elif archived.section != "Terminal Records" or archived.glyph != DERIVED[status][1]:
                issues.append(f"{archive_path.name}:{archived.ticket_id}: derived presentation mismatch")
            issues.extend(record_issues(archive_path, archived, root, tombstone=False))
            companion = get_field(archived.text, "companion")
            if companion:
                declared_companions.add(companion)
            if rating_dates(archived.text) and (
                ratings_stale(archived.text) or valid is False
            ):
                issues.append(f"{archive_path.name}:{archived.ticket_id}: ratings stale")
        for record in records:
            owners.setdefault(record.ticket_id, []).append(path.name)
            valid = hash_valid(record.text)
            if valid is False:
                issues.append(f"{path.name}:{record.ticket_id}: direct-edit drift")
            elif valid is None and SCHEMA in source:
                issues.append(f"{path.name}:{record.ticket_id}: missing record hash")
            status = record_status(record)
            if status not in DERIVED:
                issues.append(f"{path.name}:{record.ticket_id}: invalid status")
            else:
                expected_section, expected_glyph = DERIVED[status]
                if record.section != expected_section or record.glyph != expected_glyph:
                    issues.append(f"{path.name}:{record.ticket_id}: derived presentation mismatch")
            issues.extend(record_issues(
                path, record, root, tombstone=status in ("resolved", "closed")
            ))
            if status in ("active", "inactive") and any(
                get_field(record.text, key) is None for key in ("lane", "priority")
            ):
                omissions += 1
            companion = get_field(record.text, "companion")
            if companion:
                declared_companions.add(companion)
            if rating_dates(record.text) and (
                ratings_stale(record.text) or valid is False
            ):
                issues.append(f"{path.name}:{record.ticket_id}: ratings stale")

    for ticket_id, paths in owners.items():
        if len(paths) > 1:
            issues.append(f"duplicate ID {ticket_id}: {', '.join(paths)}")
    for ticket_id, paths in archive_owners.items():
        if len(paths) > 1:
            issues.append(f"duplicate archive ID {ticket_id}: {', '.join(paths)}")

    for key, path, record in index_records:
        archived = archive_by_key[key].get(record.ticket_id)
        status = record_status(record)
        if status in ("resolved", "closed"):
            if (
                not archived
                or record_status(archived) != status
                or generation(archived) != generation(record)
            ):
                issues.append(f"{path.name}:{record.ticket_id}: stale tombstone")
        elif archived and record_status(archived) in ("resolved", "closed"):
            if generation(archived) == generation(record) + 1:
                issues.append(f"{path.name}:{record.ticket_id}: half-migration")
            elif generation(archived) not in (generation(record), generation(record) + 1):
                issues.append(f"{path.name}:{record.ticket_id}: generation mismatch")

    companions = {}
    for path in root.iterdir() if root.exists() else ():
        match = re.match(r"^(ddf_[0-9a-f]{8})-.+\.md$", path.name)
        if not match:
            continue
        companions.setdefault(match.group(1), []).append(path.name)
        if path.name not in declared_companions:
            issues.append(f"{path.name}: orphan companion")
    for ticket_id, names in companions.items():
        if len(names) > 1:
            issues.append(f"{ticket_id}: companion collision: {', '.join(sorted(names))}")
    return sorted(set(issues)), omissions


def command_doctor(args):
    issues, omissions = diagnostics(Path(args.root).expanduser())
    for issue in issues:
        print(issue)
    if not issues:
        print("ok")
    if omissions:
        # Spec §3 permits migrated records to omit non-state operational metadata and
        # asks doctor to report it — informational, so it never sets the exit code.
        print(f"note: {omissions} record(s) omit optional lane/priority metadata")
    return 1 if issues else 0


def command_reconcile(args):
    project = Project(args.root, args.project_key)
    repaired = 0
    with project.lock():
        active_text = read_exact(project.active)
        archive_text = read_exact(project.archive)
        archives = {record.ticket_id: record for record in parse_records(archive_text)}
        for record in list(parse_records(active_text)):
            archived = archives.get(record.ticket_id)
            if (
                record_status(record) in ("active", "inactive")
                and archived
                and record_status(archived) in ("resolved", "closed")
                and generation(archived) == generation(record) + 1
            ):
                validate_target(record)
                validate_target(archived)
                status = record_status(archived)
                tombstone = make_tombstone(
                    archived,
                    status,
                    project.archive.name,
                    get_field(archived.text, "updated") or date.today().isoformat(),
                    generation(archived),
                )
                current = find_record(active_text, record.ticket_id)
                active_text = move_record(active_text, current, "Terminal Tombstones", tombstone)
                repaired += 1
        if repaired:
            atomic_write(project.active, active_text)
        # Spec §5: the archive-first crash is the sole repairable duplicate; every
        # other generation/status disagreement is refused rather than skipped.
        remaining = []
        for record in parse_records(active_text):
            archived = archives.get(record.ticket_id)
            if not archived:
                continue
            status = record_status(record)
            archived_status = record_status(archived)
            if status in ("resolved", "closed"):
                if archived_status != status or generation(archived) != generation(record):
                    remaining.append(
                        f"{record.ticket_id}: tombstone disagrees with archive "
                        f"({status} g{generation(record)} vs {archived_status} g{generation(archived)})"
                    )
            elif archived_status in ("resolved", "closed") and generation(archived) != generation(record):
                remaining.append(
                    f"{record.ticket_id}: unrepairable generation state "
                    f"({status} g{generation(record)} vs {archived_status} g{generation(archived)})"
                )
    print(f"reconciled {repaired}")
    for item in remaining:
        print(f"refused: {item}", file=sys.stderr)
    return 2 if remaining else 0


def command_forget(args):
    project = Project(args.root, args.project_key)
    companion = None
    target = None
    with project.lock():
        active_text = read_exact(project.active)
        record = find_record(active_text, args.ticket)
        validate_target(record)
        companion = get_field(record.text, "companion")
        if args.companion == "delete" and companion:
            target = project.root / companion
            if (
                target.resolve(strict=False).parent != project.root.resolve(strict=False)
                or not target.name.startswith(record.ticket_id + "-")
            ):
                raise DeferralError("unsafe companion path")
        active_text = remove_record(active_text, record)
        archive_text = read_exact(project.archive)
        archived = [item for item in parse_records(archive_text) if item.ticket_id == record.ticket_id]
        if archived:
            validate_target(archived[0])
            archive_text = remove_record(archive_text, archived[0])
            atomic_write(project.archive, archive_text)
        atomic_write(project.active, active_text)
        if target and target.exists():
            durable_unlink(target)
    print(f"{record.ticket_id}: forgotten; companion {args.companion}")
    return 0


def default_project_key():
    # Must match the documented rule AND deferrals_digest.sh exactly: git-common-dir
    # parent (worktree-safe, normalized — the flag returns a relative path from any
    # non-root cwd), else cwd; then '/' and ' ' both become '-'. Omitting either step
    # silently addresses a different index than the SessionStart digest reports.
    root = Path.cwd().resolve()
    try:
        common = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(root), capture_output=True, text=True, timeout=5,
        )
        if common.returncode == 0 and common.stdout.strip():
            candidate = Path(common.stdout.strip())
            if not candidate.is_absolute():
                candidate = root / candidate
            root = candidate.resolve().parent
    except (OSError, subprocess.SubprocessError):
        pass
    return str(root).replace("/", "-").replace(" ", "-")


def single_line(value):
    if "\n" in value or "\r" in value:
        raise argparse.ArgumentTypeError("value must be one line")
    return value


def metadata_token(value):
    value = single_line(value)
    if "|" in value:
        raise argparse.ArgumentTypeError("metadata token cannot contain |")
    return value


def thread_token(value):
    value = metadata_token(value)
    if "," in value:
        raise argparse.ArgumentTypeError("thread ID cannot contain a comma")
    return value


def project_key(value):
    if value == "global":
        return value
    if not value.startswith("-") or "/" in value or value.endswith(".archive"):
        raise argparse.ArgumentTypeError("project key must be global or a legacy -path key")
    return single_line(value)


def iso_date(value):
    try:
        date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD")
    return value


def parser():
    top = argparse.ArgumentParser()
    top.add_argument(
        "--root",
        default=os.environ.get(
            "DEFERRALS_ROOT", str(Path.home() / ".claude" / "deferrals")
        ),
    )
    top.add_argument("--project-key", default=default_project_key(), type=project_key)
    commands = top.add_subparsers(dest="verb")

    listing = commands.add_parser("list")
    listing.add_argument("--all-projects", action="store_true")
    listing.add_argument("--thread")
    listing.add_argument("--inactive", action="store_true")

    add = commands.add_parser("add")
    add.add_argument("--id", dest="ticket_id")
    add.add_argument("--title", required=True, type=single_line)
    add.add_argument("--thread", required=True, type=thread_token)
    add.add_argument("--lane", choices=("L", "H"), required=True)
    add.add_argument("--priority", required=True, type=metadata_token)
    add.add_argument("--actor", type=single_line)
    add.add_argument("--date", type=iso_date)
    add.add_argument("--body")
    add.add_argument("--companion", type=single_line)

    transition = commands.add_parser("transition")
    transition.add_argument("action", choices=("activate", "deactivate", "resolve", "close", "reopen"))
    transition.add_argument("ticket")
    transition.add_argument("--actor", type=single_line)
    transition.add_argument("--date", type=iso_date)
    transition.add_argument("--reason")
    transition.add_argument("--inactive-reason", type=single_line)
    transition.add_argument("--reactivate-when", type=single_line)

    edit = commands.add_parser("edit")
    edit.add_argument("ticket")
    edit.add_argument("--title", type=single_line)
    edit.add_argument("--lane", choices=("L", "H"))
    edit.add_argument("--priority", type=metadata_token)
    edit.add_argument("--companion", type=single_line)
    edit.add_argument("--not-before", type=iso_date)
    edit.add_argument("--window-closes", type=iso_date)
    edit.add_argument("--append-body")
    edit.add_argument("--date", type=iso_date)

    repair = commands.add_parser("repair-body")
    repair.add_argument("ticket")
    repair.add_argument("--old", required=True)
    repair.add_argument("--new", required=True)
    repair.add_argument("--date", type=iso_date)

    claim = commands.add_parser("claim")
    claim.add_argument("ticket")
    claim.add_argument("--thread", required=True, type=thread_token)

    rate = commands.add_parser("rate")
    rate.add_argument("ticket")
    for axis in AXES:
        rate.add_argument(f"--{axis}", type=int)
    rate.add_argument("--date", type=iso_date)

    commands.add_parser("digest")
    commands.add_parser("check")
    commands.add_parser("doctor")
    commands.add_parser("reconcile-archive")

    migrate = commands.add_parser("migrate")
    mode = migrate.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")

    forget = commands.add_parser("forget")
    forget.add_argument("ticket")
    forget.add_argument("--companion", choices=("retain", "delete"), default="retain")
    return top


def main(argv=None):
    raw = list(sys.argv[1:] if argv is None else argv)
    if "--project-key" in raw:
        index = raw.index("--project-key")
        if index + 1 < len(raw):
            raw[index:index + 2] = [f"--project-key={raw[index + 1]}"]
    args = parser().parse_args(raw)
    if args.verb is None:
        args.all_projects = False
        args.thread = None
        args.inactive = False
        return command_list(args)
    handlers = {
        "list": command_list,
        "digest": command_digest,
        "add": command_add,
        "edit": command_edit,
        "repair-body": command_repair_body,
        "transition": command_transition,
        "claim": command_claim,
        "rate": command_rate,
        "check": command_doctor,
        "doctor": command_doctor,
        "reconcile-archive": command_reconcile,
        "migrate": command_migrate,
        "forget": command_forget,
    }
    try:
        return handlers[args.verb](args)
    except DeferralError as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
