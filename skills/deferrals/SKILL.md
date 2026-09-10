---
name: deferrals
version: 0.5.3
description: "Thread-aware, project-scoped tracker for \"revisit later\" items that would otherwise be lost through compaction, new sessions, or branching. Invoke when the user asks to defer, list, resolve, close, rate, enrich, or tend deferred work. Read this skill before touching the configured deferrals data root: v0.5 is script-backed and hand-editing an index corrupts it."
---

# Deferrals

Project-scoped tracker for deferred work. **v0.4 moved all mutation into a script.**
The model's job is judgment — which ticket, what text, what rating. The write itself
is deterministic, lock-guarded, and atomic.

v0.5.3 hardens `repair-body`: a replacement must remain one complete record and may
not add, remove, or duplicate metadata owned by another verb.

## Golden rule

**Never hand-edit an index or archive file under the configured deferrals root** —
`<key>.md` and `<key>.archive.md`. Every add / claim / rate / state change goes
through:

Set `DEFERRALS_ROOT` to select a different shared store; it defaults to the canonical
`~/.claude/deferrals`. `--root <path>` overrides it per command.

[PROVIDER:CLAUDE]
```bash
python3 ~/.claude/skills/deferrals/scripts/deferrals.py [--root <path>] [--project-key <slug>] <verb> [args]
```
Claude is the default owning workflow for mutation. Use the script-only mutation,
locking, integrity, and user-confirmation rules below; the optional SessionStart hook
does not grant mutation authority.
[/PROVIDER:CLAUDE]
[PROVIDER:CODEX]
```bash
python3 ~/.codex/skills/deferrals/scripts/deferrals.py [--root <path>] [--project-key <slug>] {list|digest|check|doctor}
```
Codex use is read-only. Do not invoke `add`, `edit`, `repair-body`, `rate`, `claim`,
`transition`, `reconcile-archive`, `migrate --apply`, or `forget`; route a proposed
mutation through the separately authorized governance writer when one is available.
[/PROVIDER:CODEX]
[PROVIDER:GEMINI]
```bash
python3 ~/.gemini/skills/deferrals/scripts/deferrals.py [--root <path>] [--project-key <slug>] {list|digest|check|doctor}
```
Gemini use is read-only unless the user explicitly designates it as the owning writer
for a separate store. Missing hook integration never expands mutation authority.
[/PROVIDER:GEMINI]

Freehand markdown surgery is what v0.4 exists to eliminate: it caused multi-agent write
conflicts, cost ~52K tokens per read of the largest file, and corrupted records at
distance. Records carry a `record-hash`; hand edits show up as drift in `doctor`.

**The one sanctioned exception:** *companion body files* (`ddf_<id>-<slug>.md`) are
LLM-authored prose, carry no record-hash, and are outside the locked transaction
(spec §7). Write those with normal file tools. The script only records and validates
the pointer — it never creates or edits companion content.

Binding grammar and transaction contract: [references/v04-spec.md](references/v04-spec.md).
Load it when changing the script, debugging a `doctor` finding, or writing a new consumer —
not for routine verb use.

## When to invoke

- "defer this" / "come back to this later" / "revisit X" / "note this for later"
- "what's still open?" / "what did I defer?" / "show me my deferrals" / "list deferrals"
- "mark that done" / "resolve the deferral about Y" / "that's handled now"
- "close that deferral" (deliberately irrelevant, not completed) / "park that for now"
- "enrich that deferral" / "rate that deferral" / "tend to deferrals"
- User runs `/deferrals <verb> [args]`

Also: when completing work that clearly matches an active deferral, self-invoke
`resolve` as part of task completion (§Auto-cleanup).

## Verbs

