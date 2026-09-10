# Deferrals storage and command contract v0.4

## 1. Authority and invariants

1. `status:` is the only lifecycle authority. Checkbox glyph, section, and file
   placement are derived views and validation constraints.
2. States are `active`, `inactive`, `resolved`, and `closed`. Ticket age never
   changes status and never selects a ticket for archiving.
3. Every cooperative mutation uses the lock and durable-replace protocol in §6.
4. A terminal transition writes the recoverable archive copy before replacing
   the live record with a tombstone. A crash may duplicate data, never lose it.
5. Unknown metadata and body bytes are opaque and preserved by commands that do
   not explicitly change them.
6. `prune` does not exist. `reconcile-archive` is the repair operation.
7. Project re-keying and the D7 data relocation are outside v0.4.

## 2. Paths, keys, and discovery

- Data root is selected by `--root`, then `DEFERRALS_ROOT`, and otherwise defaults to
  `~/.claude/deferrals/`.
- The existing shared project-key rule remains: replace `/` in the absolute cwd
  with `-`; `/work/example` is `-work-example`. Do not decode, consolidate,
  alias, or silently re-key it.
- `global` is the reserved global key.
- Active index: `<root>/<key>.md`.
- Archive: `<root>/<key>.archive.md`.
- Lock: `<canonical-index-path>.lock`, where `canonical-index-path` is the
  symlink-resolved active-index path. The archive never gets a separate lock.
- Companion: `<root>/ddf_<8-lowercase-hex>-<stable-slug>.md`.

An index classifier accepts only direct children named `global.md` or matching
`^-[^/]+\.md$`. It rejects `*.archive.md`, `ddf_*.md`, `*.lock`, hidden/temp
files, backups, manifests, and migration directories. Discovery must use this
classifier, never raw `*.md`.

Default `list` renders active records from current project and `global`, plus
one active-only count from all other indexes. The elsewhere count excludes
current, global, inactive records, terminal tombstones, and archives; it
deduplicates full ticket IDs. `--inactive` may report inactive separately.

## 3. File and record grammar

UTF-8 and existing newline style are preserved. A new v0.4 active file is:

```markdown
# Deferrals — <key>
<!-- deferrals-schema: 0.4 -->

## Active

- [ ] **ddf_0123abcd** — Title
  - status: active
  - threads: thread-id[, thread-id ...]
  - created: YYYY-MM-DD by actor
  - updated: YYYY-MM-DD
  - lane: L|H
  - priority: <existing priority token>
  - archive-generation: 0
  - record-hash: sha256:<64 lowercase hex>
  <opaque metadata and body>

## Inactive

## Terminal Tombstones
```

The archive uses the same marker, `# Deferrals Archive — <key>`, and one
`## Terminal Records` section.

A full record starts at a top-level line matching
`^- \[[ x-]\] \*\*(ddf_[0-9a-f]{8})\*\* — ` and ends immediately before the
next such line, the next `## ` heading, or EOF. Its bytes, including blank
lines, are its record slice. Unknown indented lines are body, not parse errors.

Identity is the full `ddf_` ID; prefixes are accepted only when unique across
the command's search scope. New records require title, `status`, `threads`,
`created`, `lane`, `priority`, `archive-generation`, and `record-hash`.
Migrated records may omit non-state operational metadata; `doctor` reports
omissions but migration must not invent judgment-bearing values.

Derived placement is exact:

| `status` | active-file section | glyph | full body location |
|---|---|---|---|
| `active` | `Active` | `[ ]` | active index |
| `inactive` | `Inactive` | `[ ]` | active index |
| `resolved` | `Terminal Tombstones` | `[x]` | archive |
| `closed` | `Terminal Tombstones` | `[-]` | archive |

The shared `[ ]` glyph for both nonterminal states preserves Markdown checkbox
compatibility; section plus glyph are validation only, never status authority.

`record-hash` is SHA-256 over the exact record slice with the complete
`  - record-hash: ...` line removed. A mismatch is direct-edit drift. Glyph or
section mismatch is reported independently. A scripted material change updates
`updated` and the hash. Material changes are title, status, body, companion,
inactive/reactivation metadata, or window metadata; claim/thread-only changes
do not stale ratings.

