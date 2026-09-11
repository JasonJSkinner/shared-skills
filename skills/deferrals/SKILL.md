---
name: deferrals
version: 0.2
description: Lightweight thread-aware tracker for "revisit later" items that would otherwise be lost through compaction, new sessions, or /fork branching. v0.2 adds two orthogonal axes — fidelity-lane (L lightweight / H high-fidelity) and priority (trivial/normal/important/blocking) — with a "transfer test" heuristic for lane choice, plus an `enrich` verb to upgrade L items to H. Invoke when the user says "defer this", "come back to this later", "revisit X", "what's still open?", "what did I defer?", "show me my deferrals", "mark that done", "resolve the deferral about Y", "enrich that deferral", or "tend to deferrals". Stores one markdown file per project at ~/.claude/deferrals/<project-slug>.md. Items carry a list of thread_ids representing fork-lineage context. Default `list` shows only items whose thread_ids include the current session. `add` and `claim` are verbs of this skill (see the verb table).
---

# Deferrals

Thread-aware, project-scoped tracker for deferred items. LLM-consumed. No machinery
beyond markdown file mutation. Fork-safe via thread_id lineage lists.

**v0.2** adds the 2-lane × 4-priority fidelity model. The
goal: lock high-fidelity context in *structurally* so an item survives transfer to
a different chat — without forcing ceremony on trivial reminders. Bulk reference
content (worked examples, full H-lane skeleton, transfer-test elaboration,
anti-patterns) lives in [references/lane-model.md](references/lane-model.md) —
load it when authoring or enriching H-lane items.

## When to invoke

Trigger on any of:

- "defer this" / "come back to this later" / "revisit X" / "note this for later"
- "what's still open?" / "what did I defer?" / "show me my deferrals" / "list deferrals"
- "mark that done" / "resolve the deferral about Y" / "that's handled now"
- "enrich that deferral" / "upgrade that deferral to high-fidelity"
- "tend to deferrals" / "reconcile deferred items" / "clean up deferrals"
- User runs `/deferrals <verb> [args]`

Also: when completing work that clearly matches an open deferral, self-invoke
`/deferrals resolve <id>` as part of task completion (see §Auto-cleanup below).

## The 2-axis fidelity model (v0.2)

Every deferral carries two orthogonal pieces of metadata, alongside `threads:` and
`created:` on the metadata line:

- **`lane: L | H`** — *fidelity*. `L` (lightweight) = title + 1-3 lines. `H`
  (high-fidelity) = structured Background/Action/Trigger/Cross-reference.
- **`priority: trivial | normal | important | blocking`** — *importance*.

Fidelity and importance are **independent**: a `blocking` item can be mechanically
obvious; a `normal` item can need a paragraph of context. Do not conflate them.

### The transfer test — the load-bearing lane tiebreaker

> *"If another agent in a different chat picked up this item — with access only to
> (a) this deferral entry + (b) the artifacts named in its cross-references — could
> they tend to it competently without asking 'what did the user mean here?'"*

**Yes → `L` is sufficient. No or uncertain → upgrade to `H`. Lean toward fidelity
in doubt.** The transfer test is authoritative — it **overrides** the default
mapping below. A `normal`-priority item still becomes `H` whenever a different-chat
agent would lack context. Do NOT reduce lane choice to the priority table alone.

### Default lane-priority mapping

| Priority | Default lane | Why |
|---|---|---|
| `trivial` | `L` | Mechanical chore; transfer test passes from the title alone. |
| `normal` | `L` if transfer test passes, else `H` | Judgment call; default `H` if uncertain. |
| `important` | `H` always | Load-bearing for downstream work. |
| `blocking` | `H` always + escalation candidate | Explicitly blocks a sprint or cycle. |

Note: `blocking` is an "escalation **candidate**" — v0.2 does not add a
notification system or change `tend`'s confirmation rule.

### Recommended item shapes per lane