| Verb | Command | Semantics |
|---|---|---|
| `list` (default) | `list` | Active records for this project + `global`, plus an active-elsewhere count |
| | `list --inactive` | Include inactive records |
| | `list --all-projects` | Sweep every project index |
| | `list --thread <id>` | Filter to one thread's lineage |
| `digest` | `digest` | One-line summary (count + top item + elsewhere count). Powers the SessionStart hook |
| `add` | `add --title … --thread … --lane L\|H --priority …` | Create a ticket (run the §add inference loop first). Add `--id ddf_<8hex>` when you also pass `--companion`, since the basename must embed the ticket's own ID |
| `edit` (`enrich`) | `edit <id> [--title …] [--lane L\|H] [--priority …] [--append-body …] [--companion …] [--not-before YYYY-MM-DD] [--window-closes YYYY-MM-DD]` | In-place edit preserving ID, threads, and `created`. Active/inactive only — terminal records refuse (`reopen` first). Body is **append-only**; existing body bytes are never rewritten |
| `repair-body` | `repair-body <id> --old <text> --new <text>` | Fix a defect already in the body (e.g. a doubled `**Background:**`) by exact-substring replace, then re-seal the hash. Refuses unless `--old` matches exactly once, refuses any change to the title or a field another verb owns, and refuses terminal records. The only verb that rewrites existing body bytes |
| `rate` | `rate <id> [--impact N] [--opportunity N] [--confidence N] [--autonomy N]` | Write 1-5 axes + `rated:` date |
| `claim` | `claim <id> --thread <id>` | Append a thread to a ticket's lineage (post-fork inheritance) |
| transitions | `transition {activate,deactivate,resolve,close,reopen} <id> --actor <who> [--date …] [--reason …]` | The only lifecycle mutation path. `--actor` is **required** for `resolve`, `close`, and `reopen`; `reopen` also requires a non-empty `--reason` |
| `check` / `doctor` | `check` · `doctor` | Read-only integrity across the spec §8 list (see §Guardrails). Exit 1 on any defect; the optional-metadata `note:` line is informational and never sets the exit code |
| `reconcile-archive` | `reconcile-archive` | Finish an interrupted terminal transaction; **refuses** (exit 2) on any other generation/status disagreement |
| `migrate` | `migrate --check` · `migrate --apply` | Legacy → v0.4. Explicit, never implicit |
| `forget` | `forget <id> [--companion retain\|delete]` | Hard-delete. The only destructive verb; companion disposition defaults to `retain` |
| `tend` | *(no CLI verb — LLM-side)* | Walk items with the user; apply each choice through the verb that owns it (§tend) |

> **`edit` is deliberately narrow.** It cannot rewrite or delete existing body bytes
> (append only — that is `repair-body`), cannot clear a window date once set (write a corrected date instead),
> cannot touch `threads` (that is `claim`), `created`, `status` (that is `transition`),
> or ratings (that is `rate`), and never edits a `resolved`/`closed` record. Heavyweight
> or repeatedly-revised prose still belongs in a **companion file** — `edit --companion`
> attaches one to an existing ticket. Never `forget` + re-`add` to fake an edit: that
> destroys the ticket's ID, lineage, and created-date.

## Lifecycle (4 states)

For any v0.4 record, `status:` is the **only** authority — checkbox glyph, section, and
file placement are derived presentation. The glyph/section pair is read as a *fallback*
only when `status:` is absent, which after migration means an unmigrated legacy record.

| From | Command | To | Notes |
|---|---|---|---|
| active | `deactivate` | inactive | optional `inactive_reason`, `reactivate_when` |
| active | `resolve` | resolved | actually completed |
| active | `close` | closed | deliberately judged irrelevant |
| inactive | `activate` | active | |
| resolved / closed | `reopen` | active | requires actor + date + non-empty reason |

Every other edge is refused with current state, expected state, and guidance —
including inactive → resolve (activate first). Terminal records move their full body
to `<key>.archive.md`, leaving a tombstone in the index.

**Age is never a status signal.** Old tickets are live inventory, not stale ones — a
ticket from May is as actionable as one from today, often more so as models improve.
Nothing archives on age; only `resolved`/`closed` relocate.

Automation may flip active ↔ inactive only from an explicit `reactivate_when` pointer
or model/user judgment. Deterministic code must never infer relevance.

## Metadata model

Two operational axes (unchanged from v0.3) and four optional rating axes.

- **`lane: L | H`** — *transfer fidelity*. `L` = title + 1-3 lines. `H` = structured
  Background / Action / Trigger / Cross-reference.
- **`priority: trivial | normal | important | blocking`** — *user urgency*. This is the
  canonical set and what new tickets should use, but the parser accepts any single-line
  token and legacy files carry others (`low`, `medium`, `high`, `moderate`). Read them;
  don't rewrite them. Only `blocking` and `important` affect `digest` ordering.

### The transfer test — the load-bearing lane tiebreaker

> *"If another agent in a different chat picked up this item — with access only to
> (a) this deferral entry + (b) the artifacts named in its cross-references — could
> they tend to it competently without asking 'what did the user mean here?'"*

**Yes → `L` is sufficient. No or uncertain → upgrade to `H`. Lean toward fidelity in
doubt.** The transfer test **overrides** the default mapping: `trivial` → `L`;
`normal` → `L` if the test passes, else `H`; `important` and `blocking` → `H` always.
Full skeleton, worked examples, and anti-patterns:
[references/lane-model.md](references/lane-model.md).

