# /completeness-map — Nested DIB Handling

Nested completeness maps follow the recursion-stop rule, the bidirectional `.dib/` lease, and the authority-vs-completion-scope distinction.

---

## Per-`.dib/` map scope

**Each `.dib/` has its own `derived/completeness-map.md`.** A parent DIB's map does NOT enumerate descendant closure dimensions transitively.

This avoids the "transitive descendant checklist sprawl" failure mode: if every parent enumerated every grandchild's closure items, parent maps would balloon, lose focus, and double-track work the child already owns.

---

## What the parent map enumerates

For a parent DIB with N direct child DIBs:

| What | Status field | Notes |
|---|---|---|
| **Parent's own subject** | `done` / `parent_owned_open` / `uncovered` | Closure dimensions the parent directly owns (not delegated) |
| **Aggregate child closure** | `covered_by_child` | One item per direct child DIB; describes the child's *role*, not the child's own closure |
| **Explicit parent-owned items** | `parent_owned_open` | Closure dimensions the parent retains even when delegable |
| **Explicit deferred items** | `covered_by_deferral` | Closure dimensions explicitly deferred (with URI reference) |

---

## What the parent map does NOT enumerate

- Closure dimensions internal to a child DIB
- Implementation details under a child
- Sibling DIBs' closure dimensions (the parent is one level up; siblings are scoped to themselves)
- Grandchild closure dimensions

---

## Recursion-stop rule applies bidirectionally

The `.dib/` lease boundary is bidirectional. For completeness maps:

| Direction | Rule |
|---|---|
| **Parent → child** | Parent's map does NOT enumerate child's internal closure dimensions |
| **Child → parent** | Child's map does NOT reach UP into parent's protected surfaces; child's closure dimensions are scoped to the child's own subject |
| **Sibling → sibling** | Sibling maps don't enumerate each other's closure dimensions |

Crossing the boundary requires entering the target DIB's authority context (e.g., authoring an item in the parent's map that references a child via `covered_by_child` is a parent-side write, governed by the parent's authority chain; it's not a child-side write into the parent).

Use the edit-lease invariant as the boundary rule.

---

## Generation pattern for nested trees

Run the skill once per `.dib/`:

```bash
/completeness-map new <parent>.dib/ --apply
/completeness-map new <parent>/<child-1>.dib/ --apply
/completeness-map new <parent>/<child-2>.dib/ --apply
# ...
```

Order doesn't matter — maps are independent. Generation is idempotent per-DIB.

**For deeply nested trees** (parent → child → grandchild), generate at each level. The grandchild map enumerates ITS local closure; the parent's map references the child via `covered_by_child` (which itself references the grandchild via `covered_by_child` in the child's map — chain of delegation, NOT transitive enumeration).

---

## Cross-tree references (global DIBs)

When a DIB references a cross-tree governing DIB (e.g., `@global/Global-Good-Development-Principles.dib` via `forests.yaml` activation overlay), the cross-tree DIB's closure dimensions are **NOT** enumerated in this DIB's map.

The cross-tree DIB has its OWN map. The local DIB MAY note (in §4 *Implied surrounding layers*) that the cross-tree DIB's invariants apply:

```markdown
## §4 — Implied surrounding layers
- Coding standards from `@global/Global-Good-Development-Principles.dib` apply transitively
  per the `forests.yaml` activation overlay. The cross-tree DIB's own map enumerates those
  closure dimensions; this local map does not duplicate them.
```

This is consistent with the bidirectional boundary — crossing the cross-tree boundary requires entering the target DIB's authority chain.

---

## Coverage-vs-completion at the parent level

A parent's completion verdict aggregates over its children structurally (not transitively):

| Condition | Parent verdict |
|---|---|
| All children's items `done` + all parent-owned items `done` + all deferrals resolved | ✅ `complete` |
| Any child has `incomplete` items | 🛑 `incomplete` for that `covered_by_child` item; parent inherits |
| Any parent-owned item is `parent_owned_open` or `uncovered` | 🛑 `incomplete` |
| Only deferred items remain (parent's own + via children) | ⏳ *"Coverage complete, completion blocked"* |

**The aggregation is structural, not transitive** — the parent only looks at its direct children's verdicts, not at grandchildren's. The child's verdict already aggregates its grandchildren's; the parent reads the child's verdict, not the grandchildren's directly.

---

## Example map fragment (parent)

```markdown
## §1 — Intended consumers

- Humans invoking the parent DIB's documentation suite via README — *(status: done, complete)*
- Downstream consumers of the suite's documentation — *(status: covered_by_child, complete)*
  - Delegated to `Documentation-Suite.dib/Agentic-Systems-Docs.dib/`
- Future orchestrators reading the suite for the agentic-systems framework — *(status: parent_owned_open, incomplete)*
  - Parent retains this surface because it spans multiple children; not delegable to one
```

Note: the second item references the child's role; the child's own map enumerates the child's closure dimensions.

---

## Example map fragment (child of the above)

```markdown
# derived/completeness-map.md — Agentic-Systems-Docs.dib

## §1 — Intended consumers

- Operators / installers / integrators using `.agentic-systems` as a local backend — *(status: parent_owned_open, incomplete)*
- Validators consuming the operator docs as input — *(status: parent_owned_open, incomplete)*
```

The child does NOT reach UP to enumerate the parent's surfaces. The child does NOT reach SIDEWAYS to enumerate `DIB-PCB-System-Docs.dib`'s consumers. The child's scope is its own subject + its own consumers.

---

## When a child DIB needs to influence the parent's map

If a child DIB realizes its parent's map is missing an important `covered_by_child` reference (e.g., the parent forgot to delegate to it):

- **DO NOT** edit the parent's map from the child side (lease boundary violation).
- **DO** surface the gap via:
  - File a deferral against the parent's map
  - OR raise the issue to the parent's authorship chain
  - OR note it in the child's §7 (Open completeness questions) — phase-shape handoff

The map's authority is at the DIB that owns it; cross-DIB influence goes through the authority chain, not through direct edits.
