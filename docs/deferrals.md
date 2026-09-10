# Deferrals

`deferrals` is a thread-aware, project-scoped tracker for work deliberately
postponed beyond the current session. Each ticket has a stable identifier and
enough context for another agent to act on it later.

The current v0.5.3 implementation is script-backed. Index and archive mutations are
deterministic, lock-guarded, atomic, and protected by per-record hashes. Do not
hand-edit those files.

## When To Use

Use a deferral when the work is real, intentionally postponed, and likely to be
lost through compaction, a new session, or a branched conversation. Do not use
it as a sprint board, notification system, shared bug tracker, or substitute for
a Decision Record.

## Command Surface

Run the CLI shipped inside the installed skill directory:

```bash
python3 <installed-skill-dir>/scripts/deferrals.py [--root <path>] [--project-key <slug>] <verb> [args]
```

Record-root precedence is `--root`, then `DEFERRALS_ROOT`, then
`~/.claude/deferrals`. The home-relative default is intentionally preserved so
existing records remain visible across providers after migration. Git is
optional and only improves automatic project-key discovery.

| Verb | Purpose |
|---|---|
| `list`, `digest` | Read active inventory for one project or across supported scopes. |
| `add` | Create a ticket after the agent infers and confirms lane and priority. |
| `edit`, `repair-body` | Append or narrowly repair ticket content; `repair-body` rejects managed-field injection and record-boundary changes. |
| `rate` | Record optional impact, opportunity, confidence, and autonomy ratings. |
| `claim` | Attach another thread to a ticket's lineage. |
| `transition` | Move a ticket through its allowed lifecycle edge. |
| `check`, `doctor` | Validate structure, hashes, archive agreement, and related invariants. |
| `reconcile-archive` | Finish only the narrowly defined interrupted terminal transaction. |
| `migrate` | Check or explicitly apply the legacy-to-current schema migration. |
| `forget` | Hard-delete a ticket; the only destructive verb. |

`tend` remains an agent-led review loop: the agent walks tickets with the user
and applies each choice through the CLI verb that owns it.

## Ticket Model

Every ticket carries a stable id, title, status, creation and update metadata,
thread lineage, a fidelity lane, priority, archive generation, and a
`record-hash`. Optional ratings and scheduling windows can be added when the
evidence supports them.

The fidelity lane and priority are independent:

- `L` carries a title and brief context.
- `H` carries enough background, action guidance, triggers, and references to
  pass the transfer test: could another agent act competently using only the
  ticket and its cited artifacts?

Large or repeatedly revised prose belongs in a companion file. Companion bodies
are the only sanctioned free-form write surface; the CLI records and validates
their pointers but does not author their content.

## Lifecycle

The four states are `active`, `inactive`, `resolved`, and `closed`.
`transition` owns every state change. Resolved and closed records move to the
archive with a tombstone retained in the active index; reopening restores them
through a guarded transaction. Age alone never changes status.

## Integrity Boundary

The CLI is the only supported mutation path for indexes and archives. It uses a
lock, atomic replacement, and generation checks to prevent concurrent or
partial writes. `doctor` surfaces direct-edit drift, malformed records, archive
disagreement, and invalid companion pointers instead of silently repairing
them.

## Partial Adoption

The CLI and one project index are the irreducible core. Thread discovery,
ratings, scheduling windows, companion bodies, and the optional session-start
digest can be omitted without weakening transaction safety.
The core CLI uses only the Python standard library plus POSIX `fcntl`, so its
supported platforms are macOS and Linux.

## Provider Notes

The main suite installer copies the CLI and integration scripts into each
opted-in provider target. It does not execute a skill-local installer or
register a provider hook. Platforms that support the optional session-start
digest must enable it explicitly through the deferrals integration installer;
platforms without that hook can call `digest` directly. The optional Claude
hook scripts require Bash and `jq`; neither is required by the core CLI.