### Rating axes (optional, lazy, 1-5) — ratified 2026-07-30 (DR D8)

Rate on demand, never in bulk, never guessed. Each axis carries its own `rated:` date.

- **`impact`** — value plus credible downstream reach if it succeeds.
  1 = benefits only the named item, no cited dependent. 5 = protects a critical shared
  invariant or gives cited durable leverage across several workflows/tickets.
- **`opportunity`** — *present executability*: path, prerequisites, access, scope,
  proportionate effort. **Excludes** belief that the diagnosis or remedy is correct.
  1 = nothing can proceed until a named external change. 5 = all prerequisites present,
  a bounded sequence can start now.
- **`confidence`** — evidential certainty in premise + remedy, **including** side-effect
  uncertainty. **Excludes** access and prerequisite status. 1 = no direct evidence or an
  unresolved competing explanation. 5 = reproduced/validated, assumptions and rollback
  identified.
- **`autonomy`** — human-decision burden *on the identified path*, ignoring non-human
  blockers. 1 = mid-run human choices that can't be specified up front. 5 = acceptance
  criteria, authority, and guardrails explicit; no human checkpoint expected post-launch.
  A single consolidated interview at one well-defined point still rates 3 — including,
  as the standard shape, an interview scheduled AFTER a research/enrichment pass
  (research first makes the human decisions better-informed and cheaper). What lowers
  the score is scattered mid-run choices that can't be consolidated, not one planned
  checkpoint.

**The two seams raters actually blur:**
- *Opportunity vs autonomy* — "Could it start today?" → opportunity (the world).
  "Who must be in the room?" → autonomy (the executor).
- *Confidence vs opportunity* — "Evidence you can act **with**" → opportunity.
  "Evidence you should act **at all**" → confidence.
- Known hazards lower autonomy via a required checkpoint; *uncertainty* about side
  effects lowers confidence. Don't lump both into confidence.

**Operating rules:** `impact × opportunity` ranks the queue but is never authorization —
a low product can still be mandatory for safety or because it blocks other work.
Re-rate on **trigger events** (a prerequisite lands, scope opens, evidence changes),
never on a timer. `list` marks an axis stale when the ticket changed after its `rated:`
date; it never rewrites a score. `not-before:` / `window-closes:` carry real windows and
are re-rating triggers, not a fifth axis — write them with `edit --not-before` /
`--window-closes`, and only for a **real** window. They are material metadata, so writing
one bumps `updated` and marks the ratings stale; `--lane` / `--priority` are operational,
not material, and deliberately leave rating freshness alone.

**What `list` actually renders** is deliberately narrow — `<key>: <id> [status] <title>`
plus a `· ratings stale` marker. It does **not** print lane, priority, or rating values;
read those from the record when you need them for triage.

**Backwards-compat (read, never rewrite):** absent `lane`/`priority` are treated as
`L`, `normal`; absent ratings are simply absent. Embedded v0.3 metadata lines and the
The legacy `impact: N · opportunity: N (source, YYYY-MM-DD)` form also parses.
Present-but-unparseable values or duplicate conflicting keys are **corrupt** — `doctor`
surfaces them; nothing silently rewrites them.

## Storage layout

**Index:** `$DEFERRALS_ROOT/<project-slug>.md` (default `~/.claude/deferrals`) · **Archive:**
`<project-slug>.archive.md` · **Lock:** `<index>.lock` · **Companion:**
`ddf_<id>-<slug>.md` · **Reserved global key:** `global`.

**Project-key derivation** — do not re-key, alias, or consolidate:

1. `git rev-parse --git-common-dir` from cwd; on success take its parent, **normalized**
   (the flag returns a relative path like `../.git` from any non-root cwd, so an
   un-normalized `dirname` leaves a `..` in the key). Worktree-safe.
2. Not a git repo → absolute cwd.
3. Replace every `/` and space with `-`. E.g. `/work/example project` becomes
   `-work-example-project`.

All three implementations of this rule must agree: this section, `default_project_key()`
in `scripts/deferrals.py`, and any provider-specific digest integration. When they drift, the CLI
silently reads and writes a *different index* than the SessionStart digest reports —
a silent-wrong-target class of bug, not a cosmetic one. Pass `--project-key` explicitly
whenever you want certainty.

**Shape** (full grammar in `references/v04-spec.md`):

