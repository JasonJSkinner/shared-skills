# /completeness-map — Enums + Deferral Shape

The completeness map's annotation framework has two coupled enum families.

---

## Status enum (per item)

What state is this closure dimension in?

| Value | Meaning |
|---|---|
| `done` | Item is satisfied by the DIB's own implementation |
| `covered_by_child` | Delegated to a direct child DIB whose own completion map owns it (per `nested-handling.md`) |
| `covered_by_deferral` | Item is covered by an explicit external deferral URI; not yet done, but accounted-for |
| `parent_owned_open` | The parent DIB explicitly owns this item but hasn't done it yet (visible-uncovered work) |
| `uncovered` | The item is not done, not delegated, not deferred, not parent-owned — this is a gap |

---

## Completion-effect enum (per item)

What does this status MEAN for the parent's overall completion?

| Value | Meaning |
|---|---|
| `complete` | Item contributes positively to parent's completion verdict |
| `conditionally_accounted_for` | Item is accounted-for (e.g., deferred) but its completion is conditional on resolution |
| `incomplete` | Item is a gap; parent cannot be reported complete while this item exists in this state |

---

## Status × Completion-effect matrix (the meaningful pairs)

| Status | Completion-effect | Means |
|---|---|---|
| `done` | `complete` | ✅ Fully complete |
| `covered_by_child` | `complete` | ✅ Delegated, child is done |
| `covered_by_child` | `incomplete` | 🛑 Child is not done; parent inherits incompleteness |
| `covered_by_deferral` | `conditionally_accounted_for` | ⏳ Accounted-for-not-complete (the *"Coverage complete, completion blocked"* state) |
| `parent_owned_open` | `incomplete` | 🛑 Visible gap, parent's TODO |
| `uncovered` | `incomplete` | 🛑 Hidden gap (should be re-derived OR a deferral filed) |

The **"Coverage complete, completion blocked"** reporting state is exactly the `covered_by_deferral` + `conditionally_accounted_for` pair.

---

## Load-bearing deferral shape

When an item is `covered_by_deferral` AND the deferred work is load-bearing for the DIB's completion (i.e., the DIB can't be considered fully complete until the deferral resolves):

```yaml
- description: <human-readable closure dimension>
  status: covered_by_deferral
  completion_effect: conditionally_accounted_for
  blocks_full_completion: true       # load-bearing flag
  automation_blocking: false          # can automation proceed without it?
  reference:
    scheme: deferrals://  # OR github:// / linear:// / file:// / manual://
    id: <provider-stable ID>
    label: <human-readable handle, optional>
    context: <project / provider context>
```

### Provider schemes

Provider schemes must be declared in the project's provider registry or governing artifact.

The deferral's *status* is resolved from the provider at evaluation time — **DO NOT mirror provider status into the map** (that would create a stale second ledger). The reference (stable ID + provider context + label) is durable; the status is not.

### No-provider behavior

If a deferral URI's provider is not declared or resolvable, its status is `unknown` at evaluation time:

> *"An unknown/open deferral status MUST NOT be counted as completed work in strict / canonization mode."*

A map with `unknown`-status deferred items should report *"Coverage complete, completion blocked"* until the provider resolves OR the deferral is reclassified.

---

## Annotation format in the map

Each enumerated item gets a short annotation suffix:

```markdown
- Humans invoking the skill directly via slash command — *(status: done, complete)*
- Holdout discipline ≥30% — *(status: parent_owned_open, incomplete)*
- Lane file-naming convention — *(status: covered_by_deferral, conditionally_accounted_for; ref: deferrals://ddf_xxxxxxxx)*
```

For complex items (load-bearing deferrals), use the full YAML form indented under the item:

```markdown
- Multi-skill dispatch pattern across DIB-pipeline + auto-evals
  ```yaml
  status: covered_by_deferral
  completion_effect: conditionally_accounted_for
  blocks_full_completion: true
  automation_blocking: true
  reference:
    scheme: deferrals://
    id: ddf_xxxxxxxx
    label: cross_skill_dispatch_pattern
    context: dib-consolidation
  ```
```

---

## Reporting consistency (when downstream consumers read the map)

When `/auto-evals` or audit lanes consume the map and report verdicts, they MUST honor the matrix above. Specifically:

1. **A green verdict cannot include any item with `completion_effect: incomplete`** without explicit acknowledgment of the gap.
2. **The "Coverage complete, completion blocked" phrasing is reserved** for `conditionally_accounted_for` items.
3. **`unknown` (no-provider) deferrals** count as `incomplete` in strict mode.
4. **Parent completion verdict** aggregates over children's verdicts structurally (not transitively) — see `nested-handling.md`.

---

## When the enums are wrong

If you find yourself wanting an annotation that none of the enum values fit (e.g., "partially done" — there's no `partial` status), the underlying need is usually:

- Split the item into multiple closure dimensions, each with its own status (recommended)
- OR file a deferral noting the enum gap (forward-looking; don't unilaterally extend the enum here)

Do NOT silently extend the enum with custom values. The canonical enum is pinned by this release.