**`L` lane:** title + 1-3 lines of context + optional `verify:` line.
**`H` lane:** structured fields — `Background` / `Action when triggered` /
`Trigger conditions` / `Bundling` (optional) / dated inline updates /
`Cross-reference`. **Recommended, not mandatory** — the real requirement is
passing the transfer test. Full skeleton + field descriptions + worked examples +
H-lane validation guidance + anti-patterns:
[references/lane-model.md](references/lane-model.md) (§3 skeleton, §6 validation, §7 anti-patterns).

**Backwards-compat:** untagged v0.1 items (no `lane:`/`priority:`) are read as
`lane: L, priority: normal`. This is a read-time default, NOT a write-migration —
old files are not rewritten. `enrich` is the explicit per-item upgrade path.

## Verbs

| Verb | Semantics |
|------|-----------|
| `list` (default) | Show current thread's open items (`threads:` contains current thread_id, `status=open`) |
| `list --all` | All open items regardless of thread |
| `list --resolved-here` | Items resolved by the current thread |
| `list --thread <id>` | Filter by specific thread_id (short or full UUID) |
| `list --orphaned` | Items whose creating thread's JSONL is stale (>30d) or missing |
| `add <title>` | Create item via the agent-led inference loop (see §add workflow) |
| `enrich <id>` | **(v0.2)** Upgrade an `L`-lane item to `H` — prompt through the H-shape, seeding defaults from existing context |
| `resolve <id>` | Status → resolved; record resolving thread |
| `reopen <id>` | Status → open (undo an incorrect resolve) |
| `abandon <id>` | Status → abandoned (not to be revisited) |
| `claim --from <parent>` | Append current thread_id to open items whose `threads:` contains `<parent>` |
| `tend` | Walk open items; check verify pointers; prompt user per item; batch-apply |
| `prune [--older-than 30d]` | Move old resolved/abandoned items to `<slug>.archive.md` |
| `forget <id>` | Hard-delete item from both active + archive |

## Storage layout

**Path:** `~/.claude/deferrals/<project-slug>.md`

**Project-slug derivation:**

1. Run `git rev-parse --git-common-dir` from current working directory.
2. If success: take the parent directory of the output (worktree-safe — main repo root).
3. If not a git repo: fall back to the absolute current working directory.
4. Convert: replace every `/` with `-` and every space with `-`.
5. Result: e.g. `/workspace/Example Project` → `-workspace-Example-Project`.

The same project-slug scheme is used for thread-id discovery (below).

**File format:**

```markdown
# Deferrals — <project-slug>

## Open

- [ ] **ddf_a1b2c3d4** — Revisit retry-budget heuristic in TransitEventStore
  - threads: 93d4dac5, 7c4713c6 | created: <YYYY-MM-DD> by 93d4dac5 | lane: L | priority: normal
  - verify: symbol-exists `TransitEventStore.retryBudget`
  - Backoff ramps too aggressively under burst load; consider windowed smoothing.

- [ ] **ddf_e5f6a7b8** — Audit cross-provider partial-failure semantics
  - threads: 93d4dac5 | created: <YYYY-MM-DD> by 93d4dac5 | lane: H | priority: important
  - **Background:** ... — **Action when triggered:** ... — **Trigger conditions:** ...
  - **Cross-reference:** relevant design artifact   (full H-shape: references/lane-model.md §3)

## Resolved
- [x] **ddf_9f8e7d6c** — Old thing — resolved <YYYY-MM-DD> by 7c4713c6
  - threads: 93d4dac5 | created: <YYYY-MM-DD> by 93d4dac5 | lane: L | priority: trivial

## Abandoned
<!-- empty sections stay present as headers -->
```

**Item shape rules:**