```markdown
# Deferrals — <key>
<!-- deferrals-schema: 0.4 -->

## Active

- [ ] **ddf_0123abcd** — Title
  - status: active
  - threads: 93d4dac5, 7c4713c6
  - created: 2026-04-14 by 93d4dac5
  - lane: H | priority: important
  - archive-generation: 0
  - record-hash: sha256:<64 hex>
  - impact: 4 | rated: 2026-07-30
  <body — opaque, byte-preserved>

## Inactive

## Terminal Tombstones
```

`record-hash` covers the record slice minus the hash line; a mismatch is direct-edit
drift. IDs are `ddf_<8-lowercase-hex>`; prefixes accepted only when unique in scope.

**Companion files** — heavyweight payload for an `H` ticket lives in
`ddf_<id>-<slug>.md`; the index keeps the entry. Companions are ticket-ID-keyed,
stable across status and key changes, and are **never** deleted by `resolve`/`close`.
`forget` takes `--companion retain|delete` and defaults to `retain` — deletion is never
implicit, but omitting the flag is safe. Companion *bodies* are LLM-authored (§Golden
rule exception); the script only validates and records the pointer.

## Thread-id discovery

Needed only by the verbs that consume a thread — `add` and `claim`. Resolve once per
invocation and cache.

Use the current conversation/session identifier exposed by the host. If the host does
not expose one, ask for or generate a stable opaque token for this conversation; do
not scan private transcript stores. A fork may add its parent identifier with `claim`.

No thread identifier available → say so and stop **that verb**. `list`, `digest`, `check`, `doctor`,
`reconcile-archive`, `migrate`, `rate`, `edit`, and `transition` need no thread and
proceed normally.

## LLM-side workflows

The script owns the writes; these are the judgment parts.

[PROVIDER:CODEX]
The mutation workflows below describe the owning provider's contract and are context
only. Codex must not execute them; it may inspect and propose changes read-only.
[/PROVIDER:CODEX]

### `add` — inference loop (D6)

1. Resolve thread_id.
2. **Infer** `lane` + `priority` from chat context (transfer test first, then the
   priority mapping). Rate axes only when context genuinely supports a score.
3. **Confirm in one line:** *"Adding ddf_xxxx [H, important] — `<title>`. Confirm or
   override?"*
4. For `H`: author `Background` from chat history, `Action` from stated intent,
   `Cross-reference` from artifacts named. Load `references/lane-model.md` for the
   skeleton. Heavyweight payload → a companion file, not the index.
5. Write it: `deferrals.py add --title … --thread … --lane … --priority … [--body …]
   [--companion …]`, then `rate` if you have scores.
6. Echo: *"Added ddf_xxxx [lane, priority]."*

### `enrich` — the L → H upgrade, via `edit`

`enrich` is the judgment; `edit` is the write. Identity is preserved: same ID, same
`threads`, same `created`.

1. Re-run the transfer test. It fails → the item needs `H`.
2. Author the `Background` / `Action` / `Trigger` / `Cross-reference` skeleton from
   `references/lane-model.md`. Heavyweight payload → a companion file.
3. `edit <id> --lane H --append-body "**Background:** …"` (and `--companion <file>` when
   the payload lives outside the index). Body is append-only, so an enrich *adds* the
   H-shape detail; it never rewrites what the L record already said.

### `tend`

