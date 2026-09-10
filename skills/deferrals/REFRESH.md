# deferrals REFRESH

Post-compaction recovery surface for `/deferrals`.

## Read Policy

1. **Fresh session / first use:** read `SKILL.md` for full orientation.
2. **Post-compaction / first high-stakes use:** read this `REFRESH.md` before acting.
3. **Editing this skill or its script:** reread `SKILL.md` + `references/v04-spec.md`
   (binding grammar/transaction contract) before changing canonical bytes.

## Load-Bearing Invariants (v0.4)

- **Every mutation runs through `scripts/deferrals.py`.** Never hand-edit a file under
  the configured deferrals root — records carry a `record-hash` and drift is detectable.
- `status:` is the sole lifecycle authority: `active` ↔ `inactive`, one-way
  `→ resolved` (completed) / `→ closed` (deliberately irrelevant), `reopen` the only
  reversal. Checkbox glyph and section placement are derived presentation.
- **Age is never a status or archiving signal.** Old tickets are live inventory.
  Only terminal status relocates a record to `<key>.archive.md`.
- Crash semantics: the archive copy is written and flushed *before* the index tombstone —
  a crash may duplicate, never lose. `reconcile-archive` is the repair verb.
- Lane is transfer fidelity (`L`/`H`), priority is user urgency; the transfer test
  governs lane choice. The four rating axes are optional, lazily applied, never
  bulk-backfilled, and re-rated on trigger events only.
- Do not re-key, alias, or consolidate existing project slugs.

## Verify Current State

- `python3 <provider-skill-dir>/deferrals/scripts/deferrals.py --root "$DEFERRALS_ROOT" doctor`
  → `ok` means the corpus is consistent. Run it before and after any risky operation.
[PROVIDER:CLAUDE]
- `bash ~/.claude/skills/deferrals/scripts/status.sh` → optional SessionStart digest wiring state.
[/PROVIDER:CLAUDE]
[PROVIDER:CODEX]
- Codex is read-only: restrict CLI use to `list`, `digest`, `check`, and `doctor`.
  Route proposed mutations through the separately authorized governance writer.
[/PROVIDER:CODEX]
- Before authoring or enriching H-lane items, load `references/lane-model.md`.
- If this file conflicts with `SKILL.md`, trust `SKILL.md` and refresh this recovery note.