- Checkbox: `[ ]` open, `[x]` resolved, `[-]` abandoned.
- ID format: `ddf_<8-hex-chars>` — generate via `uuidgen | cut -c1-8 | tr '[:upper:]' '[:lower:]'` or equivalent.
- **Metadata line** carries, pipe-separated: `threads:` (comma-separated short-id list), `created: <YYYY-MM-DD> by <short-id>`, `lane: L|H`, `priority: trivial|normal|important|blocking`. Field order is not significant; all four SHOULD be present on v0.2-authored items.
- Resolved items append `— resolved <date> by <short-id>` to the title line.
- Optional `verify:` line — one of: `symbol-exists`, `file-exists`, `test-passes`, `url-200`, `custom <prose>`.
- Free-form context (L) or structured H-shape fields indented under the item.
- **Metadata-state classification** (read-time):
  - **Both keys absent** = valid legacy → default `L, normal` silently. Do NOT flag.
  - **Both keys present + parseable** = v0.2 item; use as-is.
  - **Present-but-unparseable value** (e.g. `lane: Q`, `priority: high` — wrong
    enum) = corrupt → surface to the user, do NOT silently rewrite.
  - **Partial presence** (one axis present, the other absent — e.g. `lane: H` with
    no `priority:`) = treat the present axis as authored; default ONLY the absent
    axis (`priority:` absent → `normal`; `lane:` absent → `L`). Do not flag —
    partial presence is a benign mixed state, not corruption.
  - **Duplicate conflicting keys** (e.g. two `lane:` values on one metadata line)
    = corrupt structure → surface to the user, do NOT silently pick one.
  Rationale: missing keys are valid legacy; broken/ambiguous keys are corruption.
  See §Guardrails.

## Thread-id discovery

Resolve the current thread_id once per invocation and cache it.

1. Compute project-dir name = absolute cwd with `/` and spaces replaced by `-`.
2. Look in `~/.claude/projects/<that-name>/` for `.jsonl` files (non-recursive).
3. Most recently modified `.jsonl` = current session.
4. Read first user-message entry in the JSONL. Extract `sessionId` = current thread_id.
5. Also extract `forkedFrom.sessionId` if present = parent thread_id (used by the `claim` verb).
6. Short-id = first 8 chars of the UUID.

If no JSONL is found, tell the user and stop.

## Verb workflows

### `list` (default)

1. Resolve thread_id.
2. Read storage file (create with empty section headers if missing).
3. Parse items under `## Open`.
4. Filter: keep items whose `threads:` list contains current short-id.
5. Render compact table: `id | title | age | lane | priority | verify-status`.
6. If zero matches, say "No open deferrals for this thread." and optionally mention
   `--all` count if non-zero.

Lane + priority are shown for triage — H/blocking items must not be visually
indistinguishable from trivial L reminders.

### `list --all` / `--resolved-here` / `--thread <id>` / `--orphaned`

Apply filter per §Verbs table. For `--orphaned`: for each item, compute creating
thread's JSONL path and check mtime; stale if >30 days or file missing.

### `add <title>` — agent-led inference loop

1. Resolve thread_id. Generate new id.
2. **Infer** default `lane` + `priority` from chat context (apply the transfer test
   + the default mapping).
3. **Confirm in one line:** *"Adding ddf_xxxx [H, important] — `<title>`. Confirm or
   override?"*
4. **For `H` lane:** populate `Background` from chat history, `Action` from stated
   intent, `Cross-reference` from artifacts mentioned. Load
   [references/lane-model.md](references/lane-model.md) for the H-shape skeleton.
5. **For `L` lane:** capture optional 1-line context if missing.
6. Append checkbox entry under `## Open`. Set `threads: [current-short-id]` + the
   inferred `lane` + `priority`.
7. **Echo:** *"Added ddf_xxxx [lane, priority]."*

**Fast-create:** a fast-create shortcut SHOULD route through this inference loop rather
than keeping a title-only fast path — a title-only bypass defeats the add contract. Prefer
invoking `/deferrals add` directly when chat context is rich enough to infer lane + priority.

### `enrich <id>` (v0.2)

1. Resolve thread_id. Locate item by id (accept unambiguous prefix).
2. If the item is already `H`, say so and stop (or offer to refine fields).
3. **Preserve identity:** the same `ddf_` ID, `threads:` list, `created:`
   metadata, `verify:` pointer, and title are RETAINED — `enrich` upgrades in
   place; it never creates a replacement item.