1. `list` active items for this project; read each record for lane/priority/ratings
   (`list` doesn't render them).
2. For each: re-check any `verify:` pointer; present
   `<id> <title> [lane, priority, ratings] — <verify status>`.
3. Collect the user's choices and apply each through the verb that owns it:

   | Choice | Verb |
   |---|---|
   | resolve / close / deactivate / activate / reopen | `transition <verb> <id> --actor <who>` |
   | re-rate | `rate <id> --impact N …` |
   | keep | no write |
   | edit / enrich (title, lane, priority, window, companion, added body) | `edit <id> …` |

4. **Never auto-resolve** — always confirm, even when a verify pointer says the work
   is done in the world.

[PROVIDER:CLAUDE]
## Optional Claude SessionStart integration

Periodic surfacing is a standing requirement, not an optional extra — the failure mode
v0.4 fixes is hygiene that only ever ran when a human remembered it.

- **SessionStart digest:** `scripts/deferrals_digest.sh` runs `digest` on
  `startup|clear` only and prints **one line** — active count, top item, elsewhere
  count. Silent when nothing is active; fail-open (any error → exit 0, no output);
  5s timeout. Resumes and compactions never re-inject it.
- **Watermark** under the configured deferrals root (hidden, so the index
  classifier ignores it; locked with `fcntl` — macOS ships no `flock(1)`). It records
  last-surfaced **per project key** and last-nudged globally, and it can only ever
  *suppress a duplicate* — every watermark failure path still prints the line.
- **Parallel-session dedup:** a second session in the same project within
  `DEFERRALS_DEDUP_SECONDS` (default 90) stays silent. Other projects are unaffected.
- **Tend nudges:** once `DEFERRALS_NUDGE_SECONDS` (default 14 days) has passed since the
  last nudge, the digest appends `· consider /deferrals tend`. Rate-limited by
  time-since-last-nudge, **never by ticket age**.
- **Manage it with the install trio**, never by hand-wiring settings:
  `scripts/install.sh` · `scripts/status.sh` · `scripts/uninstall.sh` (idempotent,
  settings-safe, refuse to install against a CLI lacking `digest`).
[/PROVIDER:CLAUDE]

## Auto-cleanup standing instruction

**When completing work that directly addresses an active deferral, run
`transition resolve <id>` as part of your task completion (same turn, not a
follow-up).** Matching is your judgment: compare the ticket's title + context against
what you just did. Err toward resolving when the match is clear; leave it active when
ambiguous (`tend` will catch it).

`resolve` means completed. `close` means deliberately judged irrelevant. They are not
interchangeable, and both are one-way except through `reopen`.

When `/deferrals` is invoked with no args, silently prime awareness of this project's
active items for the rest of the conversation.

## Guardrails

- **Script or nothing.** No freehand markdown mutation, by any agent, ever.
- Never silently delete. Terminal transitions relocate to the archive; `forget` is the
  only hard-delete, and it needs an explicit companion disposition.
- Never auto-resolve in `tend` — always confirm with the user.
- Never bulk-backfill ratings or lane/priority. Missing metadata is valid legacy;
  malformed metadata is corruption — surface it, don't rewrite it.
- Crash safety is "may duplicate, never lose": the archive copy is written and flushed
  *before* the index tombstone. `reconcile-archive` finishes the interrupted case (a
  nonterminal record at generation `g` whose archive copy is terminal at `g+1`). Every
  other generation/status disagreement is **refused** per spec §5: the repairs it *can*
  make are still committed, then it prints `refused: <id> …` to stderr and exits 2.
  Exit 0 with `reconciled N` now means no unrepairable disagreement was found.
- Migration is explicit (`migrate --check` then `--apply`), backed by a backup +
  manifest, idempotent, and refuses ambiguous legacy state.
- Discovery uses the index classifier, never raw `*.md` — archives, companions, locks,
  backups, watermarks, and temp files are not indexes.
- `check`/`doctor` cover the spec §8 list: hash drift and missing hashes, invalid status,
  glyph/section mismatch, duplicate IDs across indexes and archives, stale tombstones,
  generation mismatch, half-migrations, malformed record boundaries, mixed or legacy
  schema markers, missing required state fields, out-of-range and duplicate rating keys,
  companion mismatch/missing/collision/orphan, and stale ratings. **Two things it does
  not treat as defects:** missing `lane`/`priority` on migrated records — permitted by
  spec §3, reported as a trailing `note:` line that never sets the exit code — and
  anything the spec deems opaque. Legacy embedded rating forms are read-only history a
  canonical `  - axis:` line supersedes, so they are never flagged as conflicts.

## Out of scope for v0.4

- Project re-keying / slug consolidation. `--all-projects` plus elsewhere counts provide
  visibility without moving existing records.
- Destructive body editing (rewrite/delete of existing body bytes), window-date clearing,
  and `add`-time `--not-before`/`--window-closes` — `edit` ships the unambiguous core
  (v0.5); these three were deliberately left out rather than guessed.
  Body rewriting has since landed narrowly as `repair-body` — one unique substring,
  body bytes only (v0.5.2); the other two are still out.
- `abandon` — the v0.3 verb is gone. Its replacement is `transition close`
  (deliberately irrelevant), *not* `resolve` (actually completed). Translate the old
  word whenever a user or an old ticket uses it.
- A fifth rating axis. Effort folds into opportunity, risk-of-acting into confidence,
  perishability into `not-before:`/`window-closes:`.
- A third (medium) lane — no transfer-test-stable definition.
- `prune` — deleted from the interface; archiving is automatic storage behavior.
- `blocking`-priority notification/escalation machinery.
- Native task-list synchronization.

## Portability

The core CLI is Python-standard-library-only and supports macOS/Linux; its locking uses
POSIX `fcntl`. Git is optional and only improves automatic project-key derivation. The
Claude SessionStart integration is optional, uses Bash and `jq`, and is not installed
or invoked for other providers.