Optional machine metadata:

```markdown
  - inactive_reason: <single-line text>
  - reactivate_when: <artifact/event pointer>
  - companion: ddf_0123abcd-stable-slug.md
  - not-before: YYYY-MM-DD
  - window-closes: YYYY-MM-DD
  - impact: 1..5 | rated: YYYY-MM-DD
  - opportunity: 1..5 | rated: YYYY-MM-DD
  - confidence: 1..5 | rated: YYYY-MM-DD
  - autonomy: 1..5 | rated: YYYY-MM-DD
```

Ratings are optional and independently dated. `rate` validates 1–5 and writes
the affected axis plus `rated`. Listing marks an axis stale when `updated` is
later than its `rated` date or direct-edit drift exists; it never rewrites a
score. Re-rating is event-triggered, never timer-triggered. `not-before` and
`window-closes` are allowed only for real windows and are re-rating triggers.
`impact * opportunity` is a queue heuristic, never authorization; priority,
safety, and blocking constraints still gate work.

Axis meanings are:

- `impact`: value and credible downstream reach if successful.
- `opportunity`: present executability—path, prerequisites, access, scope, and
  proportionate effort; excludes belief that diagnosis/remedy is correct.
- `confidence`: evidential certainty in premise and remedy, including side
  effects; excludes access and prerequisite status.
- `autonomy`: human-decision/participation burden on the identified path;
  excludes non-human blockers and generic tractability.

`lane` remains transfer fidelity and `priority` remains user urgency. Parsers
must also read without rewriting:

- embedded v0.3 `lane: ... | priority: ... | autonomy: N` metadata;
- `impact: N · opportunity: N (source, YYYY-MM-DD)`, treating the final date as
  the rating date for both axes when present;
- any subset of those legacy three operational axes and rating fields.

## 4. Lifecycle

| Current | Command | Result | Required data |
|---|---|---|---|
| active | `deactivate` | inactive | optional `inactive_reason`, optional `reactivate_when` |
| active | `resolve` | resolved | actor, date; optional reason |
| active | `close` | closed | actor, date; optional reason |
| inactive | `activate` | active | actor/date when automated |
| resolved | `reopen` | active | actor, date, non-empty reason |
| closed | `reopen` | active | actor, date, non-empty reason |

All other state-changing edges are rejected with current state, expected state,
and guidance. In particular, inactive must be activated before resolve/close,
and terminal records may be activated only through `reopen`. A request already
at its target is an idempotent no-op, not an edge; it returns the existing
result and performs no write.

Automation may switch active/inactive only from `reactivate_when` or explicit
model/user judgment. Deterministic code must not infer relevance.

Terminal and reopen history use JSON to preserve arbitrary actor/reason text:

```markdown
  - terminal-event: {"generation":1,"status":"resolved","date":"2026-07-30","actor":"...","reason":"..."}
  - reopen-event: {"generation":1,"date":"2026-07-30","actor":"...","reason":"..."}
```

JSON is compact UTF-8 with sorted keys. History is retained across repeated
resolve/reopen cycles.

## 5. Archive transaction and tombstones

Each ticket carries nonnegative `archive-generation`, initially `0`. An archive
contains at most one full record per ticket ID; later terminal cycles replace
that record with the newer full record and accumulated history.

For resolve/close of active record generation `g`, under one project lock:

1. Validate active status, hashes, unique ID, and any optimistic precondition.
2. Create the terminal full record with generation `g+1`, terminal status,
   derived glyph, and appended `terminal-event`.
3. Atomically write and durably flush the archive containing that full record.
4. Replace the active full record with this tombstone and durably flush:

```markdown
- [x] **ddf_0123abcd** — Title
  - status: resolved
  - archived-at: 2026-07-30
  - archive: <key>.archive.md
  - archive-generation: 1
  - companion: ddf_0123abcd-stable-slug.md
  - record-hash: sha256:<hash>
```

Closed uses `[-]` and `status: closed`. The archive pointer is a basename, not
an arbitrary path.