4. Flip `lane: L` → `lane: H`. (Leave `priority` unchanged unless context clearly
   warrants a re-rating — `enrich`'s job is the fidelity upgrade.)
5. Prompt the agent through the H-shape fields (Background / Action / Trigger /
   Cross-reference), **seeding defaults from the existing L-item context** where
   possible. Load [references/lane-model.md](references/lane-model.md) for the skeleton.
6. Echo: *"Enriched ddf_xxxx → [H, <priority>]."*

### `resolve <id>` / `reopen <id>` / `abandon <id>`

1. Resolve thread_id.
2. Locate item by id (accept unambiguous prefix).
3. Move between sections; update checkbox glyph; append resolver metadata when resolving.
4. Echo the transition in one line.

### `claim --from <parent>`

1. Resolve current thread_id.
2. For each item under `## Open` whose `threads:` list contains `<parent>` short-id
   AND does NOT already contain current short-id: append current short-id.
3. Preserve each item's `lane` + `priority` metadata unchanged.
4. Echo count: `Claimed N items from <parent>.`

### `tend`

1. List open items for current thread (same filter as default `list`).
2. For each: re-check verify pointer if present. Present to user:
   `<id> <title> [lane, priority] — <verify status>`.
3. Collect user choices (resolve / abandon / keep / edit / enrich). Batch-apply at end.
4. Never auto-resolve without user confirmation — even if a verify pointer reports
   "resolved in world".

### `prune [--older-than 30d]`

1. Read storage file.
2. For items under `## Resolved` or `## Abandoned` with age > window: move to
   `<slug>.archive.md` (create file with same section headers if missing).
3. Echo count: `Archived N items older than <window>.`

### `forget <id>`

1. Locate item in active + archive files.
2. Delete the entry entirely (including free-form context).
3. Echo: `Forgot ddf_xxxxxxxx.`

## Auto-cleanup standing instruction

**When completing work that directly addresses an open deferral, invoke
`/deferrals resolve <id>` as part of your task completion (same turn, not as a
follow-up).** Matching is your judgment: compare deferral title + context against
what you just did. Err toward marking resolved when the match is clear; leave open
when ambiguous (user can catch it via `tend`).

When `/deferrals` is invoked with no args (default `list`), silently prime
awareness of current-thread open items for the rest of the conversation.

## Guardrails

- Never silently delete. `prune` archives; `forget` is the only hard-delete verb.
- Never auto-resolve in `tend` — always confirm with the user.
- When generating a new id, verify it does not collide with any existing id in
  the active or archive file.
- **Missing `lane:`/`priority:` is valid legacy — default `L, normal`. Genuinely
  malformed metadata or corrupt item structure → surface it to the user rather
  than silently rewriting.** Per the §Storage-layout metadata-state classification:
  absent keys = legacy (default); partial presence = default only the absent axis;
  present-but-unparseable values or duplicate conflicting keys = corrupt (surface,
  do not rewrite).
- `enrich` upgrades in place — never lose an item's ID, threads, created metadata,
  or verify pointer. `enrich` on an **untagged legacy item** INSERTS `lane: H` +
  `priority: normal` (or the inferred priority) onto that one item's metadata line
  — this is a per-item, user-invoked upgrade, NOT a bulk write-migration of the file.
- Concurrent-write hazard (iCloud/Dropbox sync of `~/.claude/`) is known and
  accepted — do not add locking machinery.

## Out of scope for v0.2

- Python parsing scripts (LLM markdown handling remains the approach)
- A third (medium) lane — `L`/`H` only; medium fidelity has no transfer-test-stable definition
- Single-axis (importance-only) model — fidelity + priority stay orthogonal
- v1.0 promotion — v0.x until `enrich`-driven backfill validates the shape
- Cross-project batch view
- Session-start surfacing via PostSessionStart hook
- Integration with Claude Code's native TaskList
- `blocking`-priority auto-escalation / notification machinery
- Global backfill of every old deferral (`enrich <id>` is the per-item upgrade path)

## Relationship to other skills

- The `add` and `claim` **verbs** (see the verb table) are this skill's create and
  post-fork inheritance operations. A fast-create shortcut, if used, should route through
  the `add` inference loop rather than a title-only bypass; `claim` auto-detects the parent
  thread via `forkedFrom.sessionId` and preserves lane/priority metadata.
- The thin-umbrella + lazy-loaded `references/` sidecar pattern (v0.2's
  `references/lane-model.md`) keeps bulk reference content out of the main doctrine file.