A crash after step 3 leaves archive generation `g+1` and active full generation
`g`; this is the sole automatically repairable duplicate. `reconcile-archive`
finishes the tombstone. Equal generations with an active full record represent
a valid reopen. Any other generation/status disagreement is refused.

`reopen` reconstructs the active full record from the archive, changes status
to active, keeps generation `g`, appends `reopen-event`, and replaces the
tombstone. The archive remains as terminal history. A later terminal cycle
replaces it at generation `g+1`.

## 6. Locking and durable replacement

For a project index, resolve symlinks before deriving the adjacent sidecar lock.
Open the stable lock file and acquire `fcntl.flock(LOCK_EX)` before any
mutation read. Hold it across read of active+archive, parse, validation,
precondition check, modification, and all commits. `migrate --apply` acquires
affected project locks in sorted canonical-path order. Read-only commands may
take `LOCK_SH` through the same primitive.

Every file commit writes a uniquely named temp file in the target directory,
preserves the target mode when it exists, flushes and `fsync`s the temp file,
calls `os.replace(temp, target)`, then `fsync`s the parent directory. Cleanup
may remove only that invocation's uncommitted temp. Locking the data-file inode
or using separate active/archive locks is forbidden.

This primitive covers add, claim, rate, activate/deactivate, resolve/close,
reopen, forget, reconciliation, migration, and trigger-watermark mutations.
No lock is held while an LLM authors a companion body.

## 7. Companion lifecycle

- `companion` is a root-relative basename whose embedded full ID must match the
  ticket. It is stable across status, reopen, and project-key changes.
- The path remains in both the archive full record and active record/tombstone.
- Resolve and close never delete or rename a companion.
- Reopen restores the same path.
- `forget` requires `--companion retain|delete`; default is `retain`. Delete
  requires an exact matching path and remains explicit/destructive.
- Missing declared companions, undeclared ID-matching files, mismatched IDs,
  and multiple companions for one ID are reported. Audits never auto-delete.
- If scripted companion mutation is later added, it uses a ticket-ID lock, not
  a project lock held across authoring.

## 8. Migration

`migrate --check` is read-only. `migrate --apply` is explicit, locked,
idempotent, and never an implicit first-run action.

Legacy mapping:

| Legacy glyph | v0.4 status | destination |
|---|---|---|
| `[ ]` | active | active index / `Active` |
| `[x]` | resolved | archive full record + active tombstone |
| `[-]` | closed | archive full record + active tombstone |

Legacy `Open`, `Resolved`, and `Abandoned` headings are constraints. A glyph
under a contradictory heading is ambiguous and blocks apply. Existing
`status:` must agree with glyph and section. There is no inferred legacy path
to inactive.

Check reports every file/line/ID for: malformed record boundaries or IDs,
glyph/section/status conflicts, duplicate canonical records within or across
indexes/archives, out-of-range or conflicting rating values, companion
collision/mismatch/orphan, hash drift, stale/missing tombstones, generation
mismatch, mixed schema markers, and half migrations.

Apply refuses malformed or ambiguous records, duplicate canonical ownership,
companion collisions/mismatches, conflicting legacy state/ratings, and
unrepairable generation states. Unknown metadata, missing optional operational
metadata, and an orphan companion are reported but do not justify discarding
an otherwise unambiguous ticket.

Before the first write, apply creates byte-exact backups under
`<root>/.migration-backups/<UTC-timestamp>/` and a JSON manifest containing
source path, preimage SHA-256, backup path, intended postimage SHA-256, and
ticket mappings. Backups and manifest are flushed before data commits. Resume
uses the manifest and hashes: already-matching postimages are skipped; the
single generation `g/g+1` archive-first state is completed; any divergent
preimage/postimage is refused. A clean v0.4 rerun performs zero writes.

## 9. Consumer cutover

Before migrating a live store, identify every writer and path consumer. Every writer
must use the script, every reader must treat `status:` as authority, and all consumers
must agree on the configured root and project-key rule. No consumer may silently create
a fresh file under a different root or slug.
